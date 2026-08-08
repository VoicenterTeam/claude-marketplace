# Session Prompts — v1.18.0 Implementation

Copy-paste start prompts for each Claude Code session. Sessions map to
milestones as follows (grouping rationale: context weight and dependency,
not 1:1):

| Session | Scope | Rationale |
|---|---|---|
| S0 | Baseline capture (pre-milestone) | Must run on untouched v1.17.0; cannot share a session with refactor work |
| S1 | MS1 + MS2 | Both live inside Skill 3 §6; splitting doubles context loading |
| S2 | MS3 | Heaviest session — three SKILL.md splits; runs alone so classification judgment gets a clean context |
| S3 | MS4 + MS5 | Both light metadata/polish work, no interdependency |
| S4 | MS6 | Validation + release; fresh context so validation isn't anchored on implementation memory |

Rules that apply to every session:
- One session's scope = one commit (or a small series within scope).
- If a session stalls or context degrades, stop at a clean boundary, commit,
  and resume with the same prompt — milestone done-criteria define the resume
  point, not conversation memory.
- Never regenerate `examples/` fixtures after S0. They are frozen v1.17.0
  baseline (see S0 prompt, step 2/4).

---

## S0 — Baseline capture (run FIRST, before any milestone)

```
You are working in the VoicenterTeam/claude-marketplace repo, on
plugins/voicenter-bot-builder, currently at v1.17.0. Read
plugins/voicenter-bot-builder/docs/README.md and
docs/planning/00-overview.md first, then
docs/reference/validation-checklist.md §Fixtures.

Task — baseline capture. This must complete BEFORE any v1.18.0 milestone
work, because the release's byte-comparability gate (V-C2) compares against
output frozen from the current, untouched v1.17.0.

1. Create examples/sample-spec-detailed.md: a complete Agent Spec for a
   fictional business (invent a small appointment-booking clinic, English,
   voice channel), fully compliant with the strict template (Doc 2 §3.7),
   8–10 intents, every section-5 entry marked [detailed], at least one
   intent per RT type (RT=1/2/3/4), at least two Mustache variable uses,
   and one callback block. Author it by actually running Skill 1 then
   Skill 2 on yourself — do not hand-write the spec freestyle; the fixture
   must be a legitimate pipeline product.
2. Run Skill 3 (v1.17.0, as-is) on that spec. Freeze the output verbatim as
   examples/expected-output.json. Record the banner output in
   examples/expected-banner.txt.
3. Create examples/sample-spec-seeded.md: copy of the clean spec with
   exactly the three violations defined in validation-checklist.md §Fixtures
   (F2). Document each seeded violation's location in
   examples/seeded-violations.md.
4. Run Skill 3 on the seeded spec; record which checks fired, their
   severity, and routing, in examples/expected-violations-report.md. This is
   the v1.17.0 detection baseline that V-C3/V-C4/V-A2 compare against.
5. Commit as a single commit: "test fixtures: freeze v1.17.0 baseline
   (F1/F2 + expected outputs)". Touch nothing outside examples/.

Constraint: zero modifications to any skill, reference, or manifest file in
this session. If you find a bug in v1.17.0 while generating fixtures, record
it in examples/baseline-notes.md and continue — do not fix it (locked
decision S, see 00-overview.md §4).
```

Human review gate after S0: read the generated spec for business
plausibility before treating the golden files as frozen. If the spec is
implausible or non-canonical, discard the commit and rerun S0 — do not
hand-patch the fixture.

---

## S1 — MS1 + MS2 (verification extraction + verifier agent)

```
You are working in the VoicenterTeam/claude-marketplace repo, on
plugins/voicenter-bot-builder. Read
plugins/voicenter-bot-builder/docs/README.md and
docs/planning/00-overview.md, then execute
docs/planning/milestone-1-verification-extraction.md followed by
docs/planning/milestone-2-verifier-agent.md.

Follow the README's operating rules strictly — especially: references win
over improvisation; no ride-along fixes (locked decision S); run the
relevant V-S checks from docs/reference/validation-checklist.md before
declaring each milestone done. Consult
docs/reference/verification-output-contract.md when embedding the output
contract (MS1 step 1.2) — the shipped copy in verification-procedure.md is
authoritative at runtime, so embed it faithfully.

The v1.17.0 baseline fixtures are in examples/ — never regenerate them. Use
them for the MS1 smoke run (done-criterion: same JSON as
examples/expected-output.json for the clean fixture) and the MS2
done-criteria (V-C2/V-C3/V-C4 subset).

Commit plan: one commit for MS1, one for MS2. If V-C4 (force-inline
equivalence) fails, the divergence is a bug in either the extraction or the
dispatch — fix within this session before committing MS2; do not defer it.
```

---

