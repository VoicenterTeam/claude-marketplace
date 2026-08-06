---
name: voicenter-bot-intent-detail-author
description: Authors the per-intent language content of a Voicenter Agent Spec — slot descriptions, capture-mapping validationPrompt (save/set logic only — never spoken scripts), announcement + intentLoadingAnnouncement spoken content, post-execution intentInstructions, and RT-specific Configuration text. Use this skill when an Agent Spec exists with section 5 entries marked `[structural]` or `[detailed-revisit]`, and the user wants to fill them in. Trigger phrases include "run Skill 2", "detail the intents", "fill in the per-intent fields", "Skill 2 (Intent Detail Author)", or any direct continuation from Skill 1's handoff hint. Walks intents in user-confirmed batches with a checkpoint after each batch. Reactivable — invoke as many times as needed; spec state is the resume point. Does NOT modify the structural skeleton (sections 1, 2, 3, 4, 4.5.1/.2/.4/.5) — that's Skill 1 (Agent Spec Designer) — with one narrow v1.14.0 exception: it authors the section-4 `**Max turns sentence:**` language field (gender-matched, once per bot). Does NOT emit wire-format JSON — that's Skill 3 (JSON Assembler).
---

> **Language.** Reply in the user's language: detect what they write — Hebrew→Hebrew, English→English — and mirror it, switching if they switch mid-conversation. This shapes your prose, your questions, and your `AskUserQuestion` option labels only. It does **not** change the artifacts you produce — identifiers, JSON keys, BCP-47 language codes, API field names, and other data stay exactly as specified.

> **Opening.** Your first message greets bilingually so the user knows both languages are available — e.g. *"נוכל להמשיך בעברית או באנגלית — מה נוח לך? / We can continue in Hebrew or English — whichever you prefer."* Then mirror whatever language the user replies in.

> **One question per turn.** Ask exactly one question per message and wait for the answer before asking the next — never present multiple questions in a single turn. When the answer is a closed set (pick-one / yes-no / pick-from-list), use the `AskUserQuestion` tool rather than plain text; it automatically adds an "Other" free-text escape, so don't hand-roll one. Reserve plain free-text questions for genuinely open inputs (names, descriptions, URLs, numbers). This complements the work-queue batching (§3) and checkpoint mechanic (§8) — those govern how intents are grouped across turns; this governs how many questions you put in one message.

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
| Doc 1 §14.3.2 — Conversation Routines style | Iron rule for intentInstructions (v1.13.0: validationPrompt uses the FP-5 capture-mapping form instead) |
| Doc 1 §14.3.3 — Slot validation guidance | Step 1 + Step 2 |
| Doc 1 §14.3.5 — Mustache referencing slots before collection | Mustache directional ordering |
| Doc 1 §14.3.6 — RT=2 api_silence_behaviour completeness | Step 3 RT=2 |
| Doc 1 §14.3.11 — Bot-level disambiguation in per-intent fields | Step 4 misplacement check |
| Doc 1 §14.3.12 — Slot validation in intentInstructions | Step 4 misplacement check |
| Doc 1 §14.3.13 — Persistent policy in single intent | Step 4 misplacement check |
| Doc 1 §14.3.14 — Field-purpose cheat sheet | Disambiguating misplacement |
| Doc 2 §5 — Skill 2 architecture | What Skill 2 does |
| Doc 2 §3.6 — Status mechanic for section 5 intents | Reactivation logic |
| `../../references/voice-prompt-doctrine.md` | Compass doctrine — 13 rules; Skill 2 owns the primary enforcement of rules 8 (TTS-safe formatting — spoken fields only, v1.13.0), 9 (date math in prompt), 10 (few-shot count cap), 11 (Hebrew-utterance isolation) |
| `../../references/field-placement-doctrine.md` | Field-placement doctrine (v1.17.0) — FP-1…FP-13; Skill 2 owns FP-3 (script home + the turn-yield rule: announcement empty on auto-chaining intents, v1.17.0), FP-4 (quote convention), FP-5 (capture-mapping validationPrompt), FP-7 (RT=3 loading announcement), FP-8's pre-terminal farewell authoring (v1.14.0), and the per-intent half of FP-6 (say-once) |
| Skill 3 SKILL.md §4.4 | RT=1/2/3/4 Configuration field shapes at emission — v1.5.0 production-aligned (announcement / function_output object / response_success object). *(v1.13.0: replaces the retired external schema-audit doc reference.)* |

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

**Iron rule (sensitive backstop — v1.14.0; fires during step 1, advisory):** if this intent's slots collect truly sensitive data (national ID / ID number, credit card number / CVV / expiry / cardholder ID, medical information) and section 4 does NOT carry `**Sensitive:** true` on it, raise to the user:

> Intent `<name>` collects `<what>` but is not flagged `**Sensitive:** true`. The flag belongs on the COLLECTING intent (this one). Recommend: pause and set it via Skill 1 patch mode — Skill 2 never edits section-4 flags.

Whenever an intent IS (or becomes) sensitive-flagged, ALWAYS deliver the disclosure — even if the user didn't ask: *"This intent has sensitive-data handling enabled for Information Security — the collected details can still be used in API calls configured on this same intent, but they will NOT be saved in the LOGS/TRACES."* Log to 7.3.

### 4.2 Step 2 — `validationPrompt` authoring

**Doctrine (v1.13.0, FP-5 — this section was inverted; see `../../references/field-placement-doctrine.md`):** the `validationPrompt` is consumed ONLY by the **Intent Agent** — the parameter-extraction/validation layer. It is never spoken and never forwarded to the live voice model. Anything written here that was meant to be spoken **will not be spoken** (verified production behavior). Its content is therefore a **capture mapping**: 1–3 short bullet lines, one per outcome or slot, in save/capture/set language. English operational prose is recommended (Compass rule 3 synergy); target-language text appears only as a quoted VALUE being saved.

