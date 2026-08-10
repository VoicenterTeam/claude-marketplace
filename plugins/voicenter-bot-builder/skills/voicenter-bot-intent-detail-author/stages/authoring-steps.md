# Skill 2 stage — Per-intent authoring (Steps 1, 2, 4) and Mustache mechanics

*Load when you begin authoring an intent. Carries slot detailing, `validationPrompt` capture
mapping, post-execution `intentInstructions`, the Mustache resolvability mechanics enforced at
write-time, the 4.5.3 / 6.1 regeneration mechanics, and the Conversation Routines style brief.*

*Step 3 (RT-specific configuration) lives in `rt-configuration.md` — SKILL.md §4 dispatches
to each in turn.*

## Table of contents

- [Step 1 — Slot detailing](#41-step-1--slot-detailing)
- [Step 2 — validationPrompt authoring](#42-step-2--validationprompt-authoring)
- [Step 4 — Post-execution intentInstructions](#44-step-4--post-execution-intentinstructions)
- [Mustache resolvability mechanics](#5-mustache-resolvability-mechanics)
- [4.5.3 and 6.1 regeneration mechanics](#73-453-regeneration-mechanic)
- [Conversation Routines style quick reference](#appendix-b--conversation-routines-style-quick-reference)
- [Invocation-completion messages](#92-per-invocation-completion-user-pauses-or-queue-exhausted)

---

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

**Doctrine (v1.13.0, FP-5 — this section was inverted; see `${CLAUDE_PLUGIN_ROOT}/references/field-placement-doctrine.md`):** the `validationPrompt` is consumed ONLY by the **Intent Agent** — the parameter-extraction/validation layer. It is never spoken and never forwarded to the live voice model. Anything written here that was meant to be spoken **will not be spoken** (verified production behavior). Its content is therefore a **capture mapping**: 1–3 short bullet lines, one per outcome or slot, in save/capture/set language. English operational prose is recommended (Compass rule 3 synergy); target-language text appears only as a quoted VALUE being saved.

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

**FORBIDDEN in validationPrompt (blocking — check 3, mirrored by CHK-16):** scripts to speak, questions to ask, greetings, turn-taking guards, routing instructions, ALL-CAPS "GATE" recipes with `Say…`/`Ask…` steps. The asking happens where the voice model can see it — in the **previous** intent's `announcement` (FP-2 staggering) or this intent's post-execution `intentInstructions` (step 4). See `conversation-routines-style-guide.md` §3 for the capture-mapping patterns (C1–C5).

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


---

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


---

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

---

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
