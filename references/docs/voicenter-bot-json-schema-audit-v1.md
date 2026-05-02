# Voicenter Bot JSON — Schema Audit (v1)

**Status:** v1 — Wire-format reference for the Voicenter platform's Bot JSON.
**Audience:** anyone implementing or consuming the Bot JSON contract — Step 8 (Assembly) of the full Agent Generator, the three Claude skills (Flow Designer, Intent Detail Builder, JSON Assembler), and any future MCP integration.
**Sources:** two production exports (`Yuval.json`, `Refua0_30.json`) + internal training doc *Voicenter Voice Bot Configuration Guide v1.0* (January 2026).

---

## Table of Contents

1. Purpose, Sources, Methodology
2. The Two-Layer Model: Runtime Prompt Assembly vs. Wire Format
3. System Prompt Assembly Order & Dynamic Mutation
4. Bot Top-Level Wrapper
5. `ActiveVersionInfo` Envelope
6. The Two `AIModelConfig` Objects
7. Crosswalk: Training-Doc Names → JSON Paths
8. `intentList` — The Six Parallel Collections
9. The Intent Definition (`intents[]` Entry)
10. `IntentParameters` — Slot Definitions
11. `ResponseTypeId` Reference — The Four Behavior Primitives
12. `ParameterTypeId` Catalog (v1)
13. Mustache Templating & Call Context Variables
14. Worked Examples (Hierarchy + Recipe + Anti-pattern Lenses)
15. ID Semantics & Cross-References
16. Schema Quirks Summary
17. v2 Roadmap — Schema Gaps
18. Lifecycle Roadmap — v1 → v5

---

## 1. Purpose, Sources, Methodology

This document is the canonical wire-format reference for the JSON configuration that the Voicenter platform accepts as a deployable voice/chat agent. It exists to serve as the contract for the Agent Generator's Step 8 (Assembly) — the mechanical step that converts internal designs into platform-deployable configs — and as the reference any downstream skill (Flow Designer, Intent Detail Builder, JSON Assembler) must satisfy.

**Sources of truth:**

- **Two production exports** — `Yuval.json` (יובל — installation scheduling, NC, Hebrew, Gemini Live) and `Refua0_30.json` (חברים לרפואה — pharmacy pickup-point finder, Hebrew, Gemini Live). Both are voice-driven agents with 6 intents each, currently active on the platform.
- **Training doc** — *Voicenter Voice Bot Configuration Guide v1.0* (January 2026), the internal training department's conceptual model of how the runtime system prompt is assembled.

**Notation used throughout this document:**

- `[CONFIRMED]` — observed in both production samples and consistent
- `[INFERRED]` — observed once, or behavior derived from naming/context
- `[v2]` — capability that exists in the schema but not specified in v1; deferred to a future iteration
- `[OPEN]` — schema element observed but inner shape not derivable from sources; flagged for future investigation
- `[QUIRK]` — known typos, casing inconsistencies, or deprecated fields that must be preserved as-is

**Scope of v1:**

- Bot-level: prompts bundle, voice config, caller-silence behavior
- All four `ResponseTypeId` primitives (1, 2, 3, 4)
- Four observed `ParameterTypeId` values (STRING=1, PHONE=10, BOOLEAN=16, ENUM=19)
- Mustache templating with the four call-context variable categories
- API-silence handling (per-intent + registry)
- The 16-field intent skeleton
- Empty `IntentConditionList[]` everywhere — i.e. all intents are always-eligible at runtime

**Out of scope for v1 (captured in §17 — v2 Roadmap):**

- `IntentCondition` entry inner schema (runtime gating)
- `silenceRelations[]` schema (caller-silence at intent level)
- Full `ParameterTypeId` catalog beyond the 4 we observed
- `llmDescription` empty-fallback behavior
- Parameter-level natural-language validation script storage
- `HandlingInstructions`, `SystemPrompt` (deprecated/empty in samples)

**Out of scope entirely for the v1 schema (Voicenter platform concerns, not document concerns):**

- IVR layer IDs (`layer`, `NEXT_VO_ID`) — environment-specific routing values
- Webhook URLs (`connector.center` artifacts) — must be supplied by user at generation time
- Numeric DB-issued IDs (`IntentId`, `BotID`, `ParameterId`, etc.) — generation uses placeholders, the platform assigns real IDs at import time

---

## 2. The Two-Layer Model: Runtime Prompt Assembly vs. Wire Format

The Voicenter agent system has **two distinct layers** that this document bridges. Confusing them is the most common reason generated configs misbehave.

### Layer A — Runtime Prompt Assembly (the training doc layer)

What actually executes when a caller dials in. The platform takes pieces from the JSON config and concatenates them in a specific order to form the active system prompt for the LLM (Gemini Live in current production). This assembled prompt **mutates** as the conversation progresses (see §3).

This is the conceptual layer the training doc describes. It's what bot designers think about when they write personas and intent instructions.

### Layer B — Wire Format (the JSON file layer)

The static, shippable artifact that gets imported into the platform. A nested JSON object with the field names, types, IDs, and structural relationships described in this document.

This is what Step 8 (Assembly) outputs and what the platform's import endpoint accepts.

### Why both layers matter

A field like `prompts.intentInstructions` at the bot level is, in Layer A, called "Opening Instructions" and serves as the active instructional content **only before any intent has been recognized**. Once an intent fires, that field is replaced in the assembled prompt by the per-intent `IntentResponces.Configuration.intentInstructions`.

A skill that designs the bot must understand both: it writes Layer B fields, but the *quality* of those fields is judged by how they perform in Layer A's dynamic assembly.

The training-doc names and JSON paths don't always match. §7 provides the full crosswalk.

---

## 3. System Prompt Assembly Order & Dynamic Mutation

Per the training doc, the runtime system prompt is built from five components in a fixed order. The order is identical for voice and chat channels — only the position-2 component differs by channel.

### Pre-intent state (caller has just connected, no intent recognized yet)

```
1. Global Instructions       ← prompts.persona
2. Voice OR Chat Instructions ← prompts.voiceInstructions  OR  prompts.chatInstructions
3. Opening Instructions      ← prompts.intentInstructions  (the BOT-level one, not per-intent)
4. Tools List                ← all intents in botIntents[], filtered by ConditionGroupList eligibility
5. Security Prompt           ← platform-managed, not in JSON, immutable
```

The opening announcement (`prompts.openingAnnouncement`) is spoken to the caller as the first audible message but is **not part of the assembled system prompt** — it's a separate runtime asset.

### Post-intent state (an intent has been recognized and executed)

```
1. Global Instructions       ← unchanged
2. Voice OR Chat Instructions ← unchanged
3. Intent Instructions       ← REPLACES position 3 from the pre-intent state
                             ← sourced from the executed intent's
                                IntentResponces.Configuration.intentInstructions
4. Related Intents           ← REPLACES position 4 from the pre-intent state
                             ← sourced from intentRelations[] filtered by
                                OriginIntentID == executed_intent_id, then
                                further filtered by ConditionGroupList eligibility
5. Security Prompt           ← unchanged, immutable
```

### What this means structurally

`botIntents[]` is **the initial Tools List**. Every intent registered as a tool on this bot lives there.

`intentRelations[]` is **the Related Intents per origin** — once intent A executes, the union of `intentRelations[]` rows where `OriginIntentID == A` defines the intent menu the LLM may transition to next.

The Security Prompt is **never in the JSON**. The platform appends it. Designers cannot override it. Treat it as a black box for our purposes.

Channel selection (voice vs. chat) happens at the platform level based on how the call was initiated. The same Bot JSON serves both channels; only one of `voiceInstructions` or `chatInstructions` is included in any given assembly.

---

## 4. Bot Top-Level Wrapper

Eleven fields, observed in both samples. This is the outermost JSON object.

| Field | Type | Required | Notes |
|---|---|---|---|
| `Name` | string | yes | Human-readable bot name. Hebrew in samples. Used for display in the bot list UI. |
| `BotID` | int | yes | Platform-assigned. Generation uses placeholder; platform assigns on import. |
| `AccountID` | int | yes | Customer account ID the bot belongs to. Must be supplied at generation time. |
| `Description` | string | yes | Free text. Often duplicates `Name` in samples. |
| `BotStatusId` | int | yes | Observed value: `1` only. `[INFERRED]` enum, full set unknown. |
| `BotLanguages` | array | yes | Observed: empty `[]` in both. `[OPEN]` — schema not derivable from samples. |
| `CreatedDate` | string | yes | ISO-style timestamp `"YYYY-MM-DD HH:MM:SS"`. |
| `ModifiedDate` | string\|null | yes | Same format as CreatedDate, or `null`. |
| `AiModelConfig` | object | yes | The model **catalog reference** — which configured model this bot uses. See §6.A. **Not the same as** `ActiveVersionInfo.AIModelConfig`, despite similar naming. `[QUIRK]` |
| `ActiveVersionInfo` | object | yes | The current version of the bot — its prompts, voice, intents. See §5. |
| `intentList` | object | yes | The six parallel collections that define the bot's intent graph. See §8. |

**Notes:**

- The double `AiModelConfig` (top-level) vs. `AIModelConfig` (inside `ActiveVersionInfo`) is the single most confusing structural element. Top-level is *which model is registered*; inside-version is *the actual prompts/voice/silence config for this version*. They serve different purposes.
- A bot can in principle have multiple versions, but the JSON export only ships the active one (`ActiveVersionInfo`). v1 generation produces a single version.

---

## 5. `ActiveVersionInfo` Envelope

The version envelope. Ten fields, observed in both samples.

| Field | Type | Required | Notes |
|---|---|---|---|
| `BotVersionId` | int | yes | Platform-assigned. Placeholder at generation. |
| `VersionNumber` | string | yes | Semantic-style: `"0.0.30"`, `"0.0.1"`, etc. v1 generates `"0.0.1"`. |
| `BotVersionStatusId` | int | yes | Observed value: `3` only. `[INFERRED]` likely "active" or "published". Full enum unknown. |
| `IsActive` | int | yes | `0` or `1`. v1 generates `1`. |
| `Description` | string | yes | Free text, often empty `""` in samples. |
| `CreatedDate` | string | yes | ISO-style timestamp. |
| `ModifiedDate` | string\|null | yes | Same format or `null`. |
| `SystemPrompt` | string | yes | **Empty `""` in both samples.** `[QUIRK]` Appears to be a deprecated/legacy field replaced by the `AIModelConfig.prompts` bundle. v1 always emits `""`. |
| `AIModelConfigId` | int | yes | Foreign key to the model config record. Mirrors `AiModelConfig.AIModelConfigID` at top level. |
| `AIModelConfig` | object | yes | The actual runtime config for this version: prompts, voice, silence. See §6.B. |

**Critical:** `SystemPrompt` at this level is **not** the active system prompt. The active system prompt is dynamically assembled per §3 from `AIModelConfig.prompts` plus the active intent's `IntentResponces.Configuration`. Filling `SystemPrompt` with content has unknown effect — it's empty in both production samples.

---

## 6. The Two `AIModelConfig` Objects

There are two distinct objects with confusingly similar names. They serve different purposes. Treat them as unrelated.

### 6.A — Top-level `AiModelConfig` (Model Catalog Reference)

Path: `<root>.AiModelConfig`

This is the platform's model registry entry — *which configured model this bot uses*. It's metadata, not behavior.

| Field | Type | Notes |
|---|---|---|
| `AIModelConfigID` | int | Foreign key. Links the bot to the model config record. |
| `Name` | string | Display name of the model config (e.g., `"Gemini Live"`). |
| `Description` | string\|null | Free text. |
| `BaseUrl` | string\|null | Provider endpoint (often null — managed by platform). |
| `AIModelTypeId` | int | The model family/type ID. |
| `Type` | object | `{ AIModelTypeId, Name, Description }` — names the model type (e.g., Gemini Live). |
| `created` | object | The literal JSON config payload sent to the LLM API. **Mirrored** in `ActiveVersionInfo.AIModelConfig.created` — same shape, same content. |

The `created` object inside this top-level reference is **identical to the one inside `ActiveVersionInfo.AIModelConfig`**. It's duplicated. Why duplicated is unclear from the samples — possibly historical, possibly intentional for catalog display. v1 generation: emit them identically.

### 6.B — `ActiveVersionInfo.AIModelConfig` (Runtime Behavior Config)

Path: `<root>.ActiveVersionInfo.AIModelConfig`

This is the **actual runtime config** for this version of the bot. Five top-level keys:

```
ActiveVersionInfo.AIModelConfig
├── prompts                  ← the persona bundle (§6.B.1) — the heart of the bot's behavior
├── created                  ← the raw LLM API payload (§6.B.2) — voice, generation params
├── silence_behaviour        ← caller-silence handler (§6.B.3) — bot-level
├── tools                    ← observed empty [] in both samples — [v2]
└── instructions             ← observed empty "" in both samples — [v2]
```

#### 6.B.1 — `prompts` (The Persona Bundle)

Five string fields. This is where **the entire bot personality and operating instructions** are stored. Maps to the training-doc Layer A names per §7.

| JSON field | Training-doc name | Layer A position |
|---|---|---|
| `prompts.persona` | Global Instructions | Always position 1 |
| `prompts.voiceInstructions` | Voice Instructions | Position 2 (voice channel) |
| `prompts.chatInstructions` | Chat Instructions | Position 2 (chat channel) |
| `prompts.intentInstructions` | Opening Instructions | Position 3 (pre-intent only) |
| `prompts.openingAnnouncement` | Opening Announcement | Spoken first, not in system prompt |

All five are **strings** (often long, often Hebrew). Mustache variables (`{{caller_name}}`, `{{TimeNow}}`) are allowed and resolved at runtime.

**`prompts.intentInstructions` is the single field most likely to be misused.** It's *not* per-intent. It's the bot's "what to do when no intent has been recognized yet" instructions — i.e., the orienting / disambiguation behavior at the start of a call. Per-intent instructions live inside each intent's `IntentResponces.Configuration.intentInstructions` (§9).

#### 6.B.2 — `created` (Raw LLM API Payload)

The literal config sent to the model provider's API (Gemini Live in current samples). Shape mirrors the Gemini Live setup payload:

```
created
├── model                                      "models/gemini-2.5-flash-preview-native-audio-dialog"
├── generationConfig
│   ├── temperature                            (number, e.g. 1.5)
│   ├── topP                                   (number, e.g. 0.95)
│   ├── topK                                   (int, e.g. 64)
│   ├── responseModalities                     ["AUDIO"]
│   ├── speechConfig
│   │   ├── languageCode                       "he-IL", etc.
│   │   └── voiceConfig.prebuiltVoiceConfig.voiceName    "Puck", "Orus", etc.
│   ├── proactivity                            (object) — provider-specific
│   ├── thinkingConfig                         (object) — provider-specific
│   └── (other provider-specific fields)
├── systemInstruction                          (object) — provider format wrapper
├── tools                                      (array)
└── (other provider fields)
```

**v1 generation strategy:** treat the `created` object as a **template**. Carry forward the production model and generation params from a known-good baseline; substitute language code and voice name based on user input during the interview. Do not generate `created` from scratch — too many provider-specific fields to get right blind.

**Voice options observed:** `"Puck"` (Yuval), `"Orus"` (Refua). Full Gemini Live voice catalog is provider-managed; v1 supports the observed two plus accepts any string the user supplies.

**Language codes observed:** `"he-IL"` only. v1 supports any BCP-47 language code; the user supplies it during the interview.

#### 6.B.3 — `silence_behaviour` (Bot-Level Caller Silence)

When the **caller** (not the API) goes silent, what does the bot say? Observed only in Yuval; absent in Refua, suggesting it's optional.

| Field | Type | Notes |
|---|---|---|
| `silence_duration` | int | Seconds of caller silence before the bot interjects. |
| `silence_loops` | int | Max number of times the bot will interject before ending the call. |
| `silence_sentence` | string | What the bot says on each interjection (Mustache supported). |
| `silence_ending_sentence` | string | What the bot says after `silence_loops` is exhausted. |

