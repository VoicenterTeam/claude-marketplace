---
name: voicenter-bot-json-assembler
description: Assembles a fully-detailed Voicenter Agent Spec into Bot JSON wire format — the final mechanical step in the three-skill pipeline. Use this skill when an Agent Spec exists with all section 5 entries marked `[detailed]` and the user wants the deployable JSON. Trigger phrases include "run Skill 3", "assemble the JSON", "emit the bot JSON", "publish the bot", "build the wire-format", "Skill 3 (JSON Assembler)", or any direct continuation from Skill 2's completion handoff. Produces a single `bot-<name>-<date>.json` file plus a banner identifying every fail-loud sentinel and any drift between spec section 6 and what Skill 3 regenerated. Refuses to assemble if any intent is still `[structural]` or `[detailed-revisit]`, or if the spec deviates from the strict template (Doc 2 §3.7). Runs the §15.4 cross-reference pass — 24 checks (8 §15.4 + 3 Compass + 3 botIntents-role + 1 duplicate-global-intent + 9 field-placement doctrine), checks 1–7, 11–13, 15, 16–21, and 24 blocking. Does NOT author any text content (Skills 1 and 2 only). Does NOT make creative decisions, interpret deviations, fix violations, or invoke other skills (it reports routing recommendations; the user invokes the relevant skill).
---

> **Language.** Reply in the user's language: detect what they write — Hebrew→Hebrew, English→English — and mirror it, switching if they switch mid-conversation. This shapes your prose, your questions, and your `AskUserQuestion` option labels only. It does **not** change the artifacts you produce — identifiers, JSON keys, BCP-47 language codes, API field names, and other data stay exactly as specified.

> **Opening.** Your first message greets bilingually so the user knows both languages are available — e.g. *"נוכל להמשיך בעברית או באנגלית — מה נוח לך? / We can continue in Hebrew or English — whichever you prefer."* Then mirror whatever language the user replies in.

> **One question per turn.** Ask exactly one question per message and wait for the answer before asking the next — never present multiple questions in a single turn. When the answer is a closed set (pick-one / yes-no / pick-from-list), use the `AskUserQuestion` tool rather than plain text; it automatically adds an "Other" free-text escape, so don't hand-roll one. Reserve plain free-text questions for genuinely open inputs (names, descriptions, URLs, numbers).

# Skill 3 — JSON Assembler & Publish

This skill produces the **deployable Bot JSON** by mechanically projecting a fully-detailed Agent Spec into Voicenter wire-format. It is the third and final skill in the Voicenter Bot generation pipeline:

- **Skill 1 (Agent Spec Designer):** structural design via interview → fills sections 1, 2, 3, 4, 4.5; creates section 5 stubs marked `[structural]`.
- **Skill 2 (Intent Detail Author):** language-heavy per-intent content → fills section 5 entries, marks them `[detailed]`.
- **Skill 3 (this skill):** mechanical assembly of spec → wire-format JSON.

**Operating principle: pure parser, not interpreter.** Skill 3 makes no creative decisions. It does not best-effort interpret ambiguous spec content; if the spec deviates from the strict template, Skill 3 reports a structured parse error and refuses to assemble. The entire skill architecture depends on Skill 3 being deterministic — if Skill 3 interprets, "what JSON does this spec produce?" depends on Skill 3's mood, and the source-of-truth contract dies. Discipline is the design.

The risk vector for this skill is **doing too much**: filling in plausible-looking values for unknowns, smoothing over template deviations, auto-fixing cross-reference violations, deciding RT-specific defaults the spec didn't specify. The anti-list (§8) is the longest and most opinionated section — read it before doing anything else.

---

## 1. Required reading at invocation

Before touching the spec, load context from these references.

| Read | Why |
|---|---|
| Doc 1 §4 — Bot top-level wrapper | Mapping for spec section 1 root fields |
| Doc 1 §5 — `ActiveVersionInfo` envelope | Mapping for version-level fields |
| Doc 1 §6 — The two `AIModelConfig` objects | Top-level vs version-level + `created` payload duplication |
| Doc 1 §7 — Crosswalk: training-doc → JSON paths | Field-name reconciliation reference |
| Doc 1 §8 — `intentList` six parallel collections | The bulk of assembly |
| Doc 1 §9 — `intents[]` 17-field skeleton | Per-intent shape |
| Doc 1 §10 — `IntentParameters` slot definitions | Per-slot shape |
| Doc 1 §11 — `ResponseTypeId` reference (RT=1/2/3/4) | RT-specific Configuration assembly (§4.4) |
| Doc 1 §11.2 — RT=2 pairing rule | CHK-05 + 6 |
| Doc 1 §12 — `ParameterTypeId` catalog | Slot type emission |
| Doc 1 §13 — Mustache + variable categories | CHK-07 |
| Doc 1 §15.3 — ID placeholder strategy (Option A) | §4.1 allocation |
| `${CLAUDE_PLUGIN_ROOT}/references/verification-procedure.md` | **The 24 checks — read and execute this; §6 only decides which path runs it** |
| Doc 1 §16 — Schema quirks summary | §4.5 + Appendix A |
| Doc 2 §3.7 — Strict-template enforcement | §3 parse rules |
| Doc 2 §6 — Skill 3 architecture | Everything in this file implements this |
| Doc 2 §7.5 — Routing failures back | Appendix B |
| `locked-decisions.md` decision B | Sentinel strategy |
| `locked-decisions.md` decision M | Section 4.5 inventory drives Mustache check |
| `${CLAUDE_PLUGIN_ROOT}/references/voice-prompt-doctrine.md` | Compass doctrine — 13 rules; Skill 3 owns checks 8 (token budget — rule 1), 9 (session resumption — rule 2), 10 (model-config doctrine — rule 12), and the banner sentinels (rule 13) |
| `${CLAUDE_PLUGIN_ROOT}/references/field-placement-doctrine.md` | Field-placement doctrine (v1.17.0) — FP-1…FP-13 incl. the FP-3 turn-yield rule; Skill 3 owns cross-reference checks 16–24 |

Also load this file from Skill 1's package:

- `skills/voicenter-bot-spec-designer/model-catalog.md` — required for resolving named catalog entries to `AIModelConfigID` / `AIModelTypeId` and provider model string (§4.2.3).

Skill 3 does **not** load Skill 2's `conversation-routines-style-guide.md`. The style of `validationPrompt` and `intentInstructions` text is Skill 2's concern; Skill 3 emits the text verbatim from the spec, regardless of style.

---

## 2. Setup

### 2.1 Detect runtime

| Signal | Runtime |
|---|---|
| Conversation in claude.ai or mobile app, no workspace file system, no `agent-spec.md` accessible | **Single-conversation** |
| Workspace file system available (Claude Code), `agent-spec.md` readable as a file | **Claude Code** |

State the detected runtime. The user can correct.

### 2.2 Read the spec

