# Conversation Routines Style Guide

**Purpose:** concrete templates and worked examples for the fields Skill 2 authors — the capture-mapping `validationPrompt`, the spoken `announcement` / `intentLoadingAnnouncement`, and post-execution `intentInstructions`. Supports Skill 2 (Intent Detail Author) — Skill 2 references this file during steps 2–4.

**Scope (v1.13.0):** Conversation Routines style (headers / numbered steps / IF-ELSE / IRON RULES) applies to `intentInstructions`. `validationPrompt` uses the FP-5 **capture-mapping form** — it is consumed only by the Intent Agent and is never spoken; scripts written there never reach the caller. Bot-level `prompts.intentInstructions` (Opening Behavior in section 2.4) is Conversation-Routines styled but is Skill 1's domain. See `../../references/field-placement-doctrine.md` for the full placement doctrine.

**Source:** Doc 1 §14.3.2 defines the CR style; field-placement doctrine v1.13.0 defines what goes where. This file expands with concrete patterns.

---

## 1. Required elements (intentInstructions)

| Element | Form | Example |
|---|---|---|
| ALL-CAPS section headers | Bare line, no markdown | `POST-EXECUTION BEHAVIOR` |
| Numbered steps | `1.`, `2.`, `3.` (not bullets) | `1. After asking, stop and wait for the customer's explicit answer.` |
| IF / ELSE branches | Inline or indented under their step | `IF customer refuses: forward the call to Transferring the call to a human representative.` |
| IRON RULE blocks | At least one per prompt | `IRON RULE: do NOT discuss pricing.` |
| FP-4 quote convention for mandated speech (v1.13.0) | `<instruction text> : "<verbatim line>"` | `Say to the customer : "מצויין, אז קבענו ל {{callback_time}}"` |

## 2. Forbidden patterns

| Pattern | Why bad | Where it belongs instead |
|---|---|---|
| Spoken script / question / greeting inside `validationPrompt` (v1.13.0, FP-5) | The Intent Agent is the only consumer — the caller NEVER hears it | `announcement` (or an FP-4 quoted line in `intentInstructions`) |
| Turn-taking guard inside `validationPrompt` or repeated per intent (v1.13.0, FP-6) | Wrong layer (never seen by the voice model) + duplication bloat | `prompts.persona` — stated once |
| Free prose ("Be helpful and friendly throughout.") | No anchors; LLM behavior drifts | Nowhere — delete or restructure |
| Vague directives ("Make it clear what we offer.") | Unverifiable | Persona, with concrete scope language |
| Channel-specific behavior ("Speak slowly and pause.") | Misplacement per §14.3.9 | `prompts.voiceInstructions` (section 2.2) |
| Persistent policy ("We're GDPR-compliant.") | Misplacement per §14.3.13 | `prompts.persona` (section 2.1) |
| Slot validation logic in `intentInstructions` | Misplacement per §14.3.12 — runs after slots are already collected | `validationPrompt` (as capture-constraint lines) |
| Pre-intent disambiguation in per-intent `intentInstructions` | Misplacement per §14.3.11 — runs after the intent has already fired | `prompts.intentInstructions` (bot-level, section 2.4) |
| Referencing another intent's parameter ("Set status_x to …") (v1.13.0, FP-8) | Un-executable — an intent can only set its own slots | The parameter's owning terminal |
| Routing by tool name / identifier (v1.13.0, FP-9) | The voice model identifies tools by their Description text | Route by section-4 Description text |

---

## 3. `validationPrompt` capture-mapping patterns (v1.13.0)

The `validationPrompt` lives in `IntentConfig.prompts.validationPrompt`. It is read ONLY by the Intent Agent — its sole job is mapping the caller's answer (to the question asked one step earlier, per FP-2 staggering) into this intent's parameters. Short `*` bullets, save/capture/set language, English operational prose, target-language text only as quoted saved VALUES.

### Pattern C1 — Boolean gate (yes/no confirmation)

Use when: the intent captures a confirm/disapprove answer into a BOOLEAN slot. (Golden-reference verbatim style.)

```
* If the customer confirms, save "true" in the parameter details_confirmed.

* If the customer disapproves, save "false" in the parameter details_confirmed.
```

### Pattern C2 — Free-text capture (callback time, name, address)

Use when: the intent captures the caller's stated value into a STRING slot. Interpretation machinery (relative dates, "עוד שעה") does NOT go here — it lives in the bot-level opening instructions per FP-12 (Skill 1's domain).

