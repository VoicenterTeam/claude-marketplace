# F2 Seeded Violations — `sample-spec-seeded.md`

`sample-spec-seeded.md` is `sample-spec-detailed.md` (F1) with **exactly three**
deliberate violations, per `../docs/reference/validation-checklist.md` §Fixtures (F2):

1. one blocking structural violation — RT=2 pairing break (CHK-05/06 class)
2. one Mustache resolvability break (CHK-07 class)
3. one advisory field-placement violation (FP class)

Nothing else differs. Regenerating F2 from F1 is three string substitutions; see the
commit that introduced this file.

---

## V1 — RT=2 API-silence failover names a non-existent intent (blocking)

**Class:** CHK-05/06 — RT=2 failover integrity
**Actually detected by:** check 3 (`apiSilenceRelations[]` resolves) — see the note below
**Spec location:** section 4, `### Intent 3: fetch_available_slots`, under
`**API silence behavior:**`

| | |
|---|---|
| F1 | `- fallback intent: transfer_to_human` |
| F2 | `- fallback intent: transfer_to_human_agent` |

`transfer_to_human_agent` does not exist in section 4. Skill 3 §4.4.1 emits the `-999`
sentinel for an unresolvable failover, so both `api_silence_behaviour.intent` and
`apiSilenceRelations[].ApiSilenceIntentID` become `-999`.

**Why check 3 fires rather than check 5.** Check 5 asserts that a pairing row exists and
that the inline `intent` equals `ApiSilenceIntentID`. Both hold — Skill 3 resolves the two
from the same spec field, so they are equal *by construction* even when both are `-999`.
Check 3 is what actually catches it, because `-999` is not a member of `intents[].IntentId`.

This is a real property of the v1.17.0 check set, not a defect in the fixture: **a typo'd
failover identifier is caught by endpoint resolution, never by the pairing check.** The
seeded violation is still in the intended class (RT=2 failover integrity) and still
blocking; only the check number differs from the checklist's parenthetical guess. Recorded
in `baseline-notes.md` N8.

**Runtime consequence if shipped:** the RT=2 intent has no failover when the caller goes
silent mid-webhook (Doc 1 §14.3.6).

---

## V2 — announcement references an undeclared Mustache variable (blocking)

**Class:** CHK-07 — Mustache resolvability
**Detected by:** check 7
**Spec location:** section 5, `### Intent: capture_caller_details`, `**Announcement:**`

| | |
|---|---|
| F1 | `Thanks, {{caller_name}}. Which clinician would you like to see, …` |
| F2 | `Thanks, {{caller_full_name}}. Which clinician would you like to see, …` |

`caller_full_name` appears in no 4.5.x inventory: it is not a call-context variable
(4.5.1), not an environment variable (4.5.2), not a slot (4.5.3 — the slot is
`caller_name`), not an API response path (4.5.4), and not a CustomData key (4.5.5).

**Runtime consequence if shipped:** the placeholder renders empty or literal, so the bot
opens the turn with a malformed sentence.

---

## V3 — authored edge into a type-2 global (advisory)

**Class:** FP-9 — minimal graph
**Detected by:** check 22
**Spec location:** section 4, `### Intent 3: fetch_available_slots`,
`**Transitions out:**`

| | |
|---|---|
| F1 | `1. confirm_slot_booking (success path)` |
| F2 | `1. confirm_slot_booking (success path)`<br>`2. transfer_to_human (fallback)` |

`transfer_to_human` has role `global` and is registered in `botIntents[]` with
`BotIntentTypeID = 2`, so it is reachable from anywhere by construction (v1.12.0). The
explicit edge is redundant and enlarges the tool-routing surface.

Side effect: `intentRelations[]` grows from 5 rows to 6.

**Runtime consequence if shipped:** none functional — this is a prompt-surface/maintenance
concern, which is why FP-9 is advisory rather than blocking.

---

## What F2 deliberately does NOT violate

So the detection baseline stays clean and attributable, F2 leaves untouched every other
blocking check that F1 passes: 1, 2, 4, 5, 6, 11, 12, 13, 15, 16, 17, 18, 19, 20, 21, 24.
Any additional failure appearing in a future run of F2 is a regression, not a seeded case.
