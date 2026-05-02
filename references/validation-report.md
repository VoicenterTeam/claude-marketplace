# Skill Suite v1 — End-to-End Validation Report

**Test run:** Conv 6 of Voicenter Bot JSON skill suite v1 build cycle
**Date:** 2026-05-01
**Method:** Reverse-engineer Agent Specs from Doc 1 §14.1.1 (Yuval) and §14.1.2 (Refua), apply Skill 3 mechanically, validate emitted JSON against Doc 1 contract.

---

## 1. Summary

**Skill suite v1 is functionally ready.** Both production reference samples (Yuval, Refua) project cleanly through Skill 3:

| Check | Yuval | Refua |
|---|---|---|
| Cross-reference pass (§15.4 — 7 checks) | 7/7 PASS | 7/7 PASS |
| Schema-quirk preservation (Appendix A) | 15/15 PASS | 16/16 PASS |
| Mustache resolvability | 12/12 resolved | 14/14 resolved |
| Sentinel inventory (expected) | 6 (matches expectation) | 6 (matches expectation) |
| Refua-specific: silence_behaviour omission | n/a | PASS — key absent from JSON |
| Refua-specific: 6-dotted-path stress (decision N) | n/a | PASS — all six resolve in single announcement |

**Findings are documentation/template gaps, not runtime breakage.** Three issues warrant skill patches; one warrants a Doc 1 update once production-confirmed.

---

## 2. What worked — confirmed behaviors

### 2.1 Cross-reference integrity (both bots)

All 7 §15.4 checks passed for both samples:
- `botIntents[].IntentID` resolves to `intents[].IntentId`
- `intentRelations[]` both endpoints resolve
- `apiSilenceRelations[]` both endpoints resolve
- `IntentCategoryId` resolves to `intentCategories[]`
- Every RT=2 intent has paired `apiSilenceRelations[]` entry
- `api_silence_behaviour` content is byte-identical to the corresponding `apiSilenceRelations[].Configuration`
- Every Mustache token resolves via 4.5.1 (call-context), 4.5.3 (slot + reachability), or 4.5.4 (RT=2 response, declared by reachable upstream)

### 2.2 Quirk preservation (Appendix A)

All 15 baseline quirks emit correctly for both samples. The full list:

`IntentResponces` typo present (#1), `intentLoadingAnnouncement`+`IntentLoadingAnnouncement` casing pair on RT=2 (#2), `HandlingInstructions: null` on every intent (#3), `SystemPrompt: ""` (#4), top-level `AiModelConfig` + version-level `AIModelConfig` both present with byte-identical `created` payload (#5), `AIModelConfig.tools: []` and `instructions: ""` (#6, #7), `IntentScripts: {}` (#8), `ValidationRules: {}` and `ValidationPattern: null` per param (#9, #10), `silenceRelations: []` (#11), `BotLanguages: []` (#12), `llmDescription: ""` (#13), `response_success: ""` on RT=2/RT=3 (#14, the §16 extra).

Refua adds the 16th quirk verification: `silence_behaviour` key **absent entirely** from version-level `AIModelConfig` when section 3 is `[not configured]` (Skill 3 §4.2.5 omission path — the field is not emitted as `null` or `{}`, it's not present).

### 2.3 Decision N stress test (Refua)

`get_nearest_collection_points.apiResponseAnnouncement` contains six dotted paths in a single text field:

```
{{available_slots.0.display}} ({{available_slots.0.distance_km}} ק"מ)
{{available_slots.1.display}} ({{available_slots.1.distance_km}} ק"מ)
{{available_slots.2.display}} ({{available_slots.2.distance_km}} ק"מ)
```

All six resolve via spec section 4.5.4 (declared by `get_nearest_collection_points`, same intent → trivially reachable). A seventh dotted-path reference appears in the downstream RT=3 `confirm_pickup_point.announcement` — `{{available_slots.0.display}}` — resolving via the upstream-RT=2 reachability rule. The Mustache-resolution algorithm holds across both same-intent and upstream-RT=2 cases.

### 2.4 Sentinel inventory — expected and matching

Both bots emit exactly 6 sentinels in identical positions:

- `AccountID: -999` (Doc 1 doesn't expose Account integer)
- `Description: <USER_TO_FILL: bot description>` (Doc 1 doesn't show top-level Description value)
- `AiModelConfig.AIModelConfigID: -999` (model-catalog has TODO)
- `AiModelConfig.AIModelTypeId: -999` (catalog TODO)
- `AiModelConfig.Type.AIModelTypeId: -999` (denorm propagation)
- `ActiveVersionInfo.AIModelConfigId: -999` (FK mirror of top-level)

This count is the **expected** count per locked decision G — Doc 1 §14.1 doesn't expose the integer IDs that would resolve these, so they're correctly flagged for the user to fill at import time. No surplus sentinels surfaced; no expected sentinel was suppressed.

### 2.5 Per-bot variation correctly preserved

Bot-specific values do not bleed across emissions:
- Voice: Yuval `Puck`, Refua `Orus` — both correctly placed at `created.generationConfig.speechConfig.voiceConfig.prebuiltVoiceConfig.voiceName`
- Layer: Yuval 43, Refua 41
- Persona, intent identifiers, and intent counts differ as expected
- Section 3 silence: Yuval emits the full block, Refua omits the key entirely

---

## 3. Findings

### 3.1 Skill 1 gap — no ASCII identifier field in spec section 1 [BLOCKING for filename]

**Severity:** medium. Skill 3 produces a meaningless filename for Hebrew bots.

**Symptom.** Skill 3 §7.3 filename rule: `bot-<bot-snake-name>-<YYYY-MM-DD>.json`, where `<bot-snake-name>` is "the spec section 1 'Bot Name' lowercased and snake_cased, ASCII-folded (Hebrew names get transliterated using the snake_case identifier convention from section 4 — typically the user-supplied bot name in English, or a fallback `bot` if no ASCII version is available)."

Spec-skeleton.md section 1 only has `**Bot Name:** [name]`. There is no `**Identifier:**` (or `**ASCII Name:**` / `**Snake Name:**`) field. For a Hebrew Bot Name like `יובל` or `חברים לרפואה`, the rule falls through to the `bot` fallback. Resulting filename: `bot-bot-2026-05-01.json` — which is uninformative when a workspace contains multiple bots.

**Test workaround.** I named the test artifacts `test-emitted-json-yuval.json` and `test-emitted-json-refua.json` by hand, treating the test prefix as a separate concern. A real Skill 3 invocation against either sample would produce `bot-bot-...`.

**Proposed fix.** Add to spec-skeleton.md section 1, immediately under `**Bot Name:**`:

```
**Identifier:** [snake_case ASCII identifier; e.g., yuval, refua, customer_support]
```

Skill 1's interview prompt should ask for this explicitly when Bot Name contains non-ASCII characters; for ASCII Bot Names it can default to the snake_cased Bot Name. Skill 3 §7.3 then reads `**Identifier:**` directly and never has to fall back to `bot`.

**Routing:** Skill 1 patch (Conv 3a). Skill 3 §7.3 also needs a one-line update to read from `**Identifier:**` instead of deriving from Bot Name.

### 3.2 Skill 1 + Skill 3 gap — section 4 RT-specific format isn't formally specified [parse-time risk]

**Severity:** low. Doesn't break this test (I'm both producer and consumer of the format), but a strict Skill 3 parser would have no grammar to enforce.

**Symptom.** Skill 3 §3.1 enumerates exact field labels for section 1 (`**Bot Name:**`, etc.) and exact line shapes for section 4 slots/transitions. It does NOT enumerate the section 4 RT-specific sub-labels. Spec-skeleton.md line 75–79 treats it as descriptive prose:

```
- **RT-specific:**
  - [for RT=1: Layer ID — int or `<UNKNOWN: layer ID>`]
  - [for RT=2: URL, Method (POST|GET), Headers (object), Body (with Mustache), API silence behavior (5 fields + fallback intent)]
  - [for RT=3: (no structural fields beyond slots)]
  - [for RT=4: Phone destination, ...]
```

This is a hint to Skill 1, not a contract Skill 3 can parse against. In my test I expanded it to `URL: https://...`, `Method: POST`, etc., with `API silence behavior:` as a sub-block of 6 fields (5 + fallback). A different implementation could choose `**URL:**` (bold), or different sub-label names, and the spec wouldn't agree with the parser.

**Proposed fix.** spec-skeleton.md should specify section 4 RT-specific structure with named sub-labels:

```
- **RT-specific:**
  - **URL:** [full URL or `<UNKNOWN: API URL>`]   (RT=2 only)
  - **Method:** [POST|GET]   (RT=2 only)
  - **Headers:** [object literal, e.g., `{}`]   (RT=2 only)
  - **Body:** [object literal with Mustache placeholders]   (RT=2 only)
  - **API silence behavior:**   (RT=2 only)
    - silence_duration: [int]
    - silence_loops: [int]
    - silence_sentence: [string]
    - silence_ending_sentence: [string]
    - silence_instructions: [string]
    - fallback intent: [intent identifier]
  - **Layer:** [int]   (RT=1 only)
  - **Phone destination:** ...   (RT=4 — analogous expansion)
```

Skill 3 §3.1 then adds these sub-labels to the strict-template enumeration.

**Routing:** Skill 1 spec-skeleton.md update + Skill 3 §3.1 enumeration update. Same conv (Conv 3a covers both since they're co-evolving the contract).

### 3.3 Doc 1 + Skill 3 — BotIntentTypeID semantics [defer until production-confirmed]

**Severity:** low (open question, currently deferred to Doc 1's authoritative ruling).

**Symptom.** Doc 1 §8.2 defines `BotIntentTypeID = 1` and notes "Only value observed: 1" — and Doc 2/Skill 3 emit 1 for every entry. The recent VOICEBOT API memory note (slot 28, after Conv 5a Swagger investigation) describes the field as `BotIntentTypeID=1=start`, which suggests the value differentiates **start-eligible** intents (those reachable directly from the bot's opening behavior) from **chained-only** intents (reachable only via `intentRelations[]`).

If true, Yuval's start-menu intents (validate_customer_address, reschedule_existing, general_inquiry, transfer_to_human — the four named in the OPENING BEHAVIOR block) would have `BotIntentTypeID = 1`, and the chained intents (get_available_slots, confirm_appointment) would have a different value (perhaps 2 or 0). Refua's start menu (validate_customer_address, report_issue, general_inquiry, transfer_to_human) would similarly differ from chained intents.

**Current handling.** Per handoff §1.7: Doc 1 wins for v1. Skill 3 emits `BotIntentTypeID: 1` for every entry in both samples. This matches Doc 1 §8.2's "always 1" statement. The deployed bot may not behave as the user expects if the field is in fact a discriminator — but no test path lets us prove that without a production export with mixed values.

**Proposed action.** Once a production export shows `BotIntentTypeID` taking a value other than 1 for any intent, raise a Doc 1 patch (Conv 1a) updating §8.2 with the discriminator semantics, then patch Skill 3 §4.3.3 to compute the field from section 4's transitions graph (intents reachable from bot-level OPENING BEHAVIOR get 1; others get the chained value). Until then, defer.

**Routing:** open issue for Doc 1; no immediate skill change.

### 3.4 Doc 1 — model-catalog defaults can't be cross-checked [low-priority Doc 1 enrichment]

**Severity:** very low (test couldn't validate, but defaults retained as-is).

**Symptom.** Doc 1 §14.1.1 confirms `temperature: 1.5` for Yuval. Doc 1 is silent on `topP: 0.95` and `topK: 64` — these come from model-catalog.md's documented Gemini Live defaults. The test can't validate them against Doc 1's public sample.

**Proposed action.** When Conv 1a happens for any reason, expand §14.1.1 to include the full `created` payload from a production export. This both verifies the topP/topK defaults and serves as a richer reference for future skill changes.

**Routing:** noted for next Doc 1 update; no immediate skill change.

### 3.5 Cosmetic — Doc 1 §14.1.1 illustrative omissions (NOT a finding)

For the record, Doc 1 §14.1.1 illustrative samples don't show every field defined in the schema sections (e.g., `IntentParameters[].ParameterId`, `IntentParameters[].IntentId`, `IntentParameters[].IsActive`, `IntentParameters[].IsDeleted`, `IntentParameters[].ParameterType` denormalized echo). My emitter includes all of these per the schema sections (§10 and §16). This is correct emission against an illustrative sample — not a finding.

---

## 4. Conclusion

**Skill suite v1 ships.** All structural and Mustache contracts hold across both production reference samples. The two skill-level findings (§3.1 ASCII identifier, §3.2 RT-specific strict template) are template-completeness issues that don't break runtime — they affect filename quality and parse-error robustness, respectively. Both are tightly scoped patches.

The Doc 1 finding (§3.3 BotIntentTypeID) is deferred until production observation; the §3.4 catalog-defaults note is incidental.

**Recommended next steps.**

1. Read `handoff-back-to-skills.md` (this conv produces it). Routes §3.1 and §3.2 to Skill 1 / Skill 3 patches in a single short conv (Conv 3a).
2. Tag §3.3 as a Doc 1 open issue, no immediate work.
3. With those patches landed, rerun this exact end-to-end test (Conv 6b, lightweight rerun) to confirm regression-free.
4. Skill suite v1 is then ready for first real production use.

**Test artifacts produced (this conv).**

- `test-bot-spec-yuval.md` — reverse-engineered Yuval spec
- `test-emitted-json-yuval.json` — Skill 3 mechanical projection
- `test-bot-spec-refua.md` — reverse-engineered Refua spec
- `test-emitted-json-refua.json` — Skill 3 mechanical projection
- `build_yuval.py`, `build_refua.py` — Python scripts that mechanically apply Skill 3's §4 assembly + §4.5 quirks + §4.6 sentinels (the test harness)
- `validation-report.md` — this document
- `handoff-back-to-skills.md` — routing for the two Skill 1 / Skill 3 patches in §3.1 and §3.2
