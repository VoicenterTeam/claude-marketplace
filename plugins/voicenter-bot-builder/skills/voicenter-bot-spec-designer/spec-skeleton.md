# Agent Spec — [Bot Name]

*This is the strict-template skeleton for the Voicenter Bot Agent Spec, per Doc 2 §3 and §3.7. Skill 1 populates sections 1, 2, 3, 4, 4.5, and stubs of section 5; Skill 1 also produces the initial pass at section 6 and initializes section 7. Skill 2 fills section 5 entries and updates 4.5.3 and 6.1. Skill 3 reads the spec deterministically; deviations from the template are parse errors, not interpretation opportunities.*

---

## 1. Bot Identity

**Bot Name:** [name]
**Identifier:** [snake_case ASCII identifier; e.g., yuval, refua, customer_support — used for the emitted JSON filename]
**Description:** [description]
**Account ID:** [int, or `<UNKNOWN: Account ID>`]
**Primary Language:** [BCP-47 code, e.g., `he-IL`, `en-US`]
**Channels Active:** [`voice` | `chat` | `voice+chat`]
**Voice Name:** [voice name from catalog | raw string | omit if no voice channel]
**Agent Gender:** [`Female` | `Male`; selection aid for the voice choice — omit if no voice channel. Spec metadata only; not emitted to the JSON.]
**AI Model Config:** [name from catalog | `raw: ID=X, TypeID=Y` | `<UNKNOWN: AI Model Config>`]
**Created by:** [bot author/owner name | omit if not set; defaults to empty string at emission]
**Max call duration:** [int seconds; default 1200]
**Record agent calls:** [`true` | `false`; default false. Skill 3 emits the STRING form per production wire format.]

---

## 2. Persona Bundle

### 2.1 Persona (Global Identity)

[persona text — identity, role, tone, language, hard constraints. Channel-agnostic. Often multiline. Often Hebrew.]

### 2.2 Voice Instructions

[voiceInstructions text — pacing, pronunciation, interruption handling, audio cues.]

[OR if defaulted: `[default — not user-authored]` followed by template content from `templates/voice-default.md` with [[PLACEHOLDERS]] substituted.]

### 2.3 Chat Instructions

[chatInstructions text — formatting, message length, emoji policy.]

[OR if defaulted: `[default — not user-authored]` followed by template content from `templates/chat-default.md` with [[PLACEHOLDERS]] substituted.]

### 2.4 Bot-Level Intent Instructions (Opening Behavior)

[intentInstructions text in Conversation Routines style. Pre-intent. Greeting + routing logic + iron rules.]

### 2.5 Opening Announcement

[openingAnnouncement text — single short utterance. The first audible message the caller hears.]

---

## 3. Caller Silence Behavior

[Caller-silence handling is MANDATORY (v1.11.0) — this section is always populated. Each field has a default the author may accept or override. Defaults: `silence_duration` 5, `silence_loops` 3, `silence_sentence` a polite re-prompt in the primary language, `silence_ending_sentence` a transfer line (if the forward target transfers) or a polite hang-up.]

