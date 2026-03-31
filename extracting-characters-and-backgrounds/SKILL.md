---
name: extracting-characters-and-backgrounds
description: >
  Reads story.md and extracts all unique characters and background locations.
  Generates detailed Pixar-style 3D image-generation prompts for each, saving
  them as characters.json and backgrounds.json. Part of the Story-to-Animation
  pipeline (Step 2 of 5). Use when story.md exists and the user wants to prepare
  character and background prompts for AI image generation. After generating
  both JSON files, ALWAYS present the output and wait for explicit user approval.
  Do NOT automatically trigger the next pipeline step.
---

# Character & Background Extraction

Parse `story.md` to extract unique characters and locations, then write detailed
image-generation prompts. Save as `characters.json` and `backgrounds.json`.

## Instructions

### Characters

1. Identify every unique character mentioned across all scenes.
2. For each, generate a detailed image prompt covering:
   - Physical appearance (age, build, skin tone, hair, eyes)
   - Clothing and accessories (era/setting-appropriate)
   - Expression and pose (neutral, full body, for reference sheet)
   - Art style suffix: `"3D animated character, Pixar-style rendering, full body, character reference sheet, white background, high detail, soft lighting"`
3. Assign IDs sequentially: `char_001`, `char_002`, ...
4. Record which scene numbers each character appears in.

### Backgrounds

1. Identify every unique location across all scenes.
2. Deduplicate: same location across multiple scenes = same `bg_id`.
3. For each, generate a detailed image prompt covering:
   - Environment type (interior/exterior)
   - Architectural or natural details
   - Lighting conditions and time of day
   - Mood and atmosphere
   - Art style suffix: `"3D animated environment, cinematic wide shot, no characters, high detail, Pixar-style rendering"`
4. Assign IDs sequentially: `bg_001`, `bg_002`, ...
5. Record which scene numbers each background appears in.

## Output Files

### characters.json
```json
{
  "characters": [
    {
      "character_id": "char_001",
      "name": "Character Name",
      "description": "Brief one-line description",
      "prompt": "Full detailed image-generation prompt...",
      "scenes_appearing": [1, 2, 3]
    }
  ]
}
```

### backgrounds.json
```json
{
  "backgrounds": [
    {
      "bg_id": "bg_001",
      "name": "Location Name",
      "description": "Brief one-line description",
      "prompt": "Full detailed image-generation prompt...",
      "scenes_used_in": [1, 5, 7]
    }
  ]
}
```

## Review Gate (MANDATORY)

After saving both JSON files, present this EXACTLY:

```
✅ Character & Background Extraction complete.

📋 Summary:
- Characters extracted: [X] → saved to characters.json
  [char_001: "Name", char_002: "Name", ...]
- Backgrounds extracted: [X] → saved to backgrounds.json
  [bg_001: "Name", bg_002: "Name", ...]

👉 Please review both JSON files. Key things to check:
  - Are all characters from the story captured?
  - Are the image-generation prompts detailed enough?
  - Are all unique locations identified (no duplicates, no missing)?
  - Do the art style directives match your vision?

You can:
  - Approve both files → say "approved" or "proceed"
  - Request changes → e.g., "make Luna's hair blonde", "add detail to bg_002"
  - Edit the JSON files directly → tell me when done

⏸️ Waiting for your approval before generating images.
```

**NEVER** proceed to the next skill automatically. Wait for explicit approval.

Allow iterative refinement — update JSON, summarize changes, ask for approval again.
