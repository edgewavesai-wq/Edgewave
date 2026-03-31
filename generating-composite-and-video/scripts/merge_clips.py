#!/usr/bin/env python3
"""
Merge all generated video clips into a single final animation.

Reads shot order from shots.json, finds ./clips/{shot_id}.mp4 for each shot,
and merges them in narrative order using FFmpeg (stream copy — no re-encoding).

Output: ./final_animation.mp4

Usage:
  cd /path/to/your/project
  python ~/.claude/skills/generating-composite-and-video/scripts/merge_clips.py

Requirements:
  FFmpeg installed and in PATH.
    Windows : winget install ffmpeg
    Mac     : brew install ffmpeg
    Linux   : sudo apt install ffmpeg
"""

import json
import subprocess
from pathlib import Path


# ── Helpers ───────────────────────────────────────────────────────────────────

def check_ffmpeg() -> bool:
    """Return True if ffmpeg is available in PATH."""
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True, text=True,
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("\n=== Story-to-Animation: Merge Clips → final_animation.mp4 ===\n")

    # ── Check FFmpeg ──────────────────────────────────────────────────────────
    if not check_ffmpeg():
        print("ERROR: FFmpeg not found in PATH.")
        print("  Windows : winget install ffmpeg   (then restart terminal)")
        print("  Mac     : brew install ffmpeg")
        print("  Linux   : sudo apt install ffmpeg")
        raise SystemExit(1)

    # ── Load shot order ───────────────────────────────────────────────────────
    if not Path("shots.json").exists():
        print("ERROR: shots.json not found in current directory")
        raise SystemExit(1)

    shots_data = json.loads(Path("shots.json").read_text(encoding="utf-8"))
    all_shots  = shots_data.get("shots", [])

    if not all_shots:
        print("ERROR: No shots found in shots.json")
        raise SystemExit(1)

    # ── Collect clips in narrative order ──────────────────────────────────────
    clips_dir = Path("clips")
    available = []
    missing   = []

    for shot in all_shots:
        sid       = shot["shot_id"]
        clip_path = clips_dir / f"{sid}.mp4"
        if clip_path.exists():
            available.append((sid, clip_path))
        else:
            missing.append(sid)

    print(f"  Shots in order : {len(all_shots)}")
    print(f"  Clips found    : {len(available)}")
    if missing:
        print(f"  Missing clips  : {', '.join(missing)}  ← will be skipped")
    print()

    if not available:
        print("ERROR: No clips found in ./clips/ — run generate_videos.py first.")
        raise SystemExit(1)

    if len(available) == 1:
        print("Only one clip found — copying directly to final_animation.mp4")
        import shutil
        shutil.copy2(available[0][1], "final_animation.mp4")
        print("✅ Done → ./final_animation.mp4")
        return

    # ── Write FFmpeg concat list ──────────────────────────────────────────────
    concat_path = Path("concat.txt")
    with open(concat_path, "w", encoding="utf-8") as f:
        for sid, clip_path in available:
            # Use forward-slash absolute path (safe on all platforms)
            abs_path = clip_path.resolve().as_posix()
            f.write(f"file '{abs_path}'\n")

    print(f"Merging {len(available)} clips in order:")
    for sid, _ in available:
        print(f"  {sid}.mp4")
    print()

    output_path = Path("final_animation.mp4")

    # ── Run FFmpeg ────────────────────────────────────────────────────────────
    cmd = [
        "ffmpeg",
        "-y",               # overwrite output if it already exists
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_path),
        "-c", "copy",       # stream copy — no re-encoding, very fast
        str(output_path),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    # Always clean up concat file
    concat_path.unlink(missing_ok=True)

    if result.returncode != 0:
        print("ERROR: FFmpeg failed:")
        # Show last 3000 chars of stderr (ffmpeg is verbose)
        print(result.stderr[-3000:] if result.stderr else "(no output)")
        raise SystemExit(1)

    # ── Summary ───────────────────────────────────────────────────────────────
    size_mb = output_path.stat().st_size / (1024 * 1024)

    print(f"{'='*50}")
    print(f"  ✅ Output   : ./final_animation.mp4")
    print(f"     Size     : {size_mb:.1f} MB")
    print(f"     Merged   : {len(available)} clips")
    if missing:
        print(f"     Skipped  : {len(missing)} missing  ({', '.join(missing)})")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