```
Save the callback time (day and time - hour) in the parameter callback_time.
```

```
* Save the customer's full address (street, house number, city) in the parameter address.
* If any part is missing, leave the parameter unfilled.
```

### Pattern C3 — Terminal outcome slot (three value modes)

Use when: the intent is an RT=1 terminal carrying a section-4 `**Terminal outcome:**`. Pick the sub-variant matching the declared value mode.

**C3a — fixed** (the spec quotes an exact string):

```
1. Set shikuf_status to exactly this value; do not translate, paraphrase, or alter it: "הלקוח לא אישר משהו"
2. Never ask the customer to choose or confirm this value — it is fixed for this outcome.
```

**C3b — captured** (save what the customer said):

```
Save the customer's stated reason for declining, in the customer's own words, in the parameter decline_reason.
```

**C3c — dynamic** (composed per call by instruction):

```
Compose a one-sentence Hebrew summary of the call outcome (which stages were confirmed, where it stopped) and save it in the parameter call_summary. Do not ask the customer anything to produce it.
```

### Pattern C4 — ENUM multi-choice capture

Use when: slot is `ParameterTypeId 19` (ENUM) with an `OptionList` — the slot selects among MULTIPLE fixed values (FP-13). The presenting of options happens in the previous announcement; here only the mapping.

```
* Map the customer's answer to one of the OptionList values: installation / repair / cancellation.
* Save the matched Value in the parameter service_type.
* If the answer clearly matches none of the options, leave the parameter unfilled.
```

### Pattern C5 — Multi-slot capture

Use when: the intent owns ≥2 collectable slots. One capture line per slot — and note the box below.

```
* Save the customer's full name in the parameter full_name.
* Save the customer's phone number (digits only, exactly 10 digits; strip dashes and spaces) in the parameter phone_number. If fewer than 10 digits, leave unfilled.
```

> **The ASKING lives elsewhere.** The questions for these slots are asked one per turn where the voice model can see them — in the previous intent's `announcement` or this intent's `intentInstructions` (FP-4 quoted lines), ordered by `CollectionOrder`. Never write "Ask for…" here (sequential-collection iron rule, Skill 2 §4.2).

Format/range constraints for v1-fallback slots (phone/date/email stored as STRING) ride on the slot's capture line, as in C5's phone example — constraint language ("save only if…", "strip silently", "leave unfilled if…"), never dialogue.

---

## 3b. `announcement` patterns (v1.13.0)

`announcement` lives in `IntentResponces.Configuration.announcement` — the deterministic speech channel, spoken when the intent's tool completes. If a sentence is compliance-critical, it belongs here, verbatim.

### Read-back + next question (RT=3 gate — the FP-2 staggered core)

The announcement delivers this stage's scripted content and ends with the question the NEXT intent captures (`**Asks next:**`):

```
התוכנית: {{policies}}, חברת הביטוח: {{insurer}}, פרמיה חודשית לאחר הנחה: {{monthlypremiumafterdiscount}}. לתשומת ליבך, ייתכן שהפרמיה תתעדכן בעקבות בדיקה נוספת של חברת הביטוח. האם הפרטים נכונים?
```

Rules: real `{{CustomData}}`/slot vars from sections 4.5.5/4.5.3 only (FP-11); ends with the question; NO filler ("תודה.") — acknowledgment goes to `intentLoadingAnnouncement`.

### Pre-terminal farewell (v1.14.0, FP-8)

**The RT=1 terminal itself has NO `announcement`.** The outcome-specific farewell, in full and exactly once (FP-6), is an FP-4 quoted line in the **predecessor's** `intentInstructions` — the last spoken line before the forward, with the no-wait / no-reveal instruction (pattern I3 is the canonical shape):

```
POST-EXECUTION BEHAVIOR
1. Say to the customer : "מתנצלת, אבל בגלל שלא אישרת את אחד מהפרטים, עליי להעביר את זה לנציג אנושי. נציג יחזור אליך בהקדם. יום טוב."
2. Immediately forward the call to Ending the call by transferring to a human representative — do not wait for an answer, and do not tell the customer the call is being transferred to a layer.
```

The terminal keeps only its short loading goodbye ("יום טוב!"). If the predecessor splits to several intents, the farewell gets its own dedicated pre-IVR intent (FP-3 corollary — structural, Skill 1).

### Intentionally empty announcement (FP-3 — exactly two cases, v1.14.0)

