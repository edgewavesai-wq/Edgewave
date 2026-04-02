#!/usr/bin/env python3
"""
Merge all generated video clips into a single final video using FFmpeg.

Reads scene order from scenes.json, concatenates ./clips/{scene_id}.mp4
files in narrative order, and writes ./final_video.mp4.

Uses FFmpeg stream copy (no re-encoding) so the merge completes in seconds
regardless of total video length.

Usage:
  cd /path/to/your/project
  python ~/.claude/skills/higgsfield-generate-videos/scripts/merge_clips.py

Requirements:
  FFmpeg installed and available in PATH
    Windows : winget install ffmpeg
    Mac     : brew install ffmpeg
    Linux   : sudo apt install ffmpeg

  scenes.json must exist in the current directory.
  At least one clip must exist in ./clips/.
"""

import json
import shutil
import subprocess
import tempfile
from pathlib import Path


def check_ffmpeg() -> bool:
    """Return True if ffmpeg is available in PATH."""
    return shutil.which("ffmpeg") is not None


def main():
    print("\n=== Higgsfield Video Generation: Merge Clips → final_video.mp4 ===\n")

    # ── Check FFmpeg ──────────────────────────────────────────────────────────
    if not check_ffmpeg():
        print("ERROR: ffmpeg not found in PATH.")
        print("  Install it and ensure it is accessible:")
        print("    Windows : winget install ffmpeg")
        print("    Mac     : brew install ffmpeg")
        print("    Linux   : sudo apt install ffmpeg")
        raise SystemExit(1)

    # ── Load scenes.json ──────────────────────────────────────────────────────
    if not Path("scenes.json").exists():
        print("ERROR: scenes.json not found in current directory.")
        raise SystemExit(1)

    scenes_data = json.loads(Path("scenes.json").read_text(encoding="utf-8"))
    all_scenes  = scenes_data.get("scenes", [])

    if not all_scenes:
        print("ERROR: scenes.json contains no scenes.")
        raise SystemExit(1)

    print(f"  Video title : {scenes_data.get('video_title', 'Untitled')}")
    print(f"  Total scenes: {len(all_scenes)}")

    # ── Collect clips in scene order ──────────────────────────────────────────
    clips_dir = Path("clips")
    found     = []
    missing   = []

    for scene in all_scenes:
        sid       = scene["scene_id"]
        clip_path = clips_dir / f"{sid}.mp4"
        if clip_path.exists() and clip_path.stat().st_size > 0:
            found.append(clip_path)
        else:
            missing.append(sid)

    if missing:
        print(f"\n  WARNING: {len(missing)} clip(s) not found — will be skipped:")
        for sid in missing:
            print(f"    - {sid}")

    if not found:
        print("\nERROR: No clips found in ./clips/. Generate clips first.")
        raise SystemExit(1)

    print(f"\n  Merging {len(found)} clip(s) in scene order...")

    # ── Write FFmpeg concat list ───────────────────────────────────────────────
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, encoding="utf-8"
    ) as tmp:
        concat_file = Path(tmp.name)
        for clip_path in found:
            # Use absolute paths so FFmpeg can find files from any cwd
            abs_path = clip_path.resolve()
            tmp.write(f"file '{abs_path}'\n")

    output_path = Path("final_video.mp4")

    # ── Run FFmpeg ─────────────────────────────────────────────────────────────
    cmd = [
        "ffmpeg",
        "-y",                  # overwrite output without prompting
        "-f", "concat",        # concat demuxer
        "-safe", "0",          # allow absolute paths in concat list
        "-i", str(concat_file),
        "-c", "copy",          # stream copy — no re-encoding
        str(output_path),
    ]

    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        print(f"\nERROR: FFmpeg failed:")
        print(e.stderr.decode(errors="replace")[-1000:])
        raise SystemExit(1)
    finally:
        concat_file.unlink(missing_ok=True)

    # ── Report ────────────────────────────────────────────────────────────────
    if not output_path.exists():
        print("\nERROR: FFmpeg reported success but final_video.mp4 was not created.")
        raise SystemExit(1)

    size_mb = output_path.stat().st_size / (1024 * 1024)

    print(f"\n{'='*55}")
    print(f"  Output  : ./final_video.mp4")
    print(f"  Size    : {size_mb:.1f} MB")
    print(f"  Clips   : {len(found)} merged in scene order")
    if missing:
        print(f"  Skipped : {len(missing)} missing clip(s)")
    print(f"{'='*55}")
    print("\nDone! The Higgsfield Video Generation pipeline is complete.")


if __name__ == "__main__":
    main()
