#!/usr/bin/env python3
"""
Generate character and background images using the kie.ai nano-banana-pro API,
then upload each image to imgbb for permanent public hosting.

Pipeline per image:
  1. POST /jobs/createTask (nano-banana-pro) → kie.ai generates image
  2. Poll /jobs/recordInfo until state: success → get kie.ai image URL
  3. Download PNG to ./characters/ or ./backgrounds/
  4. Upload PNG to imgbb → get permanent public URL
  5. Store imgbb URL as image_url in characters.json / backgrounds.json

Config — create a .env file in your project directory:
  KIE_API_TOKEN=your_kie_api_key_here
  IMGBB_API_KEY=your_imgbb_api_key_here

  On first run the script auto-creates a .env template if one is not found.
  Real environment variables always take precedence over .env values.

Usage:
  cd /path/to/your/project
  python ~/.claude/skills/generating-character-and-background-images/scripts/generate_images.py

Requirements:
  pip install requests
"""

import os
import json
import time
import base64
from pathlib import Path
import requests


# ── Config loading (.env) ─────────────────────────────────────────────────────

_ENV_TEMPLATE = """\
# Story-to-Animation — API Keys
# Get your kie.ai key from: https://kie.ai -> Dashboard -> API Keys
# Get your imgbb key from:  https://api.imgbb.com (free account)

KIE_API_TOKEN=your_kie_api_key_here
IMGBB_API_KEY=your_imgbb_api_key_here
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
        print("  -> Open .env, fill in your API keys, then re-run this script.\n")
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
KIE_API_TOKEN = get_key("KIE_API_TOKEN")
IMGBB_API_KEY = get_key("IMGBB_API_KEY")


# ── API constants ─────────────────────────────────────────────────────────────

KIE_CREATE_URL   = "https://api.kie.ai/api/v1/jobs/createTask"
KIE_STATUS_URL   = "https://api.kie.ai/api/v1/jobs/recordInfo"
IMGBB_UPLOAD_URL = "https://api.imgbb.com/1/upload"
MODEL            = "nano-banana-pro"

KIE_POST_HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {KIE_API_TOKEN}",
}
KIE_GET_HEADERS  = {"Authorization": f"Bearer {KIE_API_TOKEN}"}

KIE_POLL_INTERVAL = 5    # seconds between status polls
KIE_MAX_POLLS     = 36   # max ~3 minutes per image


# ── Step 1 & 2: kie.ai image generation ──────────────────────────────────────

def submit_task(prompt: str, aspect_ratio: str) -> tuple:
    """Submit image generation. Returns (task_id, None) or (None, error)."""
    payload = {
        "model": MODEL,
        "input": {
            "prompt": prompt,
            "aspect_ratio": aspect_ratio,
            "resolution": "1K",
            "output_format": "png",
        },
    }
    try:
        resp   = requests.post(KIE_CREATE_URL, headers=KIE_POST_HEADERS, json=payload, timeout=30)
        result = resp.json()
        if result.get("code") != 200:
            return None, result.get("msg", "Unknown error")
        return result["data"]["taskId"], None
    except Exception as e:
        return None, str(e)


def poll_task(task_id: str) -> tuple:
    """Poll recordInfo until image is ready. Returns (kie_url, None) or (None, error)."""
    params = {"taskId": task_id}
    for attempt in range(1, KIE_MAX_POLLS + 1):
        time.sleep(KIE_POLL_INTERVAL)
        try:
            resp  = requests.get(KIE_STATUS_URL, headers=KIE_GET_HEADERS, params=params, timeout=30)
            data  = resp.json().get("data", {})
            state = data.get("state", "").lower()

            if state == "success":
                result = data.get("resultJson", {})
                if isinstance(result, str):
                    result = json.loads(result)
                urls = result.get("resultUrls", [])
                if urls:
                    return urls[0], None
                return None, "No resultUrls in response"

            elif state == "fail":
                return None, data.get("failMsg", "Generation failed")

            else:
                print(f"    [kie.ai] Poll {attempt}/{KIE_MAX_POLLS} — state: {state or 'waiting'}...")

        except Exception as e:
            print(f"    [kie.ai] Poll {attempt} error: {e}")

    return None, f"Timed out after {KIE_MAX_POLLS} polls ({KIE_MAX_POLLS * KIE_POLL_INTERVAL}s)"


# ── Step 3: Download locally ──────────────────────────────────────────────────

def download_file(url: str, output_path: Path) -> bool:
    """Download image to local path. Returns True on success."""
    try:
        resp = requests.get(url, timeout=60)
        output_path.write_bytes(resp.content)
        return output_path.stat().st_size > 0
    except Exception as e:
        print(f"    Download failed: {e}")
        return False


# ── Step 4: Upload to imgbb ───────────────────────────────────────────────────

def upload_to_imgbb(local_path: Path) -> tuple:
    """Upload local PNG to imgbb. Returns (public_url, None) or (None, error)."""
    try:
        with open(local_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")
        resp   = requests.post(
            IMGBB_UPLOAD_URL,
            params={"key": IMGBB_API_KEY},
            data={"image": b64},
            timeout=60,
        )
        result = resp.json()
        if result.get("success"):
            return result["data"]["url"], None
        err_msg = result.get("error", {}).get("message", "Upload failed")
        return None, err_msg
    except Exception as e:
        return None, str(e)


# ── Full per-image pipeline ───────────────────────────────────────────────────

def generate_and_host(prompt: str, aspect_ratio: str, out_path: Path) -> tuple:
    """
    Full pipeline: generate → download → upload to imgbb.
    Returns:
      ("SKIP", None)     — file already exists, skip
      (imgbb_url, None)  — success, imgbb permanent URL
      (kie_url, None)    — imgbb failed, fallback to kie.ai URL
      (None, error)      — complete failure
    """
    if out_path.exists():
        return "SKIP", None

    # Step 1 & 2: Generate on kie.ai
    task_id, err = submit_task(prompt, aspect_ratio)
    if not task_id:
        return None, f"Submit failed: {err}"

    kie_url, err = poll_task(task_id)
    if not kie_url:
        return None, err

    # Step 3: Download locally
    if not download_file(kie_url, out_path):
        return None, "Download failed"

    # Step 4: Upload to imgbb
    imgbb_url, err = upload_to_imgbb(out_path)
    if not imgbb_url:
        print(f"\n    [imgbb] Upload failed ({err}) — using kie.ai URL as fallback")
        return kie_url, None   # fallback — still usable, just not permanent

    print(f"\n    [imgbb] Hosted at: {imgbb_url}")
    return imgbb_url, None


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("\n=== Story-to-Animation: Step 3 — Image Generation ===\n")

    for fname in ["characters.json", "backgrounds.json"]:
        if not Path(fname).exists():
            print(f"ERROR: {fname} not found in current directory")
            raise SystemExit(1)

    chars_data = json.loads(Path("characters.json").read_text(encoding="utf-8"))
    bgs_data   = json.loads(Path("backgrounds.json").read_text(encoding="utf-8"))

    Path("characters").mkdir(exist_ok=True)
    Path("backgrounds").mkdir(exist_ok=True)

    results    = {"success": [], "skipped": [], "failed": []}
    json_dirty = {"chars": False, "bgs": False}

    # ── Character images (1:1 reference sheets) ───────────────────────────────
    characters = chars_data.get("characters", [])
    print(f"Generating {len(characters)} character image(s)...\n")

    for char in characters:
        cid = char["character_id"]
        out = Path("characters") / f"{cid}.png"
        print(f"  [{cid}] {char['name']}...")

        url, err = generate_and_host(char["prompt"], "1:1", out)

        if url == "SKIP":
            print(f"         → already exists, skipping (delete to regenerate)")
            results["skipped"].append(f"characters/{cid}.png")
        elif url:
            char["image_url"] = url
            json_dirty["chars"] = True
            print(f"         → saved to characters/{cid}.png")
            results["success"].append(f"characters/{cid}.png")
        else:
            print(f"         → FAILED: {err}")
            results["failed"].append(f"characters/{cid}.png")

    # ── Background images (16:9 cinematic) ────────────────────────────────────
    backgrounds = bgs_data.get("backgrounds", [])
    print(f"\nGenerating {len(backgrounds)} background image(s)...\n")

    for bg in backgrounds:
        bid = bg["bg_id"]
        out = Path("backgrounds") / f"{bid}.png"
        print(f"  [{bid}] {bg['name']}...")

        url, err = generate_and_host(bg["prompt"], "16:9", out)

        if url == "SKIP":
            print(f"         → already exists, skipping (delete to regenerate)")
            results["skipped"].append(f"backgrounds/{bid}.png")
        elif url:
            bg["image_url"] = url
            json_dirty["bgs"] = True
            print(f"         → saved to backgrounds/{bid}.png")
            results["success"].append(f"backgrounds/{bid}.png")
        else:
            print(f"         → FAILED: {err}")
            results["failed"].append(f"backgrounds/{bid}.png")

    # ── Write image_url (imgbb) back into JSON files ──────────────────────────
    if json_dirty["chars"]:
        Path("characters.json").write_text(
            json.dumps(chars_data, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print("\n  ✓ characters.json updated with image_url (imgbb)")
    if json_dirty["bgs"]:
        Path("backgrounds.json").write_text(
            json.dumps(bgs_data, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print("  ✓ backgrounds.json updated with image_url (imgbb)")

    # ── Summary ───────────────────────────────────────────────────────────────
    print(f"\n{'='*50}")
    print(f"  Generated : {len(results['success'])}")
    print(f"  Skipped   : {len(results['skipped'])} (already existed)")
    print(f"  Failed    : {len(results['failed'])}")
    print(f"{'='*50}")

    if results["skipped"]:
        print("\nNote: Skipped images have no image_url in JSON.")
        print("      Delete the PNG file and re-run to generate + host a fresh URL.")

    if results["failed"]:
        print("\nFailed images (update prompt in JSON, delete PNG, re-run):")
        for f in results["failed"]:
            print(f"  - {f}")
        raise SystemExit(1)
    else:
        print("\nAll done! image_url fields are permanent imgbb URLs.")
        print("Next step: create the shot list (Skill 4), then run generate_videos.py (Skill 5).")


if __name__ == "__main__":
    main()
