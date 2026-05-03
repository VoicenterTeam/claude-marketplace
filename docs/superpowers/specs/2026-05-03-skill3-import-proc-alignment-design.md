# Skill 3 ↔ `ImportBotFromJSON` alignment

**Status:** design
**Date:** 2026-05-03
**Scope:** Update Skill 3 (`voicenter-bot-json-assembler`) so the JSON it emits is consumable by the MySQL stored procedure `ImportBotFromJSON` without manual editing.
**Sources of truth:**
- Procedure: [database/Procedures/ImportBotFromJSON.sql](../../../database/Procedures/ImportBotFromJSON.sql)
- Skill 3: [plugins/voicenter-bot-builder/skills/voicenter-bot-json-assembler/SKILL.md](../../../plugins/voicenter-bot-builder/skills/voicenter-bot-json-assembler/SKILL.md)
- Reference JSON (the gap-discovery sample): `bot-the_biggest_bot-2026-05-03.json`

---

## 1. Problem

The current Skill 3 emission produces a JSON shape that conflicts with `ImportBotFromJSON` in five hard-blocking ways and two fragile ways. Importing the reference JSON would fail at the first `INSERT` against `AIModelConfig` and (if that were patched) cascade through several more failures. The skill must be aligned with the procedure's expectations so a freshly assembled bot is importable after the user fills in the documented sentinels.

**Guiding principle (user directive):** *the procedure's expectations take priority over Doc 1 §16 quirks*. Where the two disagree, the procedure wins; the §16 quirk table is amended.

---

## 2. Gap inventory

### 2.1 Hard-blocking (procedure errors out)

| ID | Symptom | Root cause |
|---|---|---|
| **G1** | `INSERT INTO AIModelConfig` fails on `AIModel` / `AIModelConfig` `NOT NULL` columns. | `AiModelConfig` block is missing `AccountId`. The proc's `IF $.AiModelConfig.AccountId = 0` branch doesn't fire (NULL ≠ 0); falls into the ELSE branch which expects a full insert payload that is also missing. |
| **G2** | `INSERT INTO IntentCategory` fails on `PriorityId NOT NULL`. | `intentCategories[]` entries lack `PriorityId`. The proc passes the extracted NULL explicitly; the column DEFAULT only fires when the column is omitted from the INSERT. |
| **G3** | `INSERT INTO BotIntent` fails on `IntentId NOT NULL`. | Field-name **case mismatch**: JSON emits `IntentID` / `BotIntentID` (capital `D`) but the proc reads `$.IntentId` / `$.BotIntentId` (lowercase `d`). MySQL JSON paths are case-sensitive. |
| **G4** | `INSERT INTO BotIntent` fails on `SortOrder NOT NULL`. | `botIntents[]` entries lack `SortOrder`. Same NULL-vs-default problem as G2. |
| **G5** | `INSERT INTO IntentRelated` fails with `Duplicate entry` on `UK_IntentRelated_Origin_Next`. | When a section-4 intent has the same `transfer_to_human` (or any target) listed twice in *Transitions out* — once as success path, once as fallback — Skill 3 emits two `intentRelations[]` rows with the same `(OriginIntentID, NextIntentID)` pair. The unique key forbids it. |

### 2.2 Fragile (works only because empty)

| ID | Symptom | Root cause |
|---|---|---|
| **G6** | `intents[].IntentScripts` is emitted as `{}`. The proc loops `0..JSON_LENGTH(IntentScripts)` and indexes `[i]` — `JSON_LENGTH({})` returns 0, so the loop is silently skipped. The moment a script populates, the proc indexes `[0]` on an object and breaks. | Doc 1 §16 quirk #8 documents `IntentScripts: {}`. The procedure expects `[]`. Per user directive, the procedure wins; quirk #8 is amended. |
| **G7** | `intents[].IntentSources` not emitted. The proc tolerates with `IFNULL(JSON_LENGTH(...), 0)`, so functionally OK today, but no `Sources` channel ever populates. | Skill 3 §4.3.1 doesn't mention `IntentSources`. Low priority — keep as-is for v1, document as v3 work. |

### 2.3 Benign (procedure ignores)

These do not need Skill 3 changes:

- Top-level `BotLanguages`, `CreatedDate`, `ModifiedDate`, `AccountID` (the proc uses `p_new_account_id` parameter for account scoping)
- `silenceRelations[]`, `apiSilenceRelations[]` arrays — the proc rewrites IDs only via per-intent `Configuration.api_silence_behaviour.intent`; the top-level arrays are decorative
- `intents[].IsDeleted`, `IntentResponces.IsActive`, `IntentResponces.SuccessCondition`
- `IntentParameters[].IntentId / ParameterType / OptionList / ValidationPattern / IsDeleted`
- `Parameter.Schema` (nullable; missing → NULL → OK)

---

## 3. Resolution: AiModelConfig (G1)

The procedure has two paths:

```sql
IF $.AiModelConfig.AccountId = 0 THEN
    use existing AIModelConfigID directly         -- "shared/default model" path
ELSE
    INSERT new AIModelConfig (AccountId=p_new_account_id,
                              AIModel, Name, AIModelConfig (JSON), IsActive, ApiKey)
END IF;
```

### 3.1 Default behavior — reuse a default model (`AccountId = 0`)

For v1, every bot Skill 3 emits references a **default catalog model** (Gemini Live is the only catalog entry today). These default models live in the platform DB with `AIModelConfig.AccountId = 0` (shared across accounts). Skill 3 emits:

```jsonc
"AiModelConfig": {
    "AIModelConfigID": <catalog ID, or -999 sentinel>,
    "AccountId": 0,                     // <-- NEW, triggers reuse path
    "Name": "<catalog display name>",
    "Description": "<catalog notes, or null>",
    "BaseUrl": null,
    "AIModelTypeId": <catalog ID, or -999>,
    "Type": { "AIModelTypeId": ..., "Name": ..., "Description": null },
    "created": { ... runtime payload ... }
}
```

Result: the proc takes the IF-branch, `v_new_ai_model_config_id := AIModelConfigID`, and no new `AIModelConfig` row is inserted. The user replaces the `-999` sentinels with real platform IDs at import time (existing v1 contract — unchanged).

### 3.2 Future behavior — create a per-account config (`AccountId != 0`)

When v2/v3 needs a bot-specific AIModelConfig (custom prompts, per-account API keys, etc.), Skill 3 emits a full insert payload by **copying base values from a default (`AccountId=0`) catalog entry**:

```jsonc
"AiModelConfig": {
    "AccountId": <any non-zero — proc ignores it; account scoping comes from p_new_account_id>,
    "AIModel": <copied from default catalog entry's AIModel FK>,
    "Name": "<copied or user-supplied display name>",
    "AIModelConfig": { ...same shape as `created` payload... },
    "IsActive": 1,
    "ApiKey": null                       // ALWAYS null — never authored by Skill 3
}
```

`ApiKey` is **always `null`**. Skill 3 never emits, copies, or invents an API key.

v1 documents this path but does not exercise it. The catalog only has default (AccountId=0) entries today; the override path in `model-catalog.md` already routes raw overrides through the AccountId=0 reuse mode.

### 3.3 Real default catalog IDs (from `database/Tables/StaticData/AIModelConfig.Data.sql`)

`AIModelConfig` rows where `AccountId = 0` are the shared/default models the import procedure will reuse when `AiModelConfig.AccountId = 0` is emitted. The active ones available today:

| `AIModelConfigID` | `AIModel` (FK) | `Name` | Active |
|---|---|---|---|
| 1 | 1 (GPT-4) | Public GPT-4 Standard | active |
| 52 | 10 (Gemini) | Public Gemini-2.5 Standard | active |
| 91 | 13 (GPT-5) | Public GPT- RealTime | active |
| 132 | 15 (GPT RT Mini) | Public GPT Realtime Mini | active |
| 136 | 16 (Gemini voice driven) | Public Gemini voice driven | active |
| 139 | 18 (Gemini 3.1 - Voice driven) | Gemini 3.1 - Voice driven | active |
| 142 | 21 (Gemini 3.1 - LLM driven) | Gemini 3.1 - LLM driven | active |
| 4, 7 | 4, 7 | Public GPT-3.5 Standard, Public PaLM Standard | inactive |