**(a) API-list read-out:** the speech is carried by the intent's `intentInstructions` reading instructions — e.g., reading an API-response list, where a fixed transition sentence would get in the way:

```
announcement: ""
intentInstructions:
  POST-EXECUTION BEHAVIOR
  1. Read each option in {{available_slots}} to the customer, one at a time, pausing between items.
  2. Ask the customer : "איזה מהמועדים מתאים לך ?"
  3. After asking, stop and wait for the customer's explicit answer.
```

**(b) Pre-terminal farewell-in-instructions:** the intent immediately before the final RT=1 terminal, with **no splits to other intents** — its farewell lives in its own `intentInstructions` per the pattern above.

Log to spec 7.3: `announcement intentionally empty on [intent] — FP-3 case (a|b)`. No other empty-announcement case is allowed.

---

## 3c. `intentLoadingAnnouncement` patterns (v1.13.0, FP-7)

Spoken while the tool executes. **Mandatory on every RT=3 intent** — unset produces the default "." SAY directive (duplicated phrases / dead air in production). Short, natural, matching the persona's register and grammatical gender (female voice ⇒ "רושמת", not "רושם").

| Context | Example |
|---|---|
| Gate acknowledgment (female persona) | "מצויין, אני רושמת" / "אין בעיה, שניה רושמת" / "אחלה, רק שומרת את התשובה" |
| Terminal goodbye (RT=1) | "יום טוב!" / "מעביר לנציג אנושי." — the terminal's ONLY utterance (v1.14.0); NEVER the full farewell, which lives in the predecessor's instructions (FP-8; checks 14/18) |
| API wait (RT=2) | "רק רגע, אני בודקת במערכת" |

Never put full content sentences here, and never duplicate a sentence that exists in `announcement`.

**`max_turns_sentence` (v1.14.0):** authored once per bot in the same register/gender discipline — masculine `"מתנצל אבל נראה שיש לי בעיה מסויימת, אנא נסה שנית מאוחר יותר"`, feminine `"מתנצלת אבל נראה שיש לי בעיה מסויימת, אנא נסה שנית מאוחר יותר"`.

---

## 4. Post-execution `intentInstructions` patterns

`intentInstructions` lives in `IntentResponces.Configuration.intentInstructions`. Post-execution: delivered to the voice model after the tool completes — routing, the wait rule, and (when needed) FP-4 quoted spoken lines.

**FP-4 quote convention callout (v1.13.0):** every spoken line mandated in these instructions uses `<instruction text> : "<verbatim line>"` — e.g., `Say to the customer : "מצויין, אז קבענו ל {{callback_time}}, נחזור אלייך, שיהיה המשך יום טוב"`. The quoting doubles as Compass rule 11 RTL isolation. Route to other intents by their section-4 **Description text**, never by tool name (FP-9).

### Pattern I1 — Minimal single-path

Use when: the intent has one outcome and one next step.

```
POST-EXECUTION BEHAVIOR
1. After asking, stop and wait for the customer's explicit answer. Do not save a value or proceed until the customer responds.
2. If the customer answered, forward the call to Fetching available time slots.

IRON RULE: do NOT discuss pricing or technical issues. Forward to Transferring the call to a human representative for those.
```

### Pattern I2 — Branching on the captured answer (the FP-2 gate pattern; golden-reference shape)

Use when: the announcement asked a yes/no question and the routing branches on the answer.

```
* Act according to the following instructions based on the caller's response :

* After reading the details and asking the question, stop and wait for the customer's explicit answer. Do not save a value or proceed to the next intent until the customer responds.

  * If the customer approves, forward the call to confirming health declaration.

  * If the customer disapproves, forward the call to Ending the call by forwarding the call to a hangup layer.
```

### Pattern I3 — Mandated spoken line + immediate route (FP-4)

Use when: a short closing/confirmation line must be spoken and then the call routes on — typical when the announcement is empty or the line depends on a just-captured slot.

```
**Important -** Say to the customer : "מצויין, אז קבענו ל {{callback_time}}, נחזור אלייך, שיהיה המשך יום טוב" And immediately forward the call to Ending the call by forwarding the call to a hangup layer.
```

### Pattern I4 — RT=2 with conditional API silence escalation

Use when: an RT=2 intent has a non-trivial API silence fallback path that should be reflected in post-execution instructions (e.g., the API silence escalates to a different intent than the success path).

