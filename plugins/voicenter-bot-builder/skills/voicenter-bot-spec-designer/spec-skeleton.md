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
**Daily limit:** [int; optional (v1.13.0), default 600 — emitted to `AIModelConfig.daily_limit`]
**Daily limit layer:** [int layer ID; optional (v1.13.0), default 3 — emitted to `AIModelConfig.dailyLimitLayerId`]
**Max duration layer:** [int layer ID; optional, default **0** (v1.14.0) — emitted to `AIModelConfig.maxDurationLayerId`. When the MCP is connected, Skill 1 asks the user which layer, offering the live layer list; with no MCP account, silently default 0.]
**Daily limit sentence:** [text; optional (v1.13.0) — spoken when the daily call-duration limit is reached; primary language, persona-gender matched. Skill 3 emits a production-derived English default if omitted.]
**Max duration sentence:** [text; optional — spoken when max call duration is reached. v1.14.0 default (production-derived): `"נראה שהגענו לזמן שיחה מקסימלי, אנא נסה שנית "`. Skill 1 confirms the default with the user in one Phase-1 question (keep or replace); Skill 3 emits the default if omitted.]
**IVRLayerSelect_2:** [int; optional (v1.13.0), default 3 — emitted to `AIModelConfig.IVRLayerSelect_2`]
**Negative instructions:** [free text; optional (v1.16.0) — the UI's AI Security Settings free-text field: what the agent must never say or commit to (legally, medically, financially, etc.). NOT emitted to the wire JSON — the wire field name is unverified; Skill 3 surfaces it as a MANDATORY POST-IMPORT banner step (paste into the UI's AI Security Settings → Negative Instructions). Check 15 relocates must-never-say/never-commit content here instead of recommending removal. Omit when none.]

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

