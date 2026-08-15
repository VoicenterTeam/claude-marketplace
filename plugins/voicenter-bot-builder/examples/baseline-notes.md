# S0 Baseline Notes — observations while freezing the v1.17.0 fixtures

Per `../docs/planning/session-prompts.md` S0: issues found in v1.17.0 while generating
fixtures are **recorded here and not fixed** (locked decision S, `00-overview.md` §4).
Nothing in this file has been acted on.

---

## N1 — Skill 1's opening-behaviour template trips Skill 3 check 19 (cross-skill, real)

**Severity:** would block assembly on a canonically-authored bot.

Skill 1 §3.2.4 instructs the author to open the §2.4 block with a parenthetical that
restates the opening announcement verbatim:

```
OPENING BEHAVIOR
(Opening announcement already played: "Hello, this is X's assistant. Who am I speaking with?")
```

Skill 3 check 19 (FP-6, duplicate speak-obligation) extracts *"FP-4 quoted lines
(`: "<...>"`) inside … `prompts.intentInstructions`"* and compares them against the
sentences of `prompts.openingAnnouncement`. The parenthetical matches the `: "…"`
shape exactly, so the opening announcement is counted as a speak-obligation in two
sites and check 19 fails — **blocking**.

Skill 1's own canonical template therefore produces a spec that Skill 3 refuses to
assemble. Reproduced while authoring F1; confirmed by removing the quote.

F1 sidesteps it by phrasing the parenthetical without a quoted line:
`(The opening announcement has already greeted the caller and asked who is speaking. Do not repeat it.)`

### RESOLVED — both halves fixed

Two of the three candidate fixes were applied together:

- **Skill 1's template now paraphrases** instead of quoting
  (`stages/phase-interview.md` §3.2.4), with an inline warning explaining why quoting the
  already-played line trips CHK-19.
- **CHK-19 skips fully-parenthesised lines** when extracting FP-4 quotes
  (`references/verification-procedure.md`, mirrored in the docs page and implemented in
  `verify.py:fp4_quotes`).

The third candidate — allow-listing instruction verbs before the colon — was **rejected**:
it needs a bilingual verb list and trades this known false positive for unknown false
negatives, and double-speech is exactly what FP-6 exists to catch.

Locked by `test-chk19-regression.py`, 4 cases. The third asserts a genuine duplicate still
fails; if it ever goes quiet, the exclusion has gone too far and must be reverted.

**The fixtures did not move.** Fix A changes Skill 1's template, not F1's spec file (F1
already carried the paraphrase as its workaround), and fix B changes only the check, not
emission. Both goldens still reproduce byte-identically.

---

## N2 — `**Asks next:**` has no literal for auto-chaining non-terminals (vocabulary gap)

**Severity:** cosmetic, but forces a semantically wrong value.

Skill 3 §3 (line 128) defines `**Asks next:**` as *"free text, or the literal
`[none — terminal]`"*. Check 24 (v1.17.0, FP-3 turn-yield) keys on that field being
`[none]` to require an empty `announcement`.

v1.17.0's FP-3 case (c) introduced a third category — an intent that asks nothing and
**auto-chains to another non-terminal intent**. The grammar offers no literal for it.
The only parser-accepted way to express "asks nothing" is `[none — terminal]`, which is
factually wrong on such an intent.

F1 hits this on `collect_appointment_preferences` (RT=3, auto-chains into the RT=2
lookup). It is marked `[none — terminal]` because that is the only accepted literal.

Candidate fix (not applied): add `[none — auto-chains]` to the §3 grammar and make
check 24 match on the `[none` prefix.

---

## N3 — Mandatory-intent rules push the minimum bot size above S0's 8–10 target

**Severity:** none (fixture-design tension, not a defect).

S0 asks for 8–10 intents. Composing the v1.17.0 mandatory rules gives a higher floor:

| Requirement | Intents forced |
|---|---|
| FP-8 per-outcome RT=1 terminals | one per distinct outcome |
| FP-6(d) dedicated off-topic global (check 22) | 1 |
| v1.14.0 dedicated silence-forwarding intent (check 23) | 1 |
| v1.14.0 dedicated API-timeout forwarding intent (check 23) | 1, whenever any RT=2 exists |
| S0's own "one intent per RT type" | RT=2 and RT=4 each need a dedicated intent |
| FP-2 staggering | at least 2 flow intents (ask in N, capture in N+1) |

A naive composition lands at 12. F1 reaches exactly 10 by taking the sanctioned
escape hatch in both places — §3.1 step 9 option (c) and §3.5.1 option 3 — pointing the
caller-silence and API-timeout failovers at the existing `transfer_to_human` global
instead of creating dedicated intents. Both choices are logged in spec §7.3, as
check 23 requires.

**Coverage consequence:** F1 exercises neither `**IsSilenceIntent:** true` nor the
dedicated-forwarding-intent path. A future fixture should cover them.

---

## N4 — RT=2 live verification is unsatisfiable for a fictional business

**Severity:** none for the product; blocks fixture authoring without a workaround.

Skill 2 line 387 is a **HARD BLOCK, no waiver**: an RT=2 intent cannot reach
`[detailed]` until a live `curl` returns 2xx with every dotted path declared in §4.5.4
present in the body. S0 simultaneously requires a fictional business, an intent of
every RT type, and a fully-`[detailed]` spec. Those three cannot all hold.

Resolved by committing `stub-api-server.py` next to the fixture and verifying against
it for real — HTTP 200 with all five declared paths asserted present. The §7.6 entry is
genuine, not waived. Re-running the verification requires starting the stub first.

---

## N5 — Session skill registry resolved a stale plugin version

**Severity:** environmental, not a plugin defect.

The `Skill` tool resolved `voicenter-bot-spec-designer` to the cached **1.15.0** copy
even though `~/.claude/plugins/installed_plugins.json` records the install path as
**1.17.0** and 1.17.0 is present in the cache. The in-session registry appears to be
bound at session start.

Because S0's whole purpose is freezing a v1.17.0 baseline, these fixtures were authored
by following the **repo working-tree** SKILL.md files directly rather than through the
`Skill` tool. Cached 1.17.0 was diffed against the working tree first and is
content-identical (three files differ only by CRLF/LF).

Anyone re-running S0 through the `Skill` tool should confirm the resolved version first.

---

## N6 — V-C2's byte-comparability is unachievable as specified

