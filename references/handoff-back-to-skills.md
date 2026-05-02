# Handoff Back to Skills — Conv 3a Patch Bundle

**Source:** Conv 6 end-to-end validation (`validation-report.md` §3.1, §3.2)
**Target:** single short follow-up conv that lands two co-dependent template-completeness patches before Skill suite v1 ships.
**Scope:** strictly template/contract — no runtime behavior change.

This handoff is **not blocking**: validation showed Skill 3's mechanical projection works on both production samples. These patches close documentation gaps surfaced by the test, so a real Skill 3 invocation produces useful filenames and a strict parser has a complete grammar to lean on.

---

## Patch 1 — Skill 1: add `**Identifier:**` to spec section 1

**Why.** Skill 3 §7.3 filename rule walks from `**Bot Name:**` and ASCII-folds it. For Hebrew Bot Names (e.g., `יובל`, `חברים לרפואה`) the rule falls through to the documented `bot` fallback, producing `bot-bot-2026-05-01.json` — uninformative when a workspace has multiple bots. The fix is for Skill 1 to capture the user-supplied ASCII identifier at interview time, not for Skill 3 to invent one.

**Files to touch.**

1. `skills/voicenter-bot-spec-designer/spec-skeleton.md`, section 1.

   Insert immediately after the `**Bot Name:**` line:

   ```
   **Identifier:** [snake_case ASCII identifier; e.g., yuval, refua, customer_support — used for the emitted JSON filename]
   ```

2. `skills/voicenter-bot-spec-designer/SKILL.md`, the interview step that captures section 1.

   Add an interview question right after the Bot Name capture: *"What ASCII identifier should this bot be filed under? (snake_case; used as the filename prefix when Skill 3 emits the JSON)"*. If Bot Name is already pure ASCII, default to its snake_cased form and ask only for confirmation.

3. `skills/voicenter-bot-json-assembler/SKILL.md`, §7.3.

   Replace:

   > Where `<bot-snake-name>` is the spec section 1 "Bot Name" lowercased and snake_cased, ASCII-folded (Hebrew names get transliterated using the snake_case identifier convention from section 4 — typically the user-supplied bot name in English, or a fallback `bot` if no ASCII version is available).

   With:

   > Where `<bot-snake-name>` is the spec section 1 `**Identifier:**` value (a snake_case ASCII identifier captured by Skill 1 at interview time). If the field is missing (legacy spec from before this patch), Skill 3 falls back to ASCII-folding `**Bot Name:**`, then to `bot`.

4. `skills/voicenter-bot-json-assembler/SKILL.md`, §3.1 strict-template enumeration.

   Add `**Identifier:**` to the section-1 field-labels list, immediately after `**Bot Name:**`.

**Test after patching.** Re-run Conv 6's mechanical projection on both Yuval and Refua specs. Specs should now contain `**Identifier:** yuval` and `**Identifier:** refua` respectively (added by Skill 1 patch-mode rerun, or hand-edited for the test). Filenames should resolve to `bot-yuval-<date>.json` and `bot-refua-<date>.json`.

---

## Patch 2 — Skill 1 + Skill 3: formalize section 4 RT-specific sub-labels

**Why.** spec-skeleton.md treats section 4 RT-specific as descriptive prose (`[for RT=2: URL, Method (POST|GET), Headers (object), Body (with Mustache), API silence behavior (5 fields + fallback intent)]`). Skill 3 §3.1's strict-template enumeration covers section 1 field labels and section 4 slot/transition shapes, but does NOT enumerate the RT-specific sub-labels. A grammar-driven parser has nothing to bind against here. The test got away with it because I was both producer and consumer of the format; production usage may not.

**Files to touch.**

1. `skills/voicenter-bot-spec-designer/spec-skeleton.md`, section 4 RT-specific block (currently lines 75–79).

   Replace the descriptive bullet list with:

   ```
   - **RT-specific:**
     - **URL:** [full URL or `<UNKNOWN: API URL>`]   (RT=2 only)
     - **Method:** [POST | GET]   (RT=2 only)
     - **Headers:** [object literal, e.g., `{}`]   (RT=2 only)
     - **Body:** [object literal with Mustache placeholders]   (RT=2 only)
     - **API silence behavior:**   (RT=2 only)
       - silence_duration: [int]
       - silence_loops: [int]
       - silence_sentence: [string]
       - silence_ending_sentence: [string]
       - silence_instructions: [string, often `""`]
       - fallback intent: [intent identifier from section 4]
     - **Layer:** [int]   (RT=1 only)
     - [for RT=4: define when RT=4 enters scope; not in v1]
     - [for RT=3: no structural fields beyond slots]
   ```

2. `skills/voicenter-bot-json-assembler/SKILL.md`, §3.1 strict-template enumeration.

   Add a new bullet item after the slot/transition lines:

   > **RT-specific sub-labels in section 4:** for RT=1 intents, `**Layer:**` followed by an integer. For RT=2 intents, `**URL:**`, `**Method:**`, `**Headers:**`, `**Body:**`, and `**API silence behavior:**` (the silence block has six sub-bullets exact: `silence_duration:`, `silence_loops:`, `silence_sentence:`, `silence_ending_sentence:`, `silence_instructions:`, `fallback intent:`). For RT=3 intents, the RT-specific block is empty (no sub-bullets). RT=4 is out of scope for v1.

3. `skills/voicenter-bot-json-assembler/SKILL.md`, §3.3 common-deviations table.

   Add one row:

   | RT-specific sub-label punctuation off | `Expected: '**URL:** <value>'. Found: 'URL: <value>'. Fix: wrap the sub-label in bold markdown.` |

**Test after patching.** Re-run Conv 6's mechanical projection on both samples. Ensure both specs are updated to bold the RT-specific sub-labels (`**URL:**` etc.) — this is a one-time edit. Skill 3's parser should accept the patched format and reject the unpatched format with the new §3.3 error.

---

## Patch 3 — out of scope for this conv

§3.3 (BotIntentTypeID semantics) requires production observation before any Doc 1 patch. Track as an open issue against Doc 1 v1.1; revisit when a production export surfaces a non-1 value.

§3.4 (model-catalog defaults cross-check) is a Doc 1 enrichment, not a skill issue. Bundle into the next Doc 1 patch when one happens for another reason.

---

## Conv 3a estimated scope

Two patches, four-to-five files touched, no new content authoring (just relabeling and grammar additions). Should fit in a single short conv. After Conv 3a lands:

1. Re-run Conv 6's mechanical projection (this should be ~15 minutes — both build_yuval.py and build_refua.py already exist; only the input specs need the new fields).
2. Tag Skill suite v1 as ready for first real production use.
3. Add the new fields to Doc 2's spec-template documentation (§3) so any future rebuild from Doc 2 stays consistent.
