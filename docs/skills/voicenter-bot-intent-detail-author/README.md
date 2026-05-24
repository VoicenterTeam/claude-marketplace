# Skill: `voicenter-bot-intent-detail-author`

Fill the per-intent language content of an Agent Spec. Skill 2 in the three-skill pipeline.

> Source: [`plugins/voicenter-bot-builder/skills/voicenter-bot-intent-detail-author/SKILL.md`](../../../plugins/voicenter-bot-builder/skills/voicenter-bot-intent-detail-author/SKILL.md)
> Plugin: [voicenter-bot-builder](../../plugins/voicenter-bot-builder.md) · Pipeline phase: **2 / 3**

---

## What it does

Walks every intent in section 5 that is `[structural]` or `[detailed-revisit]` and fills its language-heavy fields:

- Slot descriptions (LLM-facing strings used at slot collection time)
- `validationPrompt` (Conversation Routines style, ALL-CAPS headers, IRON RULES)
- RT-specific Configuration text (`announcement` (was `apiResponseAnnouncement` pre-v1.5.0), `fail_output`, `function_output` (object `{ "default": "..." }`), `response_success` (object `{ "instructions": "..." }`), silence text, etc.)
- Post-execution `intentInstructions` (Conversation Routines style)

After authoring, each completed intent is flipped to `[detailed]`. Section 4.5.3 (slot variable inventory) and section 6.1 (Mustache usage) are regenerated. Section 7.3 gets a generation log entry; sections 7.4 and 7.5 are updated.

Skill 2 is **reactivable** — you can invoke it as many times as needed. Spec state (per-intent status markers) is the resume point. If a Skill 1 patch reset some intents to `[detailed-revisit]`, Skill 2 picks them up next run.

---

## When to invoke

- Skill 1 just produced a fresh spec with `[structural]` stubs.
- Skill 1 patch mode reset some intents to `[detailed-revisit]`.
- The user asked to *"detail the intents"*, *"fill in the per-intent fields"*, or *"run Skill 2"*.
- Skill 1 emitted a handoff hint pointing to Skill 2.

Trigger phrases the skill responds to: *"run Skill 2"*, *"detail the intents"*, *"fill in the per-intent fields"*, *"Skill 2 (Intent Detail Author)"*, or any continuation from Skill 1's handoff.

If the work queue is empty (every intent already `[detailed]`), Skill 2 halts and recommends Skill 3.

---

## Inputs and outputs

| | |
|---|---|
| **Input** | An Agent Spec markdown file (`agent-spec.md` in Claude Code, or the most recent spec emission in single-conversation mode) with at least one intent marked `[structural]` or `[detailed-revisit]` |
| **Output** | Same spec, modified — section 5 entries filled, status markers updated, section 4.5.3 and 6.1 regenerated, section 7 metadata updated |

Skill 2 does not produce JSON. It does not modify the structural skeleton (sections 1, 2, 3, 4, 4.5.1/.2/.4) — that's Skill 1's territory.

---

## Batching

Skill 2 walks the work queue in **batches with user confirmation between them**. This prevents context bloat in long sessions and keeps the user in the loop on progress.

The default batching algorithm (per locked decision A):

- Each **hard intent** (flagged in section 4) becomes a singleton batch.
- **Soft intents** are grouped by adaptive sizing — between 2 and 6 per batch, scaled to total queue size and target checkpoint count:

| Total queue | Target checkpoints |
|---|---|
| ≤ 5 | 2 |
| 6–10 | 3 |
| 11–15 | 3–4 (favor 4 if hard intents present) |
| 16–20 | 4 |
| > 20 | `ceil(total / 5)` |

The plan is presented before execution; the user can accept, reorder, regroup, or pick a starting intent. Overrides are recorded in section 7.3.

After each batch completes, Skill 2 reports the results and waits for explicit confirmation before continuing to the next batch.

---

## Per-intent four-step interview

For each intent in a batch, Skill 2 walks four steps in order. The interview shape varies by Response Type, especially in step 3.

### Step 1 — Slot detailing

Section 4 declares slot names, types, required flags, collection orders. Step 1 elaborates each slot:

