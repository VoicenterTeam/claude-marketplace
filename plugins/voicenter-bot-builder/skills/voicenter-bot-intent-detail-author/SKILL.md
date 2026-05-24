---
name: voicenter-bot-intent-detail-author
description: Authors the per-intent language content of a Voicenter Agent Spec — slot descriptions, validationPrompt, post-execution intentInstructions, and RT-specific Configuration text. Use this skill when an Agent Spec exists with section 5 entries marked `[structural]` or `[detailed-revisit]`, and the user wants to fill them in. Trigger phrases include "run Skill 2", "detail the intents", "fill in the per-intent fields", "Skill 2 (Intent Detail Author)", or any direct continuation from Skill 1's handoff hint. Walks intents in user-confirmed batches with a checkpoint after each batch. Reactivable — invoke as many times as needed; spec state is the resume point. Does NOT modify the structural skeleton (sections 1, 2, 3, 4, 4.5.1/.2/.4) — that's Skill 1 (Agent Spec Designer). Does NOT emit wire-format JSON — that's Skill 3 (JSON Assembler).
---

# Skill 2 — Intent Detail Author

This skill fills the language-heavy fields of an Agent Spec's section 5 — the per-intent content that determines how the bot collects slots, what it says during execution, and what it does post-execution. It is one of three skills in the Voicenter Bot generation pipeline:

- **Skill 1 (Agent Spec Designer):** structural design via interview → fills sections 1, 2, 3, 4, 4.5, section 6 (initial), section 7 (init); creates section 5 stubs marked `[structural]`.
- **Skill 2 (this skill):** language-heavy per-intent content → fills section 5 entries, marks them `[detailed]`; updates 4.5.3, 6.1, 7.3, 7.4, 7.5.
- **Skill 3 (JSON Assembler & Publish):** mechanical projection of the spec into Bot JSON wire format.

Source of truth is the spec markdown. No skill invents values.

---

## 1. Required reading at invocation

Before touching the spec, load context from these references.

| Read | Why |
|---|---|
| Doc 1 §6.B.2 — `IntentConfig.prompts.validationPrompt` | Skill 2 authors this field |
| Doc 1 §6.B.3 — `IntentResponces.Configuration` | Per-RT Configuration shape Skill 2 fills |
| Doc 1 §11 — RT=1/2/3/4 cross-RT field summary | Step 3 RT-specific authoring |
| Doc 1 §11.2 — RT=2 api_silence_behaviour pairing | Step 3 RT=2 authoring |
| Doc 1 §13 — Mustache + variable categories | Mustache resolvability check |
| Doc 1 §14.3.2 — Conversation Routines style | Iron rule for validationPrompt + intentInstructions |
| Doc 1 §14.3.3 — Slot validation guidance | Step 1 + Step 2 |
| Doc 1 §14.3.5 — Mustache referencing slots before collection | Mustache directional ordering |
| Doc 1 §14.3.6 — RT=2 api_silence_behaviour completeness | Step 3 RT=2 |
| Doc 1 §14.3.11 — Bot-level disambiguation in per-intent fields | Step 4 misplacement check |
| Doc 1 §14.3.12 — Slot validation in intentInstructions | Step 4 misplacement check |
| Doc 1 §14.3.13 — Persistent policy in single intent | Step 4 misplacement check |
| Doc 1 §14.3.14 — Field-purpose cheat sheet | Disambiguating misplacement |
| Doc 2 §5 — Skill 2 architecture | What Skill 2 does |
| Doc 2 §3.6 — Status mechanic for section 5 intents | Reactivation logic |
| `../../references/voice-prompt-doctrine.md` | Compass doctrine — 13 rules; Skill 2 owns the primary enforcement of rules 8 (TTS-safe formatting), 9 (date math in prompt), 10 (few-shot count cap), 11 (Hebrew-utterance isolation) |
| `../../../../references/docs/voicenter-bot-json-schema-audit-v1.md` §11.2, §11.3 | RT=2 / RT=3 Configuration field shapes — v1.5.0 production-aligned (announcement / function_output object / response_success object) |

Also load this file from this skill's package:

- `conversation-routines-style-guide.md` — concrete templates and worked examples for `validationPrompt` and `intentInstructions` across RTs

---

## 2. Setup

### 2.1 Detect runtime

| Signal | Runtime |
|---|---|
| Conversation in claude.ai or mobile app, no workspace file system, no `agent-spec.md` accessible | **Single-conversation** |
| Workspace file system available (Claude Code), `agent-spec.md` readable as a file | **Claude Code** |

State the detected runtime to the user. They can correct.

### 2.2 Read the spec

**Single-conversation:** read backward through the conversation context to find the most recent spec emission (from Skill 1 or a prior Skill 2 invocation). The spec is identifiable by its `## 1. Bot Identity` header and `## 7. Generation Metadata` footer.

**Claude Code:** read `agent-spec.md` from the workspace (or whatever filename the user references).

If no spec is found, abort with the message: "No Agent Spec found. Skill 2 requires an existing spec produced by Skill 1. Invoke Skill 1 (Agent Spec Designer) first."

### 2.3 Build the work queue

Walk section 5. Identify all intents whose status is `[structural]` or `[detailed-revisit]`. These are the work queue.

| Status | Treatment |
|---|---|
| `[structural]` | Stub from Skill 1 greenfield. Author from scratch. |
| `[detailed-revisit]` | Was previously `[detailed]`; reset by Skill 1 patch mode. Treat identically to `[structural]` for walking purposes — author from scratch. Distinguish in section 7.3 log entry by labeling the work as "redetail" rather than "detail". |
| `[detailed]` | Skip. Already fully authored. |

