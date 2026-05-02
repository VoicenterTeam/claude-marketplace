---
name: voicenter-bot-spec-designer
description: Designs the structural skeleton of a Voicenter Bot via interview. Use this skill when the user wants to create, design, scope, or modify a Voicenter voice/chat bot — phrases like "design a bot", "create an agent spec", "build a Voicenter bot", "patch this bot", "add an intent", "change the bot's persona", "modify the flow graph", or any reference to the Agent Spec Designer / Skill 1 in the Voicenter bot generation pipeline. Produces an Agent Spec markdown file (sections 1-4, 4.5, section 5 stubs, section 6 initial, section 7 init). Two named entry modes — greenfield (no spec attached) and patch (spec attached). Does NOT author per-intent language content (validationPrompt, post-execution intentInstructions) — that's Skill 2 (Intent Detail Author). Does NOT emit wire-format JSON — that's Skill 3 (JSON Assembler).
---

# Skill 1 — Agent Spec Designer

This skill produces the **structural skeleton** of an Agent Spec markdown file through interview. It is one of three skills in the Voicenter Bot generation pipeline:

- **Skill 1 (this skill):** structural design via interview → fills spec sections 1, 2, 3, 4, 4.5, 6 (initial), 7 (init); creates section 5 stubs marked `[structural]`.
- **Skill 2 (Intent Detail Author):** language-heavy per-intent content → fills section 5 entries, marks them `[detailed]`.
- **Skill 3 (JSON Assembler & Publish):** mechanical projection of the spec into Bot JSON wire format.

Source of truth is the spec markdown. No skill invents values.

---

## 1. Required reading at invocation

Before any user interaction, load context from these references. Path conventions assume project files are accessible.

| Read | Why |
|---|---|
| Doc 1 §6.B.1 — `prompts` bundle (5 fields) | Skill 1 authors all five |
| Doc 1 §11 — RT=1/2/3/4 cross-RT field summary | Phase 4 per-RT capture |
| Doc 1 §12 — `ParameterTypeId` catalog | Slot type mapping (Appendix B in this file) |
| Doc 1 §13 — Mustache + variable categories | Section 4.5 inventory + advisory check |
| Doc 1 §14.3 — Anti-patterns | Iron rules Skill 1 enforces (Appendix A) |
| Doc 2 §3 — Agent Spec template | What Skill 1 writes |
| Doc 2 §4 — Skill 1 architecture | What Skill 1 does |

Also load these files from this skill's package:

- `model-catalog.md` — AI model configs + voice catalog (Phase 1)
- `spec-skeleton.md` — empty Agent Spec template
- `trigger-detection-rules.md` — Deep Research nudge triggers (Phase 2/3 boundary)
- `templates/voice-default.md`, `templates/chat-default.md` — inactive-channel templated defaults (Phase 2)

---

## 2. Setup

### 2.1 Detect runtime

| Signal | Runtime |
|---|---|
| Conversation in claude.ai or mobile app, no workspace file system, no `agent-spec.md` accessible | **Single-conversation** |
| Workspace file system available (Claude Code), tool calls to read/write workspace files possible | **Claude Code** |

State the detected runtime to the user. They can correct.

### 2.2 Detect mode

| Signal | Mode |
|---|---|
| Spec file attached (uploaded by user) OR `agent-spec.md` present in workspace | **Patch** |
| No spec file present | **Greenfield** |

State the detected mode to the user. They can override (forced greenfield with prior spec attached requires explicit confirmation that existing spec content will be discarded).

### 2.3 Confirm and start

State both. Confirm the bot's working name (or a placeholder for greenfield). Then proceed to Section 3 (greenfield) or Section 4 (patch).

---

## 3. Greenfield mode

Four phases, in order. Phase boundaries are not strict — revisit earlier phases if later answers reveal omissions. The Deep Research nudge falls between Phase 2 and Phase 3.

### 3.1 Phase 1 — Identity, Channels, Model, Caller-silence

**Goal:** populate spec sections 1 and 3.

Ask, in order:

1. **Bot name** (free text, often Hebrew). Required.
2. **Identifier**: ask "What ASCII identifier should this bot be filed under? (snake_case; used as the filename prefix when Skill 3 emits the JSON)". If Bot Name is already pure ASCII, default to its snake_cased form and ask only for confirmation. Required. Written to spec section 1 as `**Identifier:**`.
3. **Description** (free text). May duplicate the name. Required.
4. **Customer Account ID** (integer, references the Voicenter customer account). If user doesn't know: mark `<UNKNOWN: Account ID>`.
5. **Primary language** (BCP-47, e.g., `he-IL`, `en-US`). Required.
6. **Channel scope:** voice / chat / voice+chat. Required.
7. **If voice active:** voice name. Present `model-catalog.md` voice catalog (`Puck`, `Orus`, plus any others); user picks by name or supplies any other string the provider supports.
8. **AI model config:** present `model-catalog.md` model list. User picks by name → map to `AIModelConfigID` + `AIModelTypeId`. Override path: user supplies raw IDs directly. If user can't decide: mark `<UNKNOWN: AI Model Config>`.
9. **Caller silence:** "Does this bot need to handle caller silence?" One yes/no.
   - If yes: walk the four fields — `silence_duration` (seconds, int), `silence_loops` (int), `silence_sentence` (text, Mustache OK), `silence_ending_sentence` (text).
   - If no: mark section 3 `[not configured]`.

**Write at end of Phase 1:** spec sections 1 and 3.

### 3.2 Phase 2 — Persona Bundle

**Goal:** populate spec section 2 (5 fields per Doc 1 §6.B.1).

#### 3.2.1 Elicit identity (`prompts.persona`)

Ask: "Who is this bot? Describe identity, role, company context, tone, language posture, and any hard constraints (e.g., 'Hebrew only, never code-switch')."

Draft a `persona` from the user's answer. Show it to them. They confirm or edit.

**Iron rules during this elicitation:**

| Rule | Source | Action |
|---|---|---|
| Persona must articulate identity, role, tone, language. Not "helpful assistant" generic. | §14.3.1 | If user's input is empty/generic, push back: "What specifically is this bot's identity, role, and language? A persona that doesn't articulate these defaults to generic chatbot behavior at runtime." |
| No channel-specific behavior in persona. | §14.3.9 | Catch voice-isms (pacing, pronunciation, interruption, audio cues) and chat-isms (formatting, message length, emojis). Offer to move them to `voiceInstructions` or `chatInstructions`. |
| No per-intent procedural logic in persona. | §14.3.10 | Catch "when validating address, repeat back..." or "after getting available slots, present in order..." — these are per-intent. Offer to move to per-intent `intentInstructions` (Skill 2 will write the actual text). |
| No persistent policy embedded in single intents. | §14.3.13 | Defer this check to Phase 3 boundary, where intents exist to compare against. But ask now: "Are there any policies that apply call-wide (privacy, GDPR, retention, escalation policy)?" — capture into persona directly. |

#### 3.2.2 Elicit channel-specific behavior

For each **active** channel:

- **Voice:** ask about pacing, pronunciation (especially for street names and numbers), interruption handling, audio cues, pauses.
- **Chat:** ask about formatting (markdown vs plain), message length, emoji policy, confirmation patterns.

For each **inactive** channel: emit the templated default automatically per `templates/voice-default.md` or `templates/chat-default.md`. Substitute `[[PERSONA_IDENTITY]]` (extracted from the just-authored persona — first sentence or two establishing identity) and `[[PRIMARY_LANGUAGE]]` (mapped from the language code in section 1 to a human-readable name, e.g., `he-IL` → "Hebrew"). Show the result to the user. Ask: "Accept default or override?"

If user accepts: write to spec preceded by `[default — not user-authored]`.
If user overrides: capture the override; do not include the marker.

#### 3.2.3 Draft `prompts.intentInstructions` (bot-level Opening Behavior)

This is **pre-intent** — what the bot does at the very start of the call, before any specific intent has fired. It contains greeting, routing logic, and disambiguation rules. (Per Doc 1 §14.3.11, this is one of the most-misused fields.)

Ask: "When the call opens, what should the bot do? Greet how, then how does it figure out which intent to route to? What if the caller says something unclear?"

Draft in **Conversation Routines style** (ALL-CAPS headers, numbered steps, IF/ELSE, IRON RULES). Example shape:

```
OPENING BEHAVIOR
1. Greet briefly.
2. Ask what the caller needs.
3. Route based on caller's response:
   - Scheduling → trigger validate_customer_address.
   - Rescheduling → trigger reschedule_existing.
   - General questions → trigger general_inquiry.

IF caller's intent is unclear:
  - Ask once for clarification.
  - If still unclear, route to transfer_to_human.

IRON RULE: Stay in scope. For pricing/billing/technical, route to transfer_to_human.
```