```
POST-EXECUTION BEHAVIOR
1. IF the API responded successfully within the silence window:
   - Read the response details from {{response.summary}}.
   - Forward the call to Confirming the appointment details.
2. IF the API silence_ending_sentence fired (the API took too long):
   - The silence handler already announced the delay.
   - Forward the call to Transferring the call to a human representative.

IRON RULE: do NOT retry the API in this intent. The silence behavior owns retries; this intent is post-call.
```

---

## 5. Worked example — complete staggered intent (v1.13.0, golden-reference shape)

Bringing it together: an RT=3 gate (`verify_plan_and_premium`) in a staggered verification flow. Section 4 declares: **Description:** `Verification of plan and premia`; **Captures answer to:** the identity read-back question asked by the opening instructions ("האם הפרטים נכונים?"); **Asks next:** the plan/premium confirmation question.

### Slot definition (from step 1)

```
Slot: details_confirmed
- Description: אישור הלקוח שפרטי הזיהוי שלו ושל המבוטחים הנוספים נכונים. כן/לא.
- Type: BOOLEAN (ParameterTypeId 16)
- Required: true
- Collection order: 1
```

Note the deliberate offset: the slot captures the IDENTITY question (asked one step earlier, by the opening), while this intent's announcement asks the PLAN question — that's FP-2 staggering, not a naming mistake.

### `validationPrompt` (from step 2 — capture mapping only, pattern C1)

```
* If the customer confirms, save "true" in the parameter details_confirmed.

* If the customer disapproves, save "false" in the parameter details_confirmed.
```

### `announcement` (from step 3 — read-back + the `**Asks next:**` question, §3b)

```
התוכנית: {{policies}}, חברת הביטוח: {{insurer}}, פרמיה חודשית לאחר הנחה: {{monthlypremiumafterdiscount}}. לתשומת ליבך, ייתכן שהפרמיה תתעדכן בעקבות בדיקה נוספת של חברת הביטוח. האם הפרטים נכונים?
```

### `intentLoadingAnnouncement` (from step 3 — mandatory on RT=3, §3c)

```
מצויין, אני רושמת
```

### Post-execution `intentInstructions` (from step 4 — pattern I2)

```
* Act according to the following instructions based on the caller's response :

* After reading the plan and premium details and asking the question, stop and wait for the customer's explicit answer. Do not save a value or proceed to the next intent until the customer responds.

  * If the customer approves, forward the call to confirming health declaration.

  * If the customer disapproves, forward the call to Ending the call by forwarding the call to a hangup layer.
```

---

## 6. Common authoring pitfalls and fixes

### Pitfall 1 — "Just be helpful" prose creeps in

Bad — in `intentInstructions`:

```
POST-EXECUTION BEHAVIOR
1. Be helpful and patient if the customer needs to think.
2. Move on when ready.
```

Why bad: step 1 is unverifiable prose. The LLM doesn't know what "helpful and patient" means concretely.

Fix: replace with a concrete behavior or remove.

```
POST-EXECUTION BEHAVIOR
1. After asking, stop and wait for the customer's explicit answer. IF the customer pauses or asks to think: wait without repeating the question.
2. If the customer answered, forward the call to Fetching available time slots.
```

### Pitfall 2 — Validation logic ends up post-execution

Bad — in `intentInstructions`:

```
POST-EXECUTION BEHAVIOR
1. After collecting the phone, ensure it's exactly 10 digits.
2. Strip dashes silently.
3. Confirm.
```

Why bad: by the time `intentInstructions` runs, the phone is already collected. The validation rules never fire.

Fix: the constraints become capture-constraint lines in `validationPrompt` (pattern C5); the instructions keep only genuinely-post-execution behavior.

`validationPrompt`:
```
* Save the customer's phone number (digits only, exactly 10 digits; strip dashes and spaces silently) in the parameter phone_number.
* If fewer than 10 digits or it contains letters, leave the parameter unfilled.
```

`intentInstructions`:
```
POST-EXECUTION BEHAVIOR
1. After asking, stop and wait for the customer's explicit answer.
2. If the phone number was captured, forward the call to the next step by its Description text.
```

### Pitfall 3 — Bot-level routing logic in per-intent fields

Bad — in `validate_customer_address.intentInstructions`:

```
POST-EXECUTION BEHAVIOR
1. When the caller first reaches us, figure out if they want to schedule or reschedule.
2. If schedule, validate the address.
3. If reschedule, transfer to reschedule_existing.
```

Why bad: by the time `validate_customer_address` is firing, disambiguation has already happened — that's why this intent fired. This text is dead code.

