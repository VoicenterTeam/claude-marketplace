# Skill: `voicenter-bot-spec-designer`

Design the structural skeleton of a Voicenter Bot through a guided interview. Skill 1 in the three-skill pipeline.

> Source: [`plugins/voicenter-bot-builder/skills/voicenter-bot-spec-designer/SKILL.md`](../../../plugins/voicenter-bot-builder/skills/voicenter-bot-spec-designer/SKILL.md)
> Plugin: [voicenter-bot-builder](../../plugins/voicenter-bot-builder.md) · Pipeline phase: **1 / 3**

---

## What it does

Produces the **structural skeleton** of an Agent Spec markdown file by interviewing the user. The output, `agent-spec.md`, is the shared artifact the entire pipeline operates on.

Skill 1 fills these spec sections:

| Section | Content |
|---|---|
| 1. Bot Identity | Name, identifier, description, account ID, language, channels, voice, model |
| 2. Persona Bundle | `persona`, voice/chat instructions, opening behavior, opening announcement |
| 3. Caller Silence Behavior | The 4 silence fields, or `[not configured]` |
| 4. Intent List (Structural) | One row per intent — identifier, RT, transitions, slots, RT-specific fields |
| 4.5 Available Variables | Call-context, environment, slot, and API-response variable inventories |
| 5. Intent Details | **Stubs only**, marked `[structural]`. Skill 2 fills the rest. |
| 6. Cross-References | Initial pass — Mustache usage, transition graph, escalation paths, ID placeholders |
| 7. Generation Metadata | Spec version, schema reference, generation log, open unknowns, pending work |

Skill 1 explicitly does **not** author per-intent language content (slot validation prompts, post-execution intent instructions, RT-specific announcements) — that's Skill 2's territory. It also does not emit wire-format JSON — that's Skill 3.

---

## When to invoke

- A user wants to **design a new Voicenter bot from scratch** ("design a bot", "create an agent spec", "build a Voicenter bot").
- A user wants to **modify an existing bot** ("patch this bot", "add an intent", "rename the bot's persona", "change the flow graph").
- A user wants to **scope a bot before writing intent content** — Skill 1 produces a complete structural picture before any language work happens.

Trigger phrases the skill responds to: *"design a bot"*, *"create an agent spec"*, *"build a Voicenter bot"*, *"patch this bot"*, *"add an intent"*, *"change the bot's persona"*, *"modify the flow graph"*, or any reference to *"Skill 1"* / *"Agent Spec Designer"*.

---

## Two entry modes

| Mode | Trigger | Behavior |
|---|---|---|
| **Greenfield** | No spec attached | Runs the 4-phase interview from a blank state |
| **Patch** | An `agent-spec.md` is attached or present in the workspace | Extracts current state, asks what to change, applies the change with cascade analysis |

Skill 1 detects the mode automatically and states it to the user. The user can override (forced greenfield with an existing spec attached requires explicit confirmation that prior content will be discarded).

---

## Greenfield mode — four phases

### Phase 1 — Identity, Channels, Model, Caller-silence

Captures section 1 + section 3:

1. **Bot name** (free text, often Hebrew)
2. **Identifier** (snake_case ASCII; used as the JSON filename prefix by Skill 3 — defaults to a snake_cased Bot Name when ASCII)
3. **Description**
4. **Customer Account ID** (or `<UNKNOWN: Account ID>`)
5. **Primary language** (BCP-47, e.g., `he-IL`)
6. **Channel scope** (voice / chat / voice+chat)
7. **Voice name** (catalog name or any provider-supported string)
8. **AI model config** (catalog name → IDs, or raw IDs)
9. **Caller silence** — yes (4 fields) or no (`[not configured]`)

### Phase 2 — Persona Bundle

Captures section 2 (the 5-field `prompts` bundle):

