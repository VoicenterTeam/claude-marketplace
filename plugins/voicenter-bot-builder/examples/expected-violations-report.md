# F2 Detection Baseline — v1.17.0

What plugin **v1.17.0** detects when Skill 3 runs against `sample-spec-seeded.md`.
This is the reference V-C3 / V-C4 / V-A2 compare against
(`../docs/reference/validation-checklist.md`).

Frozen 2026-08-08 against repo commit `cdc9922`. Do not regenerate.

---

## Outcome

```
Skill 3 cross-reference pass failed.

Checks failed: 3 of 24
Checks passed: 21

No JSON emitted. Section 7.3 has been updated with this failure log.
```

**No JSON artifact exists for F2** — §6.4 halts emission on any blocking failure. A
future run that emits JSON for F2 is a regression.

Token estimate: **1961 tok** — identical to F1 (none of the three seeded edits changes
the check-8 corpus materially). Checks 8/9/10 **fire** (model is
`models/gemini-3.1-flash-live-preview`); check 8 lands in the 1,500–4,999 advisory band,
which is a banner line, not a failure.

---

## Checks that fired

| # | Check | Severity | Blocks? | Seeded violation |
|---|---|---|---|---|
| 3 | `apiSilenceRelations[]` resolves (both endpoints) | blocking | yes | V1 |
| 7 | Mustache resolvability | blocking | yes | V2 |
| 22 | No authored edges into type-2 globals (FP-9) | advisory | no | V3 |

### Check 3 — blocking

```
Check 3: apiSilenceRelations[] resolves (both endpoints)
  Violation: apiSilenceRelations ApiSilenceIntentID -999 unresolved
  Field path: intentList.apiSilenceRelations[0].ApiSilenceIntentID
  Route to: Skill 1 patch mode
  Suggested fix: section 4 fetch_available_slots API silence behavior names
                 `transfer_to_human_agent`, which is not an intent in section 4.
                 Correct the fallback intent identifier.
```

Both `api_silence_behaviour.intent` and `ApiSilenceIntentID` carry the `-999` sentinel
(§4.4.1). Check 5 does **not** fire — the two are equal by construction, so the pairing
check is satisfied even though the target does not exist. See `seeded-violations.md` V1.

### Check 7 — blocking

```
Check 7: Mustache resolvability
  Violation: capture_caller_details.IntentResponces.Configuration.announcement
             references {{caller_full_name}}, which resolves against no 4.5.x inventory
  Field path: intentList.intents[0].IntentResponces.Configuration.announcement
  Route to: Skill 2 reactivation (the reference is wrong)
            — or Skill 1 patch mode if the variable should genuinely exist
  Suggested fix: the collected slot is `caller_name`; correct the reference.
                 CustomData keys are never invented — if {{caller_full_name}} is a real
                 per-call key, add it to spec 4.5.5 via Skill 1 patch mode.
```

### Check 22 — advisory

```
Check 22: No authored edges into type-2 globals (FP-9)
  Violation: intentRelations row targets transfer_to_human, a botIntents type-2 global
  Field path: intentList.intentRelations[5].NextIntentID
  Route to: Skill 1 patch mode (recommended, non-blocking)
  Suggested fix: drop the redundant relation — the global is reachable from anywhere
                 by construction (v1.12.0).
```

---

## Checks that passed (21)

1, 2, 4, 5, 6, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 23, 24.

Notable non-fires, each deliberate:

- **Check 5** — passes despite V1, for the by-construction reason above.
- **Check 24** — passes; the seeded edits do not touch any `**Asks next:**` value or
  announcement-emptiness pairing.
- **Check 19** — passes; V2 changes a Mustache token inside an existing sentence rather
  than duplicating a speak-obligation.
- **Check 23** — passes; the off-topic global and its persona rule are untouched.

---

## Equivalence criteria for later milestones

A later run (delegated verifier in MS2, or inline after the MS1 extraction) matches this
baseline when **all** hold:

1. Exactly checks **3, 7, 22** fire — no more, no fewer.
2. Severity is preserved: 3 and 7 blocking, 22 advisory.
3. Routing is preserved: 3 → Skill 1; 7 → Skill 2 (Skill 1 alternative offered);
   22 → Skill 1.
4. No JSON is emitted.
5. F1 still assembles clean (24/24) and byte-identical to `expected-output.json`.

Per V-A2, sensitivity differences on **advisory** checks (22) between runtimes are
documented rather than failed. A missed **blocking** violation (3 or 7) in either runtime
is a hard FAIL.
