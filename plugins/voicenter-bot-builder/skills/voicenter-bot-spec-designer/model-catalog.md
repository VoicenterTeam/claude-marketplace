# Voicenter Bot Model Catalog (v1)

This file is read by Skill 1 during Phase 1 of the greenfield interview. It maps human-readable model names to the integer IDs the Voicenter platform expects in the wire-format JSON.

The catalog is hardcoded for v1 per locked decision F. v3 replaces this with an MCP query against the platform's live model registry.

---

## AI model configs

### Gemini Live

| Field | Value |
|---|---|
| **Display name** | Gemini Live |
| **`AIModelConfigID`** | `<TODO: confirm with platform team>` |
| **`AIModelTypeId`** | `<TODO: confirm with platform team>` |
| **Provider model string** | `models/gemini-2.5-flash-preview-native-audio-dialog` |
| **Default voices** | Puck, Orus |
| **Notes** | Production reference. Used by Yuval and Refua bots in Doc 1 samples. |

*Add additional model entries below as the platform team confirms them. Each entry: Display name, `AIModelConfigID`, `AIModelTypeId`, provider model string, default voices, notes.*

---

## Voice catalog

The Gemini Live `voiceName` field accepts any string supported by the provider. v1 has observed in production:

| Voice | Used by | Language |
|---|---|---|
| **Puck** | Yuval | he-IL |
| **Orus** | Refua | he-IL |

Skill 1 presents these by name during Phase 1. The user can supply any other string the provider supports; Skill 1 records it without validation (no live provider query in v1).

---

## Override path

If the user's desired model is not in this catalog (or if the catalog entries still have `<TODO>` IDs), Skill 1 accepts a raw override:

- `AIModelConfigID`: integer
- `AIModelTypeId`: integer
- Voice name: any string

The override is written to spec section 1 as:

```
**AI Model Config:** raw: ID=<int>, TypeID=<int>
**Voice Name:** <string>
```

Skill 3 emits these values directly without catalog mapping.

---

## Unknowns

If the user picks "Gemini Live" but the catalog entry has `<TODO: confirm with platform team>` for IDs, Skill 1 marks them `<UNKNOWN: AIModelConfigID>` and `<UNKNOWN: AIModelTypeId>` in spec section 1. Section 7.3 records the catalog gap. Section 7.4 aggregates the unknowns. Skill 3 emits `-999` fail-loud sentinels for the missing IDs, and the JSON banner comment lists them. The user must replace before importing.

---

## Maintenance

This catalog is part of Skill 1's package, version-controlled with the skill. To add a new model:

1. Append a new section under "AI model configs" with all four fields populated.
2. If the model has known voices, list them in the voice catalog.
3. Update the skill version (in SKILL.md frontmatter or sidecar — TBD).

v3 will deprecate this file in favor of MCP querying the Voicenter platform's model registry directly.
