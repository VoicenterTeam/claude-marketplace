# Skill Authoring Standards for This Plugin

House rules derived from Anthropic's official guidance + the constraints in
`runtime-constraints.md`. Every skill/stage/reference file in the plugin must
comply. MS3 enforces these; MS6's static checks verify them.

## 1. File structure

| Rule | Value | Why |
|---|---|---|
| SKILL.md body length | ≤ 400 lines (hard ceiling 500) | Official 500-line guidance; 100-line headroom for the patch cadence |
| Reference/stage file depth | One level from SKILL.md | Deep chains risk partial reads |
| TOC | Required in any file > 100 lines | Official best practice; improves partial-read behavior |
| Stage-file chaining | Forbidden (stage → stage) | Depth rule; stages may point to shared `references/` via `${CLAUDE_PLUGIN_ROOT}` only |
| Cross-package pointers | `${CLAUDE_PLUGIN_ROOT}/…` always | C5 — relative escapes break post-install |

**What stays in SKILL.md (always-loaded):** decision logic, guardrails,
anti-lists, dispatch, setup/mode detection, control-flow mechanics (batching
rules, checkpoint gates, status mechanics).
**What moves to stages:** procedural walk-throughs, field mappings, per-phase
scripts, worked examples, output format samples.
**Tiebreaker:** "If Claude skipped this until the moment it's needed, could
anything go wrong earlier?" Yes → always-loaded.

## 2. Description standard

The description is the trigger — at startup only name+description load, and
Claude matches requests against them.

- **≤ 200 characters** (claude.ai truncation is the binding constraint; the
  1,024-char spec limit is irrelevant to us).
- Third person, **trigger-first**: open with "Use when…" naming the
  *condition*, not the topic.
- Include the literal phrases users actually type (the highest-value 2–3 from
  the old long lists — not all of them).
- **Negative scoping** to prevent cross-fire among the three skills
  ("Does NOT design specs or author intents").
- **Never summarize the workflow** — a workflow-summarizing description tempts
  the model to follow the description instead of reading the body.
- English. Runtime bilingualism (Hebrew/English mirroring) lives in the skill
  body, unchanged.

## 3. Skill body conventions

- Consistent terminology across all three skills (same names for the spec,
  section 5 statuses, CHK IDs, RT terms).
- State rules with their rationale; avoid walls of ALL-CAPS MUST/NEVER —
  one clear sentence with a why outperforms shouting.
- Stepwise numbered procedures for anything sequential.
- Anti-lists stay — they are decision logic. Keep entries short: violation +
  one-line why.
- `model` frontmatter: only where a stage is genuinely mechanical
  (currently: Assembler `model: haiku`, gated on the MS5 haiku eval).
  Aliases only, never dated model IDs.

## 4. Bilingual / RTL conventions

- Machine-critical text is ASCII/LTR: JSON keys, enum values, filenames,
  identifiers, CHK IDs, status markers.
- Hebrew appears in: user-facing prose, spoken-content fields' *values*,
  descriptive halves of AskUserQuestion options. Option values/identifiers
  stay LTR-stable.
- Instructions that display generated JSON or spec excerpts must fence them
  in code blocks (code blocks render LTR in bidi-weak surfaces).

## 5. Change discipline

- CHK IDs are stable forever: never renumber; retire and append.
- Plugin `name` is immutable; label changes go through `displayName`.
- Semver: user-visible behavior change → minor; fixes → patch; wire-format
  breaking change → major. Version bump + CHANGELOG entry + git tag move
  together, always.
- Golden files (`examples/`) change **only** in the same commit as an
  intentional behavior change, with the CHANGELOG entry explaining the diff.
- No functional fix rides along with structural refactors (locked decision S
  generalized): byte-comparability is only provable when refactor commits are
  pure.
