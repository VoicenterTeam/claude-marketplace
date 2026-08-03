# Skill: `voicenter-bot-intent-detail-author`

Fill the per-intent language content of an Agent Spec. Skill 2 in the three-skill pipeline.

> Source: [`plugins/voicenter-bot-builder/skills/voicenter-bot-intent-detail-author/SKILL.md`](../../../plugins/voicenter-bot-builder/skills/voicenter-bot-intent-detail-author/SKILL.md)
> Plugin: [voicenter-bot-builder](../../plugins/voicenter-bot-builder.md) · Pipeline phase: **2 / 3**

---

> **Language.** Reply in the user's language: detect what they write — Hebrew→Hebrew, English→English — and mirror it, switching if they switch mid-conversation. This shapes your prose, your questions, and your `AskUserQuestion` option labels only. It does **not** change the artifacts you produce — identifiers, JSON keys, BCP-47 language codes, API field names, and other data stay exactly as specified.

> **Opening.** Your first message greets bilingually so the user knows both languages are available — e.g. *"נוכל להמשיך בעברית או באנגלית — מה נוח לך? / We can continue in Hebrew or English — whichever you prefer."* Then mirror whatever language the user replies in.

> **One question per turn.** Ask exactly one question per message and wait for the answer before asking the next — never present multiple questions in a single turn. When the answer is a closed set (pick-one / yes-no / pick-from-list), use the `AskUserQuestion` tool rather than plain text; it automatically adds an "Other" free-text escape, so don't hand-roll one. Reserve plain free-text questions for genuinely open inputs (names, descriptions, URLs, numbers). This complements the work-queue batching (§3) and checkpoint mechanic (§8) — those govern how intents are grouped across turns; this governs how many questions you put in one message.

## What it does

Walks every intent in section 5 that is `[structural]` or `[detailed-revisit]` and fills its language-heavy fields:

