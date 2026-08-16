# Skill 1 stage — Patch mode

*Load when a prior spec is attached and the user wants it modified. Carries pre-flight
extraction, the easy/hard change taxonomy, the cascade-impact algorithm, and patch-mode iron
rules.*

*The cascade algorithm is the load-bearing part: a hard change silently invalidating
`[detailed]` content is the failure mode this mode exists to prevent, which is why every
reset is surfaced and confirmed before it is applied.*

## Table of contents

- [Pre-flight: extract from existing spec](#41-pre-flight-extract-from-existing-spec)
- [Surface current state](#42-surface-current-state)
- [Elicit change](#43-elicit-change)
- [Classify the change](#44-classify-the-change)
- [Compute cascade impact](#45-compute-cascade-impact-hard-changes-only)
- [Apply the change](#46-apply-the-change)
- [Output](#47-output)
- [Patch-mode iron rules](#48-patch-mode-iron-rules)

---

### 4.1 Pre-flight: extract from existing spec

Skill 1 must extract the following. If any extraction fails (header missing, unrecognizable format), report what couldn't be extracted and refuse to enter patch mode — instruct the user to fix the spec or restart greenfield.

| Source | Extracts |
|---|---|
| `## 1. Bot Identity` | bot name, primary language, channel scope, account ID, model config (catalog name or raw IDs) |
| `## 2. Persona Bundle` (subsections 2.1–2.5) | each `prompts` field — body text only. Channel-default provenance lives in §7.7, not in these bodies (v1.20.2) |
| `## 3. Caller Silence Behavior` | the silence failover intent + 4 silence fields (always populated — section 3 is never `[not configured]` from v1.11.0 onward) |
| `## 4. Intent List (Structural)` — per `### Intent N: <identifier>` | identifier, display name, description, tool name, RT, hard-intent flag, transitions out (ordered), escalation target, slots, RT-specific fields |
| `## 4.5 Available Variables` (subsections 4.5.1–4.5.4) | each variable inventory |
| `## 5. Intent Details` — per `### Intent: <identifier>` | the `**Status:**` marker (`[structural]`, `[detailed]`, `[detailed-revisit]`) |
| `## 7. Generation Metadata` | 7.4 unknowns, 7.5 pending |

This is **not** a full strict-template parse (that's Skill 3's responsibility). Skill 1 needs only enough extraction to operate the patch workflow.

### 4.2 Surface current state

Brief summary:

```
Bot: <name> (<primary language>)
Channels: <voice|chat|voice+chat>
Intents: <total>; status breakdown — <structural N> / <detailed M> / <detailed-revisit K>
Hard intents: <count>; identifiers <list>
Open unknowns: <count from 7.4>
```

### 4.3 Elicit change

"What do you want to change?" Plain language. No template required.

### 4.4 Classify the change

**Easy-change taxonomy** (no detailed-intent reset):

- Edit `prompts.persona` (section 2.1 only)
- Edit `prompts.voiceInstructions` or `prompts.chatInstructions`
- Edit `prompts.openingAnnouncement` — Checks 16–17 re-run after the patch (as always); if the closing question changed, offer a §2.4 first-step alignment edit in the same patch so the opening behavior still consumes the answer
- Edit non-structural intent metadata (display name, description, priority, max attempts, validation timeout)
- Add a new intent (enters as `[structural]`; existing intents untouched)
- Rename an intent identifier — Skill 1 updates all transition refs and Mustache refs; existing `[detailed]` content stays since the underlying logic is unchanged
- Edit caller-silence configuration
- Edit channel scope from one channel to two (newly-active channel gets templated defaults)
- Edit the §4.5.5 CustomData key list (v1.13.0) — re-run Check 8 after the edit; note that CHK-07 re-validates every `{{reference}}` at assembly
- Edit the §1 limit fields (Daily limit / layers / sentences / IVRLayerSelect_2) (v1.13.0)
- Edit the §1 `Negative instructions` field (v1.16.0)
- Edit `**Sensitive:**` / `**Max turns:**` / `**Max turns sentence:**` / `**IsSilenceIntent:**` on an intent (v1.14.0) — re-run Checks 23/24 after the edit

**Hard-change taxonomy** (cascade reset required — see 4.5):

- Change an intent's Response Type
- Modify an intent's slots (add, remove, reorder, retype)
- Delete an intent
- Modify the transition graph beyond simple reordering
- Edit `prompts.intentInstructions` (bot-level) routing destinations — alignment with the §2.5 opening question is re-verified by Check 17
- Change channel scope from two channels to one
- Change an intent's `**Terminal outcome:**` (slot, value, or value mode) (v1.13.0) — the terminal's Skill-2 outcome-value validationPrompt must be redone
- Change an intent's `**Captures answer to:**` / `**Asks next:**` (v1.13.0) — the staggering couples intent N's announcement to intent N+1's capture, so BOTH neighbors' Skill-2 content is affected; add the previous and next flow intents to the cascade's affected_set

If the change spans both categories: classify as hard.

### 4.5 Compute cascade impact (hard changes only)

```
affected_set = { directly_modified_intent }

REPEAT until no change in affected_set:

  FOR each intent I in section 5 (regardless of status):

    # Skill-2-territory references — only inspectable on [detailed] / [detailed-revisit]:
    IF I.status IN { [detailed], [detailed-revisit] }:
      IF I.validationPrompt text references any field of any intent in affected_set:
        add I to affected_set
      IF I.intentInstructions text references any transition involving any intent in affected_set:
        add I to affected_set

    # Skill-1-territory references — inspectable on any RT=2 intent regardless of status:
    IF I.RT == 2:
      IF I's body, headers, OR response_shape references any slot owned by an intent in affected_set:
        add I to affected_set

For each intent in affected_set (excluding the directly-modified one):
  IF status == [detailed]: set to [detailed-revisit]
  IF status == [structural]: leave as [structural] (it has nothing to invalidate)
  IF status == [detailed-revisit]: leave as [detailed-revisit]

For the directly-modified intent itself:
  IF the change is a hard structural change to its own definition: set status to [detailed-revisit] if it was [detailed], else leave.
```

Surface to user:

> "This change affects the following intents: `[A, B, C]`. Of those, `[A, B]` reset from `[detailed]` to `[detailed-revisit]` (you'll redo their detailing in Skill 2). `[C]` stays `[structural]` (no detailing existed yet)."

Then prompt via `AskUserQuestion` per Section 2.4.B (header: "Apply patch?", 2 options: "Apply with cascade *(Recommended)*" / "Cancel"). If the user picks Cancel: do not apply.

### 4.6 Apply the change

- Edit affected fields in sections 1, 2, 3, 4, 4.5, or section 5 stubs as the change requires.
- Update intent statuses per the algorithm.
- Re-run iron rules against the modified spec — same as greenfield close-out:
  - Persona-claims-vs-intents (§14.3.7): if a deletion removed an intent that the persona claimed, surface inconsistency.
  - Escalation-transition existence (§14.3.4): if a deletion broke an escalation path, surface and ask for a replacement.
- Update section 6 cross-references (regenerate from sections 4-5).
- **Regenerate section 6.6** (intent flow diagram) per §3.6.1.
- Append to section 7.3: a log entry summarizing the patch.
- Update section 7.4 and 7.5.

### 4.7 Output

- Run the **self-validation checklist** (Section 5 of this SKILL.md).
- **Show updated flow diagram + offer refinement loop** per §3.6.1. Render section 6.6 alongside the cascade summary so the user can see the structural impact of the patch visually before final emission. Prompt via `AskUserQuestion` per Section 2.4.B (header: "Diagram review", 4 options: "Looks good — finalize *(Recommended)*" / "Adjust an intent" / "Adjust a transition" / "Adjust persona / opening behavior"). On any "Adjust" pick: route back to §4.3 with the new change request, re-run the cascade analysis (§4.5), regenerate sections 6 and 6.6, re-validate. Same 5-iteration cap as greenfield.
- Emit per runtime:
  - Single-conversation: produce the modified spec as the response message.
  - Claude Code: write the modified spec back to `agent-spec.md`.
- Confirm the patch is applied and section 7.3 has the new entry.

### 4.8 Patch-mode iron rules

- Never discard `[detailed]` content silently. Every reset is explicit and confirmed in 4.5.
- Never invent values to fill gaps introduced by a deletion. Mark `<UNKNOWN>` and surface in 7.4.
- Never create or modify intent content that's Skill 2's territory (`validationPrompt`, post-execution `intentInstructions`).

---
