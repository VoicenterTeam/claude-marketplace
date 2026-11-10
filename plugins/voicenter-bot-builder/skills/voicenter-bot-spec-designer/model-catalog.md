# Voicenter Bot Model Catalog (v1)

This file is read by Skill 1 during Phase 1 of the greenfield interview. It maps human-readable model names to the integer IDs the Voicenter platform expects in the wire-format JSON.

The catalog is hardcoded for v1 per locked decision F. v3 replaces this with an MCP query against the platform's live model registry.

All catalog entries below are **default/public** `AIModelConfig` rows where `AccountId = 0`. Skill 3 emits `AiModelConfig.AccountId = 0` in the wire format, which causes `ImportBotFromJSON` to take its "reuse existing config" branch — no new `AIModelConfig` row is created. The IDs below come from `database/Tables/StaticData/AIModelConfig.Data.sql` and `AIModel.Data.sql`. They must be re-verified whenever those files change.

---

## AI model configs

> **Canonical default (v1.23.1):** when Skill 1 needs to fall back (user requests defaults, can't decide, or skips the model-config step), use **Voicenter Voicebot** — `AIModelConfigID = 321`, `AIModelTypeId = 30`. The "Voicenter Voicebot (default)" entry below is the source of truth for those numbers. (v1.23.0 defaulted to Voicenter Voicebot - ElevenLabs, `390`, which stays selectable; through v1.22.0 the default was Gemini 3.1 - LLM driven, `142`.)

### Wire family

Every entry belongs to a **wire family**, which decides the JSON shape Skill 3 emits (`assembly-mapping.md` §4.2.3–§4.2.4):

| Family | Top-level `AiModelConfig.AIModelConfig` | Voice location | Version-level `created` | `recordAgentCalls` |
|---|---|---|---|---|
| `gemini` | `{ "created": { "model": "<string>" } }` | `created.generationConfig.speechConfig.voiceConfig.prebuiltVoiceConfig.voiceName` | present | string `"true"`/`"false"` |
| `tts` | `{}` (empty object) | `tts.speak.voice` (a Voicenter TTS voice name on `321`, an ElevenLabs voice ID on `390`) | **absent** | JSON boolean |

The GPT entries use the `gemini` shape — it is the only shape Skill 3 emitted before v1.23.0.

### Voicenter Voicebot (default)

| Field | Value |
|---|---|
| **Display name** | Voicenter Voicebot |
| **`AIModelConfigID`** | `321` |
| **`AIModelTypeId`** | `30` |
| **Provider model string** | — (none; the top-level `AIModelConfig` is `{}`) |
| **Wire family** | `tts` |
| **Voice family** | Voicenter TTS (see below) |
| **Notes** | **Default since v1.23.1.** Verified from a production export: BotID 37390 "נתיב תכנון מסלול - עברית - PROD 4", version 0.1.150 (`AIModel: 30`, `AccountId: 0`, voice `eitan`). That export also carried a leftover Gemini `created` block; Skill 3 does not emit one for this family. |

### Voicenter Voicebot - ElevenLabs

| Field | Value |
|---|---|
| **Display name** | Voicenter Voicebot - ElevenLabs |
| **`AIModelConfigID`** | `390` |
| **`AIModelTypeId`** | `36` |
| **Provider model string** | — (none; the top-level `AIModelConfig` is `{}`) |
| **Wire family** | `tts` |
| **Voice family** | ElevenLabs (see below) |
| **Notes** | The default in v1.23.0; selectable since v1.23.1. Verified from a production export: BotID 37437 "נתיב תכנון מסלול - עברית - Voicenter ElevenLabs", version 0.1.149 (`AIModel: 36`, `AccountId: 0`). |

### Voicenter Voicebot - Gemini (Gemini 3.8) — UNVERIFIED

| Field | Value |
|---|---|
| **Display name** | Voicenter Voicebot - Gemini |
| **`AIModelConfigID`** | `387` |
| **`AIModelTypeId`** | `<UNKNOWN>` |
| **Provider model string** | `<UNKNOWN>` |
| **Wire family** | `<UNKNOWN>` |
| **Voice family** | `<UNKNOWN>` |
| **Notes** | The Gemini 3.8 model. **Unverified:** only the config ID is known. **Skill 3 halts** if a spec selects it (`sentinels-and-banner.md` — unverified model). Verify from a production export of a bot on 387, then fill the four unknown fields and drop this marker. |

**Skill 1 may still offer the unverified entry** when the user asks for it by name, but must warn that the build will stop at Skill 3 until the entry is verified. It never picks it as a default.

### Gemini Live (Voice driven 3.1)

| Field | Value |
|---|---|
| **Display name** | Gemini Live |
| **`AIModelConfigID`** | `139` |
| **`AIModelTypeId`** | `18` |
| **Provider model string** | `models/gemini-3.1-flash-live-preview` |
| **Wire family** | `gemini` |
| **Voice family** | Gemini (see below) |
| **Notes** | Active default. Closest match to the historical "Gemini Live" name; uses Gemini 3.1 Voice driven model under the hood. |

### Gemini 2.5

| Field | Value |
|---|---|
| **Display name** | Gemini 2.5 |
| **`AIModelConfigID`** | `52` |
| **`AIModelTypeId`** | `10` |
| **Provider model string** | `models/gemini-2.5-flash-native-audio-preview-12-2025` |
| **Wire family** | `gemini` |
| **Voice family** | Gemini |
| **Notes** | Active default. The original Gemini 2.5 native-audio entry. |

### Gemini Voice Driven

| Field | Value |
|---|---|
| **Display name** | Gemini Voice Driven |
| **`AIModelConfigID`** | `136` |
| **`AIModelTypeId`** | `16` |
| **Provider model string** | `models/gemini-3.1-flash-live-preview` |
| **Wire family** | `gemini` |
| **Voice family** | Gemini |
| **Notes** | Active default. VOICE-class model. |

### Gemini 3.1 - LLM driven

| Field | Value |
|---|---|
| **Display name** | Gemini 3.1 - LLM driven |
| **`AIModelConfigID`** | `142` |
| **`AIModelTypeId`** | `21` |
| **Provider model string** | `models/gemini-3.1-flash-live-preview` |
| **Wire family** | `gemini` |
| **Voice family** | Gemini |
| **Notes** | Active default. LLM-class model. Was the canonical default through v1.22.0. |

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

### Voicenter TTS voices

Used with Voicenter Voicebot (`321`, the default). Voicenter's own Hebrew TTS (`qwen3-tts-he`; speaks Hebrew, English and Russian). The wire value is the voice name, emitted verbatim to `ActiveVersionInfo.AIModelConfig.tts.speak.voice`.

| Voice | Wire-format value | Gender |
|---|---|---|
| Echo | `echo` | Male |
| Ariel | `ariel` | Male |
| Eitan | `eitan` | Male |
| Nadav | `nadav` | Male |
| Omer | `omer` | Male |
| Yoni | `yoni` | Male |
| Tel4n | `tel4n_h2` | Female |
| Adi | `adi` | Female |
| Hila | `hila` | Female |
| Maya | `maya` | Female |
| Noa | `noa` | Female |
| Rina | `rina` | Female |

**There is no default Voicenter TTS voice either** (the platform falls back to `echo` when none is sent, but Skill 1 never relies on that). Skill 1 asks the gender and presents that gender's six voices.

### ElevenLabs voices

Used with Voicenter Voicebot - ElevenLabs (`390`). The wire value is the **ElevenLabs voice ID**, emitted verbatim to `ActiveVersionInfo.AIModelConfig.tts.speak.voice`. These are the Hebrew voices of the shared ElevenLabs library.

| Voice | Wire-format value | Gender |
|---|---|---|
| Danit | `s0T0DT6EAPeX57MQpn3I` | Female |
| Zina | `Tbj9UQjXon5RB9MPEyc2` | Female |
| Itay | `X5KkWC7LtHHN2wzb0Lao` | Male |
| Itamar | `l7Q9rbdCC6j3J5dNlOOg` | Male |
| Nimrod | `ZiofZHcEBTn5sRySe5h8` | Male |
| Gad Tamir | `SSaO8heNHx6ee5ZRpZ1X` | Male |
| Herzl Ben | `6Ijsl5024dyMrE00loVE` | Male |
| Dorian | `PBHwEnXdzx0yfhIO2UCH` | Male |
| Viktor M | `8sZ9Z3Jy28CGLLCmKEHn` | Male |

**There is no default ElevenLabs voice.** Skill 1 always asks the agent's gender and then presents the voices of that gender — even when the user asked for defaults. Write the voice ID (not the display name) to spec section 1 `**Voice Name:**`.

### OpenAI voices

Used with the GPT family (GPT-4 Realtime, GPT-5 Realtime, GPT Realtime Mini).

| Voice | Wire-format value | Gender |
|---|---|---|
| Alloy | `alloy` | Neutral |
| Ash | `ash` | Male |
| Ballad | `ballad` | Male |
| Coral | `coral` | Female |
| Echo | `echo` | Male |
| Sage | `sage` | Female |
| Shimmer | `shimmer` | Female |
| Verse | `verse` | Male |
| Cedar | `Cedar` | Male |
| Marin | `Marin` | Female |

### Gemini voices

Used with the Gemini family (Gemini Live, Gemini 2.5, Gemini Voice Driven, Gemini 3.1 - LLM driven).

| Voice | Wire-format value | Gender |
|---|---|---|
| Puck | `Puck` | Male |
| Charon | `Charon` | Male |
| Kore | `Kore` | Female |
| Fenrir | `Fenrir` | Male |
| Aoede | `Aoede` | Female |
| Leda | `Leda` | Female |
| Orus | `Orus` | Male |
| Zephyr | `Zephyr` | Female |

Casing is preserved exactly as the platform UI presents it. Most OpenAI voices are lowercase; Cedar and Marin are capitalized. The full Gemini set is capitalized.

**Gender is a selection aid, not a wire-format field.** Skill 1 asks the user whether the agent should sound female or male (an explicit question — never inferred from the bot name, which is often unisex) and presents only voices of that gender for the active model family. Neutral voices (e.g. `alloy`) may be offered under either choice. Only the chosen `voiceName` string is emitted by Skill 3; the gender label itself is spec metadata and is not written to the JSON.

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
3. Record the model's **wire family** (`gemini` or `tts`) and confirm its voice family is listed below (or document a new family with its voice list). A model whose wire shape has not been captured from a production export is catalogued **UNVERIFIED** — Skill 3 halts on it.
4. Update the skill version (in SKILL.md frontmatter or sidecar — TBD).

v3 will deprecate this file in favor of MCP querying the Voicenter platform's model registry directly.
