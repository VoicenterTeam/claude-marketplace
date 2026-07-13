# Field-placement doctrine — Voicenter bot-builder reference (v1.13.0)

**Source:** production root-cause analysis comparing a pipeline-generated bot against a hand-built, production-validated golden bot for the same use case, plus the user-confirmed design decisions of v1.13.0. This file is the authority on **which prompt field carries which kind of content**. Where any older doc phrasing implies a different placement, this file wins.

**Read this when:** loaded by Skill 1, Skill 2, and Skill 3 at invocation per their §1 required-reading tables.

**Rule ownership:** Skill 1 owns FP-2 (structural staggering), FP-8, FP-9, FP-11 (interview), FP-12, and the persona half of FP-6. Skill 2 owns FP-3, FP-4, FP-5, FP-7, and the per-intent half of FP-6. Skill 3 verifies (cross-reference checks 16–22).

**One-line doctrine:**

> **announcement** says it, **validationPrompt** captures it, **intentInstructions** routes it, **intentLoadingAnnouncement** covers the wait, **persona** rules it — each fact exactly once, in exactly one layer.

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
| `Configuration.announcement` | Spoken to the caller when the intent completes | The scripted content the caller must hear: read-back with `{{CustomData}}` vars + the next question (FP-2/FP-3) or, on terminals, the outcome-specific closing line | Routing logic, capture rules, filler ("תודה.") |
| `IntentConfig.prompts.validationPrompt` | Intent Agent ONLY — never spoken, never seen by the voice model | Capture mapping, 1–3 bullets (FP-5); terminal outcome-value instruction per its mode | Scripts to speak, questions to ask, greetings, turn-taking guards, routing |
| `Configuration.intentInstructions` (per-intent) | Voice model, after tool completion | Post-answer routing by Description text + the wait rule; mandated spoken lines via the FP-4 convention when needed | Setting/referencing parameters of other intents; call-wide rules (persona's job); re-mandating a sentence already in `announcement` |
| `Configuration.intentLoadingAnnouncement` | Spoken while the tool executes | Short natural persona/gender-matched filler; on terminals a brief goodbye (if no farewell elsewhere) | Full content sentences; duplicate farewells |
| `prompts.persona` (bot-level) | Voice model, always | Identity, language, register + call-wide rules stated ONCE (FP-6) | Per-gate scripts |
| `prompts.intentInstructions` (bot-level — the opening instructions, spec §2.4) | Voice model, always | Opening-answer branching, identity read-back + next question when staggered (FP-2), FP-12 callback block | Re-greeting; per-gate capture logic |
| `prompts.openingAnnouncement` | First thing spoken | Greeting + purpose + recording disclosure + **the first question as the last sentence** | — |
| Intent `Description` | Voice model (tool declaration) + routing anchor | Short semantic label (FP-10) | Stage numbers, dialogue imperatives, business logic |

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

### FP-3 — Script home (blocking, Skill 2)

`announcement` is the primary home for spoken content. Per-intent `intentInstructions` may ALSO carry speech (via FP-4) when the step involves several questions or short mandated lines. `announcement` MAY be intentionally **empty** with the speech carried entirely by `intentInstructions` — e.g., reading an API-response list under reading instructions, where no fixed transition sentence is wanted; log the choice to spec §7.3. Never author filler ("תודה.", "קיבלתי.") into `announcement`: acknowledgment belongs in `intentLoadingAnnouncement`.

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

### FP-5 — validationPrompt is capture mapping only (blocking, Skill 2; verified by Skill 3 check 16)

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

### FP-6 — Say-once / rules-once (blocking; persona half Skill 1, per-intent half Skill 2; verified by Skill 3 check 19)

Every speak-obligation exists exactly once across all fields. Call-wide behavioral rules are stated exactly once, in `persona`:
- the turn-taking rule — golden wording: **"You should always act only after the customer answers and only by the instructions you got. You should never act without the customer's specific answer."**
- human-rep request handling (what to say + where to route), when a human-rep global exists
- disapproval/decline handling (what to say + where to route), when a decline terminal exists

Never paste these into per-intent fields; duplicated obligations are the diagnosed root cause of the bot saying things twice.

### FP-7 — intentLoadingAnnouncement mandatory on every RT=3 intent (blocking, Skill 2; verified by Skill 3 check 17)

An unconfigured `intentLoadingAnnouncement` produces the default `.` SAY directive — a verified production trigger for duplicated phrases and dead air. Author a short natural filler in the bot's persona and grammatical gender ("מצויין, אני רושמת", "אין בעיה, שניה רושמת"). On terminals a brief goodbye ("יום טוב") is fine — but then the farewell must not ALSO appear in another field (FP-6).

### FP-8 — Terminal doctrine (blocking, Skill 1; verified by Skill 3 checks 18/20)

- One terminal intent per distinct call outcome: `ResponseTypeId: 1` with a real `layer`, one hop to hang-up/transfer.
- Each terminal **owns** its status/outcome parameter. The value mode is per-terminal, understood from the characterization material the user sent or asked when unclear: **fixed** exact string, **captured** customer utterance, or **dynamic** per-call text (see FP-5).
- The outcome-specific closing line lives in the terminal's own `announcement`.
- **Forbidden:** finalize→end_call two-intent chains; a single intent computing the status via IF/ELSE-IF prose (forces LLM recall of the whole call — non-deterministic); any transition whose origin is an RT=1 terminal.
- **Gates NEVER reference or set another intent's parameter.** An intent can only set its own `IntentParameters` — "Set status_X to …" on a gate that doesn't own status_X is un-executable.
- The "call dropped mid-way" outcome is the *absence* of any terminal having set the status (handled downstream, e.g., in n8n) — the bot never sets it.

### FP-9 — Minimal graph (blocking at Skill 1; Skill 3 check 22 advisory)

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

### FP-11 — CustomData keys are never invented (blocking; Skill 1 interview, Skill 3 check 7)

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
| Spoken script inside validationPrompt | Never reaches the voice model — the caller doesn't hear the gate | FP-5 | Skill 2 check 3; Skill 3 check 16 |
| Same sentence mandated in two fields (announcement + intentInstructions, or intent + bot-level) | Bot says it twice | FP-6 | Skill 2 check 14; Skill 3 check 19 |
| Missing intentLoadingAnnouncement on RT=3 | Default "." SAY directive → duplicated phrases / dead air | FP-7 | Skill 2 check 12; Skill 3 check 17 |
| Gate instructed to set another intent's parameter | Un-executable; ignored or hallucinated around | FP-8 | Skill 2 check 13; Skill 3 check 18 |
| One "finalize" intent computing status via IF/ELSE-IF | Non-deterministic outcome; depends on LLM recall | FP-8 | Skill 1 check 19 |
| Terminal chain (finalize → end_call) | Extra tool round-trips; multiple farewells | FP-8 | Skill 1 check 19; Skill 3 check 20 |
| Dedicated yes/no gate for the opening question | Wasted turn before the first real question | FP-2 | Skill 1 check 18 |
| Turn-taking guard pasted into every intent | Prompt bloat in a layer the voice model never sees | FP-6 | Skill 1 check 20; Skill 3 checks 16/19 |
| Invented `{{placeholder}}` names | Literal tokens read aloud to the caller | FP-11 | Skill 3 check 7 |
| Stage markers / dialogue / business logic in Description | Degrades tool routing; leaks workflow into the tool layer | FP-10 | Skill 1 §3.4.3 authoring rule |
| Re-authored ParameterType blocks | Schema drift vs the platform's system dictionary | — | Skill 3 check 21 |
| "תודה." filler announcements | Stilted rhythm; extra speech obligation per turn | FP-3 | Skill 2 filler advisory |
