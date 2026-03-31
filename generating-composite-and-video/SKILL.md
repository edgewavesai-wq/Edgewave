---
name: generating-composite-and-video
description: >
  Reads shots.json and processes each shot in two fully-parallel phases:
  (1) generates composite scene images by blending character and background
  images (imgbb image_url fields) via the kie.ai flux-2/pro-image-to-image API,
  saving to ./composites/; (2) generates video clips from each composite using
  the kie.ai sora-2-image-to-video API, saving to ./clips/. Both phases use
  the taskId-based /jobs/recordInfo polling so all shots run concurrently —
  total time is the slowest single job, not the sum. After clips are approved,
  runs scripts/merge_clips.py (FFmpeg) to concatenate all clips in narrative
  order into ./final_animation.mp4. API keys loaded from config.json. Part of
  the Story-to-Animation pipeline (Step 5 of 5, final step). Use when
  shots.json exists and characters.json/backgrounds.json have image_url fields
  (populated by generate_images.py in Step 3). After generating and merging,
  ALWAYS present output and wait for explicit user approval.
---

# Composite Image + Video Generation → Final Merge

Three phases: composite scene images → video clips → merged final animation.

All shots are processed concurrently — for 15 shots the total runtime is roughly
the time for one composite + one video, not 15× that.

## Setup: .env

Same `.env` as Step 3 — if it already exists in your project directory from
running `generate_images.py`, no extra setup is needed. Only `KIE_API_TOKEN`
is used by this script (`IMGBB_API_KEY` is ignored here).

If no `.env` is present, the script auto-creates a template and exits:
```
KIE_API_TOKEN=your_kie_api_key_here
IMGBB_API_KEY=your_imgbb_api_key_here
```

Fill in `KIE_API_TOKEN` and re-run. Real environment variables take precedence.

## Prerequisites

- `shots.json` must exist (from Skill 4)
- `characters.json` and `backgrounds.json` must have `image_url` fields
  (permanent imgbb URLs set by `generate_images.py` in Step 3)
- `.env` in project directory with `KIE_API_TOKEN` filled in
- `pip install requests`
- FFmpeg installed and in PATH (for merge step)
  - Windows: `winget install ffmpeg`
  - Mac: `brew install ffmpeg`
  - Linux: `sudo apt install ffmpeg`

## Running the Script

### Per-shot mode (recommended — approve each clip before the next)

Run one shot at a time. Claude generates the composite + video, presents the
result, and waits for your approval before moving to the next shot.

```bash
# Claude runs this once per shot, waiting for approval in between
python ~/.claude/skills/generating-composite-and-video/scripts/generate_videos.py --shot shot_001
python ~/.claude/skills/generating-composite-and-video/scripts/generate_videos.py --shot shot_002
# ... etc.
```

### Bulk mode (generate all shots at once, approve at the end)

```bash
cd /path/to/your/project
python ~/.claude/skills/generating-composite-and-video/scripts/generate_videos.py
```

## What the Script Does

### Phase 1 — Composite images (parallel, flux-2/pro-image-to-image)

All shots submitted simultaneously. Each gets a `taskId` for independent polling.

- `input_urls` = [background `image_url`, character `image_url`(s)] from JSON
- `prompt` = shot `action` + "Pixar-style 3D animation, cinematic 16:9 composition"
- Polls `GET /jobs/recordInfo?taskId=...` until `state: success`
- Downloads to `./composites/{shot_id}.png`

### Phase 2 — Video clips (parallel, sora-2-image-to-video)

All shots submitted simultaneously. Each gets a `taskId` for independent polling.

- `image_urls` = [composite URL from Phase 1]
- `prompt` = `veo_prompt` field from `shots.json`
- `aspect_ratio` = `"landscape"`
- `n_frames` = `"10"`
- `remove_watermark` = `true`
- Polls `GET /jobs/recordInfo?taskId=...` until `state: success`
- Downloads to `./clips/{shot_id}.mp4`

