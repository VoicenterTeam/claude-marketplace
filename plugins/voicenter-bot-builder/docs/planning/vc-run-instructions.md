# V-C run instructions — the Claude Code functional suite

**These cannot run in the session that authored the branch.** Claude Code resolves skills from
the *installed* plugin cache, not the working tree, so a same-session run exercises whatever
version is installed — during this release that was a stale `1.15.0`, then upstream's `1.18.0`
(recorded as finding N5 in `../../examples/baseline-notes.md`). Running V-C against the wrong
copy is worse than not running it: it reports green for code that isn't under test.

So: install from this branch, restart, **verify the loaded version**, then run.

## Setup

```sh
# 1. Point a marketplace at the local checkout (path source, not the GitHub repo)
claude plugin marketplace add /path/to/voicenter-claude-marketplace

# 2. Install from it. If voicenter-bot-builder@voicenter is already installed from the
#    published marketplace, uninstall first — two sources for one plugin name is the
#    ambiguity that produced N5.
claude plugin uninstall voicenter-bot-builder
claude plugin install voicenter-bot-builder@<local-marketplace-name>

# 3. Restart Claude Code. Registry changes do not apply to a running session.

# 4. PROVE you are testing the branch, not the cache:
claude plugin details voicenter-bot-builder
```

Step 4 is the gate on every other test in this file. The output must show:

- the **version** you expect,
- **Agents (1)** — `spec-verifier`. If it says `Agents (0)` you are on a pre-MS2 copy,
- **Skills (6)** — the three skills *plus* `bot-assemble`, `bot-detail`, `bot-spec`.

`claude plugin details` has no `Commands` category and counts `commands/*.md` under **Skills**,
so 6 is correct and does not mean the commands mis-registered. Confirm they really are commands
by typing `/bot` in the composer: they appear as `/voicenter-bot-builder:bot-*`, distinct from
the skills.

`claude plugin details` also prints projected token cost, which is the cheapest way to
sanity-check V-A5's always-loaded number without a live conversation.

## Fixtures

`../../examples/sample-spec-detailed.md` (F1) and `../../examples/sample-spec-seeded.md` (F2).
For any RT=2 step, start `../../examples/stub-api-server.py` first.

---

## V-C1 — Install and typeahead

Covered by setup step 4, plus: type `@voicenter-bot-builder:spec-verifier` in the composer and
confirm it appears in typeahead, and `/bot` and confirm all three commands complete as
`/voicenter-bot-builder:bot-*`.

## V-C2 — Skill 3 on F1, delegated

**Do:** ask Claude to assemble F1.

**Pass criteria:**
- An **Agent tool call to `spec-verifier` is visible** — this is the only test that proves
  delegation actually engages rather than §6.0 silently always falling inline.
- The returned report matches the output contract in `../../references/verification-procedure.md`
  (all blocks present, in order, severities restated not re-decided).
- Assembly proceeds; 25 checks reported.
- Emitted JSON is byte-comparable to `../../examples/expected-output-shipping.json`.

**Byte-comparability caveat (finding N6).** Skill 3 emits an assembly-time `CreatedDate` in 26
places. Normalize those and the date in the filename before diffing — the harness pins
`ASSEMBLY_TS` for exactly this reason. A diff limited to timestamp fields is a **pass**.

## V-C3 — Skill 3 on F2, delegated

**Pass criteria:** exactly checks **3 and 7 blocking, 22 advisory**; no JSON emitted; routing
names Skill 1 for 3, Skill 2 for 7 (with the Skill 1 alternative offered), Skill 1 for 22.
Compare against `../../examples/expected-violations-report.md`.

## V-C4 — Force-inline equivalence *(the load-bearing test)*

**Do:** temporarily rename `agents/` (e.g. `agents.off/`), restart, re-run V-C2 and V-C3.

**Pass criteria:** **identical verdicts** to the delegated runs — same checks, same severities,
same routing. Sensitivity differences on the judgement-heavy advisory checks are acceptable and
should be recorded; any difference in a **blocking** verdict is a hard FAIL.

This is the single-source-of-truth proof the whole MS1 refactor rests on. If inline and
delegated disagree on a blocking check, `verification-procedure.md` is being interpreted
differently by its two consumers, and the refactor has not delivered what it claims.

**Restore `agents/` afterwards.** A renamed-and-forgotten `agents/` silently disables
delegation for every later test.

## V-C5 — Isolation probe

**Do:** in the same conversation that built a spec, delegate verification.

**Pass criteria:** the verifier's report cites only spec content — never "as we discussed" or
any fact that exists solely in conversation history. The agent gets a fresh context by
construction (C3); this confirms the prompt template doesn't leak state into it.

## V-C6 — Skill 2 checkpoint/resume

**Do:** run Skill 2 on an 8–10-intent spec so batching engages. Interrupt mid-run. Re-invoke.

**Pass criteria:** the queue is rebuilt from spec section 5 markers, not from a todo list or
conversation memory (C7 — TodoWrite is ephemeral and must never hold state).

## V-C7 — Skill 1 greenfield + patch

**Pass criteria:** stage files load at the right phases; no "missing instruction" behavior where
a gutted section's content is needed but never read. This is what the MS3 split most plausibly
broke.

## V-C8 — Commands

**Pass criteria:** each `/voicenter-bot-builder:bot-*` command invokes its skill and behaves
identically to description-triggered invocation.

**Commands are namespaced.** The bare form (`/bot-spec`) does not resolve — autocomplete expands
the prefix, but typing it literally does nothing. The plugin README documented the bare form
until this was caught during the first real V-C install. The commands hand over immediately — if Claude starts
interpreting the request before invoking the skill, the command body's "hand over immediately"
instruction isn't landing.

## V-C9 — Haiku gate

**Do:** re-run V-C2 with the Assembler's `model: haiku` frontmatter in place (the shipped state).

**Pass criteria:** byte-comparability from V-C2 still holds.

**Known limitation.** The frozen goldens were produced by `assemble.py`, a mechanical
transcription — not by a model run. So the fixtures **cannot** distinguish model tiers on their
own; this test requires a real Claude Code assembly and a human diff. If haiku drifts, change
the frontmatter to `model: sonnet` and record the observed drift in the release notes rather
than loosening the comparison.

---

## Trigger evals (MS6 §6.1B) — currently blocked

`claude plugin eval` is the first-party runner (`evals/**/case.yaml` + graders), and it takes a
path, so this *should* be automatable rather than human-run. As of this release it is gated
behind **early access** and unavailable on this account; skill-creator's `run_loop.py` is not
installed either. `../../examples/trigger-evals.json` therefore holds the query sets in a
neutral format pending one of:

1. early access to `claude plugin eval`, then port the JSON to `evals/**/case.yaml` — **do not
   hand-author that schema blind**, generate a template with `claude plugin eval init --bare`
   and fill it in, or
2. a manual run per `va-run-instructions.md` §4.

## Reporting

Record pass/fail, the surface, the date, and the **version string from
`claude plugin details`** for every test — a V-C result without the version it ran against is
not evidence. File results into `../reference/validation-checklist.md` §2.

Anything that fails and touches skill logic or the verification procedure comes back for a
decision rather than being patched in place: these files are single-source now, so a local fix
propagates to every consumer.