- `persona` — identity, role, tone, language, hard constraints
- `voiceInstructions` — pacing, pronunciation, interruption handling
- `chatInstructions` — formatting, message length, emoji policy
- `intentInstructions` — bot-level opening behavior in Conversation Routines style
- `openingAnnouncement` — the first audible message at pickup

Iron rules enforced during this phase:

- No channel-specific behavior in `persona` (move voice-isms / chat-isms to the right field)
- No per-intent procedural logic in `persona` (defer to Skill 2)
- No persistent policy embedded in single intents (move to `persona`)

For inactive channels, Skill 1 emits templated defaults from `templates/voice-default.md` or `templates/chat-default.md`, marked `[default — not user-authored]`.

### Phase 2 / 3 boundary — Deep Research nudge

If the transcript triggers any of the four cues in `trigger-detection-rules.md`, Skill 1 offers a Deep Research query the user can run separately and return with findings. The nudge is **opt-in** — the user can skip and proceed.

### Phase 3 — Flow Graph and Intent List

Captures section 4 (intent rows) and section 4.5 stubs (call-context, environment, API-response variables):

- Elicit the happy path
- Expand fallbacks for each non-terminal intent
- Per-intent capture: identifier (snake_case verb_object), display name, description, RT (1/2/3/4), transitions out (ordered), hard-intent flag

**Hard-intent criteria** — flag the intent as hard if any one applies:

- RT=2 with more than 3 slots
- Conditional post-execution branching (multiple distinct next-intents driven by API response)
- More than 4 outgoing transitions
- Slots requiring complex validation (multi-step, cross-slot dependencies)

### Phase 4 — Per-intent structural fields

Finalizes section 4 entries with per-RT specifics, generates section 4.5.3 (slot variables), runs an advisory Mustache pre-check, and creates section 5 stubs.

Per-RT capture:

| RT | Required fields |
|---|---|
| 1 (Layer transfer) | `Layer:` (int) |
| 2 (External API) | `URL:`, `Method:`, `Headers:`, `Body:`, `API silence behavior:` (six sub-fields) |
| 3 (Conversational) | (none beyond slots — RT=3 fields are language-heavy, Skill 2 territory) |
| 4 (Outbound dial) | `Dial source:` (parameter or static), then `Parameter phone:` OR `Phone1/2/3:`, plus `selectdial_option:`, `NEXT_VO_ID:`, `MAX_DIAL_DURATION:`, `Record:`, optional `Announcement:` / `Loading announcement:` / `Post-execution intent instructions:`, and `Response success:` |

