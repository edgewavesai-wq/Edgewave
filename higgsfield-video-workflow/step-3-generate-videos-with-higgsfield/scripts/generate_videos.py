#!/usr/bin/env python3
"""
Generate video clips for each scene using the Higgsfield AI API — fully parallelized.

All scenes are submitted concurrently so total runtime ≈ slowest single job:

  Phase 1 — ALL video clips IN PARALLEL (Higgsfield text-to-video)
    • Submits all scenes simultaneously → each gets a unique generation_id
    • Polls all generations concurrently → total time ≈ slowest single video
    • Downloads clips to ./clips/{scene_id}.mp4

Config — create a .env file in your project directory:
  HIGGSFIELD_API_KEY=your_higgsfield_api_key_here

  On first run the script auto-creates a .env template if one is not found.

Usage:
  cd /path/to/your/project

  # Bulk mode — generate all pending scenes
  python ~/.claude/skills/higgsfield-generate-videos/scripts/generate_videos.py

  # Per-scene mode — Claude uses this for per-scene approval workflow
  python ~/.claude/skills/higgsfield-generate-videos/scripts/generate_videos.py --scene scene_001

Requirements:
  pip install requests
  scenes.json must exist (produced by Step 2 of the pipeline).

Higgsfield API reference:
  POST https://api.higgsfield.ai/v1/generation        — submit a generation
  GET  https://api.higgsfield.ai/v1/generation/{id}   — poll status
  Authentication: Authorization: Bearer <HIGGSFIELD_API_KEY>
"""

import os
import json
import time
import threading
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import requests


# ── Config loading (.env) ─────────────────────────────────────────────────────

_ENV_TEMPLATE = """\
# Higgsfield Video Generation — API Keys
# Get your Higgsfield API key from: https://higgsfield.ai → Account → API Keys

HIGGSFIELD_API_KEY=your_higgsfield_api_key_here
"""


def load_env() -> None:
    """Load .env from the project directory into os.environ.
    Auto-creates a template .env and exits cleanly if none is found.
    Real environment variables always take precedence.
    """
    env_path = Path(".env")
    if not env_path.exists():
        env_path.write_text(_ENV_TEMPLATE, encoding="utf-8")
        print("\n  .env file created in your project directory.")
        print("  -> Open .env, fill in your HIGGSFIELD_API_KEY, then re-run this script.\n")
        raise SystemExit(0)

    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key, val = key.strip(), val.strip()
        if key and key not in os.environ:
            os.environ[key] = val

    print("  Loaded API keys from .env")


def get_key(name: str) -> str:
    """Return a required key from os.environ (populated by load_env)."""
    val = os.environ.get(name, "").strip()
    placeholder = f"your_{name.lower()}_here"
    if not val or val == placeholder:
        print(f"\nERROR: '{name}' is not set in .env")
        print(f"  Open .env in your project directory and set:  {name}=your_actual_key")
        raise SystemExit(1)
    return val


load_env()
HIGGSFIELD_API_KEY = get_key("HIGGSFIELD_API_KEY")


# ── API endpoints ─────────────────────────────────────────────────────────────

HIGGSFIELD_BASE_URL  = "https://api.higgsfield.ai"
GENERATE_URL         = f"{HIGGSFIELD_BASE_URL}/v1/generation"
STATUS_URL_TEMPLATE  = f"{HIGGSFIELD_BASE_URL}/v1/generation/{{generation_id}}"

HEADERS = {
    "Authorization": f"Bearer {HIGGSFIELD_API_KEY}",
    "Content-Type":  "application/json",
}


# ── Tunable settings ──────────────────────────────────────────────────────────

MAX_WORKERS           = 5         # parallel Higgsfield generation jobs
POLL_INTERVAL         = 5         # seconds between polls
MAX_POLLS             = 180       # max wait: 180 × 5s = 15 minutes per task

DEFAULT_ASPECT_RATIO  = "16:9"    # fallback if not set per-scene in scenes.json
DEFAULT_MOTION_STRENGTH = "medium" # "low", "medium", or "high"


# ── Thread-safe print ─────────────────────────────────────────────────────────

