---
name: generating-story-from-logline
description: >
  Expands a short story logline or premise into a full structured narrative
  screenplay saved as story.md. Use when the user provides a story idea,
  logline, or premise and wants to generate a complete story with scenes,
  characters, dialogue, and visual descriptions for 3D animation production.
  Part of the Story-to-Animation pipeline (Step 1 of 5). After generating
  story.md, ALWAYS present the output and wait for explicit user approval.
  Do NOT automatically trigger the next pipeline step.
---

# Story Generation

Expand a user-provided logline into a structured animation screenplay saved as `story.md`.

## Instructions

1. Analyze the logline: identify genre, tone, conflict arc, and resolution.
2. Expand into **8–15 scenes** (targets ~3–5 minutes at ~8 sec/shot).
3. Each scene must include:
   - **Scene number and title**
   - **Location**: detailed visual description (used for background image generation)
   - **Characters present**: with brief visual descriptions on first appearance
   - **Action and dialogue**: visual storytelling focus (show, don't tell)
   - **Shot Notes**: suggested camera angles/movements (wide, close-up, tracking, etc.)
   - **Tone/Pacing**: emotional beat
4. Write for 3D animation: visually descriptive and action-oriented.
5. Keep character count manageable (3–6 main characters).

## Output Format

Save as `story.md` in the project directory:

```markdown
# [Story Title]

## Logline
[Original logline]

## Characters
- **Name**: Brief description (age, appearance, personality)

## Scene 1: [Scene Title]
**Location**: [Detailed visual setting description]
**Characters**: [Characters present]
**Time of Day**: [Morning/Afternoon/Night]

[Narrative action and dialogue]

**Shot Notes**: [Camera angles and movements]
**Tone**: [Emotional beat]

---

## Scene 2: ...
```

## Review Gate (MANDATORY)

After saving `story.md`, present this EXACTLY:

```
✅ Story Generation complete. Output saved to story.md.

📋 Summary:
- Title: [Story Title]
- Scenes: [X]
- Characters introduced: [list names]
- Estimated animation length: [X scenes × ~8 sec/shot ≈ X seconds]

👉 Please review story.md. You can:
  - Approve as-is → say "approved" or "proceed"
  - Request changes → describe what to modify
  - Edit story.md directly → tell me when done

⏸️ Waiting for your approval before extracting characters and backgrounds.
```

**NEVER** proceed to the next skill automatically. Wait for explicit approval.

Approval keywords: `approved`, `approve`, `looks good`, `proceed`, `next step`,
`go ahead`, `continue`, `LGTM`, `ship it`, `all good`, `move on`, `next`

If changes requested: apply them, summarize what changed, ask for approval again.
