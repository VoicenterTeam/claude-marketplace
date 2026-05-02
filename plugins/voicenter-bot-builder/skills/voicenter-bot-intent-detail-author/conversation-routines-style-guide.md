# Conversation Routines Style Guide

**Purpose:** concrete templates and worked examples for `validationPrompt` and post-execution `intentInstructions` in Voicenter Agent Specs. Supports Skill 2 (Intent Detail Author) — Skill 2 references this file during steps 2 and 4.

**Scope:** the two Conversation Routines fields Skill 2 owns. Bot-level `prompts.intentInstructions` (Opening Behavior in section 2.4) is also Conversation Routines styled but is Skill 1's domain.

**Source:** Doc 1 §14.3.2 defines the style. This file expands with concrete patterns.

---

## 1. Required elements

| Element | Form | Example |
|---|---|---|
| ALL-CAPS section headers | Bare line, no markdown | `ADDRESS COLLECTION` |
| Numbered steps | `1.`, `2.`, `3.` (not bullets) | `1. Ask the caller for their address.` |
| IF / ELSE branches | Inline or indented under their step | `IF caller refuses: transfer to human.` |
| IRON RULE blocks | At least one per prompt | `IRON RULE: do NOT accept partial addresses.` |

## 2. Forbidden patterns

| Pattern | Why bad | Where it belongs instead |
|---|---|---|
| Free prose ("Be helpful and friendly throughout.") | No anchors; LLM behavior drifts | Nowhere — delete or restructure |
| Vague directives ("Make it clear what we offer.") | Unverifiable | Persona, with concrete scope language |
| Channel-specific behavior ("Speak slowly and pause.") | Misplacement per §14.3.9 | `prompts.voiceInstructions` (section 2.2) |
| Persistent policy ("We're GDPR-compliant.") | Misplacement per §14.3.13 | `prompts.persona` (section 2.1) |
| Slot validation logic in `intentInstructions` | Misplacement per §14.3.12 — runs after slots are already collected | `validationPrompt` |
| Pre-intent disambiguation in per-intent `intentInstructions` | Misplacement per §14.3.11 — runs after the intent has already fired | `prompts.intentInstructions` (bot-level, section 2.4) |

---

## 3. `validationPrompt` patterns

The `validationPrompt` lives in `IntentConfig.prompts.validationPrompt`. Pre-execution: it shapes how the bot collects the intent's slots from the caller.

### Pattern V1 — Minimal single-slot collection

Use when: the intent has one required slot, simple validation, no branching.

```
ADDRESS COLLECTION
1. Ask the caller for their full address.
2. Repeat the street name and house number back for confirmation.
3. Confirm with caller before proceeding.

IRON RULE: do NOT accept partial addresses. Street name, house number, and city are all required.
```

Hebrew variant:

```
איסוף כתובת
1. בקשי מהמתקשר את הכתובת המלאה.
2. חזרי על שם הרחוב ומספר הבית לאישור.
3. ודאי עם המתקשר לפני המשך.

חוק ברזל: אל תקבלי כתובות חלקיות. שם רחוב, מספר בית ועיר — כולם נדרשים.
```

### Pattern V2 — Multi-slot with branching

Use when: the intent has multiple slots, edge cases need explicit handling.

```
APPOINTMENT BOOKING
1. Ask for the customer's full address.
2. Repeat the street and number back; confirm.
3. Ask for preferred time slot from the options offered.
4. Confirm the slot back to the caller.

IF caller gives a partial address (only street, no number):
  - Ask for the missing piece specifically.
  - Do not move on until both are present.

IF caller asks for a time slot that wasn't offered:
  - Apologize, restate the available options.
  - If still no match, suggest scheduling for the next available day.

IF caller refuses to provide an address:
  - Explain it's required to confirm the appointment.
  - If still refused, transfer to transfer_to_human.

IRON RULES:
- Every appointment requires a complete address.
- The selected time slot must be one of the offered options. No improvisation.
- Do NOT discuss pricing — refer to transfer_to_human for billing.
```

### Pattern V3 — ENUM slot with static option list

Use when: slot is `ParameterTypeId 19` (ENUM) with a known `OptionList`.

```
SERVICE TYPE SELECTION
1. Ask the caller which service they need.
2. Present the three options:
   - Installation
   - Repair
   - Cancellation
3. Wait for the caller to pick one.
4. Confirm the selection by name.

IF caller's answer doesn't clearly match one of the three:
  - Ask once more, list the options again.
  - If still unclear, transfer to transfer_to_human.

IRON RULE: only the three offered options are valid. Do NOT improvise a fourth (e.g., "consultation" — this isn't a service we offer).
```