The Skill 1 model catalog (`model-catalog.md`) currently has `<TODO>` placeholders. It must be patched with these real IDs so Skill 3 can emit a concrete `AIModelConfigID` (and the matching `AIModel` FK as `AIModelTypeId` in wire-format) instead of always falling back to `-999` sentinels. The "Gemini Live" catalog entry maps to **`AIModelConfigID=139, AIModelTypeId=18`** (the closest active default — Gemini 3.1 Voice driven). Other models added to the catalog as the platform evolves.

**Resulting JSON (for the reference bot, "Gemini Live"):**

```jsonc
"AiModelConfig": {
    "AIModelConfigID": 139,
    "AccountId": 0,
    "Name": "Gemini 3.1 - Voice driven",
    "Description": null,
    "BaseUrl": null,
    "AIModelTypeId": 18,
    "Type": { "AIModelTypeId": 18, "Name": "Gemini - Voice - 3.1", "Description": null },
    "created": { ... runtime payload from §4.2.4 ... }
}
```

No `-999` sentinel needed — these are real platform IDs. Section 7.4 of the spec drops the `<UNKNOWN: AIModelConfigID>` and `<UNKNOWN: AIModelTypeId>` entries.

---

## 4. Resolution: other gaps

### 4.1 G2 — `intentCategories[].PriorityId`

Add a constant to the §4.3.5 emission table:

| Wire-format field | Value |
|---|---|
| `IntentCategoryId` | `-3` |
| `BotID` | `-1` |
| `Name` | `"Default Category"` |
| **`PriorityId`** | **`2`** *(new — DB column default; emit explicitly)* |
| **`IsActive`** | **`1`** *(new — was nullable but we emit explicitly to be safe)* |
| **`Description`** | **`null`** *(new — explicit)* |

### 4.2 G3 — `botIntents[]` field-name casing

Rename two paths in §4.3.3 to match the procedure's reads:

| Old (current) | New | Reason |
|---|---|---|
| `BotIntentID` | `BotIntentId` | Proc reads `$.BotIntentId` |
| `IntentID` | `IntentId` | Proc reads `$.IntentId` |
| `BotID` | `BotID` *(unchanged)* | Proc doesn't read it; cosmetic only |
| `BotIntentTypeID` | `BotIntentTypeID` *(unchanged)* | Proc reads with capital — already matches |
| `ConditionGroupList` | `ConditionGroupList` *(unchanged)* | Proc reads it as-is |

Note: `intentRelations[]` casing **already matches** the proc (`OriginIntentID`, `NextIntentID`, `IntentRelatedID` — all capital). No change there.

### 4.3 G4 — `botIntents[].SortOrder`

Add to §4.3.3 emission table:

| Wire-format field | Value |
|---|---|
| `SortOrder` | 1-based ordinal of the intent in section 4 (Intent 1 → 1, Intent 2 → 2, ...) |
| `IsActive` | `1` *(explicit; nullable but safer)* |

### 4.4 G5 — duplicate `intentRelations[]` rows

Update §4.3.4 emission rule:

> For each section 4 row's *Transitions out* list, build the candidate set of `(origin, next)` pairs. **Deduplicate by `(origin, next)`** before emission, keeping the lowest `Order` value. The unique key `UK_IntentRelated_Origin_Next` forbids duplicates; emitting two would fail import on the second row.
>
> When the spec lists the same target twice (e.g., success path AND fallback both → `transfer_to_human`), this is a structural redundancy: the runtime takes the first matching transition, so the second row never fires. Skill 3 silently de-dupes and notes the collapse in the banner under DEFAULTS APPLIED.

Banner addition: when de-duping happens, add a line like:

```
#   - intentRelations: collapsed duplicate (initiate_purchase → transfer_to_human) — success and fallback share the same target
```

### 4.5 G6 — `IntentScripts: {}` → `[]`

Amend Doc 1 §16 quirk #8 *and* Skill 3 Appendix A row 8:

> **Quirk #8 (revised):** `IntentScripts: []` per intent. Procedure `ImportBotFromJSON` iterates with `JSON_LENGTH` + integer indexing; an object form would index `[0]` on `{}` once non-empty and break. Older production samples may show `{}`; treat them as the same data shape (empty), but emit `[]` going forward.

