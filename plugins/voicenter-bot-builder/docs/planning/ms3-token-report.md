# MS3 Token Report — before/after

Measured against **v1.17.0** (repo commit `cdc9922`) after the three MS3 splits and the
description rewrites.

**Method:** char-based estimate per `voice-prompt-doctrine.md` §2 (Latin/ASCII at ¼ token).
Treat §1 and §2 as ±15% estimates of **file content** — the SKILL.md body an invocation reads —
not of a live session's startup context.

**The `claude plugin details` measurement has since been taken (2026-08-15, installed 1.20.0)
and it measures a different thing — see §1b.** The two are not interchangeable, and conflating
them is what produced the stale −75% figure this report carried into the V-A5 decision below.

---

## 1. Always-loaded body (what every invocation pays before doing anything)

| Skill | v1.17.0 | v1.20.0 | Reduction |
|---|---|---|---|
| spec-designer | 26,284 tok / 1,107 ln | 4,402 tok / 290 ln | **−84%** |
| intent-detail-author | 17,643 tok / 826 ln | 6,638 tok / 395 ln | **−63%** |
| json-assembler | 33,068 tok / 1,387 ln | 8,768 tok / 397 ln | **−74%** |
| **total** | **76,995 tok** | **19,808 tok** | **−75%** |

Descriptions (loaded at startup for *every* skill, whether invoked or not) dropped from
823 / 1,096 / 1,206 characters to 187 / 188 / 198 — all now inside claude.ai's ~200-char
truncation, which the old ones blew past by 4–6×.

## 1b. Startup context — the `claude plugin details` measurement (2026-08-15)

**This, not §1, is the V-A5 number.** §1 measures the SKILL.md body a skill loads *when
invoked*; the CLI's "always-on" is what every session pays at startup before any skill fires —
names, descriptions and frontmatter only. They differ by roughly 80×, so the −75% from §1 was
never the always-on figure.

| Scope | v1.17.0 | v1.20.0 | Reduction |
|---|---|---|---|
| Skills only (3 × ~100 tok) | ~930 tok | **~300 tok** | **−68%** |
| Total plugin always-on | ~935 tok | **~551 tok** | **−41%** |

The gap between the two rows is new surface this release added, all of it always-on: the
`spec-verifier` agent (~140 tok) and three commands (~110 tok combined). Neither existed in
v1.17.0, so the total-plugin row is not a like-for-like comparison — the skills-only row is.

**On claude.ai, expect the full −68%:** agents and commands are inert there (constraint C8), so
the plugin's startup cost is the skills row alone.

Per-component on-invoke, for reference: json-assembler ~14k, intent-detail-author ~10.8k,
spec-designer ~7.2k, spec-verifier ~990. Note the assembler's ~14k against §1's 8,768 char-based
estimate — the char method under-reads by ~40% at this size, which is worth remembering before
quoting §1/§2 anywhere a real number matters.

## 2. Per-scenario invocation cost — the number that actually matters

| Scenario | v1.17.0 | v1.20.0 | Change |
|---|---|---|---|
| Skill 3 — full assembly (happy path) | 33,068 | 35,781 | **+8%** |
| Skill 3 — halts at a pre-flight gate | 33,068 | 8,768 | −74% |
| Skill 3 — halts on a parse error | 33,068 | 9,815 | −71% |
| Skill 3 — delegated verify (procedure read by the agent, not the parent) | 33,068 | 26,939 | −19% |
| Skill 1 — greenfield full run | 26,284 | 25,951 | −2% |
| Skill 1 — patch mode | 26,284 | 14,843 | **−44%** |
| Skill 2 — full detailing run | 17,643 | 18,253 | **+3%** |
| Skill 2 — resume, everything already `[detailed]` | 17,643 | 6,638 | −63% |

---

## 3. Finding: V-A5's 40–60% expectation is not achievable by splitting alone

`validation-checklist.md` V-A5 and MS3's done-criteria expect **40–60% reduction on Skill 3
invocations**, and MS3 says that if the reduction is absent, *"the classification in the split
was wrong — fix before proceeding."*

The reduction is absent on the happy path, and the classification is **not** the reason.

Progressive disclosure only pays when an invocation reads a *subset* of the procedure. It
cannot pay when the happy path reads all of it:

- A Skill 3 invocation that actually assembles **must** read the full field mapping — every
  emitted field traces to a rule in it. Nothing there is skippable, so deferring it changes
  *when* it loads, not *whether*. The split then costs a little extra for the new TOCs,
  headers and load-instruction tables: **+8%**.
- Same shape for Skill 1 greenfield (−2%) and Skill 2 full detailing (+3%) — both walk their
  whole procedure by definition.
- The wins are real but they live on the **conditional** paths: early exits (−71/−74%),
  patch mode not reading the interview (−44%), and resume-with-nothing-to-do (−63%).

So the split delivers what progressive disclosure can deliver. What it cannot do is shrink a
run that legitimately needs every rule.

**Getting 40–60% on a full assembly would require compressing the mapping content itself** —
deduplicating the v1.5.0/v1.13.0/v1.14.0 changelog prose that is interleaved with the live
rules, and tightening the field tables. That is a rewrite, which MS3 explicitly forbids
("content moves verbatim") and which locked decision S keeps out of a structural refactor.

### Options for MS6

1. **Re-scope V-A5 to always-loaded context** (where the real measured result is −68% on
   skills, comfortably past the bar — see §1b) and measure happy-path cost separately as a non-gating metric. This matches what the
   objective O2 text actually describes — "measurable context reduction".
2. **Keep V-A5 as an end-to-end target** and schedule a *content* compression pass as its own
   version after v1.20.0, with the golden fixture proving byte-comparability across it.
3. **Accept +8%** on the happy path as the cost of the conditional-path wins, and record it in
   the release notes.

### Decision

**Option 1, decided 2026-08-10.** V-A5 is re-scoped to always-loaded context in
`../reference/validation-checklist.md` (gate: ≥ 40% reduction; **actual −68% skills-only /
−41% total plugin**, measured 2026-08-15 per §1b — the −75% this file originally cited was the
char-based file-body estimate from §1, not a startup measurement). MS6 acceptance
criterion 6 is updated to match, and the content-compression pass is scheduled as its own
version in `00-overview.md` §6.

Rationale: the always-loaded reduction is the real user-visible win — it is what *every*
invocation pays, including the many that early-exit before touching a stage file. A content
compression pass deserves its own version, where the frozen golden fixture can gate
byte-comparability honestly instead of being entangled with a structural refactor.

The per-scenario table in §2 stays in the release notes as a recorded, non-gating metric, so
the +8% on happy-path assembly is visible rather than buried.
