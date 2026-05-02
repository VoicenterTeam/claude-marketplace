# Handoff: Conv 5 → Conv 6

**From:** Conv 5 — Skill 3 SKILL.md: JSON Assembler & Publish
**To:** Conv 6 — End-to-end testing (primary: Yuval; secondary: Refua)
**Date:** May 2026
**Project state:** Conv 6 of 6 (per `project-map.md`) — final conversation in the v1 build cycle

---

## 1. Produced in this conversation

Conv 5 produced a single artifact under `skills/voicenter-bot-json-assembler/`:

- `SKILL.md` — Skill 3 instruction file (~55K, 8 main sections + 3 appendices)

Plus this handoff doc.

**No supporting files for Skill 3.** Conv 5 explicitly chose single-file structure over the handoff §6 recommendation to pull §15.4 checks into a supporting file. Rationale: the 7 cross-reference checks are short statements (the substance is the routing destination per check), the 14 quirks fit a single-page table, and the banner is one worked example. A standalone supporting file would have been 20-30% content and 70-80% indirection. If Conv 6 testing reveals that the SKILL.md is unwieldy at 55K (15-20K larger than Skills 1 and 2), pulling Appendix A (quirks) and/or Appendix B (routing table) into supporting files is the cleanest split. Conv 5a can do this without re-architecting.

No new architectural decisions. All 16 locked decisions (A–P) carry through unchanged from Conv 4. Conv 5 resolved the four deferrable open questions from handoff-conv-4-to-5 §6:

1. **Section 6 regeneration discrepancy handling.** Soft warning in the banner under "DRIFT NOTES", per-subsection one-line summaries; emission proceeds. Sections 4-5 are authoritative; section 6 is derivative. User can fix drift via Skill 1 patch (which regenerates section 6 cleanly) if it bothers them.

2. **JSON output filename.** `bot-<bot-snake-name>-<YYYY-MM-DD>.json`. Companion banner sidecar in Claude Code: `bot-<bot-snake-name>-<YYYY-MM-DD>.banner.md`. Hebrew bot names use the snake_case identifier convention from section 4 (typically a user-supplied English name); fallback to `bot` if no ASCII version is available.

3. **Banner format.** Plain text **above** the JSON code block (single-conv) or as a `.banner.md` sidecar (Claude Code). Never embedded in the JSON. This is a divergence from Doc 2 §6.8's illustrative example, which showed `#` lines that look like JSONC — but Voicenter import requires valid JSON, and Doc 2 §6.8 explicitly mentioned both options ("JSON-comment-style header (or sidecar metadata file)"). Banner has four sections always emitted in a fixed order: UNKNOWN VALUES, DRIFT NOTES, RECONCILIATION (7.4 vs emitted sentinels), DEFAULTS APPLIED.

4. **Section 7.4 vs emitted sentinels disagreement.** Emitted sentinels are authoritative. Banner's RECONCILIATION section lists discrepancies if any. Section 7.3 records the discrepancy.

Plus Conv 5 closed two additional open questions surfaced in handoff §6:

5. **§4.5.4 dotted-path validation depth.** Cross-reference check 7 in §6.2 codifies it explicitly: every Mustache reference matches against (a) same-intent slots, (b) 4.5.1/4.5.2 whitelist, (c) 4.5.3 collected by upstream intent in transition graph, (d) 4.5.4 declared for same RT=2 intent or upstream RT=2 intent. Cousin/downstream → violation. v1 uses simple reachability (path A → ... → B); full dataflow analysis is v2.

6. **What if zero `[detailed]` intents.** Pre-flight gate A in §2.3 refuses with explicit message: "Skill 3 will not assemble an incomplete spec. Section 5 has [N] intents still pending: [list with status]. Run Skill 2 (Intent Detail Author) to detail them, then re-invoke Skill 3."

Two design decisions worth flagging that weren't in the handoff but matter for Conv 6 testing:

