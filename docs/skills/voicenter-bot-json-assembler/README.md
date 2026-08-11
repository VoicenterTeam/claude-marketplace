# Skill: `voicenter-bot-json-assembler`

Assemble a fully-detailed Agent Spec into deployable Voicenter Bot JSON. Skill 3 in the three-skill pipeline.

> Source: [`plugins/voicenter-bot-builder/skills/voicenter-bot-json-assembler/SKILL.md`](../../../plugins/voicenter-bot-builder/skills/voicenter-bot-json-assembler/SKILL.md)
> Plugin: [voicenter-bot-builder](../../plugins/voicenter-bot-builder.md) · Pipeline phase: **3 / 3**

---

> **Language.** Reply in the user's language: detect what they write — Hebrew→Hebrew, English→English — and mirror it, switching if they switch mid-conversation. This shapes your prose, your questions, and your `AskUserQuestion` option labels only. It does **not** change the artifacts you produce — identifiers, JSON keys, BCP-47 language codes, API field names, and other data stay exactly as specified.

> **Opening.** Your first message greets bilingually so the user knows both languages are available — e.g. *"נוכל להמשיך בעברית או באנגלית — מה נוח לך? / We can continue in Hebrew or English — whichever you prefer."* Then mirror whatever language the user replies in.

> **One question per turn.** Ask exactly one question per message and wait for the answer before asking the next — never present multiple questions in a single turn. When the answer is a closed set (pick-one / yes-no / pick-from-list), use the `AskUserQuestion` tool rather than plain text; it automatically adds an "Other" free-text escape, so don't hand-roll one. Reserve plain free-text questions for genuinely open inputs (names, descriptions, URLs, numbers).

## What it does

Mechanically projects a `[detailed]` Agent Spec into Bot JSON wire format. Produces:

- `bot-<identifier>-<YYYY-MM-DD>.json` — the deployable JSON
- `bot-<identifier>-<YYYY-MM-DD>.banner.md` — a sidecar listing every fail-loud sentinel, drift note, and applied default

**Operating principle: pure parser, not interpreter.** Skill 3 makes no creative decisions. If the spec deviates from the strict template, Skill 3 emits a structured parse error and refuses to assemble. If the §15.4 cross-reference pass fails any of **twenty-five checks** (eight §15.4 + three Compass + three botIntents-role + one duplicate-global-intent + nine field-placement doctrine + one persona-FK sanity — v1.13.0/v1.14.0/v1.17.0/v1.18.0), Skill 3 emits a structured failure report with routing recommendations and refuses to emit JSON. Checks 1–7, 11–13, 15, 16–21, and 24 are blocking; 14, 22, 23, and 25 are advisory. The discipline is the design — if Skill 3 interpreted, "what JSON does this spec produce?" would depend on Skill 3's mood, and the source-of-truth contract dies.

The risk vector is **doing too much**: filling in plausible-looking values for unknowns, smoothing over template deviations, auto-fixing cross-reference violations. The skill's longest section (anti-list §8) is the explicit "do not" list.

---

## When to invoke

- Every intent in section 5 is `[detailed]` — Skill 2 is done.
- The user asked to *"assemble the JSON"*, *"emit the bot JSON"*, *"publish the bot"*, *"build the wire-format"*, or *"run Skill 3"*.
- Skill 2 emitted a handoff hint pointing to Skill 3.

Skill 3 refuses to run if any intent is still `[structural]` or `[detailed-revisit]` — it cites the pending list and recommends Skill 2.

---

## Pre-flight gates

Three gates run before any assembly. All blocking. Refusal at any gate emits a clear message and halts; no JSON is produced.

| Gate | Check | Refusal route |
|---|---|---|
| **A — Completeness** | Section 5 has zero `[structural]` or `[detailed-revisit]` intents | Skill 2 (Intent Detail Author) |
| **B — Parseability** | Strict-template parser succeeds against the spec | Skill 1 patch mode (structural deviation) or manual fix |

In a malformed spec where section headers are missing entirely, Gate B fires first; in a structurally clean spec with pending intents, Gate A fires first.

**Gate C — RT=2 verification.** Every RT=2 intent must carry a section 7.6 verification record (written by Skill 2 after a live `curl` confirmed 2xx + every declared response path). A missing record refuses assembly — backstop against a hand-edited spec. No waiver.

---

## Strict-template parser

Skill 3 reads the Agent Spec as a fixed grammar — no synonyms, no flexibility, no creative tolerance. The parser expects:

- **Section headers exact:** `## 1. Bot Identity`, `## 2. Persona Bundle`, `## 3. Caller Silence Behavior`, `## 4. Intent List (Structural)`, `## 4.5 Available Variables`, `## 4.6 Global/System Catalog Intents`, `## 5. Intent Details`, `## 6. Cross-References`, `## 7. Generation Metadata`.
- **Section 4.6 (optional):** either the literal `[none]`, or one or more `### Catalog Intent: <IntentId> — <Name>` blocks, each with `**Wiring:** silence-forward only|triggerable global` and a `**Definition:**` fenced ```json block. The JSON block must parse and carry a positive-integer `IntentId` and an `IntentCategoryId`. A malformed block or a non-positive `IntentId` is a parse error — Skill 3 does NOT repair it.
- **Field labels exact:** `**Bot Name:**`, `**Identifier:**`, `**Description:**`, `**Account ID:**`, `**Primary Language:**`, `**Channels Active:**`, `**Voice Name:**`, `**AI Model Config:**`.
- **Section 1 optional limit fields (v1.13.0):** `**Daily limit:**` (int), `**Daily limit layer:**` (int), `**Max duration layer:**` (int), `**Daily limit sentence:**` (free text), `**Max duration sentence:**` (free text), `**IVRLayerSelect_2:**` (int). All optional; absence parses to defaults 600 / 3 / 3 / production-default sentence / production-default sentence / 3 (see the version-envelope mapping below). A non-integer where an int is expected is a parse error.
- **Section 1 `**Negative instructions:**` (v1.16.0, optional):** free text. **Parse-only — never emitted to the wire JSON** (the wire field name is unverified). When present, the banner gains a MANDATORY POST-IMPORT step: paste the text into the UI's AI Security Settings → Negative Instructions field.
- **Status markers exact:** `[structural]`, `[detailed]`, `[detailed-revisit]`. No synonyms.
- **Unknown markers exact:** `<UNKNOWN: <description>>`, `<INCOMPLETE: <description>>`, `[not configured]`. Angle brackets, literal token.
- **Intent header in section 4:** `### Intent N: <identifier>` where N is the 1-based ordinal.
- **Bot-intent role in section 4:** `**Bot-intent role:** <value>` where `<value>` is exactly `entry`, `global`, or `chained`. The field is optional; absence is parsed as `chained`. Any other value (e.g. `start`, `escalation`) is a parse error. This field drives `botIntents[]` membership/type.
- **Staggering fields in section 4 (v1.13.0, optional):** `**Captures answer to:**` (free text) and `**Asks next:**` (free text, or the literal `[none — terminal]`). Absence ⇒ the staggering-dependent checks skip for that intent.
- **Terminal outcome in section 4 (v1.13.0, optional; RT=1 only):** `**Terminal outcome:** <slot_name> = <value-part>`. Two-mode grammar: a double-quoted `<value-part>` ⇒ **fixed** mode (the exact pinned string); an unquoted free-text `<value-part>` ⇒ **captured/dynamic** mode (a description of how the value is captured or composed). A line without `<slot_name> =` is a parse error. `<slot_name>` must be snake_case and is cross-checked against the intent's slot list by cross-reference check 20.
- **Sensitive in section 4 (v1.13.0, optional):** `**Sensitive:** true|false` only. Absence parses as `false`. Any other value is a parse error.
- **Intent header in section 5:** `### Intent: <identifier>`.
- **Section 4.5.5 (v1.13.0, optional):** header exact `### 4.5.5 CustomData keys (per-call payload)` under `## 4.5 Available Variables`; entries `- \`{{key}}\` — <meaning>`. Absence ⇒ empty CustomData key list (check 7 then allows only 4.5.1–4.5.4 references).
- **Slot lines** in section 4: numbered, format `[slot_name] — \`ParameterTypeId\` [N], Required [\`true\`|\`false\`], Order [N], OptionList [if ENUM], DefaultValue [value]`. The `DefaultValue` segment is optional (v1.16.0); absence parses to `""` (the older slot-line format without the segment remains valid).
- **Transition lines** in section 4: numbered list under `**Transitions out:**`, target identifier optionally followed by a parenthetical role label.
- **RT-specific sub-labels in section 4:**
  - RT=1: `**Layer:**` followed by an integer.
  - RT=2: `**URL:**`, `**Method:**`, `**Headers:**`, `**Body:**`, `**API silence behavior:**` (six sub-bullets exact: `silence_duration:`, `silence_loops:`, `silence_sentence:`, `silence_ending_sentence:`, `silence_instructions:`, `fallback intent:`).
  - RT=3: empty.
  - RT=4: `**Dial source:**` (`parameter` | `static`), then `**Parameter phone:**` OR `**Phone1:**`/`**Phone2:**`/`**Phone3:**`, plus `**selectdial_option:**`, `**NEXT_VO_ID:**`, `**MAX_DIAL_DURATION:**`, `**Record:**`, optional `**Announcement:**` / `**Loading announcement:**` / `**Post-execution intent instructions:**`, and `**Response success:**`.