**Empty queue case:** if no intents are `[structural]` or `[detailed-revisit]`, report: "All intents are already `[detailed]`. No work for Skill 2. Invoke Skill 3 (JSON Assembler) to emit the wire-format JSON." Halt.

### 2.4 Scan section 7.3 for staged notes from Skill 1

Skill 1's validation can extract per-intent procedural logic from the persona (Check 3) or other sources, and stages it for Skill 2 by writing entries in section 7.3 of the form:

```
[ISO timestamp]  Skill 1  greenfield|patch  ...  stage for Skill 2: intent <identifier> should carry the post-execution logic "<snippet>" (extracted from <source> during Skill 1 validation).
```

Build an internal map: `{ intent_identifier → list of staged snippets }`. When authoring step 4 (post-execution `intentInstructions`) for an intent that has staged notes, surface the snippets to the user as starting material, not directives. Format:

> Skill 1 staged the following content for this intent's post-execution instructions: "<snippet>". I'll incorporate it into the draft below — confirm or edit.

Staged snippets that the user discards should be logged to 7.3 as "discarded staged note from Skill 1: <snippet>". This keeps the audit trail intact.

### 2.5 State the plan

Tell the user:
- Detected runtime
- Number of intents in the work queue
- Number of staged notes from Skill 1 (if any)
- Next step: propose a batching plan

Then proceed to section 3.

---

## 3. Batching plan

Per decision A (locked Conv 2), Skill 2 walks the work queue in batches with user confirmation between them. This prevents context bloat and keeps the user in the loop on progress.

### 3.1 Algorithm

```
queue = [intents with status [structural] or [detailed-revisit]]
hard_intents = [intent in queue if its hard-intent flag in section 4 = true]
soft_intents = [intent in queue if its hard-intent flag in section 4 = false]

batches = []

# Each hard intent is a singleton batch
FOR each hard_intent in hard_intents (in section-4 order):
  batches.append([hard_intent])

# Soft intents grouped by adaptive sizing
total_count = len(queue)
target_checkpoints = derive_checkpoint_count(total_count)
soft_batch_size = ceil(len(soft_intents) / max(1, target_checkpoints - len(hard_intents)))
soft_batch_size = min(soft_batch_size, 6)  # upper bound

current_batch = []
FOR each soft_intent in soft_intents (in section-4 order):
  current_batch.append(soft_intent)
  IF len(current_batch) == soft_batch_size:
    batches.append(current_batch)
    current_batch = []

IF current_batch is not empty:
  batches.append(current_batch)
```

`derive_checkpoint_count(total_count)`:
- ≤ 5 intents:  2 checkpoints (with hard intent isolated if any)
- 6–10 intents: 3 checkpoints
- 11–15 intents: 3–4 checkpoints (favor 4 if hard intents present)
- 16–20 intents: 4 checkpoints
- > 20 intents: `ceil(total_count / 5)` checkpoints

**Edge case: only one intent in the queue.** Single batch, single intent. Still issue the checkpoint gate after completion before reporting overall completion. The user always sees an explicit confirmation point.

**Edge case: all queue intents are hard.** All batches are singletons. `target_checkpoints` calculation degenerates harmlessly; the loop just produces one batch per hard intent.

### 3.2 Present the plan

Block format (not a table — for ≤4 batches a table is visual overkill):

```
Plan to detail [N] intents in [K] batches:

Batch 1 (singleton — hard intent flagged in section 4): get_available_slots
Batch 2: validate_customer_address, confirm_appointment, transfer_to_human
Batch 3: general_inquiry, reschedule_existing

Confirm or override? You can:
- Accept the plan as-is
- Reorder batches (e.g., "do batch 2 first")
- Regroup intents (e.g., "merge batch 2 and 3" or "split batch 2")
- Start with a specific intent ("start with confirm_appointment")
```

### 3.3 Override handling

If the user overrides the plan, accept the override and log it to section 7.3:

```
[ISO timestamp]  Skill 2  detailing  Batching plan overridden by user. Original plan: <K> batches per algorithm. Final plan: <user's plan summary>.
```

If the user's override puts a hard intent in a non-singleton batch, push back once:

> Intent `<name>` was flagged as a hard intent in section 4 (slot count, conditional branching, transition complexity, or validation complexity). Singleton batching is the default to keep focus. Are you sure you want to group it with `<other intents>`?

If the user confirms, proceed with the override. Skill 2 doesn't refuse overrides — the user has the final say.

---

## 4. Per-intent four-step interview

For each intent in a batch, walk the four steps in order. The interview shape varies by Response Type, especially in step 3.

### 4.1 Step 1 — Slot detailing

Section 4 declares slot names, ParameterTypeIds, required flags, and collection orders. Step 1 elaborates each slot.

**Per slot, capture:**

| Field | Meaning | When |
|---|---|---|
| `Description` | User-facing description used by the LLM at runtime to phrase the slot collection question. Often Hebrew. | All slots |
| `OptionList` (with `Value` + `Label` per option) | Static list of choices | ENUM (PT=19) with known choices |
| `OptionList: []` + note | Options come from upstream API response | ENUM (PT=19) dynamically populated (typically downstream of an RT=2 intent declared in 4.5.4) |
| Validation guidance for v1 fallback | Format/range constraints to embed in `validationPrompt` | NUMBER/DATE/EMAIL stored as STRING (PT=1) per Skill 1 v1 fallback |

**Example slot detailing (Hebrew bot, RT=3 confirm_appointment intent):**