The script skips shots where `./clips/{shot_id}.mp4` already exists — safe to re-run.

### Phase 3 — Merge clips (FFmpeg)

After all clips are approved, run the merge script:

```bash
cd /path/to/your/project
python ~/.claude/skills/generating-composite-and-video/scripts/merge_clips.py
```

- Reads shot order from `shots.json`
- Concatenates `./clips/{shot_id}.mp4` in narrative order using `ffmpeg -f concat`
- Stream copy only (no re-encoding) — completes in seconds
- Skips any missing clips with a warning
- Output: `./final_animation.mp4`

## Configurable Settings (top of script)

| Setting | Default | Description |
|---------|---------|-------------|
| `COMPOSITE_MAX_WORKERS` | `5` | Max parallel composite jobs |
| `VIDEO_MAX_WORKERS` | `5` | Max parallel video jobs |
| `VIDEO_ASPECT_RATIO` | `"landscape"` | `"landscape"`, `"portrait"`, or `"square"` |
| `VIDEO_N_FRAMES` | `"10"` | Number of frames (controls clip length) |
| `VIDEO_REMOVE_WATERMARK` | `True` | Remove kie.ai watermark from output |
| `POLL_INTERVAL` | `5` | Seconds between status polls |
| `MAX_POLLS` | `120` | Max polls per task (120 × 5s = 10 min timeout) |

## API Reference

Both phases use the same kie.ai Jobs API:

| Step | Method | Endpoint | Key params |
|------|--------|----------|------------|
| Composite submit | POST | `/jobs/createTask` | model: `flux-2/pro-image-to-image`, `input_urls`, `aspect_ratio: 16:9` |
| Composite status | GET  | `/jobs/recordInfo?taskId=` | poll until `state: success` |
| Video submit     | POST | `/jobs/createTask` | model: `sora-2-image-to-video`, `image_urls`, `aspect_ratio`, `n_frames`, `remove_watermark` |
| Video status     | GET  | `/jobs/recordInfo?taskId=` | poll until `state: success` |

Base URL: `https://api.kie.ai/api/v1/...`

## Regenerating Failed or Rejected Shots

1. Delete `./composites/{shot_id}.png` and `./clips/{shot_id}.mp4`
2. Optionally update `veo_prompt` in `shots.json`
3. Re-run the script

## Review Gate (MANDATORY)

### Per-shot mode — after EACH shot

After each `--shot` run completes, present this EXACTLY:

```
🎬 Shot [shot_XXX] ready!

- Composite : ./composites/shot_XXX.png
- Video clip: ./clips/shot_XXX.mp4
- Run time  : [X min]

👉 Please review this clip. You can:
  - Approve → say "ok" or "next" to generate the next shot
  - Redo    → say "redo" (deletes composite + clip, re-runs same shot)
  - Adjust  → edit veo_prompt in shots.json, then say "redo"

⏸️ Waiting for your approval before generating shot_[next].
```

Only run the next `--shot` after explicit user approval.

### Bulk mode — after ALL shots

```
✅ Composite + Video Generation complete!

📋 Summary:
- Composite images: [X] → ./composites/
- Video clips: [X] → ./clips/
- Failed: [X] (list any failures)
- Total run time: [X min]

👉 Please review the clips. You can:
  - Approve all → say "approved" or "merge" to proceed to final merge
  - Regenerate specific shots → e.g., "redo shot_003"
    (delete composites/shot_003.png + clips/shot_003.mp4, re-run)

⏸️ Waiting for your approval before merging.
```

### Phase 3 (merge) — after clips are approved

Run `merge_clips.py` and present:

```
🎬 Final animation ready!

- Output : ./final_animation.mp4
- Size   : [X] MB
- Clips  : [X] merged in shot order

⏸️ The Story-to-Animation pipeline is complete. Please review final_animation.mp4.
```

**NEVER** mark the pipeline as complete without explicit user approval of the final merged video.