Show the draft. User confirms or edits.

#### 3.2.4 Draft `prompts.openingAnnouncement`

This is the **first audible message** the caller hears (Doc 1 §3). One short utterance.

Ask: "What does the caller hear at the moment of pickup?"

Draft. Show. Confirm.

**Write at end of Phase 2:** spec section 2 (all five fields).

### 3.3 Phase 2 / Phase 3 boundary — Deep Research nudge

Scan the transcript of phases 1-2 for any of the four trigger cues per `trigger-detection-rules.md`.

- **No cue fires:** silent. Proceed directly to Phase 3.
- **Any cue fires:** activate the nudge.

Nudge mechanic:

1. State: "Based on what you've described, external research could meaningfully inform the flow design. I can construct a research query for you to run separately."
2. Construct the query per the template in `trigger-detection-rules.md` — four sections (3 always populated, 1 conditional based on which trigger fired).
3. Present the query.
4. Ask: "Pause here, run this in Deep Research, return with findings — or skip and proceed?"
5. If pause: save state per runtime (single-conversation: emit partial spec + query as message; Claude Code: write `agent-spec.md` partial + `research-query.md`). Append to spec section 7.3: `Deep Research nudge offered (triggers: [list]); user paused for research.`
6. If skip: append to spec section 7.3: `Deep Research nudge offered (triggers: [list]); user skipped.` Proceed to Phase 3.

When user returns from research with findings, incorporate into Phase 3 elicitation. Append to 7.3: `Deep Research findings incorporated.`

### 3.4 Phase 3 — Flow Graph and Intent List

**Goal:** populate spec sections 4, 4.5.1, 4.5.2, 4.5.4 stubs.

#### 3.4.1 Elicit happy path

Ask: "Walk me through the bot's primary success path. What does the caller's first turn look like, what happens next, and how does the call end on the happy path?"

From the answer, sketch an initial intent list (rough names + transitions).

#### 3.4.2 Expand fallbacks

For each non-terminal intent in the sketch:

- "If this intent fails or the caller wants out, where does it go?" — typically `transfer_to_human` (RT=1).
- "If the caller asks something unrelated, what happens?" — typically a catch-all `general_inquiry`.

#### 3.4.3 Per-intent capture

For each intent in the list, capture:

- **Identifier:** snake_case verb_object. Skill 1 enforces strictly per §14.3.8 — reject camelCase, kebab-case, spaces, Title Case. Offer a snake_case alternative; user confirms or proposes another.
- **Display name:** human-readable, often Hebrew if bot is Hebrew-language.
- **Description:** plain language, used by the LLM at runtime for intent recognition.
- **Tool name:** same as identifier.
- **Response Type:** ask: "Does this intent **transfer the call (RT=1)**, **call an external API (RT=2)**, **collect info and continue conversationally (RT=3)**, or **initiate an outbound dial (RT=4)**?"
  - For RT=4: surface the rarity warning per Doc 1 §11.4: "RT=4 (outbound dial) is uncommon. Confirm you actually need to initiate an outbound call from this intent, not transfer the existing call."
- **Transitions out:** ordered list of (target intent, role). Role is "success path" / "fallback" / "escalation".
- **Hard-intent flag:** Skill 1 evaluates per the four criteria below; mark `true` or `false`.

**Hard-intent criteria (decision A — flag if any one applies):**

- RT=2 with more than 3 slots
- Conditional post-execution branching (multiple distinct next-intent paths driven by API response)
- More than 4 outgoing transitions
- Slots requiring complex validation (multi-step, cross-slot dependencies)

#### 3.4.4 Iron rules during Phase 3

| Rule | Source | Action |
|---|---|---|
| Every non-terminal intent has at least one transition to an escalation intent. | §14.3.4 | If missing: "Intent `[name]` has no fallback path. Per Doc 1 §14.3.4, every non-terminal intent must have a transition to (typically) `transfer_to_human`. Add one?" Block until resolved. |
| Naming convention: snake_case verb_object. | §14.3.8 | Reject violations; propose snake_case alternative. |
| Persona's claimed capabilities ⊆ intent set. | §14.3.7 | Now possible to check (intents exist). For each capability claim in `persona`, look for a matching intent. If a claim has no matching intent: "Persona claims `[capability]`, but no intent handles that. Either add an intent or trim the persona." Block until resolved. |