Fix: this content belongs in `prompts.intentInstructions` (bot-level, section 2.4). Skill 2 raises to user; Skill 1 patch mode adds it to section 2.4.

`validate_customer_address.intentInstructions` (corrected):
```
POST-EXECUTION BEHAVIOR
1. Confirm the address back.
2. Proceed to get_available_slots.
```

### Pitfall 4 — Persistent policy embedded in one intent

Bad — in `validate_customer_address.intentInstructions`:

```
POST-EXECUTION BEHAVIOR
1. Confirm the address.
2. Note: we never share customer data with third parties.
3. Note: we are GDPR-compliant; recordings are kept 30 days max.
4. Proceed to get_available_slots.
```

Why bad: the privacy policy applies to *every* intent. Putting it here means the LLM only "knows" the policy when this intent is active. In every other intent, the policy isn't in context.

Fix: move policy to `prompts.persona` (section 2.1). Skill 2 raises to user; Skill 1 patch mode handles the persona update.

### Pitfall 5 — Spoken script inside `validationPrompt` (v1.13.0, FP-5 — the #1 production failure)

Bad — in `validationPrompt` (real pipeline output, pre-v1.13):

```
GATE — PLAN & PREMIUM
1. Read clearly: the plan {{policies}}; the insurer {{insurer}}; the premium {{premium_after_discount}}.
2. Ask, in Hebrew:
   "האם זו התוכנית שביקשת לרכוש, והאם העלות מקובלת עליך?"
TURN-TAKING GUARD: wait for the customer's answer before proceeding...
```

Why bad: the Intent Agent is the ONLY consumer of `validationPrompt` — the voice model never sees it. The caller never hears the read-back or the question; the gate silently doesn't happen. The turn-taking guard is equally invisible.

Fix: script + question → `announcement` (§3b); guard → persona, once (FP-6); `validationPrompt` keeps only the capture mapping (C1). Caught by Skill 2 check 3 and Skill 3 check 16.

### Pitfall 6 — Setting another intent's parameter (v1.13.0, FP-8)

Bad — in a gate's `intentInstructions`:

```
* If the customer disapproves, set status_shikuf to: "הלקוח לא אישר משהו" and proceed to finalize_verification.
```

Why bad: `status_shikuf` belongs to a different intent. An intent can only set its own `IntentParameters` — this line is un-executable; at best ignored, at worst vocalized or hallucinated around.

Fix: the status lives on the terminal that represents this outcome, with its value written by that terminal's own `validationPrompt` (pattern C3). The gate just routes: `* If the customer disapproves, forward the call to Ending the call by forwarding the call to a hangup layer.` Caught by Skill 2 check 13 and Skill 3 check 18.

### Pitfall 7 — Duplicated farewell obligations (v1.13.0, FP-6)

Bad — call end spread across two intents and three fields:

```
finalize_verification.validationPrompt: ...speak the outcome-specific closing line...
finalize_verification.announcement: "תודה."
end_call.intentLoadingAnnouncement: "יום טוב ולהתראות."
```

Why bad: three separate speech obligations at call end — the diagnosed mechanism behind farewell-said-twice bugs. Plus an extra tool round-trip through the chained terminal.

Fix (v1.14.0): ONE terminal per outcome; the full closing line as an FP-4 quoted line in the **predecessor's** `intentInstructions` (last spoken line, then forward immediately — no wait, no reveal); the terminal keeps only the short loading goodbye. No terminal→terminal chains. Caught by Skill 2 checks 14/18 and Skill 3 checks 19/20.

### Pitfall 8 — "תודה." filler announcement (v1.13.0, FP-3)

Bad:

```
announcement: "תודה."
```

Why bad: the announcement is the deterministic speech channel — wasting it on a contentless acknowledgment creates a stilted rhythm and one more speech obligation per turn, while the real script hides in the wrong field.

Fix: acknowledgment belongs in `intentLoadingAnnouncement` ("מצויין, אני רושמת") where it naturally covers tool latency; `announcement` carries the read-back + the `**Asks next:**` question, or is intentionally empty per FP-3. Caught by the Skill 2 filler advisory and staggered-consistency check 16.

---

## 7. Checklist: are my fields placed and styled correctly? (v1.13.0)

Run through this before flipping an intent to `[detailed]`.

**validationPrompt (capture mapping, FP-5):**
- [ ] Short `*` bullets in save/capture/set language — one line per collectable slot / outcome
- [ ] NO speech: no ask/say/tell/greet/read-back imperatives, no question to the caller, no turn-taking guards, no routing
- [ ] Quoted strings appear only as VALUES being saved
- [ ] `**Terminal outcome:**` intents: the declared value mode is implemented (fixed ⇒ exact pinned string + never-ask line)