This is **bot-level** — same behavior regardless of which intent is active. The `silenceRelations[]` collection (§8.5) appears to allow per-intent overrides but is empty in both samples → `[v2]`.

---

## 7. Crosswalk: Training-Doc Names → JSON Paths

The training doc and the JSON use different names for the same concepts. This table is the canonical mapping.

| Training-doc name | JSON path | Layer |
|---|---|---|
| Global Instructions | `ActiveVersionInfo.AIModelConfig.prompts.persona` | Bot |
| Voice Instructions | `ActiveVersionInfo.AIModelConfig.prompts.voiceInstructions` | Bot |
| Chat Instructions | `ActiveVersionInfo.AIModelConfig.prompts.chatInstructions` | Bot |
| Opening Instructions | `ActiveVersionInfo.AIModelConfig.prompts.intentInstructions` | Bot |
| Opening Announcement | `ActiveVersionInfo.AIModelConfig.prompts.openingAnnouncement` | Bot |
| Security Prompt | (not in JSON — platform-managed, immutable) | Bot |
| Intent Name | `intentList.intents[].Name` | Intent |
| Intent Description | `intentList.intents[].Description` | Intent |
| Tool Description | `intentList.intents[].IntentConfig.prompts.llmDescription` | Intent |
| Parameters Collection | `intentList.intents[].IntentParameters[]` | Intent |
| Validation Script (intent-level) | `intentList.intents[].IntentConfig.prompts.validationPrompt` | Intent |
| Intent Instructions (post-execution) | `intentList.intents[].IntentResponces.Configuration.intentInstructions` | Intent |
| Intent Announcement (post-execution) | `intentList.intents[].IntentResponces.Configuration.announcement` (RT=3) or `apiResponseAnnouncement` (RT=2) | Intent |
| Related Intents | `intentList.intentRelations[]` filtered by `OriginIntentID` | Bot |
| Parameter Name | `intentList.intents[].IntentParameters[].Name` | Parameter |
| Parameter Type | `intentList.intents[].IntentParameters[].ParameterTypeId` | Parameter |
| Validations (schema) | `intentList.intents[].IntentParameters[].ValidationRules` (observed always `{}`) | Parameter `[v2]` |
| Validation Script (parameter-level) | `[OPEN]` — see §17 | Parameter `[v2]` |
| Regex | `intentList.intents[].IntentParameters[].ValidationPattern` (observed always `null`) | Parameter `[v2]` |

**Three things from the training doc that have no clear JSON home in v1:**

1. **Tool Description** is documented as "optional override of Intent Description for the tools list." JSON has `IntentConfig.prompts.llmDescription` which fits the role, but it's empty in all 12 observed intents. Fallback semantics → `[OPEN]` (§17).
2. **Parameter-level Validation Script** — training doc lists it as a parameter field for natural-language validation logic. JSON has no field that's clearly this. The intent-level `validationPrompt` covers all parameters together → `[OPEN]` (§17).
3. **Validations (schema keywords)** — training doc maps these to JSON Schema keywords (`required`, `enum`, `minimum`, etc.). JSON has `ValidationRules: {}` (always empty in samples) — likely the intended home but inner shape unobserved → `[v2]`. Currently `IsRequired` (boolean) and `OptionList` (for ENUM) carry this load.

---

## 8. `intentList` — The Six Parallel Collections

`intentList` is the brain. Six arrays, each playing a specific role. They're not nested — they're parallel, wired together by integer IDs.

```
intentList
├── intents[]              ← the intent definitions (§9)
├── botIntents[]           ← which intents are registered as tools on this bot (§8.2)
├── intentRelations[]      ← the transition graph (§8.3)
├── intentCategories[]     ← taxonomy (§8.4)
├── silenceRelations[]     ← per-intent caller-silence handlers (§8.5)
└── apiSilenceRelations[]  ← per-intent API-silence handlers (§8.6)
```

The relationships are by ID:

```
intents[].IntentId  ←──────────  botIntents[].IntentID
                  ←──────────  intentRelations[].OriginIntentID
                  ←──────────  intentRelations[].NextIntentID
                  ←──────────  intentRelations[].IntentRelatedID
                  ←──────────  apiSilenceRelations[].OriginIntentID
                  ←──────────  apiSilenceRelations[].ApiSilenceIntentID

intents[].IntentCategoryId  ←──  intentCategories[].IntentCategoryId
```

A skill that builds this must keep ID consistency end to end. v1 strategy: use string placeholders during design (`"intent:collect_address"`), assign integer IDs only at the Assembler step, propagate consistently.

### 8.1 `intents[]` — see §9 (the largest section)

### 8.2 `botIntents[]` — Bot-Level Intent Registry

