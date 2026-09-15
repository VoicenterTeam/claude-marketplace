# Chat-Default Template (Inactive Channel)

This template is emitted by Skill 1 in greenfield Phase 2 when the bot has voice channel active but chat channel inactive. It is also emitted in patch mode when channel scope expands from voice-only to voice+chat.

The emitted text carries **no provenance marker in the body**. Skill 1 records the default in
spec **§7.7 Prompt provenance** instead (v1.20.2 — see the note below).

The body follows the Markdown shape in `${CLAUDE_PLUGIN_ROOT}/references/prompt-structure.md` — `chatInstructions` carries sections 1–4 and no Global directives block.

Skill 1 substitutes `[[PLACEHOLDERS]]` at write time. Same substitution syntax as `voice-default.md`.

> **Section 2.3's body is runtime prompt content.** Skill 3 copies it verbatim into
> `prompts.chatInstructions`, so every character written there is read by the model at call
> time. Never put a provenance marker, a maintenance note, or a build-time instruction in it —
> that is what §7.7 exists for. Until v1.20.2 this template opened with
> `[default — not user-authored]` and closed with a "regenerate this section through Skill 1
> patch mode" sentence; both shipped into the deployed prompt. Caught by V-C2, 2026-08-16.

---

## Template

```
# 1. Identity

* **Identity:** you are writing as [[PERSONA_IDENTITY]]. Maintain the same identity and tone as defined in the global persona.

#### 2. Message style

* **Length:** keep messages short and focused — typically 1–3 sentences per turn, unless you are explaining something genuinely complex.
* **Emojis:** do not use emojis unless the user uses them first.
* **Formatting:** write plain text. No headers, and no bullet lists unless the content is genuinely list-shaped.

#### 3. Confirmation

* **Read back:** confirm collected information by writing it back to the user, then ask them to confirm it.

#### 4. Language

* **Language:** use [[PRIMARY_LANGUAGE]] only. Never switch languages mid-conversation unless the user does.
```

---

## Substitution rules

Identical to `voice-default.md`:

- `[[PERSONA_IDENTITY]]`: first sentence(s) of `prompts.persona` that establish identity. Fallback: `the bot persona defined in section 2.1`.
- `[[PRIMARY_LANGUAGE]]`: language code mapped to human-readable name (table in `voice-default.md`). Fallback: raw code.