**Single-conversation:** read backward through the conversation context to find the most recent spec emission. The spec is identifiable by its `## 1. Bot Identity` header and `## 7. Generation Metadata` footer. If both Skill 1 and Skill 2 ran in this conversation, take the most recent (Skill 2's output).

**Claude Code:** read `agent-spec.md` from the workspace (or whatever filename the user references).

**No spec found:** abort with: *"No Agent Spec found. Skill 3 requires a fully-detailed spec produced by Skill 1 → Skill 2. Invoke Skill 1 (Agent Spec Designer) first."*

### 2.3 Pre-flight gates

Three gates run before any assembly work. All are blocking. Refusal at any gate emits a clear message and halts; no JSON is produced.

#### Gate A — Completeness

Walk section 5. Count entries with status `[structural]` or `[detailed-revisit]`. If the count is greater than zero, refuse:

> Skill 3 will not assemble an incomplete spec. Section 5 has [N] intents still pending: [list with status per intent]. Run **Skill 2 (Intent Detail Author)** to detail them, then re-invoke Skill 3.

The list shows identifier + status (e.g., `validate_customer_address [structural]`, `confirm_appointment [detailed-revisit]`), not detail level.

Cross-check against section 7.5 (which Skill 2 maintains). If 7.5 says zero pending but section 5 has pending entries, that's a Skill 2 bookkeeping bug — surface it: *"Spec inconsistency: section 7.5 reports 0 pending, but section 5 has [N] intents in non-detailed state. Re-run Skill 2 once to refresh, then re-invoke Skill 3."*

#### Gate B — Parseability

Run the strict-template parser (§3) over the spec. The first deviation halts parsing and produces a structured error. No partial assembly.

Parseability is checked before completeness in cases where the file is malformed at the section-header level (e.g., section headers missing entirely) — in that case, Skill 3 cannot even tell which intents are pending. Practical order: try a quick scan for the seven `## N.` section headers first; if they're missing, Gate B fires first. If headers are present, Gate A fires first.

#### Gate C — RT=2 verification

For every intent whose section-4 **Response Type** is 2 (RT=2 / API Call), verify a matching entry exists in spec section 7.6 (the RT=2 API verification log). If any RT=2 intent has no 7.6 entry, refuse:

> Skill 3 will not assemble an RT=2 intent whose API was never verified. Intent(s) missing a section 7.6 verification record: [list]. Re-run **Skill 2 (Intent Detail Author)** on each — it hard-verifies the live API (real `curl`, 2xx + every declared response path present) and writes the 7.6 record. There is no waiver.

This is a backstop: a hard-verified spec reaches Skill 3 with every RT=2 intent already `[detailed]` (Gate A) and logged in 7.6. Gate C catches a hand-edited spec that flipped an intent to `[detailed]` without verifying.

---

## 3. Strict-template parsing

### 3.1 The deterministic parse principle

The Agent Spec template is documented in Doc 2 §3 and codified in Skill 1's `spec-skeleton.md`. Skill 3 reads it as a fixed grammar — no synonyms, no flexibility, no creative tolerance.

Specifically, the parser expects:

- **Section headers exact:** `## 1. Bot Identity`, `## 2. Persona Bundle`, `## 3. Caller Silence Behavior`, `## 4. Intent List (Structural)`, `## 4.5 Available Variables`, `## 4.6 Global/System Catalog Intents`, `## 5. Intent Details`, `## 6. Cross-References`, `## 7. Generation Metadata`. Exact strings, exact numbering, exact punctuation. `## 1: Bot Identity` is a parse error. `## Bot Identity` is a parse error.
- **Section 4.6 (optional):** either the literal `[none]`, or one or more `### Catalog Intent: <IntentId> — <Name>` blocks, each with `**Wiring:** silence-forward only|triggerable global` and a `**Definition:**` fenced ```json block. The JSON block must parse and carry a positive-integer `IntentId` and an `IntentCategoryId`. A malformed block or a non-positive `IntentId` is a parse error (§3.2) — Skill 3 does NOT repair it.
- **Field labels exact:** `**Bot Name:**`, `**Identifier:**`, `**Description:**`, `**Account ID:**`, `**Primary Language:**`, `**Channels Active:**`, `**Voice Name:**`, `**AI Model Config:**`. Bold markdown around the colon-terminated label, exactly as written.
- **Section 1 optional limit fields (v1.13.0; maxDurationLayerId default revised v1.14.0):** `**Daily limit:**` (int), `**Daily limit layer:**` (int), `**Max duration layer:**` (int), `**Daily limit sentence:**` (free text), `**Max duration sentence:**` (free text), `**IVRLayerSelect_2:**` (int). All optional; absence parses to defaults 600 / 3 / **0** / production-default sentence / production-default Hebrew sentence / 3 (see §4.2.2). A non-integer where an int is expected is a parse error.
- **Section 1 `**Negative instructions:**` (v1.16.0, optional):** free text. **Parse-only — NOT emitted to the wire JSON** (the wire field name is unverified). When present, Skill 3 emits a MANDATORY POST-IMPORT banner step telling the operator to paste the text into the UI's AI Security Settings → Negative Instructions field (§7.2). Absence ⇒ no banner step.
- **Status markers exact:** `[structural]`, `[detailed]`, `[detailed-revisit]`. No synonyms (e.g., `[done]`, `[in progress]`).
- **Unknown markers exact:** `<UNKNOWN: <description>>`, `<INCOMPLETE: <description>>`, `[not configured]`. The angle-bracket format is not optional; `(UNKNOWN: ...)` is a parse error.
- **Intent header in section 4:** `### Intent N: <identifier>` where N is the 1-based ordinal and identifier is snake_case. The number determines section 4 ordering (used for first-intent start-marker logic in `botIntents[]`).
- **Bot-intent role in section 4:** `**Bot-intent role:** <value>` where `<value>` is exactly one of `entry`, `global`, `chained`. The field is **optional**; absence is parsed as `chained`. Any other value (e.g. `start`, `escalation`, a list) is a parse error per §3.2. This field drives §4.3.3 botIntents membership/type.
- **Staggering fields in section 4 (v1.13.0, optional):** `**Captures answer to:**` (free text) and `**Asks next:**` (free text, or the literal `[none — terminal]`). Absence ⇒ the staggering-dependent checks skip for that intent.
- **Terminal outcome in section 4 (v1.13.0, optional; RT=1 only):** `**Terminal outcome:** <slot_name> = <value-part>`. Two-mode grammar: a double-quoted `<value-part>` ⇒ **fixed** mode (the exact pinned string); an unquoted free-text `<value-part>` ⇒ **captured/dynamic** mode (a description of how the value is captured or composed). A line without `<slot_name> =` is a parse error. `<slot_name>` must be snake_case and is cross-checked against the intent's slot list in CHK-20.
- **Sensitive in section 4 (v1.13.0, optional):** `**Sensitive:** true|false` only. Absence parses as `false`. Any other value is a parse error.
- **IsSilenceIntent in section 4 (v1.14.0, optional):** `**IsSilenceIntent:** true|false` only. Absence parses as `false`. Any other value is a parse error. Drives the intent-root `IsSilenceIntent` integer (§4.3.1 row 13).
- **Intent header in section 5:** `### Intent: <identifier>` (no ordinal). Identifier matches a section 4 entry.
- **Section 4.5.5 (v1.13.0, optional):** header exact `### 4.5.5 CustomData keys (per-call payload)` under `## 4.5 Available Variables`; entries `- \`{{key}}\` — <meaning>`. Absence ⇒ empty CustomData key list (CHK-07 then allows only 4.5.1–4.5.4 references).
- **Slot lines in section 4:** numbered list under `**Slots:**` heading, format `[slot_name] — \`ParameterTypeId\` [N], Required [\`true\`|\`false\`], Order [N], OptionList [if ENUM], DefaultValue [value]`. The `DefaultValue` segment is optional (v1.16.0); absence parses to `""` (the pre-v1.16.0 slot-line format without the segment remains valid).
- **Transition lines in section 4:** numbered list under `**Transitions out:**` heading, each item is a target intent identifier optionally followed by a parenthetical role label (e.g., `1. get_available_slots (success path)`).
- **RT-specific sub-labels in section 4:** for RT=1 intents, `**Layer:**` followed by an integer. For RT=2 intents, `**URL:**`, `**Method:**`, `**Headers:**`, `**Body:**`, and `**API silence behavior:**` (the silence block has six sub-bullets exact: `silence_duration:`, `silence_loops:`, `silence_sentence:`, `silence_ending_sentence:`, `silence_instructions:`, `fallback intent:`). For RT=3 intents, the RT-specific block is empty (no sub-bullets). For RT=4 intents, `**Dial source:**` (`parameter` | `static`), then either `**Parameter phone:**` (slot identifier, when dial-source=parameter) or `**Phone1:** / **Phone2:** / **Phone3:**` (when dial-source=static); plus `**selectdial_option:**`, `**NEXT_VO_ID:**`, `**MAX_DIAL_DURATION:**`, `**Record:**`, optional `**Announcement:**` / `**Loading announcement:**` / `**Post-execution intent instructions:**`, and `**Response success:**` (object with `instructions` key).

### 3.2 Parse error format

When a deviation is detected, halt and emit:

```
Skill 3 parse error.

Location: line <N> in <spec source>
Section: <section number, e.g., 4>
Expected: <pattern>
Found: <actual content, truncated to one line>

Fix: <one-line hint about the fix>

Skill 3 will not assemble. Re-run Skill 1 patch mode (if the spec was hand-edited or structurally invalid) or fix the deviation manually, then re-invoke Skill 3.
```

The `<spec source>` is the conversation message reference (single-conv) or the file path (Claude Code). Line numbers are within that source.

Skill 3 does not attempt to interpret around the deviation. It does not emit a partial JSON. It does not flag and continue. One deviation, one error, one halt.

### 3.3 Common deviations and example messages

These are illustrative — the parser is grammar-driven, not pattern-matched, so anything off-grammar surfaces. The examples here are the most common shapes the user will see.

| Deviation | Example error |
|---|---|
| Missing section header | `Expected: '## 4. Intent List (Structural)'. Found: '## Intent List'. Fix: restore the section number and exact heading.` |
| Bold field label punctuation off | `Expected: '**Bot Name:** <value>'. Found: 'Bot Name: <value>'. Fix: wrap the label in bold markdown.` |
| Unknown marker shape wrong | `Expected: '<UNKNOWN: <description>>'. Found: '(UNKNOWN: ...)'. Fix: use angle brackets and the literal token UNKNOWN.` |
| Status marker synonym | `Expected: one of '[structural]', '[detailed]', '[detailed-revisit]'. Found: '[done]'. Fix: re-run Skill 2 to set the canonical marker.` |
| Intent identifier in section 5 has no match in section 4 | `Section 5 entry 'verify_caller_id' has no matching intent in section 4. Fix: re-run Skill 1 patch mode to add the intent or remove the orphan section 5 entry.` |
| Section 4 reference to undeclared transition target | `Intent 'validate_customer_address' transitions to 'get_slots', but no intent 'get_slots' exists in section 4 (closest match: 'get_available_slots'). Fix: re-run Skill 1 patch mode to correct the transition target.` |
| Spec ends mid-intent (truncated upload) | `Section 5 entry 'confirm_appointment' has no closing structure (no following section 6 header). Fix: re-attach the complete spec.` |
| RT-specific sub-label punctuation off | `Expected: '**URL:** <value>'. Found: 'URL: <value>'. Fix: wrap the sub-label in bold markdown.` |
| Bot-intent role value off-grammar | `Expected: '**Bot-intent role:** entry\|global\|chained'. Found: '**Bot-intent role:** start'. Fix: use one of the three canonical role values (or omit for chained).` |
| Terminal outcome missing slot assignment (v1.13.0) | `Expected: '**Terminal outcome:** <slot_name> = "<fixed value>"' or '**Terminal outcome:** <slot_name> = <capture/compose description>'. Found: '**Terminal outcome:** הלקוח אישר הכל'. Fix: name the owning slot and use '=' (quote the value only when it is a fixed pinned string).` |
| Sensitive value off-grammar (v1.13.0) | `Expected: '**Sensitive:** true\|false'. Found: '**Sensitive:** yes'. Fix: use lowercase true or false (or omit for false).` |
| IsSilenceIntent value off-grammar (v1.14.0) | `Expected: '**IsSilenceIntent:** true\|false'. Found: '**IsSilenceIntent:** 1'. Fix: use lowercase true or false (or omit for false).` |

The transition-target check (last two rows) blurs into cross-reference territory — it's caught at parse time because it's a dangling identifier discoverable from sections 4-5 alone, and Skill 3 already has the data. Treating it as a parse error rather than waiting for §15.4 lets the user fix one thing at a time.

---

## 4. Spec-to-wire-format assembly

Run only if all three pre-flight gates pass and the parser succeeds. Assembly happens in memory; nothing is emitted until §6 (cross-reference pass) also passes.

### 4.1 ID placeholder allocation

Per Doc 1 §15.3 Option A and Doc 2 §6.5: sequential negative integers, range-coded so the kind of ID is identifiable at a glance.

| ID kind | Placeholder range | Allocation rule |
|---|---|---|
| `BotID` | `-1` | Single value |
| `BotVersionId` | `-2` | Single value |
| `IntentCategoryId` | `-3` | Single default category |
| `IntentId` | `-10, -11, -12, ...` | One per intent in section 4 ordering |
| `BotIntentId` | `-100, -101, -102, ...` | One per **emitted `botIntents[]` entry** (entry + global intents only — see §4.3.3), in section-4 order. Chained intents get no `BotIntentId`. |
| `ParameterId` | `-1000, -1001, -1002, ...` | One per slot, walked intent-by-intent then slot-by-slot |
| `IntentRelatedID` | `-2000, -2001, ...` | **v1.5.0:** one per `intentRelations[]` row (no longer mirrors `NextIntentID`) |
| `IntentConditionGroupID` | `-3000, -3001, ...` | One per **emitted** `botIntents[]` entry (subset — §4.3.3) + one per `intentRelations[]` row. |
| `IntentSourceID` | `-4000, -4001, ...` | **v1.5.0:** one per intent when voice channel is active |

**`IntentConditionRelationID` does not need a new range.** It mirrors `BotIntentId` (when inside `botIntents[]`) or `IntentRelatedID` (when inside `intentRelations[]`) — the production export pattern. Skill 3 fills it from the matching parent value.

**`AccountID` is user-supplied** (spec section 1) or `-999` sentinel if `<UNKNOWN: Account ID>`. Used at the bot top-level wrapper AND echoed into each `intents[].AccountId` and `intentCategories[].AccountId` (production pattern — v1.5.0).

**`AIModelConfigID` and `AIModel` (= `AIModelTypeId`) come from the model catalog** (`model-catalog.md`) per the spec section 1 entry. Skill 3 looks both up at emission time. `-999` sentinels if catalog has TODO or spec marks unknown.

**Allocation procedure:**

1. Walk section 4 in order. For each intent: assign `IntentId` from the `-10` series (every intent gets one). Assign `BotIntentId` from the `-100` series **only to intents whose `**Bot-intent role:**` is `entry` or `global`** (the `botIntents[]` subset); chained intents get an `IntentId` but no `BotIntentId`. Cache `<identifier> → IntentId` for all, and `<identifier> → BotIntentId` for the subset.
2. Within each intent's section 5 entry, walk slots in `Order` value. For each slot: assign `ParameterId` from the `-1000` series. Cache the mapping `<intent identifier>.<slot name> → ParameterId`.
3. Emit `BotID = -1`, `BotVersionId = -2`, `IntentCategoryId = -3` as fixed values.

The cached mappings are used in §4.3 wherever an ID is referenced (transition rows, parameter parent-ID, api-silence relations, botIntents references).

**Catalog intents (section 4.6) bypass placeholder allocation entirely.** Their `IntentId`, `IntentCategoryId`, `ParameterId`, `IntentScriptId`, and any nested IDs are real platform-assigned positives and are copied through verbatim. Do NOT assign them `-10`/`-1000`/`-3` placeholders and do NOT add them to the cached `<identifier> → IntentId` map used for the bot's own intents (they are referenced by real `IntentId`, not identifier).

The numerical ranges are wide so a human reading the JSON can identify what kind of ID a placeholder represents at a glance. Real platform-assigned IDs after import will be positive integers, so there's no collision risk on re-export.

### 4.2 Top-level wrapper and version envelope

#### 4.2.1 Top-level fields (spec section 1 → root)

Emit fields in this order (matches production export — v1.5.0):

| Order | Spec field | Wire-format path | Source |
|---|---|---|---|
| 1 | Bot Name | `<root>.Name` | Direct copy |
| 2 | (allocated) | `<root>.BotID` | `-1` |
| 3 | Account ID | `<root>.AccountID` | Direct copy, or `-999` sentinel if `<UNKNOWN>` |
| 4 | (assembled) | `<root>.intentList` | §4.3 below |
| 5 | (constant) | `<root>.BotStatusId` | `1` (per Doc 1 §4) |
| 6 | (generated) | `<root>.CreatedDate` | ISO timestamp at assembly time, format `"YYYY-MM-DD HH:MM:SS"` |
| 7 | Description | `<root>.Description` | Direct copy |
| 8 | (constant) | `<root>.BotLanguages` | `[]` (preserved per §16) |
| 9 | (constant) | `<root>.ModifiedDate` | `null` |
| 10 | (resolved) | `<root>.AiModelConfig` | §4.2.3 below |
| 11 | (assembled) | `<root>.ActiveVersionInfo` | §4.2.2 below |

**v1.5.0 wire-format correction.** Prior baseline emitted `intentList` last and `Description` near the top. Production export places `intentList` at position #4 (right after `AccountID`). Skill 3 v1.5.0+ matches the production order.

#### 4.2.2 `ActiveVersionInfo` envelope

Emit fields in this order (matches production — v1.5.0):

| Order | Wire-format path | Value |
|---|---|---|
| 1 | `IsActive` | `1` |
| 2 | `CreatedDate` | Same ISO timestamp as root |
| 3 | `Description` | `""` (matches production samples) |
| 4 | `BotVersionId` | `-2` (placeholder) |
| 5 | `ModifiedDate` | `null` |
| 6 | `SystemPrompt` | `""` (preserved per §16; NOT the bot's actual system prompt, which lives in `AIModelConfig.prompts`) |
| 7 | `AIModelConfig` | §4.2.3 + 4.2.4 + 4.2.5 below |
| 8 | `VersionNumber` | `"0.0.1"` (per Doc 1 §5; v1 always emits this) |
| 9 | `AIModelConfigId` | Same value as `<root>.AiModelConfig.AIModelConfigID` (mirror) |
| 10 | `BotVersionStatusId` | `3` (per Doc 1 §5) |

**v1.5.0 wire-format correction.** Field order revised to match production. Prior baseline had `BotVersionId` first; production has `IsActive` first.

#### 4.2.3 The two `AIModelConfig` objects

Doc 1 §6 defines two distinct objects with confusingly similar names. Both must be emitted. **v1.5.0 wire-format correction:** the prior "both `created` payloads must be identical" rule is replaced — production exports show the top-level catalog reference carries a **much leaner** `created` than the version-level. See below.

**Top-level `<root>.AiModelConfig`** (catalog reference; production export shape):

Emit fields in this order:

| Order | Field | Source |
|---|---|---|
| 1 | `Name` | From `model-catalog.md` "Display name" (e.g., `"Gemini 3.1 - Voice driven"` for `AIModelConfigID=139`) |
| 2 | `ApiKey` | `{}` (empty object, v1 default-public path) |
| 3 | `AIModel` | From `model-catalog.md` entry's `AIModelTypeId` (e.g., `18` for Gemini 3.1) — production exports denormalize this here under the field name `AIModel` |
| 4 | `IsActive` | `1` |
| 5 | `AccountId` | `0` (the reuse-existing-config switch per Appendix D §D.1; v1 always emits `0`) |
| 6 | `ModifiedBy` | `null` |
| 7 | `CreatedDate` | ISO timestamp at assembly time |
| 8 | `ModifiedDate` | ISO timestamp at assembly time |
| 9 | `AIModelConfig` | **Nested object (capital I, distinct from the lowercase-i parent name)** containing only `{ "created": { "model": "<provider model string from model-catalog.md>" } }` |
| 10 | `AIModelConfigID` | From `model-catalog.md` entry (e.g., `139`); `-999` sentinel if `<UNKNOWN>` |

**v1.5.0 fields removed from the prior baseline:** `Description`, `BaseUrl`, `Type` object, `AIModelTypeId` (the integer was kept but renamed to `AIModel` per production), full `created` payload (lives in the version-level object now).

**Version-level `<root>.ActiveVersionInfo.AIModelConfig`** (runtime config; production export shape):

Emit fields in this order:

| Order | Field | Source |
|---|---|---|
| 1 | `max_duration` | Spec section 1 `**Max call duration:**` (integer seconds; default `1200`) |
| 2 | `daily_limit` | Spec section 1 `**Daily limit:**` (integer; default `600`) — v1.13.0, golden-export field |
| 3 | `dailyLimitLayerId` | Spec section 1 `**Daily limit layer:**` (integer layer ID; default `3`) — v1.13.0 |
| 4 | `maxDurationLayerId` | Spec section 1 `**Max duration layer:**` (integer layer ID; default `0` — v1.14.0, was 3; Skill 1 asks via the MCP layer list when connected) |
| 5 | `daily_limit_sentence` | Spec section 1 `**Daily limit sentence:**`; default (production-derived): `"Sorry, but reached daily limit of calls duration, please try again later or contact the copany's support"` — v1.13.0 |
| 6 | `max_duration_sentence` | Spec section 1 `**Max duration sentence:**`; default (production-derived, v1.14.0 — verbatim incl. trailing space): `"נראה שהגענו לזמן שיחה מקסימלי, אנא נסה שנית "` |
| 7 | `IVRLayerSelect_2` | Spec section 1 `**IVRLayerSelect_2:**` (integer; default `3`) — v1.13.0 |
| 8 | `prompts` | §4.2.4 below |
| 9 | `recordAgentCalls` | Spec section 1 `**Record agent calls:**` emitted as the **STRING** `"false"` / `"true"` (production format — not a JSON boolean) |
| 10 | `silence_behaviour` | §4.2.5 below; omitted entirely if spec section 3 is `[not configured]` |
| 11 | `created` | §4.2.4 below (the lean payload — voice + realtime input only) |

**v1.5.0 fields removed from the prior baseline:** `tools: []` and `instructions: ""` at this level (production does not carry them). Reorder to match production.

**v1.13.0 fields added (golden export `בוט שיקוף – קבוצת קלי v0.0.17`):** `daily_limit`, `dailyLimitLayerId`, `maxDurationLayerId`, `daily_limit_sentence`, `max_duration_sentence`, `IVRLayerSelect_2` — all siblings of `max_duration` at this level (NOT inside `created`). When a default is applied (spec field absent), list it in the banner's DEFAULTS APPLIED section. Layer-target defaults are split since v1.14.0: `dailyLimitLayerId` and `IVRLayerSelect_2` stay at the golden-derived `3`; `maxDurationLayerId` defaults to `0` and is user-chosen via the MCP layer list when connected (Skill 1 step 13). All are account-specific — the banner note lets the operator re-check them post-import.

#### 4.2.4 The `created` payload (lean) and `prompts` bundle

**`created` payload at the version level** (`ActiveVersionInfo.AIModelConfig.created`) — v1.5.0 lean shape:

```json
{
  "realtimeInputConfig": {
    "automaticActivityDetection": {
      "disabled": "true"
    }
  },
  "generationConfig": {
    "speechConfig": {
      "voiceConfig": {
        "prebuiltVoiceConfig": {
          "voiceName": "<voice from spec section 1>"
        }
      }
    }
  }
}
```

| Path | Source |
|---|---|
| `realtimeInputConfig.automaticActivityDetection.disabled` | Always the literal string `"true"` (production format — not a JSON boolean) |
| `generationConfig.speechConfig.voiceConfig.prebuiltVoiceConfig.voiceName` | Spec section 1 `**Voice Name:**` direct copy |

If no voice channel is active in section 1: omit the `voiceConfig` object entirely — keep only `realtimeInputConfig`. (No production sample for chat-only bots; this is the safest default.)

**`created` payload at the top level** (`AiModelConfig.AIModelConfig.created`) — even leaner:

```json
{
  "model": "<provider model string from model-catalog.md>"
}
```

Just the model string. No generation config, no system instruction, no voice config (the voice config lives in the version-level created).

**v1.5.0 wire-format correction.** Prior baseline emitted both `created` payloads as identical full Gemini Live setup objects (model + full generationConfig + systemInstruction + tools). Production exports show the two `created` payloads serve different purposes — the catalog reference carries only the model string; the runtime config carries only the realtime + voice. Both prior fields `temperature`, `topP`, `topK`, `responseModalities`, `proactivity`, `thinkingConfig`, `systemInstruction`, `tools` are dropped from emission.

**Note on Compass doctrine rule 12 / CHK-10 interaction:** the dropped fields are exactly the ones CHK-10 used to validate. CHK-10 is defined in the procedure file to validate that *no removed fields are re-added*, rather than positively asserting them present. See the procedure file CHK-10 for the inverted regression-catching rule.

**`prompts` bundle** (`ActiveVersionInfo.AIModelConfig.prompts`) — unchanged from prior:

| Wire-format path | Spec source |
|---|---|
| `prompts.persona` | Section 2.1 verbatim |
| `prompts.voiceInstructions` | Section 2.2 verbatim |
| `prompts.chatInstructions` | Section 2.3 verbatim |
| `prompts.intentInstructions` | Section 2.4 verbatim (bot-level opening behavior — NOT per-intent) |
| `prompts.openingAnnouncement` | Section 2.5 verbatim |

If the spec marks any prompts field `<UNKNOWN>`, emit `""` and add the field path to the banner.

#### 4.2.5 `silence_behaviour` (spec section 3, conditional)

If section 3 reads `[not configured]`: **omit** the entire `silence_behaviour` field from `ActiveVersionInfo.AIModelConfig`. Do not emit it as `null`, do not emit it as `{}`. Refua's production sample omits it entirely; Skill 3 follows that pattern.

If section 3 has its fields populated: emit them direct field-to-field.

| Wire-format path | Spec source |
|---|---|
| `silence_behaviour.intent` | The `IntentId` of section 3's `silence failover intent:` (the intent to jump to when caller-silence loops are exhausted). Emit as the **first** key of the object (matches production shape). **IMPORT LIMITATION (empirically confirmed 2026-06-23, Matan bot, AccountID 15832):** the Voicenter import procedure remaps negative placeholders in `intents[]` / `botIntents[]` / `intentRelations[]` to real positive IDs, but it does **NOT** remap `silence_behaviour.intent` — a placeholder survives verbatim into the imported bot and the silence forward is blank in the UI until set by hand. Resolution rules (v1.14.0), in priority order: **(1)** if the failover names a **section-4.6 catalog intent** (user-supplied), emit its **real positive `IntentId`** verbatim — it survives import unchanged. **(2)** the normal case — the failover names a **bot-own intent** (the dedicated silence-forwarding intent Skill 1 always creates, or the user-chosen existing flow intent): emit its **negative placeholder** from the cached ID map, and add the MANDATORY banner line: `silence_behaviour.intent is a pre-import placeholder the import procedure does NOT remap — after import, set the silence forward to <display name> in the UI (the target intent is identifiable by IsSilenceIntent: 1)`. **(3)** `-999` + banner only if section 3 is unresolvable. Never emit as a string identifier; never omit when `silence_behaviour` is emitted. *(v1.14.0 removed the pre-v1.14 "substitute canonical system global 19" mechanism — silence forwarding always targets a real, bot-own intent the user chose an outcome for.)* Production proof of the real-id form post-import: the operator/משרד-התחבורה export carries `silence_behaviour.intent: 7518`. |
| `silence_behaviour.silence_duration` | Section 3 `silence_duration` |
| `silence_behaviour.silence_loops` | Section 3 `silence_loops` |
| `silence_behaviour.silence_sentence` | Section 3 `silence_sentence` |
| `silence_behaviour.silence_ending_sentence` | Section 3 `silence_ending_sentence` |

The `silence_behaviour.intent` failover is bot-level (caller silence regardless of active intent), distinct from each RT=2 intent's `api_silence_behaviour.intent` (API silence). Both are structural `intent` failovers; `silenceRelations[]` stays `[]` (the bot-level failover lives in this field, not a relations row).

### 4.3 `intentList` assembly (sections 4 + 5 → six parallel collections)

Per Doc 1 §8, `intentList` has six parallel collections wired by integer IDs. Skill 3 builds them from the cached ID map (§4.1) and section 4-5 content.

#### 4.3.1 `intents[]`

For each section 4 intent (in order), build a 17-field entry per the v1.5.0 production-aligned shape. Emit fields in this order (matches production export):

| Order | Wire-format field | Spec source (or default) |
|---|---|---|
| 1 | `Name` | Section 4 "Display name" |
| 2 | `IntentId` | Cached `<identifier> → IntentId` placeholder |
| 3 | `IsActive` | `1` (always — v1.5.0 restored at intent root) |
| 4 | `Priority` | `1` (per Doc 1 §9.0) |
| 5 | `AccountId` | Spec section 1 `**Account ID:**` — same value as `<root>.AccountID` (v1.5.0 added) |
| 6 | `Description` | Section 4 "Description" |
| 7 | `MaxAttempts` | Section 4 explicit value if set; else `3` |
| 8 | `IntentConfig` | `{ prompts: { llmDescription: "", validationPrompt: <section 5 verbatim> }, additional: { max_turns: <see below>, sensitive: <section 4 or false>, max_turns_sentence: <see below> } }` (v1.13.0 — `additional` block; `llmDescription` unchanged, always `""`) |
| 9 | `IntentScripts` | `[]` (empty array — per §16 quirk 8) |
| 10 | `IntentSources` | **v1.5.0:** per spec section 1 `Channels Active`. Voice active → `[{ "SourceID": 1, "SourceName": "VOICE", "IntentSourceID": <placeholder from -4000 range> }]`. Chat-only → `[]`. Both channels → emit voice entry only for v1 (chat-only sample missing). Note: the production fixture shows mixed distribution — most intents in the transport-planner have `IntentSources: []` even though voice is active, while one intent has the populated voice entry. v1.5.0 design decision 14 standardizes to populated voice entry for every intent on voice-active bots (the design intent of "channel-per-intent" semantics). |
| 11 | `IntentToolName` | Section 4 "Tool name" (= identifier) |
| 12 | `IntentResponces` | §4.4 below — invariant outer shape `{ IsActive: 1, ResponseTypeId, Configuration }` |
| 13 | `IsSilenceIntent` | **Integer 0/1**. `0` by default; `1` if spec section 4 sets `**IsSilenceIntent:** true` (v1.14.0 — the dedicated silence-forwarding intent) |
| 14 | `IntentCategoryId` | `-3` (the single default category placeholder) |
| 15 | `IntentParameters` | §4.3.2 below |
| 16 | `ValidationTimeout` | `30` (per Doc 1 §9.0) |
| 17 | `HandlingInstructions` | `null` (preserved per §16) |

**`IntentConfig.additional` emission rules (v1.13.0 — replaces the pre-v1.13 sibling `max_turns`/`max_turns_sentence` placement):**

`IntentConfig.additional` is emitted on **EVERY** bot-own intent (golden export `בוט שיקוף – קבוצת קלי v0.0.17` carries it on every real intent) with three keys:

| Key | Default | Spec override |
|---|---|---|
| `max_turns` | `5` for ALL RTs (v1.14.0 — replaces the pre-v1.14 RT=2 `15` rule; both production reference exports carry 5 everywhere except conversation-heavy intents at 10) | Section 4 `**Max turns:**` (Skill 1 sets `10` autonomously on conversation-heavy intents — never user-prompted) |
| `sensitive` | `false` (JSON boolean) | Section 4 `**Sensitive:**` (v1.14.0: true only on sensitive-collecting intents per Skill 1 §3.4.3) |
| `max_turns_sentence` | `"מתנצל אבל נראה שיש לי בעיה מסויימת, אנא נסה שנית מאוחר יותר"` for ALL RTs (v1.14.0 masculine fallback — Skill 2 normally authors the gender-matched sentence into section 4) | Section 4 `**Max turns sentence:**` |

Shape: `"additional": { "max_turns": 5, "sensitive": false, "max_turns_sentence": "" }` — a sibling of `prompts` inside `IntentConfig`. **Never emit `max_turns` / `max_turns_sentence` as direct siblings of `prompts` (the pre-v1.13 shape) — they live inside `additional`.** When a default is applied, list it once in the banner DEFAULTS APPLIED section (aggregated, not per-intent).

**Note on production distribution (v1.14.0 — replaces the v1.5.0 "RT=2 default 15" design decision 6).** Both v1.14.0 reference exports (transport route-planner; supermarket cart agent) carry `additional.max_turns: 5` on nearly every intent regardless of RT, with `10` only on conversation-heavy intents (product search; credit-card collection). The pipeline therefore standardizes to a uniform default of `5`; the `10` upgrade is Skill 1's autonomous call via section 4 `**Max turns:**` — see `spec-skeleton.md` §4.

**v1.5.0 changes from prior 14-field baseline:** Reordered to match production. Added intent-root `IsActive` (always `1`). Added intent-root `AccountId`. `IsSilenceIntent` now integer (was boolean). `IntentSources` shape includes `SourceName` and `IntentSourceID` (was `[{ SourceID: 1 }]`). `max_turns` / `max_turns_sentence` added with RT-conditional defaults (relocated into `IntentConfig.additional` in v1.13.0; RT-conditional defaults replaced by uniform 5 in v1.14.0).

**v1.5.0 fields removed from prior baseline:** intent-root `IsDeleted` (production never had it; the v1.4.1 correction removed it correctly — kept removed).

**Catalog-intent injection (v1.11.0).** After emitting the bot's own intents (above), append each section-4.6 catalog intent's `**Definition:**` JSON object to `intents[]` **verbatim**, in section-4.6 declaration order. No field is rewritten, reordered, or renumbered. (These intents already carry real IDs and a complete shape; Skill 3 is a pure conduit for them.)

#### 4.3.2 `IntentParameters[]` (per intent, slot list)

For each slot in section 5, build a parameter entry. Emit fields in this order (matches production):

| Order | Wire-format field | Spec source (or default) |
|---|---|---|
| 1 | `Name` | Slot name |
| 2 | `Schema` | `null` (preserved literal — production constant) |
| 3 | `IntentId` | Cached `<intent> → IntentId` placeholder (parent backreference) |
| 4 | `IsActive` | `1` (integer) |
| 5 | `CreatedBy` | Spec section 1 `**Created by:**` value, or `""` if not set |
| 6 | `IsRequired` | **Integer 0/1**. `1` if slot.IsRequired; else `0`. Production format — not boolean. |
| 7 | `ModifiedBy` | `" "` (single literal space — production constant per parameter row) |
| 8 | `OptionList` | For ENUM: array of `{ Value, Label }` pairs from spec. For non-ENUM: `null` (NOT `[]` — v1.5.0 correction) |
| 9 | `CreatedDate` | ISO timestamp at assembly time |
| 10 | `Description` | Section 5 slot description |
| 11 | `ParameterId` | Cached `<intent>.<slot> → ParameterId` placeholder |
| 12 | `DefaultValue` | Spec slot-line `DefaultValue` segment if present (v1.16.0); else `""` (NOT `null` — v1.5.0 correction) |
| 13 | `ModifiedDate` | ISO timestamp at assembly time |
| 14 | `ParameterType` | Full nested object — see table below |
| 15 | `CollectionOrder` | Slot order (1-indexed) |
| 16 | `ParameterTypeId` | `1` / `10` / `16` / `19` per Doc 1 §12 |
| 17 | `ValidationRules` | `{}` (preserved per §16) |

`ParameterType` nested object — frozen constants per `ParameterTypeId` (v1.5.0):

```json
{
  "Name": "STRING",
  "IsActive": 1,
  "CreatedBy": "SYSTEM",
  "ModifiedBy": null,
  "CreatedDate": "2025-01-21 11:25:25",
  "Description": "Basic text input",
  "ModifiedDate": null,
  "ParameterTypeId": 1,
  "ValidationPattern": null,
  "IsCustomValidationAllowed": 1
}
```

Per-type system-dictionary values (v1.13.0 — **captured VERBATIM from production exports; never re-authored**. STRING/BOOLEAN/ENUM/INTEGER/JSON verified against the golden export `בוט שיקוף – קבוצת קלי v0.0.17`; the pre-v1.13 BOOLEAN/ENUM rows were wrong "extrapolated" guesses and are corrected below):

| ParameterTypeId | Name | Description | ValidationPattern | IsCustomValidationAllowed | CreatedDate |
|---|---|---|---|---|---|
| 1 | `"STRING"` | `"Basic text input"` | `null` | `1` | `"2025-01-21 11:25:25"` |
| 4 | `"INTEGER"` | `"Whole number input"` | `"^[0-9]+$"` | `1` | `"2025-01-21 11:25:25"` |
| 10 | `"PHONE"` | `"Phone number"` | **unverified** | **unverified** | `"2025-01-21 11:25:25"` |
| 16 | `"BOOLEAN"` | `"Yes/No input"` | `"^(true\|false\|yes\|no)$"` | `0` | `"2025-01-21 11:25:25"` |
| 19 | `"ENUM"` | `"Selection from predefined options"` | `null` | `0` | `"2025-01-21 11:25:25"` |
| 20 | `"JSON"` | `"json schema"` | `null` | `0` | `"2025-04-10 09:50:42"` |

Shared constants across all types: `IsActive: 1`, `CreatedBy: "SYSTEM"`, `ModifiedBy: null`, `ModifiedDate: null`.

**PHONE (10) is unverified** — no production export in hand carries it. Until its dictionary row is captured from a real export or `ParameterType.Data.sql`, emit `ValidationPattern: null`, `IsCustomValidationAllowed: 1` (the pre-v1.13 values) AND add a banner line: `ParameterType PHONE block unverified against system dictionary — verify after import`. Check 21 (§6) byte-matches every emitted ParameterType block against this table; unverified PHONE downgrades to the banner note instead of failing.

**v1.5.0 fields removed from prior baseline:** parameter-root `IsDeleted` (production doesn't carry it) and parameter-root `ValidationPattern` (it lives inside `ParameterType` now).

#### 4.3.3 `botIntents[]`

**Selective membership (v1.8.0).** Emit an entry **only** for intents whose `**Bot-intent role:**` is `entry` or `global`. Skip `chained` intents entirely (default role; they are reached via `intentRelations[]`). Walk section 4 in order; emit the subset in that order. Emit fields in this order (matches production):

| Order | Wire-format field | Value |
|---|---|---|
| 1 | `BotId` | `-1` (mirror of root; lowercase `d` per production casing) |
| 2 | `DTMFList` | `[]` (always emitted, never omitted) |
| 3 | `IntentId` | Cached `<identifier> → IntentId` placeholder (lowercase `d` per production) |
| 4 | `IsActive` | `1` (integer) |
| 5 | `SortOrder` | **0-based** ordinal within the **emitted subset**, in section-4 order (first emitted → 0, second emitted → 1, …). Chained intents are skipped and do not consume an index. |
| 6 | `BotIntentId` | Cached `<identifier> → BotIntentId` placeholder (lowercase `d`) |
| 7 | `BotVersionId` | `-2` (mirror of `ActiveVersionInfo.BotVersionId`; v1.5.0 added) |
| 8 | `BotIntentTypeID` | Role discriminator (Doc 1 §8.2 / G-10): `entry` → `1`, `global` → `2`. |
| 9 | `ConditionGroupList` | **Populated by default** with single entry (see below). v1.5.0 default reversed from prior `[]`. |

Default `ConditionGroupList` content (emitted for every `botIntents[]` row):

```json
[
  {
    "Order": 1,
    "IntentConditionList": [],
    "IntentConditionName": "",
    "IntentConditionGroupID": "<placeholder from -3000 range, allocated for this botIntents row>",
    "IntentConditionGroupType": 1,
    "IntentConditionRelationID": "<same as this row's BotIntentId — mirror>",
    "IntentConditionRelationType": 1,
    "IntentConditionGroupTypeName": "tool",
    "IntentConditionRelationTypeName": "BotIntentID"
  }
]
```

**v1.5.0 changes from prior baseline:** `BotID`/`IntentID` capital-D casing changed to lowercase `BotId`/`IntentId` per production. `DTMFList: []` added. `BotVersionId: -2` added. `SortOrder` switched to 0-based. `ConditionGroupList` populated by default with the structural entry above.

**v1.8.0 worked example (Noa).** 9 intents, roles: `handle_who_are_you`/`collect_inquiry_basics`/`handle_out_of_scope` = entry, `transfer_to_human` = global, the other 5 = chained. `botIntents[]` emits 4 entries — SortOrder 0/1/2/3 over (9214 t1, 9217 t1, 9229 **t2**, 9235 t1) — and omits the 5 chained intents. See `references/test-artifacts/bot-noa-2026-06-01.json`.

**Catalog-intent wiring (v1.11.0).** A section-4.6 catalog intent wired `silence-forward only` emits NO `botIntents[]` row (free-floating). A catalog intent wired `triggerable global` emits a `botIntents[]` row with `BotIntentTypeID 2`, using its real `BotIntentId` if the 4.6 definition supplies one (else a `-100`-series placeholder). Like any authored `global`, it is reachable from anywhere via that type-2 registration — Skill 3 generates NO per-intent `intentRelations[]` edges to it (v1.12.0).

#### 4.3.4 `intentRelations[]`

For each section 4 row's "Transitions out" list, build the set of `(origin, next)` pairs from the **authored transitions only**. **No global fan-out (v1.12.0 — the v1.8.0 D4/D5 fan-out was removed):** a `global` intent is reachable from anywhere by virtue of its `botIntents[]` type-2 registration (§4.3.3), so Skill 3 does **not** append per-intent edges to global intents (hangup, transfer-to-human, etc.). Emit only the transitions the author listed (an author may still list an explicit hand-off to a global; that authored edge is kept). **Deduplicate by `(OriginIntentID, NextIntentID)` before emission**, keeping the lowest `Order` value (the DB unique key forbids duplicates). `Order` is the 0-based position in the final deduped list for that origin.

Emit fields in this order (matches production):

| Order | Wire-format field | Source |
|---|---|---|
| 1 | `Order` | **0-based** position in the transitions list (after dedup) |
| 2 | `DTMFList` | `[]` (always emitted) |
| 3 | `NextIntentID` | Cached `<target identifier> → IntentId` |
| 4 | `OriginIntentID` | Cached `<origin identifier> → IntentId` (capital-D casing per production) |
| 5 | `IntentRelatedID` | **Unique row PK** from placeholder range `-2000, -2001, …` (v1.5.0 — no longer mirrors `NextIntentID`) |
| 6 | `ConditionGroupList` | **Populated by default** with single entry (see below) |

Default `ConditionGroupList` content for `intentRelations[]`:

```json
[
  {
    "Order": 0,
    "IntentConditionList": [],
    "IntentConditionName": "",
    "IntentConditionGroupID": "<placeholder from -3000 range, allocated for this intentRelations row>",
    "IntentConditionGroupType": 1,
    "IntentConditionRelationID": "<same as this row's IntentRelatedID — mirror>",
    "IntentConditionRelationType": 2,
    "IntentConditionGroupTypeName": "tool",
    "IntentConditionRelationTypeName": "RelatedIntentID"
  }
]
```

Note the differences from `botIntents[]` ConditionGroupList: `Order: 0` (vs `1`), `IntentConditionRelationType: 2` (vs `1`), `IntentConditionRelationTypeName: "RelatedIntentID"` (vs `"BotIntentID"`).

**v1.5.0 changes:** `IntentRelatedID` is now a unique row PK with its own placeholder range (was mirror of NextIntentID). `Order` is 0-based (was 1-based). `DTMFList: []` always emitted. `ConditionGroupList` populated by default.

**Section 4.7 pass-through rule (unchanged from prior).** Section 4.7 opt-in lets the spec author override the default `condition_groups` and `dtmf_list` content. If present, Skill 3 lifts the YAML-style blocks verbatim into the corresponding JSON fields. If absent, the v1.5.0 defaults above apply.

**Catalog-intent transitions (v1.12.0).** A `triggerable global` catalog intent is reachable from anywhere via its `botIntents[]` type-2 registration, exactly like an authored `global` — Skill 3 generates NO per-intent `intentRelations[]` edges to it. A `silence-forward only` catalog intent participates in NO `intentRelations[]` rows.

#### 4.3.5 `intentCategories[]`

Single default category, all intents reference it. Emit fields in this order:

| Order | Wire-format field | Value |
|---|---|---|
| 1 | `Name` | Spec section 1 `**Bot Name:**` value (v1.12.0 — was the hardcoded literal `"Default Category"`; each bot's own category now carries the bot's name so bots don't all collide on one "Default Category" entry in the account) |
| 2 | `IsActive` | `1` |
| 3 | `AccountId` | Spec section 1 `**Account ID:**` value — same as `<root>.AccountID` (v1.5.0 added) |
| 4 | `PriorityId` | `1` (v1.5.0 correction — was `2` in prior baseline; production has `1`) |
| 5 | `Description` | Same as `Name` (production observation — v1.5.0 added) |
| 6 | `IntentCategoryId` | `-3` (placeholder) |

**v1.5.0 changes:** `BotID` removed (production doesn't carry it). `IsActive`, `AccountId`, `Description` added. `PriorityId` corrected from `2` to `1`.

**Catalog-intent category merge (v1.11.0).** For each section-4.6 catalog intent, add its category row (the full object: `Name`, `IsActive`, `AccountId` — typically `0`, `PriorityId`, `Description`, `IntentCategoryId`) to `intentCategories[]`, **de-duplicated by `IntentCategoryId`**. The bot's own `-3` category (now named after the bot, v1.12.0) is always emitted; catalog categories (e.g. system category `22` "Sales intents", `AccountId 0`) ride alongside it. If the catalog intent's `**Definition:**` does not embed its category object, the author must supply it in the 4.6 block — Skill 3 does not synthesize category metadata.

#### 4.3.6 `silenceRelations[]`

`[]` (per Doc 1 §8.5 + §16; v1 always empty).

#### 4.3.7 `apiSilenceRelations[]`

For each RT=2 intent in section 4 ordering, emit one entry. The `Configuration` is **the full content of the parent intent's `IntentResponces.Configuration`** (v1.5.0 — was just the six `silence_*` fields in prior baseline).

| Wire-format field | Source |
|---|---|
| `Configuration` | Deep copy of the parent RT=2 intent's `IntentResponces.Configuration` (every field: `url`, `method`, `headers`, `body` if any, `fail_output`, `announcement`, `function_output`, `response_success`, `intentInstructions`, `intentLoadingAnnouncement`, `api_silence_behaviour`) |
| `OriginIntentID` | Cached `<RT=2 intent identifier> → IntentId` |
| `ApiSilenceIntentID` | Cached `<fallback intent from spec section 5> → IntentId` |

**v1.5.0 wire-format correction.** Prior baseline emitted only the six `silence_*` fields here. Production shows the entire parent Configuration is copied — including `url`, `method`, `body`, the API-specific `announcement`, `function_output`, `response_success`, `intentInstructions`, etc. Skill 3 v1.5.0+ does a deep copy.

CHK-06 now validates **full Configuration deep equality**, not just the six fields. Since Skill 3 emits both from the same spec source, they match by construction; check 6 catches emission bugs.

If a non-RT=2 intent has API silence behavior in its section 5 entry, that's a Skill 2 bug — Skill 3 ignores it (RT determines whether the entry is emitted).

### 4.4 RT-specific `IntentResponces.Configuration`

Per intent, branch on `Response Type` (section 4) to assemble the correct `Configuration` shape. Doc 1 §11 has the per-RT field tables; the rules below codify Skill 3's behavior including unknowns.

**`IntentResponces` outer shape — invariant across all RTs.** Every `IntentResponces` object has the same **four** top-level keys in this order: `IsActive` (always `1`), `Configuration`, `ResponseTypeId`, `SuccessCondition` (always the empty string `""` on bot-own intents; §4.6 catalog blocks pass through verbatim). The per-RT tables below define `Configuration`'s contents only — the `IsActive` and `ResponseTypeId` rows are repeated in each RT table as a reminder.

#### RT=1 — Layer Transfer (terminal)

| Wire-format field | Source |
|---|---|
| `ResponseTypeId` | `1` |
| `IsActive` | `1` (per §16 quirk #15 — required inside every `IntentResponces`) |
| `Configuration.layer` | Section 5 "Layer" — the real layer number (fetched from the MCP during Skill 1, §2.4.A). Defaults to `0` (root layer) when the spec omits it. **No `-999` sentinel for layer** (v1.12.0 — `0` is a valid landing layer, a deliberate exception to fail-loud; see anti-list §"Suppress fail-loud sentinels"). |
| `Configuration.announcement` | **Always omitted (v1.14.0 hard rule).** RT=1 never carries an `announcement` key — the farewell lives in the PREVIOUS intent's `intentInstructions` (FP-8 farewell trigger rule; production: every layer-transfer intent has only `intentLoadingAnnouncement`). If a legacy spec supplies one, that is a **check-20 failure**, not an emission choice. |
| `Configuration.intentLoadingAnnouncement` | Section 5 "Loading announcement" verbatim. **Always emitted** for RT=1 — the terminal's only utterance, a short "יום טוב"-style line. |

RT=1 intents do **not** emit `intentInstructions` (post-execution behavior on a terminal intent has no meaning per Doc 1 §11.5).

Terminal doctrine (FP-8, v1.14.0) — one RT=1 terminal per outcome, owning its outcome slot, no terminal→anything relations, no `announcement` (farewell on the predecessor) — is validated by CHK-20 (§6).

#### RT=2 — API Call

| Wire-format field | Source |
|---|---|
| `ResponseTypeId` | `2` |
| `IsActive` | `1` (per §16 quirk #15 — required inside every `IntentResponces`) |
| `Configuration.url` | Section 5 "URL"; `<USER_TO_FILL: webhook_url>` if `<UNKNOWN>` |
| `Configuration.method` | Section 5 "Method" (`"POST"` or `"GET"`) |
| `Configuration.headers` | Section 5 "Headers" object; `{}` if not specified |
| `Configuration.fail_output` | Section 5 verbatim |
| `Configuration.announcement` | Section 5 "Announcement (after API success)" verbatim. **v1.5.0 — renamed from `apiResponseAnnouncement` in prior baseline.** May be the empty string when the intent auto-chains (`**Asks next:**` [none]) — FP-3 turn-yield, v1.17.0; Skill 2 check 10 gates upstream, CHK-24 backstops. |
| `Configuration.function_output` | Section 5 "Fail-output fallback map" — **object shape** `{ "default": "<fallback string>" }` (v1.5.0 — was a string of LLM guidance in prior baseline). User may extend with per-code keys; Skill 3 passes the object through verbatim. |
| `Configuration.response_success` | Section 5 "Response success instructions" — **object shape** `{ "instructions": "<string>" }` (v1.5.0 — was bare string in prior baseline). |
| `Configuration.intentInstructions` | Section 5 "Post-Execution Intent Instructions" verbatim |
| `Configuration.api_silence_behaviour` | Spec section 5 "API silence behavior" — the six-key object defined in §4.4.1 below (the `intent` key is the resolved failover IntentId — **mandatory, never omit**). **Same content** as `apiSilenceRelations[].Configuration.api_silence_behaviour` (CHK-06 validates). |
| `Configuration.intentLoadingAnnouncement` | Section 5 "Loading announcement" verbatim |

##### 4.4.1 The `api_silence_behaviour` object — exact shape

Every RT=2 intent's `Configuration.api_silence_behaviour` is an object with these **six keys** (emit all six; this object is the intent-failover contract — if `intent` is missing the call has no fallback when the caller goes silent during the webhook):

| Key | Source | Notes |
|---|---|---|
| `intent` | Cached `<fallback intent from spec section 5 "API silence behavior"> → IntentId` (integer) | **The failover intent.** Resolve the spec's `fallback intent:` identifier to its `IntentId`, exactly as `apiSilenceRelations[].ApiSilenceIntentID` is resolved (§4.3.7) — the two MUST be the same integer. `-999` sentinel if the fallback intent is `<UNKNOWN>`. Never emit as a string identifier; never omit. |
| `silence_loops` | Section 5 `silence_loops:` (integer) | |
| `silence_duration` | Section 5 `silence_duration:` (integer seconds) | |
| `silence_sentence` | Section 5 `silence_sentence:` verbatim | |
| `silence_instructions` | Section 5 `silence_instructions:` verbatim (`""` if empty) | |
| `silence_ending_sentence` | Section 5 `silence_ending_sentence:` verbatim | |

Because `api_silence_behaviour.intent` and `apiSilenceRelations[].ApiSilenceIntentID` are both resolved from the same spec `fallback intent:` field, they are equal by construction. CHK-06 (full Configuration deep equality) catches any drift between the inline copy and the registry copy; CHK-03 confirms the resolved `ApiSilenceIntentID` endpoint exists in `intents[]`.

**v1.5.0 wire-format corrections (RT=2):**

1. `apiResponseAnnouncement` → renamed `announcement` (production field name).
2. `function_output` → object `{ "default": "<string>" }` instead of bare string.
3. `response_success` → object `{ "instructions": "<string>" }` instead of bare string.
4. `IntentLoadingAnnouncement` (capital I) — **removed.** Prior baseline emitted both lowercase and capital-I as a "casing-bug pair." Production exports of Gemini 3.1 Voice driven bots carry only the lowercase form. v1.5.0 emits only `intentLoadingAnnouncement`.
5. **Empty-string runtime tolerance (voice-agent-llm v1.0.3+):** `announcement` may be empty at runtime — the service substitutes `[START THE CONVERSATION]` as an LLM instruction (bot opens from persona; the literal string is **not** spoken aloud). Skill 3 emits whatever the spec contains verbatim. Skill 2's Check 10 requires authored text upstream on answer-awaiting intents and the empty string on auto-chaining intents (v1.17.0, FP-3 turn-yield; CHK-24 backstops).

The `api_silence_behaviour` sub-object inside `Configuration` and the corresponding `apiSilenceRelations[].Configuration` (now a deep copy of the entire Configuration, not just the six fields) must be content-identical — Skill 3 emits both from the same spec source.

#### RT=3 — Continue

| Wire-format field | Source |
|---|---|
| `ResponseTypeId` | `3` |
| `IsActive` | `1` (per §16 quirk #15 — required inside every `IntentResponces`) |
| `Configuration.announcement` | Section 5 "Announcement" verbatim (may be the empty string when the spec logs the FP-3 intentional-empty exception — cases a/b/c; empty is MANDATORY on auto-chaining intents per the v1.17.0 turn-yield rule, check 24) |
| `Configuration.response_success` | Section 5 "Response success instructions" — **object shape** `{ "instructions": "<string>" }` (v1.5.0 — was bare string). |
| `Configuration.intentInstructions` | Section 5 "Post-Execution Intent Instructions" verbatim |
| `Configuration.intentLoadingAnnouncement` | Section 5 "Loading announcement" verbatim — **always emitted for RT=3 (v1.13.0, FP-7).** Skill 2 check 12 guarantees it is authored non-empty; CHK-17 backstops (an unset value would produce the default "." SAY directive bug at runtime). |

**v1.5.0 wire-format correction (RT=3):** `response_success` is now an object `{ "instructions": "<text>" }`, not a bare string.

**v1.13.0 wire-format addition (RT=3):** `intentLoadingAnnouncement` added (golden-export field; key order per the golden export: announcement, response_success, intentInstructions, intentLoadingAnnouncement).

#### RT=4 — Dial-Out

RT=4 has two operating modes selected by section 4 `**Dial source:**`. Both modes emit the same Configuration shape; specific fields are populated or left empty per mode.

| Wire-format field | Source |
|---|---|
| `ResponseTypeId` | `4` |
| `IsActive` | `1` (per §16 quirk #15 — required inside every `IntentResponces`) |
| `Configuration.phone1` | Section 4 `**Phone1:**` (E.164 with leading `+`) when dial-source=static; `""` when dial-source=parameter |
| `Configuration.phone2` | Section 4 `**Phone2:**` when dial-source=static; `""` when dial-source=parameter |
| `Configuration.phone3` | Section 4 `**Phone3:**` when dial-source=static; `""` when dial-source=parameter; `<USER_TO_FILL: phone3>` if static and `<UNKNOWN>` |
| `Configuration.parameter_phone` | Section 4 `**Parameter phone:**` (slot identifier) when dial-source=parameter; key omitted when dial-source=static |
| `Configuration.selectdial_option` | Section 4 `**selectdial_option:**` — literal string `"Parameter"` when dial-source=parameter; key omitted (or set to user's literal value) when dial-source=static |
| `Configuration.NEXT_VO_ID` | Section 4 `**NEXT_VO_ID:**` (int); `-999` sentinel if `<UNKNOWN>` |
| `Configuration.MAX_DIAL_DURATION` | Section 4 `**MAX_DIAL_DURATION:**` (int seconds) |
| `Configuration.record` | Section 4 `**Record:**` (boolean) |
| `Configuration.announcement` | Section 4 `**Announcement:**` verbatim; key omitted if absent in spec |
| `Configuration.intentLoadingAnnouncement` | Section 4 `**Loading announcement:**` verbatim; key omitted if absent |
| `Configuration.intentInstructions` | Section 4 `**Post-execution intent instructions:**` verbatim; emit `""` if absent (parallel to RT=2/RT=3 §16 convention) |
| `Configuration.response_success` | Section 4 `**Response success:**` object (e.g., `{ "instructions": "<text>" }`); emit `{}` if absent |

**Empty-phone handling.** A spec entry of `""` for `Phone1`, `Phone2`, or `Phone3` is preserved as `""` in the JSON — the dialer's runtime contract is "try in order, skip empties." Do not coerce empty phones to `null` and do not collapse the keys.

### 4.5 Quirk preservation

Walk Appendix A. For every quirk in the table, ensure the assembled wire structure has the exact form prescribed. This is a verification pass against the in-memory structure — if any quirk is absent or mis-emitted, that's a Skill 3 implementation bug, halt and report.

In normal operation, §4.2-4.4 already produce all quirks correctly. §4.5 is the verification gate that catches drift between the emission code and the §16 contract.

The full checklist is in Appendix A (rows 2, 5, 6, 7 marked REMOVED/CORRECTED; rows 16-19 added in v1.5.0; rows 20-23 added in v1.13.0; row 24 added in v1.14.0).

### 4.6 Sentinel emission for unknowns

Walk spec section 7.4. For each unknown marker, the corresponding wire-format field has already received a sentinel during §4.2-4.4. §4.6 is the bookkeeping pass:

1. Build the **sentinel inventory**: for each `<UNKNOWN: ...>` marker in section 7.4, identify the wire-format JSON path that received the sentinel and the sentinel value emitted.
2. Build the **disagreement list**: any `<UNKNOWN: ...>` in section 7.4 that did not produce a sentinel (Skill 1/2 staged the unknown but Skill 3 didn't find a wire-format slot for it), or any sentinel emitted at §4.2-4.4 that is not in section 7.4 (Skill 3 found an unknown the spec didn't track).
3. Both lists feed the banner (§7.2). The sentinel inventory is the user's pre-import checklist; the disagreement list is a soft warning about spec/skill drift.

**Sentinel format reference:**

| Spec marker shape | Wire-format emission |
|---|---|
| `<UNKNOWN: webhook_url>` (string field) | `"<USER_TO_FILL: webhook_url>"` |
| `<UNKNOWN: NEXT_VO_ID>` (integer field) | `-999` |
| `<UNKNOWN: phone destination>` (string) | `"<USER_TO_FILL: phone3>"` |
| `<UNKNOWN: Account ID>` (integer ID) | `-999` |
| `<UNKNOWN: AIModelConfigID>` (integer ID) | `-999` |
| `<UNKNOWN: AIModelTypeId>` (integer ID) | `-999` |
| `<UNKNOWN: AI Model Config>` (string name → triggers all model fields unknown) | `<USER_TO_FILL: ...>` for strings, `-999` for IDs across the whole `AiModelConfig` block |
| `<UNKNOWN: <some object field>>` (object) | `{}` plus a banner note |
| `<INCOMPLETE: ...>` (section partial) | Section emitted with available content; banner notes incompleteness |
| `[not configured]` (whole-section omission) | Section omitted from JSON entirely |

The sentinel value carries the field role (`webhook_url`, `phone3`, `model_config_name`) inside the placeholder text, so the banner's path-plus-value listing is self-documenting.

---

## 5. Section 6 regeneration sanity check

After §4 assembly completes and before §6 cross-reference pass: regenerate spec section 6 (subsections 6.1–6.5) from sections 4-5 fully. Compare to the spec's existing section 6.

| Subsection | Regeneration source |
|---|---|
| 6.1 Mustache variable usage | Walk every text field across sections 2 and 5 + section 4 RT=2 body; for each Mustache reference, record `(reference, location, resolution source)`. |
| 6.2 Intent transition graph | Flatten section 4 transitions out → list of `(origin → next)` pairs, deduped. **Authored transitions only (v1.12.0 — no global fan-out);** this matches the emitted `intentRelations[]` and Skill 1's section 6.2, so no spurious drift is reported. |
| 6.3 RT=2 API silence pairings | For each RT=2 intent, the `apiSilenceRelations[]` registry entry that pairs with its embedded `api_silence_behaviour`. |
| 6.4 Escalation paths | For each non-terminal intent, the transition row that points to escalation. |
| 6.5 ID assignments | The `<identifier> → IntentId` mapping built in §4.1. |

**Comparison logic:** subsection-by-subsection diff. Differences are normalized for whitespace and ordering before comparison — section 6 in spec is allowed to list entries in any order, since it's derivative.

**Drift handling: soft warning, not blocking.** Section 6 is derivative; sections 4-5 are authoritative. If the regenerated 6 differs from the spec's 6, that's a signal that either (a) sections 4-5 were edited inconsistently after section 6 was generated (e.g., manual edits between Skill 1/2 invocations), or (b) Skill 1/2's section 6 update logic has a bug. Skill 3 doesn't auto-fix and doesn't block emission. It records the drift in the banner and section 7.3 generation log.

The banner section "DRIFT NOTES" lists each subsection that drifted, with a one-line summary (e.g., `6.1: regenerated had 3 references the spec missed; 6.2: spec had 1 transition that no longer exists in section 4`).

If the user cares enough about the drift to fix it, they invoke Skill 1 patch mode (which regenerates section 6 cleanly). Otherwise the JSON is still emitted from the authoritative sections 4-5.

---

## 6. The §15.4 cross-reference pass

After §4 assembly and §5 sanity check: run the **24-check cross-reference pass**.

**The checks live in exactly one place.** Read and execute
`${CLAUDE_PLUGIN_ROOT}/references/verification-procedure.md`. That file carries
CHK-01…CHK-24 with their run order, model gating, severity assignment, per-check failure
routing, and the output contract both execution paths emit. No check procedure text is
duplicated here — if you find yourself recalling a check from memory, re-read the file.

What stays in this SKILL.md is **decision logic**: which path executes the procedure
(§6.0–§6.2), and what Skill 3 does with the results (§6.4).

Coverage summary (the procedure file is authoritative): eight checks per Doc 1 §15.4,
three from Compass doctrine, three botIntents-role integrity checks, one
duplicate-global-intent check, and nine field-placement doctrine checks. CHK-01…CHK-07,
CHK-11…CHK-13, CHK-15, CHK-16…CHK-21 and CHK-24 are blocking; CHK-08 is banded by token
count; CHK-10 blocks on mismatch; CHK-09, CHK-14, CHK-22, CHK-23 are advisory.

### 6.0 Execution mode

[MS2 fills this]

### 6.1 Delegated path

[MS2 fills this]

### 6.2 Inline path

[MS2 fills this]

### 6.3 Failure routing

Per-check routing lives in the procedure file — every `CHK-NN` block carries its own
**On failure route to:** line, and the emitted report restates it under *Routing
recommendations*. Skill 3 consumes those recommendations verbatim; it does not re-derive
or reinterpret them.

Appendix B has the consolidated routing table.

### 6.4 Pass/fail behavior

**On all checks passing (no blocking failures):** proceed to §7 emission.

**On any check failing:** emit a structured error report:

```
Skill 3 cross-reference pass failed.

Checks failed: <count> of <total checks run>
Checks passed: <count>

[For each failure:]
Check <N>: <name>
  Violation: <one-line description>
  Field path: <wire-format path or spec source>
  Route to: <Skill 1 patch mode | Skill 2 reactivation | Skill 3 internal bug>
  Suggested fix: <one-line hint>

No JSON emitted. Section 7.3 has been updated with this failure log.

Next step: <route guidance based on highest-frequency failure type>.
```

Skill 3 does not invoke Skill 1 or Skill 2 itself. The user reads the routing recommendation and invokes the appropriate skill manually (per locked decision C and architecture §9.1). After the user's fix, they re-invoke Skill 3.

---

## 7. Emission

Run only if §3 (parse), §5 (regen sanity check), and §6 (cross-reference pass) all complete. §5's drift is a soft warning, not a fail; §6 is the hard gate.

### 7.1 JSON output structure

A single JSON object per Doc 1 §4 (the top-level wrapper). Pretty-printed with 2-space indent, UTF-8, keys in the order Doc 1 documents them (Doc 1 ordering matters for human reading even though the platform parses by key not position).

The output is **valid JSON only** — no comments, no trailing commas, no JSONC extensions. The banner is delivered separately (§7.2).

### 7.2 Banner format

The banner is rendered **above** the JSON (single-conv runtime) or as a sidecar file (Claude Code runtime). It is plain text — never embedded in the JSON itself — so the user can copy the JSON code block directly without stripping anything before importing.

**Banner sections, in order:**

```
# Voicenter Bot JSON — generation banner
# Skill suite: v1
# Generated: <ISO-8601 timestamp>
# Source spec: <spec source reference>
# Source spec version: <from section 7.1>
#
# UNKNOWN VALUES — user must replace before import:
#   - <wire-format JSON path>: <sentinel value> (<role description>)
#   [...]
#
# DRIFT NOTES (section 6 sanity check):
#   - 6.1: <one-line drift summary> [if any]
#   - 6.2: <one-line drift summary> [if any]
#   - [...]
#   [or:]
#   - No drift detected.
#
# RECONCILIATION (section 7.4 vs emitted sentinels):
#   - <one-line note per discrepancy> [if any]
#   [or:]
#   - 7.4 and emitted sentinels in agreement.
#
# DOCTRINE SENTINELS (Compass advisories not resolved during authoring):
#   - Rule <N> (<name>): <one-line summary> — see references/voice-prompt-doctrine.md rule <N> for fix recipe
#   [...]
#   [or:]
#   - No doctrine sentinels.
#
# DEFAULTS APPLIED:
#   - ActiveVersionInfo.AIModelConfig.created.realtimeInputConfig.automaticActivityDetection.disabled = "true" (v1.5.0 lean payload constant)
#   - ActiveVersionInfo.AIModelConfig.max_duration = 1200 (v1.5.0 default — see spec section 1)
#   - ActiveVersionInfo.AIModelConfig.daily_limit = 600, dailyLimitLayerId = 3, maxDurationLayerId = 0, IVRLayerSelect_2 = 3 (v1.14.0 defaults — layer targets are account-specific; verify after import)
#   - IntentConfig.additional defaults applied (max_turns = 5 / sensitive = false / max_turns_sentence masculine fallback) on intents without spec overrides (v1.14.0)
#   - ActiveVersionInfo.AIModelConfig.recordAgentCalls = "false" (v1.5.0 default — see spec section 1)
#   - [...]
#
# MANDATORY POST-IMPORT STEP (v1.14.0 — emitted whenever silence_behaviour.intent is a placeholder):
#   - silence_behaviour.intent = <placeholder> is a pre-import placeholder the import procedure does NOT
#     remap — after import, set the silence forward to "<display name>" in the UI
#     (the target intent is identifiable by IsSilenceIntent: 1).
#
# MANDATORY POST-IMPORT STEP (v1.16.0 — emitted whenever spec section 1 carries **Negative instructions:**):
#   - Negative instructions are NOT emitted to the JSON (wire field unverified) — after import, paste the
#     spec's Negative instructions text into the UI's AI Security Settings → Negative Instructions field:
#     "<spec section 1 Negative instructions text>"
```

Each section is always emitted, even if its content is "(none)" or "(in agreement)" — the user gets a consistent banner shape regardless of whether the spec was tidy. Appendix C has a worked example.

The "DEFAULTS APPLIED" section lists every value Skill 3 emitted that was not authored in the spec — generation params, the constants per Doc 1 §16 (e.g., `Priority: 1`, `MaxAttempts: 3`), and the catalog-derived `created` payload defaults. This makes Skill 3's contributions auditable: anything not in the banner came from the spec.

**DOCTRINE SENTINELS population (Compass rule 13).** Walk section 7.3 of the spec. For each log entry of the form `Compass rule <N> advisory fired on [<context>] — user kept original` (or any variant where the user opted not to fix), emit one banner line under DOCTRINE SENTINELS. The line format is:

```
# - Rule <N> (<rule name>): <human-readable summary of the violation in context> — see references/voice-prompt-doctrine.md rule <N> for fix recipe
```

Rule names are sourced from the reference catalog (`references/voice-prompt-doctrine.md` §1 headings). Example lines:

```
# - Rule 3 (English operational, target-language utterances): prompts.persona is 87% Hebrew on a he-IL bot; user kept original — see references/voice-prompt-doctrine.md rule 3 for fix recipe
# - Rule 7 (Generic-policy boilerplate): "GDPR" appears in prompts.persona; user kept (declared domain-appropriate) — see references/voice-prompt-doctrine.md rule 7 for fix recipe
# - Rule 10 (Few-shot example cap): collect_inquiry_details.validationPrompt has 3 transcript pairs (Hebrew bot — ~750 tok cost); user kept — see references/voice-prompt-doctrine.md rule 10 for fix recipe
```

If no Compass advisories fired or all were resolved, emit `# - No doctrine sentinels.` (matching the established pattern of the other banner sections).

The DOCTRINE SENTINELS section is **structural** per the doctrine catalog (rule 13) — auto-applied based on the spec's section 7.3 trail; no user prompt and no opt-out at emission time. If a user wants a clean banner, they fix the advisories during Skill 1 / Skill 2 authoring.

### 7.3 Filename convention

`bot-<bot-snake-name>-<YYYY-MM-DD>.json`

Where `<bot-snake-name>` is the spec section 1 `**Identifier:**` value (a snake_case ASCII identifier captured by Skill 1 at interview time). If the field is missing (legacy spec from before this patch), Skill 3 falls back to ASCII-folding `**Bot Name:**`, then to `bot`.

Companion banner file (Claude Code only): `bot-<bot-snake-name>-<YYYY-MM-DD>.banner.md`.

If the file already exists in the workspace (Claude Code), append `-<counter>` before `.json` (e.g., `bot-yuval-2026-05-01-2.json`). Single-conv runtime doesn't have files; just emit the code block.

### 7.4 Runtime-specific delivery

**Single-conversation runtime:**

1. Render the banner as plain text in the chat message.
2. Render the JSON in a fenced code block (` ```json `).
3. Append a closing message:

> Bot JSON ready. Copy the code block above, save as `bot-<name>-<date>.json`, replace any `<USER_TO_FILL: ...>` strings or `-999` IDs with real platform values listed in the banner, then import to Voicenter via the platform UI.

**Claude Code runtime:**

1. Write the JSON to `bot-<bot-snake-name>-<YYYY-MM-DD>.json` in the workspace.
2. Write the banner to `bot-<bot-snake-name>-<YYYY-MM-DD>.banner.md` in the workspace.
3. Append a closing message:

> Bot JSON written to `<filename>`. Banner sidecar at `<banner filename>`. Replace any `<USER_TO_FILL: ...>` strings or `-999` IDs (full list in the banner) with real platform values, then import to Voicenter.

### 7.5 Spec section 7.3 update — success path

Append one entry to spec section 7.3:

```
[ISO-8601 timestamp]  Skill 3  assembling  Emitted bot.json. <N> sentinels listed in banner. <D> drift notes. Section 7.4: <unknowns count>. Cross-reference pass: <passed>/<total> passed.
```

In single-conv: this entry appears in the regenerated spec, which is part of Skill 3's chat output below the JSON code block.

In Claude Code: write the updated spec back to `agent-spec.md`.

### 7.6 Spec section 7.3 update — failure path

If parse fails, completeness gate fails, or cross-reference pass fails: append one entry to spec section 7.3:

```
[ISO-8601 timestamp]  Skill 3  assembling  Failed at <stage>: <one-line summary>. No JSON emitted. Route: <skill recommendation>.
```

`<stage>` is one of `parse`, `gate-completeness`, `cross-reference-pass-N` (where N is the failing check), or `internal`.

In Claude Code, write the updated spec back. In single-conv, the regenerated spec with the failure log is part of the error output.

---

## 8. Anti-list — what Skill 3 does NOT do

Skill 3's main risk is doing too much: filling in plausible-looking values for unknowns, smoothing over template deviations, auto-fixing cross-reference violations, deciding RT-specific defaults the spec didn't specify. This list is the guard.

- **Author any text content.** No `validationPrompt`, no `intentInstructions`, no persona, no announcements. All text is verbatim from the spec. If the spec has `<UNKNOWN>` for a text field, Skill 3 emits the sentinel — never invents.
- **Interpret deviations from the strict template.** First deviation halts the parser. Skill 3 does not best-effort guess what the user meant. Does not "smooth over" minor formatting issues. Does not accept synonyms for status markers. Does not tolerate alternate intent header conventions.
- **Auto-fix cross-reference violations.** Dangling IDs, missing API silence pairings, unresolvable Mustache references — none of these get repaired by Skill 3. The error report routes the user to the responsible skill (Skill 1 patch or Skill 2 reactivation per Doc 2 §7.5). The user invokes that skill; Skill 3 re-runs from scratch on the next invocation.
- **Modify the spec beyond appending to section 7.3.** No edits to sections 1-6. No changes to status markers. No regeneration of section 4.5.3 (Skill 2's job) or section 6 (Skill 1/2's job; Skill 3 only compares as a sanity check).
- **Skip the cross-reference pass.** Under any circumstance. Even if the user explicitly asks ("just give me the JSON, I'll fix it later") — the pass is non-negotiable per locked decision C. The cross-reference pass is the difference between a JSON that the platform can import but the runtime can't execute, and a JSON the runtime actually runs.
- **Suppress fail-loud sentinels.** They are the entire point of the unknown-value model (decision B). The banner makes them visible at import time so the user catches them before deploying. Quiet defaults (empty string, 0, null) would import successfully and break at runtime, which is much harder to diagnose. **Exception (v1.12.0): the RT=1 `Configuration.layer`** defaults to `0` (root layer) rather than a `-999` sentinel — Skill 1 fetches the real layer number from the MCP (§2.4.A), and `0` is itself a valid landing layer, so the quiet default does not break at runtime. Layer is the only field exempt from fail-loud.
- **Emit JSON if any blocking cross-reference check fails.** Partial emission is worse than no emission — a partial JSON looks deployable, the user might import it and find out at runtime that it's broken. Hard halt is the correct behavior.
- **Emit `max_turns` / `max_turns_sentence` as direct siblings of `prompts` inside `IntentConfig` (the pre-v1.13 shape).** Since v1.13.0 they live inside `IntentConfig.additional` together with `sensitive` (§4.3.1, golden-export shape).
- **Emit an `announcement` key on an RT=1 intent (v1.14.0).** RT=1 `Configuration` carries only `layer` + `intentLoadingAnnouncement`; the farewell lives in the predecessor's `intentInstructions` (§4.4 RT=1; check 20).
- **Run iteratively or repeatedly within a single invocation.** One parse, one assembly, one sanity check, one cross-reference pass, one emission. If something fails, halt and report. The user re-invokes after fixing.
- **Invoke Skill 1 or Skill 2.** Skill 3 reports routing recommendations; the user invokes the relevant skill manually (per architecture §9.1; skill-to-skill direct invocation is v3).
- **Validate content quality.** Whether the persona is good, whether the `validationPrompt` is well-styled, whether the slot collection logic makes sense — none of these are Skill 3's concern. Skills 1 and 2 own content quality. Skill 3 only validates structural/cross-reference correctness.
- **Test the bot at runtime.** No simulation, no behavior check, no deployment, no end-to-end flow. v1 lifecycle ends at "JSON ready for the user to import manually" per locked decision G.
- **Query the Voicenter platform.** No MCP in v1 (per architecture §9). The model catalog is hardcoded in `model-catalog.md`; the user's account-specific call-context variables come from spec section 4.5.1 (the user's claim, trusted at face value).
- **Modify quirk preservation.** Doc 1 §16 lists the base quirks and Appendix A extends them (v1.5.0 corrections; v1.13.0 golden-export rows 20–23); Skill 3 emits exactly what they prescribe. Any "this looks redundant, I'll skip it" reasoning is forbidden — the platform's import endpoint may strictly require these keys. When in doubt, emit what production samples emit.
- **Skip the banner.** Even on a spec with zero unknowns and zero drift, the banner is emitted with empty sections (`(none)`, `(in agreement)`). The banner contract is consistent regardless of spec state.
- **Use any sentinel value other than the ones in §4.6.** Strings → `<USER_TO_FILL: ...>`, IDs → `-999`, objects → `{}` with banner note. No alternate forms ("UNKNOWN", "TBD", "REPLACE_ME", `null` for IDs), no nuanced sentinels per field type. Consistency is the point.
- **Tolerate intent identifier collisions.** If two intents share an identifier across section 4 (which shouldn't happen post Skill 1 validation but could from a hand-edit), Skill 3 reports a parse error rather than silently reusing the cached ID. Identifier uniqueness is structurally required.
- **Rewrite or compress prompt text to meet the Compass rule 1 token budget.** When check 8 (token budget) fires at the blocking threshold (≥ 5,000 tok), Skill 3 halts and routes to Skill 1 / Skill 2 patch — it does not auto-trim, summarize, paraphrase, or re-section the user's prompt content. The user owns the prose; Skill 3's job is to measure and refuse, never to author.
- **Resolve Compass advisories without user input.** Rules 3, 4, 5, 6, 7, 9, 10 are all advisory-only at their owning skill. If a spec arrives at Skill 3 with unresolved advisories in section 7.3, Skill 3 emits the corresponding DOCTRINE SENTINELS banner lines (per rule 13) — it does not silently apply fixes. The user decides at authoring time; Skill 3 only reports.

---

## Appendix A — Doc 1 §16 quirks: complete preservation checklist

All quirks below (rows 2, 5, 6, 7 marked REMOVED/CORRECTED in v1.5.0; rows 20–23 added in v1.13.0 from the golden export; row 24 added in v1.14.0) must be present in the assembled JSON. Skill 3 verifies each before emission (§4.5).

| # | Quirk | Wire-format location | Action |
|---|---|---|---|
| 1 | `IntentResponces` (typo) | Per intent | Emit as `IntentResponces` — never autocorrect to `IntentResponses`. The platform expects this typo; correcting it breaks import. |
| 2 | ~~`intentLoadingAnnouncement` + `IntentLoadingAnnouncement` (casing-bug pair)~~ | **REMOVED in v1.5.0** | Production exports of Gemini 3.1 Voice driven carry only the lowercase form. v1.5.0 emits the lowercase form only. Earlier samples that showed both are obsolete. |
| 3 | `HandlingInstructions: null` | Per intent (root) | Emit `null`. Appears deprecated but required. |
| 4 | `SystemPrompt: ""` | `ActiveVersionInfo` | Emit empty string. NOT the bot's actual system prompt — that lives in `prompts.persona`. |
| 5 | ~~Top-level `AiModelConfig` + `ActiveVersionInfo.AIModelConfig` — identical `created` payloads~~ | **REMOVED in v1.5.0** | The two `created` payloads serve distinct purposes (catalog reference vs runtime config); they are NOT identical. The top-level carries only `{ "model": "<string>" }`; the version-level carries the realtime+voice runtime config. See §4.2.3 and §4.2.4. |
| 6 | ~~`AIModelConfig.tools: []`~~ | **REMOVED in v1.5.0** | Production exports of Gemini 3.1 Voice driven do not include `tools` inside `AIModelConfig`. Field was removed per §4.2.4 lean shape. |
| 7 | ~~`AIModelConfig.instructions: ""`~~ | **REMOVED in v1.5.0** | Production exports of Gemini 3.1 Voice driven do not include `instructions` inside `AIModelConfig`. Field was removed per §4.2.4 lean shape. |
| 8 | `IntentScripts: []` *(amended; was `{}` in earlier Doc 1 §16)* | Per intent | Emit empty **array**. The `ImportBotFromJSON` procedure iterates with `JSON_LENGTH` + integer indexing — the object form would index `[0]` on a populated `{}` and break. Older production samples may show `{}`; functionally equivalent only while empty. Forward-compatible shape is `[]`. |
| 9 | `ValidationRules: {}` | Per parameter | Emit empty object. |
| 10 | `ValidationPattern: null` | Per parameter | Emit `null`. |
| 11 | `IntentConditionList: []` | Inside `ConditionGroupList` (when present) | Emit empty array. v1 always empty. |
| 12 | `silenceRelations: []` | Top of `intentList` | Emit empty array. v1 always empty. |
| 13 | `BotLanguages: []` | Bot top-level | Emit empty array. |
| 14 | `llmDescription: ""` | Per intent (`IntentConfig.prompts`) | Emit empty string. |
| 15 | `IntentResponces.IsActive: 1` | Inside every `IntentResponces` | Emit `IsActive: 1` as the **first** key inside `IntentResponces`, before `ResponseTypeId` and `Configuration` (applies to RT=1, RT=2, RT=3, RT=4 uniformly). The platform's `ImportBotFromJSON` procedure reads `IntentResponces.IsActive` for the per-intent active flag. **v1.5.0 update:** intent-root `IsActive: 1` and intent-root `AccountId: <bot AccountID>` ARE emitted (restored from production observation; the prior v1.4.1 "anti-quirk" wording was incomplete). Intent-root `IsDeleted` remains NOT emitted (production doesn't have it). The platform reads `IntentResponces.IsActive` for the per-intent active flag (unchanged); the intent-root `IsActive` is for audit/UI display. |
| 16 | Nested `AIModelConfig` (capital I) inside top-level `AiModelConfig` (lowercase i) | `<root>.AiModelConfig.AIModelConfig` | The top-level object is named `AiModelConfig` (lowercase `i`); it contains a nested object named `AIModelConfig` (capital `I`). These are two distinct fields at two levels — the outer wrapper and the inner config blob. Do not collapse them into one. See §4.2.3. |
| 17 | `recordAgentCalls` emitted as **string** `"false"` / `"true"` | `ActiveVersionInfo.AIModelConfig.recordAgentCalls` | Not a JSON boolean — emitted as the string literal `"false"` or `"true"`. Source is spec section 1 `**Record agent calls:**`. Default is `"false"`. |
| 18 | `realtimeInputConfig.automaticActivityDetection.disabled` emitted as **string** `"true"` | `ActiveVersionInfo.AIModelConfig.created.realtimeInputConfig.automaticActivityDetection.disabled` | Not a JSON boolean — emitted as the string literal `"true"`. Production constant for Gemini 3.1 Voice driven. |
| 19 | `IntentParameters[].ModifiedBy: " "` (single space literal) | Per parameter, `ModifiedBy` field | Emit a single space character `" "` — not `null`, not `""`, not `"SYSTEM"`. Production constant for every parameter row. |
| (extra) | `response_success` → object `{ "instructions": "<string>" }` | RT=1 + RT=2 + RT=3 `Configuration` | **CORRECTED in v1.5.0** — was documented as bare empty string `""`. Production shows object shape across all RTs; see §4.4 RT-specific tables. Empty inner string (`{ "instructions": "" }`) is the common production value. |
| 20 | `IntentConfig.additional` on every bot-own intent (v1.13.0) | Per intent (`IntentConfig.additional`) | Emit `{ "max_turns": <int>, "sensitive": <bool>, "max_turns_sentence": "<string>" }` per §4.3.1. Never emit `max_turns`/`max_turns_sentence` as direct siblings of `prompts` (pre-v1.13 shape). |
| 21 | `IntentResponces.SuccessCondition: ""` | Per bot-own intent, last key of `IntentResponces` | Mechanical constant — emit the empty string. §4.6 catalog blocks pass through verbatim. |
| 22 | Version-level limit/layer fields (v1.13.0) | `ActiveVersionInfo.AIModelConfig` | Emit `daily_limit`, `dailyLimitLayerId`, `maxDurationLayerId`, `daily_limit_sentence`, `max_duration_sentence`, `IVRLayerSelect_2` per §4.2.3 (siblings of `max_duration`, NOT inside `created`). |
| 23 | RT=3 `Configuration.intentLoadingAnnouncement` (v1.13.0) | Per RT=3 intent | Always emitted, non-empty (Skill 2 check 12 upstream; CHK-17 backstop). |
| 24 | RT=1 `Configuration` carries NO `announcement` key (v1.14.0) | Per RT=1 intent | Emit only `layer` + `intentLoadingAnnouncement`. The farewell lives in the predecessor's `intentInstructions` (FP-8; check 20). |

The "extra" row is from Doc 1 §16's footnote (`response_success` observed but role unclear; preserve from baseline). Skill 3 treats it identically to the 18 numbered quirks.

**Rule for Skill 3:** when in doubt, emit what production samples emit, even if it looks redundant or empty. The platform's import endpoint may strictly require these keys to be present. Cleaning up the schema is a v3 concern (per Doc 1 §17 v2 Roadmap), not Skill 3's call.

---

## Appendix B — Doc 2 §7.5 routing table

When Skill 3 fails, it tells the user which skill to invoke for the fix. This table consolidates the routing logic.

| Failure type | Source | Route |
|---|---|---|
| Parse error: section header / field label deviation | §3 | **Manual fix** — usually a spec hand-edit. Restore the strict-template form, re-invoke Skill 3. |
| Parse error: orphan section 5 entry / undeclared transition target | §3.3 | **Skill 1 patch mode** — structural issue (added/removed an intent, broke transition references). |
| Pre-flight gate A: incomplete spec | §2.3 | **Skill 2 reactivation** — detail the remaining `[structural]` / `[detailed-revisit]` intents. |
| Pre-flight gate C: RT=2 intent missing 7.6 verification | §2.3 | **Skill 2 reactivation** — re-run on the unverified RT=2 intent(s); Skill 2 curls the live API and writes the 7.6 record. |
| CHK-01 fail (botIntents→intents dangling) | procedure file | **Skill 1 patch mode** — intent removed but `botIntents[]` reference not cleaned up. |
| CHK-02 fail (intentRelations dangling) | procedure file | **Skill 1 patch mode** — transition target removed without cleaning up relation. |
| CHK-03 fail (apiSilenceRelations dangling) | procedure file | **Skill 1 patch mode** — API silence fallback intent removed. |
| CHK-04 fail (IntentCategoryId mismatch) | procedure file | **Skill 1 patch mode** — should not happen in v1; report as a likely Skill 1 bug. |
| CHK-05 fail (RT=2 missing pairing) | procedure file | **Skill 1 patch mode** — RT=2 structural authoring incomplete. |
| CHK-06 fail (api_silence_behaviour content mismatch) | procedure file | **Skill 3 internal bug** — both copies emitted from same source; report, don't try to repair. |
| CHK-07 fail: missing variable in 4.5.1/4.5.2/4.5.4 | procedure file | **Skill 1 patch mode** — add the missing variable to the appropriate 4.5.x subsection. |
| CHK-07 fail: typo or wrong variable in per-intent text | procedure file | **Skill 2 reactivation** — fix the reference in `validationPrompt` / `intentInstructions` / per-intent fields. |
| CHK-07 fail: Mustache reference to slot from downstream/cousin intent | procedure file | **Skill 1 patch mode** if the transition graph is wrong; **Skill 2 reactivation** if the reference is wrong. Skill 3 cannot tell which — error message presents both options. |
| Quirk verification fail (§4.5) | §4.5 | **Skill 3 internal bug** — emission code drifted from §16 contract. Report, don't try to repair. |
| CHK-16 fail (speech in validationPrompt) | procedure file | **Skill 2 reactivation** — rewrite as capture mapping (FP-5, patterns C1–C5); scripts → `announcement` / FP-4 instruction lines; guards → persona (Skill 1 patch). |
| CHK-17 fail (RT=3 missing loading announcement) | procedure file | **Skill 2 reactivation** — author the FP-7 filler. |
| CHK-18 fail (foreign-parameter reference) | procedure file | **Skill 1 patch mode** (move the parameter) or **Skill 2 reactivation** (remove the reference) — error presents both. |
| CHK-19 fail (duplicate speak-obligation) | procedure file | **Skill 2 reactivation**; **Skill 1 patch mode** when a bot-level prompt is one of the sites. |
| CHK-20 fail (terminal shape) | procedure file | **Skill 1 patch mode** (structure); **Skill 2 reactivation** (value-mode implementation only). |
| CHK-21 fail (ParameterType mismatch) | procedure file | **Skill 3 internal bug** — report, don't repair. |
| CHK-22 (edges into type-2 globals) | procedure file | **Advisory** — banner line recommending Skill 1 patch to drop the redundant relation. |
| CHK-23 (off-topic global / persona rule missing) | procedure file | **Advisory** — banner line recommending Skill 1 patch mode (§3.2.5 off-topic elicitation) to add the dedicated off-topic global and/or the persona rule (v1.14.0, FP-6). |
| CHK-24 fail (turn-yield: non-empty announcement on auto-chaining intent) | procedure file | **Skill 2 reactivation** — empty the announcement; remaining speech → FP-4 quoted line in `intentInstructions` before the forward; wait rule → immediate-forward instruction (v1.17.0, FP-3). |
| Section 6 regeneration drift | §5 | **Soft warning, not blocking** — recorded in banner. User can fix via Skill 1 patch (regenerates section 6) if it bothers them; Skill 3 emits anyway. |

---

## Appendix C — Banner worked example

Sample banner for a hypothetical bot with: 1 unknown webhook URL, no model config IDs (Gemini Live with TODO), section 6 drift on subsection 6.1 (a Mustache reference Skill 2 forgot to log), and section 7.4 in agreement with emitted sentinels. (Note: RT=1 layer no longer produces a sentinel as of v1.12.0 — it defaults to `0`.)

```
# Voicenter Bot JSON — generation banner
# Skill suite: v1
# Generated: 2026-05-01T14:32:18Z
# Source spec: agent-spec.md
# Source spec version: 1.0.0
#
# UNKNOWN VALUES — user must replace before import:
#   - intents[1].IntentResponces.Configuration.url: "<USER_TO_FILL: webhook_url>" (RT=2 webhook for validate_customer_address)
#   - AccountID: -999 (customer account ID; user knows this)
#   - AiModelConfig.AIModelConfigID: -999 (Gemini Live; catalog has TODO)
#   - AiModelConfig.AIModelTypeId: -999 (Gemini Live; catalog has TODO)
#   - ActiveVersionInfo.AIModelConfigId: -999 (mirror of above)
#
# DRIFT NOTES (section 6 sanity check):
#   - 6.1: regenerated had 1 reference the spec did not log — {{caller_phone}} used in confirm_appointment.intentInstructions
#   - 6.2: in agreement
#   - 6.3: in agreement
#   - 6.4: in agreement
#   - 6.5: in agreement
#
# RECONCILIATION (section 7.4 vs emitted sentinels):
#   - 7.4 and emitted sentinels in agreement.
#
# DOCTRINE SENTINELS (Compass advisories not resolved during authoring):
#   - No doctrine sentinels.
#
# DEFAULTS APPLIED:
#   - ActiveVersionInfo.AIModelConfig.created.realtimeInputConfig.automaticActivityDetection.disabled = "true" (v1.5.0 lean payload constant)
#   - ActiveVersionInfo.AIModelConfig.max_duration = 1200 (v1.5.0 default — see spec section 1)
#   - ActiveVersionInfo.AIModelConfig.daily_limit = 600, dailyLimitLayerId = 3, maxDurationLayerId = 0, IVRLayerSelect_2 = 3 (v1.14.0 defaults — layer targets are account-specific; verify after import)
#   - IntentConfig.additional defaults applied (max_turns = 5 / sensitive = false / max_turns_sentence masculine fallback) on intents without spec overrides (v1.14.0)
#   - ActiveVersionInfo.AIModelConfig.recordAgentCalls = "false" (v1.5.0 default — see spec section 1)
#   - All intents: Priority = 1, MaxAttempts = 3, ValidationTimeout = 30 (per Doc 1 §9.0)
#   - intentCategories: single default category, IntentCategoryId = -3
#   - All §16 quirks emitted per Appendix A checklist
```

The banner stays terse — one line per item, prefixed with `#` so the user can paste it as a comment block in their notes if useful. The JSON code block follows the banner directly with no decorative separator beyond a blank line.

---

## Appendix D — Static reference data (single source of truth)

This appendix consolidates every static integer ID Skill 3 emits into the JSON. All values come from `database/Tables/StaticData/*.Data.sql`. The skill MUST NOT invent IDs outside this set. When in doubt, re-read the Data.sql files — they are the contract.

### D.1 `AiModelConfig.AccountId` — always `0` (the reuse-existing-config switch)

The `ImportBotFromJSON` procedure branches on this field:

```sql
IF $.AiModelConfig.AccountId = 0 THEN
    use existing AIModelConfigID directly         -- "shared/default model" path
ELSE
    INSERT new AIModelConfig (AccountId=p_new_account_id,
                              AIModel, Name, AIModelConfig (JSON), IsActive, ApiKey)
END IF;
```

**v1 always emits `AccountId: 0`.** The catalog (`model-catalog.md`) lists only default `AIModelConfig` rows where `AccountId = 0` in the platform DB; emitting `AccountId: 0` causes the procedure to reuse the row pointed at by `AIModelConfigID`. No new row is inserted, no NOT NULL columns to fill.

Path 2 (account-private new-config insert) is documented in §4.2.3 but not exercised in v1.

### D.2 `BotStatusId` (root)

| ID | Name | When |
|---|---|---|
| **1** | Active | **v1 default — always emitted** |
| 2 | Inactive | not emitted by Skill 3 |
| 3 | Maintenance | not emitted |
| 4 | Deleted | not emitted |

### D.3 `BotVersionStatusId` (`ActiveVersionInfo`)

| ID | Name | When |
|---|---|---|
| 1 | Draft | not emitted |
| 2 | Testing | not emitted |
| **3** | Approved | **v1 default — matches Yuval/Refua production samples** |
| 4 | Deployed | not emitted |
| 5 | Archived | not emitted (inactive in DB) |

### D.4 `BotIntentTypeID` (`botIntents[]`)

Acts as a discriminator controlling selective `botIntents[]` membership (see §4.3.3). Both values are emitted in v1.8.0; chained intents are omitted.

| ID | Name | When |
|---|---|---|
| **1** | Entry | **entry (start) — directly triggerable from the bot's opening behaviour** |
| **2** | Global | **global — triggerable from anywhere (transfer-to-human, WhatsApp)** |

### D.5 `IntentCategoryId` + `PriorityId` (`intentCategories[]`)

| Field | Value | Source |
|---|---|---|
| `IntentCategoryId` | `-3` | placeholder; resolved by procedure |
| `PriorityId` | **`1`** (production observation) | `Priority` static table. **v1.5.0 correction:** was documented as `2` (Medium) in prior baseline; production exports show `1`. |
| `Name` | Spec section 1 `**Bot Name:**` value | v1.12.0 — per-bot unique category name (was the literal `"Default Category"`) |

### D.6 `ResponseTypeId` (`intents[].IntentResponces.ResponseTypeId`)

| ID | DB name | This skill's section label | Configuration shape |
|---|---|---|---|
| 1 | IVR | "Layer Transfer (terminal)" | §4.4 RT=1 |
| 2 | API | "API Call" | §4.4 RT=2 |
| 3 | Message | "Continue" | §4.4 RT=3 |
| 4 | Dial | "Dial-Out" | §4.4 RT=4 |

The DB names differ from this skill's documentation labels (e.g., RT=1 is "IVR" in the DB but "Layer Transfer" in §4.4). The integer IDs are the contract — labels are informational.

### D.7 `SourceID` (`IntentSources[]`)

The wire-format emits `IntentSources` per intent based on the spec section 1 `Channels Active` field. The procedure walks this array and inserts into the DB `IntentSource(IntentID, SourceID)` table.

| `SourcesID` | `SourceName` | Spec `Channels Active` token |
|---|---|---|
| 1 | VOICE | `voice` |
| 2 | CHAT | `chat` |
| 3 | WEB | (not currently exposed in Skill 1's channel options) |

| Spec `Channels Active` | Per-intent emission |
|---|---|
| `voice` | `[{ "SourceID": 1, "SourceName": "VOICE", "IntentSourceID": <placeholder from -4000 range> }]` |
| `chat` | `[]` (no production sample for chat-only; emit empty array; flag in banner) |
| `voice, chat` | `[{ "SourceID": 1, "SourceName": "VOICE", "IntentSourceID": <placeholder> }]` (v1: emit voice entry only; chat structural support deferred to v2) |

**v1.5.0 wire-format correction.** Prior baseline emitted `[{ "SourceID": 1 }]` for voice (a shape derived from the database `IntentSource` table). Production exports of Gemini 3.1 Voice driven bots carry the fuller shape with `SourceName` and `IntentSourceID` (a row PK). v1.5.0 emits the production shape. Production also varies per-intent (some intents have `[]` even when voice is active) — Skill 3 v1.5.0 emits the populated shape uniformly per the spec's design decision; future versions may add per-intent opt-out via spec section 4.7.

### D.8 `ParameterTypeId` (`IntentParameters[]`)

| ID | Name | v1 supports |
|---|---|---|
| **1** | STRING | yes |
| **10** | PHONE | yes |
| **16** | BOOLEAN | yes |
| **19** | ENUM | yes (with `OptionList`) |
| 4 | INTEGER | accepted as raw spec input only |
| 7 | EMAIL | accepted as raw spec input only |
| 13 | DATE | accepted as raw spec input only |
| 20 | JSON | accepted as raw spec input only |
| 21 | LABEL_SET_SINGLE | v3 |
| 24 | LABEL_SET_MULTIPLE | v3 |

### D.9 `IntentRelatedTypeID` — procedure-internal, not emitted

| ID | Name | Used by procedure for |
|---|---|---|
| 1 | IntentRelated | `IntentRelatedDTMF.RelatedTypeID` for `intentRelations[]` DTMF |
| 2 | BotIntent | `IntentRelatedDTMF.RelatedTypeID` for `botIntents[]` DTMF |

The procedure assigns these values internally based on which array it's iterating. JSON does not emit them.

### D.10 `IntentScriptType` — not emitted in v1

| ID | Name | Active in DB |
|---|---|---|
| 1 | Opening | active |
| 2 | Collection | active |
| 3 | Validation | active |
| 4 | Success | inactive |
| 5 | Failure | active |
| 6 | Closing | active |

v1 emits `IntentScripts: []`. v3 will populate; entries pair `ScriptTypeId` with `LanguageCode` from the DB `Language` table.

### D.11 Default `AIModelConfig` rows (`AccountId = 0`)

The full set of catalog-eligible default models. See `model-catalog.md` for the named entries Skill 1 presents to users.

| `AIModelConfigID` | `AIModelTypeId` (= `AIModel` FK) | Name | Active |
|---|---|---|---|
| 1 | 1 | Public GPT-4 Standard | active |
| 52 | 10 | Public Gemini-2.5 Standard | active |
| 91 | 13 | Public GPT- RealTime | active |
| 132 | 15 | Public GPT Realtime Mini | active |
| 136 | 16 | Public Gemini voice driven | active |
| 139 | 18 | Gemini 3.1 - Voice driven | active |
| 142 | 21 | Gemini 3.1 - LLM driven | active |
| 4 | 4 | Public GPT-3.5 Standard | inactive |
| 7 | 7 | Public PaLM Standard | inactive |

Skill 3 emits one of the active rows per the catalog mapping; the matching `AIModelTypeId` is the row's `AIModel` FK. When the user picks "Gemini Live" in Skill 1, the catalog resolves to row **139** (the active Gemini 3.1 Voice driven default).