**Severity:** blocks a release acceptance criterion (MS6 gate #2).

`validation-checklist.md` V-C2 requires the assembled JSON to be *"**byte-comparable** to
F1-expected (normalize date-in-filename only)"*.

Skill 3 §4.2.1 order 6 emits `CreatedDate` as *"ISO timestamp at assembly time"*, and that
value reappears throughout: `<root>.CreatedDate`, `ActiveVersionInfo.CreatedDate`,
`AiModelConfig.CreatedDate`, `AiModelConfig.ModifiedDate`, and `CreatedDate` +
`ModifiedDate` on **every** `IntentParameters[]` row. In F1 that is 26 timestamp fields.

Two runs a second apart therefore differ in 26 places. Normalizing only the filename date
cannot make them compare equal, so V-C2 as written can never pass.

`assemble.py` pins `ASSEMBLY_TS = "2026-08-08 09:15:00"` so the golden file is stable and
the fixture is usable today.

Candidate fixes (not applied): widen V-C2's normalization to cover all assembly
timestamps, or give Skill 3 a documented deterministic-timestamp mode for eval runs. This
should be settled in MS6 before the eval harness is built.

---

## N7 — `spec-skeleton.md` §6.5 contradicts Skill 3 §4.1, so every bot reports drift

**Severity:** cosmetic but permanent — guaranteed false-positive drift on every spec.

`spec-skeleton.md` §6.5 instructs: *"Per Doc 1 §15.3 Option A: sequential negative
integers. Per intent: -1, -2, -3, ..."*.

Skill 3 §4.1 allocates `IntentId` from the **`-10` series** (`-10, -11, -12, …`); `-1`,
`-2` and `-3` are reserved for `BotID`, `BotVersionId` and `IntentCategoryId`.

A spec authored per the skeleton therefore always disagrees with Skill 3's §5 regeneration
in 6.5. Drift is a soft warning, so nothing breaks — but the banner carries a drift line on
every bot ever built, which trains operators to ignore the DRIFT NOTES section.

F1 keeps the skeleton's numbering and the resulting drift is recorded in
`expected-banner.txt`, since fixing it would hide the finding.

Candidate fix (not applied): change the skeleton's §6.5 example to the `-10` series.

---

## N8 — check 5 cannot catch a typo'd RT=2 failover identifier

**Severity:** none (coverage observation) — the violation is still caught, by check 3.

Check 5 asserts an `apiSilenceRelations[]` row exists **and** that
`api_silence_behaviour.intent` equals that row's `ApiSilenceIntentID`. Skill 3 resolves
both from the same spec field (§4.4.1), so they are equal *by construction* — including
when both are the `-999` unresolvable sentinel. Check 5 therefore cannot detect a
nonexistent failover target; it only catches emission drift between the inline copy and the
registry copy, which is a Skill 3 internal-bug class.

The user-facing error — a failover naming an intent that does not exist — is caught by
**check 3** (endpoint resolution), which rejects `-999` as a non-member of
`intents[].IntentId`.

This matters for MS1: `validation-checklist.md` labels the F2 structural fixture as the
"CHK-05/06 class". The seeded case is in that class semantically, but the check that fires
is 3. The CHK-NN routing table written in MS1 should reflect the actual detector.

---

## N9 — `expected-banner.txt` names the wrong intent ID, and nothing checks it (found 2026-08-15)

The frozen banner's MANDATORY POST-IMPORT STEP reads:

```
#   - silence_behaviour.intent = -19 is a pre-import placeholder the import procedure does NOT
#     remap — after import, set the silence forward to "Handing the call to a human representative"
```

Both goldens emit `silence_behaviour.intent` = **-18**. In this fixture `-18` is
`transfer_to_human` and `-19` is `end_off_topic`, so the banner's prose names the right target
while its numeral points at the off-topic terminal. An operator following the step literally
would look up `-19` and land on the wrong intent — and this is the one banner line the operator
*must* act on, because the import procedure does not remap the field.

**Why it survived.** Nothing verifies the banner against the JSON. `assemble.py` has no banner
generator — `--help` exposes only `-o` for JSON — so `expected-banner.txt` was hand-captured and
is mechanically unreproducible. The 26-check pass operates on the wire structure and never reads
the banner; V-S9 explicitly excludes the file (its `24` is legitimately historical).

**Not hand-patched**, per the frozen-fixture rule in `README.md` — a hand-edited golden stops
proving what it exists to prove. Two routes, both needing a decision:

1. Rerun S0 to regenerate the banner from the current pipeline.
2. Add a CI assertion that parses `silence_behaviour.intent = <n>` out of the banner and diffs
   it against the JSON. This catches the class permanently and is a small addition to
   `check-static.py` — but it only covers the IDs that appear in the banner text, so it is a
   guard, not a generator.

If the banner was hand-typed, treat every other ID in it as unverified too.

---

## Verification environment

- Plugin baseline: v1.17.0 (`plugin.json`), repo commit `cdc9922`
- True SKILL.md sizes: 1,107 / 826 / 1,387 lines (spec-designer / intent-detail-author / json-assembler)
- Model config: Gemini 3.1 - LLM driven — `AIModelConfigID=142`, `AIModelTypeId=21`,
  provider string `models/gemini-3.1-flash-live-preview`, so checks 8/9/10 **fire**
  rather than skip on this fixture
- RT=2 endpoint: `stub-api-server.py` on `127.0.0.1:8787`, deterministic payload
