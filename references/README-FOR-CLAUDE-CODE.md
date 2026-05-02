# Voicenter Bot JSON — Skill Suite v1 → Conv 3a Handoff

This bundle is a handoff to Claude Code to land **Conv 3a**, a small patch bundle that closes two template-completeness gaps surfaced by the Conv 6 end-to-end test. Once Conv 3a lands, Skill suite v1 is ready for first real production use.

---

## TL;DR — what to do

1. Read `handoff-back-to-skills.md`. It is the load-bearing doc — two patches, four-to-five files touched, no new content authoring.
2. Apply Patch 1 (Skill 1 add `**Identifier:**` field + Skill 3 §7.3 + §3.1 reads from it).
3. Apply Patch 2 (Skill 1 spec-skeleton.md formalize section 4 RT-specific sub-labels + Skill 3 §3.1 enumerate them + §3.3 add deviation row).
4. Rerun the Conv 6 regression — see `test-artifacts/` and the section "How to rerun the regression" below.
5. If both regressions still pass with the patched specs, Skill suite v1 is shippable. Tag and stop.
6. Optionally — Doc 2 update referenced as Patch 3 in handoff-back-to-skills.md is out of scope for Conv 3a; track separately.

---

## Bundle contents

```
.
├── README-FOR-CLAUDE-CODE.md          ← you are here
├── handoff-back-to-skills.md          ← THE load-bearing doc; start here after this README
├── validation-report.md               ← Conv 6 evidence — what passed, what's open, why
│
├── docs/
│   ├── voicenter-bot-json-schema-audit-v1.md     ← Doc 1 (wire-format contract — frozen for v1)
│   └── voicenter-bot-skills-architecture-v1.md   ← Doc 2 (skill suite architecture)
│
├── locked-decisions.md                ← 16 design decisions A-P
├── project-map.md                     ← original project plan
├── handoff-conv-5-to-6.md             ← Conv 5→6 handoff (Conv 6 input context)
│
├── skills/
│   ├── voicenter-bot-spec-designer/   ← Skill 1 — patch this (Patches 1 & 2)
│   │   ├── SKILL.md
│   │   ├── spec-skeleton.md           ← bulk of Patch 1 + Patch 2 lives here
│   │   ├── model-catalog.md
│   │   ├── trigger-detection-rules.md
│   │   └── templates/
│   │
│   ├── voicenter-bot-intent-detail-author/   ← Skill 2 — UNCHANGED, no patches
│   │   ├── SKILL.md
│   │   └── conversation-routines-style-guide.md
│   │
│   └── voicenter-bot-json-assembler/  ← Skill 3 — patch this (Patches 1 & 2)
│       └── SKILL.md                   ← §3.1, §3.3, §7.3 patches all live here
│
└── test-artifacts/
    ├── test-bot-spec-yuval.md          ← Yuval reverse-engineered spec (Conv 6 input)
    ├── test-emitted-json-yuval.json    ← Yuval emitted JSON (Conv 6 expected output)
    ├── test-bot-spec-refua.md          ← Refua reverse-engineered spec
    ├── test-emitted-json-refua.json    ← Refua emitted JSON
    ├── build_yuval.py                  ← mechanical Skill 3 projection (Yuval)
    └── build_refua.py                  ← mechanical Skill 3 projection (Refua)
```

---

## Context — what's already been done

Six conversations already happened. Skill suite v1 is structurally complete and tested.

| Conv | Output | Status |
|---|---|---|
| Conv 1 | Doc 1 (`voicenter-bot-json-schema-audit-v1.md`) — wire-format contract | DONE |
| Conv 2 | Doc 2 (`voicenter-bot-skills-architecture-v1.md`) — skill architecture | DONE |
| Conv 3 | Skill 1 — Agent Spec Designer | DONE |
| Conv 4 | Skill 2 — Intent Detail Author | DONE |
| Conv 5 | Skill 3 — JSON Assembler (single-file SKILL.md, ~55K) | DONE |
| Conv 6 | End-to-end test — Yuval + Refua reverse-engineered, projected, validated | DONE — PASSED |

Conv 6 results, in one paragraph: both production samples (Yuval Hebrew installation bot, Refua Hebrew pharmacy pickup bot) passed all seven §15.4 cross-reference checks; preserved all 15 wire-format quirks (Refua additionally tested the 16th quirk — `silence_behaviour` key omission); resolved every Mustache reference (12 in Yuval, 14 in Refua including six dotted paths in a single announcement); emitted exactly six expected sentinels each. No surprises, no regressions, no surplus sentinels.