| Field | Meaning | When |
|---|---|---|
| `Description` | LLM-facing string for slot collection | All slots |
| `OptionList` (Value + Label per option) | Static choice list | ENUM (PT=19) with known choices |
| `OptionList: []` + note | Choices come from upstream API response | ENUM dynamically populated |
| Validation guidance for v1 fallback | Format/range constraints to embed in `validationPrompt` | NUMBER/DATE/EMAIL slots stored as STRING per Skill 1 v1 fallback |

Iron rule: if section 4 declared a slot type that mismatches its purpose (e.g., STRING for a phone number), Skill 2 does **not** silently fix — it pauses and recommends Skill 1 patch mode to fix the type structurally.

### Step 2 — `validationPrompt` authoring

`validationPrompt` is the bot's primary lever for shaping how it collects slots. **Conversation Routines style is mandatory** per Doc 1 §14.3.2:

- ALL-CAPS section headers (`ADDRESS COLLECTION`, `IRON RULES`)
- Numbered steps for the collection sequence
- Explicit IF/ELSE for branching
- IRON RULE blocks for non-negotiables

Free prose is forbidden. The skill ships a `conversation-routines-style-guide.md` reference with templates and worked examples.

The authoring procedure:

1. Draft an initial prompt from the slot list, collection order, intent purpose, and bot-level constraints in section 2.1 persona.
2. Ask the user about edge cases (partial answer, off-topic, refusal, unexpected format).
3. Incorporate edges as IF branches and IRON RULE blocks.
4. Show the draft. User confirms or edits.
5. Verify before advancing — every slot appears, every v1-fallback slot has format guidance, at least one IRON RULE exists, language matches the bot's primary language, every Mustache reference resolves.

### Step 3 — RT-specific configuration

The Configuration shape and required language fields differ by Response Type.

#### RT=1 (Layer Transfer)

| Field | Meaning |
|---|---|
| `announcement` | What the bot says before transferring |
| `intentLoadingAnnouncement` | Latency-cover utterance between announcement and transfer |

Layer ID is structural (in section 4). If `<UNKNOWN: layer ID>`, leave as-is — Skill 3 will emit `-999`.

#### RT=2 (API Call)

| Field | Meaning |
|---|---|
| `announcement` | What the bot says when the API succeeds (v1.5.0 — was `apiResponseAnnouncement` pre-v1.5.0). Almost always uses Mustache references against section 4.5.4 dotted paths. |
| `fail_output` | Graceful default: "I couldn't reach the system right now. Let me transfer you to a human." |
| `function_output` | **Fail-output fallback map** — object shape `{ "default": "<fallback string>" }` (v1.5.0 — was a bare string of LLM guidance). User supplies a single fallback string; Skill 2 wraps it as the object. |
| `response_success` | **Response success instructions** — object shape `{ "instructions": "<text or empty>" }` (v1.5.0). Empty string inner value is the most common production shape. |
| `intentLoadingAnnouncement` | Latency-cover utterance while the API call is in flight. (v1.5.0: capital-I `IntentLoadingAnnouncement` REMOVED — only lowercase form is emitted.) |
| `silence_sentence` / `silence_ending_sentence` / `silence_instructions` | Language for the API silence-handling block. |

Iron rules: every RT=2 intent must populate all six api_silence fields and have non-empty `announcement` / `fail_output` / `function_output` / `response_success`. For `function_output`, the object `{ "default": "<fallback>" }` qualifies as non-empty. For `response_success`, the object `{ "instructions": "" }` (empty inner string) qualifies. Per §14.3.6, missing silence behavior produces dead air at runtime when the API takes 8+ seconds.

#### RT=3 (Continue)

| Field | Meaning |
|---|---|
| `announcement` | What the bot says after slot collection completes; typically uses Mustache references against own slots and/or upstream API response paths |
| `response_success` | **Response success instructions** — object shape `{ "instructions": "<text or empty>" }` (v1.5.0). Empty string inner value is the most common production shape (`{ "instructions": "" }`). |

#### RT=4 (Dial-Out)

| Field | Meaning |
|---|---|
| `announcement` | Spoken before initiating the dial |
| `intentLoadingAnnouncement` | Spoken while dialing |
| `intentInstructions` | Optional post-execution string |
| `response_success.instructions` | Runtime guidance for the success path |

