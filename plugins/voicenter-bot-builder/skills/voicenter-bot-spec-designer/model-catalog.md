# Voicenter Bot Model Catalog (v1)

This file is read by Skill 1 during Phase 1 of the greenfield interview. It maps human-readable model names to the integer IDs the Voicenter platform expects in the wire-format JSON.

The catalog is hardcoded for v1 per locked decision F. v3 replaces this with an MCP query against the platform's live model registry.

All catalog entries below are **default/public** `AIModelConfig` rows where `AccountId = 0`. Skill 3 emits `AiModelConfig.AccountId = 0` in the wire format, which causes `ImportBotFromJSON` to take its "reuse existing config" branch — no new `AIModelConfig` row is created. The IDs below come from `database/Tables/StaticData/AIModelConfig.Data.sql` and `AIModel.Data.sql`. They must be re-verified whenever those files change.

---

## AI model configs

### Gemini Live (default — Voice driven 3.1)

| Field | Value |
|---|---|
| **Display name** | Gemini Live |
| **`AIModelConfigID`** | `139` |
| **`AIModelTypeId`** | `18` |
| **Provider model string** | `models/gemini-3.1-flash-live-preview` |
| **Voice family** | Gemini (see below) |
| **Notes** | Active default. Closest match to the historical "Gemini Live" name; uses Gemini 3.1 Voice driven model under the hood. |

### Gemini 2.5

| Field | Value |
|---|---|
| **Display name** | Gemini 2.5 |
| **`AIModelConfigID`** | `52` |
| **`AIModelTypeId`** | `10` |
| **Provider model string** | `models/gemini-2.5-flash-native-audio-preview-12-2025` |
| **Voice family** | Gemini |
| **Notes** | Active default. The original Gemini 2.5 native-audio entry. |

### Gemini Voice Driven

| Field | Value |
|---|---|
| **Display name** | Gemini Voice Driven |
| **`AIModelConfigID`** | `136` |
| **`AIModelTypeId`** | `16` |
| **Provider model string** | `models/gemini-3.1-flash-live-preview` |
| **Voice family** | Gemini |
| **Notes** | Active default. VOICE-class model. |

### Gemini 3.1 LLM Driven

| Field | Value |
|---|---|
| **Display name** | Gemini 3.1 LLM Driven |
| **`AIModelConfigID`** | `142` |
| **`AIModelTypeId`** | `21` |
| **Provider model string** | `models/gemini-3.1-flash-live-preview` |
| **Voice family** | Gemini |
| **Notes** | Active default. LLM-class model. |

### GPT-4 Realtime

| Field | Value |
|---|---|
| **Display name** | GPT-4 Realtime |
| **`AIModelConfigID`** | `1` |
| **`AIModelTypeId`** | `1` |
| **Provider model string** | `gpt-4o-realtime-preview` |
| **Voice family** | OpenAI |
| **Notes** | Active default. The original public GPT-4 standard. |

### GPT-5 Realtime

| Field | Value |
|---|---|
| **Display name** | GPT-5 Realtime |
| **`AIModelConfigID`** | `91` |
| **`AIModelTypeId`** | `13` |
| **Provider model string** | `gpt-realtime-2025-08-28` |
| **Voice family** | OpenAI |
| **Notes** | Active default. |

### GPT Realtime Mini

| Field | Value |
|---|---|
| **Display name** | GPT Realtime Mini |
| **`AIModelConfigID`** | `132` |
| **`AIModelTypeId`** | `15` |
| **Provider model string** | `gpt-realtime-mini-2025-12-15` |
| **Voice family** | OpenAI |
| **Notes** | Active default. Lower-cost realtime variant. |

*Add additional model entries below as the platform team confirms them. Each entry: Display name, `AIModelConfigID`, `AIModelTypeId`, provider model string, voice family, notes. Use only `AccountId = 0` rows from `AIModelConfig.Data.sql`.*

---

## Voice catalog

The `voiceName` field in `created.generationConfig.speechConfig.voiceConfig.prebuiltVoiceConfig` is a provider-specific string. Skill 1 presents the appropriate list based on the model family chosen above; Skill 3 emits the value verbatim from the spec.

### OpenAI voices

Used with the GPT family (GPT-4 Realtime, GPT-5 Realtime, GPT Realtime Mini).

| Voice | Wire-format value |
|---|---|
| Alloy | `alloy` |
| Ash | `ash` |
| Ballad | `ballad` |
| Coral | `coral` |
| Echo | `echo` |
| Sage | `sage` |
| Shimmer | `shimmer` |
| Verse | `verse` |
| Cedar | `Cedar` |
| Marin | `Marin` |

### Gemini voices

Used with the Gemini family (Gemini Live, Gemini 2.5, Gemini Voice Driven, Gemini 3.1 LLM Driven).

| Voice | Wire-format value |
|---|---|
| Puck | `Puck` |
| Charon | `Charon` |
| Kore | `Kore` |
| Fenrir | `Fenrir` |
| Aoede | `Aoede` |
| Leda | `Leda` |
| Orus | `Orus` |
| Zephyr | `Zephyr` |

Casing is preserved exactly as the platform UI presents it. Most OpenAI voices are lowercase; Cedar and Marin are capitalized. The full Gemini set is capitalized.

The user can supply any other string the provider supports — Skill 1 records it without validation (no live provider query in v1).

---

## Override path

If the user's desired model is not in this catalog (or if a future catalog version is missing IDs), Skill 1 accepts a raw override:

- `AIModelConfigID`: integer (must reference an existing platform `AIModelConfig` row)
- `AIModelTypeId`: integer (the `AIModel` FK)
- Voice name: any string

The override is written to spec section 1 as:

```
**AI Model Config:** raw: ID=<int>, TypeID=<int>
**Voice Name:** <string>
```

Skill 3 emits these values directly without catalog mapping. Skill 3 still emits `AiModelConfig.AccountId = 0` regardless — the override path assumes the user is pointing at an existing platform row.

---

## Unknowns

If the user picks a catalog entry whose IDs are still pending platform-team confirmation (none in v1 — all entries above are confirmed), Skill 1 marks them `<UNKNOWN: AIModelConfigID>` and `<UNKNOWN: AIModelTypeId>`. Skill 3 emits `-999` fail-loud sentinels and the JSON banner lists them.

---

## Maintenance

This catalog is part of Skill 1's package, version-controlled with the skill. To add a new model:

1. Verify the target row exists in `database/Tables/StaticData/AIModelConfig.Data.sql` with `AccountId = 0` and `IsActive = 1`.
2. Append a new section under "AI model configs" with all five fields populated.
3. Confirm the model's voice family belongs to OpenAI or Gemini (or document a new family with its voice list).
4. Update the skill version (in SKILL.md frontmatter or sidecar — TBD).

v3 will deprecate this file in favor of MCP querying the Voicenter platform's model registry directly.
