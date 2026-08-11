# voicenter-bot-builder — v1.19.0 Implementation Docs

Working docs for the v1.19.0 redesign of `plugins/voicenter-bot-builder`:
subagent verification, progressive disclosure restructuring, and Anthropic
plugin directory publication readiness.

## How to use with Claude Code

Point Claude Code at this folder and a milestone:

> Read `docs/planning/00-overview.md`, then execute
> `docs/planning/milestone-1-verification-extraction.md`.
> Consult `docs/reference/` whenever a milestone cites it.

Rules for the implementing agent:

1. **Execute milestones in order.** Each milestone leaves the plugin shippable.
   Do not start milestone N+1 with milestone N's done-criteria unmet.
2. **One milestone = one commit** (or a small commit series). Never mix
   milestone scopes in a commit.
3. **Reference docs are constraints, not suggestions.** If an implementation
   choice conflicts with `reference/runtime-constraints.md`, the reference
   wins. If the reference seems wrong, stop and ask the user — do not
   improvise around it.
4. **Never bundle unrelated fixes.** Pending items (Conv 3a Identifier field,
   RT sub-label grammar) are explicitly OUT of scope for v1.19.0 — byte
   comparability of Skill 3 output (V-C2) depends on this.
5. When a milestone changes any file, re-run the static checks in
   `reference/validation-checklist.md` §1 before declaring the milestone done.

## Structure

```
docs/
├── README.md                                  ← this file
├── planning/
│   ├── 00-overview.md                         ← goals, constraints, locked decisions, milestone map
│   ├── milestone-1-verification-extraction.md ← single-source verification-procedure.md
│   ├── milestone-2-verifier-agent.md          ← agents/spec-verifier.md + soft dispatch
│   ├── milestone-3-progressive-disclosure.md  ← SKILL.md splits + description rewrites
│   ├── milestone-4-marketplace-readiness.md   ← manifest, LICENSE, README, CHANGELOG, privacy
│   ├── milestone-5-commands-and-polish.md     ← slash commands, model pinning, TodoWrite, RTL hardening
│   ├── milestone-6-validation-and-release.md  ← eval harness, full test pass, submission
│   └── session-prompts.md                     ← copy-paste start prompts per session (S0–S4) + resume prompt
└── reference/
    ├── runtime-constraints.md                 ← verified platform facts (C1–C9)
    ├── marketplace-requirements.md            ← directory submission process + policy requirements
    ├── skill-authoring-standards.md           ← size limits, description limits, disclosure rules
    ├── verification-output-contract.md        ← the report format both verification paths emit
    └── validation-checklist.md                ← V-S / V-C / V-A test suites + acceptance criteria
```

## Version anchors

- Plugin baseline: **v1.17.0** (skills-only; SKILL.md sizes 1,106 / 825 / 1,386 lines)
- Target: **v1.19.0**
- Research verified against docs current as of **2026-08-08**. Claude Code
  subagent mechanics change frequently within minor versions — re-verify
  `reference/runtime-constraints.md` items marked ⚠ before relying on them.