Two findings surfaced — both template-completeness, neither blocks runtime. They are what Conv 3a fixes.

---

## The two patches in one sentence each

**Patch 1.** Hebrew bot names produce useless filenames (`bot-bot-2026-05-01.json`) because Skill 1's spec template has no ASCII identifier field for Skill 3 to read. Add `**Identifier:**` to spec section 1; teach Skill 3 §7.3 to read it.

**Patch 2.** Section 4's RT-specific block (URL/Method/Headers/Body/silence) is descriptive prose in spec-skeleton.md, but Skill 3's strict-template parser §3.1 has no grammar for it. Bold the sub-labels, enumerate them in Skill 3 §3.1, add a deviation example to §3.3.

Full instructions in `handoff-back-to-skills.md`.

---

## How to rerun the regression after patching

The test harness in `test-artifacts/` exists for exactly this. It's a Python projection of Skill 3's §4 assembly + §4.5 quirks + §4.6 sentinels — meaning it does mechanically what a real Skill 3 invocation does, so we can compare against the known-good Doc 1 §14.1.1 / §14.1.2 samples.

**Steps after patching:**

1. Update `test-bot-spec-yuval.md` to add `**Identifier:** yuval` under `**Bot Name:**` (spec section 1) and bold the section 4 RT-specific sub-labels (`**URL:**`, `**Method:**`, `**Headers:**`, `**Body:**`, `**API silence behavior:**`).
2. Same for `test-bot-spec-refua.md` (`**Identifier:** refua`).
3. Run `python3 test-artifacts/build_yuval.py`. Expected output: `Wrote 19211 chars, 570 lines` (or similar; minor drift from comment changes is fine).
4. Run `python3 test-artifacts/build_refua.py`. Expected: `Wrote 18323 chars, 532 lines`. Critical assertion: `silence_behaviour key in version-level AIModelConfig: False`.
5. Re-run the validation pass (the cross-ref + quirk + Mustache + sentinel checks). The full inline check script is reconstructible from `validation-report.md` §2.1–2.4 — or simpler: write a one-shot Python that loads each emitted JSON and asserts the same contracts.

**Pass criteria:** identical to Conv 6 — 7/7 cross-ref both bots, 15/16 quirks, all Mustache resolved, exactly 6 sentinels each. The only structural diff post-patch should be that the filename rule produces `bot-yuval-<date>.json` instead of `bot-bot-<date>.json` — which is the whole point of Patch 1.

---

## What NOT to touch

- Doc 1 (`voicenter-bot-json-schema-audit-v1.md`). Frozen for v1. The BotIntentTypeID semantics question (validation report §3.3) is the only outstanding Doc 1 item and it's deferred until production observation.
- Skill 2 (`voicenter-bot-intent-detail-author/`). No patches in scope. Both Conv 3a patches are Skill 1 + Skill 3 only.
- The 16 locked decisions A-P. Don't relitigate.
- Conv 6 test artifacts other than the two specs. The two builders (`build_yuval.py`, `build_refua.py`) are mechanically derived from Skill 3 §4 and don't need to change for Conv 3a — they parse from the spec values directly, not from the formatting.

---

## Open issues to track separately (not Conv 3a scope)

1. **BotIntentTypeID semantics.** Validation report §3.3. Doc 1 §8.2 says always 1; recent VOICEBOT API memory note suggests 1 = start (discriminator). Doc 1 wins for v1. Revisit when a production export shows a non-1 value.
2. **Doc 1 §14.1.1 created payload depth.** Validation report §3.4. Doc 1 confirms `temperature: 1.5` but is silent on `topP: 0.95` and `topK: 64`. Bundle into next Doc 1 patch when one happens for another reason.
3. **Doc 2 spec-template documentation.** Conv 3a Patch 3 mentions updating Doc 2 §3 to reflect the new section-1 `**Identifier:**` field and bolded RT-specific sub-labels. Out of scope for Conv 3a (Conv 3a is skill-folder work). Track for a Doc 2 patch later.

---

## Origin of this bundle

Generated by Conv 6 (end-to-end validation conversation) on 2026-05-01. Conv 6 was the sixth and final conversation in the v1 build cycle (slicing α — one conv per artifact). All design decisions, slicing choices, and trade-offs through Conv 5 are captured in `locked-decisions.md` and the per-conv handoff docs.

If anything in `handoff-back-to-skills.md` or `validation-report.md` is unclear, default to the more detailed source — Doc 1 for wire-format questions, Doc 2 for skill-architecture questions, locked-decisions.md for "why was this designed this way."
