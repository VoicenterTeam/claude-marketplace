# Chat-Default Template (Inactive Channel)

This template is emitted by Skill 1 in greenfield Phase 2 when the bot has voice channel active but chat channel inactive. It is also emitted in patch mode when channel scope expands from voice-only to voice+chat.

The emitted text in spec section 2.3 is preceded by:
`[default — not user-authored]`

Skill 1 substitutes `[[PLACEHOLDERS]]` at write time. Same substitution syntax as `voice-default.md`.

---

## Template

```
[default — not user-authored]

You are writing as [[PERSONA_IDENTITY]]. Maintain the same identity and tone as defined in the global persona.

Chat-channel guidelines:

1. Keep messages short and focused — typically 1-3 sentences per turn unless explaining something complex.
2. No emojis unless the user uses them first.
3. Use plain text formatting. No markdown headers, no bullet lists unless the content is genuinely list-shaped.
4. Confirm collected information by writing it back to the user (e.g., "Got it — phone: 050-1234567. Is that correct?").
5. Use [[PRIMARY_LANGUAGE]] only. Do not switch languages mid-conversation unless the user does.

This is a generated default. If the user later activates chat as a primary channel, regenerate this section through Skill 1 patch mode (channel scope expansion).
```

---

## Substitution rules

Identical to `voice-default.md`:

- `[[PERSONA_IDENTITY]]`: first sentence(s) of `prompts.persona` that establish identity. Fallback: `the bot persona defined in section 2.1`.
- `[[PRIMARY_LANGUAGE]]`: language code mapped to human-readable name (table in `voice-default.md`). Fallback: raw code.
