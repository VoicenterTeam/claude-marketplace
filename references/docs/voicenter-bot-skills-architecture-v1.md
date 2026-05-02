# Voicenter Bot JSON — Skill Architecture (v1)

**Status:** v1 — Composition specification for the three Claude skills that produce deployable Bot JSON.
**Audience:** anyone authoring or modifying the three skills (Spec Designer, Intent Detail Author, JSON Assembler), and any future team adding capabilities (v2 MCP integration, v3 update mode, v5 autonomous iteration).
**Sources:** Doc 1 (`voicenter-bot-json-schema-audit-v1.md`, the wire-format contract), the locked decisions registry from Conv 2.

---

## Table of Contents

1. Purpose, Scope, Relationship to Doc 1
2. Pipeline at a Glance
3. The Agent Spec
4. Skill 1 — Agent Spec Designer
5. Skill 2 — Intent Detail Author
6. Skill 3 — JSON Assembler & Publish
7. Validation Strategy: Iron Rules and Where They Live
8. User Workflow
9. Out of Scope for v1 Architecture
10. Handoff to SKILL.md Authoring

---

## 1. Purpose, Scope, Relationship to Doc 1

### 1.1 What this document is

This document specifies how three Claude skills compose to produce a deployable Voicenter Bot JSON. It defines:

- The pipeline: Skill 1 → Skill 2 → Skill 3, user-driven, no skill-to-skill calls
- The Agent Spec: a single markdown document that travels through all three skills and serves as the source of truth
- Where validation lives — which iron rules each skill enforces
- How the user moves between skills in two runtimes (Claude UI, Claude Code)
- What's deferred to v2/v3/v5

### 1.2 What this document is not

This document is **not**:

- The SKILL.md files themselves. Each skill's SKILL.md is authored separately, deriving from §4-6 here.
- A runtime specification for the deployed bot. Doc 1 is that.
- A schema reference for the Voicenter wire format. Doc 1 is that.

When this document and Doc 1 conflict on schema specifics, Doc 1 wins. This document is composition; Doc 1 is contract.

### 1.3 Relationship to Doc 1

Doc 1 is **the wire-format contract** — the JSON shape, field semantics, ID semantics, the §14.3 iron rules, the §15.4 cross-reference pass, the §16 quirks, the §17 schema gaps, the §18 lifecycle roadmap. Authoritative on schema.

This document (Doc 2) is **the skill composition specification** — how three skills jointly produce JSON conforming to Doc 1, and where in the skill pipeline each Doc 1 rule is enforced.

Specifically:

- Doc 1 §3 (system prompt assembly order) drives the Agent Spec section structure (§3 below)
- Doc 1 §6.B.1 (the persona bundle) maps to Spec section 2
- Doc 1 §9-11 (intent definition, parameters, RTs) maps to Spec section 5
- Doc 1 §13 (Mustache call-context variables) maps to Spec section 4.5
- Doc 1 §14.3 (iron rules) is allocated across skills in §7
- Doc 1 §15.4 (cross-reference pass) is owned by Skill 3 (§6)
- Doc 1 §16 (schema quirks) is owned by Skill 3 (§6)
- Doc 1 §18 (lifecycle) constrains v1 scope (§9 below)

### 1.4 Locked decision recap

This document is built on twelve architectural decisions locked during Conv 2. Full registry lives in `locked-decisions.md`. Short recap, organized by what they affect:

**Pipeline shape:**
- Three skills, sequenced via user invocation, no skill-to-skill calls
- Skill 1 = Agent Spec Designer (greenfield + patch modes)
- Skill 2 = Intent Detail Author (state-based, reactivable, hybrid batching)
- Skill 3 = JSON Assembler & Publish (mechanical, zero creative decisions)

**Source of truth:**
- Agent Spec is markdown, single source of truth, lives across all three skills
- Skills 1 and 2 progressively fill the spec
- Skill 3 emits JSON as a mechanical projection of the completed spec
- No invented values; unknowns marked explicitly; Skill 3 propagates as fail-loud sentinels

**Runtime model:**
- Two runtimes for the same skills:
  - Claude UI single-conversation (best for ≤8 intents)
  - Claude Code workspace-based (best for ≤20 intents)
- Same skills, same spec format, different state mechanics

**Lifecycle scope:**
- v1: manual JSON output, manual import, no MCP
- v2-v5 deferred per Doc 1 §18

---

## 2. Pipeline at a Glance

### 2.1 The three skills

```
                  ┌─────────────────────────────────────────┐
                  │ User invokes Skill 1                    │
                  │ (greenfield: no input; patch: spec.md)  │
                  └────────────┬────────────────────────────┘
                               │
                  ┌────────────▼────────────────────────────┐
                  │ Skill 1 — Agent Spec Designer           │
                  │ Interview-driven structural design      │
                  │ Writes/patches sections 1-4, 4.5, 5     │
                  │ All section-5 intents flagged           │
                  │   [structural | detailed]               │
                  │ Includes Deep Research nudge moment     │
                  └────────────┬────────────────────────────┘
                               │
                               ▼
                  Agent Spec — sections 1-4 + 4.5 written
                  Section 5 intents marked [structural]
                               │
                  ┌────────────▼────────────────────────────┐
                  │ User invokes Skill 2                    │
                  │ (continuing or starting detailing)      │
                  └────────────┬────────────────────────────┘
                               │
                  ┌────────────▼────────────────────────────┐
                  │ Skill 2 — Intent Detail Author          │
                  │ Reads spec, finds [structural] intents  │
                  │ Walks them in adaptive batches          │
                  │ Per intent: writes language-heavy       │
                  │   fields (slots, validationPrompt,      │
                  │   intentInstructions, RT-specific)      │
                  │ Marks complete intents [detailed]       │
                  │ Reactivable until all are [detailed]    │
                  └────────────┬────────────────────────────┘
                               │
                               ▼
                  Agent Spec — all sections 1-5 fully filled
                  All section-5 intents marked [detailed]
                               │
                  ┌────────────▼────────────────────────────┐
                  │ User invokes Skill 3                    │
                  └────────────┬────────────────────────────┘
                               │
                  ┌────────────▼────────────────────────────┐
                  │ Skill 3 — JSON Assembler & Publish      │
                  │ Strict-template parser reads spec       │
                  │ Mechanical mapping per Doc 1 §4-13      │
                  │ §15.4 cross-reference pass              │
                  │ Emits Voicenter wire-format JSON        │
                  │ Unknowns → fail-loud sentinels          │
                  └────────────┬────────────────────────────┘
                               │
                               ▼
                       Bot JSON file
                       (user imports manually in v1)
```

### 2.2 Dual-runtime model

The same three skills operate in two runtimes. The skills themselves are identical; what differs is how the Agent Spec is stored and how the user invokes the next skill.

**Single-conversation runtime (Claude UI):**

The Agent Spec lives as conversation context — each skill outputs the updated spec as a message. The user invokes the next skill in the same conversation. Best for bots up to ~8 intents; beyond that, conversation context strains.

**Claude Code runtime:**

The Agent Spec lives as `agent-spec.md` in the workspace. Each skill reads and writes the file. The user invokes skills across one or more sessions; the file persists between sessions. Best for bots up to ~20 intents.

Skills detect their runtime at invocation and adjust state-handling accordingly (described in detail in §4-6 per skill). The Agent Spec format is identical in both runtimes.

### 2.3 What flows between skills

Three things flow:

1. **The Agent Spec.** Markdown, structured, the source of truth. Modified by Skills 1 and 2; consumed (read-only) by Skill 3.
2. **State markers within the spec.** Per-intent `[structural | detailed]` flags drive Skill 2's reactivation. Hard-intent flags drive Skill 2's batching plan. Generation metadata in section 7 records which skill last touched the spec and when.
3. **Out-of-pipeline handoffs.** The Deep Research nudge in Skill 1 produces a query the user takes to a Deep Research conversation; findings come back as user input to Skill 1.

What does **not** flow:

- Direct skill-to-skill calls. Every skill transition is user-initiated.
- Cross-conversation memory beyond the spec itself. The spec carries everything the next skill needs to know.

---

## 3. The Agent Spec

### 3.1 Purpose

The Agent Spec is a single markdown document that:

- Captures every decision needed to produce a deployable Bot JSON
- Travels through Skills 1, 2, and 3 as the source of truth
- Is reviewable by the user at any point in the pipeline
- Is parseable by Skill 3 deterministically (strict-template structure, not free prose)

The spec replaces what would otherwise be cross-conversation handoff JSON. It serves both human review and machine processing simultaneously.

### 3.2 Source-of-truth principle

When the spec and any other artifact disagree about bot design, **the spec wins**. Specifically:

- If Skill 1 produces a spec and a separate "summary" or "briefing" message, the spec is authoritative
- If Skill 2 modifies the spec and the user has cached an earlier version mentally, the spec is authoritative
- If Skill 3 emits JSON that contradicts the spec, that's a Skill 3 bug, not a spec problem
- If the spec contradicts Doc 1 (the wire-format contract), the spec is wrong and must be corrected before Skill 3 can produce valid output

Skills do not maintain parallel state. The spec is the only persistent design artifact.

### 3.3 Section structure

The spec has seven top-level sections, plus one nested subsection (4.5). Sections 1-4 + 4.5 are filled by Skill 1. Section 5 is initially marked `[structural]` per intent by Skill 1, then progressively filled and marked `[detailed]` by Skill 2. Section 6 is regenerated by whichever skill last modified the spec. Section 7 is metadata, updated on every skill invocation.

```
1. Bot Identity
2. Persona Bundle
3. Caller Silence Behavior
4. Intent List (structural)
4.5 Available Variables
5. Intent Details (per-intent, with completion status)
6. Cross-References
7. Generation Metadata
```

Each section is described in §3.4 below.

### 3.4 Per-section specification

#### 3.4.1 Section 1 — Bot Identity

**Purpose:** captures the bot's name, language, channel scope, and runtime account context.

**Filled by:** Skill 1 (interview phase 1).

**Fields:**

| Field | Type | Required | Notes |
|---|---|---|---|
| Bot Name | string | yes | Display name, often Hebrew |
| Description | string | yes | Free text, may duplicate name |
| Account ID | int | yes | User-supplied; references the Voicenter customer account |
| Primary Language | string | yes | ISO code, e.g., `he-IL`, `en-US` |
| Channels Active | enum | yes | `voice`, `chat`, or `voice+chat` |
| Voice Name | string | conditional | Required if voice channel active. e.g., `Puck`, `Orus`. From hardcoded catalog (per decision F) |
| AI Model Config Name | string | yes | Picked from hardcoded catalog (decision F). Skill 1 maps to `AIModelConfigID` and `AIModelTypeId` at write time |
| AI Model Config ID | int | conditional | Required only if user supplied raw IDs (override path per decision F) |
| AI Model Type ID | int | conditional | Same as above |

**Markdown skeleton:**

```markdown
## 1. Bot Identity

**Bot Name:** [name]
**Description:** [description]
**Account ID:** [int]
**Primary Language:** [language code]
**Channels Active:** [voice | chat | voice+chat]
**Voice Name:** [voice name, omit if no voice channel]
**AI Model Config:** [name from catalog | "raw: ID=X, TypeID=Y"]
```

**Unknowns:** if user does not supply Account ID at interview time, mark as `<UNKNOWN: Account ID>`. Skill 3 emits as `-999` (fail-loud sentinel for ID fields). User must replace before import.

#### 3.4.2 Section 2 — Persona Bundle

**Purpose:** captures the five `prompts` fields per Doc 1 §6.B.1.

**Filled by:** Skill 1 (interview phases 2-3, with the Deep Research nudge falling at end of phase 2).

**Fields:**