The RT-specific sub-labels are **bold** in the spec — Skill 3's strict-template parser depends on this exact form. See [Skill 3's parser](../voicenter-bot-json-assembler/README.md#strict-template-parser) for the full grammar.

---

## Patch mode

Used when the user wants to modify an existing spec.

**Easy changes** (no detailed-intent reset):

- Edit persona / voiceInstructions / chatInstructions / openingAnnouncement
- Edit non-structural intent metadata (display name, description)
- Add a new intent (enters as `[structural]`)
- Rename an intent identifier (transition refs and Mustache refs auto-update)
- Edit caller-silence configuration
- Expand channel scope (newly-active channel gets templated defaults)

**Hard changes** (cascade reset to `[detailed-revisit]` for affected intents):

- Change an intent's Response Type
- Modify slots (add, remove, reorder, retype)
- Delete an intent
- Modify the transition graph beyond simple reordering
- Edit bot-level opening behavior routing destinations
- Reduce channel scope from two channels to one

The cascade algorithm walks both Skill-1-territory references (RT=2 body / headers / response-shape inheritance) and Skill-2-territory references (validation prompts and post-execution instructions in `[detailed]` intents). Affected `[detailed]` intents reset to `[detailed-revisit]`; affected `[structural]` intents stay `[structural]`. The user confirms the cascade list before any change applies.

---

## Self-validation checklist

Run on every greenfield close-out and after every patch. 10 checks, executed in order:

| # | Check | Severity |
|---|---|---|
| 1 | Persona articulates identity, role, tone, language | Blocking |
| 2 | No channel-specific content in persona | Blocking |
| 3 | No per-intent procedural logic in persona | Blocking |
| 4 | No persistent policy embedded in single intents | Blocking |
| 5 | Persona's claimed capabilities ⊆ intent set | Blocking |
| 6 | snake_case verb_object naming on all intents | Blocking |
| 7 | Every non-terminal intent has an escalation transition | Blocking |
| 8 | Mustache references resolve against section 4.5 + section 5 slots | Advisory |
| 9 | Active-channel `prompts` fields populated | Blocking |
| 10 | Inactive-channel `prompts` have templated defaults marked | Auto-fix |

Blocking failures pause the close-out until the user resolves them. Advisory check #8 records the user's resolution to section 7.3 and continues — Skill 3's check is the authoritative blocking version.

---

## Output contract

**On greenfield completion:**

- Sections 1, 2, 3, 4, 4.5 fully filled
- Section 5: stub entries per intent, all marked `[structural]`
- Section 6: initial cross-references (subsections 6.1–6.5)
- Section 7: spec version, schema reference, generation log entry, unknowns aggregation, pending work

**On patch completion:**

- The modified spec
- Affected intents marked `[detailed-revisit]` (or stay `[structural]`)
- Section 6 regenerated
- Section 7.3 has a new log entry summarizing the patch
- Sections 7.4 and 7.5 updated

### Runtime-specific delivery

| Runtime | Output |
|---|---|
| **Single-conversation** | Full spec returned as the assistant message; handoff hint recommends Skill 2 next |
| **Claude Code** | Spec written to `agent-spec.md` in the workspace; handoff hint recommends Skill 2 |

---

## Soft-cap thresholds

Advisory warnings emitted at greenfield close-out, after intent count is final. No hard refusal at any size — user decides.

| Runtime | Silent | Advisory | Warning |
|---|---|---|---|
| Single-conversation | < 6 | 7–8 | > 8 (consider Claude Code) |
| Claude Code | < 12 | 12–20 | > 20 (consider splitting bot) |

---

## Anti-list — what Skill 1 does NOT do

- Write `validationPrompt` text (Skill 2's territory)
- Write per-intent post-execution `intentInstructions` text (Skill 2's territory)
- Write detailed slot descriptions beyond name + minimum identification
- Run the §15.4 cross-reference pass (Skill 3's territory)
- Emit any wire-format JSON (Skill 3's territory)
- Make creative decisions in patch mode beyond what the user describes
- Discard `[detailed]` content silently — every reset is explicit and confirmed
- Validate the bot at runtime — no testing, no simulation, no behavior check
- Query the Voicenter platform for live data — the model catalog is hardcoded

---

## Common pitfalls

- **Hebrew bot names without an Identifier.** Skill 3's filename rule reads section 1 `**Identifier:**`. Pre-v1.0 specs that lack the field fall back to ASCII-folding `**Bot Name:**`, and for Hebrew names that fallback fails → filename becomes `bot-bot-<date>.json`. Skill 1 always asks for an identifier explicitly.
- **Generic "helpful assistant" personas.** Skill 1 blocks at Check 1. Push the user toward concrete identity, role, tone, and language assertions.
- **Voice-isms inside `persona`.** Skill 1 blocks at Check 2 and offers to move them to `voiceInstructions`. Don't argue — accept the move.
- **`<UNKNOWN: ...>` markers used loosely.** They aggregate into section 7.4 and become Skill 3 sentinel entries the user must resolve at import time. Use them deliberately.

---

## Related skills

- [voicenter-bot-intent-detail-author](../voicenter-bot-intent-detail-author/README.md) — Skill 2; runs after Skill 1 with the section 5 stubs as input.
- [voicenter-bot-json-assembler](../voicenter-bot-json-assembler/README.md) — Skill 3; runs after Skill 2 once every intent is `[detailed]`.
