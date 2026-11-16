# Skill 2 stage — Helpers and tools

*Load when the work queue holds `### Helper:` or `### Tool:` entries (spec section 4.8). They
are detailed after the intents, as one batch with its own checkpoint (SKILL.md §8): tools
first, because each helper's instruction names its tools. Section 4.8 is Skill 1's — read it,
never change it; a structural problem routes to Skill 1 patch mode.*

## 1. Tools

For each `### Tool:` entry, from its section-4.8 block:

1. **`**Tool description:**`** (fenced) — one or two sentences in the bot's primary language:
   what the tool does, when the helper should call it, and what it returns when that is known.
   It is read by the model, never spoken: plain prose, no Markdown, no dialogue, no stage
   markers (FP-10's description rules). Never a setting value, a URL or a credential.
2. **`**Arguments:**`** — one line per argument section 4.8 declares, in its order:
   ``- `<name>` — Description: <text>``. Say what value it holds and its exact format (digits
   only, `YYYY-MM-DD`, as the caller spelled it). Keep the name exactly as section 4.8 writes
   it. Write `**Arguments:** [none]` when it declares none.

A tool marked `**Add after the import:**` is detailed the same way: Skill 3 uses its
description when it creates the tool after the import.

## 2. Helpers

For each `### Helper:` entry, write the fenced **`**Instruction:**`** — the helper's prompt —
Markdown-structured per `${CLAUDE_PLUGIN_ROOT}/references/prompt-structure.md` (helper
`Instruction` row), in the bot's primary language:

- `# 1. Role` — what the helper handles, scoped to the intents it serves (named by their
  Descriptions), and what it hands back.
- `#### 2. Tools` — one bullet per tool the file gives it: every tool whose `**Used by:**`
  names this helper and that is not marked `**Add after the import:**`. Write
  `* **<ToolName>:** <when to call it and what to do with the result>`, the ToolName exactly as
  section 4.8 writes it, character for character — the import hands the tool to the model under
  that name, and Skill 3 CHK-39 blocks an instruction that does not name it. Omit the section
  when the helper has no tool; never name a tool that is added after the import.
- `#### 3. Rules` — the helper's own non-negotiables as `CRITICAL:` lines.

Doctrine: call-wide rules — turn-taking, human-rep and off-topic handling, negative
instructions — live once, in the persona (FP-6), and are never repeated here. A line the helper
must say aloud uses the FP-4 quote convention and the TTS-safe rules
(`${CLAUDE_PLUGIN_ROOT}/references/voice-prompt-doctrine.md` rule 8). Use no `{{…}}` variable:
nothing documents that a helper's instruction resolves them. Never a credential.

**How a helper is reached:** a helper reaches its intents through its own `IntentIds` (spec section 4.8 `**Serves intents:**`) alone. The intent's text needs no mention of the helper and must not name it as a tool.

## 3. Self-validation (blocking, before the status flip)

| # | Check |
|---|---|
| H1 | The tool description is non-empty plain prose: no Markdown, no setting value, no credential |
| H2 | Exactly one description line per argument section 4.8 declares, and none for an undeclared one |
| H3 | The instruction is non-empty and has `# 1.` Role, then only `#### 2.` Tools and `#### 3.` Rules |
| H4 | The instruction names every tool the file gives the helper, exactly, and no other tool |
| H5 | The instruction repeats no persona call-wide rule and carries no `{{…}}` |
| H6 | Nothing in any of these fields looks like a credential, token, API key or password |

On a failure, do not flip the status; surface it with its number and fix it with the user. On
a pass, set `**Status:** [detailed]`, log
`[ISO timestamp]  Skill 2  detailing  Helpers and tools: detailed <n> helpers (<list>) and <m> tools (<list>). Self-validation passed for all.`
to section 7.3, refresh 7.5, and run the checkpoint.