### Pattern V4 — ENUM with dynamic options (from upstream RT=2)

Use when: slot is ENUM, `OptionList` is empty in the spec, options are populated at runtime from an upstream API response (typically declared in section 4.5.4).

```
TIME SLOT SELECTION
1. Present the available time slots from the system response.
   The slots are in {{available_slots}} as a list — read each one's display value.
2. Ask the caller to pick one.
3. Confirm the selected slot back using its exact display format.

IF the system returned no slots:
  - Apologize, explain none are available right now.
  - Offer to transfer to a human to find an alternative.

IF caller picks a slot not in the list:
  - Restate the available options.
  - If still no match, suggest the closest available alternative.

IRON RULE: only slots present in {{available_slots}} are bookable. Do NOT confirm a slot that isn't in the list.
```

### Pattern V5 — v1-fallback slot (STRING storing a phone number, date, etc.)

Use when: slot type is STRING (PT=1) but represents structured data (phone, date, email). v1 has limited ParameterTypeId coverage; the validation work moves into the prompt.

```
PHONE NUMBER COLLECTION
1. Ask for the caller's phone number.
2. Repeat the digits back, one at a time.
3. Confirm with caller.

IRON RULES:
- Must be exactly 10 digits.
- Strip dashes and spaces silently — do not require the caller to omit them.
- Do NOT accept fewer than 10 digits. Ask again if shorter.
- Do NOT accept letters or symbols. Ask again if present.
- Valid prefixes: starts with 02-09, or 050-058. Other prefixes — ask once more, then transfer to human if still unmatched.
```

```
DATE OF BIRTH COLLECTION
1. Ask for the caller's date of birth.
2. Repeat back as DD/MM/YYYY for confirmation.
3. Confirm with caller.

IF caller gives only a partial date (e.g., year only):
  - Ask for the missing pieces specifically.

IRON RULES:
- Format: day, month, year. All three required.
- Year must be 1900 or later, and not in the future.
- If caller refuses, transfer to transfer_to_human — date of birth is required for verification.
```

---

## 4. Post-execution `intentInstructions` patterns

`intentInstructions` lives in `IntentResponces.Configuration.intentInstructions`. Post-execution: defines what the bot does *after* this intent has fired and slots have been collected.

### Pattern I1 — Minimal single-path

Use when: the intent has one outcome and one next step.

```
POST-EXECUTION BEHAVIOR
1. Confirm the validated address back to the caller.
2. Proceed to fetch available time slots.

IRON RULE: do NOT discuss pricing or technical issues. Transfer to human for those.
```

Hebrew variant:

```
התנהגות לאחר ביצוע
1. אשרי את הכתובת שאומתה לאחר חזרה למתקשר.
2. עברי לשליפת חלונות זמן זמינים.

חוק ברזל: אל תדוני במחירים או בבעיות טכניות. העבירי לאדם עבור אלה.
```

### Pattern I2 — Branching by intent outcome (typically RT=2)

Use when: the intent's outcome can succeed or fail, and the next intent depends on which.

```
POST-EXECUTION BEHAVIOR
1. Read the system response.
2. IF the response indicates success:
   - Read the confirmation details to the caller.
   - Proceed to confirm_appointment.
3. IF the response indicates failure (e.g., no available slots):
   - Apologize.
   - Offer to transfer to a human for alternatives.
   - Proceed to transfer_to_human.

IRON RULES:
- Do NOT invent slots that aren't in the response.
- Do NOT promise a callback unless the system response explicitly says one is scheduled.
```

### Pattern I3 — Confirmation + transition with explicit scope guard

Use when: the intent is the last meaningful step before terminal, and scope-creep is a known risk.

```
POST-EXECUTION BEHAVIOR
1. Confirm the appointment details: time, address, service type.
2. Tell the caller they'll receive an SMS with the details.
3. Ask if there's anything else they need.

IF caller asks to change the appointment:
  - Apologize for the back-and-forth.
  - Transfer to reschedule_existing intent.

IF caller asks unrelated questions:
  - Answer briefly only if it's directly about this appointment (e.g., "what should I bring?").
  - For pricing, billing, technical issues, account changes: transfer to transfer_to_human.

IRON RULES:
- Do NOT offer to book additional appointments in this turn — that's a separate flow.
- Do NOT quote prices, even if asked. Transfer for any pricing question.
- Do NOT discuss policy details (privacy, GDPR) — these live in the persona; defer to those.
```