Other RT=4 fields (Phone1/2/3 / parameter_phone / NEXT_VO_ID / MAX_DIAL_DURATION / Record / selectdial_option) are structural — declared in section 4 by Skill 1.

### Step 4 — Post-execution `intentInstructions`

The second Conversation Routines block per intent. Defines what the bot does **after** this intent has fired and slots have been collected.

Critical distinction:

- `validationPrompt` — pre-execution, slot collection
- `intentInstructions` (per-intent) — post-execution, what to do next

Iron rules during drafting:

| Rule | Catch pattern | Handling |
|---|---|---|
| Must be Conversation Routines style | Free prose without ALL-CAPS / IRON RULES | Reformat |
| Must NOT contain pre-execution slot collection logic | "after collecting X, ensure it's…" | Silently relocate to `validationPrompt`; inform user |
| Must NOT contain persistent policy applying call-wide | "we never store payment details…" | Raise to user — destination is `prompts.persona` (Skill 1 patch territory) |
| Must NOT contain bot-level disambiguation | "first figure out if the user wants X or Y…" | Raise to user — destination is bot-level `prompts.intentInstructions` (Skill 1 patch territory) |

If the user picks the Skill 1 patch path, Skill 2 records the choice in section 7.3, halts the current intent, and waits for the user to run Skill 1 patch mode and re-invoke Skill 2.

---

## Mustache resolvability

Skill 2 enforces Doc 1 §14.3.5 — every `{{...}}` reference must resolve against an allowlist.

| Reference shape | Allowlist | Resolves if… |
|---|---|---|
| `{{slot_name}}` | Section 4.5.3 | Slot is collected by THIS intent OR by an upstream intent in the flow graph |
| `{{call_context_var}}` | Section 4.5.1 | Variable is listed |
| `{{ENV.VAR_NAME}}` | Section 4.5.2 | Variable is listed |
| `{{path.to.field}}` | Section 4.5.4 (per-intent) | Path is declared for THIS intent's RT=2 response, AND the reference appears in an RT=2 field of THIS intent — OR the path is declared by an upstream RT=2 intent reachable in the flow graph |

Directional check (v1, blocking):

- **Same-intent slots** — always resolve.
- **Upstream slots** — resolve.
- **Downstream slots** — block. The slot won't exist yet at runtime when this field fires. The user must fix the reference or pause to patch the flow graph via Skill 1.
- **Cousin slots** (no transition path either way) — warn and let the user choose. Decision logged to 7.3.

This is conservative-without-being-paranoid: catches obvious downstream errors, lets ambiguity through with explicit confirmation. Full reachability analysis ("every path from start passes through Y before X") is v2.

---

## Per-intent gate

After all four steps complete for an intent, Skill 2 runs the per-intent gate **before** flipping the status to `[detailed]`:

1. All four steps have content (no empty fields).
2. Every Mustache reference resolves per the rules above.
3. Conversation Routines style is enforced on `validationPrompt` and `intentInstructions`.
4. RT-specific iron rules pass (silence completeness for RT=2, field shapes for RT=2 and RT=3, etc.).
5. For RT=2: `announcement`, `fail_output`, `function_output` (object `{ "default": "..." }`), and `response_success` (object `{ "instructions": "..." }`) are all non-empty (structure, not content-fullness).
6. For RT=3: `response_success` object `{ "instructions": "..." }` is populated.

If the gate fails, Skill 2 returns to authoring. The status flip only happens on a clean gate.

---

## Output contract

**Per intent:**

- Section 5 entry filled with slot descriptions, validationPrompt, RT-specific Configuration, post-execution intentInstructions
- Status flipped to `[detailed]`

**Per batch:**

- All intents in the batch flipped to `[detailed]`
- Section 4.5.3 regenerated to reflect any slot description changes
- Section 6.1 (Mustache usage) regenerated
- Section 7.3 has a new log entry

**Per Skill 2 invocation:**

- Sections 7.4 and 7.5 updated
- Handoff hint to Skill 3 if all intents are now `[detailed]`

### Runtime-specific delivery

| Runtime | Output |
|---|---|
| **Single-conversation** | Updated spec returned as the assistant message |
| **Claude Code** | `agent-spec.md` overwritten with the updated spec |