### 4.6 G7 — `IntentSources` (now actionable)

The `Sources` static table maps cleanly to the spec section 1 `**Channels Active:**` field:

| `SourcesID` | `SourceName` |
|---|---|
| 1 | VOICE |
| 2 | CHAT |
| 3 | WEB |

Skill 3 §4.3.1 emits a per-intent `IntentSources` array, one entry per active channel. The procedure walks this array and inserts into `IntentSource(IntentID, SourceID)` per row.

| Spec section 1 `Channels Active` | Wire-format emission per intent |
|---|---|
| `voice` | `[{ "SourceID": 1 }]` |
| `chat` | `[{ "SourceID": 2 }]` |
| `voice, chat` | `[{ "SourceID": 1 }, { "SourceID": 2 }]` |

For the reference bot (`Channels Active: voice`), each of the 3 intents gets `IntentSources: [{ "SourceID": 1 }]`.

---

## 5. Files to change

| File | Change type | What |
|---|---|---|
| `plugins/voicenter-bot-builder/skills/voicenter-bot-json-assembler/SKILL.md` | edit | §4.2.3 (G1 + real catalog IDs), §4.3.1 (G6 IntentScripts, G7 IntentSources), §4.3.3 (G3 + G4), §4.3.4 (G5), §4.3.5 (G2), Appendix A row 8 (quirk #8 amendment). Add new Appendix D — static-data reference table. |
| `plugins/voicenter-bot-builder/skills/voicenter-bot-spec-designer/model-catalog.md` | edit | (1) Replace `<TODO: confirm with platform team>` placeholders for "Gemini Live" with real IDs (`AIModelConfigID=139, AIModelTypeId=18`). (2) Add other active default models (GPT-4, GPT-5, Gemini 2.5, etc.) as catalog entries pointing at the real default config rows. (3) Replace the 2-row voice catalog (Puck/Orus only) with the full provider voice inventories — see §8.11. |
| `docs/superpowers/specs/2026-05-03-skill3-import-proc-alignment-design.md` | new | This design (already created). |

**Out of scope** for this change:
- The procedure itself (`ImportBotFromJSON.sql`) — user directive: procedure wins, skill aligns to it.
- Skill 1 (`voicenter-bot-spec-designer/SKILL.md`) — no behavior change; Skill 1 still asks the same Phase 1 questions, the model catalog change is a data-only patch the skill consumes.
- Skill 2 — no spec-format changes needed; it already produces the inputs Skill 3 reads.
- The reference JSON (`bot-the_biggest_bot-2026-05-03.json`) — not regenerated as part of this design. The user can re-run Skill 3 against `agent-spec.md` after the patch lands to validate.
- `Language` table mapping — Skill 3 emits the Gemini API language code (`he-IL`) inside `speechConfig.languageCode`. This is a provider-side string, not a DB FK; the DB's `Language` table (`he-HE`, `en-US`, etc.) is only consulted by `IntentScript.LanguageCode`, which Skill 3 doesn't currently emit (`IntentScripts: []`). No change needed today; flag as v3 work when scripts populate.

---

## 6. Verification

After patching Skill 3 + the model catalog, manual verification by re-running Skill 3 against `agent-spec.md` and inspecting the emitted JSON:

1. `AiModelConfig.AccountId` is present and equals `0`.
2. `AiModelConfig.AIModelConfigID` equals `139` (the catalog default for "Gemini Live"). Not `-999`.
3. `AiModelConfig.AIModelTypeId` equals `18`. Not `-999`.
4. `intentCategories[0].PriorityId` is present and equals `2`.
5. `botIntents[].IntentId` (lowercase d) is present; `botIntents[].IntentID` (capital D) is **absent**. Same for `BotIntentId` vs `BotIntentID`.
6. `botIntents[].SortOrder` is present.
7. `intentRelations[]` has exactly one row per `(OriginIntentID, NextIntentID)` pair. For the reference bot, that's 3 rows: `(-10,-11)`, `(-10,-12)`, `(-11,-12)` — not 4.
8. `intents[].IntentScripts` is `[]`, not `{}`.
9. Each `intents[]` entry has `IntentSources: [{ "SourceID": 1 }]` (voice channel; reference bot has `Channels Active: voice`).

This is a static-shape check; full end-to-end validation requires running the procedure against a MySQL instance, which is out of scope for the skill change.

---

## 7. Risks

- **Silent acceptance of the procedure's quirks.** The proc has its own oddities (e.g., `BotIntent` paths use lowercase `Id` while `IntentRelated` paths use uppercase `ID`). Aligning the skill to match locks in those oddities. If the procedure is ever rewritten, the skill needs to follow. *Mitigation:* note the casing inconsistency in Skill 3 §4.3.3 so future maintainers know it is **deliberate** (matches the procedure's path syntax) rather than an authoring slip.
- **Quirk #8 contract change.** Existing production samples that emit `IntentScripts: {}` will not be consistent with new emissions. *Mitigation:* the procedure handles both shapes when empty (`JSON_LENGTH({}) == JSON_LENGTH([]) == 0`), and `[]` is the safer forward shape.
- **De-dup hides real spec errors.** A spec that lists `transfer_to_human` twice in transitions is technically redundant; collapsing it silently could mask a Skill 1 bug or hand-edit. *Mitigation:* the banner records the collapse so the user sees it.
- **Catalog IDs drift over time.** Hardcoding `AIModelConfigID=139` ties Skill 3 to a specific row in the platform DB. If that row is ever deleted or renamed, freshly emitted bots will fail import with a foreign-key violation. *Mitigation:* limit the catalog to `AccountId=0` rows (which the platform team commits to keeping stable) and document in `model-catalog.md` that catalog updates require a synchronized check against `AIModelConfig.Data.sql`. v3 replaces this with an MCP query against the live registry.

