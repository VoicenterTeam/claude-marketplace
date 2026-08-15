# Skill 3 stage — Spec-to-wire-format assembly mapping

*Load this at assembly time (Skill 3 §4). It carries the complete field-by-field mapping
from Agent Spec to Bot JSON wire format, the ID placeholder ranges, the per-RT
`Configuration` shapes, the §16 quirk checklist, and the static reference data. SKILL.md
keeps the parse rules, dispatch and anti-list; this file keeps the mechanics.*

*Emission order matters throughout — every table below is ordered to match the production
export. Field order is part of the contract, not a formatting preference.*

## Table of contents

- [4.1 ID placeholder allocation](#41-id-placeholder-allocation)
- [4.2 Top-level wrapper and version envelope](#42-top-level-wrapper-and-version-envelope)
- [4.3 intentList assembly](#43-intentlist-assembly-sections-4--5--six-parallel-collections)
- [4.4 RT-specific IntentResponces.Configuration](#44-rt-specific-intentresponcesconfiguration)
- [4.5 Quirk preservation](#45-quirk-preservation)
- [Appendix A — Doc 1 §16 quirks: complete preservation checklist](#appendix-a--doc-1-16-quirks-complete-preservation-checklist)
- [Appendix D — Static reference data](#appendix-d--static-reference-data-single-source-of-truth)

---

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
| 11 | `PersonaID` | **Added per the `ImportBotFromJSON` contract (`${CLAUDE_PLUGIN_ROOT}/references/voicebot-json-contract.md` R7).** `Persona` is a `bigint NOT NULL` FK on `BotVersion`; a missing/null value makes the proc fall back to the first `Persona` row with `AccountId=0` — if that row doesn't exist on the target server, step 3 fails and produces exactly the "Bot with intents but no BotVersion" symptom this contract exists to prevent. Skill 3 does not rely on the implicit fallback: it always emits the known shared value `3` (`TTSScriptReader`, `AccountId=0`) unless a future spec revision adds an explicit persona-catalog field. Banner DEFAULTS APPLIED note whenever this default is used (i.e. always, in v1). Verified by CHK-25. **Position unverified against a golden production export** (no golden export captured to date includes this field) — Skill 3 appends it as the last key rather than asserting a production-observed slot; re-verify the position once a real export with `PersonaID` is available. |

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

If section 3 reads `[not configured]`: **omit** the entire `silence_behaviour` field from `ActiveVersionInfo.AIModelConfig`. Do not emit it as `null`, do not emit it as `{}`. Customer B's production sample omits it entirely; Skill 3 follows that pattern.

If section 3 has its fields populated: emit them direct field-to-field.

| Wire-format path | Spec source |
|---|---|
| `silence_behaviour.intent` | The `IntentId` of section 3's `silence failover intent:` (the intent to jump to when caller-silence loops are exhausted). Emit as the **first** key of the object (matches production shape). **IMPORT LIMITATION (empirically confirmed 2026-06-23, test bot, dev account):** the Voicenter import procedure remaps negative placeholders in `intents[]` / `botIntents[]` / `intentRelations[]` to real positive IDs, but it does **NOT** remap `silence_behaviour.intent` — a placeholder survives verbatim into the imported bot and the silence forward is blank in the UI until set by hand. Resolution rules (v1.14.0), in priority order: **(1)** if the failover names a **section-4.6 catalog intent** (user-supplied), emit its **real positive `IntentId`** verbatim — it survives import unchanged. **(2)** the normal case — the failover names a **bot-own intent** (the dedicated silence-forwarding intent Skill 1 always creates, or the user-chosen existing flow intent): emit its **negative placeholder** from the cached ID map, and add the MANDATORY banner line: `silence_behaviour.intent is a pre-import placeholder the import procedure does NOT remap — after import, set the silence forward to <display name> in the UI (the target intent is identifiable by IsSilenceIntent: 1)`. **(3)** `-999` + banner only if section 3 is unresolvable. Never emit as a string identifier; never omit when `silence_behaviour` is emitted. *(v1.14.0 removed the pre-v1.14 "substitute canonical system global 19" mechanism — silence forwarding always targets a real, bot-own intent the user chose an outcome for.)* Production proof of the real-id form post-import: an operator export carries `silence_behaviour.intent: 7518`. |
| `silence_behaviour.silence_duration` | Section 3 `silence_duration` |
| `silence_behaviour.silence_loops` | Section 3 `silence_loops` |
| `silence_behaviour.silence_sentence` | Section 3 `silence_sentence` |
| `silence_behaviour.silence_ending_sentence` | Section 3 `silence_ending_sentence` |

The `silence_behaviour.intent` failover is bot-level (caller silence regardless of active intent), distinct from each RT=2 intent's `api_silence_behaviour.intent` (API silence). Both are structural `intent` failovers; `silenceRelations[]` stays `[]` (the bot-level failover lives in this field, not a relations row).

### 4.3 `intentList` assembly (sections 4 + 5 → six parallel collections)

Per Doc 1 §8, `intentList` has six parallel collections wired by integer IDs. Skill 3 builds them from the cached ID map (§4.1) and section 4-5 content.

**Emit the six collections in the sub-section order below** — `intents`, `botIntents`, `intentRelations`, `intentCategories`, `silenceRelations`, `apiSilenceRelations`. Like every other table in this file, the order is contractual. Note that `silenceRelations` is always `[]` and therefore easy to misplace without any check firing: no CHK-NN inspects key order, so a misordered emission still passes all 26 checks and is caught only by byte-comparison against a golden.

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
| `Configuration.layer` | Section 5 "Layer" — the real layer number (fetched from the MCP during Skill 1, §2.4.A), emitted as a **JSON integer, never a quoted string** (see the layer-typing rule below). Defaults to `0` (root layer) when the spec omits it. **No `-999` sentinel for layer** (v1.12.0 — `0` is a valid landing layer, a deliberate exception to fail-loud; see anti-list §"Suppress fail-loud sentinels"). Two layer IDs are portable across accounts and are Skill 1's no-preference defaults (v1.20.1): **`666`** = the built-in hang-up layer, present on every account, for terminals whose outcome is "end the call"; **`0`** = the first layer created on every account, for human-transfer terminals. Skill 3 emits whatever the spec carries — it does not substitute either value — but banner-notes any account-specific layer for post-import verification. |
| `Configuration.announcement` | **Always omitted (v1.14.0 hard rule).** RT=1 never carries an `announcement` key — the farewell lives in the PREVIOUS intent's `intentInstructions` (FP-8 farewell trigger rule; production: every layer-transfer intent has only `intentLoadingAnnouncement`). If a legacy spec supplies one, that is a **check-20 failure**, not an emission choice. |
| `Configuration.intentLoadingAnnouncement` | Section 5 "Loading announcement" verbatim. **Always emitted** for RT=1 — the terminal's only utterance, a short "יום טוב"-style line. |

RT=1 intents do **not** emit `intentInstructions` (post-execution behavior on a terminal intent has no meaning per Doc 1 §11.5).

**Layer and layer-adjacent fields are JSON integers (v1.20.1).** Emit `Configuration.layer`, `dailyLimitLayerId`, `maxDurationLayerId`, `IVRLayerSelect_2` and `NEXT_VO_ID` as bare numbers — `"layer": 666`, never `"layer": "666"`. The `ImportBotFromJSON` contract's §2 Types list enumerates the fields it requires as numbers and **does not name any of these**, so nothing upstream pins them; they are correct today only by construction. The hazard is proximity: `recordAgentCalls` and `realtimeInputConfig.automaticActivityDetection.disabled` are deliberately string-typed (Appendix A rows 17–18) and sit in the same objects, so "these platform flags are strings" is an easy over-generalization when hand-authoring. A quoted layer is an FK the platform cannot resolve — the observed symptom is the UI's layer dropdown rendering the raw ID instead of the layer name (the same symptom a dangling cross-account layer produces, so do not use the dropdown to tell the two apart).

Terminal doctrine (FP-8, v1.14.0) — one RT=1 terminal per outcome, owning its outcome slot, no terminal→anything relations, no `announcement` (farewell on the predecessor) — is validated by CHK-20 (§6).

#### RT=2 — API Call

| Wire-format field | Source |
|---|---|
| `ResponseTypeId` | `2` |
| `IsActive` | `1` (per §16 quirk #15 — required inside every `IntentResponces`) |
| `Configuration.url` | Section 5 "URL"; `<USER_TO_FILL: webhook_url>` if `<UNKNOWN>` |
| `Configuration.method` | Section 5 "Method" (`"POST"` or `"GET"`) |
| `Configuration.headers` | Section 5 "Headers" object; `{}` if not specified |
| `Configuration.body` | Section 5 "Body" object verbatim (Mustache placeholders preserved as written); **key omitted entirely** when the spec declares no `**Body:**` (typical for `GET`). Emitted immediately after `headers` — the position is contractual, and CHK-06's deep-equality key list includes `body`. |
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
| `Configuration.announcement` | Section 5 "Announcement" verbatim; else the section-4 `**Announcement:**` override; else key omitted (see the sourcing note below) |
| `Configuration.intentLoadingAnnouncement` | Section 5 "Loading announcement" verbatim; else the section-4 `**Loading announcement:**` override; else key omitted |
| `Configuration.intentInstructions` | Section 5 "Post-execution intentInstructions" verbatim; else the section-4 `**Post-execution intent instructions:**` override; else `""` (parallel to RT=2/RT=3 §16 convention) |
| `Configuration.response_success` | Section 5 "response_success" object (e.g., `{ "instructions": "<text>" }`); else the section-4 `**Response success:**` override; else `{}` |

**Sourcing note — these four are language content, so section 5 wins.** The other RT=4 rows above are structural and live in section 4's RT-specific block, which is why the whole table used to name section 4 as the source. But `announcement`, `intentLoadingAnnouncement`, `intentInstructions` and `response_success` are Skill 2's output and are normally authored into the intent's **section 5** entry, exactly as they are for RT=1/2/3 — the section-4 labels listed in SKILL.md §3.1 are *optional structural overrides*, not the primary home. Read section 5 first; fall back to the section-4 label only when section 5 has no entry for the field; apply the absent-default only when neither carries it. (Corrected after a v1.20.0 hand-assembly of `examples/sample-spec-detailed.md`, whose `dial_on_call_nurse` carries all four in section 5 and none in section 4.)

**Empty-phone handling.** A spec entry of `""` for `Phone1`, `Phone2`, or `Phone3` is preserved as `""` in the JSON — the dialer's runtime contract is "try in order, skip empties." Do not coerce empty phones to `null` and do not collapse the keys.

### 4.5 Quirk preservation

Walk Appendix A. For every quirk in the table, ensure the assembled wire structure has the exact form prescribed. This is a verification pass against the in-memory structure — if any quirk is absent or mis-emitted, that's a Skill 3 implementation bug, halt and report.

In normal operation, §4.2-4.4 already produce all quirks correctly. §4.5 is the verification gate that catches drift between the emission code and the §16 contract.

The full checklist is in Appendix A (rows 2, 5, 6, 7 marked REMOVED/CORRECTED; rows 16-19 added in v1.5.0; rows 20-23 added in v1.13.0; row 24 added in v1.14.0; row 25 added with the PersonaID contract).

## Appendix A — Doc 1 §16 quirks: complete preservation checklist

All quirks below (rows 2, 5, 6, 7 marked REMOVED/CORRECTED in v1.5.0; rows 20–23 added in v1.13.0 from the golden export; row 24 added in v1.14.0; row 25 added with the PersonaID contract) must be present in the assembled JSON. Skill 3 verifies each before emission (§4.5).

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
| 12 | `silenceRelations: []` | `intentList` — **fifth of six**, between `intentCategories` and `apiSilenceRelations` (§4.3 sub-section order: `intents`, `botIntents`, `intentRelations`, `intentCategories`, `silenceRelations`, `apiSilenceRelations`) | Emit empty array. v1 always empty. Earlier wording said "top of `intentList`", which contradicted §4.3.6's position and the production export; the §4.3 order is authoritative. |
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
| 25 | `ActiveVersionInfo.PersonaID: 3` | `ActiveVersionInfo` | Emit the shared `TTSScriptReader` persona id per §4.2.2 and Appendix D.12. Never omit and never emit `null` — the proc's implicit "first `AccountId=0` Persona" fallback is exactly the failure mode `voicebot-json-contract.md` R7 warns about (a Bot with intents but no BotVersion if that fallback row is ever removed). |

The "extra" row is from Doc 1 §16's footnote (`response_success` observed but role unclear; preserve from baseline). Skill 3 treats it identically to the 18 numbered quirks.

**Rule for Skill 3:** when in doubt, emit what production samples emit, even if it looks redundant or empty. The platform's import endpoint may strictly require these keys to be present. Cleaning up the schema is a v3 concern (per Doc 1 §17 v2 Roadmap), not Skill 3's call.

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
| **3** | Approved | **v1 default — matches two production samples** |
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

**Known gap.** `voicebot-json-contract.md` R11's live FK whitelist (2026-08-10 snapshot) additionally lists `AIModelConfigID` **303, 312, 321** as valid shared (`AccountId=0`) rows — three IDs not yet in the table above or in `model-catalog.md`. Their `Name`/`AIModelTypeId`/active status haven't been captured from a `Data.sql` dump, so Skill 3 does not fabricate rows for them: they're unusable as Skill 1 catalog choices until someone with DB access adds real entries to both this table and `model-catalog.md`. Not a defect in existing output — a coverage gap flagged for follow-up.

### D.12 `PersonaID` (`ActiveVersionInfo.PersonaID`)

Per `${CLAUDE_PLUGIN_ROOT}/references/voicebot-json-contract.md` R7/R11. `Persona.PersonaID` is a `bigint NOT NULL` FK on `BotVersion` — no golden production export captured to date includes it (persona selection isn't yet a Skill 1 interview field), so Skill 3 emits the one known shared row unconditionally.

| ID | Name | When |
|---|---|---|
| **3** | TTSScriptReader | **v1 default — always emitted** (`AccountId=0`) |

If a future spec revision adds a persona-catalog field (mirroring how `model-catalog.md` resolves `AIModelConfigID`), extend this table with the additional named rows at that time — do not invent names for ids outside `{3}` today. CHK-25 asserts the emitted value stays inside this whitelist.