[intentInstructions text in Conversation Routines style. Pre-intent. Routing logic + iron rules. First numbered step handles the caller's answer to the §2.5 opening question; never re-greets or re-asks it. v1.13.0 (FP-2/FP-4/FP-12): when the flow staggers off the opening, this section also carries the branch logic including any read-back and the next question the first flow intent will capture; any mandated spoken line uses the quote convention `<instruction text> : "<verbatim line>"`; whenever the flow collects a callback/scheduling time, include the FP-12 date/time interpretation block anchored on `{{todayHe}}`/`{{timeHe}}`.]

### 2.5 Opening Announcement

[openingAnnouncement text — single short utterance. The first audible message the caller hears. MUST end with a question mark — an engaging question, preferably asking for the first detail the bot collects (e.g., "Who am I speaking with?").]

---

## 3. Caller Silence Behavior

[Caller-silence handling is MANDATORY (v1.11.0) — this section is always populated. Each field has a default the author may accept or override. Defaults: `silence_duration` 5, `silence_loops` 3, `silence_sentence` a polite re-prompt in the primary language, `silence_ending_sentence` a transfer line (if the forward target transfers) or a polite hang-up.]

- **silence failover intent:** [intent identifier from section 4 — the intent to route to when `silence_loops` is exhausted; Skill 3 emits it as `silence_behaviour.intent`. v1.14.0: this is normally the **dedicated bot-own silence-forwarding intent Skill 1 ALWAYS creates** — an RT=1 terminal with `**IsSilenceIntent:** true` whose outcome the user chose (Hang up or Human rep). EXCEPTION: when the user asks for the caller to return to an existing flow intent (e.g., "main menu"), point at that existing intent instead — no new intent is created. A section-4.6 catalog intent's real `IntentId` is allowed only when the user supplies one. If unresolvable: `<UNKNOWN: silence failover intent>`.]
- **silence_duration:** [int seconds]
- **silence_loops:** [int]
- **silence_sentence:** [text, Mustache OK]
- **silence_ending_sentence:** [text. If the failover intent is the transfer-to-human `global`, prefer a "transferring you to a representative" line over a hang-up line. If there is no transfer-to-human global, keep a polite hang-up line.]

---

## 4. Intent List (Structural)

### Intent 1: [snake_case_identifier]

- **Display name:** [human-readable, often Hebrew]
- **Description:** [short semantic English label naming the business step, e.g., "Verification of plan and premia" (v1.13.0, FP-10). This is the LLM's intent-recognition anchor AND the name other intents' instructions use for routing. NO stage/workflow markers ("Stage 2", "Gate C"), NO dialogue imperatives ("Ask…", "Read back…", "Explain…"), NO business logic — data points go to slot Descriptions, conversational content to announcement/instructions.]
- **Tool name:** [same as identifier]
- **Response Type:** [1 | 2 | 3 | 4]
- **Purpose:** [one-line description for human review]
- **Hard intent:** [`true` | `false`]
- **Bot-intent role:** [`entry` | `global` | `chained`; default `chained`. `entry` = directly triggerable from the §2.4 opening behaviour; `global` = triggerable from anywhere (transfer-to-human, WhatsApp). `global` supersedes `entry`. Skill 3 emits `entry`→`BotIntentTypeID 1`, `global`→`2`, `chained`→omitted from `botIntents[]`.]
- **Captures answer to:** [optional (v1.13.0, FP-2) — the question whose answer this intent's slots capture, asked by the PREVIOUS intent's announcement/instructions or by the opening (§2.4/§2.5). Free text. Omit when not applicable (e.g., globals).]
- **Asks next:** [optional (v1.13.0, FP-2) — the question this intent's announcement/instructions will pose for the NEXT intent to capture, or the literal `[none — terminal]`. Free text.]
- **Terminal outcome:** [optional (v1.13.0, FP-8); RT=1 terminals only. Grammar: `<slot_name> = "<exact fixed value>"` (quoted ⇒ FIXED mode), or `<slot_name> = <free-text description of how the value is captured or composed per call>` (unquoted ⇒ CAPTURED/DYNAMIC mode). The named slot must appear in this intent's slot list. Drives Skill 2's outcome-value validationPrompt and Skill 3 check 20.]
- **Sensitive:** [`true` | `false`; optional, default `false`. Emitted to `IntentConfig.additional.sensitive`. v1.14.0 placement rule: `true` ONLY on the intent where the COLLECTION is configured — in the ask-in-N / collect-in-N+1 stagger (FP-2), that is the collecting intent N+1, never the asking intent — and ONLY when the collected data is truly sensitive (ID number, credit card / CVV / expiry / cardholder ID, medical information). When set, the skill ALWAYS proactively informs the user: sensitive-data handling is enabled on this intent for information security — the values can still be used in API calls configured on this same intent, but they will NOT be saved in LOGS/TRACES.]
- **IsSilenceIntent:** [`true` | `false`; optional (v1.14.0), default `false`. Set `true` only on the dedicated silence-forwarding intent (section 3 failover target). Emitted to the intent-root `IsSilenceIntent` as integer 1/0.]
- **Completion status:** [structural]
- **Transitions out:**
  1. [target intent identifier] (success path)
  2. [target intent identifier] (fallback / escalation)
- **Escalation target:** [identifier — typically `transfer_to_human`]
- **Slots:**
  1. [slot_name] — `ParameterTypeId` [N], Required [`true`|`false`], Order [N], OptionList [if ENUM], DefaultValue [optional (v1.16.0) — pre-filled value used when the caller doesn't supply one; most common on BOOLEAN slots (`true`|`false`). Omit when unset — Skill 3 then emits `""`.]
- **Max turns:** [int; optional override, emitted to `IntentConfig.additional.max_turns`. NEVER asked in the interview — the skills decide autonomously. v1.14.0 defaults: `5` for ALL response types; Skill 1 sets `10` on conversation-heavy intents — where extended speaking back-and-forth between the bot and the caller is expected (multi-slot collection, search-with-retries, sensitive-detail collection). The `10` goes on the intent where the actual conversation happens: in the ask-in-N / collect-in-N+1 stagger that is the asking/speaking intent, not automatically the downstream collecting intent. A turn counts each side's utterance; 5 or 10 covers both together.]
- **Max turns sentence:** [string; optional override, emitted to `IntentConfig.additional.max_turns_sentence`. v1.14.0: Skill 2 authors one default sentence per bot, adjusted to the persona's register and grammatical gender, modeled on `"מתנצל אבל נראה שיש לי בעיה מסויימת, אנא נסה שנית מאוחר יותר"` (feminine: `"מתנצלת…"`). If the field is absent, Skill 3 falls back to the masculine model sentence for every RT.]
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
    - fallback intent: [intent identifier from section 4. v1.14.0 default: the **dedicated API-timeout forwarding intent** Skill 1 always creates once per bot (outcome per the user: Hang up or Human rep, RT=1) — unless the user asked for an existing flow intent (e.g., main menu) or overrides per intent.]
  - **Layer:** [int — the real layer number fetched from the MCP (§2.4.A); defaults to 0 (root layer) if omitted]   (RT=1 only)
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

### 4.5.5 CustomData keys (per-call payload)

[Optional section (v1.13.0, FP-11). The EXACT per-call CustomData keys the caller-data pipeline sends, collected from the user during the Skill 1 interview — one per line:]

- `{{key}}` — [meaning]

[NEVER invent keys. If the user cannot enumerate them: mark `<INCOMPLETE: CustomData keys unverified>` — any `{{reference}}` not matching 4.5.1–4.5.5 blocks at Skill 3 check 7. Platform context vars used in prompts (e.g., `{{todayHe}}`, `{{timeHe}}`) belong in 4.5.1. If this section is absent, the CustomData list is empty.]

---

## 4.6 Global/System Catalog Intents

[Either declare one or more catalog intents below, or replace this entire section with `[none]` if the bot references no global/system intents.]

A global/system catalog intent is a predefined platform intent the bot references rather than authors. It carries **real positive IDs** (`IntentId`, `IntentCategoryId`, `ParameterId`, `IntentScriptId`) and `AccountId: 0`. Skill 3 injects its `**Definition:**` block verbatim — it does NOT renumber the IDs.

### Catalog Intent: [real IntentId] — [Name]

- **Wiring:** [`silence-forward only` (default) | `triggerable global`]
  - `silence-forward only` — injected into `intents[]` and its category merged into `intentCategories[]`, but NOT added to `botIntents[]` / `intentRelations[]` (free-floating; reachable only via `silence_behaviour.intent` or another structural failover field).
  - `triggerable global` — additionally wired into `botIntents[]` (`BotIntentTypeID 2`), reachable from anywhere like transfer-to-human (no per-intent fan-out edges; v1.12.0).
- **Definition:**

```json
{ "Name": "...", "IntentId": 42, "AccountId": 0, "IntentCategoryId": 22, "IntentParameters": [], "IntentScripts": [], "IntentResponces": { } }
```

[v1.14.0: the pre-v1.14 "canonical system silence-forward global (IntentId 19)" block was REMOVED. Silence forwarding always targets a dedicated bot-own intent (or a user-chosen existing flow intent) per section 3; catalog intents remain available only for genuinely user-supplied platform intents.]

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
