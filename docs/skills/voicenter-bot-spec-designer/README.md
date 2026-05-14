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

## Tool conventions used during the interview

Two tool patterns apply throughout greenfield and patch flows (full detail in SKILL.md §2.4):

**A. Live resource lookup via `voicenter-mcp.list_resources` (recommended default).** For Voicenter platform resources — **Customer Account ID** (Phase 1) and **RT=1 Layer ID** (Phase 4) — Skill 1's default is to call the [voicenter-mcp](../setup/README.md) plugin's `list_resources` tool (with `entityFilter: ["Accounts"]` or `["Layers"]`, `refresh: false`), display the returned list as an id+name table, and prompt via `AskUserQuestion`.

If MCP is unavailable, Skill 1 follows a **3-tier fallback** — never silently skipping to manual entry:

1. **Plugin not installed.** Surfaces this once and prompts via `AskUserQuestion`: *"Install and authenticate now (Recommended)"* or *"Continue with manual entry"*. If the user installs and authenticates, Skill 1 retries the `list_resources` call.
2. **Plugin installed but not authenticated** (OAuth not completed, token expired, or auth/connection error). Prompts via `AskUserQuestion`: *"Authenticate now (Recommended)"* or *"Continue with manual entry"*. If the user authenticates, Skill 1 retries.
3. **User declined or the retry still failed.** Falls back to **text-only mode** — captures the value as free text and uses `<UNKNOWN: …>` if the user doesn't know it. Logs once to section 7.3 with the reason. Skill 1 does not re-prompt for the same MCP step in the rest of the session — once the user opts out, that decision is respected.

The **model and voice catalogs** remain hardcoded in `model-catalog.md` — they are not fetched live.

**B. Menu prompts via `AskUserQuestion`.** Every closed-set choice the user makes during the interview is presented through `AskUserQuestion` — never plain free-text. The iron rule: if the user can answer with one of a fixed set of strings, route through `AskUserQuestion`. Free-text is reserved for genuinely open-ended fields (names, descriptions, free-form text content, integer/numeric values).

Concretely, this covers:

- **Setup** — runtime correction (Single-conversation vs Claude Code), mode override (Greenfield vs Patch), and the discard-existing-spec follow-up when forcing greenfield over an attached spec
- **Phase 1** — channel scope, voice name, AI model config, caller-silence yes/no, identifier ASCII-default confirmation
- **Phase 2** — every "Accept draft / Edit" prompt for `persona`, opening behavior, and opening announcement; "Accept template default / Override" for inactive channels
- **Phase 2/3 boundary** — pause vs skip Deep Research
- **Phase 3** — Response Type (RT=1/2/3/4); intent-name "Use suggestion / Propose alternative" when reject-and-suggest fires
- **Phase 4** — account selection (live list), layer selection (live list), POST vs GET, dial source (parameter vs static), per-slot `ParameterTypeId` (STRING / PHONE / BOOLEAN / ENUM / Other-fallback) and `IsRequired` (yes/no), RT=2 `silence` fallback intent reference (pick from the existing intent set), RT=4 `record` (yes/no), and the RT=4 rarity-warning confirmation
- **Patch mode §4.5** — cascade confirmation, plus every iron-rule re-prompt during patch
- **Self-validation checklist** — every "Move it?" / "Add one?" / "Add intent or trim persona?" / "Confirm or propose alternative?" / 3-way Mustache resolution prompt
- **§2.4.A MCP fallback** — Install / Authenticate / Continue manually

`AskUserQuestion` automatically adds an **Other** escape so the user can always type a custom value. Recommended options are listed first with *(Recommended)* appended to the label. Lists exceeding 4 items (the menu max) are first shown as a reference table, then prompted with the 3 most likely candidates plus **Other**.

---

## Greenfield mode — four phases

### Phase 1 — Identity, Channels, Model, Caller-silence

Captures section 1 + section 3:

1. **Bot name** (free text, often Hebrew)
2. **Identifier** (snake_case ASCII; used as the JSON filename prefix by Skill 3 — defaults to a snake_cased Bot Name when ASCII)
3. **Description**
4. **Customer Account ID** — Skill 1 calls `voicenter-mcp.list_resources` with `entityFilter: ["Accounts"]` to fetch the live account list, displays it, and prompts via `AskUserQuestion`. Falls back to free-text + `<UNKNOWN: Account ID>` if MCP is not connected.
5. **Primary language** (BCP-47, e.g., `he-IL`)
6. **Channel scope** — `AskUserQuestion` (voice / chat / voice+chat)
7. **Voice name** — `AskUserQuestion` over the `model-catalog.md` voice list; `Other` allows any provider-supported string
8. **AI model config** — `AskUserQuestion` over the `model-catalog.md` model list; `Other` allows raw `AIModelConfigID` + `AIModelTypeId`
9. **Caller silence** — `AskUserQuestion` (Yes → 4 silence fields / No → `[not configured]`)

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