- **silence failover intent:** [intent identifier from section 4, OR a global/system catalog intent's real `IntentId` declared in section 4.6 — the intent to route to when `silence_loops` is exhausted; Skill 3 emits it as `silence_behaviour.intent`. Default to the transfer-to-human `global` when one exists; else a section-4.6 catalog intent, an end-call intent, or `<UNKNOWN: silence failover intent>`.]
- **silence_duration:** [int seconds]
- **silence_loops:** [int]
- **silence_sentence:** [text, Mustache OK]
- **silence_ending_sentence:** [text. If the failover intent is the transfer-to-human `global`, prefer a "transferring you to a representative" line over a hang-up line. If there is no transfer-to-human global, keep a polite hang-up line.]

---

## 4. Intent List (Structural)

### Intent 1: [snake_case_identifier]

- **Display name:** [human-readable, often Hebrew]
- **Description:** [plain language, used by LLM at runtime for intent recognition]
- **Tool name:** [same as identifier]
- **Response Type:** [1 | 2 | 3 | 4]
- **Purpose:** [one-line description for human review]
- **Hard intent:** [`true` | `false`]
- **Bot-intent role:** [`entry` | `global` | `chained`; default `chained`. `entry` = directly triggerable from the §2.4 opening behaviour; `global` = triggerable from anywhere (transfer-to-human, WhatsApp). `global` supersedes `entry`. Skill 3 emits `entry`→`BotIntentTypeID 1`, `global`→`2`, `chained`→omitted from `botIntents[]`.]
- **Completion status:** [structural]
- **Transitions out:**
  1. [target intent identifier] (success path)
  2. [target intent identifier] (fallback / escalation)
- **Escalation target:** [identifier — typically `transfer_to_human`]
- **Slots:**
  1. [slot_name] — `ParameterTypeId` [N], Required [`true`|`false`], Order [N], OptionList [if ENUM]
- **Max turns:** [int; optional override. Skill 1 does NOT ask for this in the interview — Skill 3 applies smart defaults at emission time (RT=2 default `15`; RT=1/3/4 omit unless set). Spec authors hand-editing the spec may set this to override the Skill 3 default for a specific intent.]
- **Max turns sentence:** [string; optional override. Skill 3 default for RT=2: `"אני חייב לסיים את השיחה בשלב הזה."` Spec authors may override here; otherwise Skill 3 emits the production default when `Max turns` is set.]
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
  - **Dial source:** [`parameter` | `static`]   (RT=4 only — chooses whether the dialed number comes from a slot or is hard-coded)
  - **Parameter phone:** [slot identifier from this intent's slot list]   (RT=4 only, dial-source=parameter)
  - **Phone1 / Phone2 / Phone3:** [E.164 with leading `+`, attempted in order]   (RT=4 only, dial-source=static; any unused slot may be `""`)
  - **selectdial_option:** [`Parameter` for slot-driven; or the user's literal choice for static]   (RT=4 only)
  - **NEXT_VO_ID:** [int — destination voice-objective id; `<UNKNOWN: NEXT_VO_ID>` if not known]   (RT=4 only)
  - **MAX_DIAL_DURATION:** [int seconds]   (RT=4 only)
  - **Record:** [`true` | `false`]   (RT=4 only)
  - **Announcement:** [string spoken just before the transfer; optional]   (RT=4 only)
  - **Loading announcement:** [string spoken while dialing; optional]   (RT=4 only)
  - **Post-execution intent instructions:** [string; optional]   (RT=4 only)
  - **Response success:** [object literal `{ "instructions": "<string>" }`]   (RT=4 only)
  - [for RT=3: no structural fields beyond slots]

### Intent 2: ...

[repeat per intent]

---

## 4.5 Available Variables

### 4.5.1 Call-context variables (platform-supplied)

- `{{caller_phone}}` — caller's incoming number, always present
- `{{TimeNow}}` — current timestamp at call start
- [additional variables per user's account]

[OR if user could not enumerate: defaults above only, plus marker `<INCOMPLETE: user to verify with platform>`]

### 4.5.2 Environment variables (config-time)

- `{{ENV.[NAME]}}` — [description]

[OR if no environment vars: list empty.]

### 4.5.3 Slot variables (auto-derived from section 5)

[Auto-generated. One entry per slot across all intents.]

- `{{slot_name}}` — collected by `<intent_identifier>`, type `<ParameterTypeId name>`

### 4.5.4 API response variables (per RT=2 intent)

[For each RT=2 intent, dotted-path inventory.]

`<intent_identifier>` returns:
- `[dotted.path.to.field]`

---

## 4.6 Global/System Catalog Intents

[Either declare one or more catalog intents below, or replace this entire section with `[none]` if the bot references no global/system intents.]

A global/system catalog intent is a predefined platform intent the bot references rather than authors. It carries **real positive IDs** (`IntentId`, `IntentCategoryId`, `ParameterId`, `IntentScriptId`) and `AccountId: 0`. Skill 3 injects its `**Definition:**` block verbatim — it does NOT renumber the IDs.

### Catalog Intent: [real IntentId] — [Name]

- **Wiring:** [`silence-forward only` (default) | `triggerable global`]
  - `silence-forward only` — injected into `intents[]` and its category merged into `intentCategories[]`, but NOT added to `botIntents[]` / `intentRelations[]` (free-floating; reachable only via `silence_behaviour.intent` or another structural failover field).
  - `triggerable global` — additionally wired into `botIntents[]` (`BotIntentTypeID 2`) and the global fan-out, like transfer-to-human.
- **Definition:**

```json
{ "Name": "...", "IntentId": 19, "AccountId": 0, "IntentCategoryId": 22, "IntentParameters": [], "IntentScripts": [], "IntentResponces": { } }
```

#### Canonical system silence-forward global (`IntentId 19`) — verbatim, captured from a real Voicenter export (Matan bot, 2026-06-23)

This is the platform's default `IsSilenceIntent` system global (`AccountId 0`, category `22` "Sales intents"). When a bot's silence failover would otherwise target a *bot-own* intent (whose placeholder ID does NOT survive import — see Skill 3 §4.2.5), declare THIS block in section 4.6 with `**Wiring:** silence-forward only` and set section 3's `silence failover intent` to `19`. It imports working with no manual step. **It is functionally a dummy** (an RT=2 to `/api/printer-support`) — a generic placeholder to keep the silence forward live; re-point it in the UI to the real human-transfer target afterward if desired. Skill 3 injects it verbatim into `intents[]` and merges category `22` into `intentCategories[]`.

```json
{
  "Name": "Some global Intent",
  "IntentId": 19,
  "IsActive": 1,
  "Priority": 1,
  "AccountId": 0,
  "Description": "Some Dummy Global Intent",
  "MaxAttempts": 3,
  "IntentConfig": {},
  "IntentScripts": [
    { "IsActive": 1, "LanguageCode": "en-US", "ScriptTypeId": 1, "ScriptContent": "I'll help you check your account balance.", "IntentScriptId": 100 },
    { "IsActive": 1, "LanguageCode": "en-US", "ScriptTypeId": 2, "ScriptContent": "Please provide your account number.", "IntentScriptId": 103 }
  ],
  "IntentSources": [],
  "IntentToolName": null,
  "IntentResponces": {
    "IsActive": 1,
    "Configuration": { "method": "POST", "endpoint": "/api/printer-support" },
    "ResponseTypeId": 2,
    "SuccessCondition": null
  },
  "IsSilenceIntent": 1,
  "IntentCategoryId": 22,
  "IntentParameters": [
    {
      "Name": "account_number", "Schema": null, "IntentId": 19, "IsActive": 1, "CreatedBy": "SYSTEM",
      "IsRequired": 1, "ModifiedBy": null, "OptionList": null, "CreatedDate": "2025-01-21 11:25:25",
      "Description": "Customer account number", "ParameterId": 52, "DefaultValue": null, "ModifiedDate": null,
      "ParameterType": { "Name": "INTEGER", "IsActive": 1, "CreatedBy": "SYSTEM", "ModifiedBy": null, "CreatedDate": "2025-01-21 11:25:25", "Description": "Whole number input", "ModifiedDate": null, "ParameterTypeId": 4, "ValidationPattern": "^[0-9]+$", "IsCustomValidationAllowed": 1 },
      "CollectionOrder": 1, "ParameterTypeId": 4, "ValidationRules": { "required": true, "min_length": 5 }
    }
  ],
  "ValidationTimeout": 30,
  "HandlingInstructions": null
}
```

And its category for `intentCategories[]`:

```json
{ "Name": "Sales intents", "IsActive": 1, "AccountId": 0, "PriorityId": 1, "Description": "Sales Intents predefined by the system which everyone can use", "IntentCategoryId": 22 }
```

(The real export also carried a second `data`/JSON parameter on intent 19; it is optional and omitted here to keep the injected block lean. The `account_number` parameter above is sufficient for the import to resolve the silence-forward reference.)

---

## 5. Intent Details

### Intent: [identifier]
**Status:** [structural]
**Reference to section 4:** [pointer to row]

[No further content. Skill 2 fills.]

[repeat per intent]

---

## 6. Cross-References

### 6.1 Mustache variable usage

[For each Mustache reference in any text field:
  - reference: `{{variable_name}}` or `{{path.to.field}}`
  - used in: [intent identifier, field name]
  - resolves via: [section 4.5.X] or [section 5 slot of intent X]]

### 6.2 Intent transition graph

[Flat list of `(origin → next)` pairs, derived from section 4.]

### 6.3 RT=2 API silence pairings

[Per RT=2 intent: the registry entry that pairs with its embedded `api_silence_behaviour`.]

### 6.4 Escalation paths

[Per non-terminal intent: which transition row points to escalation (typically `transfer_to_human`).]

### 6.5 ID assignments (placeholders)

[Per Doc 1 §15.3 Option A: sequential negative integers.
 Per intent: -1, -2, -3, ...]

---

## 7. Generation Metadata

### 7.1 Spec version

1.0.0

### 7.2 Schema reference

- **Doc 1 version:** v1
- **Skill suite version:** v1

### 7.3 Generation log

- [ISO-8601] Skill 1 [greenfield | patch] [summary]

[Append-only. Each skill invocation adds an entry.]

### 7.4 Open unknowns

[Aggregated list of every `<UNKNOWN: ...>` and `<INCOMPLETE: ...>` marker in the spec. Updated whenever the spec changes.]

### 7.5 Pending work

- [count] intents still in `[structural]` state: [list]
- Hard intents pending: [list]
- [Add `[detailed-revisit]` count if any patches have run]

### 7.6 RT=2 API verification log

[Per verified RT=2 intent, one append-only entry:
 - [ISO-8601] [intent identifier] — HTTP [status]; paths confirmed: [comma-separated 4.5.4 dotted paths]; request (redacted): [method] [url], headers [names only], body [Mustache-slot values masked].
 An RT=2 intent with no entry here is unverified and CANNOT be marked `[detailed]` (Skill 2 hard block) — Skill 3 Gate C also refuses to assemble it. Never store raw secrets or PII here.]
