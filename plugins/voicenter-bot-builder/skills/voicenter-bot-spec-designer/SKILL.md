---
name: voicenter-bot-spec-designer
description: Designs the structural skeleton of a Voicenter Bot via interview. Use this skill when the user wants to create, design, scope, or modify a Voicenter voice/chat bot — phrases like "design a bot", "create an agent spec", "build a Voicenter bot", "patch this bot", "add an intent", "change the bot's persona", "modify the flow graph", or any reference to the Agent Spec Designer / Skill 1 in the Voicenter bot generation pipeline. Produces an Agent Spec markdown file (sections 1-4, 4.5, section 5 stubs, section 6 initial, section 7 init). Two named entry modes — greenfield (no spec attached) and patch (spec attached). Does NOT author per-intent language content (validationPrompt, post-execution intentInstructions) — that's Skill 2 (Intent Detail Author). Does NOT emit wire-format JSON — that's Skill 3 (JSON Assembler).
---

> **Language.** Reply in the user's language: detect what they write — Hebrew→Hebrew, English→English — and mirror it, switching if they switch mid-conversation. This shapes your prose, your questions, and your `AskUserQuestion` option labels only. It does **not** change the artifacts you produce — identifiers, JSON keys, BCP-47 language codes, API field names, and other data stay exactly as specified.

> **Opening.** Your first message greets bilingually so the user knows both languages are available — e.g. *"נוכל להמשיך בעברית או באנגלית — מה נוח לך? / We can continue in Hebrew or English — whichever you prefer."* Then mirror whatever language the user replies in.

# Skill 1 — Agent Spec Designer

This skill produces the **structural skeleton** of an Agent Spec markdown file through interview. It is one of three skills in the Voicenter Bot generation pipeline:

- **Skill 1 (this skill):** structural design via interview → fills spec sections 1, 2, 3, 4, 4.5, 6 (initial), 7 (init); creates section 5 stubs marked `[structural]`.
- **Skill 2 (Intent Detail Author):** language-heavy per-intent content → fills section 5 entries, marks them `[detailed]`.
- **Skill 3 (JSON Assembler & Publish):** mechanical projection of the spec into Bot JSON wire format.

Source of truth is the spec markdown. No skill invents values.

---

## 1. Required reading at invocation

Before any user interaction, load context from these references. Path conventions assume project files are accessible.

| Read | Why |
|---|---|
| Doc 1 §6.B.1 — `prompts` bundle (5 fields) | Skill 1 authors all five |
| Doc 1 §11 — RT=1/2/3/4 cross-RT field summary | Phase 4 per-RT capture |
| Doc 1 §12 — `ParameterTypeId` catalog | Slot type mapping (Appendix B in this file) |
| Doc 1 §13 — Mustache + variable categories | Section 4.5 inventory + advisory check |
| Doc 1 §14.3 — Anti-patterns | Iron rules Skill 1 enforces (Appendix A) |
| Doc 2 §3 — Agent Spec template | What Skill 1 writes |
| Doc 2 §4 — Skill 1 architecture | What Skill 1 does |
| `../../references/voice-prompt-doctrine.md` | Compass doctrine — 13 rules; Skill 1 owns checks 11–15 (rules 3–7) and the rule 11 mirror |

Also load these files from this skill's package:

- `model-catalog.md` — AI model configs + voice catalog (Phase 1)
- `spec-skeleton.md` — empty Agent Spec template
- `trigger-detection-rules.md` — Deep Research nudge triggers (Phase 2/3 boundary)
- `templates/voice-default.md`, `templates/chat-default.md` — inactive-channel templated defaults (Phase 2)

---

## 2. Setup

### 2.1 Detect runtime

| Signal | Runtime |
|---|---|
| Conversation in claude.ai or mobile app, no workspace file system, no `agent-spec.md` accessible | **Single-conversation** |
| Workspace file system available (Claude Code), tool calls to read/write workspace files possible | **Claude Code** |

State the detected runtime to the user, then prompt via `AskUserQuestion` per Section 2.4.B (header: "Runtime", 2 options: the detected runtime *(Recommended)* / the other runtime).

### 2.2 Detect mode

| Signal | Mode |
|---|---|
| Spec file attached (uploaded by user) OR `agent-spec.md` present in workspace | **Patch** |
| No spec file present | **Greenfield** |

State the detected mode to the user, then prompt via `AskUserQuestion` per Section 2.4.B (header: "Mode", 2 options: the detected mode *(Recommended)* / the other mode). If the user picks "Greenfield" while a prior spec is attached, confirm with a follow-up `AskUserQuestion` ("Discard existing spec and start fresh" / "Cancel and stay in Patch mode").

### 2.3 Confirm and start

State both. Confirm the bot's working name (or a placeholder for greenfield). Then proceed to Section 3 (greenfield) or Section 4 (patch).

### 2.4 Tool conventions for the interview

Two tool patterns apply throughout greenfield and patch flows:

**A. Live resource lookup via `voicenter-mcp.list_resources` (recommended default).**

For Voicenter platform resources — **Customer Account ID** (Phase 1) and **RT=1 Layer ID** (Phase 4) — the default behavior is to call `voicenter-mcp.list_resources` (with `entityFilter: ["Accounts"]` or `["Layers"]`, and `refresh: false` unless the user just created the entity), display the returned list as an id+name table, and prompt via `AskUserQuestion` per 2.4.B.

If MCP is unavailable, fall back in this order — **never silently skip to manual entry; always offer to enable MCP first**:

1. **Plugin not installed.** State once: *"voicenter-mcp is not installed. With it I can fetch your live accounts and layers."* Then prompt via `AskUserQuestion` (header: "MCP install", options: "Install and authenticate now (Recommended)" / "Continue with manual entry"). If the user picks Install: instruct `/plugin install voicenter-mcp@voicenter`, then retry the `list_resources` call (which will trigger OAuth on first use).

2. **Plugin installed but OAuth not completed, token expired, or call errors with auth/connection failure.** State once: *"voicenter-mcp is installed but not authenticated."* Then prompt via `AskUserQuestion` (header: "MCP auth", options: "Authenticate now (Recommended)" / "Continue with manual entry"). If the user picks Authenticate: trigger any voicenter-mcp tool to launch OAuth, then retry the `list_resources` call.

3. **User declined the offer in step 1 or 2, OR the retry still failed.** Fall back to **text-only mode** — capture the value as free text. If the user doesn't know it, mark `<UNKNOWN: Account ID>` / `<UNKNOWN: layer ID>`. Log once to section 7.3: *"voicenter-mcp lookup unavailable for [accounts|layers] (reason: [not installed | not authenticated | call error]); captured manually."* Do not re-prompt the user for the same MCP step in the rest of the interview — once they've declined, respect that for the session.

The **model catalog and voice catalog are NOT fetched live** — both remain hardcoded in `model-catalog.md` per decision F.

**B. Menu prompts via `AskUserQuestion`.**

Every closed-set choice the user makes during the interview must be presented through `AskUserQuestion` — never plain free-text. This applies to every "pick one" or "yes/no" step, including (but not limited to):

- Setup §2.1/§2.2 — runtime correction (Single-conversation vs Claude Code) and mode override (Greenfield vs Patch) when the auto-detected value is wrong
- Phase 1 — channel scope, agent gender (female/male), voice name, caller-silence yes/no. (The identifier is **not** prompted — it is silently auto-derived from the Bot Name, transliterating non-ASCII names, per §3.1 step 2. AI model config is **not** prompted either — it silently defaults to Gemini Live 3.1 per §3.1 step 8.)
- Phase 2 — every "Show the draft, confirm or edit" prompt (§3.2.1 persona, §3.2.3 opening behavior, §3.2.4 opening announcement) → "Accept" / "Edit" (Edit branches into free-text capture)
- Phase 2 — "Accept template default or override?" for inactive channels (§3.2.2)
- Phase 2/3 boundary — "Pause for Deep Research or skip and proceed?" (§3.3)
- Phase 3 — Response Type (RT=1/2/3/4); identifier naming when reject-and-suggest fires ("Use suggestion" / "Propose alternative")
- Phase 4 — account selection (from live list), layer selection (from live list), POST vs GET, dial source (parameter vs static), every per-slot `ParameterTypeId` (Appendix B closed enum: STRING / PHONE / BOOLEAN / ENUM / "Other unsupported — STRING fallback"), every per-slot `IsRequired` (yes/no), RT=4 `record` (yes/no), and the RT=4 rarity-warning confirmation ("Yes, this really is an outbound dial" / "No, switch to RT=1 transfer")
- Patch mode §4.5 — "Confirm cascade and proceed?"; every iron-rule re-prompt during patch (mirrors the self-validation prompts below)
- Self-validation Checks 2/3/4 — "Move it?" (yes/no)
- Self-validation Check 5 — "Add an intent for `[capability]`, or trim the persona claim?"
- Self-validation Check 6 — "Use snake_case suggestion `[name]`, or propose your own?"
- Self-validation Check 7 — "Add an escalation transition?" (yes/no)
- Self-validation Check 8 — "Collected upstream / typo for existing variable / different name?" (3 options)
- Section 2.4.A MCP fallback — "Install / Authenticate / Continue manually"