Which intents are registered as tools on this bot. Every intent in `intents[]` should have a corresponding entry here for v1 (since v1 doesn't gate availability via conditions).

```
botIntents[] entry:
├── BotIntentID                      int     platform-assigned, placeholder
├── BotID                            int     references the parent bot
├── IntentID                         int     references intents[].IntentId
├── BotIntentTypeID                  int     observed value: 1 (only one seen across both bots)
└── ConditionGroupList               array   v1: empty []  →  [v2]: gates availability
```

`BotIntentTypeID = 1` is the only value observed. `[INFERRED]` likely means "primary intent" — full enum unknown. v1 always emits `1`.

`ConditionGroupList` v1 behavior: emit empty array `[]`. Schema element observed when present has shape:

```
ConditionGroupList[] entry:
├── IntentConditionGroupId           int
├── IntentConditionGroupType         int     observed: 1
├── IntentConditionGroupTypeName     string  observed: "AND"
├── IntentConditionRelationType      int     observed: 1
├── IntentConditionRelationTypeName  string  observed: "AND"
└── IntentConditionList              array   v1: always [] — [v2] full schema
```

### 8.3 `intentRelations[]` — Transition Graph

The post-intent menu. After intent A executes, the LLM picks its next intent from the union of `intentRelations[]` rows where `OriginIntentID == A`, eligibility-gated by `ConditionGroupList` (always-eligible in v1).

```
intentRelations[] entry:
├── OriginIntentID         int     the intent we just finished
├── NextIntentID           int     the eligible next intent (one row per option)
├── IntentRelatedID        int     placeholder/junction ID, often duplicates NextIntentID
├── Order                  int     display/priority order in the menu
└── ConditionGroupList     array   v1: empty []  →  [v2]: gates the transition
```

A "terminal" intent (the call should end after it) has **zero rows** with that intent as `OriginIntentID`. The LLM then has no related intents — the platform handles call termination.

A "fan-out" intent (multiple possible nexts) has multiple rows with the same `OriginIntentID` and different `NextIntentID`s.

**Critical for v1:** transitions are **guidance, not enforcement**. The LLM chooses among the eligible options based on the natural-language `intentInstructions` of the origin intent and the conversation state. The graph defines *the menu*, not *the path*.

### 8.4 `intentCategories[]` — Taxonomy

```
intentCategories[] entry:
├── IntentCategoryId       int     placeholder, then platform-assigned
├── BotID                  int
└── Name                   string  observed: "Default Category" in both samples
```

Both samples have a single default category, with all intents in it. v1 generates one default category per bot, attaches all intents to it. Multi-category bots → `[v2]`.

### 8.5 `silenceRelations[]` — Per-Intent Caller Silence

Empty `[]` in both samples. `[v2]`. See §17.

Inferred role from naming: per-intent override of the bot-level `silence_behaviour` (§6.B.3). v1 emits `[]`; bot-level applies uniformly.

### 8.6 `apiSilenceRelations[]` — Per-Intent API-Silence Registry

Registers the relationship between an origin intent (typically RT=2 = API call) and the fallback intent invoked when the API takes too long.

```
apiSilenceRelations[] entry:
├── OriginIntentID          int     the API-calling intent
├── ApiSilenceIntentID      int     the intent to jump to after exhausting silence loops
└── Configuration           object  the silence behavior config (mirrors api_silence_behaviour, §9 RT=2)
    ├── silence_duration         int     seconds before bot interjects during wait
    ├── silence_loops            int     max interjections before falling back
    ├── silence_sentence         string  what bot says during each loop ("אני עדיין בודק")
    ├── silence_ending_sentence  string  what bot says after exhausting loops
    ├── silence_instructions     string  additional LLM guidance (often empty)
    └── intent                   int     fallback intent ID (mirrors ApiSilenceIntentID)
```

**Pairing rule:** every intent with `ResponseTypeId = 2` (API call, §9) **should** have a corresponding `apiSilenceRelations[]` entry. The Configuration here is *also* embedded in the intent's `IntentResponces.Configuration.api_silence_behaviour`. The data is duplicated — registry entry + embedded copy.

v1 generation: always emit both. They must be kept in sync; the Assembler is responsible for that.

---

## 9. The Intent Definition (`intents[]` Entry)

The most important structural unit. 16 fields per intent, but the field that determines almost everything else is `IntentResponces.ResponseTypeId`.

### 9.0 The 16-Field Skeleton

| Field | Type | Notes |
|---|---|---|
| `IntentId` | int | Placeholder during generation, platform-assigned on import. |
| `Name` | string | Human-readable name. Hebrew or English. Used in UI and logs. |
| `Description` | string | Plain-language description of what this intent does. Used by LLM for intent recognition. |
| `IntentToolName` | string | snake_case `verb_object` identifier (e.g., `validate_customer_address`). The "function name" the LLM sees in the tools list. |
| `HandlingInstructions` | string\|null | **`null` in all 12 samples.** `[QUIRK]` Appears deprecated. v1 emits `null`. |
| `IsSilenceIntent` | bool | `true` only for intents that exist *as* a silence handler (rare). v1 default `false`. |
| `IntentCategoryId` | int | References `intentCategories[].IntentCategoryId`. |
| `Priority` | int | Observed: `1` in all samples. `[INFERRED]` likely a tie-breaker. v1 emits `1`. |
| `MaxAttempts` | int | Max times the bot retries collecting parameters before giving up. Observed: `3`. v1 default `3`. |
| `ValidationTimeout` | int | Seconds. Observed: `30`. v1 default `30`. |
| `IntentParameters` | array | Slot definitions. See §10. |
| `IntentConfig` | object | Per-intent prompts: `llmDescription`, `validationPrompt`. See §9.1. |
| `IntentScripts` | object | Observed: `{}` in all samples. `[v2]`. |
| `IntentResponces` | object | **The behavior block.** Determined by `ResponseTypeId`. See §9.2. `[QUIRK]` typo preserved. |
| `IsActive` | int | `0` or `1`. v1 emits `1`. |
| `IsDeleted` | int | `0` or `1`. v1 emits `0`. |

### 9.1 `IntentConfig.prompts` — Per-Intent Prompts

Two string fields nested under `IntentConfig.prompts`:

| Field | Training-doc role | Observed |
|---|---|---|
| `llmDescription` | Tool Description (override of Intent Description for the tools list) | **Empty `""` in all 12 samples.** `[OPEN]` fallback semantics — see §17. |
| `validationPrompt` | Intent-level Validation Script — natural-language validation logic | Substantial text in samples. Conversation Routines style: numbered steps, IF/ELSE, "חוק ברזל" (iron rules). |

**v1 strategy:**
- Always emit `llmDescription` even if empty (preserve schema shape).
- `validationPrompt` is the bot designer's primary lever for shaping how the bot collects parameters before executing. Skill 2 fills this.

### 9.2 `IntentResponces` (yes, with the typo)

The container for execution behavior. Two top-level fields:

```
IntentResponces:
├── ResponseTypeId          int     1, 2, 3, or 4 — see §11 for full reference
└── Configuration           object  shape determined by ResponseTypeId
```

The casing-bug pair `intentLoadingAnnouncement` / `IntentLoadingAnnouncement` both appear inside `Configuration` for RT=2 in samples. Both must be preserved as-is. `[QUIRK]`. Full per-RT field tables in §11.

---

## 10. `IntentParameters` — Slot Definitions

The slots the bot collects from the caller before the intent can execute. Each parameter is a structured object.

```
IntentParameters[] entry:
├── ParameterId            int      placeholder, platform-assigned
├── IntentId               int      backreference to parent intent
├── Name                   string   snake_case, e.g. "customer_phone"
├── Description            string   what the bot should ask for; supports Mustache
├── IsRequired             bool     true = blocks execution until collected
├── DefaultValue           any|null typed default; null if none
├── CollectionOrder        int      explicit order, 1-indexed; lower = earlier
├── ParameterTypeId        int      see §12 — STRING=1, PHONE=10, BOOLEAN=16, ENUM=19
├── ParameterType          object   denormalized echo: { ParameterTypeId, Name }
├── OptionList             array    for ENUM (PT=19) only; structure: [{ Value, Label }]
├── ValidationRules        object   observed always {} — [v2] schema unknown
├── ValidationPattern      string|? observed always null — [v2]
├── IsActive               int      0 or 1
└── IsDeleted              int      0 or 1
```

**Observed parameter type usage:**

- **STRING (1):** generic free-text. `customer_name`, `address`, free-form fields.
- **PHONE (10):** phone numbers. The platform applies phone-specific validation and formatting.
- **BOOLEAN (16):** yes/no. Bot interprets natural language (`"כן"`, `"אישרתי"`) as true/false.
- **ENUM (19):** constrained choice. `OptionList` defines the valid options.

**`OptionList` shape for ENUM:**

```
OptionList[] entry:
├── Value     string    machine value
└── Label     string    display label (often Hebrew)
```

**Collection order semantics:** the bot collects parameters in `CollectionOrder` ascending. The LLM uses the per-intent `validationPrompt` (§9.1) to know how to ask for each. v1: assign `CollectionOrder` by the order the user lists slots in the design.

**v1 limitations on parameters:**

- Only the four observed `ParameterTypeId`s are supported. `NUMBER`, `INTEGER`, `DATE`, `EMAIL`, etc. → `[v2]` (§17).
- `ValidationRules` always emitted as `{}`. If the user wants schema constraints (min/max, regex), surface as a known v2 limitation in the interview.
- `ValidationPattern` always emitted as `null`. Regex constraints → `[v2]`.

---

## 11. `ResponseTypeId` Reference — The Four Behavior Primitives

Every intent's behavior is determined by `IntentResponces.ResponseTypeId`. There are four values. The shape of `IntentResponces.Configuration` differs for each.

### 11.1 RT=1 — Layer / IVR Transfer (Terminal)

The bot ends its session by transferring the call to a Voicenter IVR layer. Used for human-agent handoff, queue routing, voicemail, etc.

```
IntentResponces:
├── ResponseTypeId: 1
└── Configuration:
    ├── layer                          string|int    target IVR layer ID (Voicenter platform value)
    ├── announcement                   string        what the bot says before transferring; Mustache supported
    └── intentLoadingAnnouncement      string        spoken while transfer is processing
```

**Observed in samples:**
- Yuval: `transfer_to_human` intent transfers to `layer: 43`.
- Refua: terminal intent transfers to `layer: 41`.

**Behavior:** This intent terminates the bot. There should be no `intentRelations[]` rows with this intent as `OriginIntentID` — the bot is gone.

**v1 generation rules:**
- `layer` value is **user-supplied** during the interview. Generator never invents.
- `announcement` is the verbal handoff (e.g., "אני מעבירה אותך לנציג, רגע אחד").
- `intentLoadingAnnouncement` covers the latency between speaking the handoff and actual transfer (often a brief "המתן בבקשה").

### 11.2 RT=2 — API Call (Webhook)

The bot calls an external HTTP endpoint, receives data, announces a result based on it.

```
IntentResponces:
├── ResponseTypeId: 2
└── Configuration:
    ├── url                            string    full webhook URL (typically connector.center)
    ├── method                         string    "POST" | "GET"
    ├── headers                        object    HTTP headers (often empty {})
    ├── body                           object    request body template; Mustache resolved at runtime
    ├── apiResponseAnnouncement        string    spoken after API success; Mustache resolved with response
    ├── fail_output                    string    spoken on API failure (non-2xx, network error, timeout exceeded)
    ├── function_output                string    LLM guidance for interpreting/using API response in subsequent turns
    ├── intentLoadingAnnouncement      string    spoken WHILE the API is being called (loading state)
    ├── IntentLoadingAnnouncement      string    [QUIRK] capital-I duplicate; preserve as-is
    ├── intentInstructions             string    post-execution behavioral instructions (Conversation Routines style)
    ├── api_silence_behaviour          object    embedded copy of apiSilenceRelations[] Configuration (§8.6)
    ├── response_success               string    [INFERRED] — observed but role unclear; preserve from samples
    └── (other provider-specific fields observed in samples — preserve)
```

**Observed in samples:**
- Refua: `get_nearest_collection_points` calls `connector.center/...` with `{{address}}` → returns pickup points → announces them with `apiResponseAnnouncement`.
- Yuval: `validate_customer_address`, `get_available_slots` similar pattern.

**Mustache resolution timing:**
- `body` Mustache → resolved with collected slot values **at request time**.
- `apiResponseAnnouncement` Mustache → resolved with **API response data** at announcement time. Dotted paths supported: `{{available_slots.0.display}}`, `{{response.address.street}}`.

**Critical pairing rule:** every RT=2 intent must have:
1. `Configuration.api_silence_behaviour` populated (embedded copy)
2. A corresponding `apiSilenceRelations[]` entry (registry copy)

The two must be identical. Assembler's job to keep them in sync.

**v1 generation rules:**
- `url` is **user-supplied**. Generator never invents.
- `headers` defaults to `{}` unless user specifies auth headers.
- `body` is constructed from the intent's slots: each `IntentParameters[]` slot becomes a Mustache key in the body.
- `fail_output` should be a graceful "I couldn't reach the system, let me transfer you" — typically this means transitioning to an RT=1 escalation intent. v1 generates this language; user can override.
- `IntentLoadingAnnouncement` (capital I) and `intentLoadingAnnouncement` (lowercase) — observed both populated with the same content in samples. **v1: emit both, identical content.** Casing bug preserved until clarified.

### 11.3 RT=3 — Continue (Collect → Next Intent)

The bot collects information from the caller, announces something, then continues to the next intent. No external API call. No transfer. Pure conversational.

```
IntentResponces:
├── ResponseTypeId: 3
└── Configuration:
    ├── announcement              string    spoken after slot collection completes; Mustache supported
    ├── intentInstructions        string    post-execution behavioral instructions (Conversation Routines style)
    └── response_success          string    [INFERRED] role; preserve from samples
```

**Observed in samples:**
- Refua: `confirm_pickup_point` — caller has been told the available pickup points, this intent confirms which one they pick, announces confirmation, the conversation continues (typically toward end of call).
- Yuval: `confirm_appointment` — confirms a chosen slot, announces booking, continues.

**Behavior:** this is the most common pattern for "gather and proceed" steps. The intent collects its slots (per `IntentParameters[]`), executes (which here just means "validates and announces"), and the conversation continues — the LLM picks the next intent from `intentRelations[]`.

**v1 generation rules:**
- Simplest of the four RTs. Generator handles this fully without external dependencies.
- `intentInstructions` is the post-execution guidance — what the bot should focus on *after* this intent completes. Often "you've confirmed the booking; if the user asks anything else, transfer to human."

### 11.4 RT=4 — Dial-Out (Outbound Call)

The bot initiates a phone call to a number, optionally to a Voicenter NEXT_VO destination.

```
IntentResponces:
├── ResponseTypeId: 4
└── Configuration:
    ├── phone3                    string    destination phone number (E.164 or local)
    ├── parameter_phone           string    name of the parameter holding the dialed number (often "phone")
    ├── NEXT_VO_ID                int       Voicenter routing ID for the dial destination
    ├── MAX_DIAL_DURATION         int       seconds; max ring/dial duration
    ├── selectdial_option         string    observed: specific to platform; preserve from samples
    ├── record                    bool      whether to record the dial-out
    ├── announcement              string    spoken before initiating the dial; Mustache supported
    └── intentLoadingAnnouncement string    spoken while dialing
```

**Observed in samples:** present in the schema but not actively used in either Yuval or Refua's primary flows. Inferred from field names and platform context.

**v1 generation rules:**
- `phone3`, `NEXT_VO_ID`, `selectdial_option` are **user-supplied platform values**. Generator never invents.
- `parameter_phone` references a slot the user must have defined in `IntentParameters[]`.
- v1 supports RT=4 structurally (Assembler emits the correct shape) but flags it during the interview as "uncommon — confirm you actually need an outbound dial."

### 11.5 Cross-RT Field Summary

| Field | RT=1 | RT=2 | RT=3 | RT=4 |
|---|---|---|---|---|
| `announcement` | yes | — | yes | yes |
| `apiResponseAnnouncement` | — | yes | — | — |
| `intentLoadingAnnouncement` | yes | yes | — | yes |
| `IntentLoadingAnnouncement` | — | yes (`[QUIRK]`) | — | — |
| `intentInstructions` | — | yes | yes | — |
| `fail_output` | — | yes | — | — |
| `function_output` | — | yes | — | — |
| `response_success` | — | yes | yes | — |
| `api_silence_behaviour` | — | yes | — | — |
| `layer` | yes | — | — | — |
| `url`/`method`/`headers`/`body` | — | yes | — | — |
| `phone3`/`NEXT_VO_ID`/etc. | — | — | — | yes |

---

## 12. `ParameterTypeId` Catalog (v1)

Four observed values. The IDs imply a larger catalog (gaps at 2–9, 11–15, 17–18) but those are unobserved → `[v2]`.

| ID | Name | Description | Validation handled by |
|---|---|---|---|
| **1** | STRING | Free text — names, addresses, descriptions, free-form input. | `validationPrompt` (natural language) |
| **10** | PHONE | Phone numbers. Platform applies format normalization and validation. | Platform + `validationPrompt` |
| **16** | BOOLEAN | Yes/no answers. Bot interprets natural language (`"כן"`, `"לא"`, `"אישרתי"`) as true/false. | `validationPrompt` |
| **19** | ENUM | Constrained choice. Uses `OptionList` for valid values. | `OptionList` + `validationPrompt` |

**v1 mapping logic for the generator:**

| User says they need… | Use ParameterTypeId |
|---|---|
| "the customer's name" / "the address" / any free text | 1 (STRING) |
| "phone number" | 10 (PHONE) |
| "yes/no", "do they want X", "confirmation" | 16 (BOOLEAN) |
| "pick from a list of options" | 19 (ENUM) + populate `OptionList` |
| "a number" / "an integer" / "a date" / "an email" | **v1 fallback: STRING with `validationPrompt` enforcing format**, flagged to user as a v2 limitation |

The fallback for unsupported types is **STRING + natural-language validation in `validationPrompt`**. This works (the LLM can validate "must be a positive integer" via prompt) but is less robust than typed validation. Skill 1's interview should call this out when the user describes a slot that would benefit from a real type.

**`OptionList` mapping for ENUM:**

User says "the caller picks one of: Tel Aviv, Jerusalem, Haifa" →

```json
{
  "ParameterTypeId": 19,
  "OptionList": [
    { "Value": "tel_aviv", "Label": "תל אביב" },
    { "Value": "jerusalem", "Label": "ירושלים" },
    { "Value": "haifa", "Label": "חיפה" }
  ]
}
```

`Value` is the machine-side identifier (snake_case, ASCII). `Label` is what the bot recognizes/announces (the user's actual language).

---

## 13. Mustache Templating & Call Context Variables

Variables use `{{name}}` syntax. They're resolved at runtime from the **Call Context** — a dynamic data object that accumulates throughout the conversation.

### 13.1 The Four Variable Categories

**A. Slot variables** — values collected from the caller.

```
{{address}}              ← collected by an IntentParameters[] slot named "address"
{{customer_phone}}       ← collected slot
{{customer_name}}        ← collected slot
```

These become available the moment the slot is filled, persist across all subsequent intents.

**B. System variables** — populated by the platform at call start or per-turn.

Observed in samples:

```
{{TimeNow}}              current time
{{DateNow}}              current date
{{caller_id}}            caller ANI / phone number
```

**v1 stance:** the generator treats system variables as a **whitelist**. Only `TimeNow`, `DateNow`, and `caller_id` are guaranteed available. Other system variables (e.g., CRM data per training doc) → `[v2]` since their availability depends on platform integrations beyond the JSON.

**C. Dotted API-response paths** — for RT=2 intents, response fields are accessible by path.

Observed in samples:

```
{{available_slots.0.display}}     ← response.available_slots[0].display
{{available_slots.0.slot_id}}     ← response.available_slots[0].slot_id
{{response.address.street}}       ← response.address.street
```

The path navigates the parsed JSON response. Available **only after** the API call resolves, **only inside** the same intent's `apiResponseAnnouncement` and (per inference) downstream intents' fields.

**D. Cross-intent references** — values from previously-completed intents persist in context.

A slot collected in intent A is referenceable as `{{slot_name}}` in intent B's announcement, intentInstructions, or API body. Slot names should therefore be **globally unique across the bot**, not unique per intent.

### 13.2 v1 Templating Rules for the Generator

1. **Slot variables** are checked at generation time — the variable name must match an `IntentParameters[].Name` somewhere in the bot. If not, flag as a likely typo.
2. **System variables** must come from the v1 whitelist. Anything else gets flagged.
3. **Dotted paths** — generator can't validate these (no API contract), but warns the user when used: "you've referenced `{{slots.0.name}}` — confirm this matches your webhook's response shape."
4. **Cross-intent references** — must reference a slot name that exists earlier in the conversation flow. If the slot is collected after the reference, that's a logic error.

---

## 14. Worked Examples

This section serves three complementary lenses on the wire format.

**§14.1 — The hierarchy lens.** Five complete bots, each fully configured and internally consistent. Two are observed production exports. Three are constructed from realistic SMB patterns to demonstrate hierarchy across multiple business contexts and a non-Hebrew language. Each synthesized bot is explicitly marked. The structures conform to the schema in §4–§13; only domain specifics (URLs, layer IDs, account IDs) are placeholders.

**§14.2 — The recipe lens.** Standalone intents grouped by `ResponseTypeId`, showing patterns the full bots don't cover.

**§14.3 — Anti-patterns.** Failure modes the generator must refuse to produce.

The iron rules referenced throughout §14.3 are:

> Every non-terminal intent must have an escalation transition. Every Mustache variable must resolve to a known slot, system variable, or dotted API path. Every RT=2 intent must have paired silence behavior (embedded + registry). Persona may claim only what intents actually exist. Content must live in the field whose scope matches its scope.

---

### §14.1 — Full Bot Examples (Hierarchy Lens)

#### §14.1.1 — Yuval (יובל) — Installation Scheduling

**Source:** observed production export. **Account:** NC. **Voice:** Puck. **Language:** he-IL.

**Use case.** Customer of NC dials in to schedule a hardware installation appointment. The bot validates the address is in service area, fetches available slots from the scheduling backend, books the chosen slot.

##### Persona bundle

```
prompts.persona:
  "את יובל, נציגת שירות הלקוחות של חברת NC.
   את מדברת רק בעברית, בטון מקצועי, סבלני וחם.
   את עוזרת ללקוחות בנושא אחד בלבד: קביעת תורי התקנה.
   לא מטפלת בחיובים, תקלות טכניות, או שינוי תוכניות —
   על אלה את מעבירה לנציג אנושי.
   הימנעי מסלנג, אל תשתמשי באנגלית, אל תשערי כאשר את לא בטוחה.
   כשלא ברור — שאלי שוב. אם עדיין לא ברור — העבירי לנציג."

prompts.voiceInstructions:
  "דברי בקצב רגוע, עצרי בין משפטים.
   הקפידי על הגייה ברורה של שמות רחובות וערים.
   אם הלקוח קוטע אותך — עצרי מיד והקשיבי.
   הימנעי ממשפטים ארוכים מדי בנשימה אחת.
   לפני קריאת מספרים, אמרי 'הקשיבי בבקשה למספר'."

prompts.chatInstructions:
  "כתבי בעברית ברורה. הימנעי מאימוג'ים.
   שורות קצרות, תוכן ממוקד.
   רשימות ממוספרות במקום פסקאות ארוכות."

prompts.intentInstructions:
  "OPENING BEHAVIOR
   1. ברכי קצרות: 'שלום, איך אוכל לעזור?'
   2. הקשיבי לבקשה.
   3. אם הלקוח רוצה לקבוע התקנה: validate_customer_address.
   4. אם רוצה לשנות התקנה קיימת: reschedule_existing.
   5. אם שאלה כללית: general_inquiry.
   6. אם משהו אחר (חיוב, תקלה, שינוי תוכנית): transfer_to_human.

   IRON RULE: אל תנסי לטפל בנושאים מחוץ ל-scope.
   אם בספק — שאלי פעם אחת ואז העבירי לנציג."

prompts.openingAnnouncement:
  "שלום, אני יובל מ-NC. איך אוכל לעזור היום?"
```

##### Voice & generation config

```
created.model: "models/gemini-2.5-flash-preview-native-audio-dialog"
created.generationConfig.speechConfig.languageCode: "he-IL"
created.generationConfig.speechConfig.voiceConfig.prebuiltVoiceConfig.voiceName: "Puck"
created.generationConfig.temperature: 1.5
```

##### Caller-silence behavior

```
silence_behaviour:
  silence_duration: 6
  silence_loops: 3
  silence_sentence: "האם את/ה עדיין שם?"
  silence_ending_sentence: "נראה שיש בעיית קישור, אני סוגרת את השיחה. תוכל לחזור אלינו."
```

##### Intent table

| # | Name | RT | Role |
|---|---|---|---|
| 1 | `validate_customer_address` | 2 | API: validates address against service-area DB |
| 2 | `get_available_slots` | 2 | API: returns 3 nearest appointment slots |
| 3 | `confirm_appointment` | 3 | Continue: caller picks a slot, bot confirms booking |
| 4 | `reschedule_existing` | 3 | Continue: alternate flow for existing appointment changes |
| 5 | `general_inquiry` | 3 | Continue: catch-all for "I have a question" |
| 6 | `transfer_to_human` | 1 | Layer transfer to layer 43 |

##### Transition graph

```
[start] ──→ validate_customer_address  (Order 1)
       ──→ reschedule_existing          (Order 2)
       ──→ general_inquiry               (Order 3)
       ──→ transfer_to_human             (Order 4)

validate_customer_address ──→ get_available_slots  (Order 1, success)
                          ──→ transfer_to_human    (Order 2, fallback)

get_available_slots ──→ confirm_appointment  (Order 1, success)
                    ──→ transfer_to_human    (Order 2, fallback)

confirm_appointment ──→ general_inquiry   (Order 1, post-booking)
                    ──→ transfer_to_human (Order 2, escalation)

reschedule_existing ──→ confirm_appointment (Order 1)
                    ──→ transfer_to_human   (Order 2, fallback)

general_inquiry ──→ transfer_to_human (Order 1)

transfer_to_human ──→ (none — terminal)
```

##### Annotated intent: `validate_customer_address` (RT=2)

```
IntentId: <placeholder>
Name: "אימות כתובת לקוח"
Description: "וידוא שהכתובת של הלקוח נמצאת באזור השירות שלנו."
IntentToolName: "validate_customer_address"
IntentCategoryId: <default>
Priority: 1
MaxAttempts: 3
ValidationTimeout: 30
IsActive: 1
IsDeleted: 0

IntentParameters:
  - Name: "address"
    Description: "כתובת מלאה: רחוב, מספר בית, עיר. למשל: רחוב הרצל 14 רמת גן."
    ParameterTypeId: 1                       # STRING
    IsRequired: true
    DefaultValue: null
    CollectionOrder: 1
    OptionList: []
    ValidationRules: {}
    ValidationPattern: null

IntentConfig.prompts:
  llmDescription: ""                          # empty, see §17
  validationPrompt: |
    ADDRESS COLLECTION
    1. בקשי מהלקוח כתובת מלאה.
    2. ודאי: רחוב, מספר בית, עיר.
    3. חזרי על הכתובת לאישור.
    4. שמרי ב-{{address}} רק אם הלקוח אישר.

    IRON RULE: לא ממשיכה ללא רחוב + מספר + עיר.
    אם חסר אחד — שאלי שוב פעם אחת.
    אם עדיין חסר — תני fail_output ועברי ל-transfer_to_human.

IntentResponces:
  ResponseTypeId: 2
  Configuration:
    url: "https://connector.center/nc/validate-address"
    method: "POST"
    headers: {}
    body:
      address: "{{address}}"
    apiResponseAnnouncement: "הכתובת אומתה. בודקת זמינות תורים..."
    fail_output: "אני לא מצליחה לאמת את הכתובת כרגע. אעבירך לנציג."
    function_output: |
      The API returns { valid: bool, service_area: string }.
      If valid=true, proceed to get_available_slots.
      If valid=false, the address is outside service area —
      announce that politely and transfer.
    intentLoadingAnnouncement: "רגע, בודקת..."
    IntentLoadingAnnouncement: "רגע, בודקת..."   # [QUIRK] capital-I duplicate
    intentInstructions: |
      POST-EXECUTION (address validated)
      1. הזיזי את השיחה ל-get_available_slots.
      2. אם valid=false: אמרי "הכתובת לא באזור שירות שלנו",
         והציעי transfer_to_human.
    response_success: ""
    api_silence_behaviour:
      silence_duration: 8
      silence_loops: 5
      silence_sentence: "אני עדיין בודקת..."
      silence_ending_sentence: "השרת לא מגיב. אעבירך לנציג."
      silence_instructions: ""
      intent: <transfer_to_human IntentId>
```

Paired `apiSilenceRelations[]` entry:

```
OriginIntentID: <validate_customer_address IntentId>
ApiSilenceIntentID: <transfer_to_human IntentId>
Configuration: { ...same as Configuration.api_silence_behaviour above }
```

##### Annotated intent: `confirm_appointment` (RT=3)

```
Name: "אישור תור"
Description: "אישור בחירת התור על ידי הלקוח."
IntentToolName: "confirm_appointment"

IntentParameters:
  - Name: "selected_slot_id"
    ParameterTypeId: 19                      # ENUM
    IsRequired: true
    CollectionOrder: 1
    OptionList: []                           # populated dynamically — [v2] flag
    Description: "הלקוח בוחר אחד מהתורים שהוצעו: {{available_slots}}"

IntentConfig.prompts.validationPrompt: |
  SLOT SELECTION
  1. הצעי את שלושת התורים שהתקבלו מ-get_available_slots.
  2. הקשיבי לבחירה.
  3. אם הבחירה ברורה — שמרי {{selected_slot_id}}.
  4. אם לא ברור — חזרי על שלושת האפשרויות.

  IRON RULE: לא לשמור slot_id לפני אישור הלקוח.

IntentResponces:
  ResponseTypeId: 3
  Configuration:
    announcement: "מעולה. רשמתי לך תור ב-{{available_slots.0.display}} בכתובת {{address}}. נשלח לך SMS עם פרטים."
    intentInstructions: |
      POST-EXECUTION (booking confirmed)
      1. אם הלקוח שואל על משהו אחר — general_inquiry.
      2. אם רוצה לשנות — transfer_to_human (לא חוזרים ל-reschedule).
      3. אחרת — סיימי בנימוס.
    response_success: ""
```

##### Compact view: remaining 4 intents

```
get_available_slots (RT=2)
  Slots: address (inherited from context, not re-collected)
  url: connector.center/nc/get-slots
  apiResponseAnnouncement: "מצאתי שלושה תורים: 1) {{available_slots.0.display}},
                            2) {{available_slots.1.display}}, 3) {{available_slots.2.display}}"
  Pairs with apiSilenceRelations → transfer_to_human

reschedule_existing (RT=3)
  Slots: existing_appointment_id (STRING), reason (STRING, optional)
  announcement: "הבנתי, יש לך תור קיים שאת/ה רוצה לשנות. אעבירך לנציג."
  Note: actually transitions to transfer_to_human in v1 — full reschedule
  flow not implemented; this intent exists for routing recognition only.

general_inquiry (RT=3)
  Slots: question (STRING)
  announcement: "אם השאלה לא קשורה לתור התקנה, אעבירך לנציג."
  intentInstructions: routes to transfer_to_human in 95% of cases.

transfer_to_human (RT=1)
  Configuration:
    layer: 43
    announcement: "אעבירך לנציג, רגע."
    intentLoadingAnnouncement: "מעבירה..."
```

---

#### §14.1.2 — Refua (חברים לרפואה) — Pharmacy Pickup-Point Finder

**Source:** observed production export. **Account:** Friends in Medicine. **Voice:** Orus. **Language:** he-IL.

**Use case.** Patient calls in to find their nearest pharmacy pickup point and confirm collection of a prescription order.

##### Persona bundle (compact view; full structure mirrors §14.1.1)

```
prompts.persona:
  "את הקול של חברים לרפואה. את עוזרת לחברי הקופה למצוא נקודות איסוף
   קרובות, ולאשר איסוף תרופות.
   את לא נותנת ייעוץ רפואי, לא משנה תרופות, לא מאשרת מרשמים —
   אלה תפקידים של רוקח/ית מורשה.
   ספק רפואי מצריך הפניה לנציג."

prompts.openingAnnouncement:
  "שלום, אני כאן מטעם חברים לרפואה. איך אוכל לעזור?"
```

##### Voice config

```
voiceName: "Orus"
languageCode: "he-IL"
```

##### Intent table

| # | Name | RT | Role |
|---|---|---|---|
| 1 | `validate_customer_address` | 2 | API: validates address |
| 2 | `get_nearest_collection_points` | 2 | API: returns 3 nearest pickup points |
| 3 | `confirm_pickup_point` | 3 | Continue: caller picks a point |
| 4 | `report_issue` | 3 | Continue: order problem path |
| 5 | `general_inquiry` | 3 | Continue: catch-all |
| 6 | `transfer_to_human` | 1 | Layer 41 |

##### Annotated intent: `get_nearest_collection_points` (RT=2)

This is the canonical demo of dotted-path Mustache resolution.

```
IntentParameters: []                        # uses {{address}} from context

IntentResponces:
  ResponseTypeId: 2
  Configuration:
    url: "https://connector.center/refua/find-pickup-points"
    method: "POST"
    body:
      address: "{{address}}"
      max_results: 3
    apiResponseAnnouncement: |
      מצאתי שלוש נקודות איסוף קרובות:
      1. {{available_slots.0.display}} ({{available_slots.0.distance_km}} ק"מ)
      2. {{available_slots.1.display}} ({{available_slots.1.distance_km}} ק"מ)
      3. {{available_slots.2.display}} ({{available_slots.2.distance_km}} ק"מ)
      איזו מהן מתאימה לך?
    fail_output: "אני לא מצליחה למצוא נקודות איסוף כרגע. אעבירך לנציג."
    function_output: |
      Response shape: { available_slots: [{display, slot_id, distance_km}, ...] }
      Caller will pick one in confirm_pickup_point intent.
```

The `{{available_slots.N.display}}` paths navigate the response array. `available_slots` is the API response key; `.0` is array index; `.display` is the field. v1 generators don't validate dotted paths against an OpenAPI spec (one isn't supplied) — they trust the user's stated response shape and surface the paths used so the user can sanity-check them.

##### Compact view: remaining 5 intents

```
validate_customer_address (RT=2): mirrors Yuval's, different URL
confirm_pickup_point (RT=3): ENUM slot, dynamic OptionList from upstream API
report_issue (RT=3): collects free-text issue, transitions to transfer_to_human
general_inquiry (RT=3): catch-all → transfer_to_human
transfer_to_human (RT=1): layer 41
```

---

#### §14.1.3 — [SYNTHESIZED FOR REFERENCE] — Insurance Broker

**Source:** synthesized from realistic SMB patterns. Structure conforms to schema; specifics are placeholders. **Account:** placeholder. **Voice:** Puck. **Language:** he-IL.

**Use case.** Small Israeli insurance brokerage. Caller may be (a) an existing customer asking about a claim, (b) a prospect requesting a quote, (c) anyone needing to reach the broker directly. Demonstrates **mixed sales+support disambiguation at start**.

##### Persona bundle

```
prompts.persona: |
  את עדי, נציגת השירות של סוכנות הביטוח [SHEM_HASOCHENUT].
  את עוזרת בשני סוגי פניות: בקשת הצעה לפוליסה חדשה, ובדיקת סטטוס תביעה קיימת.
  את לא נותנת ייעוץ ביטוחי מקצועי. כל חישוב פרמיה, פרשנות פוליסה,
  או החלטה על אישור תביעה — דורש מעבר לסוכן.
  אל תנקבי בסכומים. אל תאשרי כיסויים. אל תפרשני סעיפים.
  בכל ספק — מעבר לנציג.

prompts.voiceInstructions: |
  טון רגוע ואמין. דברי לאט במיוחד כשמדובר במספרי פוליסה
  או תאריכי תוקף. הקפידי על הגייה של שמות לועזיים בפוליסות.

prompts.intentInstructions: |
  OPENING BEHAVIOR
  1. ברכי וזהי את צורך הלקוח.
  2. אם רוצה הצעה חדשה: collect_quote_request.
  3. אם תביעה קיימת: verify_customer_identity (חובה לפני סטטוס).
  4. אם רוצה שיחה ישירה עם הסוכן: transfer_to_broker.
  5. בכל מקרה אחר: transfer_to_broker.

  IRON RULE: לא לחשוף פרטי פוליסה ללא verify_customer_identity קודם.

prompts.openingAnnouncement:
  "שלום, סוכנות הביטוח [SHEM]. איך אפשר לעזור?"
```

##### Intent table

| # | Name | RT | Role | Lens |
|---|---|---|---|---|
| 1 | `verify_customer_identity` | 2 | API: matches phone+ID against customer DB | Support |
| 2 | `lookup_claim_status` | 2 | API: returns claim status; **gated by verify** | Support |
| 3 | `collect_quote_request` | 3 | Continue: collects insurance type, basic info | Sales |
| 4 | `submit_quote_lead` | 2 | API: posts lead to CRM, gets confirmation | Sales |
| 5 | `schedule_callback` | 4 | Dial-out: callback to caller's number | Sales |
| 6 | `general_inquiry` | 3 | Continue: catch-all | Both |
| 7 | `transfer_to_broker` | 1 | Layer to broker queue | Both |

##### Transition graph

```
[start] ──→ verify_customer_identity   (Order 1, claim path)
       ──→ collect_quote_request       (Order 2, sales path)
       ──→ general_inquiry              (Order 3)
       ──→ transfer_to_broker           (Order 4)

verify_customer_identity ──→ lookup_claim_status  (Order 1, success)
                         ──→ transfer_to_broker   (Order 2, identity failed)

lookup_claim_status ──→ general_inquiry      (Order 1)
                    ──→ transfer_to_broker   (Order 2)

collect_quote_request ──→ submit_quote_lead   (Order 1, success)
                      ──→ schedule_callback   (Order 2, alt)
                      ──→ transfer_to_broker  (Order 3)

submit_quote_lead ──→ schedule_callback     (Order 1)
                  ──→ transfer_to_broker    (Order 2)

schedule_callback ──→ (none — terminal after dial-out)

general_inquiry ──→ transfer_to_broker (Order 1)

transfer_to_broker ──→ (none — terminal)
```

##### Annotated intent: `verify_customer_identity` (RT=2 with auth headers)

```
IntentParameters:
  - Name: "customer_id"
    ParameterTypeId: 1                       # STRING (Israeli ID)
    IsRequired: true
    CollectionOrder: 1
    Description: "תעודת זהות, 9 ספרות"

  - Name: "phone_last_digits"
    ParameterTypeId: 1                       # STRING
    IsRequired: true
    CollectionOrder: 2
    Description: "ארבע ספרות אחרונות של הטלפון הרשום בפוליסה"

IntentConfig.prompts.validationPrompt: |
  IDENTITY VERIFICATION
  1. בקשי תעודת זהות (9 ספרות).
  2. בקשי 4 ספרות אחרונות של הטלפון.
  3. חזרי על שניהם לאישור.

  IRON RULES:
  - אל תקריאי בחזרה את כל מספר הטלפון מהמערכת — רק 4 ספרות שהלקוח נתן.
  - אם הלקוח לא בטוח — אל תנסי לעזור עם רמזים. transfer_to_broker.

IntentResponces:
  ResponseTypeId: 2
  Configuration:
    url: "https://crm.[SHEM_HASOCHENUT].co.il/api/verify"
    method: "POST"
    headers:
      Authorization: "Bearer {{ENV.CRM_API_TOKEN}}"   # placeholder, supplied at deploy
      Content-Type: "application/json"
    body:
      id: "{{customer_id}}"
      phone_last_4: "{{phone_last_digits}}"
    apiResponseAnnouncement: "אומת בהצלחה. ממשיכה."
    fail_output: "לא הצלחתי לאמת את הזהות. אעבירך לסוכן."
    function_output: |
      Response { verified: bool, customer_uuid: string }.
      If verified=true, customer_uuid is now in context for downstream API calls.
      If verified=false, must escalate.
    api_silence_behaviour:
      silence_duration: 6
      silence_loops: 4
      silence_sentence: "רגע, בודקת..."
      silence_ending_sentence: "השרת איטי, אעבירך לסוכן."
      intent: <transfer_to_broker IntentId>

apiSilenceRelations: [paired entry, identical Configuration]
```

This intent **gates** `lookup_claim_status` — the LLM is instructed (via `lookup_claim_status.intentInstructions` and via `prompts.intentInstructions` iron rules) never to reach claim status without `verified=true` in context. v1 doesn't have structural condition gating (`[v2]`), so the gating is enforced by natural-language instruction, not by `IntentConditionList`.

##### Annotated intent: `schedule_callback` (RT=4 — only RT=4 in the bot set)

```
IntentParameters:
  - Name: "callback_number"
    ParameterTypeId: 10                      # PHONE
    IsRequired: true
    CollectionOrder: 1

  - Name: "preferred_time_window"
    ParameterTypeId: 19                      # ENUM
    IsRequired: true
    CollectionOrder: 2
    OptionList:
      - { Value: "morning",    Label: "בוקר (8-12)" }
      - { Value: "afternoon",  Label: "צהריים (12-16)" }
      - { Value: "evening",    Label: "ערב (16-19)" }

IntentResponces:
  ResponseTypeId: 4
  Configuration:
    phone3: "{{callback_number}}"
    parameter_phone: "callback_number"
    NEXT_VO_ID: <broker_outbound_VO>         # placeholder
    MAX_DIAL_DURATION: 60
    selectdial_option: "broker_callback"
    record: true
    announcement: "מעולה, נחזור אליך ב{{preferred_time_window}} למספר שמסרת."
    intentLoadingAnnouncement: "רושמת..."
```

##### Compact view: remaining 5 intents

```
lookup_claim_status (RT=2)
  Slots: claim_number (STRING)
  Headers: Authorization: Bearer {{ENV.CRM_API_TOKEN}}, X-Customer-UUID: {{customer_uuid}}
  apiResponseAnnouncement: "התביעה {{claim_number}} בסטטוס {{response.status}}.
                            תאריך עדכון אחרון: {{response.updated_at}}."

collect_quote_request (RT=3)
  Slots: insurance_type (ENUM: דירה/רכב/חיים/בריאות), full_name (STRING)
  intentInstructions: routes to submit_quote_lead

submit_quote_lead (RT=2)
  POSTs to CRM /leads endpoint
  apiResponseAnnouncement: "ההצעה נרשמה, מספר פנייה {{response.lead_id}}.
                            נחזור אליך בהקדם."

general_inquiry (RT=3): catch-all → transfer_to_broker
transfer_to_broker (RT=1): layer <broker_layer_id>
```

---

#### §14.1.4 — [SYNTHESIZED FOR REFERENCE] — B2C Apparel E-Commerce

**Source:** synthesized. **Voice:** Aoede. **Language:** en-US.

**Use case.** Small online apparel store. Caller may be (a) a customer with an existing order needing status, return, or address change, (b) a prospect with presale questions about products/sizing/shipping, (c) a customer with delivery problems. Demonstrates **English bot, mixed sales+support, dynamic ENUM, dotted-path on nested response**.

##### Persona bundle (English)

```
prompts.persona: |
  You are Riley, the voice assistant for [STORE_NAME], a small online apparel store.
  You help with two kinds of calls: questions about existing orders (status, returns,
  delivery, address changes), and presale questions (sizing, materials, shipping policy).
  You are NOT able to: give specific style advice, modify pricing, process payments
  for new orders, or handle wholesale inquiries — for those, you transfer to a human.
  Tone: friendly, concise, helpful. American English.
  Always confirm order numbers by reading them back. Never invent product details
  you weren't told.

prompts.voiceInstructions: |
  Speak naturally and warmly. Pause briefly between sentences.
  When reading order numbers, slow down and pronounce each character clearly.
  If the caller interrupts, stop immediately and listen.

prompts.chatInstructions: |
  Keep messages short. No emoji unless the caller uses one first.
  Use line breaks between distinct ideas. Format order numbers in monospace if possible.

prompts.intentInstructions: |
  OPENING BEHAVIOR
  1. Greet briefly: "Hey, this is Riley from [STORE_NAME], how can I help?"
  2. Listen for the request type.
  3. Existing order question -> verify_order
  4. Sizing or product question -> presale_inquiry
  5. Wholesale/B2B -> transfer_to_human (we don't handle that)
  6. Anything else -> transfer_to_human

  IRON RULE: Never share order details before verify_order completes.

prompts.openingAnnouncement:
  "Hey, this is Riley from [STORE_NAME]. How can I help?"
```

##### Intent table

| # | Name | RT | Role | Lens |
|---|---|---|---|---|
| 1 | `verify_order` | 2 | API: matches order# + email/zip | Support |
| 2 | `report_order_status` | 3 | Continue: announce status from verify response | Support |
| 3 | `initiate_return` | 2 | API: creates return label | Support |
| 4 | `change_delivery_address` | 2 | API: updates shipping address pre-ship | Support |
| 5 | `presale_inquiry` | 3 | Continue: collects question, routes via FAQ KB or to human | Sales |
| 6 | `lookup_size_guide` | 2 | API: fetches size info for a product | Sales |
| 7 | `transfer_to_human` | 1 | Layer to support queue | Both |

##### Transition graph

```
[start] ──→ verify_order        (Order 1)
       ──→ presale_inquiry      (Order 2)
       ──→ transfer_to_human    (Order 3)

verify_order ──→ report_order_status      (Order 1, success — auto-route)
              ──→ transfer_to_human        (Order 2, verification failed)

report_order_status ──→ initiate_return          (Order 1, if customer wants return)
                    ──→ change_delivery_address  (Order 2, if pre-ship)
                    ──→ transfer_to_human        (Order 3, escalation)

initiate_return ──→ transfer_to_human (Order 1, post-confirmation)

change_delivery_address ──→ transfer_to_human (Order 1)

presale_inquiry ──→ lookup_size_guide  (Order 1, if size question)
                ──→ transfer_to_human  (Order 2)

lookup_size_guide ──→ transfer_to_human (Order 1)

transfer_to_human ──→ (none — terminal)
```

##### Annotated intent: `verify_order` (RT=2)

```
IntentParameters:
  - Name: "order_number"
    ParameterTypeId: 1                       # STRING (alphanumeric like "ORD-12345")
    IsRequired: true
    CollectionOrder: 1
    Description: "Order number, starts with ORD followed by digits"

  - Name: "email_or_zip"
    ParameterTypeId: 1                       # STRING (either email or zip)
    IsRequired: true
    CollectionOrder: 2
    Description: "Email used at checkout, OR billing zip code"

IntentConfig.prompts.validationPrompt: |
  ORDER VERIFICATION
  1. Ask for order number. Format is ORD-XXXXX. Read it back digit by digit.
  2. Ask for email OR zip code from the order.
  3. Confirm both with caller before proceeding.

  IRON RULE: Do not search by name. Do not bypass either parameter.
  If caller can't provide order number, transfer to human.

IntentResponces:
  ResponseTypeId: 2
  Configuration:
    url: "https://api.[STORE].com/orders/verify"
    method: "POST"
    headers:
      X-Api-Key: "{{ENV.STORE_API_KEY}}"
      Content-Type: "application/json"
    body:
      order_number: "{{order_number}}"
      verify_with: "{{email_or_zip}}"
    apiResponseAnnouncement: "Got it, found your order."
    fail_output: "I couldn't find that order. Let me transfer you."
    function_output: |
      Response: { verified: bool, order: { status, items: [...], shipping: {...} } }
      Cache response.order in context as {{order}} for downstream intents.
    api_silence_behaviour:
      silence_duration: 5
      silence_loops: 4
      silence_sentence: "Still looking..."
      silence_ending_sentence: "Our system is slow today, transferring you to support."
      intent: <transfer_to_human IntentId>
```

##### Annotated intent: `report_order_status` (RT=3) — uses dotted paths from `verify_order` response

```
IntentParameters: []                         # purely uses context

IntentResponces:
  ResponseTypeId: 3
  Configuration:
    announcement: |
      Your order is currently {{order.status}}.
      It contains {{order.items.length}} items, shipping to
      {{order.shipping.city}}, {{order.shipping.state}}.
      Estimated delivery: {{order.shipping.eta}}.
      Anything else I can help with?
    intentInstructions: |
      POST-EXECUTION (status announced)
      - If caller wants to return: initiate_return.
      - If pre-ship and wants address change: change_delivery_address.
      - If caller is satisfied: end politely.
      - Anything else: transfer_to_human.

      IRON RULE: only offer change_delivery_address if {{order.status}} is
      "processing" or "label_created" — not after "shipped".
```

##### Compact view: remaining 5 intents

```
initiate_return (RT=2)
  POSTs to /returns; receives return label URL via email.
  apiResponseAnnouncement: "Return started. Check {{response.email}} for the label."

change_delivery_address (RT=2)
  Slots: new_address (STRING with multi-step validationPrompt for street/city/zip)
  PATCHes order shipping address.

presale_inquiry (RT=3)
  Slots: product_question (STRING)
  intentInstructions: try lookup_size_guide for size questions, else transfer_to_human.

lookup_size_guide (RT=2)
  Slots: product_name (STRING)
  apiResponseAnnouncement: "For {{product_name}}, fits true to size — runs about
                            half a size {{response.fit_note}}. Specific measurements
                            are at {{response.size_chart_url}}."

transfer_to_human (RT=1)
  Layer to support queue.
```

---

#### §14.1.5 — [SYNTHESIZED FOR REFERENCE] — ISP / Communications Company

**Source:** synthesized. **Voice:** Charon. **Language:** he-IL.

**Use case.** Small Israeli ISP / business-comms provider. Caller may be (a) an existing subscriber with a technical issue (no internet, slow speeds), (b) an existing subscriber wanting to upgrade or change plan, (c) a prospect interested in a new line for home or small business. Demonstrates **chained RT=2 calls (diagnose → result-driven branching), persona limiting capability claims, sales-vs-support disambiguation**.

##### Persona bundle (compact view)

```
prompts.persona: |
  את שירה, נציגת [SHEM_HACEVERA].
  את עוזרת בשני סוגי פניות: תקלות טכניות בקו קיים, ובירורים על שדרוג
  או חיבור חדש (בית או עסק).
  לא מטפלת ב: גביה, מחיקת חוב, הסכמי ייחודיים, פטורים. את אלה לנציג שירות.
  לא מבטיחה תאריכי התקנה — תמיד "נחזור אליך לתיאום מדויק".
  לא מצטטת מחירים — תמיד "המחיר המדויק יישלח כהצעה רשמית".

prompts.intentInstructions: |
  OPENING
  1. ברכי, זהי כיוון.
  2. תקלה טכנית: verify_subscription -> run_line_diagnostic.
  3. רוצה שדרוג בקו קיים: verify_subscription -> upgrade_plan_inquiry.
  4. קו חדש (בית או עסק): collect_new_line_lead.
  5. אחר (גביה, חוב, תלונות): transfer_to_human.

prompts.openingAnnouncement:
  "שלום, [SHEM_HACEVERA]. איך אפשר לעזור?"
```

##### Intent table

| # | Name | RT | Role | Lens |
|---|---|---|---|---|
| 1 | `verify_subscription` | 2 | API: matches phone+ID against subscriber DB | Both |
| 2 | `run_line_diagnostic` | 2 | API: triggers line check, returns status | Support |
| 3 | `report_diagnostic_result` | 3 | Continue: announce result, route by outcome | Support |
| 4 | `schedule_technician_visit` | 4 | Dial-out: arranges callback for tech dispatch | Support |
| 5 | `upgrade_plan_inquiry` | 3 | Continue: collects desired plan, generates lead | Sales |
| 6 | `collect_new_line_lead` | 3 | Continue: home/business, address, callback time | Sales |
| 7 | `submit_lead_to_crm` | 2 | API: posts lead | Sales |
| 8 | `general_inquiry` | 3 | Continue: catch-all | Both |
| 9 | `transfer_to_human` | 1 | Layer to retention/billing queue | Both |

This is the largest synthesized bot (9 intents) — chosen to demonstrate that v1 schema scales to that size cleanly, and to show the chained-RT=2 pattern where diagnostic results drive branching.

##### Transition graph (key paths)

```
[start] ──→ verify_subscription      (Order 1)
       ──→ collect_new_line_lead     (Order 2, prospect path)
       ──→ general_inquiry           (Order 3)
       ──→ transfer_to_human         (Order 4)

verify_subscription ──→ run_line_diagnostic    (Order 1, technical issue)
                    ──→ upgrade_plan_inquiry    (Order 2, sales)
                    ──→ transfer_to_human       (Order 3)

run_line_diagnostic ──→ report_diagnostic_result (Order 1)
                    ──→ transfer_to_human         (Order 2, fallback)

report_diagnostic_result ──→ schedule_technician_visit (Order 1, if line down)
                         ──→ transfer_to_human          (Order 2, complex issue)
                         ──→ general_inquiry            (Order 3, if resolved)

schedule_technician_visit ──→ (none, terminal)

upgrade_plan_inquiry ──→ submit_lead_to_crm     (Order 1)
                     ──→ transfer_to_human       (Order 2)

collect_new_line_lead ──→ submit_lead_to_crm    (Order 1)
                      ──→ transfer_to_human      (Order 2)

submit_lead_to_crm ──→ transfer_to_human (Order 1, "agent will call you")

general_inquiry ──→ transfer_to_human (Order 1)
```

##### Annotated intent: `report_diagnostic_result` (RT=3, dotted-path branching)

This intent demonstrates **outcome-driven routing in `intentInstructions`** based on dotted-path response data from the previous RT=2.

```
IntentParameters: []

IntentResponces:
  ResponseTypeId: 3
  Configuration:
    announcement: |
      בדקתי את הקו: {{diagnostic.summary_he}}.
      רמת אות: {{diagnostic.signal_level}} dB. סטטוס: {{diagnostic.status_he}}.
    intentInstructions: |
      POST-EXECUTION ROUTING
      Branch by {{diagnostic.status}}:

      IF {{diagnostic.status}} == "down":
        - הציעי תור טכנאי: schedule_technician_visit.
        - הסבירי שזה דורש ביקור פיזי, לא ניתן לתקן מרחוק.

      IF {{diagnostic.status}} == "degraded":
        - הציעי restart_modem (לא קיים בגרסה הזו) או בקרי טכני.
        - אם הלקוח מאשר ביקור: schedule_technician_visit.
        - אחרת: transfer_to_human.

      IF {{diagnostic.status}} == "ok":
        - הסבירי שהקו נראה תקין מהצד שלנו.
        - אם הלקוח עדיין חווה בעיה: transfer_to_human.
        - אם פתור: סיימי בנימוס.

      IRON RULE: לא להתחייב על ETA לטכנאי בשיחה הזו.
      schedule_technician_visit הוא להחזרת שיחה לתיאום, לא לתיאום עצמו.
```

This pattern — natural-language branching on response data inside `intentInstructions` — is the v1 substitute for structural condition gating (`[v2]`). It works because the LLM has the resolved Mustache values in context after the API call.

##### Compact view: remaining 8 intents

```
verify_subscription (RT=2): mirrors insurance broker's verify_customer_identity.

run_line_diagnostic (RT=2): triggers diagnostic, longer api_silence_behaviour
  (silence_duration=10, loops=6 — diagnostics are slow).

schedule_technician_visit (RT=4): callback to caller_id.

upgrade_plan_inquiry (RT=3): collects desired plan name, routes to submit_lead_to_crm.

collect_new_line_lead (RT=3): collects line_type (ENUM: home/business),
  address (STRING), preferred_callback_time (ENUM).

submit_lead_to_crm (RT=2): POSTs lead, returns lead_id.

general_inquiry (RT=3): catch-all.

transfer_to_human (RT=1): layer <retention_billing_layer>.
```

---

### §14.2 — Standalone Intent Recipes (Pattern Lens)

The full bots in §14.1 show how intents compose. This section shows individual intents in isolation — patterns that don't fit any of the five bots cleanly but that the generator should know how to produce. Each recipe is a complete intent definition, ready to be dropped into a bot context where appropriate.

Recipes are grouped by `ResponseTypeId`. Each recipe states **when to use it**, shows the full configuration, and notes any **constraints** — what must exist elsewhere in the bot for the recipe to work.

#### §14.2.1 — RT=2 Recipes (API Calls)

##### Recipe R-1: `validate_email_otp` — Send-and-verify pattern

**When to use.** Two-step email verification: this intent sends the OTP; a second intent (R-2 below) verifies what the caller types back.

**Constraint.** Requires a paired downstream intent that collects and validates the code (R-2). Requires a CRM/auth API capable of OTP issuance.

```
Name: "שליחת קוד אימות לאימייל"
IntentToolName: "send_email_otp"
Description: "שליחת קוד אימות חד-פעמי לכתובת המייל של הלקוח."

IntentParameters:
  - Name: "customer_email"
    ParameterTypeId: 1                       # STRING
    IsRequired: true
    CollectionOrder: 1
    Description: "כתובת אימייל מלאה"

IntentConfig.prompts.validationPrompt: |
  EMAIL COLLECTION
  1. בקשי את כתובת המייל.
  2. חזרי על הכתובת לאישור (אות אחרי אות אם ארוכה).
  3. ודאי קיום @ ונקודה.
  IRON RULE: לא לשלוח OTP ללא אישור הלקוח על הכתובת.

IntentResponces:
  ResponseTypeId: 2
  Configuration:
    url: "https://api.example.com/auth/otp/issue"
    method: "POST"
    headers:
      Authorization: "Bearer {{ENV.API_TOKEN}}"
    body:
      email: "{{customer_email}}"
      purpose: "voice_verification"
    apiResponseAnnouncement: "שלחתי את הקוד. תוכל/י לקרוא לי אותו?"
    fail_output: "לא הצלחתי לשלוח את הקוד. אעבירך לנציג."
    function_output: |
      Response { issued: bool, otp_id: string }.
      Save otp_id in context — needed by verify_email_otp downstream.
    api_silence_behaviour:
      silence_duration: 5
      silence_loops: 3
      silence_sentence: "רגע, שולחת..."
      silence_ending_sentence: "השרת איטי, אעבירך לנציג."
      intent: <transfer_to_human IntentId>
```

##### Recipe R-2: `verify_email_otp` — Code-validation pattern

**When to use.** Pairs with R-1. Collects the 6-digit code the caller received and validates against the OTP service.

**Constraint.** Must execute after R-1 in the same call (relies on `{{otp_id}}` from context).

```
Name: "אימות קוד OTP"
IntentToolName: "verify_email_otp"
Description: "וידוא הקוד שהלקוח קיבל למייל."

IntentParameters:
  - Name: "otp_code"
    ParameterTypeId: 1                       # STRING (6 digits)
    IsRequired: true
    CollectionOrder: 1
    Description: "קוד בן 6 ספרות מהמייל"

IntentConfig.prompts.validationPrompt: |
  OTP COLLECTION
  1. בקשי את הקוד בן 6 ספרות.
  2. חזרי על הקוד ספרה ספרה.
  3. אשרי עם הלקוח.
  IRON RULE: 6 ספרות בדיוק. אם פחות/יותר — בקשי שוב פעם אחת.

IntentResponces:
  ResponseTypeId: 2
  Configuration:
    url: "https://api.example.com/auth/otp/verify"
    method: "POST"
    headers:
      Authorization: "Bearer {{ENV.API_TOKEN}}"
    body:
      otp_id: "{{otp_id}}"
      code: "{{otp_code}}"
    apiResponseAnnouncement: "אומת. ממשיכים."
    fail_output: "הקוד שגוי או פג תוקף. אעבירך לנציג."
    function_output: |
      Response { verified: bool }.
      If verified=true, the customer is now authenticated.
      Subsequent intents may rely on this state.
    api_silence_behaviour:
      silence_duration: 4
      silence_loops: 3
      silence_sentence: "מאמתת..."
      silence_ending_sentence: "אעבירך לנציג."
      intent: <transfer_to_human IntentId>
```

##### Recipe R-3: `lookup_with_auth` — Authenticated GET with dotted-path response

**When to use.** Read-only lookup against an authenticated REST endpoint. Returns nested JSON; announcement uses dotted paths.

**Constraint.** Requires the customer to be verified upstream (otp pair, identity check, etc.). The `Authorization` header references an env-supplied token.

```
Name: "Lookup Order Details"
IntentToolName: "lookup_order_details"

IntentParameters:
  - Name: "order_number"
    ParameterTypeId: 1
    IsRequired: true
    CollectionOrder: 1

IntentResponces:
  ResponseTypeId: 2
  Configuration:
    url: "https://api.example.com/orders/{{order_number}}"
    method: "GET"
    headers:
      Authorization: "Bearer {{ENV.API_TOKEN}}"
    body: {}
    apiResponseAnnouncement: |
      Order {{order_number}}: status is {{response.order.status}},
      placed on {{response.order.placed_at}}.
      It contains {{response.order.line_items.length}} items
      shipping to {{response.order.shipping.city}}.
    fail_output: "I couldn't find that order. Let me transfer you."
    function_output: |
      Response: { order: { status, placed_at, line_items[], shipping: {...}, total } }
      All fields available downstream via {{response.order.*}} OR {{order.*}}.
    api_silence_behaviour:
      silence_duration: 5
      silence_loops: 4
      silence_sentence: "Looking up your order..."
      silence_ending_sentence: "System is slow, transferring you."
      intent: <transfer_to_human IntentId>
```

**Note on URL templating.** The `{{order_number}}` substitution in the URL itself (not the body) is platform-dependent. Observed in samples only as body or header values; URL-path templating may behave differently. v1 generators should prefer query/body parameters over URL-path parameters; flag URL-path Mustache as `[INFERRED]` to the user.

##### Recipe R-4: `submit_form_data` — Multi-slot POST with structured body

**When to use.** Lead capture, contact-form submission, ticket creation. Multiple slots collected, all sent in one POST.

```
Name: "Submit Contact Form"
IntentToolName: "submit_contact_form"

IntentParameters:
  - Name: "full_name"
    ParameterTypeId: 1
    IsRequired: true
    CollectionOrder: 1
  - Name: "company_name"
    ParameterTypeId: 1
    IsRequired: false
    CollectionOrder: 2
  - Name: "phone"
    ParameterTypeId: 10                      # PHONE
    IsRequired: true
    CollectionOrder: 3
  - Name: "inquiry_topic"
    ParameterTypeId: 19                      # ENUM
    IsRequired: true
    CollectionOrder: 4
    OptionList:
      - { Value: "sales",        Label: "Sales inquiry" }
      - { Value: "support",      Label: "Technical support" }
      - { Value: "partnership",  Label: "Partnership" }

IntentConfig.prompts.validationPrompt: |
  FORM COLLECTION (4 slots, in order)
  1. Full name. Repeat back to confirm.
  2. Company (optional — skip if caller has none).
  3. Phone — read back digits.
  4. Topic — present 3 options, get confirmation.

  IRON RULE: collect in order. Do NOT skip required slots.

IntentResponces:
  ResponseTypeId: 2
  Configuration:
    url: "https://crm.example.com/leads"
    method: "POST"
    headers: { Authorization: "Bearer {{ENV.CRM_TOKEN}}" }
    body:
      name: "{{full_name}}"
      company: "{{company_name}}"
      phone: "{{phone}}"
      topic: "{{inquiry_topic}}"
      source: "voice_bot"
    apiResponseAnnouncement: "Thanks! Your reference number is {{response.lead_id}}. Someone will call you back."
    fail_output: "I couldn't save your details just now. Let me transfer you."
    api_silence_behaviour: { ...standard pattern, see R-1 ... }
```

#### §14.2.2 — RT=3 Recipes (Continue)

##### Recipe R-5: `collect_explicit_consent` — BOOLEAN with verbal confirmation

**When to use.** Before recording, before sharing data, before any action with legal/compliance significance. The bot must have clear verbal "yes" — not assumed consent.

**Constraint.** Persona must mention this consent step explicitly so the LLM doesn't treat it as a bypass-able formality.

```
Name: "אישור הקלטה"
IntentToolName: "collect_recording_consent"

IntentParameters:
  - Name: "recording_consent"
    ParameterTypeId: 16                      # BOOLEAN
    IsRequired: true
    CollectionOrder: 1
    Description: "האם הלקוח מאשר הקלטה? כן/לא."

IntentConfig.prompts.validationPrompt: |
  CONSENT COLLECTION
  1. אמרי בדיוק: "השיחה תוקלט לצורכי בקרת איכות. האם זה בסדר?"
  2. הקשיבי לתשובה.
  3. אישור מילולי ברור = true. כל דבר אחר = false.

  IRON RULES:
  - "כן", "אישרתי", "בסדר", "אין בעיה" -> true.
  - "לא", "לא רוצה", "אני לא מסכים" -> false.
  - שתיקה, "אולי", "תלוי" -> שאלי שוב פעם אחת.
  - בפעם השנייה ללא אישור ברור -> שמרי false ותעבירי לנציג.
  - אסור להניח אישור.

IntentResponces:
  ResponseTypeId: 3
  Configuration:
    announcement: ""    # silent — the validationPrompt already handled it
    intentInstructions: |
      POST-CONSENT
      IF {{recording_consent}} == true:
        - המשיכי לintent הבא בזרימה.
      IF {{recording_consent}} == false:
        - אמרי "הבנתי, מעבירה לנציג."
        - transfer_to_human.

      IRON RULE: לעולם לא להמשיך תהליך מלא ללא consent=true.
    response_success: ""
```

##### Recipe R-6: `select_from_dynamic_list` — ENUM with options from upstream API

**When to use.** Caller chooses from a list returned by a previous RT=2 call (pickup points, available slots, search results).

**Constraint.** The upstream RT=2 must populate a known context key (e.g., `{{available_slots}}`). v1 emits empty `OptionList` and relies on `validationPrompt` for option enumeration.

```
Name: "בחירת אפשרות מרשימה"
IntentToolName: "select_pickup_point"

IntentParameters:
  - Name: "selected_id"
    ParameterTypeId: 19                      # ENUM
    IsRequired: true
    CollectionOrder: 1
    OptionList: []                           # dynamic — flag [v2] for proper support
    Description: |
      The caller picks one option from {{available_slots}} (returned by upstream API).
      Save the chosen entry's slot_id field.

IntentConfig.prompts.validationPrompt: |
  DYNAMIC SELECTION
  1. הציעי את האפשרויות שהתקבלו: {{available_slots}}.
     צורת קריאה: "1. {{available_slots.0.display}}, 2. {{available_slots.1.display}}, ..."
  2. הקשיבי לבחירה.
  3. הלקוח יכול לבחור במספר ("הראשון") או בתיאור ("השני, ברחוב הרצל").
  4. שמרי {{selected_id}} = הערך של slot_id מהאפשרות שנבחרה.
  5. חזרי על הבחירה לאישור.

  IRON RULES:
  - אם הלקוח לא בטוח, חזרי על הרשימה פעם אחת.
  - אם בחירה לא ברורה גם בפעם השנייה — transfer_to_human.
  - לעולם אל תבחרי ברירת מחדל בעצמך.

IntentResponces:
  ResponseTypeId: 3
  Configuration:
    announcement: "מעולה, בחרת ב-{{selected_display}}."
    intentInstructions: |
      POST-SELECTION
      Selection saved as {{selected_id}}.
      Proceed to next intent in flow.
    response_success: ""
```

**Critical limitation.** Until conditional `IntentCondition` schema is supported (`[v2]`), the LLM determines option-validity by reading `validationPrompt`. The `OptionList` array is structurally empty, so the platform cannot enforce constraint at the parameter level. This is the most common case where v1 leans on natural-language enforcement.

##### Recipe R-7: `multi_step_pii_collection` — Ordered slots with cross-validation

**When to use.** Identity collection where multiple fields must be cross-validated against each other (e.g., national ID checksum, name matches a record, address matches zip).

```
Name: "Collect Identity Details"
IntentToolName: "collect_identity_details"

IntentParameters:
  - Name: "national_id"
    ParameterTypeId: 1
    IsRequired: true
    CollectionOrder: 1
  - Name: "date_of_birth"
    ParameterTypeId: 1                       # STRING (no DATE type yet — [v2])
    IsRequired: true
    CollectionOrder: 2
  - Name: "full_name"
    ParameterTypeId: 1
    IsRequired: true
    CollectionOrder: 3

IntentConfig.prompts.validationPrompt: |
  IDENTITY COLLECTION (cross-validated)
  1. National ID — read back digit by digit. Check format (9 digits).
  2. Date of birth — confirm format DD/MM/YYYY.
  3. Full name — confirm exact spelling.

  CROSS-VALIDATION (must run before completing):
  - All three values must be self-consistent.
  - If anything seems off, ask the caller to repeat the suspicious field.
  - Do NOT proceed if any field looks like a typo.

  IRON RULE: never accept a partial set. All three or none.

IntentResponces:
  ResponseTypeId: 3
  Configuration:
    announcement: "Got it. Let me check your details."
    intentInstructions: |
      POST-COLLECTION
      All three slots collected. Move to verify_identity (RT=2)
      to validate against the customer DB.
```

##### Recipe R-8: `confirm_destructive_action` — Re-prompt before irreversible action

**When to use.** Cancellation, deletion, return-finalization, anything the customer can't undo. Single-confirmation is too easy to misclick verbally.

```
Name: "Confirm Cancellation"
IntentToolName: "confirm_cancellation"

IntentParameters:
  - Name: "cancellation_confirmed"
    ParameterTypeId: 16                      # BOOLEAN
    IsRequired: true
    CollectionOrder: 1
    Description: "Caller has explicitly confirmed cancellation, twice."

IntentConfig.prompts.validationPrompt: |
  TWO-STEP CONFIRMATION
  Step 1: "I want to make sure — you'd like to cancel order {{order_number}}.
           Is that correct?"
  Wait for clear "yes."

  Step 2: "Just to confirm one more time: this cancellation cannot be undone
           and a refund will take 5-10 business days. Do you still want to proceed?"
  Wait for clear "yes" again.

  IRON RULES:
  - Both steps must yield clear "yes."
  - Any hesitation, "maybe," "let me think" -> save false, route to transfer_to_human.
  - Do NOT save true on a single "yes."

IntentResponces:
  ResponseTypeId: 3
  Configuration:
    announcement: ""
    intentInstructions: |
      POST-CONFIRMATION
      IF {{cancellation_confirmed}} == true:
        - Proceed to execute_cancellation (RT=2 API call).
      IF false:
        - "Understood, I won't cancel anything. Transferring you to support."
        - transfer_to_human.
```

#### §14.2.3 — RT=1 Recipes (Layer Transfer)

##### Recipe R-9: `escalate_with_context` — Pass collected context to the human

**When to use.** Most common RT=1 pattern. Caller is being transferred; the human agent should know what's already been collected so the caller doesn't re-explain.

**Constraint.** The human-side queue/CTI must support context handoff (typically via SIP headers, screen-pop integration). Whether `announcement` actually carries to the agent is platform-specific; the **value of being structured here** is that the verbal handoff to the **caller** is cleanly stated.

```
Name: "Transfer to Support with Context"
IntentToolName: "transfer_to_support_with_context"
Description: "Hand off to a human agent, preserving conversation context."

IntentResponces:
  ResponseTypeId: 1
  Configuration:
    layer: <support_queue_layer_id>          # placeholder
    announcement: |
      I'm transferring you to a support agent.
      They'll have your order number {{order_number}} and the details we discussed.
      One moment please.
    intentLoadingAnnouncement: "Transferring..."
```

##### Recipe R-10: `transfer_to_specialized_queue` — Different layer than the default

**When to use.** Calls with specific subject matter that should bypass general queue (billing, fraud, retention).

```
Name: "Transfer to Billing Queue"
IntentToolName: "transfer_to_billing"
Description: "Hand off specifically to the billing team."

IntentResponces:
  ResponseTypeId: 1
  Configuration:
    layer: <billing_queue_layer_id>
    announcement: "I'll connect you to billing. Hold on please."
    intentLoadingAnnouncement: "מעבירה לחיוב..."
```

**Note.** A bot can have multiple RT=1 intents going to different layers. They're distinct intents in `intents[]` and `intentRelations[]`, not a single intent with branching. The LLM picks the right one based on conversation context per `intentRelations[]` and per-intent `intentInstructions` of the origin.

##### Recipe R-11: `silent_voicemail_handoff` — Minimal-prompt transfer

**When to use.** After-hours, voicemail box, or pre-recorded queue with its own announcement. The bot says minimum, transfer is silent-ish.

```
Name: "Transfer to Voicemail"
IntentToolName: "transfer_to_voicemail"

IntentResponces:
  ResponseTypeId: 1
  Configuration:
    layer: <voicemail_layer_id>
    announcement: "Transferring you now."
    intentLoadingAnnouncement: ""             # empty intentional — voicemail starts immediately
```

#### §14.2.4 — RT=4 Recipes (Dial-Out)

##### Recipe R-12: `callback_to_caller` — Use caller_id system variable

**When to use.** Caller wants a callback; they're already calling from the right number, no need to re-collect.

```
Name: "Schedule Callback"
IntentToolName: "schedule_callback"

IntentParameters:
  - Name: "preferred_window"
    ParameterTypeId: 19
    IsRequired: true
    CollectionOrder: 1
    OptionList:
      - { Value: "asap",       Label: "As soon as possible" }
      - { Value: "in_one_hour", Label: "In one hour" }
      - { Value: "this_evening", Label: "This evening" }

IntentResponces:
  ResponseTypeId: 4
  Configuration:
    phone3: "{{caller_id}}"
    parameter_phone: "caller_id"
    NEXT_VO_ID: <outbound_VO>                 # placeholder
    MAX_DIAL_DURATION: 60
    selectdial_option: "auto_callback"
    record: true
    announcement: "Got it. We'll call you back {{preferred_window}}."
    intentLoadingAnnouncement: ""
```

##### Recipe R-13: `callback_to_provided_number` — Use a slot-collected number

**When to use.** Caller is calling on someone else's behalf, or wants the callback to a different number than their current call.

```
Name: "Callback to Different Number"
IntentToolName: "callback_to_different_number"

IntentParameters:
  - Name: "callback_phone"
    ParameterTypeId: 10                      # PHONE
    IsRequired: true
    CollectionOrder: 1
    Description: "The phone number to call back, including area code."
  - Name: "preferred_window"
    ParameterTypeId: 19
    IsRequired: true
    CollectionOrder: 2
    OptionList:
      - { Value: "asap",        Label: "ASAP" }
      - { Value: "in_one_hour", Label: "In one hour" }
      - { Value: "this_evening", Label: "This evening" }

IntentConfig.prompts.validationPrompt: |
  CALLBACK NUMBER COLLECTION
  1. Ask for callback number including area code.
  2. Read each digit back.
  3. Confirm with caller.

  IRON RULE: do NOT use {{caller_id}} as fallback. Caller explicitly chose
  to provide a different number — honor that.

IntentResponces:
  ResponseTypeId: 4
  Configuration:
    phone3: "{{callback_phone}}"
    parameter_phone: "callback_phone"
    NEXT_VO_ID: <outbound_VO>
    MAX_DIAL_DURATION: 60
    selectdial_option: "manual_callback"
    record: true
    announcement: "Calling {{callback_phone}} {{preferred_window}}."
    intentLoadingAnnouncement: "Dialing..."
```

##### Recipe R-14: `conference_with_third_party` — RT=4 with record=true

**When to use.** Bot needs to bring in a third party (translator, supervisor, partner system) while keeping the caller on the line. Less common; included for completeness.

```
Name: "Conference Third Party"
IntentToolName: "conference_third_party"

IntentParameters:
  - Name: "third_party_phone"
    ParameterTypeId: 10
    IsRequired: true
    CollectionOrder: 1

IntentResponces:
  ResponseTypeId: 4
  Configuration:
    phone3: "{{third_party_phone}}"
    parameter_phone: "third_party_phone"
    NEXT_VO_ID: <conference_VO>
    MAX_DIAL_DURATION: 90
    selectdial_option: "conference_mode"
    record: true
    announcement: "Bringing them on now."
    intentLoadingAnnouncement: "Connecting..."
```

**v1 caveat.** RT=4 with conference mode is observed in schema only by inference — neither sample uses it. v1 generators should treat this recipe as `[INFERRED]` and warn the user that production validation is needed before deploy.

---

### §14.3 — Anti-Patterns (Failure Modes)

The generator must refuse to produce these patterns; downstream skills should detect and flag them.

#### §14.3.1 — Bad Persona — Vague and Generic

```
BAD:
  persona: "You are a helpful assistant."
```

Why bad: no identity, no language, no company context, no tone, no domain. The LLM defaults to generic chatbot behavior, ignores the bot's purpose, code-switches languages mid-call.

```
GOOD:
  persona: "את יובל, נציגת שירות הלקוחות של חברת NC.
            את מדברת רק בעברית, בטון מקצועי, סבלני וחם.
            את עוזרת ללקוחות לקבוע תורי התקנה.
            הימנעי מסלנג, אל תשתמשי באנגלית.
            כשאת לא בטוחה, את שואלת שוב, לא ניחוש."
```

#### §14.3.2 — Bad Intent Instructions — Free Prose Instead of Routines

```
BAD (free prose):
  intentInstructions: "After the caller chooses a slot, just confirm
                       it for them and tell them they're booked.
                       Be helpful and friendly throughout."
```

Why bad: no structure, no decision points, no fallbacks, no anchors. The LLM has nothing concrete to follow; behavior drifts.

```
GOOD (Conversation Routines style):
  intentInstructions:
    "POST-CONFIRMATION BEHAVIOR
     1. Confirm the slot back to the caller using the exact time format.
     2. State the address that's been booked.
     3. Tell them they'll receive an SMS confirmation.

     IF caller asks to change the slot:
       - Apologize, transfer to reschedule_existing intent.

     IF caller asks unrelated questions:
       - Answer briefly only if it's about the appointment itself.
       - For anything else, transfer to general_inquiry.

     IRON RULE: do NOT discuss pricing, billing, or technical issues.
     Transfer to human for those."
```

#### §14.3.3 — Bad Slot Definition — Missing Validation Guidance

```
BAD:
  IntentParameters: [
    {
      Name: "phone",
      Description: "the caller's phone",
      ParameterTypeId: 1,        ← STRING, but it's a phone
      IsRequired: true,
      ValidationRules: {},
      ValidationPattern: null
    }
  ]
  validationPrompt: ""           ← empty
```

Why bad: STRING type for phone, no validation prompt. The LLM accepts "my phone" as the value. Garbage in.

```
GOOD:
  IntentParameters: [
    {
      Name: "customer_phone",
      Description: "מספר טלפון של הלקוח (10 ספרות, מתחיל ב-05 או 02-09)",
      ParameterTypeId: 10,       ← PHONE
      IsRequired: true,
      CollectionOrder: 1
    }
  ]
  validationPrompt:
    "1. Ask for phone number.
     2. Repeat the digits back.
     3. Confirm with caller.
     4. IRON RULE: must be 10 digits. If shorter or longer, ask again.
        Do NOT accept '050-1234567' format with dashes — strip them silently."
```

#### §14.3.4 — Bad Transition Graph — Missing Fallbacks

```
BAD: validate_customer_address → get_available_slots (only option)
```

Why bad: if validation fails or caller wants out, no escape. Caller is stuck or call drops without handoff.

```
GOOD: validate_customer_address → get_available_slots (Order 1, success path)
                                 → transfer_to_human   (Order 2, escape hatch)
```

**Iron rule for v1:** every non-terminal intent MUST have at least one transition row pointing to an escalation intent (typically RT=1 transfer_to_human). Generator enforces this.

#### §14.3.5 — Bad Mustache — Referencing Slots Before They're Collected

```
BAD:
  Intent 1 (collects nothing yet):
    announcement: "שלום {{customer_name}}, איך אני יכולה לעזור?"
                                ↑ never collected — empty/undefined at runtime
```

Why bad: variable resolves to empty string or `undefined`, bot says broken sentence.

```
GOOD:
  Intent 1: "שלום! איך אני יכולה לעזור היום?"
            (collects customer_name)
  Intent 2: "תודה {{customer_name}}, אני מטפלת..."
            (now safe — name was collected upstream)
```

**Iron rule for v1:** generator validates that every Mustache slot variable was either collected by an *earlier* intent in the flow OR is in the system-variable whitelist OR is a dotted API path inside an RT=2 intent.

#### §14.3.6 — Bad RT=2 — No `api_silence_behaviour`

```
BAD:
  ResponseTypeId: 2
  Configuration:
    url: "...connector.center..."
    method: "POST"
    apiResponseAnnouncement: "..."
    # api_silence_behaviour MISSING
  apiSilenceRelations: []  # also missing the registry entry
```

Why bad: API takes 8 seconds, bot goes silent, caller hangs up.

```
GOOD: every RT=2 intent has both the embedded api_silence_behaviour AND the apiSilenceRelations[] registry entry, with identical Configuration content.
```

#### §14.3.7 — Bad Persona — Overpromising Capabilities

```
BAD:
  persona: "...You can do anything: book appointments, check accounts,
            transfer money, look up medical records, give legal advice..."
```

Why bad: caller asks for any of those, bot tries, fails or hallucinates. The persona must reflect ONLY the intents actually built.

```
GOOD:
  persona: "...Your job is specifically to help schedule installation
            appointments. For anything else — billing, technical issues,
            account changes — you transfer to a human."
```

**Iron rule for v1:** persona's claimed capabilities must be a strict subset of the actual intent set.

#### §14.3.8 — Bad Naming — Inconsistent Style

```
BAD:
  intents: [
    { IntentToolName: "validateAddress" },        ← camelCase
    { IntentToolName: "get-slots" },              ← kebab-case
    { IntentToolName: "Confirm Appointment" },    ← spaces, Title Case
    { IntentToolName: "transferHuman" }           ← inconsistent
  ]
```

Why bad: the LLM's tools list becomes inconsistent, intent recognition degrades.

```
GOOD: all snake_case verb_object — validate_address, get_slots, confirm_appointment, transfer_to_human
```

#### §14.3.9 — Misplacement — Voice/Channel Concerns Inside `persona` (Global)

```
BAD:
  prompts.persona: "את יובל מחברת NC. את עוזרת לקבוע תורי התקנה.
                    דברי לאט וברור, הקפידי על הגייה נכונה של שמות רחובות,
                    הימנעי מהפסקות ארוכות, אם הלקוח קוטע אותך —
                    עצרי מיד והקשיבי."
                    ↑ pacing, pronunciation, interruption handling — voice-only concerns
```

Why bad: this content is in **position 1** of the assembled prompt (Global), so it's active in chat too. In the chat channel, "speak slowly" and "if the user interrupts" are nonsense. The LLM tries to honor them, behavior degrades. Worse: when this same bot is later deployed on chat, no one notices the voice-isms in the persona until calls start sounding off.

```
GOOD:
  prompts.persona: "את יובל מחברת NC. את עוזרת לקבוע תורי התקנה.
                    טון מקצועי, חם וסבלני. עברית בלבד."
                    ↑ identity, role, tone, language — channel-agnostic

  prompts.voiceInstructions: "דברי לאט וברור. הקפידי על הגייה של שמות רחובות.
                              אם הלקוח קוטע — עצרי מיד והקשיבי.
                              הימנעי מהפסקות ארוכות."
                              ↑ pacing, pronunciation, interruption handling
```

**Field-purpose rule:** `persona` is for **identity that survives both channels**. `voiceInstructions` and `chatInstructions` are for **how the identity expresses itself in that medium**.

#### §14.3.10 — Misplacement — Per-Intent Instructions Inside `persona`

```
BAD:
  prompts.persona: "...You schedule installation appointments. When validating
                    an address, always repeat it back. After getting available
                    slots, present them in the order returned by the API.
                    For confirmation, state the slot time AND the address..."
                    ↑ per-intent procedural logic in the global field
```

Why bad: §3 dictates that `persona` is in **every** assembled prompt. That logic runs even when `validate_customer_address` isn't the active intent. It also runs *during* `validate_customer_address`, where the **per-intent** `intentInstructions` is the right home — and now there's conflicting guidance in two positions of the assembled prompt. The LLM can't tell which is canonical.

```
GOOD:
  prompts.persona:                     ← global, channel-agnostic, intent-agnostic
    "Identity, role, language, tone."

  intents[validate_address].IntentResponces.Configuration.intentInstructions:
    "POST-EXECUTION: confirm address back, then proceed to slot fetch."

  intents[get_slots].IntentResponces.Configuration.intentInstructions:
    "POST-EXECUTION: present slots in order, ask caller to choose."
```

**Field-purpose rule:** `persona` is for **what's true the entire call**. Per-intent procedure goes in **per-intent** `intentInstructions`.

#### §14.3.11 — Misplacement — Bot-Level Intent Disambiguation Inside Per-Intent Fields

The mirror image of §14.3.10. Bot-level orienting logic ends up inside an intent.

```
BAD:
  intents[validate_address].IntentResponces.Configuration.intentInstructions:
    "When the caller first reaches us, figure out if they want to schedule
     or reschedule. If schedule, validate the address. If reschedule,
     transfer to the reschedule intent..."
     ↑ pre-intent disambiguation logic, but living inside an intent that's
       already past the disambiguation step
```

Why bad: by the time `validate_address` is the active intent, disambiguation has already happened — that's why this intent fired. This text is dead code. Worse, the **actual** disambiguation logic might be missing from `prompts.intentInstructions` (the bot-level Opening Instructions field) where it belongs. So at the start of the call, the bot has no orienting guidance at all.

```
GOOD:
  prompts.intentInstructions (BOT-LEVEL):
    "OPENING BEHAVIOR
     1. Greet briefly.
     2. Ask the caller what they need.
     3. Route: scheduling → validate_address; rescheduling → reschedule_existing;
        general questions → general_inquiry; anything unclear → ask once more,
        then transfer to human."

  intents[validate_address].IntentResponces.Configuration.intentInstructions:
    "POST-EXECUTION behavior only — the routing already happened."
```

**Field-purpose rule:** `prompts.intentInstructions` (bot-level) is for **before any intent fires**. `Configuration.intentInstructions` (per-intent) is for **after this specific intent has fired**. They're never both active in the same assembled prompt — they swap (§3).

#### §14.3.12 — Misplacement — Slot-Specific Validation Inside `intentInstructions`

```
BAD:
  intents[collect_phone].IntentResponces.Configuration.intentInstructions:
    "After collecting the phone number, ensure it's exactly 10 digits.
     Strip dashes silently. If shorter, ask again. Iron rule: never accept
     less than 10 digits..."
     ↑ slot validation logic inside post-execution instructions
```

Why bad: `intentInstructions` is **post-execution** — it runs *after* the intent has completed and slots are collected. By the time this text is active, the phone has already been collected (with whatever validation actually ran). Putting validation rules here means they never fire.

```
GOOD:
  intents[collect_phone].IntentConfig.prompts.validationPrompt:
    "1. Ask for phone number.
     2. Repeat digits back.
     3. IRON RULE: must be exactly 10 digits. Strip dashes silently."

  intents[collect_phone].IntentResponces.Configuration.intentInstructions:
    "POST-EXECUTION: phone is collected. Proceed to next step."
```

**Field-purpose rule:** `validationPrompt` is for **pre-execution slot collection**. `intentInstructions` (per-intent) is for **post-execution behavior**.

#### §14.3.13 — Misplacement — Persistent Policy Inside a Single Intent

```
BAD:
  intents[validate_address].IntentResponces.Configuration.intentInstructions:
    "...Note: we never share customer data with third parties. If the
     caller asks about privacy, refer them to our policy at example.com.
     We are GDPR-compliant. We do not store recordings beyond 30 days..."
     ↑ company-wide policy embedded in one intent
```

Why bad: this policy applies to **every** intent in the bot. Putting it in one intent means it only enters the assembled prompt when that intent is active. In every other intent, the LLM has no idea about the policy. Inconsistent behavior across the call.

Also: the policy is duplicated if you put it in every intent (which is what you'd do to "fix" this naively). The **right** fix is to put policy that's true for the whole call in `persona`.

```
GOOD:
  prompts.persona:
    "...PRIVACY POLICY (applies always):
     - We never share customer data with third parties.
     - GDPR-compliant.
     - Recordings retained 30 days max.
     - For privacy questions, refer to example.com..."

  intents[validate_address].IntentResponces.Configuration.intentInstructions:
    "POST-EXECUTION: address validated. Proceed to slot fetch."
```

**Field-purpose rule:** content true for **the entire call** goes in `persona`. Content true for **after this intent only** goes in per-intent `intentInstructions`.

#### §14.3.14 — The Field-Purpose Cheat Sheet

After §14.3.9–§14.3.13, condensed into a single decision rule the generator and downstream skills should follow:

| If the content is about… | It belongs in… |
|---|---|
| Identity, role, company, tone, language — true for the whole call, channel-agnostic | `prompts.persona` |
| Voice-specific behavior (pacing, pronunciation, interruption, audio cues) | `prompts.voiceInstructions` |
| Chat-specific behavior (formatting, emoji, message length) | `prompts.chatInstructions` |
| What to do **before** any intent fires (greeting, routing, disambiguation) | `prompts.intentInstructions` (bot-level) |
| The first words the caller hears | `prompts.openingAnnouncement` |
| How to collect a specific intent's parameters from the caller | `intents[].IntentConfig.prompts.validationPrompt` |
| How to behave **after** a specific intent has fired | `intents[].IntentResponces.Configuration.intentInstructions` |
| What to say after the intent's main action completes | `Configuration.announcement` (RT=3) / `apiResponseAnnouncement` (RT=2) |
| What to say while the API is processing | `Configuration.intentLoadingAnnouncement` |
| What to say if the API fails | `Configuration.fail_output` |

**The misplacement test:** for any piece of content, ask: *what's the smallest scope this is true for?* Whole call → persona. This channel only → channel instructions. Pre-any-intent → bot-level intentInstructions. This intent's slot collection → validationPrompt. After this intent fires → per-intent intentInstructions. After the API call inside this intent → apiResponseAnnouncement.

If the content's *scope* doesn't match the field's *scope*, it's misplaced.

---

## 15. ID Semantics & Cross-References

The bot JSON has nine integer-ID fields that wire its parts together. v1 generators must handle them consistently. This section is the reference.

### 15.1 — The Nine IDs

| ID | Type | Source | Lives in |
|---|---|---|---|
| `BotID` | int | platform-assigned | top-level + many backreferences |
| `AccountID` | int | user-supplied | top-level |
| `BotVersionId` | int | platform-assigned | `ActiveVersionInfo.BotVersionId` |
| `AIModelConfigID` | int | catalog reference (existing) | top-level + version |
| `AIModelTypeId` | int | catalog reference | inside AiModelConfig |
| `IntentId` | int | platform-assigned | `intents[].IntentId` (and many backreferences) |
| `BotIntentID` | int | platform-assigned | `botIntents[].BotIntentID` |
| `IntentCategoryId` | int | platform-assigned | `intentCategories[].IntentCategoryId` |
| `ParameterId` | int | platform-assigned | `IntentParameters[].ParameterId` |

Plus: `IntentConditionGroupId` for condition groups (always empty in v1) and various backreferences (`BotID` repeated inside collections, `IntentId` referenced from relations, etc.).

### 15.2 — Three Categories of ID

**Category A: User-supplied at generation time.**
`AccountID` only. The user knows the customer account this bot belongs to.

**Category B: Catalog references (existing).**
`AIModelConfigID`, `AIModelTypeId`. These reference platform-managed registries (which model, which model type). The user supplies these from a known catalog or the generator copies them from a baseline export.

**Category C: Generated locally, replaced on import.**
Everything else. The generator emits placeholder integers; the platform's import endpoint reassigns them on insert. The **internal consistency** of placeholders matters; the values themselves don't.

### 15.3 — Placeholder Strategy for v1

Three options. Pick one and apply consistently across the bot.

**Option A — Sequential negative integers.** Use negative numbers (`-1`, `-2`, …) so it's visually obvious they're placeholders and there's no collision risk with real DB IDs.

```
intents[0].IntentId = -1
intents[1].IntentId = -2
intentRelations[0].OriginIntentID = -1
intentRelations[0].NextIntentID = -2
```

**Option B — Sequential positive integers from 1.** Looks like real IDs. Higher collision risk if anything reads the JSON before import.

**Option C — Symbolic strings.** Truly unambiguous. Requires the import endpoint to accept strings or for the Assembler to do a final integer pass before serialization.

```
intents[0].IntentId = "intent:validate_address"
```

**v1 recommendation: Option A.** Simplest, signals placeholder-ness, no ambiguity, and the integer type is preserved (matches the schema's expected `int`).

### 15.4 — Assembler's Cross-Reference Pass

The Assembler step (Skill 3 in the architecture) performs **one cross-reference pass** before emitting the final JSON. Verifies:

1. Every `botIntents[].IntentID` matches an `intents[].IntentId`.
2. Every `intentRelations[].OriginIntentID` and `.NextIntentID` matches an `intents[].IntentId`.
3. Every `apiSilenceRelations[].OriginIntentID` and `.ApiSilenceIntentID` matches an `intents[].IntentId`.
4. Every `intents[].IntentCategoryId` matches an `intentCategories[].IntentCategoryId`.
5. Every RT=2 intent has a corresponding `apiSilenceRelations[]` entry (the pairing rule, §11.2).
6. Every RT=2 intent's `Configuration.api_silence_behaviour` content matches its `apiSilenceRelations[].Configuration` content (the duplication rule, §11.2).
7. Every Mustache slot variable resolves: collected by an earlier intent, or in the system-variable whitelist, or a dotted API path inside an RT=2 intent.

Any failure aborts assembly with a structured error pointing to the offending field path.

### 15.5 — `BotID` and `BotVersionId` Backreferences

These appear inside collections (e.g., `botIntents[].BotID`, `intentCategories[].BotID`, `IntentParameters[].IntentId`). They're denormalized and must match the parent. The Assembler propagates the placeholder value consistently.

---

## 16. Schema Quirks Summary

Consolidated reference of everything that violates clean-design expectations and must be preserved.

| Quirk | Where | Status | Action |
|---|---|---|---|
| `IntentResponces` (typo of "Responses") | every intent | confirmed in source | **preserve** — never autocorrect |
| `intentLoadingAnnouncement` AND `IntentLoadingAnnouncement` | RT=2 Configuration | confirmed both present | **emit both, identical content** |
| `HandlingInstructions: null` | every intent root | always null | **emit `null`** — appears deprecated |
| `SystemPrompt: ""` | `ActiveVersionInfo` | always empty | **emit `""`** — replaced by `AIModelConfig.prompts` |
| Top-level `AiModelConfig` and `ActiveVersionInfo.AIModelConfig` | top + nested | both required | **distinct objects, both must be emitted; `created` payload is duplicated** |
| `AIModelConfig.tools: []` and `AIModelConfig.instructions: ""` | inside AIModelConfig | always empty | **emit empty values** — `[v2]` semantics |
| `IntentScripts: {}` | every intent | always empty | **emit `{}`** — `[v2]` |
| `ValidationRules: {}` | every parameter | always empty | **emit `{}`** — `[v2]` |
| `ValidationPattern: null` | every parameter | always null | **emit `null`** — `[v2]` |
| `IntentConditionList: []` | inside ConditionGroupList | always empty | **emit `[]`** — `[v2]` (the big one) |
| `silenceRelations: []` | top of intentList | always empty | **emit `[]`** — `[v2]` |
| `BotLanguages: []` | bot top-level | always empty | **emit `[]`** — `[OPEN]` |
| `llmDescription: ""` | per-intent | always empty | **emit `""`** — fallback semantics `[OPEN]` |
| `response_success: ""` | RT=2/RT=3 Configuration | observed but empty | **preserve from baseline** |

**Rule for the generator:** when in doubt, emit what the production samples emit, even if it looks redundant or empty. The platform's import endpoint may strictly require these keys to be present.

---

## 17. v2 Roadmap — Schema Gaps

What v1 explicitly does not handle at the **schema level**. Captured here so future work has a concrete list.

This section covers schema-knowledge gaps. The lifecycle roadmap (read/write/update via MCP, autonomous iteration) is in §18.

### 17.1 — High-impact gaps

**G-1 — `IntentCondition` entry inner schema.**
Empty `IntentConditionList[]` in both samples. v2 needs the field shape (operator, operand, variable reference) so the generator can produce intents/transitions gated by runtime values (labels, customer-defined variables). This is the single biggest capability gap — without it, v1 leans entirely on natural-language gating in `intentInstructions`.

**Required to close:** a third example bot with populated conditions, OR the platform's documented schema, OR direct elicitation from the platform team.

**G-2 — Full `ParameterTypeId` catalog.**
Four types observed (1, 10, 16, 19). The ID gaps (2-9, 11-15, 17-18, 20+) imply at least 15 more types — likely candidates: NUMBER, INTEGER, DATE, TIME, DATETIME, EMAIL, URL, ARRAY, OBJECT, CURRENCY, etc.

**v1 fallback:** STRING (PT=1) with natural-language validation. Works but degrades robustness.

**Required to close:** platform's parameter-type catalog dump, or systematic exploration of the parameter UI.

**G-3 — `silenceRelations[]` schema.**
Empty in both samples. Distinct from `apiSilenceRelations[]` per naming. **Inferred role:** per-intent caller-silence handlers, parallel to bot-level `silence_behaviour`. Schema unobserved.

### 17.2 — Medium-impact gaps

**G-4 — `llmDescription` fallback behavior.**
Always empty in samples. Training doc states it overrides `Description` when populated. v1 emits `""` always.

**Required to close:** test on the platform whether empty `llmDescription` falls back to `Description` in the tools list, or produces an empty tool description.

**G-5 — Parameter-level Validation Script storage.**
Training doc lists it as a parameter field. JSON has no clearly matching field at the parameter level (intent-level `validationPrompt` covers all parameters together).

**Required to close:** find a sample with parameter-level validation script populated, or confirm with the platform that this concept exists only at the intent level despite the training doc framing.

**G-6 — `BotLanguages: []` schema.**
Empty in both samples. Likely contains language metadata for multilingual bots; structure unobserved.

### 17.3 — Low-impact gaps (likely deprecated or platform-internal)

**G-7 — `HandlingInstructions: null` at intent root.**
Always null. Training doc doesn't reference it. Probable deprecated field from earlier schema. v1 emits `null`.

**G-8 — `SystemPrompt: ""` at version level.**
Always empty. Replaced in practice by `AIModelConfig.prompts`. Probable legacy field. v1 emits `""`.

**G-9 — `IntentScripts: {}`.**
Always empty. Inferred to be a hook for custom JS/scripting per intent — currently inactive. v1 emits `{}`.

**G-10 — `BotIntentTypeID` enum.**
Only value observed: `1`. Full enum unknown. v1 emits `1`.

**G-11 — `BotStatusId` enum.**
Only value observed: `1`. Full enum unknown. v1 emits `1`.

**G-12 — `BotVersionStatusId` enum.**
Only value observed: `3`. Full enum unknown. v1 emits `3`.

### 17.4 — Out-of-scope for v1 schema (platform concerns)

These are runtime values the user must supply at generation time. The v2 lifecycle roadmap (§18) closes these via MCP read access:

- IVR layer IDs (`layer`, `NEXT_VO_ID`)
- Webhook URLs (`connector.center` artifacts)
- Auth tokens (env-supplied via `{{ENV.*}}` placeholders)
- Account IDs

In v1 these remain user-supplied at generation time; the generator never invents them.

### 17.5 — How to close each gap

| Gap | Cheapest path |
|---|---|
| G-1 (conditions) | Find a production bot with populated conditions, audit its `IntentConditionList[]` |
| G-2 (parameter types) | Get the `ParameterType` catalog dump from the platform DB |
| G-3 (silenceRelations) | Find a production bot with per-intent caller-silence configured |
| G-4 (llmDescription) | Empirical test on platform |
| G-5 (per-param validation) | Find a sample, or confirm absence |
| G-6 (BotLanguages) | Find a multilingual production bot |
| G-7..G-12 | Lower priority — emit observed default until evidence justifies a change |

---

## 18. Lifecycle Roadmap — v1 → v5

Distinct from §17 (schema-knowledge gaps). This section maps the **generator skill's own lifecycle** as it gains capabilities through MCP integration with the Voicenter platform.

**Framing.** The skill remains user-triggered at every stage. There is no autonomous monitoring, no drift detection, no scheduled maintenance, no KB integration in v1–v3. The skill is a tool the user runs; it produces output, the user reviews it, the user accepts or rejects. v5 is where autonomy enters — and only as an explicit, scoped extension once the manual baseline is stable.

### 18.1 — Release Map

| Version | Capability | What it adds | What's still required from the user |
|---|---|---|---|
| **v1** | Generate JSON, manual import | Interview → Bot JSON file | User imports JSON manually; supplies layer IDs, NEXT_VOs, webhook URLs |
| **v2** | MCP read + write | Skill queries platform during interview to resolve layer IDs / NEXT_VOs / AccountIDs / model catalog. Skill deploys generated JSON via MCP. | User triggers each generation/deploy; reviews proposed config |
| **v3** | MCP update | Skill reads an existing deployed bot, accepts modification request, diffs, pushes deltas. Existing bots become editable through the skill. | User explicitly invokes update with intent ("change Yuval's escalation layer"); reviews proposed diff |
| **v4** | *Reserved placeholder* | (Deliberately blank — leaves room for capability that emerges between manual update and autonomous iteration) | — |
| **v5** | Autonomous iteration | Data-set access, self-directed improvement. Bridge into the Mastra Continuous Mode pipeline (M9 of the full Agent Generator project). | User configures policy / approval thresholds; monitors rather than triggers |

### 18.2 — v2 — MCP Read + Write (the foundational integration release)

**Read capability.** Skill 1's interview no longer asks the user "what's your transfer-to-human layer ID?" — it queries the MCP for layers available on the user's account and presents them as choices. Same for NEXT_VO_IDs (RT=4 destinations), AccountID (the user's bot lives under), and the AI model catalog (which model configs exist and can be referenced).

This closes most of §17.4 — the platform values that v1 leaves as user-supplied placeholders become resolvable during generation.

**Write capability.** Skill 3 (Assembler) gains a deploy step. The generated JSON is no longer a file the user imports through the UI — it's pushed via MCP method (`create_bot_from_json` or equivalent). User confirms before push; the skill returns the new `BotID` for reference.

**Why bundled.** Read alone is a modest improvement (auto-fill instead of typing). Read becomes meaningful *because* deploy uses it — auto-resolved layer IDs are layer IDs that work when deployed. Bundling them is one coherent capability jump: "the skill talks to the platform, both for input resolution and for output deployment."

**v2 explicit non-goals:** no monitoring, no autonomous changes, no KB integration, no drift detection. The skill remains entirely user-triggered.

### 18.3 — v3 — MCP Update (incremental edits to deployed bots)

**Capability.** User says: "Update Yuval's escalation layer to the billing queue, and add a new 'check_appointment' intent that lets customers verify upcoming appointments."

The skill:
1. Reads the deployed bot's full JSON state via MCP
2. Loads it into the same intermediate JSON format used by Skills 1–3
3. Surfaces what's changing (the diff, in human-readable form)
4. User confirms
5. Pushes deltas via MCP update method

**Why update earns its own release.** Update has a hard prereq v2 doesn't have: the skill must reliably read full bot state from the platform, not just metadata. It must produce a clean diff (not re-import, which would lose history). It must handle partial updates without breaking unchanged parts of the bot. That's structurally more work than "create new bot," and it touches production data directly.

**v3 explicit non-goals:** still no autonomy. Every update is user-triggered, scoped to what the user asked for, presented as a diff for confirmation. The skill does not propose changes; the user does.

### 18.4 — v4 — Reserved Placeholder

Deliberately blank. Capability boundary between manual update (v3) and autonomous iteration (v5) is hard to predict — leaves space for whatever emerges (e.g., approval-based recommendations, batch updates across bots, multi-version bot management) without forcing premature definition.

Skipping the version number would create later ambiguity ("did v4 ship?"). Holding it open clarifies intent.

### 18.5 — v5 — Autonomous Iteration

**Capability.** The skill gains access to the user's data set (call summaries, transcripts, KPIs) and begins proposing changes proactively. This is the bridge to the Mastra Continuous Mode pipeline (M9 in the full Agent Generator project plan) — drift detection, KCP generation, scheduled review.

In v5, the skill stops being a pure tool and becomes a partial agent: it watches, learns, recommends. Approval flows still gate deployment, but the skill can now *initiate* the conversation about a change rather than only respond to it.

**Out of scope for these documents.** v5's design lives with the full Agent Generator project, not the Bot JSON skill. Captured here only to close the lifecycle narrative.

### 18.6 — Lifecycle non-goals (true through v3)

To prevent scope drift, these are explicitly NOT part of the v1–v3 scope:

- Autonomous monitoring of deployed bots
- Drift detection against call data
- Scheduled or cron-driven maintenance
- KB integration (Voicenter knowledge base, third-party docs)
- Multi-bot orchestration
- Automatic A/B testing or experimentation
- Automatic version bumping

All of these belong to the full Agent Generator pipeline (different project) or to v5 of this skill (an explicit, scoped extension once the manual baseline is stable).

---

*— End of v1 Schema Audit —*

**Document version:** 1.0
**Date:** May 2026
**Sources:** `Yuval.json`, `Refua0_30.json`, *Voicenter Voice Bot Configuration Guide v1.0*
**Open questions:** see §17 (schema gaps) and §18 (lifecycle roadmap)