**announcement / intentLoadingAnnouncement (FP-2/FP-3/FP-7/FP-8):**
- [ ] `announcement` carries the read-back + the `**Asks next:**` question (or is intentionally empty per one of the two FP-3 cases — API-list read-out / pre-terminal farewell-in-instructions — logged to 7.3)
- [ ] No filler ("תודה.") in `announcement`
- [ ] RT=1: NO `announcement` at all (v1.14.0); loading announcement is a short "יום טוב"-style line; the farewell exists exactly once, on the predecessor's instructions
- [ ] Any intent transitioning into an RT=1: its instructions end with the FP-4 quoted farewell + immediate-forward / no-wait / no-reveal instruction
- [ ] RT=3: `intentLoadingAnnouncement` non-empty, persona/gender-matched
- [ ] `max_turns_sentence` written once per bot, persona/gender-matched (v1.14.0)
- [ ] No sentence appears in two fields (FP-6 say-once)

**intentInstructions (CR style + FP-4/FP-9):**
- [ ] Has at least one ALL-CAPS section header (or the golden bullet-routing shape of pattern I2)
- [ ] Contains the explicit wait rule ("stop and wait for the customer's explicit answer")
- [ ] All branching uses explicit IF / ELSE branches on the captured answer
- [ ] Routes by section-4 Description text, never by tool name
- [ ] Every mandated spoken line uses the FP-4 form `<instruction> : "<line>"`
- [ ] References only THIS intent's parameters (FP-8)
- [ ] If the intent asks ≥2 questions: one question per turn, in `CollectionOrder`
- [ ] No paragraphs of free prose
- [ ] No channel-specific behavior (pacing, formatting, emoji policy) — these belong in section 2.2 / 2.3
- [ ] No persistent policy (privacy, GDPR, retention) — these belong in section 2.1
- [ ] No bot-level disambiguation (greeting, routing) — this belongs in section 2.4
- [ ] No slot validation logic — constraints ride the capture lines in `validationPrompt`

**Cross-field:**
- [ ] All Mustache references resolve (per Skill 2 §5 mechanics; CustomData keys from 4.5.5 only)
- [ ] Text language matches the bot's primary language for spoken content; capture mapping in English operational prose

Pass on every line → safe to mark `[detailed]`.

---

*End of Conversation Routines Style Guide.*

---

## TTS-safety addendum (Compass rule 8 + rule 11)

These rules apply to the **spoken** fields Skill 2 authors when the bot has an active voice channel: `announcement`, `intentLoadingAnnouncement`, `fail_output`, `function_output`, and the FP-4 quoted lines of post-execution `intentInstructions`. (`validationPrompt` is exempt from rule 8 since v1.13.0 — it is never vocalized, and its capture-mapping form legitimately uses `*` bullets. Rule 11 RTL isolation still applies to every field.)

### No markdown formatting in voice fields

Markdown bullets (`-`, `*`, `+`), headers (`#`), and links (`[text](url)`) are read aloud literally by TTS. Forbidden in the spoken fields listed above.

**Don't:**

```
- שלום, איך אני יכולה לעזור?
- אנא ספק את פרטיך
```

**Do:**

```
שלום, איך אני יכולה לעזור?
אנא ספק את פרטיך.
```

### No URLs spoken aloud

Voice agents should not vocalize URLs. Replace with descriptions ("our website", "the support page") or remove from the prompt entirely.

### Long digit runs need spell-out instructions

Sequences of 6+ digits read awkwardly without an explicit "digit by digit" instruction nearby. Use `חזרי ספרה ספרה` (Hebrew), `Read digit by digit` (English), or the equivalent in the bot's primary language.

### RTL isolation — Hebrew/Arabic/CJK on its own line or inside quotes

Per Compass §4 "Sanity rule": Unicode bidirectional marks tokenize to garbage when RTL content is mixed inline with LTR. Terminal display will look correct; the tokens will not be.

**Don't:**

```
IRON: say שלום to the caller when they arrive.
```

**Do (FP-4 quote convention — instruction, colon, quoted verbatim line):**

```
IRON: greet the caller when they arrive. Say to the customer : "שלום".
```

Or:

```
IRON: greet the caller when they arrive. Say:
שלום
```

The FP-4 form satisfies rule 11 by construction — the RTL content is always inside quotes.
