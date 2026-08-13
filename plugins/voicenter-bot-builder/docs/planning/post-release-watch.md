# Post-release watch — v1.19.0

Opened per MS6 §6.5. Feeds the next planning cycle. Nothing here is scheduled work yet; these
are the things whose answers only production can supply.

---

## 1. Locked decision R — the Skill 2 drafting subagent

**Revisit after ~50 builds on v1.19.0.**

R deferred a per-batch drafting subagent for Skill 2, on the theory that late-batch quality decay
might be a context-pressure symptom that MS3's lean-context world would fix on its own. That is
now testable: Skill 2's always-loaded body dropped 63%.

**What to watch:** whether intents detailed in batch 3+ still show lower quality than batch 1 —
weaker capture mappings, drifting register, more check-19 duplicates surfacing at assembly.

If decay persists in a lean-context world, the context-pressure theory was wrong and the subagent
is worth building. If it disappears, R can be retired rather than re-litigated.

## 2. Conv 3a functional patches — v1.19.0 candidate

Held out of v1.19.0 by locked decision S so byte-comparability could prove the refactor was
inert. Now unblocked:

- **S1 `Identifier:` field** handling.
- **Section 4 RT sub-label grammar.**
- **The `bot-bot-` filename gap** on Hebrew bot names (surfaced again in the MS5 RTL sweep, left
  alone as decision-S scope).

**Discipline for that release:** these change emitted output, so `examples/expected-output.json`
must be regenerated **in the same commit**, with the CHANGELOG entry explaining the diff. That is
the one sanctioned way a golden file moves.

## 3. Field-mapping content compression — next version

Decided during MS3 (see `ms3-token-report.md` §3). Progressive disclosure cannot shrink a
full-assembly run; only compressing the mapping content can. The specific target: the
v1.5.0/v1.13.0/v1.14.0 changelog prose interleaved with the live field rules in
`stages/assembly-mapping.md`.

Do it as its own version so the frozen golden gates byte-comparability honestly instead of being
entangled with a structural refactor.

## 4. Cowork-only PostToolUse validation hook — v1.19+ candidate

Progressive enhancement only, **never load-bearing** (constraint C8: hooks are inert in claude.ai
consumer chat). Idea: run the static V-S checks automatically after a skill writes a spec.

Gate any design on the rule that removing the hook must change nothing about correctness.

## 5. Re-verify the ⚠ items in `runtime-constraints.md`

Every one of these has changed within recent minor versions. Re-check before relying on them
again:

| Item | Why it moves |
|---|---|
| **C9 description limits** | The 200-char claude.ai truncation is the binding constraint on all three descriptions. If it changes, the MS3 rewrites should be revisited. |
| **`model` frontmatter behaviour** | The Assembler now pins `model: haiku`. If claude.ai stops ignoring it gracefully, that becomes a real cross-surface difference. |
| **Subagent mechanics** | Nesting depth, the Task→Agent rename, concurrency defaults. The verifier is a leaf, so nesting is irrelevant *today* — but §6.0's wording deliberately says "delegate to the agent" rather than naming a tool, and that should stay true. |
| **Plugin-agent frontmatter allow-list (C4)** | V-S4 lints against it. If the allow-list grows, the lint should follow rather than block a legitimate field. |

## 6. Carried-forward gates from v1.19.0

Not watch items — **open obligations** that were not closed before this note was written:

| Gate | Status | Owner |
|---|---|---|
| V-C1/2/3/4/6/7 — Claude Code functional suite | not run; needs an install from the branch — procedure in `vc-run-instructions.md` | — |
| V-C9 — haiku byte-comparability for `model: haiku` | **not run**, and the fixtures cannot decide it (goldens come from `assemble.py`, not a model run). If it drifts, fall back to `model: sonnet` and record why | — |
| V-A1…V-A6 — claude.ai regression | not run; see `va-run-instructions.md` | human |
| Trigger evals (MS6 §6.1B) | query sets built; runner (`claude plugin eval`) is **early-access** and unavailable | — |
| LICENSE sign-off on bundled reference material | **pending**; blocks submission | legal |
| Marketplace root + sibling manifests fail `--strict` | tracked in `license-decision.md` §3.2 | — |
| `docs/` ships inside the plugin | decide leave-or-relocate | — |

## 6a. Upstream collision — what MS7 absorbed

A **functional v1.18.0** (`1fa1351`) shipped on `main` mid-release, which is why the structural
release is numbered **1.19.0**. MS7 merged it. Three consequences worth carrying forward:

- **The single-source design was load-tested by accident and held.** Upstream added check 25;
  integrating it meant one entry in `verification-procedure.md` plus a TOC line, a severity cell
  and a run-order position. Nothing else in the plugin needed a check *procedure* edit.
- **But the check *count* is echoed in 7 files** (`agents/spec-verifier.md`, both Skill 3 dispatch
  sections, Skill 1's cross-reference, `self-validation.md`, the plugin README, the fixtures
  README). MS1 de-duplicated the procedures and left the arithmetic duplicated. A follow-up
  should either drop the counts in favour of "the checks in `verification-procedure.md`" or add a
  V-S check that asserts every stated count matches the file. **Low severity, high annoyance.**
- **Two goldens now exist** for the reason explained in `../../examples/README.md`. The frozen one
  is still byte-identical after the merge, which is the actual evidence that the restructure was
  inert. Keep the "delta between goldens is exactly one key" CI assertion — it is what bounds
  future functional releases.

## 7. The eight v1.17.0 findings in `examples/baseline-notes.md`

Recorded during S0 and deliberately not fixed, except N1:

- **N1 — FIXED.** Skill 1's template now paraphrases the opening context, and CHK-19 skips
  fully-parenthesised lines. Shipped as a deliberate exception to decision S because the
  fixtures do not move (fix A touches Skill 1's *template*, not F1's spec; fix B touches only
  the check) and because it blocked the documented happy path. Locked by
  `../../examples/test-chk19-regression.py` — **watch its third case**, which asserts a real
  duplicate still fails. That case going quiet means the exclusion widened too far.
- **N6** — V-C2's byte-comparability was unachievable as originally written (26 assembly-time
  timestamp fields). Worked around by pinning `ASSEMBLY_TS` in the harness; a real fix means
  either widening the normalization or giving Skill 3 a deterministic-timestamp mode.

N2 (`Asks next:` has no literal for auto-chaining non-terminals), N3, N4, N5, N7 (skeleton §6.5
vs §4.1 ID ranges — guaranteed drift on every bot) and N8 are lower severity but all real.