**Iron rule:** if the user can answer with one of a fixed set of strings, route through `AskUserQuestion`. The only acceptable free-text prompts are open-ended ones (names, descriptions, free-form text content, integer/numeric values). **Ask exactly one question per turn:** present a single `AskUserQuestion` (or one free-text prompt) per message and wait for the answer before asking the next. Never batch multiple questions into one turn.

`AskUserQuestion` automatically adds an **Other** escape, so the user can always type a custom value if the displayed options don't cover their case. When a recommended option exists (e.g., the MCP-enable path), put it first and append *(Recommended)* to its label.

`AskUserQuestion` accepts 2–4 options. When a list (e.g., accounts, layers) exceeds 4 items, first display the full list as a reference table, then prompt with the 3 most likely candidates as menu options and rely on **Other** for the long tail.

Free-text capture remains correct for open-ended fields — bot name, identifier, description, persona, intent identifiers, slot names, free-form announcements, integer or numeric values, etc. — where there is no closed option set.

---

## 3. Greenfield mode

Four phases, in order. Phase boundaries are not strict — revisit earlier phases if later answers reveal omissions. The Deep Research nudge falls between Phase 2 and Phase 3.

### 3.1 Phase 1 — Identity, Channels, Model, Caller-silence

**Goal:** populate spec sections 1 and 3.

Ask, in order:

1. **Bot name** (free text, often Hebrew). Required.
2. **Identifier**: ASCII snake_case used as the filename prefix when Skill 3 emits the JSON. **Always auto-derive it from the Bot Name — never prompt.** If Bot Name is pure ASCII, snake_case it (`Customer Support` → `customer_support`). If Bot Name is Hebrew or other non-ASCII, transliterate it to Latin first, then snake_case (`יובל` → `yuval`, `מוקד רפואה` → `moked_refua`). Required. Written to spec section 1 as `**Identifier:**` without asking the user.
3. **Description** (free text). May duplicate the name. Required.
4. **Customer Account ID** (integer, references the Voicenter customer account). Per Section 2.4.A, call `voicenter-mcp.list_resources` with `entityFilter: ["Accounts"]` and display the returned accounts to the user as an id+name table. Then prompt via `AskUserQuestion` per Section 2.4.B (header: "Account"). If MCP is not connected or the user genuinely doesn't know: fall back to free-text capture and mark `<UNKNOWN: Account ID>`.
5. **Primary language** (BCP-47, e.g., `he-IL`, `en-US`). Required.
6. **Channel scope:** voice / chat / voice+chat. Required. Prompt via `AskUserQuestion` per Section 2.4.B (3 options: Voice only / Chat only / Voice + Chat).
7. **If voice active — agent gender, then voice name (two prompts, in this order):**
   - **a. Agent gender.** Prompt via `AskUserQuestion` (header: "Agent voice", 2 options: "Female" / "Male"). **Always ask this explicitly — NEVER infer gender from the bot name.** Names are frequently unisex; guessing risks offering only male voices when the user wanted a female agent (or vice versa). Written to spec section 1 as `**Agent Gender:**`. (Selection aid only — not emitted to the JSON by Skill 3.)
   - **b. Voice name.** Read the `model-catalog.md` voice catalog and prompt via `AskUserQuestion` presenting **only voices whose `Gender` matches step (a)** for the active model family (default Gemini, since the default model is Gemini 3.1 Voice driven). E.g. Female → `Kore`, `Leda`, `Aoede`; Male → `Puck`, `Orus`, `Charon`. Neutral voices (e.g. `alloy`) may appear under either gender. `Other` lets the user supply any provider-supported string.
8. **AI model config: do NOT prompt.** Silently default to the most relevant model — **Gemini Live (Voice driven 3.1)** → `AIModelConfigID=139`, `AIModelTypeId=18` (per `model-catalog.md` canonical default). Write it to spec section 1 without asking. **Override only if the user volunteers a different model** (e.g. "use the OpenAI realtime one" or supplies raw `AIModelConfigID` + `AIModelTypeId`): map by name via `model-catalog.md`, or accept the raw IDs directly. Only mark `<UNKNOWN: AI Model Config>` if the user explicitly defers the choice (e.g. "leave it blank, platform team will fill in").
9. **Caller silence:** prompt via `AskUserQuestion` (Yes / No, header: "Silence handling").
   - If yes: walk the fields — `silence_duration` (seconds, int), `silence_loops` (int), `silence_sentence` (text, Mustache OK), `silence_ending_sentence` (text), and **`silence failover intent`** (an intent identifier). These are free-text, no menu. **Silence-exhaustion failover (D8 — structural):** the `silence failover intent` is the intent the caller is routed to when the loops are exhausted; Skill 3 emits it as `silence_behaviour.intent`. **Default it to the transfer-to-human `global`** when the bot will have one (decided in Phase 3 / §3.4), and default `silence_ending_sentence` to a matching "transferring you to a representative" line rather than a hang-up. If the bot has no transfer-to-human global, ask the author for a target (e.g. an end-call intent) or leave it `<UNKNOWN: silence failover intent>`. Roles are finalized in §3.6 — revisit the default there if the global set changed.
   - If no: mark section 3 `[not configured]`.
10. **Created by:** bot author/owner name (free text). Optional — Skill 1 prompts via `AskUserQuestion` per Section 2.4.B (header: "Created by", 2 options: "Skip (default: empty)" / "Provide a name"). If user picks "Provide a name", capture as free text. Written to spec section 1 as `**Created by:**`. **Purpose:** Skill 3 v1.5.0+ uses this value to populate `IntentParameters[].CreatedBy` in the emitted JSON (production-required audit field).
11. **Max call duration (seconds):** integer. Default `1200`. Prompt via `AskUserQuestion` per Section 2.4.B (header: "Max call duration", 2 options: "Use default 1200 *(Recommended)*" / "Set a different value"). If different, capture as free-text integer. Written to spec section 1 as `**Max call duration:**`.
12. **Record agent calls:** boolean. Default `false`. Prompt via `AskUserQuestion` per Section 2.4.B (header: "Record calls", 2 options: "No — do not record *(Recommended)*" / "Yes — record"). Written to spec section 1 as `**Record agent calls:**`. **Note:** Skill 3 emits this in the JSON as the **string** `"false"` / `"true"` (not a JSON boolean) — production export shape.

**Write at end of Phase 1:** spec sections 1 and 3.

### 3.2 Phase 2 — Persona Bundle

**Goal:** populate spec section 2 (5 fields per Doc 1 §6.B.1).

#### 3.2.1 Elicit identity (`prompts.persona`)

Ask: "Who is this bot? Describe identity, role, company context, tone, language posture, and any hard constraints (e.g., 'Hebrew only, never code-switch')."

Draft a `persona` from the user's answer. Show it, then prompt via `AskUserQuestion` per Section 2.4.B (header: "Persona", 2 options: "Accept draft" / "Edit"). If "Edit", capture the user's revisions as free text and re-prompt with the updated draft until accepted.

**Iron rules during this elicitation:**

| Rule | Source | Action |
|---|---|---|
| Persona must articulate identity, role, tone, language. Not "helpful assistant" generic. | §14.3.1 | If user's input is empty/generic, push back: "What specifically is this bot's identity, role, and language? A persona that doesn't articulate these defaults to generic chatbot behavior at runtime." |
| No channel-specific behavior in persona. | §14.3.9 | Catch voice-isms (pacing, pronunciation, interruption, audio cues) and chat-isms (formatting, message length, emojis). Offer to move them to `voiceInstructions` or `chatInstructions`. |
| No per-intent procedural logic in persona. | §14.3.10 | Catch "when validating address, repeat back..." or "after getting available slots, present in order..." — these are per-intent. Offer to move to per-intent `intentInstructions` (Skill 2 will write the actual text). |
| No persistent policy embedded in single intents. | §14.3.13 | Defer this check to Phase 3 boundary, where intents exist to compare against. But ask now: "Are there any policies that apply call-wide (privacy, GDPR, retention, escalation policy)?" — capture into persona directly. |

**Compass doctrine note (rules 3 and 7).** For non-English bots, the doctrine recommends writing operational prose in English (~3× token savings on the static prompt; preserves function-calling and instruction-following accuracy that degrades in Hebrew/Arabic/CJK). Verbatim utterances the agent must speak stay in the target language. Skill 1's self-validation check 11 fires advisory if a bot-level prompt field is ≥30% non-Latin characters. Independently, check 15 flags generic GDPR/HIPAA/PII boilerplate that isn't derived from the bot's domain — these belong in the data plane (Presidio, dialplan, etc.), not the persona. See `../../references/voice-prompt-doctrine.md` rules 3, 4, 7 for fix recipes.

