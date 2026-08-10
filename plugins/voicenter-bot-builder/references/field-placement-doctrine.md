# Field-placement doctrine — Voicenter bot-builder reference (v1.17.0)

**Source:** production root-cause analysis comparing a pipeline-generated bot against a hand-built, production-validated golden bot for the same use case, plus the user-confirmed design decisions of v1.13.0, plus the v1.14.0 two-reference-bot ground-truth pass (terminal farewell placement, dedicated silence/API-timeout forwarding intents, mandatory off-topic handling, sensitive-flag placement), plus the v1.17.0 turn-yield fact confirmed on live test-bot calls (a non-empty `announcement` makes the bot wait for a caller turn). This file is the authority on **which prompt field carries which kind of content**. Where any older doc phrasing implies a different placement, this file wins.

**Read this when:** loaded by Skill 1, Skill 2, and Skill 3 at invocation per their §1 required-reading tables.

**Rule ownership:** Skill 1 owns FP-2 (structural staggering), FP-8, FP-9, FP-11 (interview), FP-12, and the persona half of FP-6 (including the v1.14.0 off-topic rule). Skill 2 owns FP-3 (including the v1.17.0 turn-yield rule), FP-4, FP-5, FP-7, and the per-intent half of FP-6. Skill 3 verifies at assembly time — enforced by CHK-16…CHK-24; see [`verification-procedure.md`](verification-procedure.md). The check procedures live there and nowhere else; this file owns the rules, not their verification steps.

**One-line doctrine:**

> **announcement** asks it *and waits for the answer*, **validationPrompt** captures it, **intentInstructions** routes it (and speaks without yielding the turn), **intentLoadingAnnouncement** covers the wait, **persona** rules it — each fact exactly once, in exactly one layer.

---

## 1. The runtime-consumer model — who reads what

A Voicenter voice bot config has **three consumers**. Misplacing content across them is the #1 source of production bugs (unspoken scripts, double announcements, hallucinated behavior).

