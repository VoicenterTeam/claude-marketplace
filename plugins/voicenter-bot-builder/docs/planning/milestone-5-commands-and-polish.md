# Milestone 5 — Slash Commands, Model Pinning, TodoWrite Mirror, RTL Hardening

**Objective:** deterministic invocation entry points, cheaper mechanical
stages, in-session queue visibility, and defenses for the Hebrew/English
surface. All items degrade gracefully in claude.ai (commands and `model` are
Claude Code extensions; claude.ai ignores them without error).

**Depends on:** MS3 (descriptions and structure settled first — commands
reference the final skill shapes).

## Steps

### 5.1 Slash commands

The pipeline is user-driven and staged — explicit commands beat pure
description-triggering for invocation reliability and give clean control
points. Add `commands/`:

```
commands/
├── bot-spec.md       # invokes Skill 1 (greenfield or patch — the skill's own mode detection decides)
├── bot-detail.md     # invokes Skill 2 (queue rebuild from section 5, as always)
└── bot-assemble.md   # invokes Skill 3
```

Each command file: one-paragraph body that states the target skill by
namespaced name and hands over immediately. Commands add **no logic** — mode
detection, queue construction, and dispatch all stay in the skills. The
description-based auto-trigger remains as fallback for users who just type
"design a bot".

### 5.2 Model pinning

- `skills/voicenter-bot-json-assembler/SKILL.md` frontmatter: add
  `model: haiku`. Assembly is a deterministic projection — "pure parser, not
  interpreter" — main-model cost is waste. Use the **alias**, never a pinned
  model ID (durability across releases).
- Do **not** pin Skill 1 or Skill 2 — interview reasoning and language
  authoring want the session's model (`inherit` default).
- claude.ai ignores the `model` field (Claude Code extension) — no
  degradation risk, but record it in README known-limitations as a
  cost-behavior difference between surfaces.
- ⚠ Gate: before shipping, run the MS6 golden-file eval **with haiku** on the
  Assembler. If byte-comparability holds (it should — the task is mechanical),
  ship. If any semantic drift appears in sentinel/banner text, fall back to
  `sonnet` and record why.

### 5.3 TodoWrite mirror (Skill 2)

Add one paragraph to Skill 2 SKILL.md §2.3, immediately after work-queue
construction:

> If a todo-list tool is available, you may mirror the work queue into it for
> visibility — one item per batch, checked off at each checkpoint. The mirror
> is never authoritative: the spec's section-5 status markers are the sole
> source of truth, and queue reconstruction at every invocation reads
> section 5, never the todo list. If no todo tool exists, proceed without one.

Nothing else changes. The §8 checkpoint mechanic is untouched. (Constraint
C7: TodoWrite is ephemeral and absent in claude.ai — this wording makes both
facts harmless.)

### 5.4 RTL / bidi hardening

Terminal surfaces (Claude Code CLI, VS Code, Desktop) do not render RTL
reliably; claude.ai web is better. Defenses:

- **Machine-critical output stays ASCII/LTR:** JSON keys, enum values,
  filenames, CHK IDs, section markers. Hebrew belongs only in *values* the
  bot will speak/display. Audit: the known `bot-bot-` filename gap from
  Hebrew names is Conv 3a scope (decision S) — do not fix here, but confirm
  no *new* Hebrew-derived identifiers were introduced by MS1–3.
- **Fence generated JSON and spec excerpts in code blocks** wherever skills
  instruct Claude to display them — code blocks render LTR.
- **AskUserQuestion labels:** keep option *values*/identifiers LTR-stable;
  Hebrew goes in the descriptive text. Sweep all three skills' AskUserQuestion
  instructions for compliance.
- README known-limitations note (written in MS4) covers user expectations.

## Done criteria

- [ ] Three commands invoke the correct skills; skills behave identically to
      description-triggered invocation
- [ ] `model: haiku` on Assembler; golden-file eval passes under haiku
      (or documented fallback to sonnet)
- [ ] TodoWrite paragraph in Skill 2; pause/resume still rebuilds queue from
      section 5 (V-C6); claude.ai run makes no todo attempt (V-A4)
- [ ] RTL sweep done: no Hebrew in machine-critical fields introduced by this
      release; JSON display fenced; AskUserQuestion values LTR-stable
- [ ] `claude plugin validate --strict` still clean after adding commands/