```
Slot: address
- Description: כתובת מלאה: רחוב, מספר בית, עיר. למשל: רחוב הרצל 14 רמת גן.
- Type: STRING (ParameterTypeId 1)
- Required: true
- Collection order: 1
- OptionList: [empty for STRING]

Slot: time_slot
- Description: בחירת זמן מבין הזמנים הזמינים שהוצגו לך
- Type: ENUM (ParameterTypeId 19)
- Required: true
- Collection order: 2
- OptionList: [] (dynamically populated from upstream get_available_slots response — see section 4.5.4)
```

**Iron rule (check 4 — fires during step 1, blocking):** if section 4 declared a slot with a type that mismatches its purpose (e.g., STRING for "phone"), do NOT silently fix. Raise:

> Slot `<name>` is declared as `<type>` in section 4 but the description suggests it should be `<other type>` (e.g., PHONE, ParameterTypeId 10). This is a structural change. Pause Skill 2, invoke Skill 1 patch mode to fix the slot type, then return.

The user must either accept the type as-is (with appropriate v1-fallback validation in step 2) or pause and patch via Skill 1.

### 4.2 Step 2 — `validationPrompt` authoring

The `validationPrompt` is the bot's primary lever for shaping how it collects slots. **Conversation Routines style is mandatory** per Doc 1 §14.3.2:

- ALL-CAPS section headers (e.g., `ADDRESS COLLECTION`, `IRON RULES`)
- Numbered steps for the collection sequence
- Explicit IF/ELSE for branching
- IRON RULE blocks for non-negotiables

Free prose is forbidden. See `conversation-routines-style-guide.md` for templates and worked examples.

**Authoring procedure:**

1. **Draft an initial prompt** from:
   - The slot list and types (from step 1)
   - The collection order (from section 4)
   - The intent's purpose (from section 4 description)
   - Any bot-level constraints in section 2.1 persona (e.g., language posture)

2. **Ask the user about edge cases** before finalizing:

   > For this intent, I want to nail down edge cases. What should the bot do if:
   > - The user gives a partial answer (e.g., street name without house number for an address)?
   > - The user gives an off-topic answer?
   > - The user refuses to provide the slot?
   > - [For v1-fallback slots] The user provides the value in an unexpected format?

3. **Incorporate edge cases** into the prompt as IF branches and IRON RULE blocks.

4. **Show the draft to the user.** They confirm or edit.

5. **Verify** before moving on:
   - Every slot in the intent appears in the prompt
   - Every v1-fallback slot has explicit format/range guidance
   - At least one IRON RULE block exists for the most critical constraint
   - Prompt language matches the bot's primary language (Hebrew text for Hebrew bots, etc.)
   - Every Mustache reference resolves (see section 5 — Mustache resolvability mechanics)

If any of these fail at end-of-step, return to authoring; do not advance to step 3.

**Iron rule (Compass rule 8 — TTS-safe formatting; fires during step 2, blocking on markdown/URLs and advisory on long digit runs):**

For each `validationPrompt` field on a voice-active intent (section 1 `Channels Active` includes `voice`), run three detections:

1. **Markdown formatting** — regex `(?m)^\s*[-*+]\s` (bullets), `(?m)^\s*#+\s` (headers), or `\[.*\]\(.*\)` (markdown links). If matched: **blocking** — voice will read these aloud literally ("dash space hello"). Surface:
   > Line `[N]` of `validationPrompt` in `[intent]` contains markdown formatting (`[matched pattern]`). Per Compass §5 anti-pattern "Chat-agent boilerplate copied to voice", TTS reads markdown literally. Rewrite as natural-language prose before proceeding.

2. **URLs** — regex `https?://\S+`. If matched: **blocking** — TTS would read the URL aloud. Surface:
   > Line `[N]` of `validationPrompt` in `[intent]` contains a URL (`[matched URL]`). Voice agents should not vocalize URLs. Replace with a description ("our website") or move the URL out of the prompt entirely.

3. **Long digit runs without spell-out instruction** — regex `\d{6,}` AND no `(?i)(digit by digit|spell|ספרה ספרה|חזרי ספרה)` instruction within 100 surrounding characters. If matched: **advisory** — surface:
   > A long digit sequence (`[matched]`) appears in `validationPrompt` of `[intent]` without a nearby "spell digit-by-digit" instruction. Per Compass §6 voice output rules, long digit runs read awkwardly. Consider adding an explicit spell-out instruction (e.g., "חזרי ספרה ספרה" for Hebrew; "Read digit by digit" for English). Continue without fix, or pause to add?

Log per-intent resolution to section 7.3: `Compass rule 8 advisory/blocking fired on [intent].validationPrompt — [resolved: yes/no]`.

**Iron rule (Compass rule 9 — date math in prompt; fires during step 2, advisory):**

In each `validationPrompt`, search for date-math patterns:
- `(?i)\bnot\s+(in\s+)?(the\s+)?future\b`
- `(?i)\b(year|שנה)\s*[≥>=]+\s*\d{4}\b`
- `(?i)\b(today|tomorrow|yesterday)\b` AND no surrounding `{{TimeNow}}` or equivalent Mustache reference within 200 characters.

If matched: advisory — surface:
> `validationPrompt` of `[intent]` contains date-math instructions (`[matched pattern]`). Per Compass §2 anti-list "Date and time math" and §8 operating rule 8, LLMs are notoriously bad at calendar arithmetic, especially under latency pressure. The doctrine recommends computing dates server-side and injecting them as pre-rendered Mustache variables in section 4.5.1 (e.g., `{{TimeNow}}` for current ISO, `{{TodayHumanHe}}` for a localized human form). Two paths:
>   (a) Replace the date-math instruction with a Mustache reference to a pre-rendered variable. Skill 2 cannot add to 4.5.1 (that's Skill 1's territory) — pause and invoke Skill 1 patch mode to declare the new call-context variable, then return.
>   (b) Keep the date-math instruction and accept the runtime risk.