Canonical form (golden reference, verbatim style):

```
* If the customer confirms, save "true" in the parameter details_confirmed.
* If the customer disapproves, save "false" in the parameter details_confirmed.
```

For an intent carrying a section-4 `**Terminal outcome:**`, write the form matching the declared **value mode**:

- **fixed** (quoted value in the spec): pin the exact string —
  `1. Set <slot> to exactly this value; do not translate, paraphrase, or alter it: "<the fixed string>"`
  `2. Never ask the customer to choose or confirm this value — it is fixed for this outcome.`
- **captured**: save the customer's utterance — `Save the callback time (day and hour) the customer stated in the parameter callback_time.`
- **dynamic**: an explicit per-call composition instruction for the slot.

**FORBIDDEN in validationPrompt (blocking — check 3, mirrored by Skill 3 check 16):** scripts to speak, questions to ask, greetings, turn-taking guards, routing instructions, ALL-CAPS "GATE" recipes with `Say…`/`Ask…` steps. The asking happens where the voice model can see it — in the **previous** intent's `announcement` (FP-2 staggering) or this intent's post-execution `intentInstructions` (step 4). See `conversation-routines-style-guide.md` §3 for the capture-mapping patterns (C1–C5).

**Authoring procedure:**

1. **Read the intent's slots (step 1) and its section-4 `**Captures answer to:**`** — the question whose answer this intent stores was asked one step earlier (or by the opening). The mapping translates *that answer* into *this intent's slots*.

2. **Draft the mapping bullets** — one line per collectable slot / per outcome of the captured question; for `**Terminal outcome:**` intents, the value-mode form above.

3. **Ask the user about capture edge cases** where relevant:
   > When the caller answers "[the captured question]", how should edge answers map? E.g., a hesitant "אולי"/"maybe" — save as false, or leave the slot unfilled and let the instructions re-ask? A partial answer for `[slot]` — save what was given?

4. **Show the draft to the user.** They confirm or edit.

5. **Verify** before moving on:
   - Every collectable slot in the intent has exactly one mapping line
   - Every v1-fallback slot's mapping line carries its format/range constraint (e.g., "save only if a valid 9-digit ID, else leave unfilled")
   - NO speech content: no ask/say/tell/greet/read-back imperatives, no question addressed to the caller, no turn-taking or "wait" guards, no routing
   - For a `**Terminal outcome:**` intent: the mapping implements the declared value mode (fixed ⇒ the exact string appears verbatim)
   - Every Mustache reference resolves (see section 5 — Mustache resolvability mechanics)

If any of these fail at end-of-step, return to authoring; do not advance to step 3.

**Iron rule (sequential collection — retargeted v1.13.0; fires during steps 2–4, blocking):**

If the intent has **two or more collectable slots**, the questions must still be asked one at a time — but the ASK sequence no longer lives in `validationPrompt` (the voice model never sees it). "Collectable" excludes values populated from an upstream RT=2 API response — those are not asked of the caller.

Two conditions, both required:

1. The questions are authored where the voice model sees them — in the previous intent's `announcement`/instructions or this intent's `intentInstructions` (step 4) — **one question per turn**, ordered by `CollectionOrder`, each mandated line using the FP-4 quote convention.
2. `validationPrompt` carries exactly one capture line per slot (no bundled "capture everything" line).

If either condition is unmet, **block** — do not flip the intent to `[detailed]`.

A single logical slot the caller answers in one breath (e.g. a `full address` STRING covering street + number + city) is still **one** slot and therefore one turn — the rule constrains across distinct declared slots, not the internal richness of one slot.

Log on resolution to section 7.3: `Sequential-collection rule fired on [intent] — resolved`.

**Iron rule (Compass rule 8 — TTS-safe formatting; retargeted v1.13.0; fires during steps 3–4, blocking on markdown/URLs and advisory on long digit runs):**

`validationPrompt` is EXEMPT from rule 8 — it is never vocalized (FP-5), and its canonical capture-mapping form legitimately uses `*` bullets. The three detections below run instead on every **spoken** field Skill 2 authors on a voice-active intent (`announcement`, `intentLoadingAnnouncement`, `fail_output`, `function_output`, and the FP-4 quoted lines inside post-execution `intentInstructions`):

1. **Markdown formatting** — regex `(?m)^\s*[-*+]\s` (bullets), `(?m)^\s*#+\s` (headers), or `\[.*\]\(.*\)` (markdown links). If matched: **blocking** — voice will read these aloud literally ("dash space hello"). Surface:
   > Line `[N]` of `[spoken field]` in `[intent]` contains markdown formatting (`[matched pattern]`). Per Compass §5 anti-pattern "Chat-agent boilerplate copied to voice", TTS reads markdown literally. Rewrite as natural-language prose before proceeding.

2. **URLs** — regex `https?://\S+`. If matched: **blocking** — TTS would read the URL aloud. Surface:
   > Line `[N]` of `[spoken field]` in `[intent]` contains a URL (`[matched URL]`). Voice agents should not vocalize URLs. Replace with a description ("our website") or move the URL out of the prompt entirely.

3. **Long digit runs without spell-out instruction** — regex `\d{6,}` AND no `(?i)(digit by digit|spell|ספרה ספרה|חזרי ספרה)` instruction within 100 surrounding characters. If matched: **advisory** — surface:
   > A long digit sequence (`[matched]`) appears in `[spoken field]` of `[intent]` without a nearby "spell digit-by-digit" instruction. Per Compass §6 voice output rules, long digit runs read awkwardly. Consider adding an explicit spell-out instruction (e.g., "חזרי ספרה ספרה" for Hebrew; "Read digit by digit" for English). Continue without fix, or pause to add?

