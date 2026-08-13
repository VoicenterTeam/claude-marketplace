# v1.20.0 Overview — Goals, Constraints, Milestone Map

## 1. Why this release exists

After a few hundred production builds on v1.17.x, three problems:

1. **Verifier anchoring.** Skill 3's 24-check cross-reference pass runs inside
   the same context that watched the spec get built. It verifies what it
   remembers intending, not what is written. A fresh-context verifier is a
   better verifier.
2. **Context bloat.** SKILL.md files are 1,106 / 825 / 1,386 lines — 2–3×
   Anthropic's 500-line guideline — and each skill's required-reading table
   pulls large doc sections on every invocation. Cost, latency, and probable
   late-batch quality decay all trace here.
3. **Publication.** The plugin will be submitted to Anthropic's plugin
   directory (community-driven directory via in-app form → auto-mirrored,
   with "Anthropic Verified" as an aspirational follow-up). That imposes
   manifest, docs, licensing, privacy, and validation requirements the repo
   does not currently meet.

## 2. Objectives (priority order)

| # | Objective | Measured by |
|---|---|---|
| O1 | Fresh-context verification in Claude Code / Cowork, identical verdicts inline | V-C3 = V-C4 equivalence |
| O2 | All SKILL.md ≤ 400 lines; measurable context reduction | V-A5: expect 40–60% reduction on Skill 3 invocations |
| O3 | Zero regression in claude.ai consumer chat | V-A1 full pipeline pass, no subagent artifacts |
| O4 | Directory-submission ready | Gap list G1–G10 closed, `claude plugin validate --strict` clean |

## 3. Hard constraints

Full detail and citations in `../reference/runtime-constraints.md`. Summary:

| ID | Constraint | Design consequence |
|---|---|---|
| C1 | No documented capability probe for Task/Agent tool availability | Soft dispatch: inline is default+authoritative; delegation is opportunistic |
| C2 | Subagents are headless (AskUserQuestion filtered from all subagents) | Verifier fully autonomous; all user interaction stays in parent |
| C3 | Subagents see only their delegation prompt, never parent conversation | Parent passes spec path + plugin root explicitly |
| C4 | Plugin agents: `hooks`, `mcpServers`, `permissionMode` silently ignored | Verifier read-only via `tools` / `disallowedTools` only |
| C5 | Cross-file refs via `${CLAUDE_PLUGIN_ROOT}`; relative paths escaping plugin root break post-install | All shared-file pointers use the variable |
| C6 | SKILL.md ≤ 500 lines; refs one level deep; TOC for files > 100 lines | Governs the milestone-3 split |
| C7 | TodoWrite ephemeral, absent in claude.ai chat | Mirror only, never authoritative |
| C8 | claude.ai runs the **skills portion only** of a plugin; agents/hooks are Cowork/Claude Code only | Everything load-bearing must work skills-only |
| C9 | claude.ai truncates skill descriptions at **200 chars** (spec allows 1,024; Claude Code listing 1,536 combined) | Descriptions rewritten trigger-first, ≤200 chars |

## 4. Locked decisions (registry additions)

Continue the existing A–P registry:

- **Q — Soft dispatch, no capability probing.** The dual verification path is
  implemented as "inline default, delegation opportunistic." No skill text may
  instruct probing for tool availability; no branch may block on it. Rationale:
  C1 — the probe mechanism does not exist in any documented form.
- **R — Skill 2 drafting subagent deferred.** Not in v1.20.0. Re-evaluate only
  after ~50 post-release builds show whether late-batch quality decay persists
  in a lean-context world. Do not re-litigate inside this release.
- **S — No functional changes ride along.** Pending Conv 3a items (S1
  `Identifier:` field; sec 4 RT sub-label grammar) ship in a separate version.
  V-C2 byte-comparability is the enforcement mechanism.

## 5. Milestone map

Each milestone leaves the plugin installable and functional in both runtimes.

| MS | Name | Delivers | Depends on |
|---|---|---|---|
| 1 | Verification extraction | `references/verification-procedure.md` single source; Skill 3 §6 becomes pointer; doctrine headers become pointers | — |
| 2 | Verifier agent + dispatch | `agents/spec-verifier.md`; Skill 3 §6.0–6.2 soft dispatch + fresh-eyes inline mode | MS1 |
| 3 | Progressive disclosure | All three SKILL.md ≤ 400 lines with `stages/` files; all three descriptions rewritten ≤ 200 chars | MS1 (Skill 3 §6 already slimmed) |
| 4 | Marketplace readiness | `plugin.json` manifest, LICENSE, README (≥3 example prompts, support contact), CHANGELOG, privacy statement, validate-clean | — (parallelizable with 1–3) |
| 5 | Commands & polish | `/bot-spec` `/bot-detail` `/bot-assemble` commands; `model: haiku` on Assembler; TodoWrite mirror note; RTL hardening | MS3 |
| 6 | Validation & release | Eval harness (golden-file byte-compare + trigger tests), full V-suite pass, version bump, tag, submission | MS1–5 |

## 6. Out of scope for v1.20.0

- Skill 2 per-batch drafting subagent (decision R)
- Conv 3a functional patches (decision S)
- Cowork-only PostToolUse validation hook — recorded as candidate for v1.21
  (progressive enhancement, never load-bearing; see milestone-5 §5)
- BotIntentTypeID semantics (still awaiting production observation)
- **Field-mapping content compression** — recorded as the next version after
  v1.20.0. MS3 proved progressive disclosure cannot reduce a full-assembly run
  (it must read every mapping rule); shrinking that path needs the interleaved
  v1.5.0/v1.13.0/v1.14.0 changelog prose deduplicated out of the live rules.
  That is a content rewrite, so it gets its own version where the golden fixture
  can gate byte-comparability honestly. See `ms3-token-report.md` §3.
