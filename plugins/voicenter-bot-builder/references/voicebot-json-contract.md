# VoiceBotV2 Bot-Export JSON — Generation Contract
<!-- Single-file contract for any AI/plugin that GENERATES bot-import JSON.
     Target consumer: stored procedure VoiceBotV2.ImportBotFromJSON (+ CreateConditionGroups).
     Contains: (1) hard rules, (2) failure model, (3) runnable validator, (4) JSON Schema.
     v2 — 2026-08-10 -->

> **Provenance note.** This file is a verbatim (mojibake-cleaned) copy of an external contract
> document handed to the bot-builder pipeline on 2026-08-10, encoding the stored procedure
> `ImportBotFromJSON`'s hard requirements from a live schema/DB snapshot. Skill 3
> (`voicenter-bot-json-assembler`) cross-checked its own emission against every rule below;
> see the SKILL.md changelog for what changed as a result (PersonaID emission, check 25,
> Appendix D.11/D.12 additions). Rules already satisfied by Skill 3's existing emission are
> not called out again in SKILL.md — this file remains the authoritative source for the full
> rule set, including rules that don't currently apply to Skill 3's wire shapes (e.g. R5's
> `IntentSelect_1`/`IntentSelect_4` reference, which Skill 3 does not emit).

## Table of contents

