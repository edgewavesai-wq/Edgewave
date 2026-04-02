---
name: higgsfield-generate-scene-prompts
description: >
  Reads video_script.md and converts each scene into structured image and video
  generation prompts. Saves output as scenes.json. Each scene entry contains a
  fully self-contained image_prompt (for reference frame generation) and a
  video_prompt (fed directly to Higgsfield for video generation). Part of the
  Higgsfield Video Generation workflow (Step 2 of 3). Use when video_script.md
  exists and the user wants to prepare prompts for Higgsfield. After generating
  scenes.json, ALWAYS present the output and wait for explicit user approval.
  Do NOT automatically trigger the next pipeline step.
---

# Scene Prompt Generation

Parse `video_script.md` and produce two high-quality AI generation prompts per
scene: an `image_prompt` for a reference thumbnail and a `video_prompt` for
Higgsfield video generation. Save as `scenes.json`.

## Instructions

### For each scene in video_script.md:

1. **scene_id**: sequential identifier (`scene_001`, `scene_002`, ...)
2. **scene_number**: integer scene number
3. **title**: scene title from the script
4. **duration_seconds**: as specified in the script (5–10 s)
5. **aspect_ratio**: `"16:9"` (default), `"9:16"` for vertical/reels, or
   `"1:1"` for square — infer from the script's style or default to `"16:9"`

### image_prompt

A detailed still-frame prompt describing the key visual of the scene for an
image generation model. Must include:

- Subject / main focus (person, object, landscape, etc.)
- Setting and environment (location, time of day, lighting)
- Composition (camera angle: wide shot, close-up, aerial, etc.)
- Visual style (cinematic, photorealistic, commercial, etc.)
- Colour grade / mood (warm golden tones, cool blue desaturated, etc.)
- Quality tags: `"high resolution, sharp focus, professional photography"`

Pattern:
```
[Shot type], [subject and action], [environment], [lighting], [style],
[mood], [quality tags]
```

Example:
```
Wide establishing shot, a sleek electric car parked on an empty coastal highway
at sunrise, dramatic orange sky reflecting off the glossy bodywork, soft lens
flare, cinematic commercial photography, confident and aspirational mood,
high resolution, sharp focus
```

### video_prompt

A fully self-contained, motion-aware prompt fed directly to Higgsfield. Must
include:

- Camera movement (slow dolly-in, aerial pull-back, tracking shot, static,
  smooth pan, etc.)
- Subject action / motion description
- Setting with temporal detail (lighting change, wind, water, etc.)
- Visual style consistent with the overall video
- Duration hint matching the scene's `duration_seconds`

Pattern:
```
[Camera movement], [subject + motion], [environment + dynamic elements],
[lighting and atmosphere], [visual style], [duration hint]
```

Example:
```
Slow dolly-in from wide to medium shot, a sleek electric car glides silently
along a coastal highway at sunrise, golden light spreads across the ocean horizon,
lens flare flickers on the windshield, cinematic commercial style, 6 seconds
```

**Key rules:**
- Do NOT reference other scene IDs or asset IDs — every prompt must stand alone.
- Use motion verbs: glides, pulses, emerges, sweeps, drifts, expands, zooms, etc.
- Match the mood and visual style from `video_script.md` consistently.
- For scenes with dialogue/narration, include the visual action only (not the
  spoken words) in the video prompt.

## Output File: scenes.json

```json
{
  "video_title": "Title from video_script.md",
  "visual_style": "Overall style description",
  "scenes": [
    {
      "scene_id": "scene_001",
      "scene_number": 1,
      "title": "Scene title",
      "duration_seconds": 6,
      "aspect_ratio": "16:9",
      "narration": "Spoken line or text overlay, or empty string",
      "action_summary": "One-line summary of what happens",
      "image_prompt": "Full detailed still-frame image generation prompt...",
      "video_prompt": "Full self-contained Higgsfield video generation prompt..."
    }
  ]
}
```

## Review Gate (MANDATORY)

After saving `scenes.json`, present this EXACTLY:

```
✅ Scene Prompt Generation complete. Output saved to scenes.json.

📋 Summary:
- Video title: [Title]
- Total scenes: [X]
- Estimated duration: [sum of duration_seconds] seconds (~X min)
- Aspect ratio: [most common ratio used]

Scenes overview:
  [scene_001: "Title" — X s]
  [scene_002: "Title" — X s]
  ...

👉 Please review scenes.json. Key things to check:
  - Are video_prompts detailed, motion-aware, and fully self-contained?
  - Are image_prompts visually consistent across scenes?
  - Are durations realistic for each scene's action?
  - Does the overall style match your vision?

You can:
  - Approve → say "approved" or "proceed"
  - Request changes → e.g., "make scene_003 more dramatic", "change aspect ratio to 9:16"
  - Edit scenes.json directly → tell me when done

⏸️ Waiting for your approval before generating videos with Higgsfield.
```

**NEVER** proceed to the next skill automatically. Wait for explicit approval.

Allow iterative refinement — update prompts, durations, or style as needed.