#### 3.4.5 Available-variables interview (4.5.1, 4.5.2, 4.5.4 stubs)

Ask:

- **4.5.1 Call-context variables:** "What platform-supplied variables does your account expose at call start? Common entries: `caller_phone`, `TimeNow`, `caller_name`, `account_id`." If the user can't enumerate: emit defaults `caller_phone` and `TimeNow`, mark section `<INCOMPLETE: user to verify with platform>`.
- **4.5.2 Environment variables:** "Are there any deployment-time secrets you'll reference, like `{{ENV.API_TOKEN}}`?" Capture by name. v1 trusts the user's declaration; no validation that the secret exists.
- **4.5.4 API response shapes:** for each RT=2 intent, ask: "What dotted paths will you reference in the API response announcement? E.g., `available_slots.0.display`, `response.order.status`." Capture per intent. v1 trusts the declared shape; Skill 3 validates `apiResponseAnnouncement` references against this allowlist.

(Section 4.5.3 is auto-derived from section 5 slots — generated in Phase 4 close-out.)

**Write at end of Phase 3:** spec section 4 (intent rows with all structural fields except the per-RT specifics, which Phase 4 fills) and spec section 4.5.1, 4.5.2, 4.5.4.

### 3.5 Phase 4 — Per-intent structural fields

**Goal:** finalize section 4 entries with per-RT structural fields. Create section 5 stubs. Run advisory Mustache pre-check.

#### 3.5.1 Per-RT capture

**For all RTs:** capture slot list — name, ParameterTypeId (per Appendix B), IsRequired, CollectionOrder, OptionList for ENUM.

For unsupported types (number, integer, date, email): emit STRING (ParameterTypeId 1) and flag the slot for Skill 2 to author a `validationPrompt` enforcing format. Note in section 7.3: "Slot `[name]` requires natural-language validation (v1 type fallback: STRING)."

**RT=1:** Layer ID (user-supplied; `<UNKNOWN: layer ID>` if not known).

**RT=2:**
- URL (user-supplied; `<UNKNOWN: webhook URL>` if not known)
- Method (POST or GET)
- Headers structure (user-described; defaults to `{}`)
- Body structure with Mustache references (user-described)
- API response shape declaration → already captured in 4.5.4
- API silence behavior fields: `silence_duration`, `silence_loops`, `silence_sentence`, `silence_ending_sentence`, `silence_instructions` (text or empty), fallback intent reference

**RT=3:** no structural fields beyond slots. Announcement and post-execution `intentInstructions` are language-heavy — Skill 2 territory.

**RT=4:**

Ask the user "Does this intent dial a number from a slot the caller provided, or a hard-coded number?" and capture per **Dial source**:

- **Dial source = parameter** (slot-driven):
  - `parameter_phone`: the slot identifier on this intent that holds the dialed number
  - `selectdial_option`: literal `"Parameter"`
  - phone1/phone2/phone3: emit empty strings `""`

- **Dial source = static** (hard-coded numbers):
  - `phone1`, `phone2`, `phone3`: up to three E.164 numbers with leading `+`. Tried in order; any unused slot is `""`. Per the global E.164 rule (CLAUDE.md house rules), warn the user that elsewhere in Voicenter `+` is forbidden — RT=4 is the exception.
  - `selectdial_option`: capture the user's literal value (the static-mode value isn't documented as a single fixed string; if user doesn't know, emit the key absent and note in 7.4)
  - `parameter_phone`: emit absent

- **Common (both modes):**
  - `NEXT_VO_ID`: int destination voice-objective id; `<UNKNOWN: NEXT_VO_ID>` if not known
  - `MAX_DIAL_DURATION`: integer seconds (typical: 60)
  - `record`: bool (typical: `true`)
  - `announcement`: optional string spoken just before transfer
  - `intentLoadingAnnouncement`: optional string spoken while dialing
  - `intentInstructions`: optional post-execution string (Skill 2 may elaborate)
  - `response_success`: object literal `{ "instructions": "<string>" }` — guidance text the runtime uses on successful dial

Surface the rarity warning per Doc 1 §11.4 once at intent classification: "RT=4 (outbound dial) is uncommon. Confirm you actually need to initiate an outbound call from this intent, not transfer the existing call."