Log per-intent resolution to section 7.3: `Compass rule 8 advisory/blocking fired on [intent].[field] — [resolved: yes/no]`.

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

**TTS sanitization (voice-agent-llm v1.0.3+):** the service now sanitizes voice-active text before it reaches TTS, so unintended Markdown is no longer spoken literally. The existing authoring rule still applies: write plain conversational prose in the spoken fields — `announcement`, `intentLoadingAnnouncement`, `fail_output`, `function_output`, and the quoted spoken lines of post-execution `intentInstructions`. (`validationPrompt` is exempt — never vocalized, v1.13.0 FP-5.) The sanitizer is a belt-and-suspenders safeguard, not a substitute for clean authoring.

### 4.3 Step 3 — RT-specific configuration

The Configuration shape and required language fields differ by Response Type. Section 4 declares the RT for each intent — read it and branch.

#### RT=1 (Layer Transfer)

**v1.14.0 hard rule — RT=1 has NO `announcement`. Never author one.** The ending/farewell sentence is authored while detailing the terminal's **PREVIOUS** intent (or the dedicated pre-IVR farewell intent Skill 1 created when the predecessor splits): an FP-4 quoted line as the LAST spoken line of that predecessor's post-execution `intentInstructions`, immediately followed by the instruction to forward to this terminal (by its Description) **without waiting for a caller answer and without telling the caller the call is being transferred to a layer**. Production-verbatim shape:

```
עלייך לומר את המשפט הבא ללקוח מיד : "ההודעה נשלחה, שמחתי לעזור, שיהיה יום נהדר".
מיד לאחר מכן עלייך להעביר את השיחה מיד ל-[terminal Description] ללא המתנה לתגובה מהלקוח.
אסור לך לומר ללקוח שאתה מעביר לשכבת ניתוק.
```

