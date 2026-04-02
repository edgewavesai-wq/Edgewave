---
name: higgsfield-generate-video-script
description: >
  Takes a user's video idea, concept, or topic and expands it into a full
  structured video script saved as video_script.md. Covers narration, scene
  descriptions, on-screen action, and tone for each segment. Part of the
  Higgsfield Video Generation workflow (Step 1 of 3). After generating
  video_script.md, ALWAYS present the output and wait for explicit user approval.
  Do NOT automatically trigger the next pipeline step.
---

# Video Script Generation

Expand a user-provided idea, concept, or topic into a structured video script
saved as `video_script.md`.

## Instructions

1. Analyze the user's idea: identify the genre, tone, target audience, message,
   and desired emotional impact.
2. Expand into **5–12 scenes** targeting a total video length of 30 seconds to
   2 minutes (each scene maps to a ~5–10 second video clip).
3. Each scene must include:
   - **Scene number and title**
   - **Duration**: suggested clip length in seconds (5–10 s)
   - **Narration / Voiceover**: spoken words or text overlay (if any)
   - **On-screen action**: clear visual description of what happens
   - **Setting**: location, environment, time of day, atmosphere
   - **Camera**: suggested shot type and movement (wide, close-up, pan, dolly, etc.)
   - **Mood**: emotional tone and pacing note
4. Write for video generation: be visually descriptive and action-oriented.
   Avoid abstract concepts — describe only what can be *seen* on screen.
5. Keep a consistent visual style throughout (e.g. cinematic, documentary,
   product showcase, social-media reel, etc.).

## Output Format

Save as `video_script.md` in the project directory:

```markdown
# [Video Title]

## Concept
[Original user idea]

## Style
[Visual style, tone, target audience]

## Total Estimated Duration
[X scenes × avg Y sec ≈ Z seconds]

---

## Scene 1: [Scene Title]
**Duration**: X seconds
**Setting**: [Detailed visual environment]
**Camera**: [Shot type and movement]
**Action**: [What is happening on screen]
**Narration**: "[Spoken line or text overlay, or leave blank]"
**Mood**: [Emotional tone]

---

## Scene 2: ...
```

## Review Gate (MANDATORY)

After saving `video_script.md`, present this EXACTLY:

```
✅ Video Script Generation complete. Output saved to video_script.md.

📋 Summary:
- Title: [Video Title]
- Style: [Visual style]
- Scenes: [X]
- Estimated duration: [X seconds (~X min)]

👉 Please review video_script.md. You can:
  - Approve as-is → say "approved" or "proceed"
  - Request changes → describe what to modify
  - Edit video_script.md directly → tell me when done

⏸️ Waiting for your approval before generating scene prompts.
```

**NEVER** proceed to the next skill automatically. Wait for explicit approval.

Approval keywords: `approved`, `approve`, `looks good`, `proceed`, `next step`,
`go ahead`, `continue`, `LGTM`, `ship it`, `all good`, `move on`, `next`

If changes requested: apply them, summarize what changed, ask for approval again.