Common deviations the parser surfaces:

| Deviation | Example error |
|---|---|
| Missing section header | `Expected: '## 4. Intent List (Structural)'. Found: '## Intent List'. Fix: restore the section number and exact heading.` |
| Bold field label punctuation off | `Expected: '**Bot Name:** <value>'. Found: 'Bot Name: <value>'. Fix: wrap the label in bold markdown.` |
| Unknown marker shape wrong | `Expected: '<UNKNOWN: <description>>'. Found: '(UNKNOWN: ...)'. Fix: use angle brackets and the literal token UNKNOWN.` |
| RT-specific sub-label punctuation off | `Expected: '**URL:** <value>'. Found: 'URL: <value>'. Fix: wrap the sub-label in bold markdown.` |
| Status marker synonym | `Expected: one of '[structural]', '[detailed]', '[detailed-revisit]'. Found: '[done]'. Fix: re-run Skill 2 to set the canonical marker.` |
| Bot-intent role value off-grammar | `Expected: '**Bot-intent role:** entry\|global\|chained'. Found: '**Bot-intent role:** start'. Fix: use one of the three canonical role values (or omit for chained).` |
| Section 4 transition target missing | `Intent 'validate_customer_address' transitions to 'get_slots', but no intent 'get_slots' exists in section 4 (closest match: 'get_available_slots'). Fix: re-run Skill 1 patch mode.` |
| Terminal outcome missing slot assignment (v1.13.0) | `Expected: '**Terminal outcome:** <slot_name> = "<fixed value>"' or '**Terminal outcome:** <slot_name> = <capture/compose description>'. Found: '**Terminal outcome:** הלקוח אישר הכל'. Fix: name the owning slot and use '=' (quote the value only when it is a fixed pinned string).` |
| Sensitive value off-grammar (v1.13.0) | `Expected: '**Sensitive:** true\|false'. Found: '**Sensitive:** yes'. Fix: use lowercase true or false (or omit for false).` |

Skill 3 halts on the first deviation, emits a structured error, and does not attempt to interpret around it. One deviation, one error, one halt.

---

## Spec-to-wire-format assembly

Runs only if all three pre-flight gates pass.

### ID placeholder allocation

Sequential negative integers, range-coded so the kind of ID is identifiable at a glance:

| ID kind | Placeholder range | Rule |
|---|---|---|
| `BotID` | `-1` | Single value |
| `BotVersionId` | `-2` | Single value |
| `IntentCategoryId` | `-3` | Single category, named after the bot (v1.12.0) |
| `IntentId` | `-10, -11, -12, ...` | One per intent in section 4 ordering |
| `BotIntentId` | `-100, -101, -102, ...` | **v1.8.0: one per emitted `botIntents[]` entry (entry + global intents only)** — chained intents get no `BotIntentId`. In section-4 order over the emitted subset. (note lowercase `d` per production casing) |
| `ParameterId` | `-1000, -1001, ...` | One per slot, intent-by-intent then slot-by-slot |
| `IntentRelatedID` | `-2000, -2001, ...` | **v1.5.0:** one per `intentRelations[]` row (unique row PK — no longer mirrors `NextIntentID`) |
| `IntentConditionGroupID` | `-3000, -3001, ...` | **v1.5.0:** one per emitted `botIntents[]` entry (entry + global only — v1.8.0 selective) + one per `intentRelations[]` row |
| `IntentSourceID` | `-4000, -4001, ...` | **v1.5.0:** one per intent when voice channel is active |

Real platform-assigned IDs after import are positive integers, so there's no collision risk on re-export.

### Top-level wrapper and version envelope

