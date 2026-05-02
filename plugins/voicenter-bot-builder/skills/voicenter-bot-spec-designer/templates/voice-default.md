# Voice-Default Template (Inactive Channel)

This template is emitted by Skill 1 in greenfield Phase 2 when the bot has chat channel active but voice channel inactive. It is also emitted in patch mode when channel scope expands from chat-only to voice+chat.

The emitted text in spec section 2.2 is preceded by:
`[default — not user-authored]`

Skill 1 substitutes `[[PLACEHOLDERS]]` at write time. Bracketed `[[...]]` is build-time substitution syntax — distinct from runtime Mustache `{{...}}` to avoid collision.

---

## Template

```
[default — not user-authored]

You are speaking as [[PERSONA_IDENTITY]]. Maintain the same identity and tone as defined in the global persona.

Voice-channel guidelines:

1. Speak clearly and at a measured pace. Avoid speaking too fast.
2. Pronounce names, numbers, and addresses carefully. Confirm them back to the caller when collected.
3. If the caller interrupts, stop speaking immediately and listen.
4. Avoid long pauses. If you need a moment to look something up, say so explicitly ("Give me a moment to check that...").
5. Use [[PRIMARY_LANGUAGE]] only. Do not switch languages mid-call unless the caller does.

This is a generated default. If the user later activates voice as a primary channel, regenerate this section through Skill 1 patch mode (channel scope expansion).
```

---

## Substitution rules

### `[[PERSONA_IDENTITY]]`

Extract from spec section 2.1 (`prompts.persona`). Take the first sentence or two that establishes who the bot is — name, role, company. Examples:
- Persona starts "את יובל, נציגת שירות הלקוחות של חברת NC..." → `[[PERSONA_IDENTITY]]` = "יובל, נציגת שירות הלקוחות של חברת NC"
- Persona starts "You are Sarah, a scheduling assistant at Acme Corp." → `[[PERSONA_IDENTITY]]` = "Sarah, a scheduling assistant at Acme Corp."

If `[[PERSONA_IDENTITY]]` cannot be cleanly extracted (e.g., persona is multi-paragraph and identity is buried), fall back to: `the bot persona defined in section 2.1`.

### `[[PRIMARY_LANGUAGE]]`

Map from the language code in spec section 1 to a human-readable name:

| Code | Substitution |
|---|---|
| `he-IL` | Hebrew |
| `en-US` | English |
| `en-GB` | English |
| `es-ES` | Spanish |
| `fr-FR` | French |
| `de-DE` | German |
| `ar-SA` | Arabic |

If the code is unrecognized, substitute the raw code itself.
