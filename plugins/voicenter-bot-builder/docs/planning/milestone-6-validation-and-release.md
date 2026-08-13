# Milestone 6 — Eval Harness, Full Validation Pass, Release & Submission

**Objective:** prove equivalence and non-regression, wire permanent regression
protection into CI, ship v1.20.0, submit to the directory.

**Depends on:** MS1–5 complete.

## Steps

### 6.1 Build the eval harness

Two eval families, both permanent (they run on every future push — directory
CI auto-mirrors repo updates, so every push is effectively a release):

**A. Golden-file assembly eval (byte-compare).**
- Fixtures: `examples/sample-spec-detailed.md` → `examples/expected-output.json`
  (created in MS4.5), plus a **seeded-violations variant** with exactly three
  deliberate breaks: one blocking structural (RT=2 pairing, CHK-05/06 class),
  one Mustache resolvability (CHK-07 class), one advisory FP violation.
- Assertions: clean fixture assembles to byte-identical JSON (normalize the
  date in the filename only); seeded fixture reports exactly the three
  violations with correct severity and routing, and blocking ones block.
- Use skill-creator's eval tooling (`evals.json` + grader) where it fits;
  a plain script diff is acceptable for the byte-compare itself —
  determinism is the point, an LLM grader adds noise.

**B. Trigger evals for the three descriptions.**
- Use skill-creator's description-optimization loop (`run_loop.py`, ~20
  queries) per skill: positive set (phrases that must trigger, drawn from the
  removed long-form trigger lists) and negative set (phrases that must trigger
  a *different* skill of the three — the cross-fire matrix).
- Acceptance: no cross-fire between the three skills on the negative set;
  all positives trigger.

Wire both into GitHub Actions alongside the MS4.7 validate job.

### 6.2 Execute the full validation suite

Run everything in `../reference/validation-checklist.md`, in order: V-S
(static) → V-C (Claude Code functional) → V-A (claude.ai regression). Record
results in the release notes. The suite's acceptance criteria are the release
gate — notably:

- V-C2 **byte-comparability** with v1.17.0 output (proves the restructure
  changed zero assembly behavior — enforcement of locked decision S)
- V-C4 **inline/delegated equivalence** (proves single source of truth)
- V-A1 **claude.ai full-pipeline pass** with zero subagent artifacts
- V-A5 **context reduction measured** (target 40–60% on Skill 3 invocations)

### 6.3 Release

1. Final `CHANGELOG.md` entry; bump `plugin.json` to `1.20.0`; then tag with
   **`claude plugin tag ./plugins/voicenter-bot-builder`** rather than a hand-written
   `git tag`. The CLI mints `{name}--v{version}` (**double** hyphen —
   `voicenter-bot-builder--v1.20.0`, not the single-hyphen form this doc originally
   specified) and **validates that `plugin.json` and the enclosing marketplace entry
   agree** before creating it. That is exactly the lockstep-version rule CLAUDE.md
   imposes, enforced by a tool instead of by discipline. Use `--dry-run` first;
   `--push` when the version bump is final.
2. Update plugin `description` in plugin.json + marketplace.json if the MS3
   rewrites changed the one-liner.
3. Push. Remind self-hosted-marketplace users: third-party marketplaces
   default auto-update **off** — publish a short upgrade note (enable
   auto-update or `/plugin` refresh manually).

### 6.4 Directory submission

Per `../reference/marketplace-requirements.md`:

1. Confirm the repo is fully public.
2. Run `claude plugin validate --strict` one final time on the exact HEAD
   being submitted.
3. Submit the GitHub link via the in-app form — claude.ai admin settings
   (Team/Enterprise org, Owner role) **or** Console at platform.claude.com
   (any account with Developer+ role). **Not a PR** — PRs against Anthropic's
   directory repos are auto-closed.

   **Name the plugin and its subdirectory explicitly — never submit a bare
   monorepo root.** This repo is a marketplace containing three plugins, and an
   indexer given only the root URL captured the *marketplace* name `voicenter` as
   if it were a plugin, producing an entry that could not resolve to any manifest
   (claude-plugins-community issue #6 — see
   `../../../../docs/community-marketplace-issue-6-reply.md` for the exchange and
   what we changed). State: plugin name `voicenter-bot-builder`, path
   `plugins/voicenter-bot-builder`, manifest
   `plugins/voicenter-bot-builder/.claude-plugin/plugin.json`.
4. Expect automated safety screening; review time varies with queue volume —
   no SLA. The skills-only, no-network, no-hooks profile is a strength; the
   README data-handling statement makes it legible to reviewers.
5. After acceptance: pushes auto-mirror with re-screening; version bumps
   control what installed users receive.
6. Aspirational follow-up: "Anthropic Verified" badge — criteria not public;
   clean profile + docs + reviewer test kit improve odds. Do not plan around it.

### 6.5 Post-release watch items

Open a tracking note (feeds the next planning cycle):
- ~50 builds on v1.20.0 → re-evaluate locked decision R (Skill 2 drafting
  subagent) against observed late-batch quality.
- Conv 3a patches (decision S) → v1.21.0 candidate, with the golden files
  updated deliberately in the same commit.
- Cowork-only PostToolUse validation hook → v1.21+ candidate, progressive
  enhancement only.
- Re-verify ⚠-marked items in `../reference/runtime-constraints.md`
  (description limits, model-field behavior, subagent mechanics) — all have
  changed within recent minor versions.

## Done criteria

- [ ] Both eval families green in CI
- [ ] Full V-suite pass recorded; all acceptance criteria met
- [ ] v1.20.0 tagged, CHANGELOG/plugin.json/tag consistent
- [ ] Directory submission sent; submission date + channel recorded
- [ ] Post-release watch note opened