Section 1 fields map to top-level root keys in production order: `Name`, `BotID`, `AccountID`, `intentList` (position #4 — v1.5.0 correction), `BotStatusId`, `CreatedDate`, `Description`, `BotLanguages`, `ModifiedDate`, `AiModelConfig`, `ActiveVersionInfo`.

**`ActiveVersionInfo` field order (v1.5.0):** `IsActive` is first (was `BotVersionId` in prior baseline). Fields: `IsActive`, `CreatedDate`, `Description`, `BotVersionId`, `ModifiedDate`, `SystemPrompt`, `AIModelConfig`, `VersionNumber`, `AIModelConfigId`, `BotVersionStatusId`, `PersonaID` (v1.18.0 — see below).

**`PersonaID` (v1.18.0, new).** `BotVersion.PersonaID` is a `bigint NOT NULL` FK on `Persona`; per the `ImportBotFromJSON` stored-procedure contract (`references/voicebot-json-contract.md` R7), an omitted/null value makes the proc fall back to the first `Persona` row with `AccountId=0` — if that row is absent on the target server, the BotVersion insert fails, producing a Bot with intents but no version. Skill 3 does not rely on that implicit fallback: it always emits the known shared value `3` (`TTSScriptReader`), banner-noted under DEFAULTS APPLIED. No golden production export has been captured with this field yet, so its position in the object is unverified — Skill 3 appends it last pending confirmation.

**The two `AIModelConfig` objects** (top-level `AiModelConfig` + version-level `AIModelConfig` per Doc 1 §6) now carry **distinct** `created` payloads (v1.5.0):

- **Top-level `AiModelConfig.AIModelConfig.created`** — lean: `{ "model": "<provider model string>" }` only.
- **Version-level `ActiveVersionInfo.AIModelConfig.created`** — lean: `realtimeInputConfig` + voice `generationConfig` only (no temperature, topP, topK, responseModalities, systemInstruction, tools — all dropped in v1.5.0).

**Version-level `ActiveVersionInfo.AIModelConfig` fields (v1.5.0, extended v1.13.0):** `max_duration` (spec section 1 `**Max call duration:**`, default 1200), `daily_limit` (spec section 1 `**Daily limit:**`, integer, default 600 — v1.13.0 golden-export field), `dailyLimitLayerId` (spec section 1 `**Daily limit layer:**`, integer layer ID, default 3 — v1.13.0), `maxDurationLayerId` (spec section 1 `**Max duration layer:**`, integer layer ID, default 3 — v1.13.0), `daily_limit_sentence` (spec section 1 `**Daily limit sentence:**`; production-derived default `"Sorry, but reached daily limit of calls duration, please try again later or contact the copany's support"` — v1.13.0), `max_duration_sentence` (spec section 1 `**Max duration sentence:**`; production-derived default `"Sorry, but reached max duration of the call, please try again later"` — v1.13.0), `IVRLayerSelect_2` (spec section 1 `**IVRLayerSelect_2:**`, integer, default 3 — v1.13.0), `prompts` (five-field bundle), `recordAgentCalls` (spec section 1 `**Record agent calls:**` emitted as STRING `"false"`/`"true"`), `silence_behaviour` (conditional on section 3; **v1.8.0:** carries a structural `intent` failover as its first key — the resolved `IntentId` to jump to on caller-silence exhaustion, defaulting to the transfer-to-human global; the bot-level analogue of `api_silence_behaviour.intent`), `created` (lean payload above). Fields `tools: []` and `instructions: ""` removed from this level.

**v1.13.0 fields added (golden export `בוט שיקוף – קבוצת קלי v0.0.17`):** the six limit/layer fields above are all **siblings of `max_duration`** at this level — NOT inside `created`. When a default is applied (spec field absent), it is listed in the banner's DEFAULTS APPLIED section. The layer-target defaults (`3`) are golden-derived and account-specific — Skill 1 may offer the MCP layer list when collecting them; the banner note lets the operator re-check them post-import.

**Top-level `AiModelConfig` fields (v1.5.0):** `Name`, `ApiKey: {}`, `AIModel` (AIModelTypeId integer), `IsActive: 1`, `AccountId: 0`, `ModifiedBy: null`, `CreatedDate`, `ModifiedDate`, `AIModelConfig` (nested object with only `created: { "model": "..." }`), `AIModelConfigID`. Fields `Description`, `BaseUrl`, `Type`, `AIModelTypeId` (as separate field), full `created` payload removed.

### `IntentConfig` — the `additional` block (v1.13.0)

Each intent's `IntentConfig` (row 8 of the 17-field intent shape) is now:

```json
{
  "prompts": { "llmDescription": "", "validationPrompt": "<section 5 verbatim>" },
  "additional": { "max_turns": 5, "sensitive": false, "max_turns_sentence": "" }
}
```

`llmDescription` is unchanged (always `""`). `IntentConfig.additional` is emitted on **every** bot-own intent (golden export `בוט שיקוף – קבוצת קלי v0.0.17` carries it on every real intent) with three keys:

| Key | Default | Spec override |
|---|---|---|
| `max_turns` | RT=2: `15` (v1.5.0 rationale preserved); RT=1/3/4: `5` (golden-export value) | Section 4 `**Max turns:**` |
| `sensitive` | `false` (JSON boolean) | Section 4 `**Sensitive:**` |
| `max_turns_sentence` | RT=2: `"אני חייב לסיים את השיחה בשלב הזה."`; RT=1/3/4: `""` | Section 4 `**Max turns sentence:**` (the golden reference sets a Hebrew technical-difficulty fallback on its callback intent) |

**This replaces the pre-v1.13 sibling emission block: never emit `max_turns` / `max_turns_sentence` as direct siblings of `prompts` inside `IntentConfig` (the pre-v1.13 shape)** — they live inside `additional` together with `sensitive`. When a default is applied, it is listed once in the banner DEFAULTS APPLIED section (aggregated, not per-intent). The RT=2 `max_turns: 15` standardization (v1.5.0 design decision 6, mixed production distribution) is preserved inside `additional`; spec authors can override per intent via section 4 `**Max turns:**`.

### `ParameterType` system dictionary (v1.13.0 — CORRECTED)

Per-type system-dictionary values are **captured VERBATIM from production exports — never re-authored**. STRING/BOOLEAN/ENUM/INTEGER/JSON are verified against the golden export `בוט שיקוף – קבוצת קלי v0.0.17`; the pre-v1.13 BOOLEAN/ENUM rows were wrong "extrapolated" guesses, corrected below:

| ParameterTypeId | Name | Description | ValidationPattern | IsCustomValidationAllowed | CreatedDate |
|---|---|---|---|---|---|
| 1 | `"STRING"` | `"Basic text input"` | `null` | `1` | `"2025-01-21 11:25:25"` |
| 4 | `"INTEGER"` | `"Whole number input"` | `"^[0-9]+$"` | `1` | `"2025-01-21 11:25:25"` |
| 10 | `"PHONE"` | `"Phone number"` | **unverified** | **unverified** | `"2025-01-21 11:25:25"` |
| 16 | `"BOOLEAN"` | `"Yes/No input"` | `"^(true\|false\|yes\|no)$"` | `0` | `"2025-01-21 11:25:25"` |
| 19 | `"ENUM"` | `"Selection from predefined options"` | `null` | `0` | `"2025-01-21 11:25:25"` |
| 20 | `"JSON"` | `"json schema"` | `null` | `0` | `"2025-04-10 09:50:42"` |

Shared constants across all types: `IsActive: 1`, `CreatedBy: "SYSTEM"`, `ModifiedBy: null`, `ModifiedDate: null`.

**PHONE (10) is unverified** — no production export in hand carries it. Until its dictionary row is captured from a real export or `ParameterType.Data.sql`, Skill 3 emits `ValidationPattern: null`, `IsCustomValidationAllowed: 1` (the pre-v1.13 values) AND adds a banner line: `ParameterType PHONE block unverified against system dictionary — verify after import`. Cross-reference check 21 byte-matches every emitted ParameterType block against this table; unverified PHONE downgrades to the banner note instead of failing.

### Per-RT Configuration assembly

**Outer shape — invariant across all RTs (v1.13.0).** Every `IntentResponces` object has the same **four** top-level keys in this order (verified against the golden export): `IsActive` (always `1` in v1), `Configuration`, `ResponseTypeId`, `SuccessCondition`. `SuccessCondition` is always the empty string `""` on bot-own intents; §4.6 catalog blocks pass through verbatim (the canonical intent 19 carries `null`, which stays `null`). The table below lists only what's inside `Configuration` for each RT — the outer keys are invariant.

Skill 3 emits the Configuration shape per Response Type, populating language fields verbatim from section 5:

| RT | Configuration keys |
|---|---|
| 1 | `layer`, `announcement` (optional), `intentLoadingAnnouncement` (always emitted). Terminal doctrine (v1.13.0, FP-8) — one RT=1 terminal per outcome, owning its outcome slot, no terminal→anything relations — is validated by cross-reference check 20. |
| 2 | `url`, `method`, `headers`, `body`, `announcement` (v1.5.0 — was `apiResponseAnnouncement`), `fail_output`, `function_output` (object `{ "default": "..." }` — v1.5.0), `response_success` (object `{ "instructions": "..." }` — v1.5.0), `intentLoadingAnnouncement` (lowercase only — capital-I `IntentLoadingAnnouncement` REMOVED), `intentInstructions`, `api_silence_behaviour` (six-key object — see below) |

**`api_silence_behaviour` — the intent-failover object (RT=2).** This object carries the call's silence failover while the webhook runs. It has **six keys**, all mandatory: `intent` (the resolved failover `IntentId`, integer — the spec's `fallback intent:` identifier mapped to its `IntentId`; **never omit, never emit as a string** — equals the paired `apiSilenceRelations[].ApiSilenceIntentID` by construction), `silence_loops`, `silence_duration`, `silence_sentence`, `silence_instructions`, `silence_ending_sentence`. A missing or null `intent` means the intent has no failover — cross-reference check 5 (below) is blocking on this.
| 3 | `announcement`, `response_success` (object `{ "instructions": "..." }` — v1.5.0), `intentInstructions`, `intentLoadingAnnouncement` (**always emitted for RT=3 — v1.13.0, FP-7**; golden-export key order: announcement, response_success, intentInstructions, intentLoadingAnnouncement. Skill 2 check 12 guarantees it is authored non-empty; Skill 3 check 17 backstops — an unset value would produce the default `"."` SAY-directive bug at runtime) |
| 4 | `phone1`, `phone2`, `phone3`, `parameter_phone` (when slot-driven), `selectdial_option`, `NEXT_VO_ID`, `MAX_DIAL_DURATION`, `record`, `announcement`, `intentLoadingAnnouncement`, `intentInstructions`, `response_success` (object `{ "instructions": "..." }`) |

### Optional `ConditionGroupList` and `DTMFList` pass-through

**v1.5.0:** `ConditionGroupList` is now **populated by default** on both `botIntents[]` and `intentRelations[]` with a single structural entry (the production default shape). `DTMFList: []` is also always emitted on both (never omitted). If spec section **4.7 Advanced overrides** is present, Skill 3 passes the user-authored blocks through verbatim.

If spec section **4.7 Advanced overrides** is present (Skill 1 §3.5.5 opt-in), Skill 3 lifts each `### Intent: <identifier>` and `### Transition: <origin> → <next>` block's `condition_groups:` and `dtmf_list:` bodies verbatim into the corresponding JSON fields. Skill 3 does **not** validate the contents — it's pass-through. The user is responsible for the inner schema matching the DB enums (`IntentConditionGroupType`, `IntentConditionRelationType`).

If §4.7 is absent or empty (the default), Skill 3 emits the safe defaults and the bot imports normally.

### Quirk preservation

Skill 3 walks Appendix A (the §16 schema-quirks list) after assembly and verifies every quirk is correctly emitted. Key v1.5.0 quirk updates:

- **Row 2 REMOVED:** the `intentLoadingAnnouncement` + `IntentLoadingAnnouncement` casing-bug pair is obsolete for Gemini 3.1 Voice driven bots. Only the lowercase form is emitted.
- **Row 15 updated:** intent-root `IsActive: 1` and intent-root `AccountId: <bot AccountID>` ARE emitted (restored from production observation). `IntentResponces.IsActive: 1` is also emitted inside the wrapper. Intent-root `IsDeleted` remains NOT emitted.
- **Extra row:** `response_success` is now an object `{ "instructions": "<string>" }` across RT=1 + RT=2 + RT=3 Configuration (was bare empty string in prior baseline).

Key v1.13.0 quirk additions (Appendix A rows 20–23, captured from the golden export):