### Consumer 1 — the live voice model (e.g., Gemini Live)
Always sees the bot-level prompt fields of the active version: `prompts.persona`, `prompts.voiceInstructions`, `prompts.intentInstructions` (the opening instructions, spec §2.4), `prompts.openingAnnouncement`, and the tool declarations (each intent's `IntentToolName`, `Description`, and parameter `Description`s). Per turn, when an intent tool completes, it receives that intent's `Configuration.announcement` (to speak) and `Configuration.intentInstructions` (what to do next).

**Key fact: the live voice model NEVER sees `validationPrompt`.** Anything written there that was meant to be spoken will not be spoken.

### Consumer 2 — the Intent Agent (parameter extraction/validation)
Sees `IntentConfig.prompts.validationPrompt` and the intent's `IntentParameters` — nothing else. Its only job is turning the caller's utterance into parameter values. Its instructions are never vocalized and never forwarded to the voice model.

### Consumer 3 — the platform / IVR layer
Consumes the structural fields: `ResponseTypeId`, `Configuration.layer`, `intentLoadingAnnouncement`, `botIntents` (entry/global roles), `intentRelations` (routing graph), `silence_behaviour`, `daily_limit` / `max_duration` and their layer targets.

---

## 2. Rule catalog

Severity legend matches `voice-prompt-doctrine.md`: **blocking** = the owning skill refuses to proceed until resolved; **advisory** = warn, record in spec §7.3, continue.

### FP-1 — Field-placement hard-rule table (blocking, all skills)

| Field | Consumer | Allowed content | Forbidden content |
|---|---|---|---|
| `Configuration.announcement` | Spoken to the caller when the intent completes — **and then the bot yields the turn and WAITS for a caller answer (v1.17.0 turn-yield fact)** | The scripted content the caller must hear when the intent awaits an answer: read-back with `{{CustomData}}` vars + the next question (FP-2/FP-3) | Routing logic, capture rules, filler ("תודה."); **any content at all on an auto-chaining intent (`Asks next:` [none]) — the announcement stalls the call waiting for an answer that never comes (FP-3 turn-yield, v1.17.0)**; **any content at all on RT=1 terminals (v1.14.0 — RT=1 never carries `announcement`; see the trigger rule below the table and FP-8)** |
| `IntentConfig.prompts.validationPrompt` | Intent Agent ONLY — never spoken, never seen by the voice model | Capture mapping, 1–3 bullets (FP-5); terminal outcome-value instruction per its mode | Scripts to speak, questions to ask, greetings, turn-taking guards, routing |
| `Configuration.intentInstructions` (per-intent) | Voice model, after tool completion | Post-answer routing by Description text + the wait rule; mandated spoken lines via the FP-4 convention when needed | Setting/referencing parameters of other intents; call-wide rules (persona's job); re-mandating a sentence already in `announcement` |
| `Configuration.intentLoadingAnnouncement` | Spoken while the tool executes | Short natural persona/gender-matched filler; on RT=1 terminals this is the intent's ONLY utterance — a short "יום טוב"-style line ("יום טוב!", "מעביר לנציג אנושי.") (v1.14.0) | Full content sentences; full farewell sentences; duplicate farewells |
| `prompts.persona` (bot-level) | Voice model, always | Identity, language, register + call-wide rules stated ONCE (FP-6) | Per-gate scripts |
| `prompts.intentInstructions` (bot-level — the opening instructions, spec §2.4) | Voice model, always | Opening-answer branching, identity read-back + next question when staggered (FP-2), FP-12 callback block | Re-greeting; per-gate capture logic |
| `prompts.openingAnnouncement` | First thing spoken | Greeting + purpose + recording disclosure + **the first question as the last sentence** | — |
| Intent `Description` | Voice model (tool declaration) + routing anchor | Short semantic label (FP-10) | Stage numbers, dialogue imperatives, business logic |

**RT=1 farewell trigger rule (v1.14.0, blocking).** The rule fires on a precise condition: **whenever an intent has a transition INTO an RT=1 (IVR / layer-transfer) intent.** In that case:
- The **predecessor's** `intentInstructions` MUST carry the ending/farewell sentence as the **LAST spoken line** (FP-4 quoted), said **immediately before forwarding** — without waiting for a caller answer, and without telling the caller the call is being transferred to a layer.
- The **RT=1 intent itself** then speaks ONLY its short `intentLoadingAnnouncement` ("יום טוב!"-style); it never carries an `announcement`.
- Production-verbatim shape (reference bot): `עלייך לומר את המשפט הבא ללקוח מיד : "ההודעה נשלחה, שמחתי לעזור… שתהיה נסיעה בטוחה". מיד לאחר מכן עלייך להעביר את השיחה מיד לסיום השיחה ללא המתנה לתגובה מהלקוח. אסור לך לומר ללקוח שאתה מעביר לשכבת ניתוק.`

### FP-2 — Staggered pipeline (BINDING; supersedes any conflicting phrasing in older docs)

The question the customer answers is asked by the **previous** intent's `announcement` (or its intent instructions), or — for the first answer — by the `openingAnnouncement` / opening instructions (spec §2.4). Intent N's parameters **capture that earlier question's answer**; intent N's own `announcement` asks the **next** question. The pipeline is offset by one step, because the runtime is function-calling: the caller's answer arrives as the parameters of the *next* tool call.

Worked example (golden-bot shape):

```
openingAnnouncement: "...האם זה זמן נוח לשיחה?"        ← question 0
opening instructions (§2.4): on "good time" → read identity
  details and ask : "האם הפרטים נכונים?"               ← question 1
        │ customer answers question 1
        ▼
Intent A  verify_plan_and_premium   (Description: "Verification of plan and premia")
  parameter  details_confirmed  ← captures the answer to question 1
  announcement: plan/premium read-back + "האם הפרטים נכונים?"   ← asks question 2
        │ customer answers question 2
        ▼
Intent B  confirm_health_declaration  (Description: "confirming health declaration")
  parameter  plan_confirmed   ← captures the answer to question 2
  announcement: health-declaration text + question              ← asks question 3
        ▼  …and so on. The intent-name↔parameter-name offset is intentional.
```

Structural encoding in the spec: section 4 fields `**Captures answer to:**` and `**Asks next:**` (Skill 1 fills them while walking the happy path).

### FP-3 — Script home + the turn-yield rule (blocking, Skill 2; verified by CHK-24)

**Turn-yield platform fact (v1.17.0 — confirmed on live test-bot calls):** a non-empty `announcement` makes the bot speak it and then **yield the turn — it waits for the caller to answer** before doing anything else. `announcement` is not merely "the spoken-content home"; it is a **wait-for-answer directive**. The placement rule follows directly from section-4 `**Asks next:**`:

- **`Asks next:` is a question** (the intent awaits a caller answer) → `announcement` MUST be non-empty and MUST carry the read-back + that question (FP-2 staggering).
- **`Asks next:` is `[none]`** (the intent auto-chains — its instructions immediately forward to the next intent) → `announcement` MUST be **empty**. Any line the caller must still hear moves to an FP-4 quoted line in the intent's post-execution `intentInstructions` (spoken without yielding the turn, immediately before the forward); pure acknowledgment belongs in `intentLoadingAnnouncement`.

A non-empty announcement on an auto-chaining intent stalls the call: the bot speaks it, waits for a caller turn that never comes, and the silence loop fires ("האם אתם עדיין על הקו?"). **Scope:** RT=2 and RT=3 `announcement`. RT=1 never carries one (FP-8). RT=4's `announcement` is pre-dial speech — the platform initiates the dial immediately after, so no turn-yield applies.

`announcement` remains the primary home for spoken content on answer-awaiting intents. Per-intent `intentInstructions` may ALSO carry speech (via FP-4) when the step involves several questions or short mandated lines. The two v1.14.0 production-verified intentional-empty cases are instances of the turn-yield rule (log every intentional-empty choice to spec §7.3):

- **(a) API list read-out:** an RT=2 intent whose API response returns a list of items the bot must start reading immediately — the read-out lives entirely under the intent's `intentInstructions` reading instructions, and no fixed transition sentence is wanted.
- **(b) Pre-terminal farewell-in-instructions:** the intent immediately before the final RT=1 terminal, with **no splits to other intents** — its farewell is an FP-4 quoted line in its own `intentInstructions` (the RT=1 farewell trigger rule, FP-1/FP-8).
- **(c) Any other auto-chaining intent (v1.17.0):** `Asks next:` is `[none]` and the flow proceeds automatically — e.g., a collect-and-forward RT=3 gate, or an RT=2 whose success speech is carried by the FP-4 farewell lines in its own instructions.

**Corollary (structural, Skill 1):** if the intent before the final RT=1 DOES have splits/transitions to other intents, Skill 1 must create a **dedicated pre-IVR intent whose only job is saying the ending sentence** before the terminal — case (b) never applies to a splitting intent.

Never author filler ("תודה.", "קיבלתי.") into `announcement`: acknowledgment belongs in `intentLoadingAnnouncement`.

### FP-4 — Quote convention for mandated speech (blocking, Skill 2; Skill 1 for §2.4/persona)

Whenever intent instructions or opening instructions (and persona call-wide rules) mandate a spoken line, use:

```
<instruction text> : "<verbatim target-language line, {{placeholders}} allowed>"
```

Examples (golden bot verbatim):
- `Say to the customer : "מצויין, אז קבענו ל {{callback_time}}, נחזור אלייך, שיהיה המשך יום טוב"`
- `Ask the customer : "האם הפרטים נכונים?"`
- `you must say to the customer : "בסדר גמור. נציג אנושי מטעם קבוצת קלי יחזור אליך בהקדם."`

Never used in `validationPrompt` — it never speaks. The quoting also satisfies Compass rule 11 (RTL isolation).

### FP-5 — validationPrompt is capture mapping only (blocking, Skill 2; verified by CHK-16)

1–3 bullet lines in save/capture/set language, one per outcome or slot:

```
* If the customer confirms, save "true" in the parameter details_confirmed.
* If the customer disapproves, save "false" in the parameter details_confirmed.
```

For a terminal's outcome slot, write the form matching the **user-chosen value mode** (see FP-8):
- **fixed** — pin the exact string: `shikuf_status MUST be exactly the string below; do not translate, paraphrase, or alter it: "הלקוח לא אישר משהו"` + `Never ask the customer to choose or confirm the status value.`
- **captured** — save the customer's utterance: `Save the callback time (day and hour) the customer stated in the parameter callback_time.`
- **dynamic** — compose per call: an explicit composition instruction for the slot.

**Forbidden here:** scripts to speak, questions to ask, greetings, turn-taking guards, routing. All of that is invisible to the voice model and noise to the Intent Agent.

### FP-6 — Say-once / rules-once (blocking; persona half Skill 1, per-intent half Skill 2; verified by CHK-19)

Every speak-obligation exists exactly once across all fields. Call-wide behavioral rules are stated exactly once, in `persona`:
- the turn-taking rule — golden wording: **"You should always act only after the customer answers and only by the instructions you got. You should never act without the customer's specific answer."**
- human-rep request handling (what to say + where to route), when a human-rep global exists
- disapproval/decline handling (what to say + where to route), when a decline terminal exists
- **off-topic handling (v1.14.0 — MANDATORY on every bot):** a persona section forbidding talk about subjects unrelated to the bot's purpose. On the **first** off-topic occurrence the bot says one deflection line + a redirect question back to the flow (e.g., `"מתנצל אבל אני כאן לעזור רק לגביי X, תרצה שנמשיך ?"`). If the caller **persists for N loops** (N is user-chosen in the Skill 1 interview, default 2), the bot says an FP-4 quoted ending line and forwards to the **dedicated off-topic global terminal**, referenced by its Description. The rule should warn against confusing a domain word/product with an off-topic subject.

Never paste these into per-intent fields; duplicated obligations are the diagnosed root cause of the bot saying things twice.

### FP-7 — intentLoadingAnnouncement mandatory on every RT=3 intent (blocking, Skill 2; verified by CHK-17)

An unconfigured `intentLoadingAnnouncement` produces the default `.` SAY directive — a verified production trigger for duplicated phrases and dead air. Author a short natural filler in the bot's persona and grammatical gender ("מצויין, אני רושמת", "אין בעיה, שניה רושמת"). On RT=1 terminals the loading announcement is the intent's **ONLY spoken content** (v1.14.0) — a short "יום טוב"-style goodbye ("יום טוב!", "מעביר לנציג אנושי.") — NEVER the full farewell, which lives in the previous intent's `intentInstructions` per the RT=1 farewell trigger rule (FP-1/FP-8).

### FP-8 — Terminal doctrine (blocking, Skill 1; verified by CHK-18/CHK-20)

- One terminal intent per distinct call outcome: `ResponseTypeId: 1` with a real `layer`, one hop to hang-up/transfer.
- Each terminal **owns** its status/outcome parameter. The value mode is per-terminal, understood from the characterization material the user sent or asked when unclear: **fixed** exact string, **captured** customer utterance, or **dynamic** per-call text (see FP-5).
- **The outcome-specific closing line lives in the PREVIOUS intent's `intentInstructions` (v1.14.0 — RT=1 farewell trigger rule).** It applies to EVERY intent whose transition target is RT=1: the ending sentence is the LAST spoken line there, an FP-4 quoted line followed by the instruction to forward immediately — without waiting for an answer and without announcing the transfer. The terminal itself carries **NO `announcement`**, only a short `intentLoadingAnnouncement` ("יום טוב!" / "מעביר לנציג אנושי."). If the predecessor splits to several intents, a dedicated pre-IVR farewell intent is created instead (FP-3 corollary).
- **Forbidden:** finalize→end_call two-intent chains; a single intent computing the status via IF/ELSE-IF prose (forces LLM recall of the whole call — non-deterministic); any transition whose origin is an RT=1 terminal.
- **Gates NEVER reference or set another intent's parameter.** An intent can only set its own `IntentParameters` — "Set status_X to …" on a gate that doesn't own status_X is un-executable.
- The "call dropped mid-way" outcome is the *absence* of any terminal having set the status (handled downstream, e.g., in n8n) — the bot never sets it.

### FP-9 — Minimal graph (blocking at Skill 1; CHK-22 advisory)

`intentRelations` carry only the linear happy-path spine + true branches. Exception outcomes (human-rep request, decline/not-confirmed) are registered in `botIntents` with `BotIntentTypeID: 2` (globally triggerable) and routed by the persona's FP-6 call-wide rules — no explicit edge from every gate. Announcements/instructions reference next intents by their section-4 **Description text** (that is how the voice model identifies them), never by tool name. Golden reference: 6 edges for a 9-intent flow.

### FP-10 — Description doctrine (blocking, Skill 1)

`Description` = a **short semantic English label naming the business step** — the LLM's intent-recognition anchor and the name other intents' instructions use for routing:

| Bad (v1.12 output) | Good (golden bot) |
|---|---|
| "Stage 2. Read back the plan/program name, the insurer, and the monthly premium after discount, plus the underwriting disclaimer…, and ask the customer to confirm…" | "Verification of plan and premia" |
| "Stage 3. Explain the importance of the health declaration and the consequences of inaccuracy, and ask…" | "confirming health declaration" |
| "Stage 4. Confirm the customer received the fair-disclosure document…, read aloud the key fair-disclosure points, and ask…" | "Confirming the customer received the fair-disclosure document from the sales supporter" |

**Forbidden in Description:** workflow/stage markers ("Stage 2", "Gate C"), dialogue imperatives ("Read back…", "Ask…", "Explain…"), business logic ("premium may change after further review"). Specific data points belong in the intent's parameter `Description` fields; conversational content belongs in `announcement`/instructions per FP-3; business logic belongs in the opening instructions or persona.

`llmDescription` is out of scope for this doctrine — it keeps its existing pipeline behavior (emitted `""`, Skill 3 Appendix A quirk 14).

### FP-11 — CustomData keys are never invented (blocking; Skill 1 interview, CHK-07)

Every `{{placeholder}}` used anywhere must exactly match a key declared in spec §4.5 — including the per-call payload list in §4.5.5 — or a platform context var (e.g., `{{todayHe}}`, `{{timeHe}}`). A wrong or invented key means the caller hears the literal token or nothing. Skill 1's interview collects the exact key list; Skills 2/3 may only use keys from that list.

### FP-12 — Callback date/time interpretation block (blocking when a callback/scheduling time is collected; Skill 1 check 21)

Whenever the flow collects a callback or scheduling time, the opening instructions (§2.4) must include the canonical interpretation block:

- Anchor: `Current conversation date and day: {{todayHe}}; conversation time: {{timeHe}}. Use this date and time to interpret terms like "now," "today," "tomorrow," or "the day after tomorrow" relative to the current conversation time.`
- Relative time ("עכשיו", "עוד שעה", "בקרוב") → **compute silently**; do not ask for or read back the time.
- Relative day without an hour ("היום", "מחר", a weekday) → ask only : `"באיזו שעה ?"`.
- Both day and time provided → proceed.
- **Never re-ask information the customer already provided**; ask only for what is missing.

### FP-13 — ENUM doctrine (blocking, Skill 1 Appendix B mapping)

ENUM (ParameterTypeId 19, with `OptionList`) is used only when a parameter selects among **multiple** fixed values. A single pinned value (e.g., a fixed-mode terminal status) stays STRING (ParameterTypeId 1) with the value pinned in that terminal's validationPrompt per FP-5. Free text the customer supplies (e.g., a natural-language callback time) is STRING.

---

## 3. Anti-pattern table (all observed in production or in v1.12 pipeline output)

| Anti-pattern | Consequence | Rule | Caught by |
|---|---|---|---|
| Spoken script inside validationPrompt | Never reaches the voice model — the caller doesn't hear the gate | FP-5 | Skill 2 check 3; CHK-16 |
| Same sentence mandated in two fields (announcement + intentInstructions, or intent + bot-level) | Bot says it twice | FP-6 | Skill 2 check 14; CHK-19 |
| Missing intentLoadingAnnouncement on RT=3 | Default "." SAY directive → duplicated phrases / dead air | FP-7 | Skill 2 check 12; CHK-17 |
| Gate instructed to set another intent's parameter | Un-executable; ignored or hallucinated around | FP-8 | Skill 2 check 13; CHK-18 |
| One "finalize" intent computing status via IF/ELSE-IF | Non-deterministic outcome; depends on LLM recall | FP-8 | Skill 1 check 19 |
| Terminal chain (finalize → end_call) | Extra tool round-trips; multiple farewells | FP-8 | Skill 1 check 19; CHK-20 |
| Dedicated yes/no gate for the opening question | Wasted turn before the first real question | FP-2 | Skill 1 check 18 |
| Turn-taking guard pasted into every intent | Prompt bloat in a layer the voice model never sees | FP-6 | Skill 1 check 20; CHK-16/CHK-19 |
| Invented `{{placeholder}}` names | Literal tokens read aloud to the caller | FP-11 | CHK-07 |
| Stage markers / dialogue / business logic in Description | Degrades tool routing; leaks workflow into the tool layer | FP-10 | Skill 1 §3.4.3 authoring rule |
| Re-authored ParameterType blocks | Schema drift vs the platform's system dictionary | — | CHK-21 |
| "תודה." filler announcements | Stilted rhythm; extra speech obligation per turn | FP-3 | Skill 2 filler advisory |
| Non-empty `announcement` on an auto-chaining intent (`Asks next:` [none]) (v1.17.0) | Bot speaks it, yields the turn, and waits for an answer that never comes → silence loop → "האם אתם עדיין על הקו?" | FP-3 | Skill 2 checks 10/16; CHK-24 |
| Explicit wait rule ("stop and wait for the customer's answer") in an auto-chaining intent's `intentInstructions` (v1.17.0) | Voice model obeys post-execution, stalls waiting for a turn that never comes → silence loop | FP-3 | Skill 2 step-4 authoring rule; CHK-24 (advisory half) |
| Full farewell inside an RT=1 terminal's `announcement` / loading announcement (v1.14.0) | Double farewell + farewell spoken from the wrong layer; predecessor forwards mid-sentence | FP-8 | Skill 2 check 18; CHK-20 |
| No off-topic rule in persona / no dedicated off-topic global intent (v1.14.0) | Bot chats off-scope indefinitely; no escape hatch when the caller won't return to the flow | FP-6 | Skill 1 checks 20/22; CHK-23 |