| Field | Maps to Doc 1 path | Required | Channel-conditional |
|---|---|---|---|
| `persona` | `prompts.persona` | yes | always |
| `voiceInstructions` | `prompts.voiceInstructions` | conditional | filled if voice channel; defaulted if voice inactive |
| `chatInstructions` | `prompts.chatInstructions` | conditional | filled if chat channel; defaulted if chat inactive |
| `intentInstructions` (bot-level) | `prompts.intentInstructions` | yes | always |
| `openingAnnouncement` | `prompts.openingAnnouncement` | yes | always |

**Templated defaults for inactive channels (per decision D):**

When a channel is inactive, Skill 1 emits a templated default rather than empty string. Defaults are:

- **Voice default (when only chat active):** generic voice instructions injecting the persona's identity and primary language. Marked in spec as `[default — not user-authored]`.
- **Chat default (when only voice active):** generic chat instructions injecting the persona's identity and primary language. Marked similarly.

Templates live in Skill 1's SKILL.md, not in this document. The default-marker convention is part of the spec contract.

**Markdown skeleton:**

```markdown
## 2. Persona Bundle

### 2.1 Persona (Global Identity)
[persona text, often multiline, often Hebrew]

### 2.2 Voice Instructions
[voiceInstructions text]
[OR if defaulted: "[default — not user-authored]" followed by template content]

### 2.3 Chat Instructions
[chatInstructions text]
[OR if defaulted: "[default — not user-authored]" followed by template content]

### 2.4 Bot-Level Intent Instructions (Opening Behavior)
[intentInstructions text — the pre-intent disambiguation logic per Doc 1 §6.B.1]

### 2.5 Opening Announcement
[openingAnnouncement text — the first audible message per Doc 1 §3]
```

**Unknowns:** persona, intentInstructions, and openingAnnouncement are required and cannot be defaulted. If Skill 1 cannot extract them from the interview, the spec marks them `<UNKNOWN>` and Skill 3 emits empty string with a fail-loud warning in section 7's metadata block. (Empty `prompts.persona` is a known §14.3.1 anti-pattern; the warning catches it.)

#### 3.4.3 Section 3 — Caller Silence Behavior

**Purpose:** captures the bot-level silence handler per Doc 1 §6.B.3.

**Filled by:** Skill 1 (typically interview phase 1, alongside identity). Optional per Doc 1 §6.B.3 (Refua omits it).

**Fields:**

| Field | Maps to Doc 1 path | Required |
|---|---|---|
| `silence_duration` | `silence_behaviour.silence_duration` | conditional |
| `silence_loops` | `silence_behaviour.silence_loops` | conditional |
| `silence_sentence` | `silence_behaviour.silence_sentence` | conditional |
| `silence_ending_sentence` | `silence_behaviour.silence_ending_sentence` | conditional |

If Skill 1's interview surfaces no silence-handling requirement, this section is marked `[not configured]` and Skill 3 omits the `silence_behaviour` field entirely from the wire format.

**Markdown skeleton:**

```markdown
## 3. Caller Silence Behavior

[either:]
- silence_duration: [int seconds]
- silence_loops: [int]
- silence_sentence: [text]
- silence_ending_sentence: [text]

[or:]
[not configured]
```

#### 3.4.4 Section 4 — Intent List (Structural)

**Purpose:** the structural overview of every intent. One row per intent. This section is the **flow graph** — the transitions are documented here, not in section 5.

**Filled by:** Skill 1 (interview phase 3).

**Per-intent fields:**

| Field | Maps to | Notes |
|---|---|---|
| Intent identifier | section 5 anchor | snake_case `verb_object` per Doc 1 §14.3.8 |
| Display name | `Name` | Human-readable, often Hebrew |
| Description | `Description` | Plain language, used by LLM for intent recognition |
| Tool name | `IntentToolName` | Same as identifier |
| Response Type | `ResponseTypeId` | 1, 2, 3, or 4 |
| Purpose | (spec-only) | One-line description for human review |
| Hard-intent flag | (spec-only) | `true` if Skill 1 marks this intent as structurally complex (decision A) |
| Completion status | (spec-only) | `[structural]` initially, `[detailed]` after Skill 2 |
| Transitions out | `intentRelations[]` | Ordered list of (target intent, order) |
| Escalation target | (derived) | Required for non-terminal intents per §14.3.4 |

**Hard-intent criteria (per decision A):** Skill 1 marks an intent as hard if any of:
- RT=2 with more than 3 slots
- Conditional post-execution branching (multiple distinct next-intent paths driven by API response)
- More than 4 outgoing transitions
- Slots requiring complex validation (multi-step, cross-slot dependencies)

Skill 2 reads these flags and proposes a batching plan that isolates hard intents into singleton batches. User confirms or overrides at Skill 2 invocation start.

**Markdown skeleton:**

```markdown
## 4. Intent List (Structural)

### Intent 1: validate_customer_address
- **Display name:** אימות כתובת לקוח
- **Description:** וידוא שהכתובת של הלקוח נמצאת באזור השירות
- **Tool name:** validate_customer_address
- **Response Type:** 2 (API call)
- **Purpose:** Validates address against service-area DB before fetching slots
- **Hard intent:** false
- **Completion status:** [structural]
- **Transitions out:**
  1. get_available_slots (success path)
  2. transfer_to_human (fallback)
- **Escalation target:** transfer_to_human

### Intent 2: ...
```

#### 3.4.5 Section 4.5 — Available Variables

**Purpose:** the canonical inventory of variables available for Mustache templating across the entire bot. Sources both the advisory Mustache check in Skill 1 and the authoritative Mustache check in Skill 3 (per decision C).

**Filled by:** Skill 1 (interview phase 3, alongside flow graph).

**Subsections:**

```
4.5.1 Call-context variables (platform-supplied at call start)
4.5.2 Environment variables (config-time secrets via {{ENV.*}})
4.5.3 Slot variables (auto-derived from section 5 intent definitions)
4.5.4 API response variables (per-intent, RT=2 only — dotted paths)
```

**4.5.1 Call-context variables.** Skill 1 asks the user which call-context variables the platform supplies on their account (per Doc 1 §13). v1 cannot query the platform directly (no MCP); user supplies the list. Common entries: `caller_name`, `caller_phone`, `TimeNow`, `account_id`, etc.

**4.5.2 Environment variables.** Skill 1 asks about deployment-time secrets (e.g., API tokens). User lists them by `{{ENV.*}}` name. v1 does not validate the secret's existence; it trusts the user's declaration.

**4.5.3 Slot variables.** This subsection is **auto-derived** from section 5 intent definitions — each intent's slots become available variables for downstream intents. Skill 1 emits an initial pass at this subsection based on section 5's structural definitions; Skill 2 updates it as slot details are refined; Skill 3 regenerates it as a final cross-check before its Mustache resolvability pass.

**4.5.4 API response variables.** For each RT=2 intent, the spec lists the dotted paths the user expects the API response to expose (e.g., `available_slots.0.display`, `response.order.status`). v1 trusts the user's declared shape; Skill 3 validates that all dotted paths used in `apiResponseAnnouncement` resolve against the declared shape.

**Markdown skeleton:**

```markdown
## 4.5 Available Variables

### 4.5.1 Call-context variables (platform-supplied)
- `{{caller_name}}` — caller's name from CRM lookup, may be empty
- `{{caller_phone}}` — caller's incoming number, always present
- `{{TimeNow}}` — current timestamp at call start
- [additional variables per user's account configuration]

### 4.5.2 Environment variables (config-time)
- `{{ENV.API_TOKEN}}` — auth token for connector.center
- [additional secrets the user has declared]

### 4.5.3 Slot variables (auto-derived from section 5)
[Skill-generated list, one entry per slot, with the intent that collects it.
 Format:  `{{slot_name}}` — collected by `<intent_identifier>`, type `<ParameterTypeId name>`]

### 4.5.4 API response variables (per RT=2 intent)
[For each RT=2 intent, the dotted-path inventory:
 `<intent_identifier>` returns:
   - `available_slots.N.display`
   - `available_slots.N.distance_km`
   - ...]
```

**Unknowns:** if user cannot enumerate the call-context variables their account exposes, Skill 1 emits a default minimal set (`caller_phone`, `TimeNow`) and marks the section `<INCOMPLETE: user to verify with platform>`. The advisory Mustache check still operates; the authoritative check in Skill 3 will fail any reference outside the declared set.

#### 3.4.6 Section 5 — Intent Details

**Purpose:** the language-heavy per-intent fields — slots with full definitions, `validationPrompt`, post-execution `intentInstructions`, RT-specific Configuration fields.

**Filled by:** Skill 1 emits each intent's section 5 entry as a stub marked `[structural]`. Skill 2 fills the entry and marks it `[detailed]`.

**Per-intent structure (when `[structural]`):**

```markdown
### Intent: validate_customer_address
**Status:** [structural]
**Reference to section 4:** [pointer to row in section 4]

[No further content. Skill 2 fills the rest.]
```

**Per-intent structure (when `[detailed]`):**

The detailed shape varies by Response Type. The skeleton below shows fields common across RTs; RT-specific fields follow.

```markdown
### Intent: validate_customer_address
**Status:** [detailed]
**Reference to section 4:** [pointer to row in section 4]

#### Slots

##### Slot: address
- **Description:** כתובת מלאה: רחוב, מספר בית, עיר
- **Type:** STRING (ParameterTypeId 1)
- **Required:** true
- **Default value:** none
- **Collection order:** 1
- **Option list:** [empty for STRING; populated for ENUM]

#### Validation Prompt
[The full validationPrompt text in Conversation Routines style:
 ALL-CAPS headers, numbered steps, IF/ELSE, IRON RULES.
 Per Doc 1 §14.3.2.]

#### Per-RT Configuration

[For RT=2:]
- **URL:** https://connector.center/...
- **Method:** POST
- **Headers:** [object]
- **Body:** [object with Mustache references]
- **Response shape (declared):** [for §4.5.4 cross-reference]
- **API response announcement:** [text with Mustache]
- **Failure output:** [text]
- **Function output (LLM guidance):** [text]
- **Loading announcement:** [text]
- **API silence behavior:**
  - silence_duration: [int]
  - silence_loops: [int]
  - silence_sentence: [text]
  - silence_ending_sentence: [text]
  - silence_instructions: [text or empty]
  - fallback intent: [reference to escalation intent]

[For RT=3:]
- **Announcement:** [text with Mustache]

[For RT=1:]
- **Layer:** [int — user-supplied or <UNKNOWN>]
- **Announcement:** [text]
- **Loading announcement:** [text]

[For RT=4:]
- **Phone destination:** [string or <UNKNOWN>]
- **Parameter holding phone:** [reference to a slot]
- **NEXT_VO_ID:** [int or <UNKNOWN>]
- **Max dial duration:** [int seconds]
- **Select-dial option:** [string or <UNKNOWN>]
- **Record:** [bool]
- **Announcement:** [text]
- **Loading announcement:** [text]

#### Post-Execution Intent Instructions
[The intentInstructions text in Conversation Routines style.
 Defines what the bot does AFTER this intent completes.
 Per Doc 1 §14.3.10 — must not contain pre-execution logic
 or persistent policy.]
```

**Status mechanic:** Skill 2's reactivation logic depends on this. Skill 2 scans section 5, finds intents marked `[structural]`, and walks them. When all intents are `[detailed]`, Skill 2 reports completion. The user invokes Skill 3 at that point.

#### 3.4.7 Section 6 — Cross-References

**Purpose:** consolidated index of relationships across the spec. Used by Skill 3 to drive the §15.4 cross-reference pass.

**Regenerated by:** whichever skill last modified the spec. This section is **derivative** — it does not contain authoritative information; it summarizes what's already in sections 4-5 for ease of validation.

