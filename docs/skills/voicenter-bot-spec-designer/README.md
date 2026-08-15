# Skill: `voicenter-bot-spec-designer`

Design the structural skeleton of a Voicenter Bot through a guided interview. Skill 1 in the three-skill pipeline.

> Source: [`plugins/voicenter-bot-builder/skills/voicenter-bot-spec-designer/SKILL.md`](../../../plugins/voicenter-bot-builder/skills/voicenter-bot-spec-designer/SKILL.md)
> Plugin: [voicenter-bot-builder](../../plugins/voicenter-bot-builder.md) · Pipeline phase: **1 / 3**

---

> **Language.** Reply in the user's language: detect what they write — Hebrew→Hebrew, English→English — and mirror it, switching if they switch mid-conversation. This shapes your prose, your questions, and your `AskUserQuestion` option labels only. It does **not** change the artifacts you produce — identifiers, JSON keys, BCP-47 language codes, API field names, and other data stay exactly as specified.

> **Opening.** Your first message greets bilingually so the user knows both languages are available — e.g. *"נוכל להמשיך בעברית או באנגלית — מה נוח לך? / We can continue in Hebrew or English — whichever you prefer."* Then mirror whatever language the user replies in.

## What it does

Produces the **structural skeleton** of an Agent Spec markdown file by interviewing the user. The output, `agent-spec.md`, is the shared artifact the entire pipeline operates on.

Skill 1 fills these spec sections:

| Section | Content |
|---|---|
| 1. Bot Identity | Name, identifier, description, account ID, language, channels, voice, model, created by, max call duration, record agent calls; optional limit fields (v1.13.0): daily limit, daily-limit layer, max-duration layer, limit sentences, `IVRLayerSelect_2`; optional `Negative instructions` (v1.16.0, AI-security never-say field — banner-only, not emitted to the JSON) |
| 2. Persona Bundle | `persona`, voice/chat instructions, opening behavior, opening announcement |
| 3. Caller Silence Behavior | Mandatory (v1.11.0) — 4 silence fields (with defaults) + the silence forward intent |
| 4. Intent List (Structural) | One row per intent — identifier, RT, transitions, slots, RT-specific fields; v1.13.0 adds the staggering fields (`**Captures answer to:**` / `**Asks next:**`) and `**Terminal outcome:**` on RT=1 terminals |
| 4.5 Available Variables | Call-context, environment, slot, API-response, and (v1.13.0) §4.5.5 CustomData-key variable inventories |
| 4.6 Global/System Catalog Intents | Verbatim definitions of referenced platform intents (e.g. silence-forward target id=19), or `[none]` |
| 5. Intent Details | **Stubs only**, marked `[structural]`. Skill 2 fills the rest. |
| 6. Cross-References | Initial pass — Mustache usage, transition graph, escalation paths, ID placeholders |
| 7. Generation Metadata | Spec version, schema reference, generation log, open unknowns, pending work |

Skill 1 explicitly does **not** author per-intent language content (slot validation prompts, post-execution intent instructions, RT-specific announcements) — that's Skill 2's territory. It also does not emit wire-format JSON — that's Skill 3.

---

## When to invoke

- A user wants to **design a new Voicenter bot from scratch** ("design a bot", "create an agent spec", "build a Voicenter bot").
- A user wants to **modify an existing bot** ("patch this bot", "add an intent", "rename the bot's persona", "change the flow graph").
- A user wants to **scope a bot before writing intent content** — Skill 1 produces a complete structural picture before any language work happens.

Trigger phrases the skill responds to: *"design a bot"*, *"create an agent spec"*, *"build a Voicenter bot"*, *"patch this bot"*, *"add an intent"*, *"change the bot's persona"*, *"modify the flow graph"*, or any reference to *"Skill 1"* / *"Agent Spec Designer"*.

---

## Two entry modes

| Mode | Trigger | Behavior |
|---|---|---|
| **Greenfield** | No spec attached | Runs the 4-phase interview from a blank state |
| **Patch** | An `agent-spec.md` is attached or present in the workspace | Extracts current state, asks what to change, applies the change with cascade analysis |

Skill 1 detects the mode automatically and states it to the user. The user can override (forced greenfield with an existing spec attached requires explicit confirmation that prior content will be discarded).

---

## Tool conventions used during the interview

Two tool patterns apply throughout greenfield and patch flows (full detail in SKILL.md §2.4):

**A. Live resource lookup via `voicenter-mcp.list_resources` (recommended default).** For Voicenter platform resources — **Customer Account ID** (Phase 1) and **RT=1 Layer ID** (Phase 4) — Skill 1's default is to call the [voicenter-mcp](../setup/README.md) plugin's `list_resources` tool (with `entityFilter: ["Accounts"]` or `["Layers"]`, `refresh: false`), display the returned list as an id+name table, and prompt via `AskUserQuestion`.

If MCP is unavailable, Skill 1 follows a **3-tier fallback** — never silently skipping to manual entry:

1. **Plugin not installed.** Surfaces this once and prompts via `AskUserQuestion`: *"Install and authenticate now (Recommended)"* or *"Continue with manual entry"*. If the user installs and authenticates, Skill 1 retries the `list_resources` call.
2. **Plugin installed but not authenticated** (OAuth not completed, token expired, or auth/connection error). Prompts via `AskUserQuestion`: *"Authenticate now (Recommended)"* or *"Continue with manual entry"*. If the user authenticates, Skill 1 retries.
3. **User declined or the retry still failed.** Falls back to **text-only mode** — captures the value as free text and uses `<UNKNOWN: …>` if the user doesn't know it. Logs once to section 7.3 with the reason. Skill 1 does not re-prompt for the same MCP step in the rest of the session — once the user opts out, that decision is respected.

**Layer IDs never fall back to `<UNKNOWN>` (v1.20.1).** Two layer IDs are portable across accounts, so an RT=1 terminal always has a usable value even with no MCP:

| Layer | What it is | Offered as the default for |
|---|---|---|
| **`666`** | The built-in **hang-up** layer — present on every account, not user-created, not deletable | Every terminal whose outcome is "end the call": the dedicated silence-forwarding intent, the dedicated API-timeout forwarding intent, the off-topic global terminal, and ordinary end-of-flow terminals |
| **`0`** | The first layer created on every account (exists unless someone deleted it) | Human-transfer terminals, as the last-resort placeholder |

Preference order per terminal: the MCP-fetched layer the user picks (always preferred — an account's real transfer or hang-up layer may carry extra dialplan behaviour), then the outcome-matched portable default above. Which rung was used is logged to section 7.3.

**Why this matters:** bots are routinely designed against one account and imported into another, where an account-specific layer number does not exist. The FK then dangles, and the platform UI renders the raw layer ID instead of the layer name — a symptom easily mistaken for a JSON type bug. Layer IDs are emitted as JSON integers throughout (`"layer": 666`, never `"layer": "666"`); see the [assembler's layer-typing rule](../voicenter-bot-json-assembler/README.md).

The **model and voice catalogs** remain hardcoded in `model-catalog.md` — they are not fetched live.

**B. Menu prompts via `AskUserQuestion`.** Every closed-set choice the user makes during the interview is presented through `AskUserQuestion` — never plain free-text. The iron rule: if the user can answer with one of a fixed set of strings, route through `AskUserQuestion`. Free-text is reserved for genuinely open-ended fields (names, descriptions, free-form text content, integer/numeric values). **Ask exactly one question per turn** — a single `AskUserQuestion` (or one free-text prompt) per message, waiting for the answer before the next; never batch multiple questions into one turn.

Concretely, this covers:

- **Setup** — runtime correction (Single-conversation vs Claude Code), mode override (Greenfield vs Patch), and the discard-existing-spec follow-up when forcing greenfield over an attached spec
- **Phase 1** — channel scope, agent gender (female/male), voice name, caller-silence fields and silence-forward intent (MANDATORY — always configured, no yes/no gate) (the identifier is **not** prompted — silently auto-derived from the Bot Name, transliterating non-ASCII; AI model config is **not** prompted either — silent default)
- **Phase 2** — every "Accept draft / Edit" prompt for `persona`, opening announcement, and opening behavior (elicited in that order as of v1.12.1 — the behavior is authored around the announcement's question); "Accept template default / Override" for inactive channels
- **Phase 2/3 boundary** — pause vs skip Deep Research
- **Phase 3** — Response Type (RT=1/2/3/4); intent-name "Use suggestion / Propose alternative" when reject-and-suggest fires
- **Phase 4** — account selection (live list), layer selection (live list), POST vs GET, dial source (parameter vs static), per-slot `ParameterTypeId` (STRING / PHONE / BOOLEAN / ENUM / Other-fallback) and `IsRequired` (yes/no), RT=2 `silence` fallback intent reference (pick from the existing intent set), RT=4 `record` (yes/no), and the RT=4 rarity-warning confirmation
- **Patch mode §4.5** — cascade confirmation, plus every iron-rule re-prompt during patch
- **Self-validation checklist** — every "Move it?" / "Add one?" / "Add intent or trim persona?" / "Confirm or propose alternative?" / 3-way Mustache resolution prompt
- **§2.4.A MCP fallback** — Install / Authenticate / Continue manually

`AskUserQuestion` automatically adds an **Other** escape so the user can always type a custom value. Recommended options are listed first with *(Recommended)* appended to the label. Lists exceeding 4 items (the menu max) are first shown as a reference table, then prompted with the 3 most likely candidates plus **Other**.

---

## Greenfield mode — four phases

### Phase 1 — Identity, Channels, Model, Caller-silence

Captures section 1 + section 3:

1. **Bot name** (free text, often Hebrew)
2. **Identifier** (snake_case ASCII; used as the JSON filename prefix by Skill 3 — always auto-derived from the Bot Name, never prompted: ASCII names are snake_cased, non-ASCII names are transliterated to Latin then snake_cased)
3. **Description**
4. **Customer Account ID** — Skill 1 calls `voicenter-mcp.list_resources` with `entityFilter: ["Accounts"]` to fetch the live account list, displays it, and prompts via `AskUserQuestion`. Falls back to free-text + `<UNKNOWN: Account ID>` if MCP is not connected.
5. **Primary language** (BCP-47, e.g., `he-IL`)
6. **Channel scope** — `AskUserQuestion` (voice / chat / voice+chat)
7. **Agent gender + voice name** (two prompts, voice only):
   - **a. Agent gender** — `AskUserQuestion` (header: "Agent voice", options: Female / Male). **Always asked explicitly — never inferred from the bot name** (names are frequently unisex; guessing risks offering only male voices when the user wanted a female agent). Written to spec section 1 as `**Agent Gender:**` — a selection aid only, not emitted to the JSON.
   - **b. Voice name** — `AskUserQuestion` presenting **only the voices whose `Gender` matches step (a)** for the active model family (default Gemini; e.g. Female → `Kore`, `Leda`, `Aoede`; Male → `Puck`, `Orus`, `Charon`). `Other` allows any provider-supported string.
8. **AI model config** — **not prompted.** Silently defaults to the canonical model **Gemini 3.1 - LLM driven** (`AIModelConfigID=142`, `AIModelTypeId=21`) per `model-catalog.md`. Overridden only if the user volunteers a different model by name (mapped via the catalog) or supplies raw `AIModelConfigID` + `AIModelTypeId` directly.
9. **Caller silence (mandatory — v1.11.0)** — always configured; Skill 1 does NOT ask Yes/No. It collects the 4 silence fields (each with an accepted default: `silence_duration` 5, `silence_loops` 3, `silence_sentence`, `silence_ending_sentence`), then **explicitly** asks "after the silence loops are exhausted, which intent should the call forward to?". The forward target may be the transfer-to-human `global`, another own intent, or **a global/system catalog intent (e.g. id=19, `AccountId 0`)** declared verbatim in spec section 4.6. Skill 3 emits the choice as `silence_behaviour.intent`; `silence_ending_sentence` defaults to a "transferring you to a representative" line when the target transfers. Section 3 is never `[not configured]`. **Import limitation (v1.11.1, empirically confirmed 2026-06-23):** the Voicenter import does NOT remap placeholder IDs inside `silence_behaviour.intent`, so a *bot-own* target (a placeholder pre-import) cannot survive import — for those, Skill 3 substitutes the canonical system silence-forward global `19` (a positive real id that imports working; re-pointable in the UI). A real catalog/global intent (option c, e.g. `19`) is the only target that imports working with no manual step, so prefer it for a self-contained deployable bot; `silence_behaviour.intent` is never a negative sentinel in normal operation.
10. **Created by** — bot author/owner name (free text). Optional; `AskUserQuestion` (header: "Created by", options: "Skip (default: empty)" / "Provide a name"). Written to spec section 1 as `**Created by:**`. **Purpose:** Skill 3 v1.5.0+ uses this value to populate `IntentParameters[].CreatedBy` (production-required audit field).
11. **Max call duration (seconds)** — integer, default `1200`. `AskUserQuestion` (header: "Max call duration", options: "Use default 1200 *(Recommended)*" / "Set a different value"). Written to spec section 1 as `**Max call duration:**`.
12. **Record agent calls** — boolean, default `false`. `AskUserQuestion` (header: "Record calls", options: "No — do not record *(Recommended)*" / "Yes — record"). Written to spec section 1 as `**Record agent calls:**`. **Note:** Skill 3 emits this as the **string** `"false"` / `"true"` (not a JSON boolean) — production export shape.
13. **Negative instructions (v1.16.0)** — optional free text: the UI's AI Security Settings field for what the agent must never say or commit to (legally, medically, financially — e.g., "never promise a refund", "never give medical advice"). `AskUserQuestion` (header: "Guardrails", options: "Skip — none *(Recommended)*" / "Add never-say rules" with free-text capture). Written to spec section 1 as `**Negative instructions:**`; omitted entirely when skipped. **Not emitted to the wire JSON** (wire field name unverified) — Skill 3 surfaces it as a MANDATORY POST-IMPORT banner step: paste the text into the UI's AI Security Settings → Negative Instructions. Self-validation Check 15 may also relocate must-never-say content here from prompt fields.

### Phase 2 — Persona Bundle

Captures section 2 (the 5-field `prompts` bundle):

- `persona` — identity, role, tone, language, hard constraints
- `voiceInstructions` — pacing, pronunciation, interruption handling
- `chatInstructions` — formatting, message length, emoji policy
- `intentInstructions` — bot-level opening behavior in Conversation Routines style; its first step handles the caller's answer to the opening announcement's question, and it never re-greets or re-asks it (v1.12.1). **IRON RULE extension (v1.13.0, FP-2/FP-4/FP-12):** when the flow staggers off the opening, §2.4 carries the full branch content — including any read-back the caller must hear on the "proceed" branch and the next question the first flow intent will capture; a flow must NOT start with a dedicated yes/no gate intent (the opening question is the last sentence of §2.5 and the yes/no branch lives in §2.4 — enforced by Check 18); any mandated spoken line uses the FP-4 quote convention `<instruction text> : "<verbatim line>"`; and whenever the flow collects a callback/scheduling time, §2.4 must include the canonical FP-12 date/time interpretation block (anchor on `{{todayHe}}`/`{{timeHe}}`; relative time → compute silently; day without hour → ask only `"באיזו שעה ?"`; never re-ask provided info — enforced by Check 21)
- `openingAnnouncement` — the first audible message at pickup; MUST end with a question mark, preferably asking for the first detail the bot collects, e.g. "Who am I speaking with?" (v1.12.1). Elicited **before** the opening behavior, which is authored around it. **Staggered-pipeline note (v1.13.0, FP-2):** the opening question is pipeline question #1 — its answer is captured by the FIRST flow intent's slots, not by any "opening gate" intent; it is recorded as that intent's `**Captures answer to:**`, and a dedicated yes/no intent whose only job is the opening question is forbidden (Check 18)

Iron rules enforced during this phase:

- No channel-specific behavior in `persona` (move voice-isms / chat-isms to the right field)
- No per-intent procedural logic in `persona` (defer to Skill 2)
- No persistent policy embedded in single intents (move to `persona`)
- **Call-wide rules stated ONCE, in persona (v1.13.0, FP-6).** The persona must state, exactly once each: (a) the turn-taking rule — canonical wording: *"You should always act only after the customer answers and only by the instructions you got. You should never act without the customer's specific answer."*; (b) human-rep request handling (what to say via the FP-4 quote convention + where to route) whenever a human-rep `global` exists; (c) disapproval/decline handling (same shape) whenever a decline terminal exists. These rules are NEVER repeated in per-intent fields — enforced by Check 20. Rules (b)/(c) are finalized at the Phase 3→close-out boundary when the globals/terminals are known.

For inactive channels, Skill 1 emits templated defaults from `templates/voice-default.md` or `templates/chat-default.md`, marked `[default — not user-authored]`.

### Phase 2 / 3 boundary — Deep Research nudge

If the transcript triggers any of the four cues in `trigger-detection-rules.md`, Skill 1 offers a Deep Research query the user can run separately and return with findings. The nudge is **opt-in** — the user can skip and proceed.

### Phase 3 — Flow Graph and Intent List

Captures section 4 (intent rows) and section 4.5 stubs (call-context, environment, API-response variables, and — v1.13.0 — the §4.5.5 CustomData keys):

The declared response shape is provisional — Skill 2 hard-verifies it against the live API (a real `curl` returning 2xx with every declared dotted path present) before the RT=2 intent can be detailed; an unverifiable endpoint blocks.

- Elicit the happy path
- Expand fallbacks for each non-terminal intent
- Per-intent capture: identifier (snake_case verb_object), display name, description, RT (1/2/3/4), transitions out (ordered), `**Bot-intent role:**`, hard-intent flag; plus (v1.13.0) the staggering fields and terminal outcome, below

**Description doctrine (v1.13.0, FP-10).** The Description is a **short semantic English label naming the business step** — e.g., "Verification of plan and premia", "confirming health declaration". It is both the LLM's intent-recognition anchor and the name other intents' instructions use for routing (FP-9). **Forbidden:** stage/workflow markers ("Stage 2", "Gate C"), dialogue imperatives ("Ask…", "Read back…", "Explain…"), business logic ("premium may change after further review"). Specific data points belong in slot Descriptions; conversational content belongs in announcement/instructions (Skill 2); business logic belongs in §2.4 or persona. If the user supplies a long descriptive sentence, Skill 1 distills it to the semantic label and confirms. (Check 12's English preference remains advisory; FP-10 recommends English by default.)

**Staggering fields (v1.13.0, FP-2).** While walking the happy path, Skill 1 fills two fields per flow intent: the caller answers question Q(n-1) — asked by the previous intent's announcement or by the opening — and this intent's slots capture that answer; this intent's announcement will ask Q(n). Q(n-1) is recorded as `**Captures answer to:**` and Q(n) as `**Asks next:**` (terminals: `[none — terminal]`; both omitted on globals). Skill 1 records only the question text as a structural pointer — the announcement wording itself is Skill 2 territory.

**Terminal outcome (v1.13.0, FP-8).** For each RT=1 terminal, Skill 1 captures the outcome slot and its **value mode** — *fixed* (one exact string, e.g., `shikuf_status = "הלקוח ביקש נציג אנושי"`), *captured* (save what the customer said), or *dynamic* (text composed per call). The mode is **inferred from the characterization/requirements material the user provided** when it determines the answer; Skill 1 asks (or confirms the inference) only when it doesn't. Written per the two-mode grammar in `spec-skeleton.md` §4.

**Phase 3 iron rules — three new blocking rules (v1.13.0):**

- **Per-outcome terminals (FP-8).** Every distinct call outcome named in the interview gets its OWN RT=1 terminal that owns an outcome slot (`**Terminal outcome:**`) and ends the call in one hop. **Forbidden:** a finalize→end_call two-intent chain; a single intent that computes the outcome via IF/ELSE-IF prose (non-deterministic — depends on LLM recall). On detection, Skill 1 proposes the per-terminal decomposition and blocks until resolved.
- **Status ownership (FP-8).** The outcome/status parameter appears ONLY on terminals. Gates never carry, set, or mention it — an intent can only set its own slots; "Set status_X to …" on a gate is un-executable at runtime. Blocking.
- **Minimal graph (FP-9).** Transitions exist only for the linear happy-path spine + true branches. Exception outcomes (human-rep request, decline/not-confirmed) are `global` terminals reachable from anywhere, driven by the persona's FP-6 call-wide rules — never wire an explicit edge from every gate (reinforces the v1.12.0 no-fan-out rule). Blocking.

**§4.5.5 CustomData keys interview (v1.13.0, FP-11).** Skill 1 asks for the EXACT per-call CustomData keys the pipeline sends with each call (e.g., `firstnamelastname`, `nationalid`, `policies`, `insurer`, `monthlypremiumafterdiscount`) and records them verbatim in §4.5.5 — key names are **never invented**; any `{{placeholder}}` not on the list blocks assembly at Skill 3 check 7. If the user cannot enumerate: `<INCOMPLETE: CustomData keys unverified>`. When the flow reads per-call data or collects a callback time (Hebrew bots especially), Skill 1 also confirms the platform context vars `{{todayHe}}` / `{{timeHe}}` are available and adds them to 4.5.1.

**Bot-intent role field (v1.8.0).** Each section-4 intent carries a `**Bot-intent role:**` field with one of three values:

| Value | Meaning | BotIntentTypeID (Skill 3) |
|---|---|---|
| `entry` | Directly triggerable from the §2.4 opening behaviour | 1 |
| `global` | Triggerable from anywhere (transfer-to-human, WhatsApp); supersedes `entry` | 2 |
| `chained` | Reached only via another intent's transition (default) | omitted from `botIntents[]` |

Skill 1 **infers** roles from context in Phase 3 — it does NOT prompt per-intent. Roles are confirmed in one batch at §3.6 close-out. Authors must NOT hand-author transitions to `global` intents — a `global` is reachable from anywhere via its `botIntents[]` type-2 registration, so no explicit edge is needed (v1.12.0 — Skill 3 no longer fans out edges; FP-9's minimal-graph rule reinforces this).

**Hard-intent criteria** — flag the intent as hard if any one applies:

- RT=2 with more than 3 slots
- Conditional post-execution branching (multiple distinct next-intents driven by API response)
- More than 4 outgoing transitions
- Slots requiring complex validation (multi-step, cross-slot dependencies)

### Phase 4 — Per-intent structural fields

Finalizes section 4 entries with per-RT specifics, generates section 4.5.3 (slot variables), runs an advisory Mustache pre-check, creates section 5 stubs, and (optionally) captures advanced overrides into section 4.7.

Per-RT capture:

| RT | Required fields |
|---|---|
| 1 (Layer transfer) | `Layer:` (int) — Skill 1 calls `voicenter-mcp.list_resources` with `entityFilter: ["Layers"]` and prompts via `AskUserQuestion`. Additionally for terminals (v1.13.0, FP-8): the outcome slot named in `**Terminal outcome:**` must appear in the intent's slot list — typically STRING (ParameterTypeId 1) per FP-13; ENUM (19, with OptionList) only when the slot selects among multiple fixed values |
| 2 (External API) | `URL:`, `Method:` (`AskUserQuestion` POST/GET), `Headers:`, `Body:`, `API silence behavior:` (six sub-fields) |
| 3 (Conversational) | (none beyond slots — RT=3 fields are language-heavy, Skill 2 territory) |
| 4 (Outbound dial) | `Dial source:` (`AskUserQuestion` parameter/static), then `Parameter phone:` OR `Phone1/2/3:`, plus `selectdial_option:`, `NEXT_VO_ID:`, `MAX_DIAL_DURATION:`, `Record:`, optional `Announcement:` / `Loading announcement:` / `Post-execution intent instructions:`, and `Response success:` |

**Max turns / Max turns sentence (per-intent turn cap — v1.5.0, defaults updated v1.13.0):** Skill 1 does NOT ask about these in the interview. Skill 3 applies smart defaults at emission — now inside `IntentConfig.additional` (v1.13.0): RT=2 keeps `max_turns: 15` with the standard Hebrew sentence (`"אני חייב לסיים את השיחה בשלב הזה."`); all other RTs default to `max_turns: 5` with an empty sentence `""`. If a spec author needs to override a specific intent's cap, they can hand-edit spec section 4 with the optional `**Max turns:**` and `**Max turns sentence:**` fields documented in `spec-skeleton.md §4` (e.g., the golden reference sets a Hebrew technical-difficulty fallback sentence on its callback intent).

The RT-specific sub-labels are **bold** in the spec — Skill 3's strict-template parser depends on this exact form. See [Skill 3's parser](../voicenter-bot-json-assembler/README.md#strict-template-parser) for the full grammar.

#### Optional advanced features (§3.5.5 — default: skip, *not required*)

Two runtime features are **opt-in only** in v1 and not part of the default interview:

| Feature | Default | When opted-in |
|---|---|---|
| `ConditionGroupList` (conditional branching on `BotIntent` / `IntentRelated`) | Skill 3 emits `[]`; proc skips cleanly via NULL-guard in `CreateConditionGroups` | Captured under spec **§4.7 Advanced overrides** as a freeform `condition_groups:` block per intent or transition; Skill 3 passes through verbatim |
| `DTMFList` (DTMF keypad routing on `BotIntent` / `IntentRelated`) | Skill 3 omits the key; proc gates with `IS NOT NULL AND JSON_LENGTH > 0` | Captured under spec §4.7 as `dtmf_list:` block; Skill 3 emits a `DTMFList[]` sibling field |

After Phase 4 captures the structural intent set, Skill 1 prompts once via `AskUserQuestion` (header: "Advanced features", options: "Skip — accept defaults *(Recommended)*" / "Configure conditional branching" / "Configure DTMF routing"). The default-skip path is what every existing bot in the catalog uses. Skill 1 does not validate the contents of §4.7 — it's pass-through to Skill 3, which lifts the blocks verbatim into the JSON.

---

## Patch mode

Used when the user wants to modify an existing spec.

**Easy changes** (no detailed-intent reset):

- Edit persona / voiceInstructions / chatInstructions / openingAnnouncement
- Edit non-structural intent metadata (display name, description)
- Add a new intent (enters as `[structural]`)
- Rename an intent identifier (transition refs and Mustache refs auto-update)
- Edit caller-silence configuration
- Expand channel scope (newly-active channel gets templated defaults)
- Edit the §4.5.5 CustomData key list (v1.13.0) — Check 8 re-runs after the edit; Skill 3 check 7 re-validates every `{{reference}}` at assembly
- Edit the §1 limit fields (Daily limit / layers / sentences / `IVRLayerSelect_2`) (v1.13.0)
- Edit the §1 `Negative instructions` field (v1.16.0)

**Hard changes** (cascade reset to `[detailed-revisit]` for affected intents):

- Change an intent's Response Type
- Modify slots (add, remove, reorder, retype)
- Delete an intent
- Modify the transition graph beyond simple reordering
- Edit bot-level opening behavior routing destinations
- Reduce channel scope from two channels to one
- Change an intent's `**Terminal outcome:**` (slot, value, or value mode) (v1.13.0) — the terminal's Skill-2 outcome-value validationPrompt must be redone
- Change an intent's `**Captures answer to:**` / `**Asks next:**` (v1.13.0) — the staggering couples intent N's announcement to intent N+1's capture, so BOTH neighbors' Skill-2 content is affected; the previous and next flow intents join the cascade's affected set

The cascade algorithm walks both Skill-1-territory references (RT=2 body / headers / response-shape inheritance) and Skill-2-territory references (validation prompts and post-execution instructions in `[detailed]` intents). Affected `[detailed]` intents reset to `[detailed-revisit]`; affected `[structural]` intents stay `[structural]`. The user confirms the cascade list before any change applies.

---

## Self-validation checklist

Run on every greenfield close-out and after every patch. 21 checks total — 14 blocking, 6 advisory (Checks 8 + 11–15, of which 11–15 are Compass doctrine), 1 structural-correctness — executed in order. Checks 16–17 are house rules (v1.12.1); checks 18–21 are field-placement doctrine rules (v1.13.0, FP-2/FP-8/FP-6/FP-12). The Compass-doctrine advisories 11–15 are documented in the SKILL.md; the table below lists the core, house-rule, and field-placement checks:

| # | Check | Severity |
|---|---|---|
| 1 | Persona articulates identity, role, tone, language | Blocking |
| 2 | No channel-specific content in persona | Blocking |
| 3 | No per-intent procedural logic in persona | Blocking |
| 4 | No persistent policy embedded in single intents | Blocking |
| 5 | Persona's claimed capabilities ⊆ intent set | Blocking |
| 6 | snake_case verb_object naming on all intents | Blocking |
| 7 | Every non-terminal intent has an escalation transition (auto-satisfied when a `global` intent exists — reachable from anywhere) | Blocking |
| 8 | Mustache references resolve against section 4.5 (4.5.1–4.5.4 + 4.5.5 CustomData keys, v1.13.0) + section 5 slots | Advisory |
| 9 | Active-channel `prompts` fields populated | Blocking |
| 10 | Inactive-channel `prompts` have templated defaults marked | Auto-fix |
| 16 | Opening announcement ends with a question (house rule, v1.12.1) | Blocking |
| 17 | Opening behavior consumes the announcement's answer — no re-greet, no re-ask (house rule, v1.12.1) | Blocking |
| 18 | Opening-gate merge (v1.13.0, FP-2) — no dedicated intent exists only to ask the §2.5 opening question; the question is the last sentence of §2.5, the yes/no branch lives in §2.4, and the first flow intent captures the answer. Proposed restructure: delete the gate, move its branch logic into §2.4. "Keep" is an escape hatch only when the gate does more than the yes/no (justification logged to 7.3) | Blocking |
| 19 | Terminal shape (v1.13.0, FP-8) — every distinct outcome has an owning RT=1 terminal with `**Terminal outcome:**` and its slot in the slot list; no terminal→anything chains (incl. finalize→end_call); no gate references an outcome/status slot it doesn't own; no centralized IF/ELSE outcome computation | Blocking |
| 20 | Persona call-wide rules stated once (v1.13.0, FP-6) — turn-taking rule present (canonical wording); human-rep handling present when a human-rep `global` exists; disapproval handling present when a decline terminal exists; none of them duplicated into per-intent fields | Blocking |
| 21 | Callback date/time machinery (v1.13.0, FP-12) — when any intent collects a callback/scheduling time, §2.4 must contain the `{{todayHe}}`/`{{timeHe}}` interpretation block and 4.5.1 must list `todayHe`/`timeHe` | Blocking (only fires when a callback/scheduling-time slot exists) |

New in v1.13.0: check 8's resolution allowlist extends to §4.5.5, and its warning offers a third possibility — the reference is a real CustomData key missing from 4.5.5 (keys are never invented; if real, it is added to the list).

Blocking failures pause the close-out until the user resolves them. Advisory check #8 records the user's resolution to section 7.3 and continues — Skill 3's check is the authoritative blocking version.

**Global interaction with Check 7.** When the bot has at least one `global` intent, it is reachable from anywhere via its `botIntents[]` type-2 registration, so every non-global intent has an escalation path by construction and Check 7 is automatically satisfied (v1.12.0 — this implicit reachability replaces the v1.8.0 fan-out edges). Check 7 still fires for bots with **no** global intent — those must have explicit escalation transitions, or the user should designate a `global` transfer-to-human.

### Greenfield close-out: role classification (v1.8.0)

Before running the self-validation checklist, Skill 1 proposes a `**Bot-intent role:**` assignment for every section-4 intent using the **Approach-B** algorithm:

- `entry` — each intent that the §2.4 opening-behaviour block (spec section 2.4) routes to directly.
- `global` — each intent the user described as always-available or triggerable from anywhere (transfer-to-human, WhatsApp catch-all). `global` supersedes `entry`.
- `chained` — all others (default).

Roles are **inferred in Phase 3**, not prompted per-intent. They are **confirmed in one `AskUserQuestion`** batch at close-out. On approval, Skill 1 writes the explicit `**Bot-intent role:**` field into every section-4 intent entry. Skill 3 reads the written field verbatim; no inference is re-done at assembly time.

After role confirmation, Skill 1 revisits `silence_ending_sentence`: if a transfer-to-human `global` exists and the current ending sentence describes a hang-up, Skill 1 offers to switch it to a failover-to-representative line.

---

## Output contract

**On greenfield completion:**

- Sections 1, 2, 3, 4, 4.5 fully filled — including (v1.13.0) the §1 limit fields (or defaults), the per-intent staggering fields (`**Captures answer to:**` / `**Asks next:**`), `**Terminal outcome:**` on RT=1 terminals, and §4.5.5 CustomData keys; section 4.6 populated when a catalog intent is referenced, else `[none]`
- Section 5: stub entries per intent, all marked `[structural]`
- Section 6: initial cross-references (subsections 6.1–6.5). Section 6.2 lists the authored `(origin → next)` transition pairs only (v1.12.0 — no fan-out; globals are reachable from anywhere via their `botIntents[]` type-2 registration), so section 6.2 exactly matches what Skill 3 will emit.
- **Section 6.6: Mermaid `flowchart TD` of the intent graph** — generated at close-out, shown to the user with a refinement loop, and embedded in the spec for human comprehension. Skill 3 ignores this section.
- Section 7: spec version, schema reference, generation log entry, unknowns aggregation, pending work
- Optional section 4.7: present iff the user opted in via §3.5.5 (advanced features)

**On patch completion:**

- The modified spec
- Affected intents marked `[detailed-revisit]` (or stay `[structural]`)
- Section 6 regenerated (including 6.6 — the diagram refreshes after every patch)
- Section 7.3 has a new log entry summarizing the patch
- Sections 7.4 and 7.5 updated

### Runtime-specific delivery

| Runtime | Output |
|---|---|
| **Single-conversation** | Full spec returned as the assistant message; handoff hint recommends Skill 2 next |
| **Claude Code** | Spec written to `agent-spec.md` in the workspace; handoff hint recommends Skill 2 |

### Intent flow diagram + refinement loop

Before final emission (and again after every patch), Skill 1 renders the bot as a **Mermaid `flowchart TD`** under spec section 6.6. Each intent is one node; transitions are labeled edges (`success` / `fallback` / `escalation`). Node shapes encode response type:

| RT | Mermaid shape |
|---|---|
| 1 (transfer) | stadium `([ ... ])` |
| 2 (API) | rounded rectangle `( ... )` |
| 3 (conversational) | default rectangle `[ ... ]` |
| 4 (outbound dial) | subroutine `[[ ... ]]` |

Hard intents get a ` ⚑` flag in the label. If section 4.7 declares `dtmf_list:` for a transition, the digits are appended to the edge label.

After rendering, Skill 1 prompts via `AskUserQuestion` (4 options: "Looks good — finalize *(Recommended)*" / "Adjust an intent" / "Adjust a transition" / "Adjust persona / opening behavior"). Any "Adjust" pick routes back to the relevant phase, applies the change, regenerates section 6 (including 6.6), re-runs validation, and re-prompts. The loop is capped at 5 iterations to prevent accidental endless cycles.

Section 6.6 is **for human comprehension only** — Skill 3 ignores it when projecting to JSON. The diagram refreshes automatically after every patch so the user can see the structural impact visually before finalizing.

---

## Soft-cap thresholds

Advisory warnings emitted at greenfield close-out, after intent count is final. No hard refusal at any size — user decides.

| Runtime | Silent | Advisory | Warning |
|---|---|---|---|
| Single-conversation | < 6 | 7–8 | > 8 (consider Claude Code) |
| Claude Code | < 12 | 12–20 | > 20 (consider splitting bot) |

---

## Anti-list — what Skill 1 does NOT do

- Write `validationPrompt` text (Skill 2's territory)
- Write per-intent post-execution `intentInstructions` text (Skill 2's territory)
- Write per-intent `announcement` / `intentLoadingAnnouncement` text (Skill 2's territory) — Skill 1 records only the `**Asks next:**` question text as a structural pointer (v1.13.0)
- Write detailed slot descriptions beyond name + minimum identification
- Run the §15.4 cross-reference pass (Skill 3's territory)
- Emit any wire-format JSON (Skill 3's territory)
- Make creative decisions in patch mode beyond what the user describes
- Discard `[detailed]` content silently — every reset is explicit and confirmed
- Validate the bot at runtime — no testing, no simulation, no behavior check
- Query live data for the model catalog or voice catalog — both remain hardcoded in `model-catalog.md`. (Accounts and layers ARE fetched live via `voicenter-mcp.list_resources` — see the *Tool conventions* section above.)
- Capture `ConditionGroupList` or `DTMFList` as part of the default interview — these are **opt-in only** under spec §4.7. Default-skip emits the safe defaults that every existing bot uses; the proc imports cleanly without them.

---

## v1.5.0 changes

- **Three new Phase 1 questions** added to the interview: `Created by` (optional, populates `IntentParameters[].CreatedBy` audit field), `Max call duration` (default 1200 seconds), `Record agent calls` (default `false`; emitted as a STRING in the JSON — not a JSON boolean).
- **spec-skeleton.md §1** gains three matching new fields. `spec-skeleton.md §4` gains optional `**Max turns:**` and `**Max turns sentence:**` per-intent override fields.
- **Skill 1 does NOT interview for max_turns / max_turns_sentence.** Skill 3 applies smart defaults (RT=2 → `max_turns: 15`, standard Hebrew sentence; other RTs → omit). Spec authors can hand-edit section 4 to override.

---

## v1.8.0 changes

- **`**Bot-intent role:**` field added to section 4** (per intent): `entry` | `global` | `chained` (default `chained`). `entry` = directly triggerable from §2.4 opening behaviour; `global` = triggerable from anywhere (transfer-to-human, WhatsApp); `chained` = reached only via another intent's transition. `global` supersedes `entry`.
- **Approach-B role classification at close-out.** Skill 1 infers roles in Phase 3 (entry = §2.4 routing targets; global = always-available/transfer intents) and confirms them in **one** `AskUserQuestion` batch at §3.6 close-out. NOT prompted per-intent during the interview.
- **No fan-out to globals (v1.12.0).** Authors must NOT hand-author transitions to `global` intents — a `global` is reachable from anywhere via its `botIntents[]` type-2 registration, so no explicit edge is needed (the v1.8.0 auto-fan-out was removed). Skill 1's section 6.2 lists authored transitions only, matching what Skill 3 emits.
- **Caller-silence failover.** When a transfer-to-human `global` intent exists, `silence_ending_sentence` defaults to a "transferring you to a representative" line rather than a hang-up.
- **Check 7 is auto-satisfied** when a `global` intent exists, because the global is reachable from anywhere, giving every non-global intent an escalation path by construction.
- **Section 6.4** (escalation paths): when a global exists, each non-global intent's escalation path is the global itself, reachable from anywhere (no explicit edge; v1.12.0).

---

## v1.13.0 changes

- **New required reading:** `plugins/voicenter-bot-builder/references/field-placement-doctrine.md` (FP-1…FP-13) joins Skill 1's §1 required-reading table. Skill 1 owns FP-2 (structural staggering), FP-8/FP-9 (terminals/graph), FP-10 (Description), FP-11 (CustomData interview), FP-12 (callback block), the persona half of FP-6, and checks 18–21. See *Field-placement doctrine integration* below.
- **Persona iron rule (FP-6):** call-wide rules stated ONCE, in persona — the turn-taking rule (canonical wording), human-rep handling when a human-rep `global` exists, disapproval handling when a decline terminal exists. Never repeated in per-intent fields (Check 20).
- **§3.2.3 staggered-pipeline note (FP-2):** the opening question is pipeline question #1 — captured by the FIRST flow intent's slots, not by an opening-gate intent. **§3.2.4 IRON RULE extension (FP-2/FP-4/FP-12):** staggered branch content lives in §2.4 (read-back + next question); the opening-gate merge rule (no dedicated yes/no gate intent); the FP-4 quote convention for mandated speech; the FP-12 callback date/time block.
- **§3.4.3 per-intent capture:** Description becomes a short semantic English label (no stage markers, dialogue imperatives, or business logic — FP-10); new fields `**Captures answer to:**` / `**Asks next:**` (FP-2 staggering) and `**Terminal outcome:**` with value mode fixed / captured / dynamic (FP-8), the mode inferred from the user's characterization material and asked only when unclear.
- **§3.4.4 three new blocking iron rules:** per-outcome terminals (no finalize→end_call chains, no centralized IF/ELSE status computation), status ownership (status params only on terminals), minimal graph (spine + true branches only; exception outcomes are persona-driven globals).
- **§3.4.5 new interview question:** §4.5.5 CustomData keys — exact keys recorded verbatim, never invented; `{{todayHe}}`/`{{timeHe}}` availability confirmed and added to 4.5.1 when relevant.
- **RT=1 capture:** the terminal outcome slot must appear in the terminal's slot list — STRING per FP-13; ENUM only for multi-value selection.
- **Check 8** allowlist extended to §4.5.5.
- **Checklist grows 17 → 21 checks (14 blocking):** new blocking checks 18 (opening-gate merge), 19 (terminal shape), 20 (persona call-wide rules once), 21 (callback date/time machinery — blocking only when a callback slot exists).
- **Patch mode:** new easy changes (edit the §4.5.5 key list; edit the §1 limit fields); new hard changes (change `**Terminal outcome:**`; change `**Captures answer to:**` / `**Asks next:**` — cascades to both neighbor intents).
- **Anti-list:** Skill 1 does not author `announcement` / `intentLoadingAnnouncement` text; it records only `**Asks next:**` as a structural pointer.
- **spec-skeleton.md:** §1 gains optional limit fields (`Daily limit` default 600, `Daily limit layer` 3, `Max duration layer` 3, `Daily limit sentence` / `Max duration sentence`, `IVRLayerSelect_2` 3); §4 gains optional `**Captures answer to:**` / `**Asks next:**`, `**Terminal outcome:**` (two-mode grammar: quoted ⇒ FIXED, unquoted ⇒ CAPTURED/DYNAMIC), and `**Sensitive:**` (default `false`, emitted to `IntentConfig.additional.sensitive`); new §4.5.5 CustomData-keys section; updated `Description` and `Max turns` / `Max turns sentence` help text (emission now via `IntentConfig.additional`; default `5` for non-RT=2, RT=2 stays `15`).

---

## voice-agent-llm v1.0.3+ runtime notes

**Empty `announcement` fallback.** If an emitted RT=2 `announcement` is empty at runtime, the voice-agent service substitutes the sentinel `[START THE CONVERSATION]` as an LLM instruction telling the bot to open from persona — the literal string is **not** spoken aloud. Skill 1 still asks for the field upstream and Skill 2's Check 10 is blocking on it; the runtime fallback is a production safety net, not an authoring relaxation.

---

## Common pitfalls

- **Hebrew bot names without an Identifier.** Skill 3's filename rule reads section 1 `**Identifier:**`. Pre-v1.0 specs that lack the field fall back to ASCII-folding `**Bot Name:**`, and for Hebrew names that fallback fails → filename becomes `bot-bot-<date>.json`. Skill 1 always populates an identifier by auto-transliterating the Bot Name (e.g. `יובל` → `yuval`), so specs it produces never hit this fallback.
- **Generic "helpful assistant" personas.** Skill 1 blocks at Check 1. Push the user toward concrete identity, role, tone, and language assertions.
- **Voice-isms inside `persona`.** Skill 1 blocks at Check 2 and offers to move them to `voiceInstructions`. Don't argue — accept the move.
- **`<UNKNOWN: ...>` markers used loosely.** They aggregate into section 7.4 and become Skill 3 sentinel entries the user must resolve at import time. Use them deliberately.

---

## Compass doctrine integration

The bot-builder plugin includes a shared doctrine reference at `plugins/voicenter-bot-builder/references/voice-prompt-doctrine.md`, derived from the Gemini Live 3.1 voice agent engineering guideline. Skill 1 owns the structural self-validation checks for five doctrine rules from that catalog.

Checks 11–15 extend the self-validation checklist (see table above) and run at greenfield close-out and after every patch:

| # | Check | Doctrine rule | Severity |
|---|---|---|---|
| 11 | Bot-level prompt fields (`persona`, `voiceInstructions`, `intentInstructions`) authored in English only, even for non-English bots | Rule 3 — English operational | Advisory |
| 12 | Intent `description` fields authored in English | Rule 4 — Intent description in English | Advisory |
| 13 | Bot-level `prompts.intentInstructions` contains a language-lock guardrail (`NEVER infer language from caller name/accent/tone`) located in the final third (recency slot) of the field. | Rule 5 — Recency-slot language-lock guardrail | Advisory |
| 14 | `voiceInstructions` pacing/length directives do not contradict each other (e.g., "speak slowly" + "be concise and fast") | Rule 6 — Contradictory pacing/length | Advisory |
| 15 | `persona` and `intentInstructions` do not contain generic compliance boilerplate copied from policy documents (v1.16.0: the recommended resolution for must-never-say/never-commit content is relocation to the §1 `Negative instructions` field, not removal) | Rule 7 — Generic-policy boilerplate | Advisory |

**Rule-11 mirror on rewritten fields.** When Skill 1 patch mode rewrites any of `persona`, `voiceInstructions`, `chatInstructions`, or `intentInstructions`, it re-runs check 11 (English operational) on the rewritten content before accepting the change. This prevents a patch from accidentally introducing non-English bot-level prompt text.

New Appendix D in the SKILL.md documents the full mapping between self-validation checks 11–15 and their corresponding doctrine rules. See the reference doc for detection methods and fix recipes.

---

## Field-placement doctrine integration (v1.13.0)

A second shared doctrine reference, `plugins/voicenter-bot-builder/references/field-placement-doctrine.md`, joined Skill 1's §1 required-reading table in v1.13.0. Derived from a production root-cause analysis (pipeline-generated bot vs a hand-built, production-validated golden bot), it is the authority on **which prompt field carries which kind of content** — rules FP-1 through FP-13, spanning the three runtime consumers (live voice model, Intent Agent, platform/IVR layer).

Skill 1 owns:

| Rule | Name | Skill 1 hook |
|---|---|---|
| FP-2 | Staggered pipeline (structural half) | §3.2.3 note, §3.2.4 extension, §3.4.3 `**Captures answer to:**` / `**Asks next:**`, Check 18 |
| FP-6 | Call-wide rules once (persona half) | Phase 2 persona iron rule, Check 20 |
| FP-8 | Terminal doctrine | §3.4.3 `**Terminal outcome:**`, §3.4.4 per-outcome-terminals + status-ownership rules, RT=1 slot-list rule, Check 19 |
| FP-9 | Minimal graph | §3.4.4 minimal-graph rule |
| FP-10 | Description doctrine | §3.4.3 Description authoring rule |
| FP-11 | CustomData keys never invented (interview half) | §3.4.5 §4.5.5 interview, Check 8 allowlist |
| FP-12 | Callback date/time interpretation block | §3.2.4 extension, Check 21 |
| FP-13 | ENUM doctrine | Appendix B mapping (single-value outcome slots stay STRING) |

Skill 2 owns FP-3, FP-4, FP-5, FP-7, and the per-intent half of FP-6; Skill 3 verifies via cross-reference checks 16–22.

---

## Related skills

- [voicenter-bot-intent-detail-author](../voicenter-bot-intent-detail-author/README.md) — Skill 2; runs after Skill 1 with the section 5 stubs as input.
- [voicenter-bot-json-assembler](../voicenter-bot-json-assembler/README.md) — Skill 3; runs after Skill 2 once every intent is `[detailed]`.