#### 3.2.2 Elicit channel-specific behavior

For each **active** channel:

- **Voice:** ask about pacing, pronunciation (especially for street names and numbers), interruption handling, audio cues, pauses.
- **Chat:** ask about formatting (markdown vs plain), message length, emoji policy, confirmation patterns.

For each **inactive** channel: emit the templated default automatically per `templates/voice-default.md` or `templates/chat-default.md`. Substitute `[[PERSONA_IDENTITY]]` (extracted from the just-authored persona — first sentence or two establishing identity) and `[[PRIMARY_LANGUAGE]]` (mapped from the language code in section 1 to a human-readable name, e.g., `he-IL` → "Hebrew"). Show the result to the user. Prompt via `AskUserQuestion` per Section 2.4.B (header: "Channel default", 2 options: "Accept default" / "Override").

If user accepts: write to spec preceded by `[default — not user-authored]`.
If user overrides: capture the override; do not include the marker.

#### 3.2.3 Draft `prompts.intentInstructions` (bot-level Opening Behavior)

This is **pre-intent** — what the bot does at the very start of the call, before any specific intent has fired. It contains greeting, routing logic, and disambiguation rules. (Per Doc 1 §14.3.11, this is one of the most-misused fields.)

Ask: "When the call opens, what should the bot do? Greet how, then how does it figure out which intent to route to? What if the caller says something unclear?"

Draft in **Conversation Routines style** (ALL-CAPS headers, numbered steps, IF/ELSE, IRON RULES). Example shape:

```
OPENING BEHAVIOR
1. Greet briefly.
2. Ask what the caller needs.
3. Route based on caller's response:
   - Scheduling → trigger validate_customer_address.
   - Rescheduling → trigger reschedule_existing.
   - General questions → trigger general_inquiry.

IF caller's intent is unclear:
  - Ask once for clarification.
  - If still unclear, route to transfer_to_human.

IRON RULE: Stay in scope. For pricing/billing/technical, route to transfer_to_human.
```

Show the draft, then prompt via `AskUserQuestion` per Section 2.4.B (header: "Opening behavior", 2 options: "Accept draft" / "Edit"). If "Edit", capture revisions as free text and re-prompt until accepted.