- **Row 20 — `IntentConfig.additional` on every bot-own intent:** emit `{ "max_turns": <int>, "sensitive": <bool>, "max_turns_sentence": "<string>" }` per the `IntentConfig` rules above. Never emit `max_turns`/`max_turns_sentence` as direct siblings of `prompts` (pre-v1.13 shape).
- **Row 21 — `IntentResponces.SuccessCondition: ""`:** the empty string, as the last key of `IntentResponces` on every bot-own intent. §4.6 catalog blocks pass through verbatim (intent 19 carries `null` — stays `null`).
- **Row 22 — version-level limit/layer fields:** `daily_limit`, `dailyLimitLayerId`, `maxDurationLayerId`, `daily_limit_sentence`, `max_duration_sentence`, `IVRLayerSelect_2` emitted as siblings of `max_duration` inside `ActiveVersionInfo.AIModelConfig` (NOT inside `created`).
- **Row 23 — RT=3 `Configuration.intentLoadingAnnouncement`:** always emitted, non-empty (Skill 2 check 12 upstream; Skill 3 check 17 backstop).

Other active quirks: `IntentResponces` typo, `HandlingInstructions: null` per intent, `SystemPrompt: ""`, dual `AiModelConfig` / `AIModelConfig` (now with distinct lean `created` payloads), `IntentScripts: []`, `ValidationRules: {}` and `ValidationPattern: null` per param (inside `ParameterType`), `silenceRelations: []`, `BotLanguages: []`, `llmDescription: ""`, `Priority: 1` / `MaxAttempts: 3` / `ValidationTimeout: 30` per intent, `silence_behaviour` key omission when section 3 is `[not configured]`, `DTMFList: []` always emitted on `botIntents[]` and `intentRelations[]`.

### Sentinel emission for unknowns

| Spec marker | Wire-format emission |
|---|---|
| `<UNKNOWN: webhook_url>` (string) | `"<USER_TO_FILL: webhook_url>"` |
| `<UNKNOWN: NEXT_VO_ID>` (integer) | `-999` |
| `<UNKNOWN: phone destination>` (string) | `"<USER_TO_FILL: phone3>"` |
| `<UNKNOWN: Account ID>` (integer ID) | `-999` |
| `<UNKNOWN: AI Model Config>` (cascade) | `<USER_TO_FILL: ...>` for strings, `-999` for IDs across the whole `AiModelConfig` block |
| `<UNKNOWN: <object field>>` (object) | `{}` plus a banner note |
| `<INCOMPLETE: ...>` (section partial) | Section emitted with available content; banner notes incompleteness |
| `[not configured]` (whole section) | Section omitted from JSON entirely |

The sentinel value carries the field role inside the placeholder text, so the banner's path-plus-value listing is self-documenting.

---

## §15.4 cross-reference pass — twenty-five checks

After assembly + section 6 sanity check, run all **twenty-five** checks against the in-memory wire structure — eight per Doc 1 §15.4, three Compass doctrine checks (8–10), three botIntents-role integrity checks (11–13, v1.8.0), one duplicate-global-intent check (15, v1.12.0), **nine field-placement doctrine checks (16–24, v1.13.0/v1.14.0/v1.17.0)** per `plugins/voicenter-bot-builder/references/field-placement-doctrine.md`, and one **persona-FK sanity check (25, v1.18.0)** per `plugins/voicenter-bot-builder/references/voicebot-json-contract.md` R7/R11. Checks 1–7, 11–13, 15, 16–21, and 24 are blocking and run unconditionally so the user gets a complete failure report rather than fixing one issue at a time. Check 8 is advisory/blocking by token band, check 9 is advisory, check 10 is blocking on mismatch — all three gated on Gemini 3.1 (`AiModelConfig.created.model = "models/gemini-3.1-flash-live-preview"`, i.e. `AIModelConfigID=139` or `142`). Checks 14, 22, 23, and 25 are non-blocking advisory. Checks 11–13, 15, 16–24, and 25 are model-agnostic. (The v1.8.0 fan-out-completeness check was removed in v1.12.0 when global fan-out was dropped.)

Run order: 1 → 2 → 3 → 4 → 5 → 6 → 7 → 11 → 12 → 13 → 15 → 16 → 17 → 18 → 19 → 20 → 21 → 22 → 23 → 24 → 8 → 9 → 10 → 14 → 25. The pass operates on the assembled in-memory wire structure; checks 16–24 additionally consult the spec's section-4 staggering/terminal/role fields (check 24 reads `**Asks next:**`), the 4.5 variable inventory, and — for check 23 — the persona text. The failure report is count-agnostic: `Checks failed: <count> of <total checks run>`.

