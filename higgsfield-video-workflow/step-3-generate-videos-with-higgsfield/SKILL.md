---
name: higgsfield-generate-videos
description: >
  Reads scenes.json and generates one video clip per scene using the Higgsfield
  AI video generation API. Submits all scenes in parallel, polls for completion,
  and downloads clips to ./clips/. After all clips are approved, runs
  scripts/merge_clips.py (FFmpeg) to concatenate them in scene order into
  ./final_video.mp4. Part of the Higgsfield Video Generation workflow
  (Step 3 of 3, final step). Use when scenes.json exists with fully crafted
  video_prompts. After generating and merging, ALWAYS present output and wait
  for explicit user approval.
---

# Higgsfield Video Generation → Final Merge

Two phases: generate video clips per scene → merge into final video.

All scenes are submitted to Higgsfield simultaneously — for 10 scenes the total
runtime is roughly the time for one video job, not 10× that.

## Setup: .env

Create a `.env` file in your project directory:

```
HIGGSFIELD_API_KEY=your_higgsfield_api_key_here
```

Get your API key from: https://higgsfield.ai → Account → API Keys

If no `.env` is present, the script auto-creates a template and exits.

## Prerequisites

- `scenes.json` must exist (from Step 2)
- `.env` in project directory with `HIGGSFIELD_API_KEY` filled in
- `pip install requests`
- FFmpeg installed and in PATH (for merge step)
  - Windows: `winget install ffmpeg`
  - Mac: `brew install ffmpeg`
  - Linux: `sudo apt install ffmpeg`

## Running the Script

### Per-scene mode (recommended — approve each clip before the next)

```bash
python ~/.claude/skills/higgsfield-generate-videos/scripts/generate_videos.py --scene scene_001
python ~/.claude/skills/higgsfield-generate-videos/scripts/generate_videos.py --scene scene_002
# ... etc.
```

### Bulk mode (generate all scenes at once, approve at the end)

```bash
cd /path/to/your/project
python ~/.claude/skills/higgsfield-generate-videos/scripts/generate_videos.py
```

## What the Script Does

### Phase 1 — Video Clips (parallel, Higgsfield text-to-video)

All scenes submitted simultaneously via the Higgsfield API:

- `prompt` = `video_prompt` field from `scenes.json`
- `aspect_ratio` = from `scenes.json` scene entry (default `"16:9"`)
- `duration` = `duration_seconds` from `scenes.json`
- Polls `GET /v1/generation/{generation_id}` until `status: completed`
- Downloads to `./clips/{scene_id}.mp4`

The script skips scenes where `./clips/{scene_id}.mp4` already exists — safe to re-run.

### Phase 2 — Merge Clips (FFmpeg)

After all clips are approved, run the merge script:

```bash
cd /path/to/your/project
python ~/.claude/skills/higgsfield-generate-videos/scripts/merge_clips.py
```

- Reads scene order from `scenes.json`
- Concatenates `./clips/{scene_id}.mp4` in narrative order using `ffmpeg -f concat`
- Stream copy only (no re-encoding) — completes in seconds
- Skips missing clips with a warning
- Output: `./final_video.mp4`

## Configurable Settings (top of generate_videos.py)

| Setting | Default | Description |
|---------|---------|-------------|
| `MAX_WORKERS` | `5` | Max parallel Higgsfield generation jobs |
| `POLL_INTERVAL` | `5` | Seconds between status polls |
| `MAX_POLLS` | `180` | Max polls per task (180 × 5s = 15 min timeout) |
| `DEFAULT_ASPECT_RATIO` | `"16:9"` | Fallback if not set per-scene in scenes.json |
| `DEFAULT_MOTION_STRENGTH` | ``"medium"`` | `"low"`, `"medium"`, or `"high"` |

## API Reference

| Step | Method | Endpoint | Key params |
|------|--------|----------|------------|
| Submit generation | POST | `/v1/generation` | `prompt`, `aspect_ratio`, `duration`, `motion_strength` |
| Check status | GET  | `/v1/generation/{generation_id}` | — |
| List generations | GET  | `/v1/generation` | — |

Base URL: `https://api.higgsfield.ai`

## Regenerating Failed or Rejected Scenes

1. Delete `./clips/{scene_id}.mp4`
2. Optionally update `video_prompt` in `scenes.json`
3. Re-run the script (or `--scene scene_XXX`)

## Review Gate (MANDATORY)

### Per-scene mode — after EACH scene

After each `--scene` run completes, present this EXACTLY:

```
🎬 Scene [scene_XXX] ready!

- Video clip : ./clips/scene_XXX.mp4
- Prompt used: [first 80 chars of video_prompt...]
- Run time   : [X min]

👉 Please review this clip. You can:
  - Approve → say "ok" or "next" to generate the next scene
  - Redo    → say "redo" (deletes clip, re-runs same scene)
  - Adjust  → edit video_prompt in scenes.json, then say "redo"

⏸️ Waiting for your approval before generating scene_[next].
```

Only run the next `--scene` after explicit user approval.

### Bulk mode — after ALL scenes

```
✅ Higgsfield Video Generation complete!

📋 Summary:
- Video clips: [X] → ./clips/
- Failed: [X] (list any failures)
- Total run time: [X min]

👉 Please review the clips. You can:
  - Approve all → say "approved" or "merge" to proceed to final merge
  - Regenerate specific scenes → e.g., "redo scene_003"
    (delete clips/scene_003.mp4 and re-run)

⏸️ Waiting for your approval before merging.
```

### After merge

```
🎬 Final video ready!

- Output : ./final_video.mp4
- Size   : [X] MB
- Clips  : [X] merged in scene order

⏸️ The Higgsfield Video Generation pipeline is complete. Please review final_video.mp4.
```

**NEVER** mark the pipeline as complete without explicit user approval of the
final merged video.
