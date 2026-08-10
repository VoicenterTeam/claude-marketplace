# V-A run instructions — the claude.ai regression suite

**These tests cannot be run from Claude Code.** V-A is the constraint that must not break:
claude.ai runs the *skills portion only* of a plugin (constraint C8), so agents, commands and
`model` pinning are inert there. Everything load-bearing has to work skills-only, and the only
way to prove it is to run the pipeline on claude.ai.

Run these before v1.18.0 is tagged. Report results back into
`../reference/validation-checklist.md` §3 and the release notes.

## Setup

1. A claude.ai account with **"Code execution and file creation" enabled** (skills work on all
   plans including Free since 2026-02-11, but this toggle gates the runtime).
2. Install the plugin from the branch under test, or upload the three `skills/` directories.
3. Fixtures: `examples/sample-spec-detailed.md` (F1) and `examples/sample-spec-seeded.md` (F2).
4. For any RT=2 step: `examples/stub-api-server.py` is local-only and **will not be reachable
   from claude.ai**. See V-A2's note.

---

## V-A1 — Full pipeline, one conversation

**Do:** in a single conversation, design a small bot with Skill 1 (any 3–4 intent business),
detail it with Skill 2, then assemble with Skill 3.

**Pass criteria:**
- Completes end-to-end.
- **No mention of a subagent, no delegation attempt, no error and no visible hesitation at the
  dispatch point** (Skill 3 §6.0). The inline path should engage silently — a user on claude.ai
  should never learn that a delegated path exists.
- The assembler emits JSON plus a banner.

**This is the single most important test in the suite.** If §6.0's soft dispatch leaks — if
Claude announces it cannot delegate, or asks the user which path to take — the dispatch wording
is wrong and must be fixed before release.

## V-A2 — Seeded fixture, inline verification

**Do:** attach F2 (`sample-spec-seeded.md`) and ask Claude to assemble it.

**Pass criteria:** the same three violations found in Claude Code — **checks 3 and 7 blocking,
check 22 advisory** — with matching routing (3 → Skill 1, 7 → Skill 2 with the Skill 1
alternative offered, 22 → Skill 1). No JSON emitted.

- Sensitivity differences on the **advisory** check (22) between runtimes: **document, do not
  fail.**
- A missed **blocking** violation (3 or 7): **hard FAIL.**

**RT=2 caveat.** F2's RT=2 intent points at `127.0.0.1:8787`, unreachable from claude.ai. That
does not affect this test — the seeded violations are all detected from spec content, not from
calling the API, and Skill 3's gate C reads the §7.6 record F1/F2 already carry. If you want to
exercise Skill 2's *live* verification on claude.ai, substitute a publicly reachable endpoint;
that is a separate check, not V-A2.

## V-A3 — Fresh-eyes discipline observable

**Do:** in the V-A1 conversation, watch what Claude does at the start of the cross-reference
pass.

**Pass criteria:** it visibly re-reads the spec from the artifact before checking, per §6.2's
fresh-eyes rule — not verifying from memory of the conversation that just built it.

## V-A4 — TodoWrite absence is harmless

**Do:** run Skill 2 on a spec with 8+ intents so batching engages.

**Pass criteria:** no attempt to call a todo tool, no error, no complaint about one being
missing. The §2.3 mirror paragraph is explicitly optional; its absence must be silent.

## V-A5 — Context measurement *(re-scoped — see note)*

**Do:** record tokens-to-first-question for Skill 1 and total pipeline tokens, against the
v1.17.0 numbers in `ms3-token-report.md`.

**Gate:** ≥ 40% reduction in **always-loaded** context. Estimated at −75%; confirm on the live
surface.

**Note:** this was re-scoped after MS3 measurement. End-to-end happy-path cost is recorded as a
**non-gating** metric — progressive disclosure cannot shrink a run that legitimately reads every
mapping rule, and a full assembly is ~+8%. Full reasoning in `ms3-token-report.md` §3. Do not
fail the release on the end-to-end number.

## V-A6 — Bilingual smoke

**Do:** run Skill 1 Phases 1–2 in Hebrew.

**Pass criteria:**
- `AskUserQuestion` option **values/labels stay LTR-stable and readable**; Hebrew appears in
  the option descriptions (the MS5 §5.4 rule).
- Generated identifiers are ASCII — a Hebrew bot name must transliterate (`יובל` → `yuval`).
- Nothing machine-critical (filename, identifier, status marker) comes back in Hebrew.

---

## Also needs a live run: the trigger evals (MS6 §6.1B)

`examples/trigger-evals.json` carries the positive sets and the cross-fire matrix for all three
rewritten descriptions. Executing it needs model invocations with only the three skills'
name+description in context.

**Acceptance:** every positive triggers its owning skill; **no negative triggers the skill it is
listed under**, and each routes to its `expected_instead`. The file also lists three
`_ambiguous_by_design` queries that must **not** be counted as failures.

This matters more than usual for this release: MS3 cut the descriptions from ~1,100 characters to
under 200, so most of the old trigger phrases are gone. The evals are what proves the surviving
ones are the right ones.

---

## Reporting

For each test record: pass/fail, the surface (claude.ai web / desktop), the date, and any
observed difference from the Claude Code run. Anything that fails and touches skill logic or the
verification procedure should be brought back for a decision rather than patched in place —
these files are now single-source, so a local fix propagates to every consumer.