#### 3.5.2 Auto-derive section 4.5.3

For each slot captured across all intents, emit a 4.5.3 entry: `{{slot_name}}` — collected by `<intent_identifier>`, type `<ParameterTypeId name>`.

#### 3.5.3 Advisory Mustache pre-check

For every Mustache reference Skill 1 captured (in RT=2 body, headers, response shape declarations, plus any references in persona/intentInstructions/openingAnnouncement from Phase 2 — once 4.5 is populated):

Verify the reference resolves against:
- 4.5.1 (call-context vars)
- 4.5.2 (environment vars)
- 4.5.3 (slot vars)
- 4.5.4 (API response paths, only inside the same RT=2 intent's `apiResponseAnnouncement`)

If a reference doesn't resolve: warn the user.

> "You referenced `{{customer_name}}` in `[intent.field]` but no slot, call-context variable, or environment variable by that name is in section 4.5. Will it be collected upstream, or is it a typo for a different name?"

This is **advisory, not blocking** — Skill 1 records the user's resolution in section 7.3, then continues. Skill 3's authoritative check is blocking and runs against the same allowlist.

#### 3.5.4 Create section 5 stubs

For each intent: emit a stub of the form:

```markdown
### Intent: <identifier>
**Status:** [structural]
**Reference to section 4:** [pointer to row]
```

No further content. Skill 2 fills the rest.

**Write at end of Phase 4:** spec section 4 finalized; section 4.5.3 generated; section 5 stubs created.

### 3.6 Greenfield close-out

1. Run the **self-validation checklist** (Section 5 of this SKILL.md).
2. Generate **spec section 6** initial pass:
   - 6.1: Mustache variable usage (every `{{...}}` reference, where used, what it resolves via).
   - 6.2: Intent transition graph (flat list of `origin → next` pairs derived from section 4).
   - 6.3: RT=2 API silence pairings (per RT=2 intent: Skill 3 will pair its embedded `api_silence_behaviour` with an `apiSilenceRelations[]` registry entry; section 6.3 lists which RT=2 intents need pairing).
   - 6.4: Escalation paths (per non-terminal intent: which transition row is the escalation).
   - 6.5: ID assignments — placeholders, sequential negative integers per Doc 1 §15.3 Option A. Per intent: `-1`, `-2`, `-3`, ...
3. Initialize **spec section 7:**
   - 7.1: spec version `1.0.0`
   - 7.2: Doc 1 v1, Skill suite v1
   - 7.3: append the close-out log entry (see Section 6 of this SKILL.md for format)
   - 7.4: aggregate every `<UNKNOWN: ...>` and `<INCOMPLETE: ...>` marker in the spec into a single list
   - 7.5: pending work — count and list of intents in `[structural]` state; list of hard intents
4. **Soft-cap warnings** (Appendix C):
   - Single-conversation: ≥7 intents triggers advisory; >8 triggers "consider Claude Code".
   - Claude Code: ≥12 intents triggers advisory; >20 triggers "consider splitting bot".
5. **Emit per runtime:**
   - Single-conversation: produce the spec as the response message, plus the handoff hint (Section 6 of this SKILL.md).
   - Claude Code: write to `agent-spec.md` in the workspace, plus the handoff hint.

---

## 4. Patch mode

Skill 1 enters patch mode when invoked with a prior spec attached.

### 4.1 Pre-flight: extract from existing spec

Skill 1 must extract the following. If any extraction fails (header missing, unrecognizable format), report what couldn't be extracted and refuse to enter patch mode — instruct the user to fix the spec or restart greenfield.

| Source | Extracts |
|---|---|
| `## 1. Bot Identity` | bot name, primary language, channel scope, account ID, model config (catalog name or raw IDs) |
| `## 2. Persona Bundle` (subsections 2.1–2.5) | each `prompts` field, plus inactive-channel `[default — not user-authored]` markers |
| `## 3. Caller Silence Behavior` | the four silence fields, OR the marker `[not configured]` |
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
- Edit `prompts.openingAnnouncement`
- Edit non-structural intent metadata (display name, description, priority, max attempts, validation timeout)
- Add a new intent (enters as `[structural]`; existing intents untouched)
- Rename an intent identifier — Skill 1 updates all transition refs and Mustache refs; existing `[detailed]` content stays since the underlying logic is unchanged
- Edit caller-silence configuration
- Edit channel scope from one channel to two (newly-active channel gets templated defaults)

**Hard-change taxonomy** (cascade reset required — see 4.5):

- Change an intent's Response Type
- Modify an intent's slots (add, remove, reorder, retype)
- Delete an intent
- Modify the transition graph beyond simple reordering
- Edit `prompts.intentInstructions` (bot-level) routing destinations
- Change channel scope from two channels to one

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

> "This change affects the following intents: `[A, B, C]`. Of those, `[A, B]` reset from `[detailed]` to `[detailed-revisit]` (you'll redo their detailing in Skill 2). `[C]` stays `[structural]` (no detailing existed yet). Confirm to proceed."

If user objects: do not apply.

### 4.6 Apply the change

- Edit affected fields in sections 1, 2, 3, 4, 4.5, or section 5 stubs as the change requires.
- Update intent statuses per the algorithm.
- Re-run iron rules against the modified spec — same as greenfield close-out:
  - Persona-claims-vs-intents (§14.3.7): if a deletion removed an intent that the persona claimed, surface inconsistency.
  - Escalation-transition existence (§14.3.4): if a deletion broke an escalation path, surface and ask for a replacement.
- Update section 6 cross-references (regenerate from sections 4-5).
- Append to section 7.3: a log entry summarizing the patch.
- Update section 7.4 and 7.5.

### 4.7 Output

- Run the **self-validation checklist** (Section 5 of this SKILL.md).
- Emit per runtime:
  - Single-conversation: produce the modified spec as the response message.
  - Claude Code: write the modified spec back to `agent-spec.md`.
- Confirm the patch is applied and section 7.3 has the new entry.

### 4.8 Patch-mode iron rules

- Never discard `[detailed]` content silently. Every reset is explicit and confirmed in 4.5.
- Never invent values to fill gaps introduced by a deletion. Mark `<UNKNOWN>` and surface in 7.4.
- Never create or modify intent content that's Skill 2's territory (`validationPrompt`, post-execution `intentInstructions`).

---

## 5. Self-validation checklist

Run on **every greenfield close-out** and **after every patch**, before declaring the spec ready.

10 checks total: 8 blocking, 1 advisory, 1 structural-correctness.

Execute in the order below.

### Check 1 — Persona articulates identity, role, tone, language (§14.3.1) — blocking

**Trigger:** `prompts.persona` is empty, generic ("helpful assistant"), or missing one or more of: identity, role, tone, language.

**Failure message:**
> The persona doesn't articulate `[missing element(s)]`. A bot persona must include identity, role, tone, and language at minimum. Empty or generic personas default to generic chatbot behavior at runtime, and code-switch languages mid-call. (Doc 1 §14.3.1.)

**Remediation:** revise persona; re-check.

### Check 2 — No channel-specific content in persona (§14.3.9) — blocking

**Trigger:** `prompts.persona` contains references to pacing, pronunciation, interruption, audio cues (voice-isms), OR formatting, message length, emojis (chat-isms).

**Failure message:**
> The persona contains channel-specific content: "[quoted snippet]". This belongs in `voiceInstructions` (or `chatInstructions`), not `persona` — `persona` is in position 1 of the assembled prompt and runs on every channel. Move it?

**Remediation:** offer to move; on confirmation, edit both fields.

### Check 3 — No per-intent procedural logic in persona (§14.3.10) — blocking

**Trigger:** `prompts.persona` references specific intents or per-intent procedural steps ("when validating address...", "after getting available slots...").

**Failure message:**
> The persona contains per-intent procedural logic: "[quoted snippet]". `persona` runs on every assembled prompt; per-intent logic belongs in the intent's post-execution `intentInstructions` (Skill 2 will author that text). Move it?

**Remediation:** offer to extract; on confirmation, remove from persona and stage a note for Skill 2 about which intent should carry the logic.

### Check 4 — No persistent policy embedded in single intents (§14.3.13) — blocking

**Trigger:** an intent's Skill-1-captured fields (e.g., RT=2 body, RT=4 announcement) contain policy that should apply call-wide (privacy, GDPR, retention, escalation policy, scope-out rules).

**Failure message:**
> Intent `[name]` contains policy that applies to the whole call: "[quoted snippet]". Persistent policy belongs in `persona`, not a single intent — otherwise it's only in scope when that intent is active. Move it?

**Remediation:** offer to move to persona; remove from intent.

### Check 5 — Persona's claimed capabilities ⊆ intent set (§14.3.7) — blocking

**Trigger:** `persona` claims capability X, but no intent handles X.

**Failure message:**
> Persona claims to "[capability]", but no intent is defined to handle that. Either add an intent or trim the persona claim. (Doc 1 §14.3.7 — overpromising leads to hallucinations at runtime.)

**Remediation:** user picks one; act on choice.

### Check 6 — snake_case verb_object naming on all intents (§14.3.8) — blocking

**Trigger:** any `IntentToolName` not in snake_case verb_object form (e.g., camelCase, kebab-case, spaces, Title Case).

**Failure message:**
> Intent identifier "[bad name]" doesn't follow snake_case verb_object. Suggested: "[snake_case suggestion]". Confirm or propose alternative?

**Remediation:** rename; update all transition refs and Mustache refs.

### Check 7 — Every non-terminal intent has escalation transition (§14.3.4) — blocking

**Trigger:** a non-terminal intent (RT ≠ 1, OR RT=1 but not an explicit transfer) lacks at least one transition pointing to an escalation intent.

**Failure message:**
> Intent `[name]` has no escalation path. Per Doc 1 §14.3.4, every non-terminal intent must have a fallback (typically `transfer_to_human`). Add one?

**Remediation:** user supplies escalation target; transition is added.

### Check 8 — Mustache references resolve against section 4.5 + section 5 slots (§14.3.5) — **advisory**

**Trigger:** a Mustache `{{...}}` reference doesn't resolve against:
- 4.5.1 (call-context)
- 4.5.2 (environment)
- 4.5.3 (slots)
- 4.5.4 (API response paths, scoped to the same RT=2 intent's `apiResponseAnnouncement`)

**Warning message:**
> Reference `{{[name]}}` in `[intent.field]` doesn't resolve against section 4.5. Possibilities: (a) it's collected upstream and I missed it, (b) it's a typo for an existing variable, (c) it's a different name. Which?

**Action:** record the user's resolution to section 7.3. Continue. Skill 3's check is blocking — this is the early-warning version.

### Check 9 — Active-channel `prompts` fields populated (§14.3.1) — blocking

**Trigger:** a channel marked active in section 1 has empty `prompts.{voice,chat}Instructions`.

**Failure message:**
> Channel `[voice|chat]` is marked active but `prompts.[name]` is empty. Author content for that channel.

**Remediation:** revisit Phase 2.2 for the missing channel.

### Check 10 — Inactive-channel `prompts` have templated defaults marked (decision D) — structural-correctness (auto-fix)

**Trigger:** a channel marked inactive in section 1 has `prompts.[name]` empty (no template emitted) OR has template content not marked `[default — not user-authored]`.

**Action:** auto-fix — emit the template if missing, add the marker if missing. Log to 7.3: "Auto-applied templated default for inactive channel `[name]`."

No user prompt required.

---

### Severity-handling rules

- **Blocking failures:** do not declare the spec ready until the user resolves them. Each failure is surfaced one at a time, in order, with the exact failure message above.
- **Advisory failures:** record the user's resolution in 7.3, continue. Do not block.
- **Structural-correctness:** auto-fix; log to 7.3; continue.

---

## 6. Output contract

### 6.1 What Skill 1 writes to the spec

**On greenfield completion:**
- Sections 1, 2, 3, 4, 4.5 fully filled
- Section 5: stub entries per intent, all marked `[structural]`
- Section 6: initial pass (subsections 6.1–6.5) derived from sections 4-5
- Section 7: initialized — version, schema reference, generation log entry, unknowns aggregation, pending work

**On patch completion:**
- The modified spec
- Affected intents marked `[detailed-revisit]` (or `[structural]` if they were already `[structural]`)
- Section 6 regenerated
- Section 7.3 has a new log entry summarizing the patch
- Section 7.4 updated with new unknowns introduced by the patch
- Section 7.5 updated with newly affected intents

### 6.2 Runtime-specific delivery

**Single-conversation runtime:**

The full spec is the response message. Append a handoff hint:

> Spec is ready. Next step: invoke **Skill 2 (Intent Detail Author)** in this conversation to fill the per-intent language fields. Type "run Skill 2" or attach this spec to a fresh conversation if context is getting long.

**Claude Code runtime:**

Write the spec to `agent-spec.md` in the workspace. Append a handoff hint:

> Spec written to `agent-spec.md`. Next step: invoke **Skill 2 (Intent Detail Author)** to fill the per-intent language. Skill 2 reads the same file. May be invoked in this session or a new one.

### 6.3 Section 7.3 generation log entry format

`[ISO-8601 timestamp]  Skill 1  [greenfield|patch]  [summary]`

Examples:
- `2026-05-01T14:23:00Z  Skill 1  greenfield  Initial spec produced; 6 intents in [structural] state; 1 hard intent flagged (get_available_slots).`
- `2026-05-02T09:15:00Z  Skill 1  patch  Modified slots in get_available_slots; 2 intents reset from [detailed] to [detailed-revisit] (validate_customer_address, confirm_appointment); 1 [structural] unaffected.`

---

## 7. Anti-list — what Skill 1 does NOT do

- Write `validationPrompt` text (Skill 2's territory)
- Write per-intent post-execution `intentInstructions` text (Skill 2's territory)
- Write detailed slot descriptions beyond name + minimum identification (Skill 2 elaborates)
- Run the §15.4 cross-reference pass (Skill 3's territory)
- Emit any wire-format JSON (Skill 3's territory)
- Make creative decisions in patch mode beyond what the user describes
- Discard `[detailed]` content silently — every reset is explicit and confirmed
- Validate the bot at runtime — no testing, no simulation, no behavior check
- Query the Voicenter platform for live data — no MCP in v1; the model catalog is hardcoded per decision F

---

## Appendix A — Doc 1 §14.3 anti-patterns Skill 1 enforces

| § | Name | Skill 1 enforcement |
|---|---|---|
| 14.3.1 | Bad persona — vague/generic | Phase 2 + Self-validation Check 1 + Check 9 |
| 14.3.4 | Bad transition graph — missing fallbacks | Phase 3 + Self-validation Check 7 |
| 14.3.5 | Bad Mustache — referencing slots before collection | Phase 4 advisory pre-check + Self-validation Check 8 (advisory) |
| 14.3.7 | Bad persona — overpromising capabilities | Phase 3 + Self-validation Check 5 |
| 14.3.8 | Bad naming — inconsistent style | Phase 3 strict naming + Self-validation Check 6 |
| 14.3.9 | Misplacement — voice/channel concerns inside persona | Phase 2 + Self-validation Check 2 |
| 14.3.10 | Misplacement — per-intent instructions inside persona | Phase 2 + Self-validation Check 3 |
| 14.3.13 | Misplacement — persistent policy inside a single intent | Phase 2 + Self-validation Check 4 |

Skill 2 owns: §14.3.2 (Conversation Routines style), §14.3.3 (slot validation guidance), §14.3.6 (RT=2 api_silence completeness), §14.3.11 (bot-level disambiguation in per-intent fields), §14.3.12 (slot validation in intentInstructions).

---

## Appendix B — ParameterTypeId mapping

| User says they need… | ParameterTypeId |
|---|---|
| "name", "address", any free text | 1 (STRING) |
| "phone number" | 10 (PHONE) |
| "yes/no", "confirmation" | 16 (BOOLEAN) |
| "pick one from a list" | 19 (ENUM) + populate `OptionList` |
| "a number" / "an integer" / "a date" / "an email" | **v1 fallback: STRING (1) + flag for Skill 2 to author validationPrompt enforcing format**, surface to user as a v2 limitation |

For ENUM, capture options as `{ Value: "snake_case", Label: "user's display string" }`. `Value` is machine-side; `Label` is what the bot recognizes/announces.

---

## Appendix C — Soft-cap thresholds (decision E)

**Single-conversation runtime:**
- < 6 intents: silent
- 7–8 intents: advisory — "This is approaching the recommended limit for single-conversation runtime."
- > 8 intents: warning — "Consider switching to Claude Code runtime. Single-conversation context can strain on bots this size."

**Claude Code runtime:**
- < 12 intents: silent
- 12–20 intents: advisory — "Bot is on the larger side. Skill 2 will likely need 4+ checkpoints to detail the intent set."
- > 20 intents: warning — "Consider splitting this bot into multiple smaller bots. v1 hasn't been tested at this scale; expect Skill 2 batching to need close attention."

These warnings are emitted at greenfield close-out, after intent count is final. No hard refusal at any size — user decides.

---

*End of Skill 1 — Agent Spec Designer.*