## S2 — MS3 (progressive disclosure + description surgery)

```
You are working in the VoicenterTeam/claude-marketplace repo, on
plugins/voicenter-bot-builder. Read
plugins/voicenter-bot-builder/docs/README.md and
docs/planning/00-overview.md, then execute
docs/planning/milestone-3-progressive-disclosure.md. Keep
docs/reference/skill-authoring-standards.md open throughout — it defines
the classification rule, the description standard, and the structural
limits this milestone enforces.

Work order: Skill 3, then Skill 1, then Skill 2. Apply the classification
rule per section explicitly — when a section is ambiguous, state your
classification reasoning in one line before moving it. If you cannot decide,
default to always-loaded (the cost of over-retaining is tokens; the cost of
over-moving is a missing guardrail).

Content moves verbatim — this milestone relocates text, it does not rewrite
it. The only newly authored text is: one-line summaries + load instructions
in SKILL.md, stage-file TOCs, and the three frontmatter descriptions per
§3.5 (≤200 chars each, trigger-first, negative-scoped, no workflow summary).

After each skill's split: run V-S1/V-S5, then that skill's smoke test
(V-C6 for Skill 2, V-C7 for Skill 1, re-run the MS1 clean-fixture smoke for
Skill 3). After all three: record `claude plugin details
voicenter-bot-builder` token estimates in docs/planning/ms3-token-report.md
(before/after — the before numbers are in git history if not captured; if
missing, note it and capture after only).

Commit plan: one commit per skill split, one for the description rewrites.
No ride-along fixes.
```

---

## S3 — MS4 + MS5 (marketplace readiness + commands/polish)

```
You are working in the VoicenterTeam/claude-marketplace repo, on
plugins/voicenter-bot-builder. Read
plugins/voicenter-bot-builder/docs/README.md and
docs/planning/00-overview.md, then execute
docs/planning/milestone-4-marketplace-readiness.md followed by
docs/planning/milestone-5-commands-and-polish.md. Consult
docs/reference/marketplace-requirements.md for every MS4 requirement — it
carries the policy citations.

MS4 note: step 4.2 (LICENSE) requires a human decision. If the license
choice and legal sign-off are not already recorded in this repo (look for
docs/planning/license-decision.md), create the plugin-side scaffolding
(placeholder LICENSE noting the pending decision, README license section
stub), list what legal must confirm — including distribution rights on the
bundled doctrine/procedure reference files — in
docs/planning/license-decision.md, and continue. Do not invent a license.

MS5 note: the haiku gate (§5.2) requires the clean-fixture assembly to be
byte-comparable under model: haiku. Run it. If it fails, set model: sonnet,
record the observed drift in the CHANGELOG draft, and move on.

Commit plan: one commit for MS4, one for MS5. Run V-S8
(claude plugin validate --strict) at the end of each.
```

---

## S4 — MS6 (validation + release + submission prep)

```
You are working in the VoicenterTeam/claude-marketplace repo, on
plugins/voicenter-bot-builder. All prior milestones (1–5) are committed.
Read plugins/voicenter-bot-builder/docs/README.md,
docs/planning/00-overview.md, then execute
docs/planning/milestone-6-validation-and-release.md with
docs/reference/validation-checklist.md as the test specification.

You are the validator, not the implementer: verify against what is written
in the repo, not against any assumption about what prior sessions intended.
If a V-suite item fails, diagnose and report the failure with its milestone
of origin — fix trivial mechanical issues (paths, typos, lint) directly;
for anything touching skill logic or the verification procedure, stop and
present the failure to the user before changing it.

Sequence: V-S full pass → build both eval families (§6.1) and wire into CI
→ V-C full pass → prepare the V-A run (V-A tests execute on claude.ai, not
here: emit docs/planning/va-run-instructions.md with the exact steps,
fixtures, and pass criteria for the human to execute) → on green V-S/V-C
and confirmed V-A results from the user: release steps §6.3 (CHANGELOG,
version bump to 1.18.0, tag) and submission prep §6.4 (final validate on
HEAD, submission checklist). Do not perform the directory submission
itself — that is a human action via the in-app form.

Open the post-release watch note (§6.5) as
docs/planning/post-release-watch.md.
```

Human actions in S4 that Claude Code cannot perform: executing the V-A suite
on a claude.ai account, confirming the LICENSE sign-off landed (S3
dependency), and submitting via the in-app form.

---

## Resume prompt (any session, after interruption)

```
Resume v1.18.0 work on plugins/voicenter-bot-builder. Read
docs/README.md and docs/planning/00-overview.md, then determine current
state from the repo itself: check git log for milestone commits and each
milestone's done-criteria checklist against the actual files. Continue from
the first unmet criterion of the earliest incomplete milestone. Do not trust
conversation memory or summaries over repo state.
```