---

## 8. Static reference data — single source of truth

This appendix is the consolidated reference list of static IDs Skill 3 emits. All values come from `database/Tables/StaticData/*.Data.sql`. The skill must NOT invent IDs outside this set.

### 8.1 `BotStatusId` (root `BotStatusId` field)

| ID | Name | When to emit |
|---|---|---|
| **1** | Active | **Default for v1** — every freshly assembled bot |
| 2 | Inactive | Not emitted by Skill 3 |
| 3 | Maintenance | Not emitted by Skill 3 |
| 4 | Deleted | Not emitted by Skill 3 |

### 8.2 `BotVersionStatusId` (`ActiveVersionInfo.BotVersionStatusId`)

| ID | Name | When to emit |
|---|---|---|
| 1 | Draft | Not emitted by Skill 3 |
| 2 | Testing | Not emitted by Skill 3 |
| **3** | Approved | **Default for v1** — matches Yuval/Refua production samples |
| 4 | Deployed | Not emitted by Skill 3 |
| 5 | Archived | Not emitted (inactive in DB) |

### 8.3 `BotIntentTypeID` (`botIntents[].BotIntentTypeID`)

| ID | Name | When to emit |
|---|---|---|
| **1** | Normal | **Default for v1** — every botIntent row |
| 2 | Global | Reserved for v2 (global intents) |

### 8.4 `IntentCategoryId` + `PriorityId` (`intentCategories[]`)

| Field | Value | Reason |
|---|---|---|
| `IntentCategoryId` | `-3` (placeholder, replaced by proc) | v1 uses single default category |
| `PriorityId` | **`2`** (Medium, from `Priority` table) | DB column default; safest emit value |
| `Name` | `"Default Category"` | Matches production samples |

### 8.5 `ResponseTypeId` (`intents[].IntentResponces.ResponseTypeId`)

| ID | DB Name | Skill 3 doc name | Configuration shape |
|---|---|---|---|
| 1 | IVR | "Layer Transfer (terminal)" | §4.4 RT=1 |
| 2 | API | "API Call" | §4.4 RT=2 |
| 3 | Message | "Continue" | §4.4 RT=3 |
| 4 | Dial | "Dial-Out" | §4.4 RT=4 |

Note the DB names differ from Skill 3's documentation labels (e.g., RT=1 is "IVR" in DB, "Layer Transfer" in skill docs). This is a documentation-only divergence — the integer IDs are the contract. Skill 3 docs already use the integer IDs in §4.4 sub-headers.