Finalizes section 4 entries with per-RT specifics, generates section 4.5.3 (slot variables), runs an advisory Mustache pre-check, creates section 5 stubs, and (optionally) captures advanced overrides into section 4.7.

Per-RT capture:

| RT | Required fields |
|---|---|
| 1 (Layer transfer) | `Layer:` (int) — Skill 1 calls `voicenter-mcp.list_resources` with `entityFilter: ["Layers"]` and prompts via `AskUserQuestion` |
| 2 (External API) | `URL:`, `Method:` (`AskUserQuestion` POST/GET), `Headers:`, `Body:`, `API silence behavior:` (six sub-fields) |
| 3 (Conversational) | (none beyond slots — RT=3 fields are language-heavy, Skill 2 territory) |
| 4 (Outbound dial) | `Dial source:` (`AskUserQuestion` parameter/static), then `Parameter phone:` OR `Phone1/2/3:`, plus `selectdial_option:`, `NEXT_VO_ID:`, `MAX_DIAL_DURATION:`, `Record:`, optional `Announcement:` / `Loading announcement:` / `Post-execution intent instructions:`, and `Response success:` |

The RT-specific sub-labels are **bold** in the spec — Skill 3's strict-template parser depends on this exact form. See [Skill 3's parser](../voicenter-bot-json-assembler/README.md#strict-template-parser) for the full grammar.

#### Optional advanced features (§3.5.5 — default: skip, *not required*)

Two runtime features are **opt-in only** in v1 and not part of the default interview:

| Feature | Default | When opted-in |
|---|---|---|
| `ConditionGroupList` (conditional branching on `BotIntent` / `IntentRelated`) | Skill 3 emits `[]`; proc skips cleanly via NULL-guard in `CreateConditionGroups` | Captured under spec **§4.7 Advanced overrides** as a freeform `condition_groups:` block per intent or transition; Skill 3 passes through verbatim |
| `DTMFList` (DTMF keypad routing on `BotIntent` / `IntentRelated`) | Skill 3 omits the key; proc gates with `IS NOT NULL AND JSON_LENGTH > 0` | Captured under spec §4.7 as `dtmf_list:` block; Skill 3 emits a `DTMFList[]` sibling field |

After Phase 4 captures the structural intent set, Skill 1 prompts once via `AskUserQuestion` (header: "Advanced features", options: "Skip — accept defaults *(Recommended)*" / "Configure conditional branching" / "Configure DTMF routing"). The default-skip path is what every existing bot in the catalog uses. Skill 1 does not validate the contents of §4.7 — it's pass-through to Skill 3, which lifts the blocks verbatim into the JSON.

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
- **Section 6.6: Mermaid `flowchart TD` of the intent graph** — generated at close-out, shown to the user with a refinement loop, and embedded in the spec for human comprehension. Skill 3 ignores this section.
- Section 7: spec version, schema reference, generation log entry, unknowns aggregation, pending work
- Optional section 4.7: present iff the user opted in via §3.5.5 (advanced features)

**On patch completion:**

- The modified spec
- Affected intents marked `[detailed-revisit]` (or stay `[structural]`)
- Section 6 regenerated (including 6.6 — the diagram refreshes after every patch)
- Section 7.3 has a new log entry summarizing the patch
- Sections 7.4 and 7.5 updated

### Runtime-specific delivery

| Runtime | Output |
|---|---|
| **Single-conversation** | Full spec returned as the assistant message; handoff hint recommends Skill 2 next |
| **Claude Code** | Spec written to `agent-spec.md` in the workspace; handoff hint recommends Skill 2 |

### Intent flow diagram + refinement loop

Before final emission (and again after every patch), Skill 1 renders the bot as a **Mermaid `flowchart TD`** under spec section 6.6. Each intent is one node; transitions are labeled edges (`success` / `fallback` / `escalation`). Node shapes encode response type:

| RT | Mermaid shape |
|---|---|
| 1 (transfer) | stadium `([ ... ])` |
| 2 (API) | rounded rectangle `( ... )` |
| 3 (conversational) | default rectangle `[ ... ]` |
| 4 (outbound dial) | subroutine `[[ ... ]]` |

Hard intents get a ` ⚑` flag in the label. If section 4.7 declares `dtmf_list:` for a transition, the digits are appended to the edge label.

After rendering, Skill 1 prompts via `AskUserQuestion` (4 options: "Looks good — finalize *(Recommended)*" / "Adjust an intent" / "Adjust a transition" / "Adjust persona / opening behavior"). Any "Adjust" pick routes back to the relevant phase, applies the change, regenerates section 6 (including 6.6), re-runs validation, and re-prompts. The loop is capped at 5 iterations to prevent accidental endless cycles.

Section 6.6 is **for human comprehension only** — Skill 3 ignores it when projecting to JSON. The diagram refreshes automatically after every patch so the user can see the structural impact visually before finalizing.

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
- Query live data for the model catalog or voice catalog — both remain hardcoded in `model-catalog.md`. (Accounts and layers ARE fetched live via `voicenter-mcp.list_resources` — see the *Tool conventions* section above.)
- Capture `ConditionGroupList` or `DTMFList` as part of the default interview — these are **opt-in only** under spec §4.7. Default-skip emits the safe defaults that every existing bot uses; the proc imports cleanly without them.

---

## Common pitfalls

- **Hebrew bot names without an Identifier.** Skill 3's filename rule reads section 1 `**Identifier:**`. Pre-v1.0 specs that lack the field fall back to ASCII-folding `**Bot Name:**`, and for Hebrew names that fallback fails → filename becomes `bot-bot-<date>.json`. Skill 1 always asks for an identifier explicitly.
- **Generic "helpful assistant" personas.** Skill 1 blocks at Check 1. Push the user toward concrete identity, role, tone, and language assertions.
- **Voice-isms inside `persona`.** Skill 1 blocks at Check 2 and offers to move them to `voiceInstructions`. Don't argue — accept the move.
- **`<UNKNOWN: ...>` markers used loosely.** They aggregate into section 7.4 and become Skill 3 sentinel entries the user must resolve at import time. Use them deliberately.

---

## Compass doctrine integration

The bot-builder plugin includes a shared doctrine reference at `plugins/voicenter-bot-builder/references/voice-prompt-doctrine.md`, derived from the Gemini Live 3.1 voice agent engineering guideline. Skill 1 owns the structural self-validation checks for five doctrine rules from that catalog.

Checks 11–15 extend the self-validation checklist (see table above) and run at greenfield close-out and after every patch:

| # | Check | Doctrine rule | Severity |
|---|---|---|---|
| 11 | Bot-level prompt fields (`persona`, `voiceInstructions`, `intentInstructions`) authored in English only, even for non-English bots | Rule 3 — English operational | Advisory |
| 12 | Intent `description` fields authored in English | Rule 4 — Intent description in English | Advisory |
| 13 | Bot-level `prompts.intentInstructions` contains a language-lock guardrail (`NEVER infer language from caller name/accent/tone`) located in the final third (recency slot) of the field. | Rule 5 — Recency-slot language-lock guardrail | Advisory |
| 14 | `voiceInstructions` pacing/length directives do not contradict each other (e.g., "speak slowly" + "be concise and fast") | Rule 6 — Contradictory pacing/length | Advisory |
| 15 | `persona` and `intentInstructions` do not contain generic compliance boilerplate copied from policy documents | Rule 7 — Generic-policy boilerplate | Advisory |

**Rule-11 mirror on rewritten fields.** When Skill 1 patch mode rewrites any of `persona`, `voiceInstructions`, `chatInstructions`, or `intentInstructions`, it re-runs check 11 (English operational) on the rewritten content before accepting the change. This prevents a patch from accidentally introducing non-English bot-level prompt text.

New Appendix D in the SKILL.md documents the full mapping between self-validation checks 11–15 and their corresponding doctrine rules. See the reference doc for detection methods and fix recipes.

---

## Related skills

- [voicenter-bot-intent-detail-author](../voicenter-bot-intent-detail-author/README.md) — Skill 2; runs after Skill 1 with the section 5 stubs as input.
- [voicenter-bot-json-assembler](../voicenter-bot-json-assembler/README.md) — Skill 3; runs after Skill 2 once every intent is `[detailed]`.