- [0. Why this exists](#0-why-this-exists)
- [1. Hard rules — violating ANY of these breaks the import](#1-hard-rules--violating-any-of-these-breaks-the-import) (R1–R12)
- [2. Types](#2-types)
- [3. Skeleton (minimal correct shape)](#3-skeleton-minimal-correct-shape)
- [4. Mandatory gate before returning any JSON](#4-mandatory-gate-before-returning-any-json)
- [5. Validator (runnable, self-contained — Python 3 stdlib only)](#5-validator-runnable-self-contained--python-3-stdlib-only)
- [6. JSON Schema (draft 2020-12, structural checks only — optional fast gate)](#6-json-schema-draft-2020-12-structural-checks-only--optional-fast-gate)

**What Skill 3 owns from this file:** `ActiveVersionInfo.PersonaID` emission (R7) and CHK-25 in
[`verification-procedure.md`](verification-procedure.md). The `AIModelConfigID` whitelist in R11
lists three ids (303, 312, 321) not yet in the assembler's catalog — see the known-gap note in
`skills/voicenter-bot-json-assembler/stages/assembly-mapping.md` Appendix D.11.

## 0. Why this exists

The importer's error handling is a trap: any SQL error inside the loops trips a
`CONTINUE HANDLER`, the procedure finishes "normally", tries to roll back, and
still returns a `new_bot_id`. Worse, the original procedure's `TRUNCATE` of its
temp tables implicitly COMMITS the transaction before the first insert, so a
mid-way failure leaves PARTIAL data — e.g. a Bot with intents but **no
BotVersion** (the classic symptom of a missing/incomplete `ActiveVersionInfo`).
A returned bot id is NOT proof of success. The only safe strategy is: generate
JSON that cannot error. These rules make that guarantee. Validate before you
ever hand the JSON to the importer.

## 1. Hard rules — violating ANY of these breaks the import

**R1. `ConditionGroupList` is ALWAYS an array — never a bare object.**
Every `botIntents[]` and `intentRelations[]` entry:
```json
"ConditionGroupList": [ { "Order": 1, "IntentConditionList": [], ... } ]
```
Use `[]` when there are no groups. A bare object `{...}` is the #1 real-world
failure: `CreateConditionGroups` walks it by array index, `JSON_LENGTH(object)`
returns the KEY COUNT, `$[i]` returns NULL — junk rows or an error — full rollback.

**R2. The response key is `IntentResponces` — keep the typo.**
The procedure reads the mis-spelled path `$.IntentResponces`. Emit the correct
English spelling `IntentResponses` and the whole response is silently dropped.
It is a single OBJECT (not an array), and its `Configuration` must be a JSON
object (the proc runs `JSON_SET` remaps on it).

**R3. IDs are map-table PRIMARY KEYS — present and unique, or full rollback.**
The proc copies old→new ids into temp tables with `PRIMARY KEY (old_id)`:

| field | scope of uniqueness | if missing/duplicate |
|---|---|---|
| `intents[].IntentId` | across all intents | NULL/dup PK → error → rollback |
| `intentCategories[].IntentCategoryId` | across all categories | same |
| `botIntents[].BotIntentId` | across all botIntents | same |
| `intentRelations[].IntentRelatedID` | across all (inserted) relations | same |
| `IntentParameters[].ParameterId` | **GLOBAL — across ALL intents combined** | same |

Use unique negative numbers (-1, -10, -1000…) as export-side ids; they only
serve as map keys.

**R4. These are ALWAYS arrays** (never object, never string):
`intentList.intents`, `.intentCategories`, `.botIntents`, `.intentRelations`,
and per-intent `IntentScripts`, `IntentParameters`, `IntentSources`, and every
`DTMFList` (the proc runs `JSON_TABLE(... '$[*]')` over DTMFList).
Empty is `[]`, not `null`, not `{}`.

**R5. Every reference must resolve inside the file:**
- `intents[].IntentCategoryId` → `intentCategories[].IntentCategoryId`
  (else the Intent insert FAILS — `Intent.IntentCategoryId` is `bigint NOT NULL`);
- `botIntents[].IntentId` → `intents[].IntentId`;
- `intentRelations[].OriginIntentID` and `.NextIntentID` → `intents[].IntentId`
  (unresolved relations are silently skipped — the edge just vanishes);
- `ActiveVersionInfo.AIModelConfig.silence_behaviour.intent`,
  `.api_silence_behaviour.intent`, and `IntentResponces.Configuration.IntentSelect_1|_4`
  should each point at an `intents[].IntentId`, or they stay unmapped (stale old id).

**R6. `AiModelConfig` (top level) is required.**
- `"AccountId": 0` → proc REUSES an existing config; `AIModelConfigID` required.
- `AccountId != 0` → new row inserted; `AIModel`, `Name`, `AIModelConfig`,
  `IsActive` required (`ApiKey` optional).

**R7. `ActiveVersionInfo` is REQUIRED — a missing/incomplete one is exactly the
"bot created but no BotVersion" failure.** The `BotVersion` table enforces
(from the DDL):

| JSON field | column constraint | if missing in JSON |
|---|---|---|
| `VersionNumber` | `varchar(50) NOT NULL` | NULL insert → step 3 FAILS |
| `BotVersionStatusId` | `tinyint NOT NULL`, FK → `BotVersionStatus` | NULL insert → step 3 FAILS |
| `IsActive` | `tinyint(1)` | inserts NULL (allowed but wrong — always send 0/1) |
| `AIModelConfig` | `json` | must be an OBJECT (holds `silence_behaviour`; remapped in step 5b) |
| `Description` | `varchar(512)` | optional; ≤512 chars |
| `PersonaID` | `bigint NOT NULL`, FK → `Persona` | omitted/null → proc uses first `Persona` with `AccountId=0`; if NONE exists on the target server, step 3 FAILS |
| `SystemPrompt` | `text` | optional |

If `ActiveVersionInfo` is absent entirely, every one of these extracts as NULL,
the BotVersion insert dies on `VersionNumber cannot be null`, and (with the
original procedure's broken transaction) you're left with a Bot and intents but
NO version. Always emit the full object:
```json
"ActiveVersionInfo": {
  "IsActive": 1, "VersionNumber": "0.0.1", "BotVersionStatusId": 3,
  "SystemPrompt": "...", "Description": null, "PersonaID": null,
  "AIModelConfig": { ... }
}
```
Note `AIModelConfigID` on BotVersion is `NOT NULL` FK too — it comes from R6's
`AiModelConfig`, so R6 (`AIModelConfigID` must exist on the TARGET server when
`AccountId==0`) is equally hard.

**R8. Top-level Bot:** `Name` non-empty string ≤100 (`varchar(100) NOT NULL`),
`BotStatusId` one of 1–4 (FK → `BotStatus`: 1 Active, 2 Inactive,
3 Maintenance, 4 Deleted).

**R9. String length limits — verified against the live schema. The server runs
`STRICT_TRANS_TABLES`, so over-length strings fail the insert with "Data too
long":**

| field | column | limit |
|---|---|---|
| `Name` (Bot) | `varchar(100) NOT NULL` | 100 |
| `Description` (Bot, top-level) | `text` | unbounded |
| `ActiveVersionInfo.VersionNumber` | `varchar(50) NOT NULL` | 50 |
| `ActiveVersionInfo.Description` | `varchar(512)` | **512** |
| `intentCategories[].Name` | `varchar(100) NOT NULL` | 100 |
| `intents[].Name` | `varchar(100) NOT NULL` | 100 |
| `intents[].IntentToolName` | `varchar(255)` | 255 |
| `IntentParameters[].Name` | `varchar(100) NOT NULL` | 100 |
| `IntentScripts[].LanguageCode` | `varchar(10) NOT NULL` | 10 (e.g. `he-IL`) |
| `DTMFList[]` entries | `varchar(20)` | 20 |
| `ConditionGroupList[].IntentConditionName` | `varchar(100)` | 100 |
| `AiModelConfig.Name` | `varchar(100) NOT NULL` | 100 |
| category/intent/parameter `Description`, `SystemPrompt`, `HandlingInstructions`, `ScriptContent`, `DefaultValue`, `SuccessCondition`, `ApiKey` | `text` | unbounded |

Do NOT write changelogs into Description fields — a 494-char changelog in
`ActiveVersionInfo.Description` is exactly what once produced a bot with
intents but no BotVersion. Keep descriptions short; changelogs belong outside
the JSON.

**R10. NOT NULL columns fed VERBATIM from JSON — these fields are REQUIRED in
every occurrence; a missing one becomes an explicit NULL insert, which FAILS
under strict mode even though the column has a default:**

| JSON field | column | note |
|---|---|---|
| `intents[].Priority` | `Intent.Priority float NOT NULL` | always send (e.g. 1) |
| `intents[].ValidationTimeout` | `Intent.ValidationTimeout int NOT NULL` | always send (e.g. 30) |
| `intents[].MaxAttempts` | `Intent.MaxAttempts int NOT NULL` | always send (e.g. 3) |
| `intentCategories[].PriorityId` | `IntentCategory.PriorityId tinyint NOT NULL` FK → `Priority` | always send (e.g. 2) |
| `IntentParameters[].CollectionOrder` | `Parameter.CollectionOrder int NOT NULL` | always send |
| `IntentScripts[].ScriptContent` | `IntentScript.ScriptContent text NOT NULL` | never null/empty |
| `botIntents[].SortOrder` | `BotIntent.SortOrder int NOT NULL` | always send |
| `intentRelations[].Order` | `IntentRelated.Order float NOT NULL` | always send |
| `ConditionGroupList[].Order` | `IntentConditionGroup.Order tinyint NOT NULL` | always send in every group |

**R11. Lookup ids must come from these whitelists (FK-enforced; live values):**

| field | valid values |
|---|---|
| `BotStatusId` | 1 Active, 2 Inactive, 3 Maintenance, 4 Deleted |
| `BotVersionStatusId` | 1 Draft, 2 Testing, 3 Approved, 4 Deployed, 5 Archived |
| `ScriptTypeId` | 1 Opening, 2 Collection, 3 Validation, 4 Success (inactive), 5 Failure, 6 Closing |
| `ParameterTypeId` | 1 STRING, 4 INTEGER, 7 EMAIL, 10 PHONE, 13 DATE, 16 BOOLEAN, 19 ENUM, 20 JSON, 21 LABEL_SET_SINGLE, 24 LABEL_SET_MULTIPLE |
| `ResponseTypeId` | 1 IVR, 2 API, 3 Message, 4 Dial |
| `BotIntentTypeID` | 1 Normal, 2 Global |
| `IntentSources[].SourceID` | 1 VOICE, 2 CHAT, 3 WEB |
| shared `AIModelConfigID` (AccountId=0) | 1, 4, 7, 52, 91, 132, 136, 139, 142, 303, 312, 321 (snapshot — may grow) |
| shared `PersonaID` (AccountId=0) | 3 (TTSScriptReader) |

**R12. ConditionGroupList entry contract** (what `CreateConditionGroups`
actually reads — anything else in the group object is ignored):
```json
{
  "Order": 1,                              // REQUIRED (tinyint NOT NULL)
  "IntentConditionName": "…",             // <=100 chars
  "IntentConditionGroupType": 1,           // tinyint, FK -> IntentConditionGroupType
  "IntentConditionList": [                 // array; may be []
    {
      "IntentConditionParameter": "…",    // REQUIRED (inserted into IntentConditions)
      "IntentConditionOperator": 1,        // REQUIRED (numeric — extracted WITHOUT unquote)
      "IntentConditionParameterValue": "…" // REQUIRED
    }
  ]
}
```
Old ids inside groups (`IntentConditionGroupID`, `IntentConditionRelationID`)
are ignored — the procedure supplies the new relation id itself.

## 2. Types

Numeric ids and flags (`*Id`/`*ID`, `Priority`, `SortOrder`, `Order`,
`MaxAttempts`, `ValidationTimeout`, `IsActive`, `IsRequired`, `IsSilenceIntent`,
`PriorityId`, `ScriptTypeId`, `ParameterTypeId`, `ResponseTypeId`,
`BotIntentTypeID`) are JSON numbers; booleans as 0/1.
`IntentConfig`, `ValidationRules`, `Schema`, `AIModelConfig`, `Configuration`
are JSON objects — NOT stringified JSON. Free-text fields may be `null`.

## 3. Skeleton (minimal correct shape)

```json
{
  "Name": "My Bot", "BotID": -1, "AccountID": -999, "BotStatusId": 1,
  "Description": null,
  "AiModelConfig": { "AccountId": 0, "AIModelConfigID": 142 },
  "ActiveVersionInfo": {
    "IsActive": 1, "VersionNumber": "0.0.1", "BotVersionStatusId": 3,
    "SystemPrompt": "...", "PersonaID": null,
    "AIModelConfig": { "silence_behaviour": { "intent": -38 } }
  },
  "intentList": {
    "intentCategories": [ { "IntentCategoryId": -1, "Name": "General", "PriorityId": 1, "IsActive": 1 } ],
    "intents": [ {
      "IntentId": -10, "IntentCategoryId": -1, "Name": "...", "IsActive": 1,
      "Priority": 1, "MaxAttempts": 3, "IsSilenceIntent": 0,
      "IntentConfig": {}, "IntentScripts": [], "IntentParameters": [], "IntentSources": [],
      "IntentResponces": { "ResponseTypeId": 1, "Configuration": {}, "IsActive": 1 }
    } ],
    "botIntents": [ {
      "BotIntentId": -100, "IntentId": -10, "SortOrder": 1, "IsActive": 1,
      "BotIntentTypeID": 1, "DTMFList": [], "ConditionGroupList": []
    } ],
    "intentRelations": [ {
      "IntentRelatedID": -200, "OriginIntentID": -10, "NextIntentID": -11,
      "Order": 1, "DTMFList": [], "ConditionGroupList": []
    } ]
  }
}
```

## 4. Mandatory gate before returning any JSON

Save the script in section 5 as `validate_bot_json.py` and run:
```bash
python3 validate_bot_json.py yourfile.json   # exit 0 + "0 error(s)" required
```
Fix every ERROR and regenerate. WARNs are advisory. Never deliver JSON that
has not passed this gate.

## 5. Validator (runnable, self-contained — Python 3 stdlib only)

The full validator script (`validate_bot_json.py`) — FK whitelists, NOT NULL
checks, varchar limits, and cross-reference/duplicate-id checks encoding the
rules above — is on file with whoever supplied this contract. Skill 3 does not
shell out to it (v1 has no Python runtime dependency); instead, the equivalent
mechanical checks are folded into Skill 3's own §15.4 cross-reference pass and
its by-construction emission rules (SKILL.md §4), so the same defects are
caught before the JSON ever leaves the pipeline.

## 6. JSON Schema (draft 2020-12, structural checks only — optional fast gate)

The validator above is authoritative (it also checks cross-references and
duplicates, which schema can't). See the source contract for the full schema;
omitted here since Skill 3's own §6 cross-reference pass (SKILL.md) plays the
same role for the bot-builder pipeline's specific wire shapes.