### 8.6 `ParameterTypeId` (`IntentParameters[].ParameterTypeId`)

| ID | Name | Skill 3 supports |
|---|---|---|
| **1** | STRING | yes |
| **10** | PHONE | yes |
| **16** | BOOLEAN | yes |
| **19** | ENUM | yes |
| 4 | INTEGER | accepted via raw spec input but no Phase 1 catalog entry yet |
| 7 | EMAIL | accepted via raw spec input but no Phase 1 catalog entry yet |
| 13 | DATE | accepted via raw spec input but no Phase 1 catalog entry yet |
| 20 | JSON | accepted via raw spec input but no Phase 1 catalog entry yet |
| 21 | LABEL_SET_SINGLE | v3 |
| 24 | LABEL_SET_MULTIPLE | v3 |

The four supported types in v1 (1, 10, 16, 19) match Skill 3 §4.3.2. No change.

### 8.7 `SourceID` (`IntentSources[].SourceID`)

| ID | Name | Maps to spec section 1 `Channels Active` |
|---|---|---|
| 1 | VOICE | `voice` |
| 2 | CHAT | `chat` |
| 3 | WEB | (not currently exposed in Skill 1's channel options) |

### 8.8 `AIModelConfigID` (default catalog) — `AccountId = 0`

See §3.3 above for the full table. The seven active rows are the entire universe of "default model" choices the catalog can offer. When Skill 3 emits `AiModelConfig.AccountId = 0`, the `AIModelConfigID` and `AIModelTypeId` (= `AIModel` FK) MUST come from this list.

### 8.9 `IntentRelatedTypeID` — internal to procedure, not emitted

| ID | Name | Procedure use |
|---|---|---|
| 1 | IntentRelated | `IntentRelatedDTMF.RelatedTypeID` for `intentRelations[]` DTMF |
| 2 | BotIntent | `IntentRelatedDTMF.RelatedTypeID` for `botIntents[]` DTMF |

The procedure sets these values internally based on which array it's iterating; the JSON does not need to emit them. Skill 3's `DTMFList` arrays (currently empty in v1) are bound to one of these types implicitly.

### 8.10 `IntentScriptType` — not emitted in v1

| ID | Name |
|---|---|
| 1 | Opening |
| 2 | Collection |
| 3 | Validation |
| 5 | Failure |
| 6 | Closing |
| 4 | Success (inactive in DB) |

Skill 3 emits `IntentScripts: []` in v1. When script support lands (v3), entries will use these IDs as `ScriptTypeId` and pair with `LanguageCode` from the `Language` static table.

### 8.11 Voice catalog (per provider)

Wire-format path: `ActiveVersionInfo.AIModelConfig.created.generationConfig.speechConfig.voiceConfig.prebuiltVoiceConfig.voiceName` — a string Skill 3 copies verbatim from spec section 1 `**Voice Name:**`. The string is provider-specific; not a DB FK. The platform UI presents these dropdowns:

**OpenAI voices** (used by AIModel 1 / 4 / 13 / 15 — GPT family):

| Wire-format value | Display |
|---|---|
| `alloy` | Alloy |
| `ash` | Ash |
| `ballad` | Ballad |
| `coral` | Coral |
| `echo` | Echo |
| `sage` | Sage |
| `shimmer` | Shimmer |
| `verse` | Verse |
| `Cedar` | Cedar |
| `Marin` | Marin |

**Gemini voices** (used by AIModel 10 / 16 / 18 / 21 — Gemini family):

| Wire-format value | Display |
|---|---|
| `Puck` | Puck |
| `Charon` | Charon |
| `Kore` | Kore |
| `Fenrir` | Fenrir |
| `Aoede` | Aoede |
| `Leda` | Leda |
| `Orus` | Orus |
| `Zephyr` | Zephyr |

Casing is preserved as the platform UI presents it (lowercase for OpenAI's standard set, capitalized for Cedar/Marin and the entire Gemini set). Skill 3 emits the string exactly as the spec records it; Skill 1's Phase 1 picker presents the appropriate provider list based on the chosen `AIModelConfig` family.

The user can supply any other string the provider supports (Skill 1 records it without validation, per the existing override path). The catalog is the recommendation set, not an exhaustive whitelist.