- Slot descriptions (LLM-facing strings used at slot collection time)
- `validationPrompt` (capture mapping — 1–3 save/capture/set bullets consumed ONLY by the Intent Agent; never spoken scripts — v1.13.0, FP-5)
- Spoken content: `announcement` (the read-back + next question, or the terminal's closing line) and `intentLoadingAnnouncement` (latency filler; mandatory on RT=3) (v1.13.0)
- RT-specific Configuration text (`announcement` (was `apiResponseAnnouncement` pre-v1.5.0), `fail_output`, `function_output` (object `{ "default": "..." }`), `response_success` (object `{ "instructions": "..." }`), silence text, etc.)
- Post-execution `intentInstructions` (Conversation Routines style — routing by Description text, the explicit wait rule, optional FP-4 quoted spoken lines)

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

Skill 2 does not produce JSON. It does not modify the structural skeleton (sections 1, 2, 3, 4, 4.5.1/.2/.4/.5) — that's Skill 1's territory.

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

**Doctrine (v1.13.0, FP-5 — this step was inverted; see `references/field-placement-doctrine.md`):** the `validationPrompt` is consumed ONLY by the **Intent Agent** — the parameter-extraction/validation layer. It is never spoken and never forwarded to the live voice model. Anything written here that was meant to be spoken **will not be spoken** (verified production behavior). Its content is therefore a **capture mapping**: 1–3 short bullet lines, one per outcome or slot, in save/capture/set language. English operational prose is recommended; target-language text appears only as a quoted VALUE being saved.

Golden example (verbatim style):

```
* If the customer confirms, save "true" in the parameter details_confirmed.
* If the customer disapproves, save "false" in the parameter details_confirmed.
```

For an intent carrying a section-4 `**Terminal outcome:**`, the mapping implements the declared **value mode**:

- **fixed** (quoted value in the spec) — pin the exact string (`Set <slot> to exactly this value; do not translate, paraphrase, or alter it: "<the fixed string>"`) plus a never-ask line (`Never ask the customer to choose or confirm this value — it is fixed for this outcome.`)
- **captured** — save the customer's utterance (e.g., `Save the callback time (day and hour) the customer stated in the parameter callback_time.`)
- **dynamic** — an explicit per-call composition instruction for the slot

**FORBIDDEN in `validationPrompt` (blocking — check 3; mirrored by Skill 3 check 16):** scripts to speak, questions to ask, greetings, turn-taking guards, routing instructions, ALL-CAPS "GATE" recipes with `Say…`/`Ask…` steps. The asking happens where the voice model can see it — in the **previous** intent's `announcement` (FP-2 staggering) or this intent's post-execution `intentInstructions` (step 4). The skill ships a `conversation-routines-style-guide.md` reference with the capture-mapping patterns (C1–C5), announcement patterns (§3b), `intentLoadingAnnouncement` patterns (§3c), instruction patterns (I1–I4), and a golden staggered worked example.

The authoring procedure (v1.13.0):

1. Read the intent's slots (step 1) and its section-4 `**Captures answer to:**` — the question whose answer this intent stores was asked one step earlier (or by the opening). The mapping translates *that answer* into *this intent's slots*.
2. Draft the mapping bullets — one line per collectable slot / per outcome of the captured question; the value-mode form for `**Terminal outcome:**` intents.
3. Ask the user about capture edge cases (a hesitant "אולי"/"maybe" — save as false, or leave unfilled? a partial answer — save what was given?).
4. Show the draft. User confirms or edits.
5. Verify before advancing — every collectable slot has exactly one mapping line, every v1-fallback slot's line carries its format/range constraint, NO speech content (no ask/say/tell/greet/read-back imperatives, no question to the caller, no turn-taking guards, no routing), the terminal value mode is implemented, every Mustache reference resolves.

**Sequential collection (retargeted v1.13.0, blocking).** When an intent has two or more caller-collectable slots, the questions must still be asked one at a time — but the ASK sequence no longer lives in `validationPrompt` (the voice model never sees it). Two conditions, both required:

1. The questions are authored where the voice model sees them — in the previous intent's `announcement`/instructions or this intent's `intentInstructions` (step 4) — **one question per turn**, ordered by `CollectionOrder`, each mandated line using the FP-4 quote convention.
2. `validationPrompt` carries exactly one capture line per slot (no bundled "capture everything" line).

Slots populated from an upstream RT=2 response do not count toward the threshold. A single logical slot (e.g. a `full address` covering street + number + city) is one turn. Skill 2 will not mark the intent `[detailed]` until both conditions hold; resolution is logged to section 7.3.

### Step 3 — RT-specific configuration

The Configuration shape and required language fields differ by Response Type.

#### RT=1 (Layer Transfer)

**v1.14.0 hard rule — RT=1 has NO `announcement`. Never author one.** The farewell/closing line is authored on the terminal's PREDECESSOR intent instead (or on a dedicated pre-IVR farewell intent Skill 1 creates when the predecessor splits): an FP-4 quoted line as the last spoken line of that predecessor's post-execution `intentInstructions`, immediately followed by the instruction to forward to this terminal by its Description — without waiting for a caller answer and without telling the caller the call is being transferred to a layer.

**Iron rule (RT=1 wording match, v1.15.1 — blocking):** before picking `intentLoadingAnnouncement` wording — the terminal's ONLY spoken content — determine which RT=1 sub-case this is, from the intent's section-4 Description:

- **Hang-up terminal** (the call ends here — e.g. "ניתוק עקב שקט ממושך"): a short farewell/goodbye filler is correct.
- **Transfer terminal** (the call continues to a queue or human rep — e.g. "העברה לתור טכני"): the filler MUST communicate that a transfer is happening. Farewell/goodbye phrasing here reads to the caller as the call ending, not as being connected onward — this exact mistake shipped on a production bot (a transfer intent's loading announcement carried a farewell line) and is why the rule exists.

| Field | Terminal type | Example (Hebrew) |
|---|---|---|
| `intentLoadingAnnouncement` | Hang-up | "יום טוב!" / "שיהיה המשך יום טוב!" |
| `intentLoadingAnnouncement` | Transfer | "רגע אחד, מעביר אותך." / "מעביר לנציג אנושי." |

Either way it must NOT duplicate the predecessor's farewell (FP-6 say-once — check 14; farewell placement — check 18).

Layer ID is structural (in section 4). Skill 1 captures the real layer number from the MCP; if omitted, Skill 3 defaults it to `0` (root layer) — no `-999` sentinel for layer (v1.12.0).

For a terminal carrying `**Terminal outcome:**`, step 2 already wrote the outcome-value capture mapping (check 17); step 3 confirms the closing line and loading filler only. (v1.13.0)

#### RT=2 (API Call)

**Live API verification (blocking — hard block, no waiver).** Before authoring the RT=2 `announcement`, Skill 2 curls the real endpoint with a user-supplied sample request (real slot values + any auth/secret header values). The intent cannot be marked `[detailed]` unless the call returns HTTP 2xx AND every dotted path declared in 4.5.4 / referenced in the `announcement` is present in the live response JSON. Any failure — non-2xx, unreachable, unknown URL, or a missing path — blocks; there is no override. On success, a redacted verification record (masked request, status, confirmed paths — never raw secrets/PII) is written to spec section 7.6.

| Field | Meaning |
|---|---|
| `announcement` | What the bot says when the API succeeds (v1.5.0 — was `apiResponseAnnouncement` pre-v1.5.0). Almost always uses Mustache references against section 4.5.4 dotted paths. |
| `fail_output` | Graceful default: "I couldn't reach the system right now. Let me transfer you to a human." |
| `function_output` | **Fail-output fallback map** — object shape `{ "default": "<fallback string>" }` (v1.5.0 — was a bare string of LLM guidance). User supplies a single fallback string; Skill 2 wraps it as the object. |
| `response_success` | **Response success instructions** — object shape `{ "instructions": "<text or empty>" }` (v1.5.0). Empty string inner value is the most common production shape. |
| `intentLoadingAnnouncement` | Latency-cover utterance while the API call is in flight. (v1.5.0: capital-I `IntentLoadingAnnouncement` REMOVED — only lowercase form is emitted.) |
| `silence_sentence` / `silence_ending_sentence` / `silence_instructions` | Language for the API silence-handling block. |

Iron rules: every RT=2 intent must have a complete `api_silence_behaviour` (six components: the three language fields `silence_sentence` / `silence_ending_sentence` / `silence_instructions` authored here, plus the three structural fields `silence_duration` / `silence_loops` / **fallback intent** owned by Skill 1 in section 4) and have non-empty `announcement` / `fail_output` / `function_output` / `response_success`. The **fallback intent** is the failover Skill 3 resolves into `api_silence_behaviour.intent` and `apiSilenceRelations[].ApiSilenceIntentID` — if it's missing/unresolved in section 4, check 11 halts and routes back to Skill 1 patch mode (an RT=2 intent without it has no failover when the caller goes silent mid-API). For `function_output`, the object `{ "default": "<fallback>" }` qualifies as non-empty. For `response_success`, the object `{ "instructions": "" }` (empty inner string) qualifies. Per §14.3.6, missing silence behavior produces dead air at runtime when the API takes 8+ seconds.

#### RT=3 (Continue)

Rewritten in v1.13.0 per FP-2/FP-3/FP-7:

| Field | Meaning |
|---|---|
| `announcement` | The REAL spoken content delivered when this intent's tool completes: the read-back with `{{CustomData}}`/slot vars plus **the section-4 `**Asks next:**` question** — the question the NEXT intent's slots will capture (FP-2 staggering). NEVER filler ("תודה.", "קיבלתי.") — acknowledgment belongs in `intentLoadingAnnouncement`. MAY be intentionally empty ONLY when this intent's post-execution `intentInstructions` carry the speech instead (FP-3 exception — e.g., reading an API-response list under reading instructions); the choice is logged to section 7.3. |
| `intentLoadingAnnouncement` | **MANDATORY, non-empty (FP-7 — check 12; Skill 3 check 17 backstops).** Short natural filler spoken while the tool executes, matching the persona's register and grammatical gender (e.g., "מצויין, אני רושמת"). An unconfigured value produces the default "." SAY directive — a verified production trigger for duplicated phrases and dead air. |
| `response_success` | **Response success instructions** — object shape `{ "instructions": "<text or empty>" }` (v1.5.0). Empty string inner value is the most common production shape (`{ "instructions": "" }`). |

**Filler-announcement advisory (v1.13.0):** an RT=3 `announcement` with no `{{…}}` reference, no question mark, and ≤ ~15 characters (e.g., "תודה.") is almost certainly misplaced acknowledgment — Skill 2 surfaces it and offers to move it to `intentLoadingAnnouncement`.

#### RT=4 (Dial-Out)

| Field | Meaning |
|---|---|
| `announcement` | Spoken before initiating the dial |
| `intentLoadingAnnouncement` | Spoken while dialing |
| `intentInstructions` | Optional post-execution string |
| `response_success.instructions` | Runtime guidance for the success path |

Other RT=4 fields (Phone1/2/3 / parameter_phone / NEXT_VO_ID / MAX_DIAL_DURATION / Record / selectdial_option) are structural — declared in section 4 by Skill 1.

#### Step-3 cross-RT iron rules (v1.13.0)

- **Say-once (FP-6 — check 14, blocking):** no sentence may be mandated as speech in two places — within this intent's fields (`announcement` vs `intentLoadingAnnouncement` vs a quoted line in `intentInstructions`), or between this intent and a bot-level prompt (persona / opening instructions / openingAnnouncement). Compared on normalized text (trim, strip punctuation/niqqud, collapse whitespace). Duplicated speak-obligations are the diagnosed root cause of the bot saying things twice in production. Keep the sentence in exactly one field — announcement for content, loading for acknowledgment.
- **Routing anchor (FP-9, blocking):** wherever an announcement or instruction references another intent, reference it by its section-4 **Description text** (e.g., "forward the call to confirming health declaration") — never by tool name, identifier, or an invented label. The Description is how the voice model identifies tools.

### Step 4 — Post-execution `intentInstructions`

The second Conversation Routines block per intent. Defines what the bot does **after** this intent has fired and slots have been collected.

Critical distinction (v1.13.0):

- `validationPrompt` — the Intent-Agent capture mapping (FP-5) — never spoken
- `intentInstructions` (per-intent) — post-execution, delivered to the voice model after the tool completes: what to do next

Skill 2 writes `intentInstructions` (v1.13.0) to cover:

- **Post-answer routing by Description text** (FP-9): `* If the customer approves, forward the call to confirming health declaration.`
- **The explicit wait rule**: `After asking, stop and wait for the customer's explicit answer. Do not save a value or proceed to the next intent until the customer responds.`
- **Optional mandated spoken lines via the FP-4 quote convention** (`<instruction text> : "<verbatim line>"`) — the sanctioned home for speech when the announcement is empty (FP-3 exception) or the step involves several short questions
- Conditional next-intent routing when the outcome varies, plus IRON RULES for scope-creep prevention

Iron rules during drafting:

| Rule | Catch pattern | Handling |
|---|---|---|
| Must be Conversation Routines style | Free prose without ALL-CAPS / IRON RULES | Reformat |
| Must NOT contain pre-execution slot collection logic | "after collecting X, ensure it's…" | Silently relocate to `validationPrompt`; inform user |
| Must NOT contain persistent policy applying call-wide | "we never store payment details…" | Raise to user — destination is `prompts.persona` (Skill 1 patch territory) |
| Must NOT contain bot-level disambiguation | "first figure out if the user wants X or Y…" | Raise to user — destination is bot-level `prompts.intentInstructions` (Skill 1 patch territory) |
| Own-parameters only (v1.13.0, FP-8 — check 13) | A parameter name in `validationPrompt` / `announcement` / `intentInstructions` that doesn't exist in THIS intent's slot list ("Set status_shikuf to …" on a gate that doesn't own it) — un-executable at runtime | Raise to user — either the parameter moves to this intent (Skill 1 patch) or the reference is removed; never author around it |
| Quote convention (v1.13.0, FP-4 — check 15) | A mandated verbatim spoken line not in the `<instruction text> : "<line>"` form (unquoted inline speech, or a quoted line with no instruction verb) | Reformat |

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

After all four steps complete for an intent, Skill 2 runs the self-validation checklist **before** flipping the status to `[detailed]`. As of v1.13.0 the checklist has 17 checks, all blocking (was 11):

| # | Check |
|---|---|
| 1 | `validationPrompt` is non-empty and capture-mapping styled (v1.13.0, FP-5 — short save/capture/set bullets; was "Conversation Routines styled" pre-v1.13) |
| 2 | `validationPrompt` covers every collectable slot in the intent (one mapping line per slot) |
| 3 | `validationPrompt` contains NO speech content — no ask/say/tell/greet/read-back imperatives, no question addressed to the caller, no turn-taking guards, no routing; quoted strings appear only as VALUES being saved (v1.13.0, FP-5 — replaces the pre-v1.13 "at least one IRON RULE block" check, which mandated the opposite pattern; mirrored by Skill 3 check 16) |
| 4 | Slot type matches purpose (no STRING for phone, etc.) |
| 5 | `intentInstructions` is non-empty and Conversation Routines styled |
| 6 | `intentInstructions` does not contain slot collection logic |
| 7 | `intentInstructions` does not contain persistent policy |
| 8 | `intentInstructions` does not contain bot-level disambiguation |
| 9 | All Mustache references resolve against section 4.5 (incl. 4.5.5 CustomData keys, v1.13.0) + upstream slots, with directional ordering |
| 10 | RT=2 only: `announcement`, `fail_output`, `function_output` (object `{ "default": "..." }`), `response_success` (object `{ "instructions": "..." }`) all populated |
| 11 | RT=2 only: API silence behavior fully populated (three language fields + the structural duration/loops/fallback intent from section 4) |
| 12 | RT=3 only: `intentLoadingAnnouncement` is non-empty, not `"."`, and matches the persona's register and grammatical gender (v1.13.0, FP-7) |
| 13 | Own-parameters only: every parameter name referenced in this intent's `validationPrompt` / `announcement` / `intentInstructions` exists in THIS intent's slot list (v1.13.0, FP-8) |
| 14 | No duplicate speak-obligation: no normalized sentence is mandated in two of this intent's fields, or in this intent + a bot-level prompt (v1.13.0, FP-6) |
| 15 | Quote convention: every mandated verbatim spoken line in `intentInstructions` uses `<instruction text> : "<line>"` (v1.13.0, FP-4) |
| 16 | Staggered consistency (fires only when the section-4 fields exist, else skipped): the `validationPrompt` maps the answer to `**Captures answer to:**` into this intent's slots, AND the `**Asks next:**` question appears in exactly ONE of {this intent's `announcement`, an FP-4 quoted line in its `intentInstructions`} (v1.13.0, FP-2/FP-3) |
| 17 | Terminal outcome consistency (fires only when section-4 `**Terminal outcome:**` exists): the `validationPrompt` implements the declared value mode — fixed ⇒ the exact string pinned verbatim with the no-translate + never-ask lines; captured/dynamic ⇒ a matching save/compose instruction (v1.13.0, FP-5/FP-8) |

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

- Modify section 1, 2, 3, 4, or 4.5.1/.2/.4/.5 — those are Skill 1's territory
- Write speech content into `validationPrompt` — no scripts, questions, greetings, turn-taking guards, or routing (v1.13.0, FP-5); it is a capture mapping only
- Paste turn-taking / human-rep / disapproval rules into per-intent fields — call-wide rules live once, in persona (FP-6; Skill 1's domain) (v1.13.0)
- Invent `{{…}}` placeholder names — only keys declared in 4.5.1–4.5.5 (FP-11) (v1.13.0)
- Mandate the same sentence as speech in two fields (FP-6 — check 14) (v1.13.0)
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
- **Required-reading row for RT field shapes:** the RT=1/2/3/4 Configuration field shapes at emission are cited from Skill 3 SKILL.md §4.4 (v1.13.0 — the retired external schema-audit doc reference was removed; §4.4 is v1.5.0 production-aligned).

---

## v1.13.0 changes

The v1.13.0 release inverts the `validationPrompt` doctrine and introduces the field-placement doctrine reference (`plugins/voicenter-bot-builder/references/field-placement-doctrine.md`, FP-1…FP-13 — new required reading; Skill 2 owns FP-3 script home, FP-4 quote convention, FP-5 capture-mapping validationPrompt, FP-7 RT=3 loading announcement, and the per-intent half of FP-6 say-once):

- **`validationPrompt` is a capture mapping (FP-5).** It is consumed ONLY by the Intent Agent — never spoken, never seen by the voice model. Step 2 was rewritten: 1–3 save/capture/set bullets, one per outcome or slot; three value modes for terminal outcome slots (fixed pinned string / captured utterance / dynamic per-call). Speech content in `validationPrompt` is FORBIDDEN — check 3 was replaced (the old "at least one IRON RULE block" check mandated the opposite pattern).
- **Sequential collection retargeted.** The ask-sequence lives in the previous intent's `announcement` or this intent's `intentInstructions` (one question per turn, FP-4 quoted); `validationPrompt` keeps one capture line per slot.
- **Compass rule 8 retargeted.** `validationPrompt` is exempt from TTS-safe formatting (never vocalized; its canonical form legitimately uses `*` bullets); the detections run on `announcement` / `intentLoadingAnnouncement` / `fail_output` / `function_output` / quoted instruction lines instead.
- **RT=3 configuration rewritten (FP-2/FP-3/FP-7).** `announcement` = the read-back with `{{CustomData}}` vars + the section-4 `**Asks next:**` question; never filler ("תודה."); may be intentionally empty when `intentInstructions` carry the speech (FP-3 exception, logged to 7.3). `intentLoadingAnnouncement` is now MANDATORY and non-empty (FP-7 — check 12). A filler-announcement advisory catches misplaced acknowledgments.
- **RT=1:** `announcement` carries the outcome-specific FULL closing line; `intentLoadingAnnouncement` must not duplicate the farewell.
- **New cross-RT iron rules:** say-once (FP-6 — check 14) and routing by section-4 Description text (FP-9).
- **Step 4:** instructions route by Description text, include the explicit wait rule, and may carry FP-4 quoted spoken lines (`<instruction> : "<verbatim line>"`); new blocking rules: own-parameters only (FP-8 — check 13) and quote convention (FP-4 — check 15).
- **Checklist grew from 11 to 17 checks, all blocking:** amended 1 (capture-mapping styled) and 2 (every collectable slot); replaced 3 (no speech); new 12 (RT=3 loading non-empty + gender-consistent), 13 (own-parameters), 14 (no duplicate speak-obligation), 15 (quote convention), 16 (staggered consistency — skipped when the section-4 spec fields are absent), 17 (terminal outcome consistency per value mode).
- **Style guide rewritten:** patterns V1–V5 became capture-mapping patterns C1–C5 (boolean gate / free-text / terminal outcome in 3 modes / ENUM multi-choice / multi-slot); new §3b announcement patterns and §3c `intentLoadingAnnouncement` patterns; I1–I4 updated (wait rule, Description routing, FP-4); a golden staggered worked example (`verify_plan_and_premium` capturing `details_confirmed`); new pitfalls 5–8 (script-in-validationPrompt, foreign parameter, duplicated farewell, "תודה." filler); rewritten placement checklist; TTS addendum scope change.

---

## voice-agent-llm v1.0.3+ runtime notes

**Empty `announcement` fallback.** If `announcement` ships empty in the emitted config, the voice-agent service substitutes the sentinel `[START THE CONVERSATION]` as an LLM instruction (bot opens from persona; the literal string is **not** spoken aloud). **Check 10 still requires `announcement` populated** — the fallback is a service-side safety net, not a license to ship empty.

**TTS sanitization.** The service now sanitizes voice-active text before TTS, so unintended Markdown is no longer spoken literally. The existing Compass rule 8 authoring rule still applies — write plain conversational prose in the spoken fields: `announcement`, `intentLoadingAnnouncement`, `fail_output`, `function_output`, and the quoted spoken lines of post-execution `intentInstructions`. (`validationPrompt` is exempt — never vocalized, v1.13.0 FP-5.) The sanitizer is a belt-and-suspenders safeguard, not a substitute for clean authoring.

---

## Common pitfalls

- **Spoken script inside `validationPrompt` (v1.13.0, FP-5 — the #1 production failure).** Skill 2 blocks (check 3; Skill 3 check 16 mirrors). The Intent Agent is the only consumer — the caller never hears the read-back or the question; the gate silently doesn't happen. Script + question move to `announcement`; turn-taking guards move to persona (once, FP-6); `validationPrompt` keeps only the capture mapping.
- **Foreign parameter reference (v1.13.0, FP-8).** "Set status_x to …" on an intent that doesn't own `status_x` is un-executable — Skill 2 blocks (check 13). The value belongs to the owning terminal's own `validationPrompt`; the gate just routes.
- **Duplicated farewell obligations (v1.13.0, FP-6).** A closing line spread across multiple fields or chained terminals makes the bot say goodbye twice — Skill 2 blocks (check 14). One terminal per outcome; the full closing line in that terminal's `announcement`; a short goodbye in `intentLoadingAnnouncement` only if the announcement doesn't already say it.
- **"תודה." filler announcement (v1.13.0, FP-3).** Skill 2 surfaces the filler advisory. Acknowledgment belongs in `intentLoadingAnnouncement`; `announcement` carries the read-back + the `**Asks next:**` question, or is intentionally empty per FP-3.
- **Mustache reference to a downstream slot.** Skill 2 blocks. Either fix the reference or pause and run Skill 1 patch mode to fix the flow graph.
- **`fail_output` left empty on RT=2.** Skill 2 blocks. The graceful default ("I couldn't reach the system right now…") is acceptable; rewrite is up to the user.
- **Persistent policy snippet appearing in a per-intent `intentInstructions`.** Skill 2 raises and recommends moving to `prompts.persona` via Skill 1 patch.

---

## Compass doctrine integration

The bot-builder plugin includes a shared doctrine reference at `plugins/voicenter-bot-builder/references/voice-prompt-doctrine.md`, derived from the Gemini Live 3.1 voice agent engineering guideline. Skill 2 owns the primary enforcement of four per-intent rules from that catalog:

- **Rule 8 — TTS-safe formatting (spoken fields only, v1.13.0).** Blocking on markdown bullets/headers/URLs; advisory on raw long digit runs without a "spell digit-by-digit" instruction nearby. Fires during steps 3–4 on every spoken field — `announcement`, `intentLoadingAnnouncement`, `fail_output`, `function_output`, and the FP-4 quoted lines inside post-execution `intentInstructions`. `validationPrompt` is EXEMPT — it is never vocalized (FP-5), and its canonical capture-mapping form legitimately uses `*` bullets.
- **Rule 9 — Date math in prompt.** Advisory. Detects "not future", "year ≥ 1900", "today/tomorrow without {{TimeNow}}" patterns. Recommends pre-rendered Mustache variables via Skill 1 patch mode.
- **Rule 10 — Few-shot example cap.** Advisory when a single `validationPrompt` contains more than 2 transcript-style example pairs. Hebrew/non-English bots get a harsher message reflecting the ~3× per-example token cost.
- **Rule 11 — Hebrew-utterance isolation.** Blocking. Forbids inline RTL Hebrew/Arabic/CJK content mixed with LTR English on the same line. Required on its own line or wrapped in quotes. Applies to every field Skill 2 authors, including `validationPrompt`. The FP-4 quote convention satisfies it by construction.

A second shared reference, `plugins/voicenter-bot-builder/references/field-placement-doctrine.md` (v1.13.0, FP-1…FP-13), is the authority on which prompt field carries which kind of content. Skill 2 owns FP-3 (script home), FP-4 (quote convention), FP-5 (capture-mapping validationPrompt), FP-7 (RT=3 loading announcement), and the per-intent half of FP-6 (say-once); Skill 3 verifies via cross-reference checks 16–22.

See the reference docs for detection methods and fix recipes.

---

## Related skills

- [voicenter-bot-spec-designer](../voicenter-bot-spec-designer/README.md) — Skill 1; provides the structural skeleton Skill 2 fills.
- [voicenter-bot-json-assembler](../voicenter-bot-json-assembler/README.md) — Skill 3; runs after every intent is `[detailed]` to emit the wire-format JSON.