Log per-intent: `Compass rule 9 advisory fired on [intent].validationPrompt — [resolved: yes/no]`.

**Iron rule (Compass rule 10 — few-shot example cap; fires during step 2, advisory):**

In each `validationPrompt`, count transcript-style example pairs. A pair is matched by:
- A line matching `(?im)^\s*(user|caller|פונה|לקוח)\s*:` followed within 10 lines by
- A line matching `(?im)^\s*(agent|bot|נציג|בוט)\s*:`.

If more than 2 pairs are found in a single `validationPrompt`: advisory — surface:
> `validationPrompt` of `[intent]` contains `[N]` transcript-style few-shot examples. Per Compass §4 "Examples vs rules", each transcript example is 80–200 tokens in English and 250–500 in Hebrew — three Hebrew few-shots can blow the entire prompt budget. The doctrine recommendation is zero examples by default; add one or two only to fix specific recurring failures (brand-name pronunciation, Hebrew date register, a misclassified tool trigger). Two paths:
>   (a) Trim to the single most calibration-relevant pair.
>   (b) Keep as-is and accept the token cost (will surface in Skill 3's rule 1 token-budget check at assembly time).

If the bot's primary language is non-English, prepend to the message: *"This bot is `[language]`, so the per-example cost is roughly 3× the English baseline — trimming has higher ROI here."*

Log per-intent: `Compass rule 10 advisory fired on [intent].validationPrompt with [N] examples — [resolved: yes/no]`.

**Iron rule (Compass rule 11 — Hebrew-utterance isolation; fires during steps 2, 3, and 4; blocking):**

For each text field Skill 2 authors (`validationPrompt`, RT-specific `announcement`/`fail_output`/`function_output`/`intentLoadingAnnouncement`, post-execution `intentInstructions`), run per-line:

Detection regex: a line contains `[֐-׿؀-ۿ一-鿿぀-ゟ゠-ヿ]+` AND the line's remaining non-whitespace content is ≥50% ASCII alphanumerics. (A line that is entirely Hebrew, or entirely English, passes. A line that mixes inline fails.)

If matched: blocking — surface:
> Line `[N]` of `[field]` in `[intent]` mixes inline RTL (`[matched text]`) with LTR English text. Per Compass §4 "Sanity rule: never inject RTL Hebrew strings into the middle of an LTR English instruction line" — terminal display lies and Unicode bidi marks tokenize to garbage. Move the RTL content to its own line, wrap it in quotes, or rewrite the line entirely. Then re-check.

Block authoring of this field until the user provides a compliant revision.

Log per-intent on resolution: `Compass rule 11 blocking fired on [intent].[field] line [N] — resolved`.

### 4.3 Step 3 — RT-specific configuration

The Configuration shape and required language fields differ by Response Type. Section 4 declares the RT for each intent — read it and branch.

#### RT=1 (Layer Transfer)

Required language fields:

| Field | Meaning | Example (Hebrew) |
|---|---|---|
| `announcement` | What the bot says before transferring | "אני מעבירה אותך לנציג, רגע אחד" |
| `intentLoadingAnnouncement` | Latency-cover utterance between announcement and the actual transfer | "המתן בבקשה" |

Layer ID is structural (declared in section 4). If marked `<UNKNOWN: layer ID>`, leave as-is — Skill 3 will emit the fail-loud sentinel `-999`. Do not invent a layer.

#### RT=2 (API Call)

Required language fields:

| Field | Meaning |
|---|---|
| **Announcement (after API success)** [JSON field: `announcement` — was `apiResponseAnnouncement` pre-v1.5.0] | What the bot says when the API succeeds. Almost always uses Mustache references against section 4.5.4 dotted paths declared by the user. |
| `fail_output` | What the bot says when the API fails. **Default pattern (graceful):** "I couldn't reach the system right now. Let me transfer you to a human." Skill 2 drafts this default; user confirms or rewrites. |
| `function_output` | **Fail-output fallback map** [JSON field: `function_output` — object shape `{ "default": "<fallback string>" }`, v1.5.0 shape change]. Skill 2 prompts the user for the fallback string the runtime should say when the API returns no usable response. The user supplies a single short Hebrew/English string (e.g., `"הייתה תקלה בחיפוש"` / `"Something went wrong, let me try again."`); Skill 2 wraps it as `{ "default": "<user's string>" }` in the spec. Skill 3 emits this object verbatim. If the user wants per-error-code fallbacks (e.g., `{ "default": "...", "503": "..." }`), they can extend the object via patch mode. v1 default capture is `default` key only. |
| `response_success` | **Response success instructions** [JSON field: `response_success` — object shape `{ "instructions": "<text or empty>" }`, v1.5.0 shape change]. Skill 2 prompts the user for any instructional text the runtime should use after a successful API call (e.g., next-step guidance for the LLM). Empty string is the most common production shape (`{ "instructions": "" }`). User supplies the inner string; Skill 2 wraps it as the object. |
| `intentLoadingAnnouncement` AND `IntentLoadingAnnouncement` | Same content, both populated. This is the case-bug pair per Doc 1 §16 — preserve both, identical content. |
| `silence_sentence` | What the bot says during the API wait |
| `silence_ending_sentence` | What the bot says after silence loops are exhausted |
| `silence_instructions` | Additional LLM guidance for silence handling (often empty) |

**Iron rule (check 11 — fires during step 3, blocking):** every RT=2 intent must populate all six api_silence fields above (silence_sentence, silence_ending_sentence, silence_instructions, plus the durations and loops which are structural in section 4). Per Doc 1 §14.3.6, an RT=2 intent without complete silence behavior produces dead air at runtime when the API takes 8+ seconds.

**Iron rule (check 10 — fires during step 3, blocking):** `announcement` (was `apiResponseAnnouncement` pre-v1.5.0), `fail_output`, `function_output`, and `response_success` must all be non-empty. The `fail_output` graceful default qualifies as non-empty. For `function_output`, the object `{ "default": "<fallback>" }` qualifies as non-empty. For `response_success`, the object `{ "instructions": "" }` (empty inner string) qualifies as non-empty.

**Mustache references in `announcement` (RT=2 success field):** must resolve against section 4.5.4 dotted paths declared for THIS intent, OR against slots collected by THIS intent or upstream intents (per section 5 mechanics). Verify at write-time.

#### RT=3 (Continue)

Required language fields:

| Field | Meaning | Example (Hebrew) |
|---|---|---|
| `announcement` | What the bot says after slot collection completes | "מעולה. רשמתי לך תור ב-{{available_slots.0.display}} בכתובת {{address}}. נשלח לך SMS עם פרטים." |

The `announcement` typically uses Mustache references against the intent's own collected slots and/or upstream API response paths.

#### RT=4 (Dial-Out)

Required language fields:

| Field | Meaning |
|---|---|
| `announcement` | Spoken before initiating the dial |
| `intentLoadingAnnouncement` | Spoken while dialing |

Other RT=4 fields (Phone destination, NEXT_VO_ID, etc.) are structural — declared in section 4 by Skill 1.

### 4.4 Step 4 — Post-execution `intentInstructions`

This is the second Conversation Routines block per intent. It defines what the bot does **after** this intent has fired and slots have been collected.

**Critical distinction (per Doc 1 §14.3.10, §14.3.12):**

- `validationPrompt` is **pre-execution** — slot collection
- `intentInstructions` (per-intent) is **post-execution** — what to do next

Skill 2 writes `intentInstructions` to cover:

- Confirmation language (e.g., `POST-EXECUTION: address validated. Proceed to slot fetch.`)
- Conditional next-intent routing if the intent's outcome varies (RT=2 with conditional success/failure paths)
- Iron rules for what NOT to do post-execution (scope-creep prevention)

**Authoring procedure:**

1. Surface any staged notes for this intent from section 2.4 (the section 7.3 scan).
2. Draft an initial `intentInstructions` block in Conversation Routines style.
3. Show the draft. User confirms or edits.
4. Verify against the four iron rules below.

**Iron rules (checks 5, 6, 7, 8 — fire during step 4, blocking):**

| Rule | Source | Catch pattern |
|---|---|---|
| Must be Conversation Routines style | §14.3.2 | Free prose without ALL-CAPS headers, numbered steps, IF/ELSE, or IRON RULES → reformat |
| Must NOT contain pre-execution slot collection logic | §14.3.12 | Sentences like "after collecting X, ensure it's…" or validation rules → relocate to `validationPrompt` |
| Must NOT contain persistent policy that applies call-wide | §14.3.13 | Sentences about privacy, GDPR, retention, broad escalation policy → relocate to `prompts.persona` (raise to user; this is a Skill 1 patch) |
| Must NOT contain bot-level disambiguation that runs before any intent fires | §14.3.11 | Sentences like "first figure out if the user wants X or Y…" → relocate to `prompts.intentInstructions` (bot-level; raise to user; this is a Skill 1 patch) |

**Misplacement handling during drafting:**

- For §14.3.12 (slot validation in intentInstructions): Skill 2 silently relocates to `validationPrompt` and informs the user. This is content Skill 2 owns on both sides of the misplacement.
- For §14.3.13 (persistent policy) and §14.3.11 (bot-level disambiguation): Skill 2 raises to user. The destination field (`prompts.persona` or `prompts.intentInstructions` bot-level) is in section 2, which Skill 2 does not modify. Recommended message:

> The text "<snippet>" appears to be <persistent policy | bot-level disambiguation> that belongs in section 2.<X>. I won't put it in this intent's post-execution instructions. Options: (a) drop the text, (b) pause Skill 2, invoke Skill 1 patch mode to add it to section 2.<X>, then return. Which?

If the user picks (b), record the choice in 7.3 and halt the current intent's authoring. The user runs Skill 1 patch mode separately, then re-invokes Skill 2 — the spec state will reflect the patch.

---

## 5. Mustache resolvability mechanics

Doc 1 §14.3.5 iron rule: every Mustache slot variable must resolve against an allowlist. Skill 2 enforces this **blocking** at field-write time and at end-of-intent gate.

### 5.1 Allowlist sources

| Reference shape | Allowlist source | Resolves if… |
|---|---|---|
| `{{slot_name}}` | Section 4.5.3 (slot inventory) | The slot is collected by THIS intent OR by an upstream intent in the flow graph (see 5.2) |
| `{{call_context_var}}` | Section 4.5.1 | The variable is listed in 4.5.1 |
| `{{ENV.VAR_NAME}}` | Section 4.5.2 | The variable is listed in 4.5.2 |
| `{{response.path.to.field}}` or `{{available_slots.N.field}}` | Section 4.5.4 (per-intent) | The dotted path is declared in 4.5.4 for THIS intent, AND the reference appears in an RT=2 field of THIS intent (`announcement`, `function_output`, etc.) |

### 5.2 Directional ordering check (v1)

The "earlier in the flow" requirement from §14.3.5 is enforced as a v1 check, not full reachability analysis.

For a slot reference `{{slot_name}}` in intent X:

1. **Same-intent slots resolve unconditionally.** If the slot is collected by intent X itself, the reference is valid in any field of X (validationPrompt, RT-specific fields, intentInstructions). The slot is collected before any of X's fields execute.

2. **Upstream slots resolve.** If 4.5.3 says the slot is collected by intent Y, AND intent Y is **not downstream** of intent X in the transition graph (section 6.2), the reference resolves. Downstream = reachable from X via outbound transitions.

3. **Downstream slots block.** If Y is downstream of X (X transitions to Y, directly or transitively), the reference is a runtime bug. Block:

   > Reference `{{<slot>}}` in `<intent X>.<field>` references a slot collected by `<intent Y>`. But `<Y>` is downstream of `<X>` in the flow graph — at runtime, the slot won't exist yet when this field fires. Possibilities: (a) the reference is wrong, (b) the flow graph order is wrong (structural — Skill 1 patch). Which?

4. **Cousin intents warn but permit.** If Y is neither upstream nor downstream of X (no transition path either way), warn:

   > Reference `{{<slot>}}` in `<intent X>.<field>` references a slot collected by `<intent Y>`. `<Y>` is neither upstream nor downstream of `<X>` in the flow graph — the runtime path may or may not pass through `<Y>` before `<X>` fires. Verify the call flow is OK with this. Continue, or pause to fix?

   Log the user's choice to 7.3. Continue or halt per their decision.

This v1 check is conservative-without-being-paranoid: catches obvious downstream errors, lets cousin-intent ambiguity through with explicit user confirmation. Full reachability analysis ("every path from start passes through Y before X") is v2.

### 5.3 Check timing

| Timing | Action |
|---|---|
| At write-time during step 2/3/4 | If Skill 2 catches an unresolvable reference while drafting, interrupt and ask the user before continuing. Do not silently emit broken text. |
| End-of-intent gate (check 9 in §6) | Re-verify all references in the intent's fields resolve. Blocking. |

### 5.4 Why blocking at Skill 2 vs advisory at Skill 1

Skill 1's pre-check is advisory because Skill 1 doesn't have all slots elaborated yet — false positives are common. By Skill 2 time, the slot inventory is final and the actual references are being written. An unresolvable reference at this stage is a real bug. Skill 3 also runs the authoritative §15.4 check — Skill 2's blocking check catches issues earlier, where the user is already authoring content.

---

## 6. Self-validation checklist

Per intent, before flipping status to `[detailed]`. Each check has a timing classification: **during** (fires while authoring the relevant step) or **gate** (fires at end-of-intent before status flip). Some fire at both.

| # | Check | Source | Severity | Timing |
|---|---|---|---|---|
| 1 | `validationPrompt` is non-empty and Conversation Routines styled | §14.3.2 | blocking | during step 2 + gate |
| 2 | `validationPrompt` covers every slot in the intent | §14.3.2 | blocking | gate |
| 3 | `validationPrompt` includes at least one IRON RULE block | §14.3.3 | blocking | gate |
| 4 | Slot type matches purpose (no STRING for phone, etc.) | §14.3.3 | blocking | during step 1 |
| 5 | `intentInstructions` is non-empty and Conversation Routines styled | §14.3.2 | blocking | during step 4 + gate |
| 6 | `intentInstructions` does not contain slot collection logic | §14.3.12 | blocking | during step 4 |
| 7 | `intentInstructions` does not contain persistent policy | §14.3.13 | blocking | during step 4 |
| 8 | `intentInstructions` does not contain bot-level disambiguation | §14.3.11 | blocking | during step 4 |
| 9 | All Mustache references resolve against section 4.5 + upstream slots, with directional ordering | §14.3.5 / §15.4 #7 | blocking | during steps 2/3/4 + gate |
| 10 | RT=2 only: `announcement` (was `apiResponseAnnouncement` pre-v1.5.0), `fail_output`, `function_output` (object `{ "default": "..." }`), `response_success` (object `{ "instructions": "..." }`) all populated | §14.3.6 | blocking | during step 3 + gate |
| 11 | RT=2 only: API silence behavior fully populated (`silence_sentence`, `silence_ending_sentence`, `silence_instructions`, plus the structural duration and loops from section 4) | §14.3.6 | blocking | during step 3 + gate |

**Behavior on blocking failure at gate:** do NOT mark the intent `[detailed]`. Surface the failure to the user with the specific check number and remediation suggestion. The user fixes the field; Skill 2 re-runs the gate; on pass, status flips.

**Behavior on blocking failure during authoring:** interrupt the step, surface the issue, get user input, retry the step. Do not advance to the next step until resolved.

---

## 7. Section update boundaries

Skill 2 modifies a defined subset of the spec. Crossing these boundaries silently is a category error.

### 7.1 What Skill 2 writes

| Section | Operation | When |
|---|---|---|
| Section 5 entry per intent | Fill content; flip status `[structural]` or `[detailed-revisit]` → `[detailed]` | After self-validation passes |
| Section 4.5.3 (slot inventory) | Regenerate from section 5 state | At end of each batch |
| Section 6.1 (Mustache variable usage) | Append references just written, with location and resolution source | After each intent's step 2/3/4 |
| Section 7.3 (generation log) | Append entry per batch + per invocation | At each batch checkpoint and at invocation end |
| Section 7.4 (open unknowns) | Add or remove `<UNKNOWN: ...>` markers if the batch introduced or resolved any | At end of each batch |
| Section 7.5 (pending work) | Refresh remaining `[structural]` and `[detailed-revisit]` count + list | At end of each batch |

### 7.2 What Skill 2 leaves untouched

- **Section 1** — Bot Identity. Skill 1's domain.
- **Section 2** — Persona Bundle. All five fields. Skill 1's domain. If Skill 2 detects content that should live here (per §14.3.11 or §14.3.13), it raises to the user and recommends Skill 1 patch mode.
- **Section 3** — Caller Silence Behavior. Skill 1's domain.
- **Section 4** — Intent List structural. Slot names, types, required, collection order, transitions, RT, hard-intent flags. Skill 1's domain. If Skill 2 detects a structural problem (e.g., wrong slot type in step 1 check 4), it raises to the user and recommends Skill 1 patch mode.
- **Section 4.5.1** — Call-context variables. Skill 1's domain.
- **Section 4.5.2** — Environment variables. Skill 1's domain.
- **Section 4.5.4** — API response variables per RT=2 intent. Skill 1's domain.

### 7.3 4.5.3 regeneration mechanic

Section 4.5.3 format from Skill 1's spec-skeleton:

```
- `{{slot_name}}` — collected by `<intent_identifier>`, type `<ParameterTypeId name>`
```

There is no description field. Skill 2's slot description (authored in step 1) lives in section 5, not 4.5.3. The 4.5.3 regeneration is a consistency operation: walk all intents in section 5 (including those still `[structural]`), enumerate slots, write the standard line per slot. In normal cases, the regenerated 4.5.3 is identical to Skill 1's version. If it differs, that's a signal section 4 was edited inconsistently — surface to the user as a soft warning.

### 7.4 6.1 incremental update mechanic

Section 6.1 format from Skill 1's spec-skeleton:

```
- reference: `{{variable_name}}` or `{{path.to.field}}`
- used in: [intent identifier, field name]
- resolves via: [section 4.5.X] or [section 5 slot of intent X]
```

Each Mustache reference Skill 2 writes during steps 2/3/4 gets a 6.1 entry appended. Skill 1's initial 6.1 covers references in section 2 (persona, openingAnnouncement, bot-level intentInstructions) and section 4 (RT=2 body fields). Skill 2's additions cover validationPrompt, per-intent intentInstructions, RT-specific announcement/fail_output/function_output fields.

Skill 3 will regenerate section 6 entirely as a sanity check before §15.4. If Skill 3's regeneration differs from the spec's 6.1, that's a drift signal Skill 3 reports.

---

## 8. Checkpoint mechanic

After each batch completes (all intents in the batch are `[detailed]`), Skill 2 issues a checkpoint gate. Same prompt in both runtimes; different state mechanic.

### 8.1 Single-conversation runtime

Emit the updated spec as a chat message. Then:

> Batch [N] complete. Intents now `[detailed]`: [list].
>
> Section 7.5 says [M] intents still pending: [list].
>
> Continue with batch [N+1] or pause?

If user pauses: halt. The spec is in the conversation; user re-invokes Skill 2 in the same conversation or a new one. Reactivation re-reads the spec and rebuilds the work queue from current `[structural]` / `[detailed-revisit]` markers.

### 8.2 Claude Code runtime

Write the updated spec to `agent-spec.md` in the workspace. Then:

> Batch [N] complete. Spec written to `agent-spec.md`. Intents now `[detailed]`: [list].
>
> Section 7.5 says [M] intents still pending: [list].
>
> Continue with batch [N+1] or pause?

If user pauses: halt. The spec file is the durable state. User re-invokes Skill 2 in this session or a future one — same skill reads the same file, rebuilds the work queue.

### 8.3 The spec is the state

There is no session token, no "continue command", no internal flag. The work queue is computed at the start of every invocation by scanning section 5. If a previous invocation marked some intents `[detailed]` and the user paused, the next invocation sees those intents as `[detailed]` and skips them.

This means: the user can edit the spec between invocations (e.g., manually flip an intent back to `[structural]` to redo it, or add a new intent via Skill 1 patch mode). Skill 2 picks up from whatever the spec currently says.

### 8.4 Single-batch case

If the work queue is exactly one intent (one batch with one intent), the checkpoint gate still fires. The user always sees an explicit confirmation point, even when there's nothing left to do.

> Batch 1 complete (single intent). Intent `<name>` is now `[detailed]`. All intents in this invocation are detailed. Invoke Skill 3 (JSON Assembler) to emit the wire-format JSON.

---

## 9. Output contract

### 9.1 Per batch

- Updated spec: this batch's intents now `[detailed]`, content fully filled
- Section 4.5.3 regenerated
- Section 6.1 appended with this batch's Mustache references
- Section 7.3 generation log entry for the batch
- Section 7.4 updated if unknowns changed
- Section 7.5 updated to reflect remaining work
- Checkpoint gate prompt (§8)

Section 7.3 entry format:

```
[ISO timestamp]  Skill 2  detailing  Batch <N>: detailed <count> intents (<list>). <H> hard intents (<list>) handled as singletons. <D> redetailed (<detailed-revisit list>). Self-validation passed for all.
```

### 9.2 Per invocation completion (user pauses or queue exhausted)

After the final batch in this invocation:

> [N] intents detailed in this invocation. [M] intents still pending: [list, or "none"]. Re-invoke Skill 2 to continue, or invoke Skill 3 if [M] = 0.

### 9.3 Final completion (all intents `[detailed]`)

When the work queue is exhausted and section 7.5 reports zero pending:

- Section 7.3 log entry: `Skill 2 detailing complete. All intents [detailed]. Spec ready for Skill 3.`
- Section 7.5: `0 intents pending. 0 hard intents pending. Ready for Skill 3.`
- Closing message:

> Spec is fully detailed. All intents are `[detailed]`. Open unknowns (section 7.4): [count]. Next step: invoke **Skill 3 (JSON Assembler & Publish)** to emit the wire-format JSON.
>
> [single-conversation: type "run Skill 3" or attach this spec to a fresh conversation]
> [Claude Code: invoke Skill 3 — it reads the same `agent-spec.md` file]

---

## 10. Anti-list — what Skill 2 does NOT do

- Modify spec sections 1, 2, 3, 4, 4.5.1, 4.5.2, 4.5.4 — Skill 1's domain. If a structural change is needed, raise to user, recommend Skill 1 patch mode, halt the current intent's authoring.
- Change an intent's Response Type. Structural — Skill 1 patch mode.
- Add or remove intents. Skill 1.
- Modify transitions. Skill 1.
- Run the §15.4 cross-reference pass. Skill 3.
- Emit wire-format JSON. Skill 3.
- Walk past a batch checkpoint without explicit user confirmation.
- Mark an intent `[detailed]` without passing the §6 self-validation checklist.
- Invent values for unknowns. Mark `<UNKNOWN: ...>` instead and aggregate to section 7.4.
- Auto-fix structural issues caught during authoring (wrong slot type, missing transitions, etc.). Raise to user, recommend Skill 1 patch.
- Discard staged notes from Skill 1 silently. Surface them to the user; if discarded, log to 7.3.
- Constrain `validationPrompt` length or character set. Doc 1 v1 doesn't constrain; trust the platform to reject if it has limits.
- Refuse user overrides to the batching plan. Push back once for hard-intent-in-non-singleton-batch, then accept.

---

## Appendix A — Doc 1 §14.3 anti-patterns Skill 2 enforces

| § | Name | Skill 2 enforcement |
|---|---|---|
| 14.3.2 | Free prose instead of Conversation Routines | Steps 2 + 4 authoring + checks 1 and 5 |
| 14.3.3 | Slot definition missing validation guidance | Step 1 + check 4 + check 3 (IRON RULE block in validationPrompt) |
| 14.3.5 | Mustache referencing slots before collection | Section 5 (Mustache resolvability) + check 9 |
| 14.3.6 | RT=2 missing api_silence_behaviour | Step 3 RT=2 branch + checks 10 and 11 |
| 14.3.11 | Bot-level disambiguation in per-intent fields | Step 4 + check 8 |
| 14.3.12 | Slot validation in intentInstructions | Step 4 + check 6 |
| 14.3.13 | Persistent policy in single intent | Step 4 + check 7 |

Skill 1 owns: §14.3.1 (persona content), §14.3.4 (escalation transitions), §14.3.7 (capabilities ⊆ intents), §14.3.8 (naming), §14.3.9 (channel content placement), §14.3.10 (per-intent logic in persona).

Skill 3 owns: §14.3.5 authoritative cross-reference (§15.4 #7), plus all 7 cross-reference checks.

---

## Appendix B — Conversation Routines style quick reference

Full templates and worked examples in `conversation-routines-style-guide.md`. This appendix is the brief.

**Required elements:**

1. **ALL-CAPS section headers** anchor the structure. Examples: `ADDRESS COLLECTION`, `IRON RULES`, `POST-EXECUTION BEHAVIOR`, `OPENING BEHAVIOR`.
2. **Numbered steps** for sequential collection or post-execution actions. Use `1.`, `2.`, `3.`, not bullets.
3. **IF / ELSE branches** for conditional behavior. Indented under the step they condition.
4. **IRON RULE blocks** for non-negotiables. Always at least one, typically at the end of the prompt.

**Forbidden:**

- Free prose paragraphs ("After the user gives their address, just verify it makes sense and then move on.")
- Vague directives ("Be helpful.")
- Channel-specific behavior in `validationPrompt` or `intentInstructions` (belongs in voiceInstructions / chatInstructions, section 2)
- Persistent policy ("We're GDPR-compliant. We never share data.") in `intentInstructions` (belongs in persona, section 2.1)

**Minimal valid `validationPrompt`:**

```
ADDRESS COLLECTION
1. Ask the caller for their full address.
2. Repeat the street and number back for confirmation.
3. Confirm with caller.

IRON RULE: do not accept partial addresses. Street name + house number + city are all required.
```

**Minimal valid post-execution `intentInstructions`:**

```
POST-EXECUTION BEHAVIOR
1. Confirm the validated address back to the caller.
2. Proceed to fetch available time slots.

IRON RULE: do not discuss pricing or technical issues. Transfer to human for those.
```

---

## Appendix C — RT-specific field cheat sheet

What Skill 2 must populate in step 3 per RT.

| RT | Required fields (Skill 2) | Mustache scope |
|---|---|---|
| 1 | `announcement`, `intentLoadingAnnouncement` | Slots from this intent + upstream + 4.5.1 + 4.5.2 |
| 2 | `announcement` (was `apiResponseAnnouncement` pre-v1.5.0), `fail_output`, `function_output` (object `{ "default": "..." }`), `response_success` (object `{ "instructions": "..." }`), `intentLoadingAnnouncement`, `IntentLoadingAnnouncement` (case-bug pair, identical content), `silence_sentence`, `silence_ending_sentence`, `silence_instructions` | Above + 4.5.4 dotted paths declared for THIS intent |
| 3 | `announcement` | Slots from this intent + upstream + 4.5.1 + 4.5.2 + 4.5.4 from upstream RT=2 intents |
| 4 | `announcement`, `intentLoadingAnnouncement` | Slots from this intent + upstream + 4.5.1 + 4.5.2 |

Structural fields per RT (declared in section 4 by Skill 1 — not Skill 2's domain):

- RT=1: layer ID
- RT=2: URL, method, headers, body (with Mustache), structural api_silence_behaviour pairing in section 4 + 6.3, response shape declared in 4.5.4
- RT=3: (no structural fields beyond slots)
- RT=4: phone destination, parameter holding phone, NEXT_VO_ID, max dial duration, select-dial option, record (bool)

---

*End of Skill 2 — Intent Detail Author.*
