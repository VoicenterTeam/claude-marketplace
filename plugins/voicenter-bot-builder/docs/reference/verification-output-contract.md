# Verification Output Contract

Design spec for the report format that **both** verification paths — the
`spec-verifier` subagent and Skill 3's inline execution — must emit. MS1
embeds this contract as the final section of
`references/verification-procedure.md` (the shipped copy); this doc is the
design source. If they ever diverge, the shipped procedure file wins at
runtime and this doc must be corrected.

The contract exists so that: (a) Skill 3 §6.1 can consume delegated reports
verbatim, (b) V-C4 can assert inline/delegated equivalence mechanically,
(c) a malformed/foreign report is detectable and triggers inline fallback.

## 1. Report structure (exactly these blocks, in order)

```markdown
## Verification Report
Spec: <absolute path or "in-conversation">
Procedure version: <plugin version from plugin.json>
Executed: <delegated | inline>

### Verdicts
| CHK | Severity | Verdict | Detail |
|-----|----------|---------|--------|
| CHK-01 | blocking | pass | — |
| CHK-02 | blocking | FAIL | <one-line: what, where in the spec (section/intent id)> |
| …all 24 rows, in order, no omissions… |

### Blocking failures
<numbered list of every blocking FAIL: CHK id, spec location, one-line description.
 If none: "None.">

### Routing recommendations
<one line per FAIL: "CHK-NN → Skill 1|Skill 2 — <what the responsible skill
 must change>". Advisory failures included, marked "(advisory)".
 If none: "None.">

### Drift notes
<discrepancies between spec section 6 and regenerated views, per the
 v1.17.0 drift semantics. If none: "None.">
```

## 2. Rules

- **All 24 rows, always, in CHK order.** A skipped check is itself a
  malformed report.
- Verdict vocabulary: `pass` | `FAIL` | `error` (check could not be executed —
  detail says why). `error` on a blocking check is treated as blocking.
- Severity column restates the procedure file's assignment — the consumer
  never re-decides severity.
- Detail lines are one line each. The report is a verdict artifact, not an
  essay; explanation depth belongs in the routing recommendation.
- No content outside the four blocks. No preamble, no summary paragraph, no
  advice beyond routing lines.

## 3. Structured-error form (unrunnable verification)

If the spec path is missing/unreadable, or the procedure file cannot be
loaded, emit instead:

```markdown
## Verification Report — ERROR
Spec: <path as given>
Executed: <delegated | inline>
Error: <one line: what could not be done>
Action: <one line: what the caller should fix>
```

The subagent never hunts for alternative files; the inline path may ask the
user (it is in the main conversation) but must not guess.

## 4. Consumer-side validity check (Skill 3 §6.1)

A delegated report is valid iff: the `## Verification Report` header is
present, the Verdicts table contains exactly CHK-01…CHK-24 in order, and
every verdict is in the allowed vocabulary. Anything else → discard, log one
line to the user ("verifier report malformed — running checks inline"),
fall back to §6.2.