### Pattern I4 — RT=2 with conditional API silence escalation

Use when: an RT=2 intent has a non-trivial API silence fallback path that should be reflected in post-execution instructions (e.g., the API silence escalates to a different intent than the success path).

```
POST-EXECUTION BEHAVIOR
1. IF the API responded successfully within the silence window:
   - Read the response details from {{response.summary}}.
   - Proceed to confirm_appointment.
2. IF the API silence_ending_sentence fired (the API took too long):
   - The silence handler already announced the delay.
   - Transfer to transfer_to_human.

IRON RULE: do NOT retry the API in this intent. The silence behavior owns retries; this intent is post-call.
```

---

## 5. Worked example — complete intent

Bringing it together: a complete RT=3 intent (`validate_customer_address`) with both fields filled.

### Slot definitions (from step 1)

```
Slot: address
- Description: כתובת מלאה: רחוב, מספר בית, עיר. למשל: רחוב הרצל 14 רמת גן.
- Type: STRING (ParameterTypeId 1)
- Required: true
- Collection order: 1
```

### `validationPrompt` (from step 2)

```
איסוף כתובת
1. בקשי מהמתקשר את הכתובת המלאה (רחוב, מספר בית, עיר).
2. חזרי על שם הרחוב ומספר הבית לאישור.
3. ודאי עם המתקשר לפני המשך.

אם המתקשר נותן כתובת חלקית (רק רחוב, ללא מספר):
  - בקשי את החלק החסר במפורש.
  - אל תמשיכי עד ששני החלקים נוכחים.

אם המתקשר מסרב לתת כתובת:
  - הסבירי שזה נדרש כדי לקבוע את התור.
  - אם עדיין מסרב, העבירי ל-transfer_to_human.

חוקי ברזל:
- שם רחוב, מספר בית ועיר — כל השלושה נדרשים.
- אל תדוני במחירים. העבירי ל-transfer_to_human עבור שאלות חיוב.
```

### Post-execution `intentInstructions` (from step 4)

```
POST-EXECUTION BEHAVIOR
1. Confirm {{address}} back to the caller in clear Hebrew.
2. Tell them you're now checking available time slots.
3. Proceed to get_available_slots.

IRON RULES:
- Do NOT discuss pricing, billing, or technical issues. Transfer to transfer_to_human for those.
- Do NOT make promises about appointment timing — wait for get_available_slots to return.
```

---

## 6. Common authoring pitfalls and fixes

### Pitfall 1 — "Just be helpful" prose creeps in

Bad:

```
ADDRESS COLLECTION
1. Ask the caller for their address.
2. Be helpful and patient if they need to think.
3. Repeat it back.
```

Why bad: step 2 is unverifiable prose. The LLM doesn't know what "helpful and patient" means concretely.

Fix: replace with a concrete behavior or remove.

```
ADDRESS COLLECTION
1. Ask the caller for their address.
2. IF caller pauses or asks to think: wait without repeating the question for at least 3 seconds.
3. Repeat the address back.
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

Fix: move steps 1-2 to `validationPrompt`. Keep `intentInstructions` to genuinely-post-execution behavior.

`validationPrompt`:
```
PHONE COLLECTION
1. Ask for the phone number.
2. Repeat digits back.
3. IRON RULE: must be exactly 10 digits. Strip dashes silently.
```

`intentInstructions`:
```
POST-EXECUTION BEHAVIOR
1. Confirm the phone number back to the caller.
2. Proceed to next step.
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

---

## 7. Checklist: is my prompt Conversation Routines styled?

Run through this before flipping an intent to `[detailed]`.

- [ ] Has at least one ALL-CAPS section header
- [ ] Steps are numbered (`1.`, `2.`, `3.`), not bulleted
- [ ] All branching uses explicit IF / ELSE
- [ ] At least one IRON RULE block exists
- [ ] No paragraphs of free prose
- [ ] No channel-specific behavior (pacing, formatting, emoji policy) — these belong in section 2.2 / 2.3
- [ ] No persistent policy (privacy, GDPR, retention) — these belong in section 2.1
- [ ] No bot-level disambiguation (greeting, routing) — this belongs in section 2.4
- [ ] No slot validation logic in `intentInstructions` — that belongs in `validationPrompt`
- [ ] All Mustache references resolve (per Skill 2 §5 mechanics)
- [ ] Prompt language matches the bot's primary language

Pass on every line → safe to mark `[detailed]`.

---

*End of Conversation Routines Style Guide.*