---

## Anti-list — what Skill 2 does NOT do

- Modify section 1, 2, 3, 4, or 4.5.1/.2/.4 — those are Skill 1's territory
- Emit wire-format JSON — that's Skill 3
- Invent slot types, transition targets, or RT classifications
- Skip the per-intent gate
- Auto-fix structural inconsistencies — those route to Skill 1 patch mode
- Run the §15.4 cross-reference pass — that's Skill 3
- Make creative decisions about persona / opening behavior — those are Skill 1 patches

---

## v1.5.0 changes

- **`announcement` (RT=2)** — field renamed from `apiResponseAnnouncement`. The spec and JSON wire format now use the shorter name. Pre-v1.5.0 specs that used `apiResponseAnnouncement` should be patched via Skill 1 patch mode.
- **`function_output` shape change** — was a bare string of LLM guidance; now an object `{ "default": "<fallback string>" }`. Skill 2 captures the user's fallback string and wraps it. The user can extend the object with per-error-code keys via patch mode.
- **`response_success` shape change (RT=2 and RT=3)** — was a bare string; now an object `{ "instructions": "<text or empty>" }`. The empty inner string `{ "instructions": "" }` is the most common production shape.
- **RT=3 now also has `response_success`** — Skill 2 must author the object for RT=3 intents as well as RT=2.
- **`IntentLoadingAnnouncement` (capital I) REMOVED** — the prior "casing-bug pair" (`intentLoadingAnnouncement` + `IntentLoadingAnnouncement`) is obsolete for Gemini 3.1 Voice driven bots. Skill 2 authors only the lowercase form. Skill 3 emits only the lowercase form.
- **New required-reading row:** schema audit `§11.2` and `§11.3` cover the RT=2 and RT=3 Configuration field shapes. Skill 2 should load this reference at invocation.

---

## Common pitfalls

- **Free-prose `validationPrompt`.** Skill 2 blocks. Conversation Routines style is mandatory; rewrite as ALL-CAPS / numbered / IRON RULE.
- **Mustache reference to a downstream slot.** Skill 2 blocks. Either fix the reference or pause and run Skill 1 patch mode to fix the flow graph.
- **`fail_output` left empty on RT=2.** Skill 2 blocks. The graceful default ("I couldn't reach the system right now…") is acceptable; rewrite is up to the user.
- **Persistent policy snippet appearing in a per-intent `intentInstructions`.** Skill 2 raises and recommends moving to `prompts.persona` via Skill 1 patch.

---

## Compass doctrine integration

The bot-builder plugin includes a shared doctrine reference at `plugins/voicenter-bot-builder/references/voice-prompt-doctrine.md`, derived from the Gemini Live 3.1 voice agent engineering guideline. Skill 2 owns the primary enforcement of four per-intent rules from that catalog:

- **Rule 8 — TTS-safe formatting.** Blocking on markdown bullets/headers/URLs in voice-active intent fields. Advisory on raw long digit runs without a "spell digit-by-digit" instruction nearby. Fires during step 2 (validationPrompt) and step 3 (RT-specific config).
- **Rule 9 — Date math in prompt.** Advisory. Detects "not future", "year ≥ 1900", "today/tomorrow without {{TimeNow}}" patterns. Recommends pre-rendered Mustache variables via Skill 1 patch mode.
- **Rule 10 — Few-shot example cap.** Advisory when a single `validationPrompt` contains more than 2 transcript-style example pairs. Hebrew/non-English bots get a harsher message reflecting the ~3× per-example token cost.
- **Rule 11 — Hebrew-utterance isolation.** Blocking. Forbids inline RTL Hebrew/Arabic/CJK content mixed with LTR English on the same line. Required on its own line or wrapped in quotes.

See the reference doc for detection methods and fix recipes.

---

## Related skills

- [voicenter-bot-spec-designer](../voicenter-bot-spec-designer/README.md) — Skill 1; provides the structural skeleton Skill 2 fills.
- [voicenter-bot-json-assembler](../voicenter-bot-json-assembler/README.md) — Skill 3; runs after every intent is `[detailed]` to emit the wire-format JSON.