**Subsections:**

```markdown
## 6. Cross-References

### 6.1 Mustache variable usage
[For each Mustache reference in any text field:
 - reference: {{variable_name}} or {{path.to.field}}
 - used in: [intent identifier, field name]
 - resolves via: [section 4.5.X] or [section 5 slot of intent X]]

### 6.2 Intent transition graph
[Flat list of (origin → next) pairs derived from section 4]

### 6.3 RT=2 API silence pairings
[Per RT=2 intent: the registry entry that pairs with its embedded api_silence_behaviour]

### 6.4 Escalation paths
[Per non-terminal intent: which transition row points to escalation (typically transfer_to_human)]

### 6.5 ID assignments (placeholders)
[Per Doc 1 §15.3 Option A: sequential negative integers.
 Per intent: -1, -2, -3, ...]
```

**Note on automation:** section 6 is mechanically derivable from sections 4-5. Skill 1 generates an initial version; Skill 2 updates it as section 5 fills; Skill 3 regenerates it from scratch as a sanity check before the cross-reference pass. If Skill 3's regenerated version differs from the existing section 6, that's a signal section 4 or 5 was edited inconsistently — Skill 3 reports the discrepancy.

#### 3.4.8 Section 7 — Generation Metadata

**Purpose:** records the spec's history — which skill last touched it, when, in which mode, and what's left to do.

**Updated by:** every skill on every invocation, append-only within a single project pipeline.

**Fields:**

```markdown
## 7. Generation Metadata

### 7.1 Spec version
[Semantic version, e.g., 1.0.0. Bumped by skills when major sections are filled.]

### 7.2 Schema reference
- **Doc 1 version:** v1
- **Skill suite version:** v1

### 7.3 Generation log
[Append-only entries:
 - [ISO timestamp] [skill name] [mode: greenfield | patch | detailing | assembling] [summary]
 - example:  2026-05-01T14:23:00Z  Skill 1  greenfield  Initial spec produced; 6 intents in [structural] state]

### 7.4 Open unknowns
[Aggregated list of all <UNKNOWN: ...> markers in the spec.
 Updated whenever the spec changes.
 Skill 3 reads this to know what fail-loud sentinels to emit.]

### 7.5 Pending work
[Skill 2 reactivation hint:
 - [count] intents still in [structural] state
 - hard intents pending: [list]]
```

### 3.5 Unknown-marker convention

Per decision B, no skill invents values. Whenever a required value is not provided by the user, the spec marks it explicitly.

**Marker formats:**

| Field type | Marker in spec | Skill 3 emits |
|---|---|---|
| String value (e.g., URL, name) | `<UNKNOWN: webhook_url>` | `"<USER_TO_FILL: webhook_url>"` |
| Integer ID (e.g., layer, AccountID) | `<UNKNOWN: layer ID>` | `-999` |
| Object value (e.g., headers) | `<UNKNOWN: headers>` | `{}` with metadata warning |
| Optional whole-section value | `[not configured]` | omitted from JSON |

**Section 7.4 aggregation:** every `<UNKNOWN>` marker propagates to section 7.4 as a single line listing the field path. Skill 3 reads section 7.4 to decide which sentinels to emit and to write a banner comment in the JSON header listing them. The user reads the banner before importing.

**Why fail-loud:** if the user accidentally imports a JSON with `-999` as a layer ID, the platform's import will fail or the bot will route incorrectly — visibly, immediately. Quiet defaults (like `0` or `null`) would import successfully and break at runtime, which is harder to diagnose.

### 3.6 Status mechanic for section 5 intents

Each intent in section 5 has one of three statuses:

| Status | Set by | Meaning |
|---|---|---|
| `[structural]` | Skill 1 | Section 4 row exists for this intent; section 5 entry is a stub. Skill 2 needs to fill it. |
| `[detailed]` | Skill 2 | Section 5 entry is fully filled. Skill 2 self-validation passed. Ready for Skill 3. |
| `[detailed-revisit]` | Skill 1 patch mode | Was `[detailed]`, but a hard structural change in patch mode reset it. Treated as `[structural]` for Skill 2's reactivation, but distinguishable in section 7.3 generation log. |

Skill 2's reactivation: scans section 5, finds entries with status `[structural]` or `[detailed-revisit]`, walks them. When all entries are `[detailed]`, reactivation exit condition met; user invokes Skill 3.

### 3.7 Strict-template enforcement

Skill 3's deterministic parsing requires the spec to follow the exact section structure documented above. **Deviation is a parse error, not a basis for interpretation.**

Specifically:

- Section headers must match exactly (`## 1. Bot Identity`, not `## Bot Identity` or `## 1: Bot Identity`)
- Field labels in italics or bold must match exactly (`**Bot Name:** [value]`)
- The intent header convention `### Intent N: <identifier>` is fixed — Skill 3 parses identifiers from this line
- Status markers `[structural]`, `[detailed]`, `[detailed-revisit]` are exact strings; no synonyms
- Unknown markers `<UNKNOWN: description>` and `<INCOMPLETE: ...>` and `[not configured]` are exact strings

Skills 1 and 2 generate spec content according to these conventions. The user is not expected to hand-author specs in this format from scratch — but if they edit the spec between skill invocations, they must respect the conventions or Skill 3 will fail to parse.

**Skill 3 parser failure:** if the spec deviates from the template, Skill 3 emits a structured error pointing to the first deviation (line number, expected pattern, found content). Does not attempt to interpret. User fixes the spec and re-invokes.

---

## 4. Skill 1 — Agent Spec Designer

### 4.1 Purpose and scope boundary

Skill 1 produces the structural skeleton of the Agent Spec through user interview. It owns Spec sections 1, 2, 3, 4, and 4.5, and produces section 5 entries marked `[structural]` for Skill 2 to detail. It does not write language-heavy per-intent fields (those belong to Skill 2). It does not produce wire-format JSON (that belongs to Skill 3).

**What Skill 1 owns:**
- Bot identity, channel scope, AI model selection
- Persona bundle authoring (full content for active channels, templated defaults for inactive)
- Caller-silence configuration (or `[not configured]`)
- Intent list with structural fields, transitions, hard-intent flags
- Available variables inventory (4.5.1, 4.5.2 by interview; 4.5.3 auto-derived; 4.5.4 by interview per RT=2 intent)
- Section 6 initial generation (cross-references derived from sections 4 and 5)
- Section 7 metadata initialization

**What Skill 1 does not own:**
- `validationPrompt` text — Skill 2
- Per-intent post-execution `intentInstructions` — Skill 2
- Slot details beyond name, type, required, collection order — Skill 2 fills descriptions and any v1-fallback validation guidance
- RT-specific Configuration content (URL bodies, headers, response shape declarations) — Skill 1 captures structurally what the user said; Skill 2 refines language-heavy parts
- Wire-format JSON emission — Skill 3
- Cross-reference validation — Skill 3 (Skill 1 runs only the advisory Mustache pre-check)

### 4.2 Two named entry modes

Skill 1 detects its mode at invocation:

**Greenfield mode:** no prior spec attached. User invokes Skill 1 with no input file. Skill 1 conducts the full four-phase interview from scratch.

**Patch mode:** prior spec attached (uploaded as file in Claude UI; present in workspace in Claude Code). Skill 1 reads the spec, asks the user what to change, computes cascade impact, modifies in place, surfaces affected intents.

Mode detection logic:

```
At invocation:
  IF spec file is present (uploaded or in workspace):
    → patch mode
  ELSE:
    → greenfield mode
```

The user can force greenfield with the prior spec attached if they want to start fresh — Skill 1 asks for confirmation before discarding existing spec content.

### 4.3 Greenfield mode — four-phase interview

Skill 1's greenfield interview has four phases. Phase boundaries are not strict — Skill 1 may revisit earlier phases if the user's answers reveal omissions. The Deep Research nudge falls at the end of phase 2 per decision H.

#### Phase 1 — Identity and Channels

**Goal:** populate spec sections 1 (Bot Identity) and 3 (Caller Silence Behavior).

**Questions Skill 1 covers:**
- Bot name, description
- Customer account ID (Voicenter platform context)
- Primary language
- Channel scope: voice-only, chat-only, or both
- If voice active: voice name (from hardcoded catalog; raw override accepted)
- AI model config: pick from hardcoded catalog or supply raw IDs (per decision F)
- Caller-silence behavior: configure or skip (most bots configure; Refua omits)

**Skill 1 behavior on this phase:**

The model catalog is hardcoded in Skill 1's SKILL.md package. v1 entries are at minimum `Gemini Live` (the production reference per Doc 1 samples). Skill 1 presents the catalog as a list; user picks by name. Override path: user supplies raw `AIModelConfigID` and `AIModelTypeId` integers, Skill 1 records them as raw without catalog mapping.

For caller-silence: Skill 1 asks one yes/no ("does this bot need to handle caller silence?") and if yes, walks through the four fields. If no, section 3 is marked `[not configured]`.

#### Phase 2 — Persona Bundle

**Goal:** populate spec section 2.

**Approach:**

Skill 1 elicits identity-level content first (who the bot is, role, tone, language posture, hard constraints). This becomes `prompts.persona`.

Then Skill 1 walks the user through channel-specific behavior:
- For active voice channel: pacing, pronunciation, interruption handling, audio cues
- For active chat channel: formatting, message length, emoji policy
- For inactive channel: Skill 1 emits the templated default automatically (per decision D), shows it to the user, asks "accept default or override?"

Skill 1 then produces:
- `prompts.intentInstructions` (bot-level Opening Behavior): a Conversation Routines structured block with greeting, routing logic, and an iron rule about staying in scope. Skill 1 drafts this from the user's articulation of bot purpose; user confirms or edits.
- `prompts.openingAnnouncement`: a single short utterance the caller hears first. Skill 1 drafts; user confirms.

**Iron rules Skill 1 enforces during phase 2:**

- Persona must articulate identity, role, tone, language. Empty or generic persona fails (§14.3.1).
- Persona must not include channel-specific behavior (§14.3.9). Skill 1 catches voice-isms in persona text and offers to move them to `voiceInstructions`.
- Persona must not include per-intent procedural logic (§14.3.10). Skill 1 catches references to specific intent steps and offers to move them.
- Persona must not include persistent policy presented as a single intent's responsibility (§14.3.13). Skill 1 catches global policy embedded in intent context and offers relocation.
- Persona's claimed capabilities must be a strict subset of what intents will actually handle (§14.3.7). Skill 1 cannot fully validate this until phase 3 (intent list exists), so it runs the check at phase 3 boundary instead.

#### Phase 2 / Phase 3 boundary — Deep Research nudge moment

Per decisions H, I, and J, the nudge fires at end of phase 2.

**Trigger detection:** Skill 1 watches for any of four cues during phases 1-2:

| Trigger | Detection cue |
|---|---|
| Regulated industry | User mentions medical, financial, legal, insurance, or pharmaceutical context |
| Expressed uncertainty | User says they don't know typical patterns, asks Skill 1 what's standard |
| Competitor question | User asks how others do it, or mentions specific competitors |
| Unrecognized niche domain | Skill 1 has no priors on the domain (e.g., very specific industry vertical) |

If any cue fires during phases 1-2, Skill 1 activates the nudge at end of phase 2.

**Nudge mechanic:**

1. Skill 1 announces: "Based on what you've described, external research could meaningfully inform the flow design. I can construct a research query for you to run separately."
2. Skill 1 generates the parameterized query (per decision J) — four sections, conditionally populated based on which trigger fired:
   - **Domain context** (always): the bot's industry and use case
   - **Regional/language context** (always): location and primary language
   - **Intent-derived focus** (always): the rough intent set sketched so far, asking for common patterns
   - **Regulatory/competitive context** (conditional): populated only if regulated-industry or competitor cues fired