7. **`BotIntentTypeID` emission.** All `botIntents[]` entries get `BotIntentTypeID = 1` per Doc 1 §8.2 ("v1 always emits `1`"). This is in slight tension with Doc 2 §6.3's phrasing "with `BotIntentTypeID = 1` (start-marker) for the first entry per the spec's section 4 ordering," which could be misread as implying others get something else. Doc 1 (the wire-format contract) wins — all entries emit 1. Memory slot 28 has a refined interpretation ("BotIntentTypeID=1=start") that may surface in production observation; v1 follows Doc 1's documented behavior.

8. **`created` payload defaults.** The Gemini Live `generationConfig` fields (`temperature: 1.5`, `topP: 0.95`, `topK: 64`) are emitted as v1 hardcoded defaults from Doc 1 §6.B.2 examples. The banner's "DEFAULTS APPLIED" section makes them visible. If Conv 6's Yuval test surfaces different production values, those become the new defaults (or get parameterized, but parameterization is v2).

---

## 2. Inherited context

Attach to Conv 6:

- `voicenter-bot-json-schema-audit-v1.md` — Doc 1 (wire-format ground truth — Conv 6 compares emitted JSON to Doc 1 §14.1.1 Yuval reference)
- `voicenter-bot-skills-architecture-v1.md` — Doc 2 (skill architecture)
- `project-map.md` — current
- `locked-decisions.md` — current (16 decisions A–P, no changes in Conv 5)
- `skills/voicenter-bot-spec-designer/` — Skill 1 SKILL.md + supporting files
- `skills/voicenter-bot-intent-detail-author/` — Skill 2 SKILL.md + supporting file
- `skills/voicenter-bot-json-assembler/SKILL.md` — Skill 3 (this conv's deliverable)
- `handoff-conv-5-to-6.md` (this document)

Conv 6 is a full pipeline test, so all three skills are needed at once. Doc 1 §14.1 (Yuval reference) and §14.2 (Refua reference) are the comparison ground truth.

---

## 3. Locked architecture facts critical to remember

For Conv 6 specifically:

1. **The test target is reverse-engineered, not authored.** Conv 6's first step is to produce an Agent Spec for Yuval by reverse-engineering from Doc 1 §14.1.1 — i.e., reading the production JSON and writing the spec that would produce it. This is not an interview; the spec is constructed deterministically from Doc 1's documentation. The spec is then run through Skill 3 directly (Skill 1 patch mode and Skill 2 reactivation are not exercised in this path — they're tested implicitly by the spec format being one Skill 1/2 would produce).

2. **The comparison is structural, not byte-perfect.** Skill 3 emits placeholder negative-integer IDs (`-1`, `-10`, etc.); Doc 1 §14.1.1 has whatever IDs the production export shipped with. The comparison must normalize IDs (substitute the placeholder map for production IDs) before diffing. Field ordering may also differ — normalize to a canonical order before comparison.

3. **Sentinels are expected, not failures.** Yuval's production export has real values for `AccountID`, `layer`, `AIModelConfigID`, etc. The reverse-engineered spec will have those values too (read directly from §14.1.1), so the emitted JSON should NOT have sentinels. If sentinels appear, that's a Skill 3 bug or a reverse-engineering omission. Refua's spec may have a `silence_behaviour` `[not configured]` (Refua omits it in production) — Skill 3 should omit the field entirely from the JSON, not emit it as `null` or `{}`.

4. **Banner is part of the deliverable.** Conv 6 should verify the banner's four sections render correctly — not just the JSON. The "DEFAULTS APPLIED" section in particular should match the v1 hardcoded defaults; if it lists fields that production explicitly populated differently, that's signal that the v1 defaults need adjustment.

5. **Failure routing is testable.** Conv 6 can synthesize a deliberately broken spec (e.g., delete an intent from section 4 but leave its references in transitions) and verify Skill 3 emits the right routing recommendation per Doc 2 §7.5. This is optional but high-value for confirming the §15.4 cross-reference checks fire correctly.

6. **The test is allowed to find skill bugs.** Conv 6 may discover that Skill 1, 2, or 3 has a defect — wrong field mapping, missed quirk, broken Mustache check, etc. The protocol is: report the bug in `validation-report.md`, route to a fix conversation (Conv 3a / 4a / 5a per project-map.md §6 outcome line), repeat the test after the fix. Conv 6 may iterate.

7. **Skill 3 is not idempotent across IDs.** Re-running Skill 3 on the same spec produces different placeholder integers each time (the cache is rebuilt). The internal consistency of the cache within one invocation is what matters; the actual placeholder values don't. Conv 6 should not test for byte-identical re-runs.

---

## 4. Inputs the next conv needs

- The full Conv 5 bundle (zip)
- Doc 1 §14.1.1 (Yuval) and §14.2 (Refua) as the comparison targets — these are inside Doc 1, no separate file needed
- The user (Shlomi) attaches the bundle and triggers Conv 6's test workflow

**Confirmations Conv 6 should establish before testing:**

- **ID normalization strategy for comparison.** When comparing Skill 3's output to Doc 1 §14.1.1, the placeholder IDs must be normalized. Recommend: substitute Skill 3's placeholders with their position-equivalent production IDs before diffing (e.g., the first intent's `IntentId` in Skill 3's output is `-10`; in production it's whatever Doc 1 has — substitute by position, not by value).

- **Field-order normalization.** Both inputs must be canonicalized to the same key order before diffing. Recommend: alphabetize keys, then diff. Or use `jq -S` if Conv 6 runs in Claude Code with shell access.

- **What to do if Yuval's production export uses different `created` payload defaults.** If Conv 6 finds that Yuval has `temperature: 0.7` (or whatever) instead of `1.5`, the question is whether to (a) update Skill 3's hardcoded default to match Yuval, (b) parameterize the default per spec, (c) leave as-is and flag as a known v1 limitation. Recommend: update to match Yuval if the value is consistent across both Yuval and Refua; parameterize in v2 if they differ.

- **Whether to test failure-routing flows.** Optional but high-value. Recommend: spend ~20% of Conv 6's effort on synthesized broken specs to validate the §15.4 routing logic.

---

## 5. Outputs Conv 6 must produce

Per project-map.md §6:

- `test-bot-spec-yuval.md` — the reverse-engineered Agent Spec for Yuval (input to Skill 3 in this test)
- `test-emitted-json-yuval.json` — Skill 3's output for the Yuval spec
- `validation-report.md` — gaps, anomalies, fixes needed; structured per skill (Skill 1 issues, Skill 2 issues, Skill 3 issues)
- `handoff-back-to-skills.md` — only if fixes are needed; routes back to Conv 3a / 4a / 5a

**Optional secondary test** (if time permits and primary passes):

- `test-bot-spec-refua.md` — reverse-engineered Refua spec
- `test-emitted-json-refua.json`
- Refua section in `validation-report.md` — focus is multi-field dotted-path Mustache in `get_nearest_collection_points` (decision N)

**Acceptance criteria for declaring v1 ready:**

- Yuval emitted JSON, after ID and field-order normalization, matches Doc 1 §14.1.1's documented structure
- All 14 §16 quirks present in emitted JSON
- All 7 §15.4 cross-reference checks pass
- Banner emits the four sections in the prescribed order
- Refua test (if run) passes the secondary criteria

If acceptance criteria fail: route fix to the responsible skill conversation.

---

## 6. Open questions still pending

**Blocking Conv 6:** none. All architectural decisions necessary for Conv 6 to start are locked.

**Deferrable (resolve during Conv 6 if relevant):**

- **Whether the `created` payload defaults need adjustment.** Conv 6's Yuval comparison will surface this. If production differs, Conv 5a updates Skill 3.

- **Whether `BotIntentTypeID` should always be 1 or just for the first entry.** Conv 6's Yuval comparison surfaces this. Doc 1 says all 1; Doc 2 hints at first-only. If production has a non-1 value for non-first entries, that's a Doc 1 update + Skill 3 update (Conv 1a + Conv 5a).

- **The model catalog's TODO IDs for Gemini Live.** v1 ships with `<TODO>` placeholders in `model-catalog.md`. Conv 6's Yuval test will require real values to compare cleanly. Recommend: confirm with Voicenter platform team during Conv 6 setup; update `model-catalog.md` (Conv 3a) before running the test, or accept that emitted JSON will have `-999` sentinels for those IDs (and the test compares modulo sentinels).

- **Hebrew bot name → snake_case transliteration.** Yuval's bot name is "יובל" — what does the snake_case form look like? Recommend: user supplies an English form during Skill 1 interview (e.g., `yuval`); fallback rule in Skill 3 (`bot` if no ASCII available) is rarely hit.

- **Whether single-conv runtime works for the Yuval test.** Yuval has ~6-8 intents per Doc 1 §14.1.1. Should fit single-conv per decision E. If it strains, Conv 6 switches to Claude Code mid-test.

---

## 7. References

- Project map: `project-map.md` (Conv 6 details in the conversation map section)
- Locked decisions: `locked-decisions.md` (16 decisions A–P)
- Memory slot 28: project state summary; recommend updating end-of-Conv-5 with: "Conv 5 done; Skill 3 SKILL.md (no supporting files) produced at 55K. Ready for Conv 6 (end-to-end test)."
- Doc 1 §14.1 — Yuval reference
- Doc 1 §14.2 — Refua reference
- Doc 1 §15.4 — cross-reference checks (Skill 3 §6 implements)
- Doc 1 §16 — quirks (Skill 3 §4.5 + Appendix A implements)
- Doc 2 §6 — Skill 3 architecture (all of Skill 3's SKILL.md implements)
- Doc 2 §7.5 — routing table (Skill 3 Appendix B implements)

---

## 8. Brief notes for Conv 6's testing approach

Three suggestions worth carrying forward from prior convs:

1. **Run Skill 3 first, not last.** The traditional pipeline order is Skill 1 → Skill 2 → Skill 3. For testing, the more efficient sequence is: reverse-engineer the spec by hand, run Skill 3 directly, compare to Doc 1 §14.1.1. This validates Skill 3 in isolation. If Skill 3 fails the comparison, the fix is unambiguously in Skill 3 (or in the spec's reverse-engineering, which is also testable). Running through Skill 1 → Skill 2 → Skill 3 introduces three potential failure points; isolating to Skill 3 first makes diagnosis cleaner.

2. **Reverse-engineering the spec is itself a validation of Doc 2 §3.** If Doc 1 §14.1.1 contains information that doesn't fit cleanly into the spec template — e.g., a per-intent field that has no spec section to live in — that's a gap in Doc 2 §3 (or equivalently in Skill 1's interview). Surface those gaps in `validation-report.md` even if they don't break the JSON comparison.

3. **The §15.4 cross-reference pass on a real spec is the highest-value test.** Yuval's production data has every cross-reference type (RT=1 transfer, RT=2 API calls with `apiSilenceRelations` pairings, multi-step transitions, Mustache references to slots and to API responses). If Skill 3's §15.4 pass produces zero false positives and zero false negatives on Yuval, Skill 3 is ready. If false positives appear, the check is too strict; if false negatives, the check is too lax. Both are fixable in Conv 5a.

The end of Conv 6 — assuming acceptance criteria pass — closes the v1 skill build cycle. The next phase (post-v1) is field validation: putting the skills in front of bot designers and watching what breaks. That's a different project shape and not part of this conversation map.