**Compass doctrine note (rule 5 — recency-slot language-lock).** The bot-level `intentInstructions` is the recency slot of the assembled systemInstruction (per "Lost in the Middle" + "Found in the Middle" U-shaped attention bias). For non-English bots, a known production bug (Gemini cookbook #1197) causes the model to code-switch based on the caller's name or accent even with English-only instructions. The doctrine's mitigation is to place an extreme negative constraint — equivalent to `"NEVER infer language from caller's name, accent, or tone."` — in the final third of `prompts.intentInstructions`. Skill 1's self-validation check 13 detects whether this constraint is present in the recency slot and, if not, offers to inject the standard line. See `../../references/voice-prompt-doctrine.md` rule 5 for the detection pattern and fix recipe.

#### 3.2.4 Draft `prompts.openingAnnouncement`

This is the **first audible message** the caller hears (Doc 1 §3). One short utterance.

Ask: "What does the caller hear at the moment of pickup?"

Draft and show. Prompt via `AskUserQuestion` per Section 2.4.B (header: "Opening line", 2 options: "Accept draft" / "Edit"). If "Edit", capture revisions as free text and re-prompt until accepted.

**Write at end of Phase 2:** spec section 2 (all five fields).

### 3.3 Phase 2 / Phase 3 boundary — Deep Research nudge

Scan the transcript of phases 1-2 for any of the four trigger cues per `trigger-detection-rules.md`.

- **No cue fires:** silent. Proceed directly to Phase 3.
- **Any cue fires:** activate the nudge.

Nudge mechanic:

1. State: "Based on what you've described, external research could meaningfully inform the flow design. I can construct a research query for you to run separately."
2. Construct the query per the template in `trigger-detection-rules.md` — four sections (3 always populated, 1 conditional based on which trigger fired).
3. Present the query.
4. Prompt via `AskUserQuestion` per Section 2.4.B (header: "Deep Research", 2 options: "Pause and run Deep Research" / "Skip and proceed").
5. If pause: save state per runtime (single-conversation: emit partial spec + query as message; Claude Code: write `agent-spec.md` partial + `research-query.md`). Append to spec section 7.3: `Deep Research nudge offered (triggers: [list]); user paused for research.`
6. If skip: append to spec section 7.3: `Deep Research nudge offered (triggers: [list]); user skipped.` Proceed to Phase 3.

When user returns from research with findings, incorporate into Phase 3 elicitation. Append to 7.3: `Deep Research findings incorporated.`

### 3.4 Phase 3 — Flow Graph and Intent List

**Goal:** populate spec sections 4, 4.5.1, 4.5.2, 4.5.4 stubs.

#### 3.4.1 Elicit happy path

Ask: "Walk me through the bot's primary success path. What does the caller's first turn look like, what happens next, and how does the call end on the happy path?"

From the answer, sketch an initial intent list (rough names + transitions).

#### 3.4.2 Expand fallbacks

For each non-terminal intent in the sketch:

- "If this intent fails or the caller wants out, where does it go?" — typically `transfer_to_human` (RT=1).
- "If the caller asks something unrelated, what happens?" — typically a catch-all `general_inquiry`.

#### 3.4.3 Per-intent capture

For each intent in the list, capture:

- **Identifier:** snake_case verb_object. Skill 1 enforces strictly per §14.3.8 — reject camelCase, kebab-case, spaces, Title Case. Offer a snake_case alternative and prompt via `AskUserQuestion` per Section 2.4.B (header: "Intent name", 2 options: "Use suggested `[snake_case]` *(Recommended)*" / "Propose alternative" — Other captures the alternative as free text).
- **Display name:** human-readable, often Hebrew if bot is Hebrew-language.
- **Description:** plain language, used by the LLM at runtime for intent recognition.
- **Tool name:** same as identifier.
- **Response Type:** prompt via `AskUserQuestion` per Section 2.4.B (header: "Response type", 4 options: "RT=1 — Transfer the call", "RT=2 — Call an external API", "RT=3 — Collect info and continue", "RT=4 — Initiate an outbound dial"). *(Note for cross-referencing the schema: RT=3 is stored as `ResponseTypeId=3` and the DB seed name is "Message" / "Update Bot Configuration" — but operationally, RT=3 is what every conversational data-collection intent uses. Match the operational semantic, not the seed label.)*
  - For RT=4: surface the rarity warning per Doc 1 §11.4: "RT=4 (outbound dial) is uncommon. Confirm you actually need to initiate an outbound call from this intent, not transfer the existing call."
- **Transitions out:** ordered list of (target intent, role). Role is "success path" / "fallback" / "escalation". **Do NOT hand-author transitions to `global` intents** (e.g. transfer-to-human) — Skill 3 auto-generates those edges from every non-global intent (D6). List only flow transitions to entry/chained intents.
- **Bot-intent role:** `entry` | `global` | `chained` (default `chained`). Captured here as a first pass — **infer from context; do NOT prompt the user for this field per-intent during Phase 3.** It is confirmed in one batch at §3.6. `entry` = the §2.4 opening behaviour routes to it directly; `global` = triggerable from anywhere (transfer-to-human, WhatsApp); `chained` = reached only via another intent's transition. `global` supersedes `entry`.
- **Hard-intent flag:** Skill 1 evaluates per the four criteria below; mark `true` or `false`.

**Hard-intent criteria (decision A — flag if any one applies):**

- RT=2 with more than 3 slots
- Conditional post-execution branching (multiple distinct next-intent paths driven by API response)
- More than 4 outgoing transitions
- Slots requiring complex validation (multi-step, cross-slot dependencies)

#### 3.4.4 Iron rules during Phase 3

| Rule | Source | Action |
|---|---|---|
| Every non-terminal intent has at least one transition to an escalation intent. | §14.3.4 | If missing: "Intent `[name]` has no fallback path. Per Doc 1 §14.3.4, every non-terminal intent must have a transition to (typically) `transfer_to_human`. Add one?" Block until resolved. |
| Naming convention: snake_case verb_object. | §14.3.8 | Reject violations; propose snake_case alternative. |
| Persona's claimed capabilities ⊆ intent set. | §14.3.7 | Now possible to check (intents exist). For each capability claim in `persona`, look for a matching intent. If a claim has no matching intent: "Persona claims `[capability]`, but no intent handles that. Either add an intent or trim the persona." Block until resolved. |

#### 3.4.5 Available-variables interview (4.5.1, 4.5.2, 4.5.4 stubs)

Ask:

- **4.5.1 Call-context variables:** "What platform-supplied variables does your account expose at call start? Common entries: `caller_phone`, `TimeNow`, `caller_name`, `account_id`." If the user can't enumerate: emit defaults `caller_phone` and `TimeNow`, mark section `<INCOMPLETE: user to verify with platform>`.
- **4.5.2 Environment variables:** "Are there any deployment-time secrets you'll reference, like `{{ENV.API_TOKEN}}`?" Capture by name. v1 trusts the user's declaration; no validation that the secret exists.
- **4.5.4 API response shapes:** for each RT=2 intent, ask: "What dotted paths will you reference in the API response announcement? E.g., `available_slots.0.display`, `response.order.status`." Capture per intent. The declared shape is **provisional** — Skill 2 hard-verifies it against the live API (real `curl`, 2xx + every declared path present) before the intent can be detailed; an unverifiable endpoint blocks. Skill 3 also validates `announcement` (was `apiResponseAnnouncement` pre-v1.5.0) references against this allowlist.

(Section 4.5.3 is auto-derived from section 5 slots — generated in Phase 4 close-out.)

**Runtime fallback (voice-agent-llm v1.0.3+):** if an emitted RT=2 `announcement` is empty at runtime, the service substitutes the sentinel `[START THE CONVERSATION]` as an LLM instruction telling the bot to open from persona — the literal string is **not** spoken aloud. Skill 2 still requires authored text for RT=2 (Check 10 remains blocking); the fallback is a production safety net, not an authoring choice.

**Write at end of Phase 3:** spec section 4 (intent rows with all structural fields except the per-RT specifics, which Phase 4 fills) and spec section 4.5.1, 4.5.2, 4.5.4.

### 3.5 Phase 4 — Per-intent structural fields

**Goal:** finalize section 4 entries with per-RT structural fields. Create section 5 stubs. Run advisory Mustache pre-check.

#### 3.5.1 Per-RT capture

**For all RTs:** capture slot list — name (free text), `ParameterTypeId` (closed set per Appendix B → prompt via `AskUserQuestion`, header "Slot type", 4 options: STRING / PHONE / BOOLEAN / ENUM, with Other for the unsupported-type fallback path), `IsRequired` (yes/no → prompt via `AskUserQuestion`, header "Required?"), `CollectionOrder` (integer, free text), `OptionList` for ENUM (free-text capture of `{Value, Label}` pairs).

For unsupported types (number, integer, date, email — captured via the `ParameterTypeId` Other branch): emit STRING (ParameterTypeId 1) and flag the slot for Skill 2 to author a `validationPrompt` enforcing format. Note in section 7.3: "Slot `[name]` requires natural-language validation (v1 type fallback: STRING)."

**RT=1:** Layer ID. Per Section 2.4.A, call `voicenter-mcp.list_resources` with `entityFilter: ["Layers"]` and display the returned layers to the user as an id+name table. Then prompt via `AskUserQuestion` per Section 2.4.B (header: "Layer"). If MCP is not connected or the user genuinely doesn't know: fall back to free-text capture and mark `<UNKNOWN: layer ID>`.

**RT=2:**
- URL (user-supplied; `<UNKNOWN: webhook URL>` if not known)
- Method — prompt via `AskUserQuestion` (POST / GET, header: "HTTP method")
- Headers structure (user-described; defaults to `{}`)
- Body structure with Mustache references (user-described)
- API response shape declaration → already captured in 4.5.4 (provisional; Skill 2 hard-verifies it against the live API before the intent can be detailed)
- API silence behavior fields: `silence_duration`, `silence_loops`, `silence_sentence`, `silence_ending_sentence`, `silence_instructions` (text or empty), and **fallback intent reference** — pick from the existing intent set via `AskUserQuestion` per Section 2.4.B (header: "Fallback intent"; show the full intent list as a reference table first if it exceeds 4 items, then top candidates with Other for the long tail)
- **Max turns / Max turns sentence (per-intent turn cap):** Skill 1 does NOT capture these in the interview. Skill 3 v1.5.0+ applies smart defaults at emission — RT=2 gets `max_turns: 15` and the standard Hebrew sentence; other RTs omit. If the spec author needs to override a specific intent's cap (e.g., set RT=1 unrelated-topic to `max_turns: 1` like the transport-planner production sample), they can hand-edit spec section 4 with the optional `**Max turns:**` field documented in `spec-skeleton.md` §4.

**RT=3:** no structural fields beyond slots. Announcement and post-execution `intentInstructions` are language-heavy — Skill 2 territory.

**RT=4:**

Prompt via `AskUserQuestion` per Section 2.4.B (header: "Dial source", 2 options: "Parameter — dial from a slot the caller provided", "Static — dial a hard-coded number"). Capture per **Dial source**:

- **Dial source = parameter** (slot-driven):
  - `parameter_phone`: the slot identifier on this intent that holds the dialed number
  - `selectdial_option`: literal `"Parameter"`
  - phone1/phone2/phone3: emit empty strings `""`

- **Dial source = static** (hard-coded numbers):
  - `phone1`, `phone2`, `phone3`: up to three E.164 numbers with leading `+`. Tried in order; any unused slot is `""`. Per the global E.164 rule (CLAUDE.md house rules), warn the user that elsewhere in Voicenter `+` is forbidden — RT=4 is the exception.
  - `selectdial_option`: capture the user's literal value (the static-mode value isn't documented as a single fixed string; if user doesn't know, emit the key absent and note in 7.4)
  - `parameter_phone`: emit absent

- **Common (both modes):**
  - `NEXT_VO_ID`: int destination voice-objective id; `<UNKNOWN: NEXT_VO_ID>` if not known
  - `MAX_DIAL_DURATION`: integer seconds (typical: 60; free text)
  - `record`: bool — prompt via `AskUserQuestion` per Section 2.4.B (header: "Record call", 2 options: "Yes *(Recommended)*" / "No")
  - `announcement`: optional string spoken just before transfer
  - `intentLoadingAnnouncement`: optional string spoken while dialing
  - `intentInstructions`: optional post-execution string (Skill 2 may elaborate)
  - `response_success`: object literal `{ "instructions": "<string>" }` — guidance text the runtime uses on successful dial

Surface the rarity warning per Doc 1 §11.4 once at intent classification, then prompt via `AskUserQuestion` per Section 2.4.B (header: "Confirm RT=4", 2 options: "Yes — really need outbound dial" / "No — switch to RT=1 transfer"). If the user picks "No", change the intent's RT to 1 and re-capture the RT=1 fields.

#### 3.5.2 Auto-derive section 4.5.3

For each slot captured across all intents, emit a 4.5.3 entry: `{{slot_name}}` — collected by `<intent_identifier>`, type `<ParameterTypeId name>`.

#### 3.5.3 Advisory Mustache pre-check

For every Mustache reference Skill 1 captured (in RT=2 body, headers, response shape declarations, plus any references in persona/intentInstructions/openingAnnouncement from Phase 2 — once 4.5 is populated):

Verify the reference resolves against:
- 4.5.1 (call-context vars)
- 4.5.2 (environment vars)
- 4.5.3 (slot vars)
- 4.5.4 (API response paths, only inside the same RT=2 intent's `announcement` — was `apiResponseAnnouncement` pre-v1.5.0)

If a reference doesn't resolve: warn the user.

> "You referenced `{{customer_name}}` in `[intent.field]` but no slot, call-context variable, or environment variable by that name is in section 4.5. Will it be collected upstream, or is it a typo for a different name?"

This is **advisory, not blocking** — Skill 1 records the user's resolution in section 7.3, then continues. Skill 3's authoritative check is blocking and runs against the same allowlist.

#### 3.5.4 Create section 5 stubs

For each intent: emit a stub of the form:

```markdown
### Intent: <identifier>
**Status:** [structural]
**Reference to section 4:** [pointer to row]
```

No further content. Skill 2 fills the rest.

#### 3.5.5 Optional advanced features (default: skip — *not required*)

The `ImportBotFromJSON` proc supports two runtime features that v1 of Skill 1 does **not** capture as a first-class part of the interview:

| Feature | DB target | Proc behavior when absent |
|---|---|---|
| **`ConditionGroupList`** — conditional branching attached to `BotIntent` and/or `IntentRelated` | `IntentConditionGroup` + `IntentConditions` | `CreateConditionGroups` reads `JSON_LENGTH` of the path; if missing/null, the WHILE loop iterates 0 times — clean skip. |
| **`DTMFList`** — DTMF (keypad-digit) routing attached to `BotIntent` and/or `IntentRelated` | `IntentRelatedDTMF` | Proc gates with `IF v_dtmf_list IS NOT NULL AND JSON_LENGTH(v_dtmf_list) > 0` — clean skip. |

Most bots don't need either. **Default behavior:** Skill 1 emits nothing; Skill 3 emits `ConditionGroupList: []` (current default per Skill 3 §4.3.3 / §4.3.4) and omits `DTMFList`. The bot imports cleanly.

**Opt-in capture:** after section 5 stubs are created (above), prompt **once** via `AskUserQuestion` per Section 2.4.B:

- Header: "Advanced features"
- Options: "Skip — accept defaults *(Recommended)*" / "Configure conditional branching" / "Configure DTMF routing"
- (Other allows the user to type "both" or any custom path.)

If the user picks **Skip**: continue to §3.6 close-out. No additional spec content is written. **This is the default and the recommended path for v1.**

If the user picks **Configure conditional branching** or **DTMF routing** (or both via Other): write a new spec section **4.7 Advanced overrides** with one sub-block per intent or transition the user wants to annotate. The block is **freeform markdown** in v1 — no strict schema. Skill 3 reads section 4.7 verbatim if present and passes it through to the corresponding `botIntents[]` / `intentRelations[]` entry; if absent, Skill 3 falls back to the current empty-default behavior.

Suggested freeform shape (not enforced):

```markdown
## 4.7 Advanced overrides

### Intent: <identifier>
condition_groups:
  - name: <human label>
    type: <IntentConditionGroupType — see DB enum>
    order: <int>
    conditions:
      - <condition spec — freeform>

dtmf_list:
  - <digit string, e.g. "1", "2", "*">

### Transition: <origin> → <next>
condition_groups: [...]
dtmf_list: [...]
```

Skill 1 does NOT validate the contents of section 4.7 in v1 — it's pass-through. The user is responsible for matching the `IntentConditionGroupType` / `IntentConditionRelationType` enums in the DB. Note in section 7.3: "Section 4.7 advanced overrides authored by user; Skill 3 will pass through verbatim."

If section 4.7 is empty or missing (the default), Skill 3 emits the safe defaults and the import proceeds normally.

**Write at end of Phase 4:** spec section 4 finalized; section 4.5.3 generated; section 5 stubs created. If the user opted in, section 4.7 captured; otherwise, section 4.7 is omitted entirely.

### 3.6 Greenfield close-out

1. **Role classification (Approach B, D2/D7).** Propose a `**Bot-intent role:**` for every section-4 intent:
   - `entry` for each intent named as a routing target in the OPENING BEHAVIOR block (spec section 2.4, drafted in Phase 2 §3.2.3).
   - `global` for each intent the user described as always-available / triggerable from anywhere (transfer-to-human, WhatsApp). `global` supersedes `entry`.
   - `chained` for all others.
   Present the full proposed classification in one `AskUserQuestion` (per §2.4 tool conventions) for confirmation; on approval, write the explicit `**Bot-intent role:**` field into every section-4 intent. The inference lives here in Skill 1 — Skill 3 only reads the written field.
   Then revisit §3 `silence_ending_sentence` (D8): if a transfer-to-human `global` exists and the current ending is a hang-up, offer to switch it to a failover-to-representative line.
2. Run the **self-validation checklist** (Section 5 of this SKILL.md).
3. Generate **spec section 6** initial pass:
   - 6.1: Mustache variable usage (every `{{...}}` reference, where used, what it resolves via).
   - 6.2: Intent transition graph — list authored `(origin → next)` pairs AND the **auto-fan-out** edges `(every non-global intent → each global)` so section 6 matches what Skill 3 will emit (D4/D5). Mark fan-out rows with a trailing `[auto: global fan-out]`.
   - 6.3: RT=2 API silence pairings (per RT=2 intent: Skill 3 will pair its embedded `api_silence_behaviour` with an `apiSilenceRelations[]` registry entry; section 6.3 lists which RT=2 intents need pairing).
   - 6.4: Escalation paths — for every non-global intent, the fan-out edge to each `global` is its escalation path. (When a global exists, this also satisfies §5 Check 7 for every intent.)
   - 6.5: ID assignments — placeholders, sequential negative integers per Doc 1 §15.3 Option A. Per intent: `-1`, `-2`, `-3`, ...
   - 6.6: Intent flow diagram (Mermaid) — see §3.6.1 below.
4. Initialize **spec section 7:**
   - 7.1: spec version `1.0.0`
   - 7.2: Doc 1 v1, Skill suite v1
   - 7.3: append the close-out log entry (see Section 6 of this SKILL.md for format)
   - 7.4: aggregate every `<UNKNOWN: ...>` and `<INCOMPLETE: ...>` marker in the spec into a single list
   - 7.5: pending work — count and list of intents in `[structural]` state; list of hard intents
5. **Soft-cap warnings** (Appendix C):
   - Single-conversation: ≥7 intents triggers advisory; >8 triggers "consider Claude Code".
   - Claude Code: ≥12 intents triggers advisory; >20 triggers "consider splitting bot".
6. **Show flow diagram + offer refinement loop** (per §3.6.1 below). Render section 6.6 to the user and prompt via `AskUserQuestion` per Section 2.4.B (header: "Diagram review", 4 options: "Looks good — finalize *(Recommended)*" / "Adjust an intent" / "Adjust a transition" / "Adjust persona / opening behavior"). On any "Adjust" pick: route back to the relevant phase (Phase 3 / Phase 2 / Phase 4), apply the change, **regenerate section 6 (including 6.6)**, re-run the self-validation checklist, and re-prompt the diagram. Loop until the user picks "Finalize" or until 5 iterations elapse (then surface the iteration count in section 7.3 and proceed regardless — avoids accidental infinite loops).
7. **Emit per runtime:**
   - Single-conversation: produce the spec as the response message, plus the handoff hint (Section 6 of this SKILL.md).
   - Claude Code: write to `agent-spec.md` in the workspace, plus the handoff hint.

#### 3.6.1 Intent flow diagram (spec section 6.6)

Skill 1 emits a **Mermaid `flowchart TD`** (top-down) representation of the intent graph at close-out and after every patch. The diagram is for human comprehension and refinement — it is NOT consumed by Skill 3 or the import proc. Skill 3 ignores section 6.6.

**Generation rules:**

1. One node per intent in section 4.
2. Node label: `<identifier><br/>RT=<n> · slots: <count>`. If hard-intent flag is true, append ` ⚑` to the label.
3. Node shape:
   - RT=1 (Layer transfer): stadium shape `([ ... ])`
   - RT=2 (External API): rounded rectangle `( ... )`
   - RT=3 (Conversational): default rectangle `[ ... ]`
   - RT=4 (Outbound dial): subroutine shape `[[ ... ]]`
4. One directed edge per transition in section 4. Edge label: the transition role (`success`, `fallback`, or `escalation`).
5. If section 4.7 (advanced overrides — §3.5.5 opt-in) declares `dtmf_list:` for a transition, append the DTMF digits to that edge's label as ` · DTMF: <digits>`.
6. Mark intents with no outgoing transitions as terminal (no special syntax — they're naturally leaf nodes; the platform handles termination).
7. Wrap the diagram in a fenced Mermaid block under `## 6.6 Intent flow diagram` in the spec.

**Example output:**

```markdown
## 6.6 Intent flow diagram

\`\`\`mermaid
flowchart TD
    answer_product_question[answer_product_question<br/>RT=3 · slots: 1] -->|success| initiate_purchase
    answer_product_question -->|fallback| transfer_to_human
    initiate_purchase(initiate_purchase<br/>RT=2 · slots: 3 · ⚑) -->|success| transfer_to_human
    initiate_purchase -->|fallback| transfer_to_human
    transfer_to_human([transfer_to_human<br/>RT=1])
\`\`\`
```

Identifiers used as Mermaid node IDs must be valid Mermaid syntax — snake_case identifiers comply directly. If an identifier ever contains characters Mermaid rejects (it currently shouldn't, since §14.3.8 enforces snake_case), substitute a stable hash and emit the original identifier in the label only.

**Patch-mode regeneration.** After every patch (§4.6), regenerate section 6.6 from the modified section 4. Show the new diagram alongside the cascade summary so the user sees the structural impact visually before confirming.

---

## 4. Patch mode

Skill 1 enters patch mode when invoked with a prior spec attached.

### 4.1 Pre-flight: extract from existing spec

Skill 1 must extract the following. If any extraction fails (header missing, unrecognizable format), report what couldn't be extracted and refuse to enter patch mode — instruct the user to fix the spec or restart greenfield.

| Source | Extracts |
|---|---|
| `## 1. Bot Identity` | bot name, primary language, channel scope, account ID, model config (catalog name or raw IDs) |
| `## 2. Persona Bundle` (subsections 2.1–2.5) | each `prompts` field, plus inactive-channel `[default — not user-authored]` markers |
| `## 3. Caller Silence Behavior` | the silence failover intent + 4 silence fields, OR the marker `[not configured]` |
| `## 4. Intent List (Structural)` — per `### Intent N: <identifier>` | identifier, display name, description, tool name, RT, hard-intent flag, transitions out (ordered), escalation target, slots, RT-specific fields |
| `## 4.5 Available Variables` (subsections 4.5.1–4.5.4) | each variable inventory |
| `## 5. Intent Details` — per `### Intent: <identifier>` | the `**Status:**` marker (`[structural]`, `[detailed]`, `[detailed-revisit]`) |
| `## 7. Generation Metadata` | 7.4 unknowns, 7.5 pending |

This is **not** a full strict-template parse (that's Skill 3's responsibility). Skill 1 needs only enough extraction to operate the patch workflow.

### 4.2 Surface current state

Brief summary:

```
Bot: <name> (<primary language>)
Channels: <voice|chat|voice+chat>
Intents: <total>; status breakdown — <structural N> / <detailed M> / <detailed-revisit K>
Hard intents: <count>; identifiers <list>
Open unknowns: <count from 7.4>
```

### 4.3 Elicit change

"What do you want to change?" Plain language. No template required.

### 4.4 Classify the change

**Easy-change taxonomy** (no detailed-intent reset):

- Edit `prompts.persona` (section 2.1 only)
- Edit `prompts.voiceInstructions` or `prompts.chatInstructions`
- Edit `prompts.openingAnnouncement`
- Edit non-structural intent metadata (display name, description, priority, max attempts, validation timeout)
- Add a new intent (enters as `[structural]`; existing intents untouched)
- Rename an intent identifier — Skill 1 updates all transition refs and Mustache refs; existing `[detailed]` content stays since the underlying logic is unchanged
- Edit caller-silence configuration
- Edit channel scope from one channel to two (newly-active channel gets templated defaults)

**Hard-change taxonomy** (cascade reset required — see 4.5):

- Change an intent's Response Type
- Modify an intent's slots (add, remove, reorder, retype)
- Delete an intent
- Modify the transition graph beyond simple reordering
- Edit `prompts.intentInstructions` (bot-level) routing destinations
- Change channel scope from two channels to one

If the change spans both categories: classify as hard.

### 4.5 Compute cascade impact (hard changes only)

```
affected_set = { directly_modified_intent }

REPEAT until no change in affected_set:

  FOR each intent I in section 5 (regardless of status):

    # Skill-2-territory references — only inspectable on [detailed] / [detailed-revisit]:
    IF I.status IN { [detailed], [detailed-revisit] }:
      IF I.validationPrompt text references any field of any intent in affected_set:
        add I to affected_set
      IF I.intentInstructions text references any transition involving any intent in affected_set:
        add I to affected_set

    # Skill-1-territory references — inspectable on any RT=2 intent regardless of status:
    IF I.RT == 2:
      IF I's body, headers, OR response_shape references any slot owned by an intent in affected_set:
        add I to affected_set

For each intent in affected_set (excluding the directly-modified one):
  IF status == [detailed]: set to [detailed-revisit]
  IF status == [structural]: leave as [structural] (it has nothing to invalidate)
  IF status == [detailed-revisit]: leave as [detailed-revisit]

For the directly-modified intent itself:
  IF the change is a hard structural change to its own definition: set status to [detailed-revisit] if it was [detailed], else leave.
```

Surface to user:

> "This change affects the following intents: `[A, B, C]`. Of those, `[A, B]` reset from `[detailed]` to `[detailed-revisit]` (you'll redo their detailing in Skill 2). `[C]` stays `[structural]` (no detailing existed yet)."

Then prompt via `AskUserQuestion` per Section 2.4.B (header: "Apply patch?", 2 options: "Apply with cascade *(Recommended)*" / "Cancel"). If the user picks Cancel: do not apply.

### 4.6 Apply the change

- Edit affected fields in sections 1, 2, 3, 4, 4.5, or section 5 stubs as the change requires.
- Update intent statuses per the algorithm.
- Re-run iron rules against the modified spec — same as greenfield close-out:
  - Persona-claims-vs-intents (§14.3.7): if a deletion removed an intent that the persona claimed, surface inconsistency.
  - Escalation-transition existence (§14.3.4): if a deletion broke an escalation path, surface and ask for a replacement.
- Update section 6 cross-references (regenerate from sections 4-5).
- **Regenerate section 6.6** (intent flow diagram) per §3.6.1.
- Append to section 7.3: a log entry summarizing the patch.
- Update section 7.4 and 7.5.

### 4.7 Output

- Run the **self-validation checklist** (Section 5 of this SKILL.md).
- **Show updated flow diagram + offer refinement loop** per §3.6.1. Render section 6.6 alongside the cascade summary so the user can see the structural impact of the patch visually before final emission. Prompt via `AskUserQuestion` per Section 2.4.B (header: "Diagram review", 4 options: "Looks good — finalize *(Recommended)*" / "Adjust an intent" / "Adjust a transition" / "Adjust persona / opening behavior"). On any "Adjust" pick: route back to §4.3 with the new change request, re-run the cascade analysis (§4.5), regenerate sections 6 and 6.6, re-validate. Same 5-iteration cap as greenfield.
- Emit per runtime:
  - Single-conversation: produce the modified spec as the response message.
  - Claude Code: write the modified spec back to `agent-spec.md`.
- Confirm the patch is applied and section 7.3 has the new entry.

### 4.8 Patch-mode iron rules

- Never discard `[detailed]` content silently. Every reset is explicit and confirmed in 4.5.
- Never invent values to fill gaps introduced by a deletion. Mark `<UNKNOWN>` and surface in 7.4.
- Never create or modify intent content that's Skill 2's territory (`validationPrompt`, post-execution `intentInstructions`).

---

## 5. Self-validation checklist

Run on **every greenfield close-out** and **after every patch**, before declaring the spec ready.

15 checks total: 8 blocking, 6 advisory (Checks 8 + 11–15, of which Checks 11–15 are Compass doctrine), 1 structural-correctness.

Execute in the order below.

### Check 1 — Persona articulates identity, role, tone, language (§14.3.1) — blocking

**Trigger:** `prompts.persona` is empty, generic ("helpful assistant"), or missing one or more of: identity, role, tone, language.

**Failure message:**
> The persona doesn't articulate `[missing element(s)]`. A bot persona must include identity, role, tone, and language at minimum. Empty or generic personas default to generic chatbot behavior at runtime, and code-switch languages mid-call. (Doc 1 §14.3.1.)

**Remediation:** revise persona; re-check.

### Check 2 — No channel-specific content in persona (§14.3.9) — blocking

**Trigger:** `prompts.persona` contains references to pacing, pronunciation, interruption, audio cues (voice-isms), OR formatting, message length, emojis (chat-isms).

**Failure message:**
> The persona contains channel-specific content: "[quoted snippet]". This belongs in `voiceInstructions` (or `chatInstructions`), not `persona` — `persona` is in position 1 of the assembled prompt and runs on every channel. Move it?

**Remediation:** offer to move; on confirmation, edit both fields.

### Check 3 — No per-intent procedural logic in persona (§14.3.10) — blocking

**Trigger:** `prompts.persona` references specific intents or per-intent procedural steps ("when validating address...", "after getting available slots...").

**Failure message:**
> The persona contains per-intent procedural logic: "[quoted snippet]". `persona` runs on every assembled prompt; per-intent logic belongs in the intent's post-execution `intentInstructions` (Skill 2 will author that text). Move it?

**Remediation:** offer to extract; on confirmation, remove from persona and stage a note for Skill 2 about which intent should carry the logic.

### Check 4 — No persistent policy embedded in single intents (§14.3.13) — blocking

**Trigger:** an intent's Skill-1-captured fields (e.g., RT=2 body, RT=4 announcement) contain policy that should apply call-wide (privacy, GDPR, retention, escalation policy, scope-out rules).

**Failure message:**
> Intent `[name]` contains policy that applies to the whole call: "[quoted snippet]". Persistent policy belongs in `persona`, not a single intent — otherwise it's only in scope when that intent is active. Move it?

**Remediation:** offer to move to persona; remove from intent.

### Check 5 — Persona's claimed capabilities ⊆ intent set (§14.3.7) — blocking

**Trigger:** `persona` claims capability X, but no intent handles X.

**Failure message:**
> Persona claims to "[capability]", but no intent is defined to handle that. Either add an intent or trim the persona claim. (Doc 1 §14.3.7 — overpromising leads to hallucinations at runtime.)

**Remediation:** user picks one; act on choice.

### Check 6 — snake_case verb_object naming on all intents (§14.3.8) — blocking

**Trigger:** any `IntentToolName` not in snake_case verb_object form (e.g., camelCase, kebab-case, spaces, Title Case).

**Failure message:**
> Intent identifier "[bad name]" doesn't follow snake_case verb_object. Suggested: "[snake_case suggestion]". Confirm or propose alternative?

**Remediation:** rename; update all transition refs and Mustache refs.

### Check 7 — Every non-terminal intent has escalation transition (§14.3.4) — blocking

**Trigger:** a non-terminal intent (RT ≠ 1, OR RT=1 but not an explicit transfer) lacks at least one transition pointing to an escalation intent.

**Failure message:**
> Intent `[name]` has no escalation path. Per Doc 1 §14.3.4, every non-terminal intent must have a fallback (typically `transfer_to_human`). Add one?

**Remediation:** user supplies escalation target; transition is added.

**v1.8.0 interaction:** when the bot has a `global` intent, the auto-fan-out (every non-global intent → each global) provides each intent's escalation transition by construction, so Check 7 is satisfied automatically. Check 7 still fires for bots with **no** global intent — those must author explicit escalation transitions, or the user should designate a `global` transfer-to-human.

### Check 8 — Mustache references resolve against section 4.5 + section 5 slots (§14.3.5) — **advisory**

**Trigger:** a Mustache `{{...}}` reference doesn't resolve against:
- 4.5.1 (call-context)
- 4.5.2 (environment)
- 4.5.3 (slots)
- 4.5.4 (API response paths, scoped to the same RT=2 intent's `announcement` — was `apiResponseAnnouncement` pre-v1.5.0)

**Warning message:**
> Reference `{{[name]}}` in `[intent.field]` doesn't resolve against section 4.5. Possibilities: (a) it's collected upstream and I missed it, (b) it's a typo for an existing variable, (c) it's a different name. Which?

**Action:** record the user's resolution to section 7.3. Continue. Skill 3's check is blocking — this is the early-warning version.

### Check 9 — Active-channel `prompts` fields populated (§14.3.1) — blocking

**Trigger:** a channel marked active in section 1 has empty `prompts.{voice,chat}Instructions`.

**Failure message:**
> Channel `[voice|chat]` is marked active but `prompts.[name]` is empty. Author content for that channel.

**Remediation:** revisit Phase 2.2 for the missing channel.

### Check 10 — Inactive-channel `prompts` have templated defaults marked (decision D) — structural-correctness (auto-fix)

**Trigger:** a channel marked inactive in section 1 has `prompts.[name]` empty (no template emitted) OR has template content not marked `[default — not user-authored]`.

**Action:** auto-fix — emit the template if missing, add the marker if missing. Log to 7.3: "Auto-applied templated default for inactive channel `[name]`."

No user prompt required.

### Check 11 — English operational prose for non-English bots (Compass rule 3) — advisory

**Trigger:** Skill 1 inspects each of `prompts.persona`, `prompts.voiceInstructions` (if voice active), `prompts.intentInstructions`. For each field, count non-Latin script characters (Hebrew U+0590–U+05FF, Arabic U+0600–U+06FF, CJK ranges). If a field is ≥30% non-Latin AND section 1's `Primary Language` ≠ `en-US` / `en-GB` / `en-AU` / similar: fire.

**Failure message:**
> The `[field name]` is ≥30% Hebrew/Arabic/CJK characters. Per Compass rule 3, non-Latin scripts tokenize ~3× more densely than English — operational instructions written in English save substantial tokens (the assembled prompt is paid in full on every Gemini Live 3.1 session start; there is no context caching). The model handles English-instruction / target-language-utterance as a stable cross-lingual generation task. Would you like to:
>   (a) Rewrite the operational prose in English while preserving the target-language utterances on their own lines? *(Recommended)*
>   (b) Keep as-is and continue.

**Remediation:** if (a): draft an English rewrite, show to user, capture revisions, replace the field on confirmation. Then trigger check 11-mirror (rule 11) on the rewritten field. If (b): record the decision in section 7.3 — `Compass rule 3 (English operational) advisory fired on [field]; user kept original.`

**Gating:** applies when section 1's `Channels Active` includes `voice`. Skips silently otherwise (with a one-time 7.3 log entry per spec — see §4.2 of the spec doc).

**Mirror — Hebrew-utterance isolation on rewritten fields (Compass rule 11):** when the user accepts an English rewrite per (a) above, Skill 1 immediately re-scans the rewritten text using the same regex Skill 2 applies for rule 11: `[֐-׿؀-ۿ一-鿿぀-ゟ゠-ヿ]+` inside a line whose remaining non-whitespace content is ≥50% ASCII alphanumerics. If a line contains inline RTL Hebrew/target-language characters next to ASCII English (rather than on its own line or inside quotes), block the rewrite and surface: *"The rewritten `[field]` has inline RTL content on line `[N]`. Per Compass rule 11, RTL must live on its own line or inside quotes — Unicode bidi marks tokenize to garbage when mixed inline with LTR. Adjust the line and confirm again."* User edits; Skill 1 re-checks. This mirror is **blocking** for the rewrite step only — if the user picks (b) and keeps the original (non-rewritten) content, the mirror does not fire.

### Check 12 — Intent description in English (Compass rule 4) — advisory

**Trigger:** for each intent in section 4, inspect the `Description` field. If ≥30% of `Description` characters are non-Latin: fire.

**Failure message:**
> Intent `[identifier]`'s Description is ≥30% non-Latin characters. Per Compass rule 4, the Gemini function-calling layer is English-trained, and non-English tool descriptions degrade intent selection accuracy at runtime. The Display Name can stay in the target language (it's user-facing); the Description is consumed by the LLM. Would you like to:
>   (a) Rewrite the Description in English? *(Recommended)*
>   (b) Keep as-is and continue.

**Remediation:** if (a): draft and replace on confirmation. If (b): log to 7.3.

**Gating:** `[any voice]`.

### Check 13 — Recency-slot language-lock guardrail (Compass rule 5) — advisory

**Trigger:** apply only when section 1's `Primary Language` is not English. Inspect `prompts.intentInstructions` text. Apply the regex pattern `(?i)(infer|switch|change).*(language|לשון|לעבור)` OR `(?i)(name|accent|tone).*(language|לשון)`.

- If a match exists and is located in the final third (≥66% of total character offset) of the text: pass; no warning.
- If a match exists earlier in the text: warn — "the guardrail is present but not in the recency slot."
- If no match: warn — "no language-lock guardrail detected."

**Failure message (no match case):**
> The bot-level `prompts.intentInstructions` has no language-lock guardrail. Per Compass rule 5 and the cookbook #1197 production bug, Gemini Live can code-switch based on caller name/accent even with English-only instructions elsewhere in the prompt. The mitigation is a recency-slot constraint such as:
>
>   `IRON: NEVER infer language from caller's name, accent, or tone. Speak only the bot's primary language.`
>
> (For a Hebrew bot, equivalent Hebrew text in its own line.) Would you like to:
>   (a) Append the standard guardrail at the end of `prompts.intentInstructions`? *(Recommended)*
>   (b) Skip and continue.

**Failure message (match-but-not-in-recency case):**
> The language-lock guardrail in `prompts.intentInstructions` is present but located at character offset `[N]` of `[total]` ([percent]%). Per Compass §4 "Found in the Middle" + Gemini prompting guidance, negative constraints belong at the end of the instruction. Would you like to move it to the recency slot? *(Recommended yes)*

**Remediation:** on user opt-in: inject the standard line or move the existing match to the end. Log resolution to 7.3.

**Gating:** `[any voice; especially recommended for non-English bots]`.

### Check 14 — Contradictory pacing/length (Compass rule 6) — advisory

**Trigger:** concatenate `prompts.persona` and `prompts.voiceInstructions`. Apply both patterns: tone descriptor regex `(?i)\b(warm|conversational|friendly|relaxed|easygoing|easy-going|patient)\b` AND length-constraint regex `(?i)\b(\d+|one|two)\s*(sentence|sentences|words|line|lines)\s*(max|maximum|or less|or fewer|at most)\b`. Fire if both match within the same field or across fields.

**Failure message:**
> The persona/voice instructions combine a tone descriptor ("[matched tone]") with a strict length constraint ("[matched length]"). Per Compass §5 anti-pattern "Contradictory pacing/tone" and the ConInstruct benchmark (arXiv 2511.14342), this produces friendly preambles that consume the length budget before answering, and response length variance balloons across turns. Pick one primary tone and define an explicit, non-conflicting length bound — e.g., "Default: 1–2 sentences. Use brief affirmations like 'יהי' for soft acknowledgment within longer turns."

**Remediation:** advise rewrite; do not auto-resolve. User confirms with revised text or accepts the warning and continues. Log resolution to 7.3.

**Gating:** `[any voice]`.

### Check 15 — Generic-policy boilerplate (Compass rule 7) — advisory

**Trigger:** case-insensitive substring search across `prompts.persona`, `prompts.voiceInstructions`, `prompts.intentInstructions`, and all per-intent `validationPrompt` fields. v1 stem list: `gdpr`, `hipaa`, `pii`, `personally identifiable`, `medical advice`, `legal advice`, `financial advice`, `we do not store`, `we do not retain`, `data retention`, `do not provide professional`. Fire if any stem matches.

**Failure message:**
> Detected generic-policy boilerplate `"[matched stem]"` in `[field]`. Per Compass §2 anti-list ("generic content-policy lists"), the prompt cannot enforce GDPR/HIPAA/PII compliance — these belong in the data plane (Presidio redaction, dialplan recording-consent gating, SIEM audit). Putting them in the prompt is "a liability waiting to surface in your next HIPAA audit" (Prediction Guard analysis cited in Compass). Two paths:
>   (a) Confirm the boilerplate is appropriate to this bot's domain (e.g., medical-domain bot rightly mentions HIPAA) and keep it.
>   (b) Remove the boilerplate and rely on platform-side controls (or accept that prompt-side enforcement is probabilistic).

**Remediation:** record user's decision per match in 7.3 — `Compass rule 7 advisory: stem "[X]" in [field] — user kept|removed`. Do not auto-remove.

**Gating:** `[any]`.

---

### Severity-handling rules

- **Blocking failures:** do not declare the spec ready until the user resolves them. Each failure is surfaced one at a time, in order, with the exact failure message above.
- **Advisory failures:** record the user's resolution in 7.3, continue. Do not block.
- **Structural-correctness:** auto-fix; log to 7.3; continue.

---

## 6. Output contract

### 6.1 What Skill 1 writes to the spec

**On greenfield completion:**
- Sections 1, 2, 3, 4, 4.5 fully filled
- Section 5: stub entries per intent, all marked `[structural]`
- Section 6: initial pass (subsections 6.1–6.5) derived from sections 4-5
- Section 6.6: Mermaid `flowchart TD` of the intent graph (per §3.6.1) — for human comprehension; not consumed by Skill 3 or the import proc
- Section 7: initialized — version, schema reference, generation log entry, unknowns aggregation, pending work
- Optional section 4.7: present iff the user opted in via §3.5.5 (advanced features)

**On patch completion:**
- The modified spec
- Affected intents marked `[detailed-revisit]` (or `[structural]` if they were already `[structural]`)
- Section 6 regenerated (including 6.6 — the diagram refreshes after every patch)
- Section 7.3 has a new log entry summarizing the patch
- Section 7.4 updated with new unknowns introduced by the patch
- Section 7.5 updated with newly affected intents

### 6.2 Runtime-specific delivery

**Single-conversation runtime:**

The full spec is the response message. Append a handoff hint:

> Spec is ready. Next step: invoke **Skill 2 (Intent Detail Author)** in this conversation to fill the per-intent language fields. Type "run Skill 2" or attach this spec to a fresh conversation if context is getting long.

**Claude Code runtime:**

Write the spec to `agent-spec.md` in the workspace. Append a handoff hint:

> Spec written to `agent-spec.md`. Next step: invoke **Skill 2 (Intent Detail Author)** to fill the per-intent language. Skill 2 reads the same file. May be invoked in this session or a new one.

### 6.3 Section 7.3 generation log entry format

`[ISO-8601 timestamp]  Skill 1  [greenfield|patch]  [summary]`

Examples:
- `2026-05-01T14:23:00Z  Skill 1  greenfield  Initial spec produced; 6 intents in [structural] state; 1 hard intent flagged (get_available_slots).`
- `2026-05-02T09:15:00Z  Skill 1  patch  Modified slots in get_available_slots; 2 intents reset from [detailed] to [detailed-revisit] (validate_customer_address, confirm_appointment); 1 [structural] unaffected.`

---

## 7. Anti-list — what Skill 1 does NOT do

- Write `validationPrompt` text (Skill 2's territory)
- Write per-intent post-execution `intentInstructions` text (Skill 2's territory)
- Write detailed slot descriptions beyond name + minimum identification (Skill 2 elaborates)
- Run the §15.4 cross-reference pass (Skill 3's territory)
- Emit any wire-format JSON (Skill 3's territory)
- Make creative decisions in patch mode beyond what the user describes
- Discard `[detailed]` content silently — every reset is explicit and confirmed
- Validate the bot at runtime — no testing, no simulation, no behavior check
- Query live data for the model catalog or voice catalog — both remain hardcoded in `model-catalog.md` per decision F. (Accounts and layers ARE fetched live via `voicenter-mcp.list_resources` — see Section 2.4.A.)
- Capture `ConditionGroupList` or `DTMFList` as part of the default greenfield/patch flow — these are **opt-in only** per §3.5.5. The default-skip path emits empty/missing arrays which the import proc handles cleanly. v1 does not validate the contents of an opted-in section 4.7 — it's pass-through to Skill 3.

---

## Appendix A — Doc 1 §14.3 anti-patterns Skill 1 enforces

| § | Name | Skill 1 enforcement |
|---|---|---|
| 14.3.1 | Bad persona — vague/generic | Phase 2 + Self-validation Check 1 + Check 9 |
| 14.3.4 | Bad transition graph — missing fallbacks | Phase 3 + Self-validation Check 7 |
| 14.3.5 | Bad Mustache — referencing slots before collection | Phase 4 advisory pre-check + Self-validation Check 8 (advisory) |
| 14.3.7 | Bad persona — overpromising capabilities | Phase 3 + Self-validation Check 5 |
| 14.3.8 | Bad naming — inconsistent style | Phase 3 strict naming + Self-validation Check 6 |
| 14.3.9 | Misplacement — voice/channel concerns inside persona | Phase 2 + Self-validation Check 2 |
| 14.3.10 | Misplacement — per-intent instructions inside persona | Phase 2 + Self-validation Check 3 |
| 14.3.13 | Misplacement — persistent policy inside a single intent | Phase 2 + Self-validation Check 4 |

Skill 2 owns: §14.3.2 (Conversation Routines style), §14.3.3 (slot validation guidance), §14.3.6 (RT=2 api_silence completeness), §14.3.11 (bot-level disambiguation in per-intent fields), §14.3.12 (slot validation in intentInstructions).

---

## Appendix B — ParameterTypeId mapping

| User says they need… | ParameterTypeId |
|---|---|
| "name", "address", any free text | 1 (STRING) |
| "phone number" | 10 (PHONE) |
| "yes/no", "confirmation" | 16 (BOOLEAN) |
| "pick one from a list" | 19 (ENUM) + populate `OptionList` |
| "a number" / "an integer" / "a date" / "an email" | **v1 fallback: STRING (1) + flag for Skill 2 to author validationPrompt enforcing format**, surface to user as a v2 limitation |

For ENUM, capture options as `{ Value: "snake_case", Label: "user's display string" }`. `Value` is machine-side; `Label` is what the bot recognizes/announces.

---

## Appendix C — Soft-cap thresholds (decision E)

**Single-conversation runtime:**
- < 6 intents: silent
- 7–8 intents: advisory — "This is approaching the recommended limit for single-conversation runtime."
- > 8 intents: warning — "Consider switching to Claude Code runtime. Single-conversation context can strain on bots this size."

**Claude Code runtime:**
- < 12 intents: silent
- 12–20 intents: advisory — "Bot is on the larger side. Skill 2 will likely need 4+ checkpoints to detail the intent set."
- > 20 intents: warning — "Consider splitting this bot into multiple smaller bots. v1 hasn't been tested at this scale; expect Skill 2 batching to need close attention."

These warnings are emitted at greenfield close-out, after intent count is final. No hard refusal at any size — user decides.

---

## Appendix D — Compass doctrine cross-reference (rules Skill 1 enforces)

The doctrine catalog lives in [`../../references/voice-prompt-doctrine.md`](../../references/voice-prompt-doctrine.md). Skill 1 owns the rules below; Skills 2 and 3 own the remainder.

| Compass rule | Name | Skill 1 hook | Severity | Model gating |
|---|---|---|---|---|
| 3 | English operational, target-language utterances | §5 check 11 | advisory; opt-in rewrite | `[any voice]` |
| 4 | Intent description in English | §5 check 12 | advisory; opt-in rewrite | `[any voice]` |
| 5 | Recency-slot language-lock guardrail | §5 check 13 | advisory; opt-in injection/move | `[any voice]` |
| 6 | Contradictory pacing/length | §5 check 14 | advisory | `[any voice]` |
| 7 | Generic-policy boilerplate | §5 check 15 | advisory | `[any]` |
| 11 (mirror) | Hebrew-utterance isolation on rewritten fields | §5 check 11 mirror | blocking on rewrite step | `[any]` |

Skills 2 and 3 own the remaining 7 rules of the 13 (Skill 2: rules 8, 9, 10, 11 primary; Skill 3: rules 1, 2, 12, 13).

Skill 1 does NOT enforce: rule 1 (token budget — final assembly concern), rule 2 (session resumption ceiling), rule 8 (TTS-safe formatting — per-intent text), rule 9 (date math in prompt — Skill 2 per-intent), rule 10 (few-shot count — per-intent), rule 12 (model-config doctrine — assembled JSON), rule 13 (banner sentinels — Skill 3 emission).

---

*End of Skill 1 — Agent Spec Designer.*