3. Skill 1 presents the full query for the user to review.
4. User chooses: pause-and-research (copy query, open Deep Research conversation, return with findings) or skip (proceed to phase 3 without research).
5. If pause-and-research: Skill 1 saves current spec state (in single-conversation: outputs the partial spec; in Claude Code: writes to file), instructs the user how to return.
6. If skip: Skill 1 records in section 7.3 generation log that the nudge was offered and skipped, then proceeds to phase 3.

**Returning from research:** user pastes findings into Skill 1. Skill 1 incorporates findings into the user's articulation of phase 3, then proceeds.

If no trigger fires during phases 1-2, the nudge is silent — the user never sees it. This is intentional per decision I.

#### Phase 3 — Flow Graph and Intent List

**Goal:** populate spec sections 4, 4.5.1, 4.5.2, 4.5.4.

**Approach:**

Skill 1 elicits the bot's primary success path: what's the happy-path sequence of intents from caller's first turn to call termination. From this, Skill 1 derives the initial intent list and rough transitions.

Then Skill 1 expands fallback paths:
- For each non-terminal intent, what's the escalation route (typically `transfer_to_human`)?
- What does the bot do if the user asks something out-of-scope?
- What's the catch-all path (typically a `general_inquiry` intent)?

Per intent, Skill 1 captures structural fields:
- Identifier (snake_case verb_object per §14.3.8 — Skill 1 enforces naming convention strictly, asks for clarification if user's suggestion doesn't fit)
- Display name (human-readable, often Hebrew if bot is Hebrew-language)
- Description (plain language, used by LLM for intent recognition)
- Response Type (1, 2, 3, or 4) — Skill 1 asks "does this intent transfer the call (1), call an external API (2), collect info and continue conversationally (3), or initiate an outbound call (4)?"
- Transitions out, with explicit ordering
- Hard-intent flag — Skill 1 evaluates the four criteria from §3.4.4 and marks accordingly

**Iron rules Skill 1 enforces during phase 3:**

- Every non-terminal intent must have an escalation transition (§14.3.4). Skill 1 catches missing escalation paths and prompts the user to add them.
- Naming convention strict (§14.3.8). Skill 1 rejects camelCase, kebab-case, spaces, and offers a snake_case verb_object alternative.
- Persona-claims-vs-intents check (§14.3.7). Skill 1 cross-checks the persona's claimed capabilities (from phase 2) against the intent set (from phase 3) and flags any persona-claimed capability not represented by an intent.
- For RT=4 intents (outbound dial), Skill 1 surfaces the rarity warning per Doc 1 §11.4 — confirms the user actually needs outbound dial.

**Available-variables interview (4.5.1, 4.5.2, 4.5.4):**

After the intent list is sketched, Skill 1 asks:
- Which platform-supplied call-context variables does the user's account expose? (4.5.1)
- Are there environment-supplied secrets (`{{ENV.*}}`)? (4.5.2)
- For each RT=2 intent, what's the expected response shape — what dotted paths will the user reference in `apiResponseAnnouncement`? (4.5.4)

If the user can't enumerate 4.5.1, Skill 1 emits the minimal default (`caller_phone`, `TimeNow`) and marks 4.5.1 `<INCOMPLETE>`. Same fallback for 4.5.2.

For 4.5.4, Skill 1 captures whatever the user describes; this is treated as user-declared truth. Skill 3's authoritative Mustache check uses 4.5.4 as the allowlist for dotted-path references.

#### Phase 4 — Per-intent structural fields

**Goal:** finalize section 4 entries with the per-intent details that are still structural (not language-heavy).

**Per intent, Skill 1 captures:**

For all RTs:
- Slot list with name, ParameterTypeId, IsRequired, CollectionOrder, OptionList for ENUM
- Slot type guidance: Skill 1 maps user's description to ParameterTypeId per Doc 1 §12 (STRING, PHONE, BOOLEAN, ENUM). For unsupported types (NUMBER, DATE, EMAIL), Skill 1 emits STRING with a flag for Skill 2 to write a `validationPrompt` enforcing format.

For RT=1:
- Layer ID (user-supplied; `<UNKNOWN>` if not known)

For RT=2:
- URL (user-supplied; `<UNKNOWN>` if not known)
- Method (POST or GET)
- Headers structure (user-described; defaults to `{}`)
- Body structure with Mustache references (user-described; Skill 1 validates each Mustache reference against 4.5 inventory)
- API response shape declaration (per intent, captured for 4.5.4)
- API silence behavior fields

For RT=3:
- (No structural fields beyond slots; announcement and intentInstructions are language-heavy, deferred to Skill 2)

For RT=4:
- Phone destination (user-supplied; `<UNKNOWN>` if not known)
- Slot reference for the dialed number
- NEXT_VO_ID (user-supplied; `<UNKNOWN>` if not known)
- Max dial duration, select-dial option, record flag

**Advisory Mustache pre-check (per decision C):**

For every Mustache reference Skill 1 captures (in body, headers, response declarations), Skill 1 verifies the reference resolves against section 4.5. If a reference doesn't resolve, Skill 1 issues an advisory warning:

> "You referenced `{{customer_name}}` but no slot, call-context variable, or environment variable by that name is in the spec. Will it be collected upstream, or did you mean a different name?"

This is **advisory, not blocking** — Skill 1 records the user's resolution in section 7.3, then continues. Skill 3's authoritative check is blocking and runs against the same allowlist.

### 4.4 Patch mode

Skill 1 enters patch mode when invoked with a prior spec attached.

#### 4.4.1 Patch mode workflow

1. **Read the existing spec.** Validate that it parses against the strict template. If parse fails, Skill 1 reports the parse error and refuses to enter patch mode — the user fixes the spec or starts greenfield.
2. **Surface current state.** Skill 1 produces a brief summary: bot name, channel scope, intent count, count of intents in `[structural]` vs `[detailed]` status.
3. **Ask what to change.** Skill 1 elicits the desired change in plain language.
4. **Classify the change.** Per the easy-change / hard-change taxonomy below, Skill 1 categorizes the requested change.
5. **Compute cascade impact.** Skill 1 identifies which intents are structurally affected (directly and transitively).
6. **Surface impact.** Skill 1 reports: "This change resets these intents from `[detailed]` to `[detailed-revisit]`: [A, B, C]. You'll redo their detailing in Skill 2. Confirm to proceed."
7. **Apply the change.** Skill 1 modifies the spec in place — updates affected sections, resets affected intents, updates section 6 cross-references, appends to section 7.3 generation log.
8. **Output the modified spec.** Per runtime: outputs as message in single-conversation, writes to workspace file in Claude Code.

#### 4.4.2 Easy-change taxonomy (no detailed-intent reset)

These changes leave all `[detailed]` intents intact:

- Edit `prompts.persona` (section 2.1 only)
- Edit `prompts.voiceInstructions` or `prompts.chatInstructions`
- Edit `prompts.openingAnnouncement`
- Edit non-structural intent metadata (display name, description, priority, max attempts, validation timeout)
- Add a new intent (it enters as `[structural]`; existing intents untouched)
- Rename an intent's identifier — Skill 1 updates all transition references and Mustache references; existing `[detailed]` content stays since the underlying logic is unchanged
- Edit caller-silence configuration
- Edit channel scope from one channel to two (newly-active channel gets templated defaults)

#### 4.4.3 Hard-change taxonomy (cascade reset required)

These changes reset affected intents:

- **Change an intent's Response Type.** That intent resets to `[detailed-revisit]` (its Configuration shape changes entirely).
- **Modify an intent's slots** (add, remove, reorder, retype). That intent resets, plus any other intent whose `validationPrompt`, `intentInstructions`, or RT=2 body references the modified slot must reset.
- **Delete an intent.** All `intentRelations` referencing it as origin or next must be cleaned up. Intents whose transitions pointed to it lose that path; if the lost path was the only escalation, those intents need a new escalation (Skill 1 surfaces this as a follow-up question).
- **Modify the transition graph** beyond simple reordering. Affected intents reset because their post-execution `intentInstructions` may reference removed transitions.
- **Edit `prompts.intentInstructions` (bot-level)** in a way that changes routing destinations. Affected: all intents whose recognition logic depends on the routing pattern. Skill 1 surfaces which intents are likely affected and asks the user to confirm.
- **Change channel scope from two channels to one.** The dropped channel's instructions become defaulted; persona may need re-review since voice-vs-chat-isms might have leaked in.

#### 4.4.4 Cascade impact algorithm

For a hard change, Skill 1 computes the affected set:

```
affected_set = { directly_modified_intent }

REPEAT until no change:
  FOR each intent I in spec section 5:
    IF I's validationPrompt text references any field of any intent in affected_set:
      add I to affected_set
    IF I's intentInstructions text references any transition involving an intent in affected_set:
      add I to affected_set
    IF I's RT=2 Configuration body or headers reference a slot owned by an intent in affected_set:
      add I to affected_set

For each intent in affected_set:
  Mark status as [detailed-revisit] in section 5
```

Skill 1 reports the final affected set to the user before applying. If the user objects, Skill 1 does not apply.

#### 4.4.5 Patch mode iron rules

The structural iron rules from greenfield phase 3 still apply after a patch:
- Every non-terminal intent must have an escalation transition. If a deletion breaks this, Skill 1 surfaces it as a follow-up question.
- Persona-claims-vs-intents check. If the patch removed an intent that the persona claimed, Skill 1 surfaces the inconsistency.

### 4.5 Skill 1 self-validation checklist

Before declaring a spec ready for Skill 2 (greenfield) or for re-handoff (patch), Skill 1 runs:

| Check | Source | Severity |
|---|---|---|
| Persona is non-empty and articulates identity/role/tone/language | §14.3.1 | blocking |
| No channel-specific content in persona | §14.3.9 | blocking |
| No per-intent procedural logic in persona | §14.3.10 | blocking |
| No persistent policy embedded in single intents | §14.3.13 | blocking |
| Persona's claimed capabilities ⊆ intent set | §14.3.7 | blocking |
| Naming convention (snake_case verb_object) on all intents | §14.3.8 | blocking |
| Every non-terminal intent has escalation transition | §14.3.4 | blocking |
| All Mustache references resolve against section 4.5 + section 5 slots | §14.3.5 / §15.4 item 7 | advisory |
| Active-channel `prompts` fields populated | §14.3.1 | blocking |
| Inactive-channel `prompts` fields have templated defaults marked | decision D | structural-correctness |

Blocking failures: Skill 1 does not declare the spec ready until the user resolves them.

Advisory failures: Skill 1 records in section 7.3, continues.

### 4.6 Skill 1 outputs

**On greenfield completion:**

- Spec sections 1, 2, 3, 4, 4.5, 6 fully filled
- Section 5 contains stub entries per intent, all marked `[structural]`
- Section 7 metadata initialized; 7.4 unknowns aggregated; 7.5 lists all intents pending Skill 2

**On patch completion:**

- Spec is the modified version of the input
- Affected intents marked `[detailed-revisit]`
- Section 7.3 has a new log entry summarizing the patch
- Section 7.4 updated with new unknowns introduced by the patch
- Section 7.5 lists intents requiring Skill 2 attention

**Runtime-specific delivery:**

- Single-conversation: spec is the most recent message; user reads it inline, then invokes Skill 2 in the same conversation
- Claude Code: spec is written to `agent-spec.md`; user invokes Skill 2 in the same or a new session

### 4.7 Skill 1 anti-list

Skill 1 explicitly does **not**:

- Write `validationPrompt` text (Skill 2)
- Write per-intent `intentInstructions` text (Skill 2)
- Write detailed slot descriptions (beyond what's needed for the user to confirm the slot exists; Skill 2 elaborates)
- Run the §15.4 cross-reference pass (Skill 3)
- Emit any wire-format JSON (Skill 3)
- Make creative decisions in patch mode beyond what the user describes
- Discard `[detailed]` content silently — every reset is explicit and confirmed

---

## 5. Skill 2 — Intent Detail Author

### 5.1 Purpose and scope boundary

Skill 2 fills the language-heavy fields in spec section 5 — the per-intent content that determines how the bot behaves at runtime. It thinks deeply about each intent: what the bot should say to collect slots, how to validate user input, what to do after the intent fires, how to handle edge cases.

**What Skill 2 owns:**
- Slot descriptions (full, user-visible text)
- `validationPrompt` for each intent (Conversation Routines style)
- Post-execution `intentInstructions` for each intent (Conversation Routines style)
- RT-specific language fields: `apiResponseAnnouncement`, `fail_output`, `function_output`, `intentLoadingAnnouncement`, `announcement` for RT=3
- API silence behavior text (per RT=2): `silence_sentence`, `silence_ending_sentence`, `silence_instructions`
- Status updates: `[structural]` → `[detailed]` per intent
- Section 4.5.3 updates as slot details are refined

**What Skill 2 does not own:**
- Structural fields (handled by Skill 1: identifiers, RTs, slot types/order, transitions, hard-intent flags)
- Persona, channel instructions, opening behavior (Skill 1)
- Wire-format JSON emission (Skill 3)
- The §15.4 cross-reference pass (Skill 3)

### 5.2 State-based reactivation

Skill 2 is designed to be invoked multiple times against the same spec. Each invocation:

1. Reads the spec
2. Identifies intents requiring detailing (status `[structural]` or `[detailed-revisit]`)
3. Walks them in batches per the batching plan
4. Returns control to the user at each batch checkpoint

When all intents are `[detailed]`, Skill 2 reports completion and instructs the user to invoke Skill 3.

**Reactivation has no special invocation semantics.** The user invokes Skill 2 the same way every time. Skill 2 inspects spec state and resumes from where the previous invocation left off. There is no "session token," no "continue command" — the spec is the state.

### 5.3 Hybrid batching with adaptive sizing

Per decision A, Skill 2 batches intents into checkpoints rather than walking all intents in a single uninterrupted pass.

**Batching algorithm (computed at each invocation):**

```
intents_to_detail = [intents in section 5 with status [structural] or [detailed-revisit]]
hard_intents = [intents in intents_to_detail with hard-intent flag = true]
soft_intents = [intents in intents_to_detail with hard-intent flag = false]

batches = []

# Hard intents are singletons
FOR each hard_intent in hard_intents:
  batches.append([hard_intent])

# Soft intents grouped by adaptive sizing
soft_count = len(soft_intents)
target_checkpoints = derive_checkpoint_count(soft_count + len(hard_intents))
soft_batch_size = ceil(soft_count / max(1, target_checkpoints - len(hard_intents)))
soft_batch_size = min(soft_batch_size, 6)  # upper bound

batch = []
FOR each soft_intent in soft_intents:
  batch.append(soft_intent)
  IF len(batch) == soft_batch_size:
    batches.append(batch)
    batch = []

IF batch is not empty:
  batches.append(batch)

# target_checkpoints is derived from total count:
#   <= 5 intents:   2 checkpoints (with hard intent isolated if any)
#   6-10 intents:   3 checkpoints
#   11-15 intents:  3-4 checkpoints
#   16-20 intents:  4 checkpoints
#   > 20 intents:   ceil(count / 5) checkpoints
```

**User confirms or overrides the batching plan.** At Skill 2 invocation start, after reading the spec, Skill 2 proposes the plan:

> "I'm going to detail [N] intents in [K] batches:
> - Batch 1: [intent_a, intent_b]
> - Batch 2: [intent_c — flagged as complex, singleton]
> - Batch 3: [intent_d, intent_e, intent_f]
>
> Confirm or override?"

User accepts the plan, modifies it (different grouping), or starts with a specific intent. If the user overrides, Skill 2 records the override choice in section 7.3.

**Checkpoint mechanic per batch:**

```
FOR each batch in batches:
  FOR each intent in batch:
    walk the intent's detailing interview (§5.4)
    update spec section 5 entry to [detailed]
    update section 4.5.3 with refined slot variables
    update section 6 cross-references involving this intent
    update section 7.3 generation log
  
  output the updated spec (single-conversation: as message; Claude Code: write to file)
  ask user: "Batch [N] complete: intents [list] are now [detailed]. Continue with batch [N+1] or pause?"
  IF user pauses:
    halt; user re-invokes Skill 2 to resume
  ELSE:
    proceed to next batch
```

**Special case: a single batch with one intent.** If the bot has only one intent requiring detailing, Skill 2 still issues the confirmation gate after completion before reporting overall completion. The user always sees an explicit confirmation point.

### 5.4 Per-intent detailing interview

For each intent in a batch, Skill 2 conducts a focused interview. The interview shape varies by Response Type, but follows a common four-step pattern:

1. **Slot detailing** — complete the slot descriptions and any v1-fallback validation guidance
2. **Validation prompt authoring** — write the `validationPrompt` in Conversation Routines style
3. **RT-specific configuration** — fill the RT-specific language fields
4. **Post-execution instructions** — write the per-intent `intentInstructions` in Conversation Routines style

#### Step 1 — Slot detailing

Skill 1 captured slot names, types, required flags, collection orders. Skill 2 elaborates:

- **Description (user-facing):** what the bot will use to phrase the slot collection question. Often Hebrew. Example: `"כתובת מלאה: רחוב, מספר בית, עיר. למשל: רחוב הרצל 14 רמת גן."`
- **For ENUM slots:** if `OptionList` is static (known choices), Skill 2 confirms the option list and `Label` text per option. If `OptionList` is dynamic (populated from upstream API response), Skill 2 marks `OptionList: []` and notes in the validationPrompt that options come from `{{available_slots}}` or similar.
- **For v1-fallback slots (NUMBER, DATE, EMAIL stored as STRING):** Skill 2 captures the validation guidance to embed in `validationPrompt` — format constraints, range constraints, etc.

#### Step 2 — `validationPrompt` authoring

This is the bot's primary lever for shaping how it collects slots. The text must follow Conversation Routines style per Doc 1 §14.3.2:
- ALL-CAPS section headers (e.g., `ADDRESS COLLECTION`, `IRON RULES`)
- Numbered steps for the collection sequence
- Explicit IF/ELSE for branching
- IRON RULE blocks for non-negotiables (rejection criteria, format requirements)

**Skill 2's authoring approach:**

Skill 2 drafts an initial `validationPrompt` based on:
- The slot list and their types
- The collection order
- The intent's purpose (from section 4 description)
- The user's articulation of edge cases (Skill 2 asks: "what should the bot do if the user gives a partial answer? An off-topic answer? Refuses to provide?")

User reviews and edits. Skill 2 ensures:
- All slots in the intent are addressed in the validationPrompt
- Each slot has at least one explicit validation rule (especially for v1-fallback types)
- An IRON RULE block exists for the most critical constraints
- The prompt language matches the bot's primary language (Hebrew text for Hebrew bots, etc.)

#### Step 3 — RT-specific configuration

**For RT=1 (Layer Transfer):**
- `announcement` — what the bot says before transferring (e.g., `"אני מעבירה אותך לנציג, רגע אחד"`)
- `intentLoadingAnnouncement` — covers latency between announcement and actual transfer (e.g., `"המתן בבקשה"`)

**For RT=2 (API Call):**
- `apiResponseAnnouncement` — what the bot says when the API succeeds. Skill 2 uses Mustache references against section 4.5.4 dotted paths declared by the user.
- `fail_output` — what the bot says when the API fails. Default pattern: graceful "I couldn't reach the system, transferring to a human."
- `function_output` — LLM guidance for interpreting the API response in subsequent turns. Skill 2 drafts based on the response shape declared in section 4.5.4.
- `intentLoadingAnnouncement` and `IntentLoadingAnnouncement` (the case-bug pair per Doc 1 §16) — same content, both populated.
- `silence_sentence`, `silence_ending_sentence`, `silence_instructions` — what the bot says during the API wait, after silence loops exhausted, and any additional LLM guidance. Skill 2 drafts; user confirms.

**For RT=3 (Continue):**
- `announcement` — what the bot says after slot collection completes (e.g., `"מעולה. רשמתי לך תור ב-{{available_slots.0.display}} בכתובת {{address}}. נשלח לך SMS עם פרטים."`)

**For RT=4 (Dial-Out):**
- `announcement` — spoken before initiating the dial
- `intentLoadingAnnouncement` — spoken while dialing

**Mustache reference handling:**

Every Mustache reference Skill 2 writes must resolve against section 4.5 (per the advisory check Skill 1 ran, plus Skill 2's own self-check). Skill 2 verifies each reference at write time:

- `{{slot_name}}` resolves if the slot is collected by this intent or an upstream intent
- `{{call_context_var}}` resolves if listed in 4.5.1
- `{{ENV.*}}` resolves if listed in 4.5.2
- `{{response.*}}` or `{{available_slots.N.*}}` resolves if declared in 4.5.4 for this intent (RT=2 only)

If Skill 2 catches an unresolvable reference during drafting, it asks the user before proceeding.

#### Step 4 — Post-execution `intentInstructions`

This is the second Conversation Routines block per intent. It defines what the bot does **after** this intent has fired and slots have been collected.

**Critical distinction (per Doc 1 §14.3.10, §14.3.12):**
- `validationPrompt` is **pre-execution** — slot collection
- `intentInstructions` is **post-execution** — what to do next

Skill 2 writes `intentInstructions` to cover:
- Confirmation language (e.g., `"POST-EXECUTION: address validated. Proceed to slot fetch."`)
- Conditional next-intent routing if the intent's outcome varies (e.g., for RT=2 with conditional success/failure paths)
- Iron rules for what NOT to do post-execution (e.g., scope-creep prevention)

**Iron rules Skill 2 enforces during step 4:**
- `intentInstructions` must NOT contain pre-execution slot collection logic (§14.3.12)
- `intentInstructions` must NOT contain persistent policy that belongs in `prompts.persona` (§14.3.13)
- `intentInstructions` must NOT contain bot-level disambiguation that belongs in `prompts.intentInstructions` (§14.3.11)
- Format must be Conversation Routines style, not free prose (§14.3.2)

If Skill 2 catches a misplacement during drafting, it relocates the content to the correct field and informs the user.

### 5.5 Skill 2 self-validation checklist

Per intent, before marking it `[detailed]`:

| Check | Source | Severity |
|---|---|---|
| `validationPrompt` is non-empty and Conversation Routines styled | §14.3.2 | blocking |
| `validationPrompt` covers every slot in the intent | §14.3.2 | blocking |
| `validationPrompt` includes at least one IRON RULE block | §14.3.3 | blocking |
| Slot type matches purpose (no STRING for phone, etc.) | §14.3.3 | blocking |
| `intentInstructions` is non-empty and Conversation Routines styled | §14.3.2 | blocking |
| `intentInstructions` does not contain slot collection logic | §14.3.12 | blocking |
| `intentInstructions` does not contain persistent policy | §14.3.13 | blocking |
| `intentInstructions` does not contain bot-level disambiguation | §14.3.11 | blocking |
| All Mustache references resolve against section 4.5 + upstream slots | §14.3.5 / §15.4 item 7 | blocking at this level |
| For RT=2: `apiResponseAnnouncement`, `fail_output`, `function_output` all populated | §14.3.6 | blocking |
| For RT=2: API silence behavior fully populated | §14.3.6 | blocking |

**Why Mustache resolution is blocking at Skill 2 (vs advisory at Skill 1):** Skill 2 has the full slot inventory and writes the actual Mustache references. False positives from Skill 1's advisory check are gone. By Skill 2 time, an unresolvable reference is genuinely a bug.

Blocking failures: Skill 2 does not mark the intent `[detailed]`. Asks the user to resolve, then re-validates.

### 5.6 Skill 2 outputs

**Per batch checkpoint:**
- Updated spec with the batch's intents marked `[detailed]`
- Section 4.5.3 refreshed with refined slot variables (e.g., if a slot description changed)
- Section 6 cross-references updated for the affected intents
- Section 7.3 generation log entry summarizing the batch
- Section 7.4 updated if the batch resolved or introduced any unknowns
- Section 7.5 updated to reflect remaining `[structural]` / `[detailed-revisit]` intents

**Per invocation completion (when all intents in current invocation's plan are detailed):**
- Above, plus a clear status report: "[N] intents detailed in this invocation. [M] intents still pending. Re-invoke Skill 2 to continue, or invoke Skill 3 if [M] = 0."

**Final completion (all intents `[detailed]`):**
- Spec is fully filled
- Section 7.5 reports zero pending
- Skill 2 instructs the user to invoke Skill 3

### 5.7 Skill 2 anti-list

Skill 2 explicitly does **not**:

- Modify spec sections 1, 2, 3, 4, 4.5.1, 4.5.2, 4.5.4 (Skill 1's domain)
- Change an intent's Response Type (that's a structural change requiring Skill 1 patch mode)
- Add or remove intents (Skill 1)
- Modify transitions (Skill 1)
- Run the §15.4 cross-reference pass (Skill 3)
- Emit wire-format JSON (Skill 3)
- Walk past a batch checkpoint without user confirmation
- Mark an intent `[detailed]` without passing the §5.5 checklist

---

## 6. Skill 3 — JSON Assembler & Publish

### 6.1 Purpose and scope boundary

Skill 3 is mechanical. It reads the completed Agent Spec and emits a Voicenter wire-format Bot JSON. It makes no creative decisions. It does not interpret ambiguous content; if the spec doesn't parse against the strict template (§3.7), Skill 3 reports a structured parse error and refuses to assemble.

**What Skill 3 owns:**
- Strict-template parsing of the Agent Spec
- Mechanical mapping of spec sections to Voicenter wire-format paths per Doc 1 §4-13
- The §15.4 cross-reference pass (authoritative, blocking)
- ID placeholder strategy per Doc 1 §15.3 Option A (sequential negative integers)
- Quirk preservation per Doc 1 §16
- Fail-loud sentinel emission for unknown values
- Final JSON output, ready for the user's manual import (v1)

**What Skill 3 does not own:**
- Authoring any text content (Skills 1 and 2)
- Making any decision about bot behavior (Skills 1 and 2)
- Validating content quality (Skills 1 and 2; Skill 3 only validates structural correctness)
- v2/v3 capabilities like MCP push (deferred)

### 6.2 Operating principle: pure parser, not interpreter

Skill 3 has one operating mode: parse the spec deterministically, map each parsed element to its wire-format path, emit. There is no "best-effort" interpretation of ambiguous spec content. If the spec deviates from the strict template:

- Skill 3 reports the deviation: line number, expected pattern, found content
- Skill 3 does not emit JSON
- The user fixes the spec (or invokes Skill 1 patch mode if the deviation reflects a structural problem) and re-invokes Skill 3

**Why pure parsing:** the entire skill architecture rests on Skill 3 being deterministic. If Skill 3 interprets, then "what JSON does this spec produce?" depends on Skill 3's mood. Spec-driven loses its meaning. Pure parsing preserves the contract: the spec is the source of truth, the JSON is a mechanical projection.

### 6.3 Spec-to-wire-format mapping

The mapping is documented per Doc 1 section. For each spec section, Skill 3 follows a deterministic mapping rule.

**Spec section 1 (Bot Identity) → wire-format paths:**

| Spec field | Wire-format path |
|---|---|
| Bot Name | `<root>.Name` |
| Description | `<root>.Description` |
| Account ID | `<root>.AccountID` |
| Primary Language | `<root>.ActiveVersionInfo.AIModelConfig.created.generationConfig.speechConfig.languageCode` |
| Voice Name | `<root>.ActiveVersionInfo.AIModelConfig.created.generationConfig.speechConfig.voiceConfig.prebuiltVoiceConfig.voiceName` |
| AI Model Config Name (catalog map → IDs) | `<root>.AiModelConfigID`, `<root>.AiModelConfig.AIModelConfigID`, etc. (mirrored top-level + version-level per Doc 1 §6) |

**Channel-conditional emission (per decision D):**
- If channels active = voice or voice+chat: emit `voiceInstructions` with user content
- If channels active = chat only: emit `voiceInstructions` with the templated default (marked `[default — not user-authored]` in spec)
- Same logic for `chatInstructions` based on chat channel state

**Spec section 2 (Persona Bundle) → `<root>.ActiveVersionInfo.AIModelConfig.prompts`:**

Direct field-to-field mapping:
- `persona` → `prompts.persona`
- `voiceInstructions` → `prompts.voiceInstructions`
- `chatInstructions` → `prompts.chatInstructions`
- `intentInstructions` (bot-level) → `prompts.intentInstructions`
- `openingAnnouncement` → `prompts.openingAnnouncement`

**Spec section 3 (Caller Silence Behavior) → `<root>.ActiveVersionInfo.AIModelConfig.silence_behaviour`:**

If `[not configured]`: omit the entire `silence_behaviour` field from the wire format.
If configured: direct field-to-field mapping.

**Spec section 4 (Intent List, structural) + Spec section 5 (Intent Details) → `<root>.intentList.intents[]`:**

Per intent, Skill 3 builds a single `intents[]` entry per Doc 1 §9.0 (the 16-field skeleton). Mapping:

- `IntentId` ← assigned placeholder (sequential negative integer, per §6.5 below)
- `Name` ← spec section 4 "Display name"
- `Description` ← spec section 4 "Description"
- `IntentToolName` ← spec section 4 "Tool name" (= identifier)
- `HandlingInstructions` ← `null` (preserved quirk per Doc 1 §16)
- `IsSilenceIntent` ← `false` (default; v1 doesn't generate silence handler intents)
- `IntentCategoryId` ← single default category placeholder
- `Priority` ← `1` (per Doc 1 §9.0)
- `MaxAttempts` ← `3` (per Doc 1 §9.0)
- `ValidationTimeout` ← `30` (per Doc 1 §9.0)
- `IntentParameters[]` ← built from spec section 5 slot list (§6.4 below)
- `IntentConfig.prompts.llmDescription` ← `""` (preserved per Doc 1 §16)
- `IntentConfig.prompts.validationPrompt` ← spec section 5 "Validation Prompt"
- `IntentScripts` ← `{}` (preserved per Doc 1 §16)
- `IntentResponces` ← built from spec section 5 RT-specific fields (§6.4 below)
- `IsActive` ← `1`
- `IsDeleted` ← `0`

**`<root>.intentList.botIntents[]`:** one entry per intent, with `BotIntentTypeID = 1` (start-marker) for the first entry per the spec's section 4 ordering, and matching `IntentID` references.

**`<root>.intentList.intentRelations[]`:** built from spec section 4 "Transitions out" — one row per (origin, next) pair with `Order` from the spec's transition list.

**`<root>.intentList.intentCategories[]`:** one default category entry, all intents reference it.

**`<root>.intentList.silenceRelations[]`:** `[]` (per Doc 1 §17, v1 always empty).

**`<root>.intentList.apiSilenceRelations[]`:** built from spec section 5 — one entry per RT=2 intent, mirroring the embedded `api_silence_behaviour` in the intent's `Configuration`.

**Spec section 4.5 (Available Variables):** not directly emitted into wire format. Used only to validate Mustache references during the cross-reference pass.

**Spec section 6 (Cross-References):** not directly emitted. Used as a sanity-check input to the cross-reference pass.

**Spec section 7 (Generation Metadata):** the unknowns from 7.4 drive sentinel emission; the rest is logged as a banner comment in the JSON header (or as a separate metadata file alongside, depending on runtime).

### 6.4 RT-specific Configuration assembly

For each intent, Skill 3 assembles `IntentResponces.Configuration` per the intent's Response Type:

**RT=1 (Layer Transfer):**
```
IntentResponces:
  ResponseTypeId: 1
  Configuration:
    layer: <spec section 5 "Layer"> | -999 if <UNKNOWN>
    announcement: <spec section 5 "Announcement">
    intentLoadingAnnouncement: <spec section 5 "Loading announcement">
```

**RT=2 (API Call):**
```
IntentResponces:
  ResponseTypeId: 2
  Configuration:
    url: <spec section 5 "URL"> | "<USER_TO_FILL: webhook_url>" if <UNKNOWN>
    method: <spec section 5 "Method">
    headers: <spec section 5 "Headers"> | {} if not specified
    body: <spec section 5 "Body">
    apiResponseAnnouncement: <spec section 5 "API response announcement">
    fail_output: <spec section 5 "Failure output">
    function_output: <spec section 5 "Function output (LLM guidance)">
    intentLoadingAnnouncement: <spec section 5 "Loading announcement">
    IntentLoadingAnnouncement: <spec section 5 "Loading announcement">  # quirk: same content as lowercase variant
    intentInstructions: <spec section 5 "Post-Execution Intent Instructions">
    api_silence_behaviour: { ... built from spec section 5 "API silence behavior" ... }
    response_success: ""  # preserved per Doc 1 §16
```

Plus the corresponding `apiSilenceRelations[]` registry entry — identical content, mirrored per Doc 1 §11.2.

**RT=3 (Continue):**
```
IntentResponces:
  ResponseTypeId: 3
  Configuration:
    announcement: <spec section 5 "Announcement">
    intentInstructions: <spec section 5 "Post-Execution Intent Instructions">
    response_success: ""  # preserved per Doc 1 §16
```

**RT=4 (Dial-Out):**
```
IntentResponces:
  ResponseTypeId: 4
  Configuration:
    phone3: <spec section 5 "Phone destination"> | "<USER_TO_FILL: phone3>" if <UNKNOWN>
    parameter_phone: <spec section 5 "Parameter holding phone">
    NEXT_VO_ID: <spec section 5 "NEXT_VO_ID"> | -999 if <UNKNOWN>
    MAX_DIAL_DURATION: <spec section 5 "Max dial duration">
    selectdial_option: <spec section 5 "Select-dial option">
    record: <spec section 5 "Record">
    announcement: <spec section 5 "Announcement">
    intentLoadingAnnouncement: <spec section 5 "Loading announcement">
```

**`IntentParameters[]` per intent:**

Per slot in spec section 5:
```
{
  ParameterId: <placeholder negative integer>,
  IntentId: <parent intent placeholder>,
  Name: <slot name>,
  Description: <slot description>,
  IsRequired: <slot required flag>,
  DefaultValue: <slot default value> | null,
  CollectionOrder: <slot order>,
  ParameterTypeId: <slot type ID>,
  ParameterType: { ParameterTypeId: <id>, Name: <type name> },  # denormalized echo
  OptionList: <slot option list> | [],
  ValidationRules: {},  # preserved per Doc 1 §16
  ValidationPattern: null,  # preserved per Doc 1 §16
  IsActive: 1,
  IsDeleted: 0
}
```

### 6.5 ID placeholder strategy

Per decision (Doc 1 §15.3 Option A), Skill 3 emits sequential negative integers for all platform-assigned IDs. The actual integer values don't matter — internal consistency does.

**Allocation order:**

1. Top-level: `BotID = -1`, `AccountID = <user-supplied>`, `BotVersionId = -2`
2. AI model: `AIModelConfigID`, `AIModelTypeId` from catalog or user-supplied (not placeholders if catalog-mapped)
3. Categories: `IntentCategoryId = -3` (single default category)
4. Intents: `IntentId = -10, -11, -12, ...` (one per intent in spec section 4 order)
5. BotIntents: `BotIntentID = -100, -101, ...` (one per intent)
6. Parameters: `ParameterId = -1000, -1001, ...` (one per slot, per intent)

The numerical ranges are wide so a human reading the JSON can identify what kind of ID a placeholder represents at a glance. Real platform-assigned IDs after import will be positive integers, so there's no collision risk.

**Backreference propagation:** wherever an ID is referenced in another part of the JSON (e.g., `intentRelations[].OriginIntentID`, `IntentParameters[].IntentId`, `apiSilenceRelations[].OriginIntentID`), Skill 3 substitutes the placeholder consistently. The cross-reference pass (§6.6) validates this.

### 6.6 The §15.4 cross-reference pass

Per Doc 1 §15.4, before emitting JSON, Skill 3 runs seven validation checks:

1. Every `botIntents[].IntentID` matches an `intents[].IntentId`
2. Every `intentRelations[].OriginIntentID` and `.NextIntentID` matches an `intents[].IntentId`
3. Every `apiSilenceRelations[].OriginIntentID` and `.ApiSilenceIntentID` matches an `intents[].IntentId`
4. Every `intents[].IntentCategoryId` matches an `intentCategories[].IntentCategoryId`
5. Every RT=2 intent has a corresponding `apiSilenceRelations[]` entry
6. Every RT=2 intent's `Configuration.api_silence_behaviour` content matches its `apiSilenceRelations[].Configuration` content (the duplication rule per Doc 1 §11.2)
7. Every Mustache slot variable resolves: collected by an earlier intent, in the system-variable whitelist (sections 4.5.1 + 4.5.2), or a dotted API path declared in section 4.5.4 for an RT=2 intent

**Failure mode:** any check fails → Skill 3 emits a structured error pointing to the offending field path and the spec section that owns the violation. Does not emit JSON. User goes back to Skill 1 (if the violation is structural — sections 1-4) or Skill 2 (if the violation is content — section 5) to fix.

**Passing all 7 checks:** Skill 3 proceeds to emission.

### 6.7 Quirk preservation per Doc 1 §16

Skill 3 emits exactly what production samples emit, even where it looks redundant or wrong:

| Quirk | Skill 3 behavior |
|---|---|
| `IntentResponces` typo | Emit as `IntentResponces` (never autocorrect) |
| `intentLoadingAnnouncement` + `IntentLoadingAnnouncement` | Emit both, identical content |
| `HandlingInstructions: null` | Emit `null` |
| `SystemPrompt: ""` | Emit `""` |
| Top-level `AiModelConfig` + `ActiveVersionInfo.AIModelConfig` | Emit both, with `created` payload identical |
| `tools: []` and `instructions: ""` inside `AIModelConfig` | Emit empty values |
| `IntentScripts: {}` | Emit `{}` |
| `ValidationRules: {}` | Emit `{}` |
| `ValidationPattern: null` | Emit `null` |
| `IntentConditionList: []` (empty in v1) | Emit `[]` |
| `silenceRelations: []` (v1) | Emit `[]` |
| `BotLanguages: []` | Emit `[]` |
| `llmDescription: ""` | Emit `""` |
| `response_success: ""` | Emit `""` |

### 6.8 Fail-loud sentinel emission

For each `<UNKNOWN: ...>` marker in the spec (aggregated in section 7.4), Skill 3 emits a fail-loud sentinel per the type:

| Spec marker | Wire-format emission |
|---|---|
| `<UNKNOWN: webhook_url>` | `"<USER_TO_FILL: webhook_url>"` (string) |
| `<UNKNOWN: layer ID>` | `-999` (integer) |
| `<UNKNOWN: NEXT_VO_ID>` | `-999` |
| `<UNKNOWN: phone destination>` | `"<USER_TO_FILL: phone3>"` |
| `<UNKNOWN: Account ID>` | `-999` |
| `<INCOMPLETE: ...>` (spec section partial) | section emitted with available content; banner notes incompleteness |
| `[not configured]` | section omitted from wire format |

**Banner comment in JSON header:** Skill 3 prepends a JSON-comment-style header (or sidecar metadata file) listing all sentinels emitted, with their field paths and human descriptions. The user reads this before importing.

Example banner content:
```
# Generated by Voicenter Bot JSON skills v1
# Date: 2026-05-01
# Source: agent-spec.md (version 1.0.0)
#
# UNKNOWN VALUES — user must replace before import:
#   - intents[0].IntentResponces.Configuration.url ("<USER_TO_FILL: webhook_url>")
#   - intents[5].IntentResponces.Configuration.layer (-999)
#   - <root>.AccountID (-999)
```

### 6.9 Skill 3 output

**On successful assembly:**
- One JSON file conforming to Doc 1 wire format
- Banner header / sidecar metadata file listing sentinels and source spec
- Section 7.3 of the spec gets a final entry: `[ISO timestamp] Skill 3 assembled — emitted bot.json with N sentinels`

**On parse or cross-reference failure:**
- No JSON emitted
- Structured error report: failure type, field path, spec section to fix, recommended skill to invoke (Skill 1 patch mode or Skill 2 reactivation)
- Section 7.3 records the failure

**Runtime-specific delivery:**
- Single-conversation: Skill 3 outputs the JSON inline (with code block formatting); user copies and saves locally
- Claude Code: Skill 3 writes `bot.json` to the workspace; user retrieves the file

### 6.10 Skill 3 anti-list

Skill 3 explicitly does **not**:

- Author any text (no Skill 1 or Skill 2 work)
- Interpret ambiguous spec content (pure parse, no heuristics)
- Fix cross-reference failures by inventing values (failures route back to user)
- Modify the spec (read-only access)
- Skip the cross-reference pass under any circumstances
- Suppress fail-loud sentinels (they're the entire point of the unknown-value model)
- Emit JSON if any of the 7 cross-reference checks fail
- Run iteratively or repeatedly within a single invocation (one parse, one cross-ref pass, one emission)

---

## 7. Validation Strategy: Iron Rules and Where They Live

### 7.1 The validation surface

The skills enforce two distinct categories of rules from Doc 1:

**Category 1 — Iron rules from Doc 1 §14.3.** Content-quality rules. Catch design mistakes that produce legal but misbehaving bots. Examples: empty persona, free prose where Conversation Routines is required, channel content in global persona, slot type mismatch.

**Category 2 — Cross-reference and structural integrity from Doc 1 §15.4.** Mechanical-correctness rules. Catch internal inconsistencies that produce legal-shaped JSON the platform can import but the runtime can't execute. Examples: dangling intent references, missing API silence pairings, unresolvable Mustache.

### 7.2 Allocation principle: validate at the earliest skill that has the information

Each rule fires in the skill that:
- Has the data needed to evaluate the rule
- Is authoring or modifying the data being evaluated
- Can route the user to a fix without unnecessary handoffs

Earlier validation catches errors closer to their source. Late validation (e.g., everything in Skill 3) means failures route the user backward through the pipeline, costing rework. Early validation means the error fires while the user is still thinking about the relevant decision.

### 7.3 The split across the three skills

#### Skill 1 owns structural rules and persona-coherence rules

Skill 1 has the full structural picture by end of phase 3: identity, persona text, channel scope, intent list, transitions, available variables. It validates:

| Rule | Source | When |
|---|---|---|
| Persona is non-empty, articulates identity/role/tone/language | §14.3.1 | Phase 2 self-check |
| No channel-specific content in persona | §14.3.9 | Phase 2 self-check |
| No per-intent procedural logic in persona | §14.3.10 | Phase 2 self-check |
| No persistent policy embedded in single intents | §14.3.13 | Phase 3+ self-check |
| Persona's claimed capabilities ⊆ intent set | §14.3.7 | Phase 3 boundary |
| Naming convention (snake_case verb_object) | §14.3.8 | Phase 3 |
| Every non-terminal intent has escalation transition | §14.3.4 | Phase 3 self-check |
| Active-channel `prompts` fields populated | §14.3.1 | Phase 2 self-check |
| Mustache references resolve (advisory) | §14.3.5 / §15.4 item 7 | Phase 4 |

#### Skill 2 owns content-shape rules

Skill 2 writes the language-heavy fields. It self-validates against §14.3 misplacement rules:

| Rule | Source | When |
|---|---|---|
| `validationPrompt` is Conversation Routines styled | §14.3.2 | Per intent, before marking `[detailed]` |
| `validationPrompt` covers every slot in the intent | §14.3.2 | Per intent |
| `validationPrompt` includes at least one IRON RULE block | §14.3.3 | Per intent |
| Slot type matches purpose | §14.3.3 | Per intent |
| `intentInstructions` is Conversation Routines styled | §14.3.2 | Per intent |
| `intentInstructions` does not contain slot collection logic | §14.3.12 | Per intent |
| `intentInstructions` does not contain persistent policy | §14.3.13 | Per intent |
| `intentInstructions` does not contain bot-level disambiguation | §14.3.11 | Per intent |
| Mustache references resolve (blocking) | §14.3.5 / §15.4 item 7 | Per intent |
| For RT=2: API call fields fully populated | §14.3.6 | Per intent |
| For RT=2: API silence behavior fully populated | §14.3.6 | Per intent |

#### Skill 3 owns the §15.4 cross-reference pass

Skill 3 runs all seven checks per §15.4 against the assembled JSON before emission:

1. Every `botIntents[].IntentID` matches an `intents[].IntentId`
2. Every `intentRelations[].OriginIntentID` and `.NextIntentID` matches an `intents[].IntentId`
3. Every `apiSilenceRelations[].OriginIntentID` and `.ApiSilenceIntentID` matches an `intents[].IntentId`
4. Every `intents[].IntentCategoryId` matches an `intentCategories[].IntentCategoryId`
5. Every RT=2 intent has a corresponding `apiSilenceRelations[]` entry
6. Every RT=2 intent's `Configuration.api_silence_behaviour` content matches its `apiSilenceRelations[].Configuration`
7. Every Mustache slot variable resolves against the §4.5 inventory + section 5 slot collection order

### 7.4 Severity model

**Blocking failures.** The skill does not advance until the user resolves the failure.
- Skill 1: blocking failures prevent the spec from being declared "ready for Skill 2"
- Skill 2: blocking failures prevent an intent from being marked `[detailed]`
- Skill 3: blocking failures prevent JSON emission

**Advisory failures.** The skill records the issue and continues. The user is informed but not blocked.
- Skill 1's Mustache pre-check is the primary advisory category. False positives are possible because the user may resolve a reference later in the interview (e.g., reference an upstream intent's slot before that intent is fully detailed). Skill 1 flags, doesn't block.
- Skill 3's Mustache check is the authoritative version of the same rule, blocking. By Skill 3 time, all slots are known.

**Why the split:** Skill 1 needs to surface potential issues without freezing the interview every time the user mentions a variable that hasn't been defined yet. Skill 3 has full information and can be unambiguous about resolution. Two passes, one advisory and one authoritative.

### 7.5 Routing failures back to the responsible skill

When Skill 3 detects a violation, it tells the user which skill to invoke for the fix:

| Violation type | Route to | Why |
|---|---|---|
| Missing escalation transition (§14.3.4) | Skill 1 patch mode | Structural change to section 4 |
| Persona-claims-vs-intents mismatch (§14.3.7) | Skill 1 patch mode | Touches both section 2 and section 4 |
| Naming convention violation (§14.3.8) | Skill 1 patch mode | Identifier rename, section 4 |
| Channel content misplacement (§14.3.9) | Skill 1 patch mode | Section 2 |
| Free prose in `validationPrompt` (§14.3.2) | Skill 2 reactivation | Section 5 content |
| Misplaced policy in `intentInstructions` (§14.3.10-13) | Skill 2 reactivation | Section 5 content |
| Cross-reference dangling ID | Skill 1 patch mode (likely structural) | Section 4-related |
| RT=2 missing API silence pairing | Skill 1 patch mode | Section 5 RT-specific structural |
| Mustache unresolvable | Skill 1 patch mode (if reference is structural) or Skill 2 reactivation (if content) | Depends on where reference lives |

### 7.6 What this validation strategy guarantees

If the spec passes Skill 1 → Skill 2 → Skill 3 without violations, then:

- The wire-format JSON conforms structurally to Doc 1's contract
- Every Mustache reference resolves at runtime
- Every RT=2 intent has the registry pairing the platform expects
- No iron rule from §14.3 is violated by the spec content
- No internal cross-reference is dangling

What it does not guarantee:
- That the bot performs well at runtime. Performance is a function of content quality, which Skill 1's persona authoring and Skill 2's `validationPrompt`/`intentInstructions` authoring shape but cannot fully validate. The user's review at each skill checkpoint is the final filter.
- That all `<UNKNOWN: ...>` markers have been replaced with real values before import. The fail-loud sentinels surface them; the user must act.
- That the platform-supplied call-context variables actually exist on the user's account. Skill 1 captures the user's claim; Skill 3 trusts it.

---

## 8. User Workflow

### 8.1 The linear happy path

1. **User invokes Skill 1 (greenfield)** — no prior spec attached
2. **Phase 1-4 interview** — Skill 1 builds spec sections 1-4, 4.5, 5 with all intents marked `[structural]`
3. **Skill 1 self-validates** against §7.3 rules; emits the spec
4. **User reviews the spec** — reads through, notes anything needing correction
5. **User invokes Skill 2** — spec attached (single-conv: in conversation context; Claude Code: in workspace)
6. **Skill 2 proposes batching plan** — user confirms or overrides
7. **Skill 2 walks each batch** with confirmation gates between batches
8. **At final batch completion**, Skill 2 reports all intents `[detailed]` and instructs to invoke Skill 3
9. **User invokes Skill 3** — spec attached
10. **Skill 3 parses and runs cross-reference pass**
11. **If pass: Skill 3 emits JSON** with banner identifying any sentinels
12. **User reviews JSON**, replaces any `<USER_TO_FILL: ...>` strings or `-999` IDs with real platform values
13. **User imports JSON** to Voicenter platform manually (v1 lifecycle)

### 8.2 Reactivation paths

#### Reactivating Skill 2

User left some intents `[structural]` in a prior Skill 2 invocation, or Skill 1 patch mode reset some intents to `[detailed-revisit]`. User invokes Skill 2 again.

- Skill 2 reads spec, scans section 5
- Identifies remaining intents requiring detailing
- Proposes a new batching plan covering only those intents
- User confirms or overrides
- Walks batches per §5.3

No special invocation syntax. Spec state drives behavior.

#### Reactivating Skill 1 (patch mode)

User has a fully `[detailed]` spec — or partially, if patch fires mid-Skill-2 — and wants to change something structural. User invokes Skill 1 with the spec attached.

- Skill 1 detects spec → patch mode
- Asks what to change
- Computes cascade impact
- Surfaces affected intents
- User confirms
- Skill 1 modifies spec; affected intents marked `[detailed-revisit]`
- User invokes Skill 2 to redetail affected intents
- Then Skill 3

### 8.3 Failure recovery

#### Skill 1 self-validation blocks completion

User can:
- Fix the issue and have Skill 1 re-validate
- Decide the issue isn't a real problem (rare, since these are blocking iron rules) and contest with Skill 1; Skill 1 may explain the rule and require a fix anyway

Recovery is in-conversation; no skill change needed.

#### Skill 2 self-validation blocks an intent

Skill 2 won't mark the intent `[detailed]`. User can:
- Edit the offending field with Skill 2's guidance
- If the issue is structural (the intent shouldn't exist, or has the wrong RT, or the wrong slots), pause Skill 2, invoke Skill 1 patch mode, fix structurally, return to Skill 2

#### Skill 3 cross-reference pass fails

Skill 3 doesn't emit JSON. User reads the structured error, identifies which skill to invoke for the fix per §7.5 routing table, makes the fix, re-invokes the chain (Skill 1 patch → Skill 2 reactivation if needed → Skill 3).

If the failure is in cross-reference checks 1-4 (ID dangling) or check 5 (missing API silence pairing), the cause is almost certainly a Skill 1 structural error during patch mode. Most common case: an intent was deleted but its references in `intentRelations[]` weren't fully cleaned up — Skill 1 patch mode handles this in v2; in v1, the user reopens patch mode and explicitly removes the reference.

If the failure is in check 6 (api_silence_behaviour mismatch with apiSilenceRelations), this is a Skill 3 internal error (Skill 3 mirrors them). User should report; the skill itself needs a fix. Should not happen in normal use.

If the failure is in check 7 (Mustache unresolvable), the cause is content: a reference to an undefined variable. User invokes either Skill 1 patch mode (to add a variable to section 4.5) or Skill 2 reactivation (to remove the bad reference from per-intent text), depending on whether the variable should exist.

### 8.4 Runtime-specific workflow notes

#### Single-conversation runtime (Claude UI)

- All three skill invocations happen in one conversation
- Spec lives as the most recent message produced by whichever skill last ran
- Skill transitions: user types something like "OK now run Skill 2" — Skill 2 reads the conversation backward to find the latest spec
- Conversation length is the practical constraint. ≤8 intents recommended (per decision E)
- If conversation gets long, the user can copy the latest spec to a new conversation and continue there — all skills are stateless beyond the spec

#### Claude Code runtime

- Spec lives as `agent-spec.md` (or similar) in the workspace
- Each skill invocation reads the file, modifies it, writes it back
- Skill invocations can span multiple Claude Code sessions; the file persists
- Conversation length per session is less constrained; the file is the durable state
- Up to ~20 intents recommended (per decision E)
- If a session ends mid-batch in Skill 2, the spec captures the state — next session reads it and resumes

#### Choosing a runtime

Skill 1 detects context and adapts. The user makes the runtime choice implicitly (they invoke from Claude UI or from Claude Code). If a user starts in Claude UI for a small bot and discovers it's getting larger, they can copy the spec out, switch to Claude Code, and continue — same skills, same spec, different state mechanic.

### 8.5 What the user is responsible for

The skills do a lot, but not everything. The user must:
- Provide complete and accurate inputs at the interview stage
- Review the spec at each handoff (between Skill 1 and Skill 2, between Skill 2 and Skill 3)
- Replace fail-loud sentinels with real values before importing JSON
- Import the JSON manually to the Voicenter platform
- Verify the bot's behavior at runtime; report bugs back to the skill team if the skills produced something wrong

The skills do **not** test the bot. v1 has no runtime simulation, no automated testing of the deployed bot's behavior. That's the user's responsibility post-import.

---

## 9. Out of Scope for v1 Architecture

This section enumerates what v1 deliberately does not include, with pointers to where each capability lands.

### 9.1 Skill-to-skill direct invocation

Skills are user-invoked. Skill 1 cannot call Skill 2; Skill 2 cannot call Skill 3. The user invokes each skill explicitly.

Rationale: user retains control over pacing, can pause between skills, can review the spec at any handoff. The cost — manual transitions — is intentional.

Lands in: not planned. The user-driven model is permanent through v3. v5 (autonomous iteration) may revisit.

### 9.2 Automated state detection

Skills do not infer "I should be Skill 2 now" from the spec state. The user picks which skill to invoke. If they invoke Skill 1 with a fully-detailed spec, Skill 1 enters patch mode (because a spec was attached) but does not autonomously delegate to Skill 2.

Rationale: same as §9.1 — user control. Auto-routing introduces failure modes (spec misclassification, infinite loops between skills) that are not worth the convenience gain in v1.

Lands in: possibly v3 or v4, if user feedback indicates auto-routing would meaningfully reduce friction.

### 9.3 Update flow on deployed bots

v1 patch mode operates on a spec in the current pipeline only. If the user wants to modify a deployed bot, they must export its current configuration, re-create a spec from it, and run the full pipeline. v1 does not provide mechanisms for this re-creation.

Rationale: deployed-bot updates require MCP read access (to fetch current state) and MCP write access (to push deltas). v1 has neither.

Lands in: v3 per Doc 1 §18.3 — full update flow with diff and incremental push.

### 9.4 Drift detection, monitoring, autonomous iteration

v1 skills do not monitor deployed bots, do not detect drift in call data, do not propose changes proactively. The skill is invoked when the user wants something; otherwise it is silent.

Rationale: autonomy requires data access (call history, KPIs), drift baselines, and approval workflows that v1 explicitly defers.

Lands in: v5 per Doc 1 §18.5 — autonomous iteration via Mastra Continuous Mode pipeline.

### 9.5 KB integration

v1 skills do not consult external knowledge bases, do not integrate with the Voicenter KB, do not pull from web sources at design time. The Deep Research nudge is the one exception: the *user* pursues research separately and brings findings back. The skill does not query.

Rationale: τ-Knowledge principle — KB is a build-time resource consumed at design time, not a runtime resource queried by the skill. v1 keeps the user as the bridge between research and design.

Lands in: not directly planned. KB integration is part of the larger Mastra Agent Generator project, not the Bot JSON skill project.

### 9.6 Multi-bot orchestration

v1 produces one bot per pipeline run. Designing a system of multiple bots that coordinate (e.g., a top-level dispatcher that routes to specialized sub-bots) is out of scope.

Rationale: the Voicenter Bot JSON is single-bot scoped. Multi-bot orchestration is a platform-level concern, not a skill-level one.

Lands in: not planned for this skill suite.

### 9.7 Schema gaps from Doc 1 §17

v1 skills handle the schema as documented in Doc 1 v1 — the four observed RTs, the four observed `ParameterTypeId` values, the empty-but-required fields, the preserved quirks. Doc 1 §17 lists 12 gaps (G-1 through G-12) where the schema is partially-known.

When Doc 1 advances to v2 (closing some gaps), the skills update accordingly. The skills track Doc 1 versions; they do not invent solutions for gaps Doc 1 hasn't closed.

Lands in: skill updates triggered by Doc 1 version bumps, not by independent skill development.

---

## 10. Handoff to SKILL.md Authoring

This document specifies the architecture. The next phase is authoring the three SKILL.md files — one per skill — that implement the architecture. Each SKILL.md is the actual instruction file Claude reads at skill-invocation time; this document is the reference its content derives from.

§4 here drives Skill 1's SKILL.md. §5 drives Skill 2's. §6 drives Skill 3's. §3 (the Agent Spec format) is shared infrastructure all three SKILL.md files reference.

The SKILL.md authoring for the three skills happens in three separate conversations (Conv 3, 4, 5 of the project per `project-map.md`). Each one inherits this document and Doc 1, and produces one SKILL.md file plus supporting templates.

Once all three SKILL.md files exist, end-to-end testing (Conv 6) validates the full pipeline against a known-good production sample (Yuval primary, Refua secondary).

---

*— End of Skill Architecture v1 —*

**Document version:** 1.0
**Date:** May 2026
**Sources:** `voicenter-bot-json-schema-audit-v1.md` (Doc 1), `locked-decisions.md`, `project-map.md`
**Status:** v1 locked at end of Conv 2