_print_lock = threading.Lock()


def tprint(*args, **kwargs):
    with _print_lock:
        print(*args, **kwargs)


def fmt_elapsed(start: float) -> str:
    s = int(time.time() - start)
    return f"{s // 60}m{s % 60:02d}s" if s >= 60 else f"{s}s"


# ── Higgsfield API helpers ────────────────────────────────────────────────────

def submit_generation(scene: dict) -> tuple:
    """Submit a text-to-video generation to Higgsfield.

    Returns (generation_id, None) on success or (None, error_str) on failure.
    """
    payload = {
        "prompt":          scene["video_prompt"],
        "aspect_ratio":    scene.get("aspect_ratio", DEFAULT_ASPECT_RATIO),
        "duration":        scene.get("duration_seconds", 6),
        "motion_strength": DEFAULT_MOTION_STRENGTH,
    }

    try:
        resp = requests.post(GENERATE_URL, headers=HEADERS, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        # Higgsfield returns the generation ID in data["id"] or data["generation_id"]
        generation_id = data.get("id") or data.get("generation_id")
        if not generation_id:
            return None, f"No generation_id in response: {data}"
        return generation_id, None

    except requests.HTTPError as e:
        return None, f"HTTP {e.response.status_code}: {e.response.text[:200]}"
    except Exception as e:
        return None, str(e)


def poll_generation(generation_id: str, label: str) -> tuple:
    """Poll Higgsfield until the generation completes.

    Returns (video_url, None) on success or (None, error_str) on failure.

    Higgsfield status values:
      pending   — queued, not yet started
      processing — generation in progress
      completed — done, video_url is available
      failed    — generation failed
    """
    url = STATUS_URL_TEMPLATE.format(generation_id=generation_id)

    for attempt in range(1, MAX_POLLS + 1):
        time.sleep(POLL_INTERVAL)
        try:
            resp   = requests.get(url, headers=HEADERS, timeout=30)
            resp.raise_for_status()
            data   = resp.json()
            status = data.get("status", "").lower()

            if status == "completed":
                video_url = data.get("video_url") or data.get("url")
                if video_url:
                    return video_url, None
                return None, "status=completed but no video_url in response"

            elif status == "failed":
                reason = data.get("error") or data.get("message") or "no reason given"
                return None, f"Generation failed: {reason}"

            else:
                elapsed_s = attempt * POLL_INTERVAL
                if elapsed_s % 30 == 0:
                    tprint(f"    [{label}] {status or 'pending'} — {elapsed_s}s elapsed...")

        except requests.HTTPError as e:
            tprint(f"    [{label}] poll HTTP error: {e.response.status_code}")
        except Exception as e:
            tprint(f"    [{label}] poll error: {e}")

    timeout_s = MAX_POLLS * POLL_INTERVAL
    return None, f"Timed out after {timeout_s // 60}m{timeout_s % 60:02d}s"


def download_file(url: str, output_path: Path) -> bool:
    try:
        resp = requests.get(url, timeout=120)
        resp.raise_for_status()
        output_path.write_bytes(resp.content)
        return output_path.stat().st_size > 0
    except Exception as e:
        tprint(f"    Download failed: {e}")
        return False


# ── Per-scene worker ──────────────────────────────────────────────────────────

def run_scene(scene: dict, clip_path: Path) -> tuple:
    """Generate one video clip for a scene.

    Returns (scene_id, True, None) on success or (scene_id, False, error_str).
    """
    sid = scene["scene_id"]
    t0  = time.time()

    generation_id, err = submit_generation(scene)
    if not generation_id:
        return sid, False, f"Submit failed: {err}"

    tprint(f"  [{sid}] submitted → generation_id: {generation_id[:16]}...")

    video_url, err = poll_generation(generation_id, sid)
    if not video_url:
        return sid, False, err

    if download_file(video_url, clip_path):
        tprint(f"  [{sid}] done ({fmt_elapsed(t0)}) → clips/{sid}.mp4")
        return sid, True, None

    return sid, False, "Download failed or empty file"


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Generate Higgsfield video clips for each scene in scenes.json."
    )
    parser.add_argument(
        "--scene", metavar="SCENE_ID",
        help="Process a single scene only (e.g. --scene scene_001). "
             "Claude uses this for per-scene approval workflow. "
             "Omit to process all pending scenes at once.",
    )
    args = parser.parse_args()

    run_start = time.time()
    print("\n=== Higgsfield Video Generation: Step 3 — Generate Video Clips ===\n")

    # ── Load scenes.json ──────────────────────────────────────────────────────
    if not Path("scenes.json").exists():
        print("ERROR: scenes.json not found in current directory.")
        print("  Run Step 2 (generate scene prompts) first.")
        raise SystemExit(1)

    scenes_data = json.loads(Path("scenes.json").read_text(encoding="utf-8"))
    all_scenes  = scenes_data.get("scenes", [])

    if not all_scenes:
        print("ERROR: scenes.json contains no scenes.")
        raise SystemExit(1)

    print(f"  Video title : {scenes_data.get('video_title', 'Untitled')}")
    print(f"  Total scenes: {len(all_scenes)}")

    # ── Build pending list ─────────────────────────────────────────────────────
    Path("clips").mkdir(exist_ok=True)

    if args.scene:
        # Single-scene mode — Claude calls this once per scene for approval workflow
        target = next((s for s in all_scenes if s["scene_id"] == args.scene), None)
        if not target:
            print(f"ERROR: scene_id '{args.scene}' not found in scenes.json")
            raise SystemExit(1)
        clip_path = Path("clips") / f"{args.scene}.mp4"
        if clip_path.exists():
            print(f"[{args.scene}] clip already exists — nothing to do.")
            return
        pending = [target]
        skipped = []
        print(f"  Mode        : single-scene  ({args.scene})\n")
    else:
        # Bulk mode — process all pending scenes without pausing
        pending = [s for s in all_scenes if not (Path("clips") / f"{s['scene_id']}.mp4").exists()]
        skipped = [s["scene_id"] for s in all_scenes if s not in pending]
        print(f"  Mode        : bulk  ({len(pending)} pending, {len(skipped)} already done)\n")

    if skipped:
        print(f"Skipping {len(skipped)} scene(s) with existing clips: {', '.join(skipped)}")
    if not pending:
        print("All clips already exist. Nothing to do.")
        return

    # ── Generate clips ─────────────────────────────────────────────────────────
    print(f"Submitting {len(pending)} scene(s) to Higgsfield...\n")

    results = {"success": [], "failed": [], "skipped": skipped}

    if args.scene:
        # Single scene — run directly without thread pool
        sid, ok, err = run_scene(pending[0], Path("clips") / f"{args.scene}.mp4")
        if ok:
            results["success"].append(sid)
        else:
            print(f"  [{sid}] FAILED: {err}")
            results["failed"].append(sid)
    else:
        # Bulk — all scenes in parallel
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {
                executor.submit(
                    run_scene,
                    scene,
                    Path("clips") / f"{scene['scene_id']}.mp4"
                ): scene["scene_id"]
                for scene in pending
            }
            for future in as_completed(futures):
                sid, ok, err = future.result()
                if ok:
                    results["success"].append(sid)
                else:
                    tprint(f"  [{sid}] FAILED: {err}")
                    results["failed"].append(sid)

    # ── Summary ───────────────────────────────────────────────────────────────
    total_run_time = fmt_elapsed(run_start)

    print(f"\n{'='*55}")
    print(f"  Total run time : {total_run_time}")
    print(f"  Generated      : {len(results['success'])} clips")
    print(f"  Skipped        : {len(results['skipped'])} (clips already existed)")
    print(f"  Failed         : {len(results['failed'])}")
    print(f"{'='*55}")
    print(f"  Clips → ./clips/")

    if results["failed"]:
        print("\nFailed scenes (delete clip file then re-run to retry):")
        for sid in results["failed"]:
            print(f"  - {sid}")
        raise SystemExit(1)
    else:
        print("\nAll clips generated! Run merge_clips.py to create the final video.")


if __name__ == "__main__":
    main()