Required language field (the terminal's ONLY utterance):

**Iron rule (RT=1 wording match — fires during step 3, blocking):** before picking `intentLoadingAnnouncement` wording, determine which RT=1 sub-case this terminal is, from its section-4 **Description**:

- **Hang-up terminal** (the call ends here — e.g. "ניתוק עקב שקט ממושך", "סיום השיחה במקרה של דיבור על נושא לא קשור יותר מ-N פעמים"): a short farewell/goodbye filler is correct.
- **Transfer terminal** (the call continues to a queue or human rep — e.g. "העברה לתור טכני", "העברה לנציג אנושי"): the filler MUST communicate that a transfer is happening. Farewell/goodbye phrasing here reads to the caller as the call ending, not as being connected onward — this exact mistake shipped on a production bot (a transfer intent's loading announcement carried a farewell line) and is why this rule exists.

| Field | Terminal type | Example (Hebrew) |
|---|---|---|
| `intentLoadingAnnouncement` | Hang-up | "יום טוב!" / "שיהיה המשך יום טוב!" |
| `intentLoadingAnnouncement` | Transfer | "רגע אחד, מעביר אותך." / "מעביר לנציג אנושי." |

Either way, it must NOT be the full farewell (that lives on the predecessor — FP-6 say-once, check 14; farewell placement, check 18) — it is the RT=1 intent's ONLY spoken content (v1.14.0).

Layer ID is structural (declared in section 4). Skill 1 captures the real layer number from the MCP; if the spec omits a layer, Skill 3 defaults it to `0` (root layer) — there is no `-999` sentinel for layer (v1.12.0). Do not invent a specific layer.

For a terminal carrying `**Terminal outcome:**`, step 2 already wrote the outcome-value capture mapping (check 17); step 3 confirms the loading filler only — the closing line is authored on the predecessor (check 18).

#### RT=2 (API Call)

**Iron rule (live API verification — fires during step 3, blocking; HARD BLOCK, no waiver):**

Before authoring/confirming the RT=2 `announcement`, Skill 2 must verify the API live. An RT=2 intent CANNOT be marked `[detailed]` until this passes. There is no waiver.

1. **Gather a concrete sample request.** Ask the user for real values for the body's Mustache slots and for any secret/auth header values (from section 4.5.2 env or supplied inline for the call). If the URL is still `<UNKNOWN: webhook URL>`, verification cannot run — **block** and route the user back to Skill 1 patch mode to supply the URL.
2. **Execute a live `curl`** (via the Bash tool) against the section-4 URL using the captured method/headers/body with the sample values substituted. Example shape: `curl -sS -X POST "<url>" -H "<header>: <value>" -d '<body-json>' -w "\n%{http_code}"`.
3. **Pass condition (both must hold):**
   - HTTP status is 2xx.
   - Every dotted path declared in section 4.5.4 for this intent, AND every path referenced in the `announcement`, is present in the live response JSON (path form per 4.5.4: `available_slots.0.display`, `response.order.status`).
4. **On pass:** record a verification entry in spec section 7.6 (see `spec-skeleton.md` §7.6) — ISO-8601 timestamp, intent identifier, HTTP status, the confirmed dotted paths, and a **redacted** echo of the request (method, URL, header NAMES with values masked, body with Mustache-slot values masked). Then continue to the language fields.
5. **On any failure** — non-2xx, network/DNS error, unknown URL, or any declared path absent — **block**. Surface the exact failure (HTTP code + body excerpt, or the specific missing path). The intent cannot reach `[detailed]`.

**Secrets & PII:** never write raw secrets or raw PII to the spec. Section 7.6 stores only the masked request echo, the status code, and the confirmed path list.

Required language fields:

| Field | Meaning |
|---|---|
| **Announcement (after API success)** [JSON field: `announcement` — was `apiResponseAnnouncement` pre-v1.5.0] | What the bot says when the API succeeds — **and then it yields the turn and WAITS for a caller answer (v1.17.0 turn-yield fact, FP-3)**. Author it ONLY when the intent's section-4 `**Asks next:**` is a question; it then carries the read-back + that question, almost always with Mustache references against section 4.5.4 dotted paths. When `**Asks next:**` is `[none]` (the intent auto-chains), this field MUST be the empty string — the success speech lives as FP-4 quoted lines in the post-execution `intentInstructions`, immediately before the forward. Log the intentional-empty choice to §7.3. |
| `fail_output` | What the bot says when the API fails. **Default pattern (graceful):** "I couldn't reach the system right now. Let me transfer you to a human." Skill 2 drafts this default; user confirms or rewrites. |
| `function_output` | **Fail-output fallback map** [JSON field: `function_output` — object shape `{ "default": "<fallback string>" }`, v1.5.0 shape change]. Skill 2 prompts the user for the fallback string the runtime should say when the API returns no usable response. The user supplies a single short Hebrew/English string (e.g., `"הייתה תקלה בחיפוש"` / `"Something went wrong, let me try again."`); Skill 2 wraps it as `{ "default": "<user's string>" }` in the spec. Skill 3 emits this object verbatim. If the user wants per-error-code fallbacks (e.g., `{ "default": "...", "503": "..." }`), they can extend the object via patch mode. v1 default capture is `default` key only. |
| `response_success` | **Response success instructions** [JSON field: `response_success` — object shape `{ "instructions": "<text or empty>" }`, v1.5.0 shape change]. Skill 2 prompts the user for any instructional text the runtime should use after a successful API call (e.g., next-step guidance for the LLM). Empty string is the most common production shape (`{ "instructions": "" }`). User supplies the inner string; Skill 2 wraps it as the object. |
| `intentLoadingAnnouncement` | Latency-cover utterance while the API call is in flight. (v1.5.0: capital-I `IntentLoadingAnnouncement` removed; only lowercase is emitted.) |
| `silence_sentence` | What the bot says during the API wait |
| `silence_ending_sentence` | What the bot says after silence loops are exhausted |
| `silence_instructions` | Additional LLM guidance for silence handling (often empty) |

**Iron rule (check 11 — fires during step 3, blocking):** every RT=2 intent must have a complete `api_silence_behaviour`, which is **six components** — three language fields Skill 2 authors here (`silence_sentence`, `silence_ending_sentence`, `silence_instructions`) and three structural fields owned by Skill 1 in section 4 (`silence_duration`, `silence_loops`, and the **fallback intent** — the `intent` failover that Skill 3 resolves to an `IntentId` and emits as `api_silence_behaviour.intent` + `apiSilenceRelations[].ApiSilenceIntentID`). If the structural **fallback intent is missing or unresolved** in section 4, halt and route the user back to Skill 1 patch mode — do not author around it. Per Doc 1 §14.3.6, an RT=2 intent without complete silence behavior produces dead air at runtime when the API takes 8+ seconds; an RT=2 intent **without a fallback intent has no failover** when the caller goes silent mid-API.

**Iron rule (check 10 — fires during step 3, blocking; announcement clause rewritten v1.17.0 per FP-3 turn-yield):** `fail_output`, `function_output`, and `response_success` must all be non-empty. `announcement` is conditional: **non-empty and question-carrying when `**Asks next:**` is a question; MUST be the empty string when `**Asks next:**` is `[none]`** — a non-empty announcement on an auto-chaining intent makes the bot wait for a caller answer that never comes (turn-yield stall → silence loop). The `fail_output` graceful default qualifies as non-empty. For `function_output`, the object `{ "default": "<fallback>" }` qualifies as non-empty. For `response_success`, the object `{ "instructions": "" }` (empty inner string) qualifies as non-empty. **Note:** for `function_output`, `{ "default": "" }` (empty inner string) also qualifies as non-empty for this check — only a missing `function_output` key fails. Production has RT=2 intents with empty inner strings (e.g., transport-planner `plan_customer_travel_route`); the check validates structure, not content fullness.

**Mustache references in `announcement` (RT=2 success field):** must resolve against section 4.5.4 dotted paths declared for THIS intent, OR against slots collected by THIS intent or upstream intents (per section 5 mechanics). Verify at write-time.

**Runtime fallback (voice-agent-llm v1.0.3+):** if `announcement` ships empty, the service substitutes the sentinel `[START THE CONVERSATION]` as an LLM instruction (bot opens from persona; the literal string is **not** spoken aloud). **Check 10 requires `announcement` populated on answer-awaiting intents** — the fallback is a service-side safety net, not a license to ship empty there. On auto-chaining intents (`**Asks next:**` [none]) the empty string is mandatory (v1.17.0, FP-3 turn-yield).

#### RT=3 (Continue)

Required language fields (v1.13.0 — rewritten per FP-2/FP-3/FP-7):

| Field | Meaning | Example (Hebrew) |
|---|---|---|
| `announcement` | The REAL spoken content delivered when this intent's tool completes — **after which the bot yields the turn and WAITS for a caller answer (v1.17.0 turn-yield fact, FP-3)**: the read-back with `{{CustomData}}`/slot vars plus **the section-4 `**Asks next:**` question** — the question the NEXT intent's slots will capture (FP-2 staggering). NEVER filler ("תודה.", "קיבלתי.") — acknowledgment belongs in `intentLoadingAnnouncement`. **MUST be empty whenever `**Asks next:**` is `[none]`** — an auto-chaining intent with a non-empty announcement stalls waiting for an answer that never comes (turn-yield → silence loop). The FP-3 named cases: (a) an API-response list read immediately under this intent's `intentInstructions` reading instructions; (b) this is the intent immediately before the final RT=1 terminal with no splits — its farewell is an FP-4 quoted line in its own `intentInstructions` (check 18); (c) any other auto-chaining intent (v1.17.0) — any remaining spoken line moves to an FP-4 quoted line in `intentInstructions` before the forward. A splitting predecessor never qualifies for (b) — that needs a dedicated pre-IVR farewell intent (structural → Skill 1 patch). Log to 7.3: `announcement intentionally empty on [intent] — FP-3 case (a|b|c)`. | "התוכנית: {{policies}}, חברת הביטוח: {{insurer}}, פרמיה חודשית לאחר הנחה: {{monthlypremiumafterdiscount}}. לתשומת ליבך, ייתכן שהפרמיה תתעדכן בעקבות בדיקה נוספת. האם הפרטים נכונים?" |
| `intentLoadingAnnouncement` | **MANDATORY, non-empty (FP-7 — check 12; Skill 3 check 17 backstops).** Short natural filler spoken while the tool executes, matching the persona's register and grammatical gender. An unconfigured value produces the default "." SAY directive — a verified production trigger for duplicated phrases and dead air. | "מצויין, אני רושמת" / "אין בעיה, שניה רושמת" / "אחלה, רק שומרת את התשובה" |
| `response_success` | **Response success instructions** [JSON field: `response_success` — object shape `{ "instructions": "<text or empty>" }`, v1.5.0 shape change]. Skill 2 prompts the user for any instructional text the runtime should use after RT=3 success (collect-and-continue). Empty string is the most common production shape (`{ "instructions": "" }`). User supplies the inner string; Skill 2 wraps it as the object. | `{ "instructions": "" }` |

**Filler-announcement advisory (v1.13.0, fires during step 3):** an RT=3 `announcement` that contains no `{{…}}` reference, no question mark, and is ≤ ~15 characters (e.g., "תודה.") is almost certainly misplaced acknowledgment. Surface: "Acknowledgment belongs in `intentLoadingAnnouncement`; `announcement` must carry the read-back + the `**Asks next:**` question, or be intentionally empty per FP-3 (API-list read-out / pre-terminal farewell-in-instructions / any auto-chaining intent, v1.17.0). Move it?"

**Question-less announcement rule (v1.17.0, FP-3 turn-yield — fires during step 3, blocking):** an RT=3 or RT=2 `announcement` on an intent whose `**Asks next:**` is `[none]` must be the empty string — regardless of length or content. The announcement is a wait-for-answer directive; on an auto-chaining intent it stalls the call into the silence loop. Move any content the caller must still hear into an FP-4 quoted line in the post-execution `intentInstructions` (immediately before the forward instruction), or into `intentLoadingAnnouncement` if it is pure acknowledgment. Log to 7.3.

#### RT=4 (Dial-Out)

Required language fields:

| Field | Meaning |
|---|---|
| `announcement` | Spoken before initiating the dial |
| `intentLoadingAnnouncement` | Spoken while dialing |

Other RT=4 fields (Phone destination, NEXT_VO_ID, etc.) are structural — declared in section 4 by Skill 1.

#### Step-3 cross-RT iron rules (v1.13.0)

**Max turns sentence authoring (v1.14.0 — fires once per bot, during the first step 3):** Skill 2 authors ONE default `max_turns_sentence` for the bot — a short apology-and-retry line adjusted to the persona's register and **grammatical gender**, modeled on:

- masculine: `"מתנצל אבל נראה שיש לי בעיה מסויימת, אנא נסה שנית מאוחר יותר"`
- feminine: `"מתנצלת אבל נראה שיש לי בעיה מסויימת, אנא נסה שנית מאוחר יותר"`

Show it to the user once (accept/edit), then write it into each intent's section-4 `**Max turns sentence:**` field. **Boundary note:** section 4 is Skill 1's domain; this field is a narrow, explicit Skill 2 write exception (like the §4.5.3 regeneration) because the content is language authoring, not structure. Never ask the user about `max_turns` values themselves — those are autonomous (Skill 1 §3.4.3 / Skill 3 default 5).

**Iron rule (say-once, FP-6 — fires during step 3 + gate, blocking; check 14):** no sentence may be mandated as speech in two places — within this intent's fields (`announcement` vs `intentLoadingAnnouncement` vs a quoted line in `intentInstructions`), or between this intent and a bot-level prompt (persona / opening instructions / openingAnnouncement). Compare normalized text (trim, strip punctuation/niqqud, collapse whitespace). Duplicated speak-obligations are the diagnosed root cause of the bot saying things twice in production. On detection: keep the sentence in exactly one field (announcement for content, loading for acknowledgment) and remove the other.

**Iron rule (routing anchor, FP-9 — fires during steps 3–4, blocking):** wherever an announcement or instruction references another intent, reference it by its section-4 **Description text** (e.g., "forward the call to confirming health declaration") — never by tool name, identifier, or an invented label. The Description is how the voice model identifies tools.

### 4.4 Step 4 — Post-execution `intentInstructions`

This is the second Conversation Routines block per intent. It defines what the bot does **after** this intent has fired and slots have been collected.

**Critical distinction (per Doc 1 §14.3.10, §14.3.12):**

- `validationPrompt` is the Intent-Agent capture mapping (v1.13.0, FP-5) — never spoken
- `intentInstructions` (per-intent) is **post-execution** — delivered to the voice model after the tool completes: what to do next

Skill 2 writes `intentInstructions` (v1.13.0) to cover:

- **Post-answer routing by Description text** (FP-9): `* If the customer approves, forward the call to confirming health declaration.` / `* If the customer disapproves, forward the call to Ending the call by forwarding the call to a hangup layer.`
- **The explicit wait rule — ONLY on intents that ask a question (v1.17.0 scope fix)**: `After asking, stop and wait for the customer's explicit answer. Do not save a value or proceed to the next intent until the customer responds.` This line belongs ONLY where this intent's `announcement` or instructions actually ask the caller something (`**Asks next:**` is a question). **NEVER author it on an auto-chaining intent (`**Asks next:**` [none])** — post-execution the answer is already captured, so the voice model obeys the wait, stalls for a caller turn that never comes, and the silence loop fires (verified live). Auto-chaining intents get the OPPOSITE instruction instead: `Immediately forward the call to <next intent's Description>, without waiting for a response from the customer.`
- **Optional mandated spoken lines via the FP-4 quote convention** — the sanctioned home for speech when the announcement is empty (FP-3 exception) or the step involves several short questions: `Say to the customer : "מצויין, אז קבענו ל {{callback_time}}, נחזור אלייך, שיהיה המשך יום טוב"` — then route.
- Conditional next-intent routing if the intent's outcome varies (RT=2 with conditional success/failure paths)
- Iron rules for what NOT to do post-execution (scope-creep prevention)

**Authoring procedure:**

1. Surface any staged notes for this intent from section 2.4 (the section 7.3 scan).
2. Draft an initial `intentInstructions` block in Conversation Routines style, routing by Description text, including the wait rule; add FP-4 quoted lines only where the announcement doesn't already carry the speech (FP-6 say-once).
3. Show the draft. User confirms or edits.
4. Verify against the iron rules below.

**Iron rules (checks 5, 6, 7, 8, 13, 15 — fire during step 4, blocking):**

| Rule | Source | Catch pattern |
|---|---|---|
| Must be Conversation Routines style | §14.3.2 | Free prose without ALL-CAPS headers, numbered steps, IF/ELSE, or IRON RULES → reformat |
| Must NOT contain pre-execution slot collection logic | §14.3.12 | Sentences like "after collecting X, ensure it's…" or validation rules → relocate to `validationPrompt` |
| Must NOT contain persistent policy that applies call-wide | §14.3.13 | Sentences about privacy, GDPR, retention, broad escalation policy → relocate to `prompts.persona` (raise to user; this is a Skill 1 patch) |
| Must NOT contain bot-level disambiguation that runs before any intent fires | §14.3.11 | Sentences like "first figure out if the user wants X or Y…" → relocate to `prompts.intentInstructions` (bot-level; raise to user; this is a Skill 1 patch) |
| Own-parameters only (v1.13.0, FP-8 — check 13) | FP-8 | Any parameter name mentioned in this intent's `validationPrompt` / `announcement` / `intentInstructions` must exist in THIS intent's slot list. "Set status_shikuf to …" on a gate that doesn't own `status_shikuf` is un-executable at runtime — either the parameter moves to this intent (Skill 1 patch) or the reference is removed. Raise to user; never author around it. |
| Quote convention (v1.13.0, FP-4 — check 15) | FP-4 | Every mandated verbatim spoken line uses `<instruction text> : "<line>"` (colon before the quoted line). Unquoted inline speech or a quoted line with no instruction verb → reformat. |

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
| 1 | `validationPrompt` is non-empty and capture-mapping styled (v1.13.0, FP-5 — short save/capture/set bullets; was "Conversation Routines styled" pre-v1.13) | FP-5 | blocking | during step 2 + gate |
| 2 | `validationPrompt` covers every collectable slot in the intent (one mapping line per slot) | §14.3.2 / FP-5 | blocking | gate |
| 3 | `validationPrompt` contains NO speech content — no ask/say/tell/greet/read-back imperatives, no question addressed to the caller, no turn-taking guards, no routing; quoted strings appear only as VALUES being saved (v1.13.0, FP-5 — replaces the pre-v1.13 "at least one IRON RULE block" check, which mandated the opposite pattern; mirrored by Skill 3 check 16) | FP-5 | blocking | during step 2 + gate |
| 4 | Slot type matches purpose (no STRING for phone, etc.) | §14.3.3 | blocking | during step 1 |
| 5 | `intentInstructions` is non-empty and Conversation Routines styled | §14.3.2 | blocking | during step 4 + gate |
| 6 | `intentInstructions` does not contain slot collection logic | §14.3.12 | blocking | during step 4 |
| 7 | `intentInstructions` does not contain persistent policy | §14.3.13 | blocking | during step 4 |
| 8 | `intentInstructions` does not contain bot-level disambiguation | §14.3.11 | blocking | during step 4 |
| 9 | All Mustache references resolve against section 4.5 (incl. 4.5.5 CustomData keys, v1.13.0) + upstream slots, with directional ordering | §14.3.5 / §15.4 #7 | blocking | during steps 2/3/4 + gate |
| 10 | RT=2 only: `fail_output`, `function_output` (object `{ "default": "..." }`), `response_success` (object `{ "instructions": "..." }`) all populated; `announcement` populated when `**Asks next:**` is a question and **empty string when `**Asks next:**` is `[none]`** (v1.17.0, FP-3 turn-yield) | §14.3.6 / FP-3 | blocking | during step 3 + gate |
| 11 | RT=2 only: API silence behavior fully populated (`silence_sentence`, `silence_ending_sentence`, `silence_instructions`, plus the structural duration and loops from section 4) | §14.3.6 | blocking | during step 3 + gate |
| 12 | RT=3 only: `intentLoadingAnnouncement` is non-empty, not `"."`, and matches the persona's register and grammatical gender (v1.13.0, FP-7) | FP-7 | blocking | during step 3 + gate |
| 13 | Own-parameters only: every parameter name referenced in this intent's `validationPrompt` / `announcement` / `intentInstructions` exists in THIS intent's slot list (v1.13.0, FP-8) | FP-8 | blocking | during steps 2/4 + gate |
| 14 | No duplicate speak-obligation: no normalized sentence is mandated in two of this intent's fields, or in this intent + a bot-level prompt (persona / opening instructions / openingAnnouncement) (v1.13.0, FP-6) | FP-6 | blocking | during steps 3/4 + gate |
| 15 | Quote convention: every mandated verbatim spoken line in `intentInstructions` uses `<instruction text> : "<line>"` (v1.13.0, FP-4) | FP-4 | blocking | during step 4 + gate |
| 16 | Staggered consistency (fires only when the section-4 fields exist, else skipped): the `validationPrompt` maps the answer to `**Captures answer to:**` into this intent's slots, AND the `**Asks next:**` question appears in exactly ONE of {this intent's `announcement`, an FP-4 quoted line in its `intentInstructions`}; when `**Asks next:**` is `[none]`, the `announcement` is the empty string AND the `intentInstructions` carry no wait rule — only the immediate-forward instruction (v1.13.0 FP-2 / v1.17.0 FP-3 turn-yield) | FP-2/FP-3 | blocking | gate |
| 17 | Terminal outcome consistency (fires only when section-4 `**Terminal outcome:**` exists): the `validationPrompt` implements the declared value mode — fixed ⇒ the exact string pinned verbatim with the no-translate + never-ask lines; captured/dynamic ⇒ a matching save/compose instruction for the slot (v1.13.0, FP-5/FP-8) | FP-8 | blocking | during step 2 + gate |
| 18 | RT=1 farewell placement (v1.14.0, FP-8): the terminal has NO authored `announcement`; its `intentLoadingAnnouncement` is a short "good day"-style line; and the ending sentence exists exactly ONCE — as an FP-4 quoted line in the predecessor's (or the dedicated pre-IVR intent's) `intentInstructions`, followed by the immediate-forward / no-wait / no-reveal instruction. When detailing any intent that transitions into an RT=1 terminal, this check fires on THAT intent too (its instructions must carry the farewell + forward). | FP-8 | blocking | during steps 3/4 + gate |

**Behavior on blocking failure at gate:** do NOT mark the intent `[detailed]`. Surface the failure to the user with the specific check number and remediation suggestion. The user fixes the field; Skill 2 re-runs the gate; on pass, status flips.

**Behavior on blocking failure during authoring:** interrupt the step, surface the issue, get user input, retry the step. Do not advance to the next step until resolved.

---

## 7. Section update boundaries

Skill 2 modifies a defined subset of the spec. Crossing these boundaries silently is a category error.

### 7.1 What Skill 2 writes

| Section | Operation | When |
|---|---|---|
| Section 5 entry per intent | Fill content; flip status `[structural]` or `[detailed-revisit]` → `[detailed]` | After self-validation passes |
| Section 4 `**Max turns sentence:**` per intent (v1.14.0) | Write the bot's gender-matched default sentence (narrow explicit exception to the section-4 boundary — language content only) | Once per bot, during the first step 3 |
| Section 4.5.3 (slot inventory) | Regenerate from section 5 state | At end of each batch |
| Section 6.1 (Mustache variable usage) | Append references just written, with location and resolution source | After each intent's step 2/3/4 |
| Section 7.3 (generation log) | Append entry per batch + per invocation | At each batch checkpoint and at invocation end |
| Section 7.4 (open unknowns) | Add or remove `<UNKNOWN: ...>` markers if the batch introduced or resolved any | At end of each batch |
| Section 7.5 (pending work) | Refresh remaining `[structural]` and `[detailed-revisit]` count + list | At end of each batch |

### 7.2 What Skill 2 leaves untouched

- **Section 1** — Bot Identity. Skill 1's domain.
- **Section 2** — Persona Bundle. All five fields. Skill 1's domain. If Skill 2 detects content that should live here (per §14.3.11 or §14.3.13), it raises to the user and recommends Skill 1 patch mode.
- **Section 3** — Caller Silence Behavior. Skill 1's domain.
- **Section 4** — Intent List structural. Slot names, types, required, collection order, transitions, RT, hard-intent flags, `**Sensitive:**`, `**Max turns:**`, `**IsSilenceIntent:**`. Skill 1's domain. If Skill 2 detects a structural problem (e.g., wrong slot type in step 1 check 4, or an unflagged sensitive-collecting intent per the v1.14.0 sensitive backstop), it raises to the user and recommends Skill 1 patch mode. **Sole exception (v1.14.0):** the `**Max turns sentence:**` field — language content Skill 2 writes per §7.1.
- **Section 4.5.1** — Call-context variables. Skill 1's domain.
- **Section 4.5.2** — Environment variables. Skill 1's domain.
- **Section 4.5.4** — API response variables per RT=2 intent. Skill 1's domain.
- **Section 4.5.5** — CustomData keys (v1.13.0). Skill 1's domain. Skill 2 consumes the list as a Mustache allowlist and NEVER adds to it — a missing real key routes to Skill 1 patch mode (FP-11).

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

- Modify spec sections 1, 2, 3, 4, 4.5.1, 4.5.2, 4.5.4, 4.5.5 — Skill 1's domain. If a structural change is needed, raise to user, recommend Skill 1 patch mode, halt the current intent's authoring. *(Sole v1.14.0 exception: the section-4 `**Max turns sentence:**` field — language content per §7.1.)*
- Author an `announcement` on an RT=1 terminal (v1.14.0, FP-8) — the farewell lives in the predecessor's `intentInstructions`; the terminal carries only its short loading announcement (check 18).
- Write speech content into `validationPrompt` — no scripts, questions, greetings, turn-taking guards, or routing (v1.13.0, FP-5). It is a capture mapping only.
- Paste turn-taking / human-rep / disapproval rules into per-intent fields — call-wide rules live once, in persona (FP-6; Skill 1's domain).
- Invent `{{…}}` placeholder names — only keys declared in 4.5.1–4.5.5 (FP-11).
- Mandate the same sentence as speech in two fields (FP-6 — check 14).
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
| 14.3.2 | Free prose instead of Conversation Routines (intentInstructions; validationPrompt is capture-mapping styled since v1.13.0) | Steps 2 + 4 authoring + checks 1 and 5 |
| 14.3.3 | Slot definition missing validation guidance | Step 1 + check 4 + the per-slot constraint lines in the capture mapping (v1.13.0) |
| 14.3.5 | Mustache referencing slots before collection | Section 5 (Mustache resolvability) + check 9 |
| 14.3.6 | RT=2 missing api_silence_behaviour | Step 3 RT=2 branch + checks 10 and 11 |
| 14.3.11 | Bot-level disambiguation in per-intent fields | Step 4 + check 8 |
| 14.3.12 | Slot validation in intentInstructions | Step 4 + check 6 |
| 14.3.13 | Persistent policy in single intent | Step 4 + check 7 |
| FP-5 | Spoken script inside validationPrompt (v1.13.0) | Step 2 doctrine + check 3; Skill 3 check 16 |
| FP-6 | Duplicate speak-obligation (v1.13.0) | Step 3 say-once iron rule + check 14; Skill 3 check 19 |
| FP-7 | Missing RT=3 intentLoadingAnnouncement (v1.13.0) | Step 3 RT=3 table + check 12; Skill 3 check 17 |
| FP-8 | Foreign-parameter reference (v1.13.0) | Step 4 own-parameters rule + check 13; Skill 3 check 18 |
| FP-8 | Farewell inside an RT=1 terminal / missing pre-terminal farewell (v1.14.0) | Step 3 RT=1 hard rule + step 4 predecessor authoring + check 18; Skill 3 check 20 |

Skill 1 owns: §14.3.1 (persona content), §14.3.4 (escalation transitions), §14.3.7 (capabilities ⊆ intents), §14.3.8 (naming), §14.3.9 (channel content placement), §14.3.10 (per-intent logic in persona).

Skill 3 owns: §14.3.5 authoritative cross-reference (§15.4 #7), plus all 7 cross-reference checks.

---

## Appendix B — Conversation Routines style quick reference

Full templates and worked examples in `conversation-routines-style-guide.md`. This appendix is the brief.

**Scope (v1.13.0):** Conversation Routines style applies to `intentInstructions` (per-intent and bot-level). `validationPrompt` uses the FP-5 capture-mapping form instead — short `*` bullets in save/capture/set language (see the minimal example below and style guide §3).

**Required elements (intentInstructions):**

1. **ALL-CAPS section headers** anchor the structure. Examples: `POST-EXECUTION BEHAVIOR`, `OPENING BEHAVIOR`, `IRON RULES`.
2. **Numbered steps** for post-execution actions. Use `1.`, `2.`, `3.`, not bullets.
3. **IF / ELSE branches** for conditional behavior. Indented under the step they condition.
4. **IRON RULE blocks** for non-negotiables. Always at least one, typically at the end of the prompt.

**Forbidden:**

- Free prose paragraphs ("After the user gives their address, just verify it makes sense and then move on.")
- Vague directives ("Be helpful.")
- Channel-specific behavior in `validationPrompt` or `intentInstructions` (belongs in voiceInstructions / chatInstructions, section 2)
- Persistent policy ("We're GDPR-compliant. We never share data.") in `intentInstructions` (belongs in persona, section 2.1)

**Minimal valid `validationPrompt` (v1.13.0, FP-5 — capture mapping only; the asking lives in the previous intent's announcement or this intent's instructions):**

```
* Save the customer's full address (street, house number, city) in the parameter address.
* If any part is missing, leave the parameter unfilled.
```

**Minimal valid post-execution `intentInstructions` (v1.13.0 — wait rule + routing by Description text):**

```
POST-EXECUTION BEHAVIOR
1. After asking, stop and wait for the customer's explicit answer. Do not proceed until the customer responds.
2. If the address was captured, forward the call to Fetching available time slots.
3. If the customer refuses or the address is unusable, forward the call to Transferring the call to a human representative.

IRON RULE: do not discuss pricing or technical issues. Transfer to human for those.
```

---

## Appendix C — RT-specific field cheat sheet

What Skill 2 must populate in step 3 per RT.

| RT | Required fields (Skill 2) | Mustache scope |
|---|---|---|
| 1 | `intentLoadingAnnouncement` only (v1.14.0 — NO `announcement`; the farewell lives on the predecessor per FP-8 / check 18) | Slots from this intent + upstream + 4.5.1 + 4.5.2 |
| 2 | `announcement` (was `apiResponseAnnouncement` pre-v1.5.0), `fail_output`, `function_output` (object `{ "default": "..." }`), `response_success` (object `{ "instructions": "..." }`), `intentLoadingAnnouncement` (v1.5.0: capital-I `IntentLoadingAnnouncement` removed), `silence_sentence`, `silence_ending_sentence`, `silence_instructions` | Above + 4.5.4 dotted paths declared for THIS intent |
| 3 | `announcement` (the read-back + `**Asks next:**` question, or intentionally empty per FP-3), `intentLoadingAnnouncement` (**mandatory, v1.13.0 FP-7**), `response_success` (object `{ "instructions": "..." }`) | Slots from this intent + upstream + 4.5.1 + 4.5.2 + 4.5.4 from upstream RT=2 intents + 4.5.5 CustomData keys |
| 4 | `announcement`, `intentLoadingAnnouncement` | Slots from this intent + upstream + 4.5.1 + 4.5.2 |

Structural fields per RT (declared in section 4 by Skill 1 — not Skill 2's domain):

- RT=1: layer ID
- RT=2: URL, method, headers, body (with Mustache), structural api_silence_behaviour pairing in section 4 + 6.3, response shape declared in 4.5.4
- RT=3: (no structural fields beyond slots)
- RT=4: phone destination, parameter holding phone, NEXT_VO_ID, max dial duration, select-dial option, record (bool)

---

*End of Skill 2 — Intent Detail Author.*
