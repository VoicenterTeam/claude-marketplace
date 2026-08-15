# Milestone 1 — Single-Source Verification Procedure

**Objective:** every consumer of the 25-check cross-reference pass (24 at MS1 time) — inline
path, subagent (MS2), future CI — executes one file:
`references/verification-procedure.md`. No check text survives in two places.

**Why:** kills the version-drift bug class already hit with Doc 1 §15.4
references duplicated across skills. The v1.17.0 FP-3 turn-yield update
touched three files; after this milestone the same class of change touches one.

**Files touched:**
- `references/verification-procedure.md` (NEW)
- `skills/voicenter-bot-json-assembler/SKILL.md` (§6 gutted to pointer)
- `references/voice-prompt-doctrine.md` (ownership headers → pointers)
- `references/field-placement-doctrine.md` (ownership headers → pointers)

## Steps

### 1.1 Create `references/verification-procedure.md`

Copy Skill 3 §6 checks 1–24 **verbatim** — this is a move, not a rewrite.
Structure:

```
# Verification Procedure (25-check cross-reference pass)
## Table of contents          ← required, file will exceed 100 lines (C6)
## How to execute this file   ← ordering rule, blocking vs advisory handling
## Checks
### CHK-01 …
### CHK-24 …
## Output contract            ← see 1.2
```

Each `CHK-NN` block carries, explicitly:
- **Verifies:** one-sentence statement of the invariant
- **Source:** anchor (Doc 1 §15.4 item / Compass rule N / FP-N)
- **Severity:** `blocking` | `advisory` (preserve v1.17.0 assignment exactly:
  checks 1–7, 11–13, 15, 16–21, 24 blocking)
- **On failure route to:** Skill 1 | Skill 2 (preserve Appendix B logic)
- **Procedure:** the verbatim check text from Skill 3 §6

Stable IDs `CHK-01`…`CHK-24` map 1:1 to the v1.17.0 numbering. Never renumber;
retire IDs if a check is removed, append new IDs at the end.

### 1.2 Append the output contract

Embed the contract from `../reference/verification-output-contract.md` into
the procedure file's final section (the reference doc is the design spec; the
procedure file is what ships). Both execution paths must emit exactly this
format — MS6's equivalence test (V-C4) depends on it.

### 1.3 Gut Skill 3 §6

Replace the check bodies in `skills/voicenter-bot-json-assembler/SKILL.md` §6
with:
- A pointer: read and execute
  `${CLAUDE_PLUGIN_ROOT}/references/verification-procedure.md` (C5 — do not
  use a bare relative path).
- Placeholder subsection stubs §6.0/§6.1/§6.2 marked `[MS2 fills this]` —
  MS2 writes the dispatch logic; MS1 must not.
- Blocking/advisory *handling* (what Skill 3 does with a failed check) stays
  in SKILL.md — it is decision logic, not procedure.

### 1.4 Convert doctrine ownership headers to pointers

Both doctrine files currently carry "Skill X owns checks N–M" prose in their
headers. Replace with pointers to CHK IDs, e.g. "enforced at assembly time by
CHK-16…CHK-24 — see `verification-procedure.md`". Do not touch the doctrine
rules themselves.

### 1.5 Sweep stale references

Grep the entire plugin for: `§6`, `checks 1–24`, `cross-reference pass`,
`check 5`, `check 11` etc. Retarget every hit to the CHK-NN vocabulary or the
procedure file. Skill 1 and Skill 2 SKILL.md both reference specific check
numbers in their doctrine-loading tables — update those rows.

## Done criteria

- [ ] `verification-procedure.md` exists with TOC, 24 CHK blocks, output contract
- [ ] Grep test: 3 distinctive phrases sampled from CHK bodies each appear in
      exactly one file plugin-wide (V-S2)
- [ ] Skill 3 §6 contains zero check-procedure text
- [ ] All cross-file pointers use `${CLAUDE_PLUGIN_ROOT}` (V-S3)
- [ ] Severity and routing per check are byte-identical in meaning to v1.17.0
- [ ] Plugin still assembles a known-good spec correctly end-to-end (smoke run:
      Skill 3 reads the procedure file inline and produces the same JSON as
      v1.17.0 for the same fixture)