| # | Check | Validates |
|---|---|---|
| 1 | `botIntents[].IntentID` resolves | Every `botIntents[].IntentID` matches an `intents[].IntentId` |
| 2 | `intentRelations[]` resolves (both endpoints) | Every `OriginIntentID` and `NextIntentID` matches an `intents[].IntentId`. `IntentRelatedID` is not checked separately (it's a unique row PK from the `-2000` placeholder range — verified by the allocator). |
| 3 | `apiSilenceRelations[]` resolves (both endpoints) | Every `OriginIntentID` and `ApiSilenceIntentID` matches an `intents[].IntentId` |
| 4 | `intents[].IntentCategoryId` resolves | Every `IntentCategoryId` matches an `intentCategories[].IntentCategoryId` |
| 5 | RT=2 has `apiSilenceRelations[]` pairing **and an inline failover `intent`** | Every RT=2 intent has (a) a corresponding `apiSilenceRelations[]` entry, and (b) a `Configuration.api_silence_behaviour.intent` that is a present, non-null integer equal to that entry's `ApiSilenceIntentID`. Missing/null/string `intent` is a blocking failure (no failover). |
| 6 | `IntentResponces.Configuration` matches `apiSilenceRelations[].Configuration` | **Full Configuration deep equality** (v1.5.0 — was just 6 silence fields). Every key in the parent intent's Configuration: `url`, `method`, `headers`, `body`, `fail_output`, `announcement`, `function_output`, `response_success`, `intentInstructions`, `intentLoadingAnnouncement`, and the nested `api_silence_behaviour` sub-object (all six keys including the failover `intent`). |
| 7 | Mustache resolvability | Every Mustache token resolves via 4.5.1 / 4.5.2 / 4.5.3 / 4.5.4 with directional ordering, **or via the §4.5.5 CustomData key list (v1.13.0, FP-11)**. The failure message appends: `CustomData keys are never invented — if {{<name>}} is a real per-call key, add it to spec 4.5.5 via Skill 1 patch mode.` |
| 10 | Model-config doctrine (v1.5.0 inverted) | **Blocking.** Validates that the version-level `AIModelConfig.created` does NOT contain dropped fields (`temperature`, `topP`, `topK`, `responseModalities`, `proactivity`, `thinkingConfig`, `systemInstruction`, `tools`, `affectiveDialog`, `proactiveAudio`). The lean payload has none of these by construction; check 10 catches future regressions. |
| 11 | Global intents have `BotIntentTypeID = 2` | **Blocking (v1.8.0).** Every `global` intent in section 4 maps to a `botIntents[]` entry with `BotIntentTypeID = 2`. An entry with type `1` for a global intent is an emission bug. |
| 12 | No chained intents in `botIntents[]` | **Blocking (v1.8.0).** `botIntents[]` contains only `entry` (type 1) and `global` (type 2) intents. A `chained` intent appearing in `botIntents[]` is an emission error — chained intents are reached only via `intentRelations[]`. |
| 13 | Start point exists | **Blocking (v1.8.0).** At least one intent has role `entry` or `global` so there is a registered start point in `botIntents[]`. A spec with all intents `chained` cannot be imported — the platform has no entry point. |
| 14 | Section-4.6 catalog intents resolve | **Non-blocking advisory (v1.11.0).** Every catalog intent referenced by section 3 (`silence_behaviour.intent`) or any structural failover field is present in the emitted `intents[]` by real `IntentId`, AND its `IntentCategoryId` is present in `intentCategories[]`. The §4.6 parse already guaranteed structure; this check catches a reference to an undeclared catalog id. |
| 15 | No duplicate global intents by tool name (C-e) | **Blocking (v1.12.0).** For each unique `IntentToolName` across section 4, at most **one** intent with that tool name may have role `global` (registered in `botIntents[]` with `BotIntentTypeID = 2`). Multiple globals with the same tool name render as duplicates in the UI (the rebuilt-bot orphan pattern). Detection: group section-4 intents by `IntentToolName`; any group with more than one `global` is a blocking failure listing the duplicate identifiers. |
| 16 | validationPrompt speech-free (v1.13.0, FP-5) | **Blocking.** No `IntentConfig.prompts.validationPrompt` contains imperative speech content — scripts, questions to the caller, greetings, or turn-taking guards. The Intent Agent is the only consumer; anything written to be spoken there is never spoken. Detection, per validationPrompt, per line: (i) imperative-speech regex `(?im)^\s*\W*(say|ask|tell|greet|announce|read (back|aloud)|repeat back)\b` and Hebrew imperatives (`אמרי`, `אמור`, `שאלי`, `שאל`, `חזרי`, `הקריאי`, `קראי`, `ברכי`); (ii) a question mark inside a quoted string or ending a non-quoted line; (iii) guard/gate headers (`(?im)^(TURN.?TAKING|GATE\b)`) or IRON-RULE blocks containing wait/turn phrasing; (iv) greeting tokens (`שלום`, `hello`, `hi there`) outside a saved-value context. **Whitelist:** quoted strings on lines that also contain save/set/store/"exactly" language plus a parameter name owned by THIS intent (protects pinned outcome values and `"true"`/`"false"` literals). |
| 17 | RT=3 `intentLoadingAnnouncement` present (v1.13.0, FP-7) | **Blocking.** Every RT=3 intent's `Configuration.intentLoadingAnnouncement` is present, non-empty, not whitespace-only, and not the literal `"."` (the default SAY-directive bug). Detection: walk RT=3 intents; test the field. |
| 18 | Own-parameter references (v1.13.0, FP-8) | **Blocking.** No intent's `validationPrompt`, `Configuration.announcement`, or `Configuration.intentInstructions` references a parameter name that belongs to a DIFFERENT intent — an intent can only set its own `IntentParameters`; foreign references (e.g., a gate "setting" a terminal's status slot) are un-executable. Detection: build the bot-wide set of all `IntentParameters[].Name` values with their owning IntentIds; scan the three fields for word-boundary matches of any slot name; any match whose owner is a different intent fails, reporting intent, field, matched name, and the owning intent. |
| 19 | No duplicate speak-obligation (v1.13.0, FP-6) | **Blocking.** No normalized speech obligation appears in two or more obligation sites — the diagnosed mechanism of double-speech bugs (e.g., a farewell in both a terminal's announcement and another field). Detection: extract mandated-speech strings — sentences of every `announcement`, every `intentLoadingAnnouncement`, sentences of `prompts.openingAnnouncement`, and FP-4 quoted lines (`: "<...>"`) inside per-intent `Configuration.intentInstructions`, `prompts.intentInstructions`, and `prompts.persona`; normalize each (trim; strip punctuation and niqqud; collapse whitespace); any normalized string ≥ 12 characters appearing in 2+ sites fails, reporting both JSON paths. |
| 20 | Terminal shape (v1.13.0, FP-8) | **Blocking.** Every RT=1 terminal: has `Configuration.layer` (0 allowed — banner-noted); when the spec declares `**Terminal outcome:**`, the named slot exists in that intent's `IntentParameters` AND the validationPrompt implements the declared value mode (fixed mode ⇒ the exact pinned string appears verbatim; captured/dynamic ⇒ a save/compose instruction naming the slot exists); and NO `intentRelations[]` row has an RT=1 intent as `OriginIntentID` (no terminal→anything chains, incl. finalize→end_call). Detection: walk RT=1 intents against the spec section-4 fields and the relations array. |
| 21 | ParameterType dictionary byte-match (v1.13.0) | **Blocking (Skill 3 internal).** Every emitted `ParameterType` object on bot-own intents matches the system-dictionary table (above) field-for-field: Name, Description, ParameterTypeId, ValidationPattern, IsCustomValidationAllowed, IsActive, CreatedBy, CreatedDate, ModifiedBy, ModifiedDate. System dictionary rows are copied verbatim, never re-authored — a mismatch is a Skill 3 emission bug. Carve-outs: §4.6 catalog-intent blocks are verbatim pass-through (excluded); unverified PHONE downgrades to a banner note. |
| 22 | No authored edges into type-2 globals (v1.13.0, FP-9) | **Advisory.** `intentRelations[]` rows whose `NextIntentID` is a type-2 global are legal but usually redundant — globals are reachable from anywhere by construction, and extra edges enlarge the tool-routing surface. Detection: list any relation targeting a botIntents type-2 IntentId; banner line recommending removal via Skill 1 patch mode. |
| 23 | Off-topic global present (v1.14.0, FP-6) | **Advisory.** The mandatory off-topic pair exists: (a) an RT=1 intent registered type-2 in `botIntents[]` whose Description/Name marks it as the off-topic terminal, AND (b) a `prompts.persona` off-topic section (forbid + deflect + N-loop ending) referencing that intent's Description. On miss: banner line routing to Skill 1 patch mode. |
| 24 | Turn-yield announcement gating (v1.17.0, FP-3) | **Blocking** (advisory half noted). A non-empty `announcement` makes the bot yield the turn and WAIT for a caller answer (confirmed live). Every RT=2/RT=3 intent whose section-4 `**Asks next:**` is `[none]` must have `Configuration.announcement === ""` — a non-empty value there stalls the call into the silence loop. Advisory half: those intents' `intentInstructions` should carry no wait rule, only the immediate-forward instruction. RT=1 covered by check 20 (no announcement key); RT=4 exempt (pre-dial speech). Remediation: Skill 2 reactivation — empty the announcement; remaining speech → FP-4 quoted line in `intentInstructions` before the forward. |
| 25 | Persona FK sanity (v1.18.0) | **Advisory.** `ActiveVersionInfo.PersonaID` is present and is one of the known shared `Persona` rows (`AccountId=0`): `{3}` (TTSScriptReader). v1 always emits `3` by construction, so the check is trivial today — it future-proofs a later spec-level persona-selection feature. A value outside the known whitelist gets a banner note asking the operator to confirm the row exists on the target account (FK), rather than a silent pass. |

Failure routing:

| Failure | Route |
|---|---|
| Check 1, 2, 3 — dangling ID | Skill 1 patch mode (structural error — intent deleted but reference not cleaned up) |
| Check 4 — IntentCategoryId mismatch | Skill 1 patch mode (should never happen in v1; if it does, hand-edit error or Skill 1 bug) |
| Check 5 — RT=2 missing pairing | Skill 1 patch mode (RT=2 structural authoring incomplete) |
| Check 6 — `api_silence_behaviour` mismatch | Skill 3 internal bug (Skill 3 emits both from the same source; mismatch means emission bug) |
| Check 7 — Mustache unresolvable | Skill 1 patch mode (variable should exist — add to 4.5.1 / 4.5.4) OR Skill 2 reactivation (reference is wrong — typo) |
| Check 11 — global not type-2 | Skill 1 patch mode — role/registry inconsistency; re-run role classification. |
| Check 12 — chained intent in `botIntents[]` | Skill 1 patch mode — an intent marked chained was registered; fix the role or membership. |
| Check 13 — no start point | Skill 1 patch mode (spec has no `entry` or `global` intents — set at least one role to `entry` or `global`) |
| Check 14 — catalog intent unresolved (advisory) | Skill 1 patch mode or manual fix — verify the §4.6 catalog `IntentId`; remove the reference or add the catalog definition |
| Check 15 — duplicate global by tool name (blocking) | Skill 1 patch mode — mark the legacy intent role=`chained` (keep it in `intents[]`, unregister from `botIntents[]`), leaving only the current intent as `global`; or remove the old intent from section 4 entirely |
| Check 16 — speech content in validationPrompt (blocking) | Skill 2 reactivation — rewrite as capture mapping (FP-5, style-guide patterns C1–C5); the script/question moves to `announcement` or an FP-4 quoted instruction line; a turn-taking guard moves to persona (Skill 1 patch) |
| Check 17 — RT=3 missing `intentLoadingAnnouncement` (blocking) | Skill 2 reactivation — author the FP-7 filler for the flagged intent(s) |
| Check 18 — foreign-parameter reference (blocking) | Skill 1 patch mode if the parameter should move to the flagged intent, OR Skill 2 reactivation to remove the reference (the outcome slot lives on its owning terminal per FP-8) — the error offers both paths |
| Check 19 — duplicate speak-obligation (blocking) | Skill 2 reactivation for intent-field duplicates; Skill 1 patch mode when one site is persona / opening instructions / openingAnnouncement. Keep the sentence in exactly one field. |
| Check 20 — terminal shape (blocking) | Skill 1 patch mode — per-outcome terminal restructure (add the outcome slot / remove the terminal-origin relation / merge the finalize→end_call chain); Skill 2 reactivation when only the validationPrompt's value-mode implementation is off |
| Check 21 — ParameterType mismatch (blocking) | Skill 3 internal bug — Skill 3 emits these from its own system dictionary; a mismatch means emission drift. Report, don't repair. |
| Check 22 — authored edge into a type-2 global (advisory) | Informational — recommend Skill 1 patch mode to drop the redundant relation; the global is reachable from anywhere by construction |
| Check 25 — PersonaID outside known whitelist (advisory) | Informational — banner note asking the operator to confirm the `Persona` row exists on the target account before import; not user-actionable during authoring until Skill 1 gets a persona-selection field |

Skill 3 does not invoke Skill 1 or Skill 2 itself. It reports the routing recommendation; the user invokes the appropriate skill.

---

## Filename convention

`bot-<bot-snake-name>-<YYYY-MM-DD>.json`

`<bot-snake-name>` is the spec section 1 `**Identifier:**` value (a snake_case ASCII identifier captured by Skill 1 at interview time). If the field is missing (legacy spec from before v1.0), Skill 3 falls back to ASCII-folding `**Bot Name:**`, then to `bot`. For Hebrew bot names, this fallback fails — which is why Skill 1 asks for an explicit identifier.

Companion banner file (Claude Code only): `bot-<bot-snake-name>-<YYYY-MM-DD>.banner.md`.

If the file already exists in the workspace, Skill 3 appends `-<counter>` before `.json`.

---

## Banner format

The banner is rendered **above** the JSON (single-conversation runtime) or as a sidecar file (Claude Code runtime). Plain text — never embedded in the JSON itself, so the user can copy the JSON code block directly.

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
#   - ActiveVersionInfo.AIModelConfig.daily_limit = 600, dailyLimitLayerId = 3, maxDurationLayerId = 3, IVRLayerSelect_2 = 3 (v1.13.0 golden-derived defaults — layer targets are account-specific; verify after import)
#   - IntentConfig.additional defaults applied (max_turns / sensitive / max_turns_sentence) on intents without spec overrides (v1.13.0)
#   - ActiveVersionInfo.AIModelConfig.recordAgentCalls = "false" (v1.5.0 default — see spec section 1)
#   - ActiveVersionInfo.PersonaID = 3 (shared TTSScriptReader persona, AccountId=0 — v1.18.0; verify this Persona row exists on the target account before import)
#   - [...]
#
# MANDATORY POST-IMPORT STEP (v1.16.0 — emitted whenever spec section 1 carries **Negative instructions:**):
#   - Negative instructions are NOT emitted to the JSON (wire field unverified) — after import, paste the
#     spec's Negative instructions text into the UI's AI Security Settings → Negative Instructions field:
#     "<spec section 1 Negative instructions text>"
```

Each section is always emitted, even if its content is "(none)" — consistent banner shape regardless of whether the spec was tidy. The "DEFAULTS APPLIED" section lists every value Skill 3 emitted that wasn't authored in the spec; this makes Skill 3's contributions auditable.

---

## Section 6 drift handling

After §4 assembly and before §6 cross-reference pass, Skill 3 regenerates spec sections 6.1–6.5 from sections 4-5 and compares to the spec's existing section 6. Subsection-by-subsection diff, normalized for whitespace and ordering.

**Drift handling: soft warning, not blocking.** Section 6 is derivative; sections 4-5 are authoritative. If the regenerated 6 differs, Skill 3 records the drift in the banner ("DRIFT NOTES") and the section 7.3 generation log, but does not auto-fix and does not block emission. If the user cares enough about the drift to fix it, they invoke Skill 1 patch mode (which regenerates section 6 cleanly).

---

## Output contract

**On success:**

- A single JSON object per Doc 1 §4 — pretty-printed with 2-space indent, UTF-8, keys in Doc 1 documentation order
- Valid JSON only — no comments, no trailing commas
- Banner emitted as plain text (single-conversation) or a sidecar file (Claude Code)
- Spec section 7.3 updated with: timestamp, sentinel count, drift count, cross-reference pass result — logged count-agnostically as `Cross-reference pass: <passed>/<total> passed` (v1.13.0 — fixes the stale hard-coded `14/14` literal)

**On failure:**

- No JSON emitted
- Spec section 7.3 updated with the failure log
- Closing message points to the appropriate skill or fix path

### Runtime-specific delivery

| Runtime | Output |
|---|---|
| **Single-conversation** | Banner rendered as plain text in the chat message; JSON in a fenced code block; closing message instructs how to copy and import |
| **Claude Code** | JSON written to `bot-<id>-<date>.json`; banner written to `bot-<id>-<date>.banner.md`; closing message references both files |

---

## Anti-list — what Skill 3 does NOT do

- Author any text content (Skills 1 and 2 only)
- Make creative decisions about RT-specific defaults the spec didn't specify
- Fill in plausible-looking values for unknowns (fail loud with sentinels instead)
- Smooth over template deviations (parse error and halt instead)
- Auto-fix cross-reference violations (route to Skill 1 / Skill 2 instead)
- Invoke other skills (recommends routing; the user invokes)
- Emit a partial JSON when assembly fails midway
- Emit JSON if any **blocking** cross-reference check fails (v1.13.0 wording — a partial JSON looks deployable and breaks at runtime; hard halt is the correct behavior)
- Emit `max_turns` / `max_turns_sentence` as direct siblings of `prompts` inside `IntentConfig` (the pre-v1.13 shape) — since v1.13.0 they live inside `IntentConfig.additional` together with `sensitive`
- Modify the spec beyond the section 7.3 generation log entry

---

## v1.5.0 changes

**ID placeholder ranges:** added `IntentRelatedID` (-2000+, unique row PK), `IntentConditionGroupID` (-3000+), `IntentSourceID` (-4000+). `BotIntentID` renamed to `BotIntentId` (lowercase `d`) per production casing.

**Top-level wrapper:** `intentList` moved to position #4 (right after `AccountID`). `ActiveVersionInfo` field order — `IsActive` is now first.

**Dual `AIModelConfig` — lean shapes:** the two `created` payloads now serve distinct roles. Top-level carries only `{ "model": "..." }`; version-level carries only `realtimeInputConfig` + voice `generationConfig`. Dropped from version-level: `tools`, `instructions`, `temperature`, `topP`, `topK`, `responseModalities`, `systemInstruction`, and all other generationConfig fields. Dropped from top-level: `Description`, `BaseUrl`, `Type`, `AIModelTypeId` (as separate field), full `created` payload.

**`intents[]` — 17-field shape:** restored intent-root `IsActive: 1` and intent-root `AccountId`. `IsSilenceIntent` is now integer 0/1 (was boolean). `IntentSources` shape expanded to `{ SourceID, SourceName, IntentSourceID }` (was `{ SourceID: 1 }` only). `max_turns` / `max_turns_sentence` added with RT-conditional defaults (RT=2 defaults to `max_turns: 15` — rationale preserved; **relocated into `IntentConfig.additional` in v1.13.0**, where non-RT=2 intents now default to `5` instead of omitting).

**`IntentParameters[]`:** audit fields added (`Schema: null`, `CreatedBy` from spec section 1, `ModifiedBy: " "` literal space, `CreatedDate`, `ModifiedDate`). `IsRequired` and `IsActive` are now integers. `OptionList` is `null` for non-ENUM (not `[]`). `DefaultValue` is `""` (not `null`); v1.16.0: populated from the spec slot-line's optional `DefaultValue` segment when present. Full nested `ParameterType` object with frozen constants (per-type dictionary values CORRECTED in v1.13.0 — see the `ParameterType` system dictionary section above; the v1.5.0 BOOLEAN/ENUM rows were extrapolated guesses).

**`botIntents[]`:** `BotId`/`IntentId` lowercase `d`. `DTMFList: []` always emitted. `BotVersionId: -2` added. `SortOrder` is 0-based. `ConditionGroupList` now populated by default with structural entry.

**`intentRelations[]`:** `IntentRelatedID` is now a unique row PK (was mirror of `NextIntentID`). `Order` is 0-based. `DTMFList: []` always emitted. `ConditionGroupList` populated by default.

**`intentCategories[]`:** `BotID` removed. `IsActive`, `AccountId`, `Description` added. `PriorityId` corrected from `2` to `1`.

**Global/system catalog intents (v1.11.0).** Spec section 4.6 declares predefined platform intents (e.g. silence-forward target id=19, `AccountId 0`) as verbatim JSON blocks. Skill 3 appends each to `intents[]` unchanged (real IDs preserved, bypassing the negative-placeholder allocator), merges its system category into `intentCategories[]` de-duped, resolves `silence_behaviour.intent` to its real `IntentId`, and — per the per-intent `Wiring:` flag — either leaves it free-floating (`silence-forward only`, the default, matching production exports) or wires it into `botIntents[]` as a type-2 global (`triggerable global`, reachable from anywhere with no per-intent edges).

**`silence_behaviour.intent` is never a negative placeholder (v1.11.1, empirically confirmed 2026-06-23).** The Voicenter import procedure remaps negative placeholder IDs inside `intents[]` / `botIntents[]` / `intentRelations[]` to real positive IDs, but it does **NOT** remap `silence_behaviour.intent`. A negative value therefore survives verbatim into the imported bot, points at no real intent, and the silence forward silently breaks (the UI shows the silence behaviour blank until set by hand). Skill 3 resolves the field, in priority order: **(1)** a section-4.6 catalog/global intent → its real positive `IntentId` (e.g. `19`) verbatim — the preferred, self-contained target; **(2)** a bot-own intent (placeholder-only pre-import) → **substitute the canonical system silence-forward global `19`** (`IsSilenceIntent` system intent, `AccountId 0`, category `22`; verbatim definition in `spec-skeleton.md` §4.6), inject intent `19` into `intents[]` + merge category `22`, and emit a banner line noting it can be re-pointed in the UI; **(3)** `-999` + banner only in the genuinely impossible case that id `19`'s definition is unavailable AND no real catalog target is declared. In normal operation the value is always a positive id (`19` when no real catalog target was chosen).

**`apiSilenceRelations[]`:** `Configuration` is now a full deep copy of the parent intent's `IntentResponces.Configuration` (not just the six silence fields). Check 6 validates full deep equality.

**RT=2 Configuration:** `apiResponseAnnouncement` renamed `announcement`. `function_output` changed from bare string to object `{ "default": "..." }`. `response_success` changed from bare string to object `{ "instructions": "..." }`. Capital-I `IntentLoadingAnnouncement` removed (lowercase form only).

**RT=3 Configuration:** `response_success` changed from bare string to object `{ "instructions": "..." }`.

**Cross-reference check 2:** `IntentRelatedID` is a unique row PK — no longer checked as a mirror of `NextIntentID`.

**Cross-reference check 6:** validates full Configuration deep equality (was 6 silence fields only).

**Cross-reference check 10:** inverted — now catches regressions *to* dropped fields rather than asserting the old fields present.

**Appendix A row 2:** casing-bug pair REMOVED. **Row 15:** intent-root `IsActive` + `AccountId` restored. **Extra row:** `response_success` object shape across RT=1 + RT=2 + RT=3.

**Appendix D.5:** `PriorityId: 1` (corrected from `2`). **Appendix D.7:** `IntentSources` now emits `{ SourceID, SourceName, IntentSourceID }`.

---

## v1.8.0 changes

**`**Bot-intent role:**` field in section 4.** Skill 3 parses this field (strict grammar; off-grammar value = parse error; absence = `chained`). Three values: `entry`, `global`, `chained`.

**`botIntents[]` — selective registry.** Prior versions emitted an entry for every intent. v1.8.0 changes `botIntents[]` to a **selective registry**: only `entry` (BotIntentTypeID 1) and `global` (BotIntentTypeID 2) intents are included. `chained` intents are omitted from `botIntents[]` entirely — they are reached only via `intentRelations[]`. `SortOrder` is 0-based over the emitted subset.

**No global fan-out in `intentRelations[]` (v1.12.0).** `intentRelations[]` carries authored transitions only. A `global` intent is reachable from anywhere via its `botIntents[]` type-2 registration, so Skill 3 does **not** generate per-intent edges from every non-global intent to each global (the v1.8.0 auto-fan-out was removed). An author who lists an explicit hand-off to a global keeps that authored edge; the `(origin, next)` deduplication still collapses duplicates.

**Section 6.2 regeneration.** Skill 3's section 6.2 regeneration pass emits authored transitions only (v1.12.0 — no fan-out), matching Skill 1's section 6.2, so no spurious drift is flagged between the authored spec and the assembled JSON.

**Cross-reference pass gained three botIntents-role checks.** Three blocking checks (11–13): check 11 verifies global intents have `BotIntentTypeID = 2`; check 12 verifies no chained intents appear in `botIntents[]`; check 13 verifies at least one start point exists. (Check 14, a non-blocking advisory for catalog-intent resolution, was added in v1.11.0. The v1.8.0 fan-out-completeness check was removed in v1.12.0 when global fan-out was dropped. Check 15 — duplicate-global-intent — was added in v1.12.0; checks 16–22 — field-placement doctrine — in v1.13.0; check 23 — off-topic global — in v1.14.0; check 24 — turn-yield announcement gating — in v1.17.0; and check 25 — persona-FK sanity — in v1.18.0, bringing the pass to twenty-five checks.)

**`BotIntentId` placeholder allocation.** The `-100` series now allocates only to the emitted subset (entry + global intents). Chained intents get an `IntentId` but no `BotIntentId`.

---

## v1.13.0 changes

Derived from a production root-cause analysis against the golden export `בוט שיקוף – קבוצת קלי v0.0.17` and codified in the new shared reference `plugins/voicenter-bot-builder/references/field-placement-doctrine.md` (rules FP-1…FP-13), which is now a required-reading row in Skill 3's §1 table. Skill 3 owns the doctrine's verification layer: cross-reference checks 16–22.

**Parser grammar extensions (§3.1/§3.3):**

- Section-1 optional limit fields: `**Daily limit:**`, `**Daily limit layer:**`, `**Max duration layer:**`, `**Daily limit sentence:**`, `**Max duration sentence:**`, `**IVRLayerSelect_2:**` — all optional, defaulting to 600 / 3 / 3 / production sentences / 3; non-integer where an int is expected is a parse error.
- Section-4 optional fields: `**Captures answer to:**` / `**Asks next:**` (staggering, FP-2), `**Terminal outcome:** <slot_name> = <value-part>` (two-mode grammar: quoted value ⇒ fixed, unquoted ⇒ captured/dynamic; missing `<slot_name> =` is a parse error), and `**Sensitive:** true|false` (absence = `false`).
- New optional §4.5.5 header `### 4.5.5 CustomData keys (per-call payload)` under §4.5.
- Two new deviation-table rows (terminal-outcome missing slot assignment; sensitive value off-grammar).

**Version-level `AIModelConfig` (§4.2.3):** new golden-export fields `daily_limit` (600), `dailyLimitLayerId` (3), `maxDurationLayerId` (3), `daily_limit_sentence`, `max_duration_sentence`, `IVRLayerSelect_2` (3) — siblings of `max_duration`, NOT inside `created`. Golden-derived defaults are banner-listed under DEFAULTS APPLIED (layer targets are account-specific — verify after import).

**`IntentConfig` (§4.3.1):** row 8 is now `{ prompts: { llmDescription: "" (unchanged), validationPrompt }, additional: { max_turns, sensitive, max_turns_sentence } }`. The old sibling `max_turns` emission block is replaced by the `IntentConfig.additional` rules — RT=2 default 15 preserved, other RTs default 5, `sensitive` false, sentence `""` or the RT=2 Hebrew default (`"אני חייב לסיים את השיחה בשלב הזה."`). Never emit the pre-v1.13 sibling shape.

**`ParameterType` dictionary (§4.3.2):** CORRECTED — captured verbatim from the golden export (STRING 1: null/1/"Basic text input"; INTEGER 4: `"^[0-9]+$"`/1/"Whole number input"; BOOLEAN 16: `"^(true|false|yes|no)$"`/0/"Yes/No input"; ENUM 19: null/0/"Selection from predefined options"; JSON 20: null/0/"json schema", CreatedDate 2025-04-10 09:50:42). PHONE (10) unverified → emit the old values + a banner line. System dictionary rows are never re-authored; check 21 byte-matches.

**`IntentResponces` outer shape (§4.4):** now FOUR keys in golden order — `IsActive`, `Configuration`, `ResponseTypeId`, `SuccessCondition` (`""` on bot-own intents; catalog blocks keep `null`). RT=3 gains `Configuration.intentLoadingAnnouncement` (always emitted; key order: announcement, response_success, intentInstructions, intentLoadingAnnouncement). RT=1 note: terminal doctrine (FP-8) validated by check 20.

**Cross-reference pass (§6):** seven new field-placement checks 16–22 — 16 validationPrompt speech-free, 17 RT=3 loading announcement, 18 own-parameter references, 19 duplicate speak-obligation, 20 terminal shape, 21 ParameterType byte-match, 22 authored edges into type-2 globals (advisory) — see the checks table for detection heuristics. Check 7's allowlist extended with §4.5.5 CustomData keys plus the "never invented" failure message. New run order: 1–7 → 11–13 → 15 → 16–22 → 8 → 9 → 10 → 14.

**Bookkeeping:** §6.3/Appendix B routing rows for checks 16–22; §6.4 failure-report wording is count-agnostic; the §7.5 success log line is now `Cross-reference pass: <passed>/<total> passed` (fixing the stale `14/14`); the stale "The fourteen checks" heading renamed; Appendix A gains quirk rows 20–23 (`IntentConfig.additional`; `SuccessCondition: ""`; version-level limit/layer fields; RT=3 loading announcement); anti-list additions (never emit `max_turns` as a sibling of `prompts`; never emit JSON when a blocking check fails); banner DEFAULTS APPLIED gains the daily-limit/layer and `IntentConfig.additional` lines.

---

## voice-agent-llm v1.0.3+ runtime notes

**Empty `announcement` is runtime-tolerant.** RT=2 `announcement` may be empty at runtime — the voice-agent service substitutes `[START THE CONVERSATION]` as an LLM instruction (bot opens from persona; the literal string is **not** spoken aloud). Skill 3 emits whatever the spec contains verbatim. No new validation rule — Skill 2's Check 10 still requires authored text upstream.

---

## Common pitfalls

- **Spec has `[detailed-revisit]` intents.** Skill 3 refuses at Gate A. Run Skill 2 to redetail them.
- **Hand-edited spec breaks the strict template.** Skill 3 refuses at Gate B with a one-line fix hint. Either fix manually or run Skill 1 patch mode.
- **Filename produces `bot-bot-<date>.json`.** The spec is missing `**Identifier:**` (legacy spec from before v1.0). Run Skill 1 patch mode to add the field.
- **Cross-reference Check 7 fails on a typo.** Re-run Skill 2 for the affected intent, fix the Mustache reference, re-invoke Skill 3.
- **Cross-reference Check 1/2/3 fails on a deleted intent.** Spec was edited inconsistently — run Skill 1 patch mode to clean up the references.
- **Banner says `<USER_TO_FILL: bot description>` and similar.** Expected — the spec marked these as `<UNKNOWN: ...>`. Replace before importing to the platform.
- **Cross-reference Check 13 fires — no start point.** All section-4 intents are `chained`. Run Skill 1 patch mode to assign `entry` or `global` to at least one intent.
- **Cross-reference Check 12 fires — chained intent in `botIntents[]`.** Skill 1 patch mode — a chained intent was wrongly registered; fix the role or membership in the spec and re-run Skill 3.
- **`**Bot-intent role:** start` causes Gate B failure.** Only `entry`, `global`, and `chained` are valid. Run Skill 1 patch mode to correct the role value.

---

## Compass doctrine integration

The bot-builder plugin includes a shared doctrine reference at `plugins/voicenter-bot-builder/references/voice-prompt-doctrine.md`. Skill 3 owns three new cross-reference checks plus a banner extension:

- **Check 8 — Assembled-prompt token budget (Compass rule 1).** Advisory at 1,500–4,999 tok; blocking at ≥ 5,000 tok (forced decomposition at ≥ 6,000 tok). The block threshold is deliberately set above the Compass-measured degradation point (~2,500 tok) — the advisory band still surfaces that degradation, but the pipeline only halts at 5,000 to give authors working room. Estimated via a char-based method (Latin at 1/4 tok per char, Hebrew/Arabic/CJK at 1/1.5). Excludes `prompts.openingAnnouncement` (platform-rendered). Gated on `AiModelConfig.created.model = "models/gemini-3.1-flash-live-preview"`.
- **Check 9 — Session-resumption ceiling (Compass rule 2).** Advisory. Fires only when the spec declares cross-session continuity is required. Warns if the assembled prompt exceeds 200 tok.
- **Check 10 — Model-config doctrine (Compass rule 12 — v1.5.0 inversion).** Blocking. Validates that the version-level `AIModelConfig.created` does NOT contain any dropped field (`temperature`, `topP`, `topK`, `responseModalities`, `proactivity`, `thinkingConfig`, `systemInstruction`, `tools`, `affectiveDialog`, `proactiveAudio`). The lean payload has none of these by construction; the check catches future regressions.
- **DOCTRINE SENTINELS banner section (Compass rule 13).** Auto-applied at emission. One banner line per Compass advisory (rules 3, 4, 5, 6, 7, 9, 10) that fired during authoring and was not resolved.

Cross-references 1–7 (per Doc 1 §15.4), 11–13, 15, and 16–21 are blocking; checks 8–10 are gated on Gemini 3.1 (`AIModelConfigID=139` or `142`) and skip silently with a one-time section 7.3 log entry for other models; 14 and 22 are non-blocking advisory.

Anti-list addition: Skill 3 **does not auto-trim prompt text** to satisfy the token budget. Above 5,000 tok, assembly halts and routes to Skill 1 / Skill 2 patch.

---

## Field-placement doctrine integration (v1.13.0)

The plugin adds a second shared doctrine reference at `plugins/voicenter-bot-builder/references/field-placement-doctrine.md` (rules FP-1…FP-13), sourced from a production root-cause analysis against a hand-built golden bot. One-line doctrine: *announcement says it, validationPrompt captures it, intentInstructions routes it, intentLoadingAnnouncement covers the wait, persona rules it — each fact exactly once, in exactly one layer.* The file is a required-reading row in Skill 3's §1 table.

Rule ownership: Skill 1 owns FP-2 (structural staggering), FP-8, FP-9, FP-11 (interview), FP-12, and the persona half of FP-6. Skill 2 owns FP-3, FP-4, FP-5, FP-7, and the per-intent half of FP-6. **Skill 3 verifies** — cross-reference checks 16–22 (see the checks table above for the detection heuristics): 16 (FP-5, validationPrompt speech-free), 17 (FP-7, RT=3 loading announcement), 18 (FP-8, own-parameter references), 19 (FP-6, duplicate speak-obligation), 20 (FP-8, terminal shape), 21 (ParameterType dictionary byte-match), 22 (FP-9, authored edges into type-2 globals — advisory). FP-11 (CustomData keys are never invented) rides on check 7's extended §4.5.5 allowlist.

---

## `ImportBotFromJSON` contract integration (v1.18.0)

The plugin adds a third shared reference at `plugins/voicenter-bot-builder/references/voicebot-json-contract.md` — the `ImportBotFromJSON` stored procedure's hard rules (R1–R12), from a 2026-08-10 schema/FK snapshot handed to the pipeline for compliance review. Skill 3's existing emission already satisfied R1–R6, R8–R10, and R12 by construction (always-array `ConditionGroupList`/`DTMFList`, the `IntentResponces` typo, globally-unique placeholder ids, the `AiModelConfig.AccountId` reuse switch, and the NOT-NULL constants already emitted per Doc 1 §16/§9.0). Reviewing R7 and R11 against the skill surfaced two real gaps, both fixed in v1.18.0:

- **`ActiveVersionInfo.PersonaID` (R7) — previously unemitted.** `BotVersion.PersonaID` is a `bigint NOT NULL` FK with no fail-loud path in the stored procedure (a missing value silently falls back to the account's first `Persona` row, which can be absent on a given target server — the exact "Bot with intents but no BotVersion" failure class this whole contract exists to prevent). Skill 3 now always emits the known shared value `3` (`TTSScriptReader`) — see §4.2.2, Appendix D.12, and cross-reference check 25 (advisory — trivial today, future-proofed for a later persona-selection feature).
- **Appendix D.11 `AIModelConfigID` whitelist gap (R11) — flagged, not fixed.** The contract's live FK snapshot lists three additional shared ids (303, 312, 321) beyond the nine already catalogued. Their names/types haven't been captured into `model-catalog.md`, so Skill 3 does not fabricate entries for them — Appendix D.11 now carries a "Known gap" note instead.

One rule (R5's `IntentResponces.Configuration.IntentSelect_1`/`IntentSelect_4` cross-reference) does not apply — Skill 3 never emits an `IntentSelect_*` field in any RT's `Configuration` shape, so there is nothing to check.

---

## Related skills

- [voicenter-bot-spec-designer](../voicenter-bot-spec-designer/README.md) — Skill 1; produces the structural skeleton Skill 3 reads.
- [voicenter-bot-intent-detail-author](../voicenter-bot-intent-detail-author/README.md) — Skill 2; fills the language Skill 3 emits verbatim.
