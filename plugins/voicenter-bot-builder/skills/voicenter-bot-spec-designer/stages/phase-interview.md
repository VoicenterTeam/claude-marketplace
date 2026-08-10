# Skill 1 stage — The greenfield interview (Phases 1–4)

*Load at the start of greenfield mode. Carries the four interview phases in order, the
per-RT structural capture, and the full enumeration of prompt sites that must route through
`AskUserQuestion`. SKILL.md keeps mode detection, the iron rules and the phase index.*

*Interview order is not arbitrary — later phases depend on answers from earlier ones
(the opening announcement is elicited before the opening behaviour, because the behaviour is
authored around the announcement's closing question).*

## Table of contents

- [Tool conventions for the interview](#tool-conventions-for-the-interview)
- [Phase 1 — Identity, Channels, Model, Caller-silence](#31-phase-1--identity-channels-model-caller-silence)
- [Phase 2 — Persona Bundle](#32-phase-2--persona-bundle)
- [Phase 2 / Phase 3 boundary — Deep Research nudge](#33-phase-2--phase-3-boundary--deep-research-nudge)
- [Phase 3 — Flow Graph and Intent List](#34-phase-3--flow-graph-and-intent-list)
- [Phase 4 — Per-intent structural fields](#35-phase-4--per-intent-structural-fields)

---

## Tool conventions for the interview

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
- Phase 1 — channel scope, agent gender (female/male), voice name, caller-silence fields and silence-forward outcome (MANDATORY — always configured), max-duration sentence confirm, max-duration layer (via MCP when connected). (The identifier is **not** prompted — it is silently auto-derived from the Bot Name, transliterating non-ASCII names, per §3.1 step 2. AI model config is **not** prompted either — it silently defaults to Gemini 3.1 - LLM driven per §3.1 step 8. Per-intent `max_turns` is NEVER prompted — the skills decide autonomously per §3.4.3.)
- Phase 2 — off-topic policy (§3.2.5): forward outcome (Human rep / Hang up / Other), loop count, and the "Accept example wording / Edit" prompt
- Phase 3/4 — API-timeout forward outcome (once per bot, §3.5.1)
- Phase 2 — every "Show the draft, confirm or edit" prompt (§3.2.1 persona, §3.2.3 opening announcement, §3.2.4 opening behavior) → "Accept" / "Edit" (Edit branches into free-text capture)
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
- Self-validation Check 16 — "Use suggested rewrite *(Recommended)*" / "Write my own question"
- Self-validation Check 17 — "Apply aligned rewrite *(Recommended)*" / "Edit myself"
- Self-validation Check 18 — "Apply restructure *(Recommended)*" / "Keep the intent" (v1.13.0)
- Self-validation Check 20 — "Inject missing rule *(Recommended)*" / "Edit" (v1.13.0)
- Self-validation Check 21 — "Inject canonical block *(Recommended)*" / "Edit" (v1.13.0)
- Self-validation Check 22 — "Add the off-topic global *(Recommended)*" / "Edit" (v1.14.0)
- Self-validation Check 23 — "Create the dedicated forwarding intent *(Recommended)*" / "Pick an existing intent" (v1.14.0)
- Self-validation Check 24 — "Set Sensitive: true *(Recommended)*" / "Keep false" (v1.14.0)
- Phase 3 §3.4.3 — terminal outcome value mode when the characterization material doesn't determine it ("Fixed value" / "Save what the customer said" / "Composed per call") (v1.13.0)
- Section 2.4.A MCP fallback — "Install / Authenticate / Continue manually"

**Iron rule:** if the user can answer with one of a fixed set of strings, route through `AskUserQuestion`. The only acceptable free-text prompts are open-ended ones (names, descriptions, free-form text content, integer/numeric values). **Ask exactly one question per turn:** present a single `AskUserQuestion` (or one free-text prompt) per message and wait for the answer before asking the next. Never batch multiple questions into one turn.

`AskUserQuestion` automatically adds an **Other** escape, so the user can always type a custom value if the displayed options don't cover their case. When a recommended option exists (e.g., the MCP-enable path), put it first and append *(Recommended)* to its label.

`AskUserQuestion` accepts 2–4 options. When a list (e.g., accounts, layers) exceeds 4 items, first display the full list as a reference table, then prompt with the 3 most likely candidates as menu options and rely on **Other** for the long tail.

Free-text capture remains correct for open-ended fields — bot name, identifier, description, persona, intent identifiers, slot names, free-form announcements, integer or numeric values, etc. — where there is no closed option set.

---


---

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
   - **b. Voice name.** Read the `model-catalog.md` voice catalog and prompt via `AskUserQuestion` presenting **only voices whose `Gender` matches step (a)** for the active model family (default Gemini, since the default model is Gemini 3.1 - LLM driven). E.g. Female → `Kore`, `Leda`, `Aoede`; Male → `Puck`, `Orus`, `Charon`. Neutral voices (e.g. `alloy`) may appear under either gender. `Other` lets the user supply any provider-supported string.
8. **AI model config: do NOT prompt.** Silently default to the most relevant model — **Gemini 3.1 - LLM driven** → `AIModelConfigID=142`, `AIModelTypeId=21` (per `model-catalog.md` canonical default). Write it to spec section 1 without asking. **Override only if the user volunteers a different model** (e.g. "use the OpenAI realtime one" or supplies raw `AIModelConfigID` + `AIModelTypeId`): map by name via `model-catalog.md`, or accept the raw IDs directly. Only mark `<UNKNOWN: AI Model Config>` if the user explicitly defers the choice (e.g. "leave it blank, platform team will fill in").
9. **Caller silence (MANDATORY — v1.11.0; reworked v1.14.0).** Caller-silence handling is always configured; do NOT ask whether to enable it. Collect each field via `AskUserQuestion` with a "Use default *(Recommended)*" option (free-text override allowed): `silence_duration` (default **5** s), `silence_loops` (default **3**), `silence_sentence` (default: a polite re-prompt in the bot's primary language, e.g. Hebrew "האם אתם עדיין על הקו?"), `silence_ending_sentence` (default per the forward outcome — see below). Then **explicitly ask** (via `AskUserQuestion`, header "Silence forward"): *"After the silence loops are exhausted, what should happen to the call?"* Options: (a) **"Hang up *(Recommended)*"**; (b) **"Transfer to a human representative"**; (c) **"Return to an existing flow intent (e.g., main menu)"**.
   - **Options (a)/(b) — the normal case:** Skill 1 **ALWAYS creates a dedicated bot-own silence-forwarding intent** — an RT=1 terminal (role `chained`, free-floating), `**IsSilenceIntent:** true`, layer captured in Phase 4 via MCP (hang-up/disconnect layer for (a), human-rep layer for (b)), short "יום טוב"-style loading announcement only (FP-8). Stage it now; materialize it in Phase 3 alongside the user's flow intents. Section 3's `silence failover intent` points at it.
   - **Option (c) — the exception:** point section 3's failover at the chosen **existing** flow intent. Do NOT create a new intent.
   - Default `silence_ending_sentence` to a "transferring you to a representative" line when the outcome is (b); else a polite hang-up line. Section 3 is never `[not configured]`. Roles are finalized in §3.6.
   - **IMPORT-LIMITATION NOTE (empirically confirmed 2026-06-23):** the Voicenter import procedure does NOT remap placeholder IDs inside `silence_behaviour.intent` (unlike `intents[]`/`botIntents[]`/`intentRelations[]`). Skill 3 therefore emits the placeholder plus a MANDATORY banner line instructing the operator to set the silence forward in the UI post-import (the target is identifiable by `IsSilenceIntent: 1`). Mention this once to the user; no further action needed during the interview. (v1.14.0 removed the pre-v1.14 "substitute catalog intent 19" mechanism.)
10. **Created by:** bot author/owner name (free text). Optional — Skill 1 prompts via `AskUserQuestion` per Section 2.4.B (header: "Created by", 2 options: "Skip (default: empty)" / "Provide a name"). If user picks "Provide a name", capture as free text. Written to spec section 1 as `**Created by:**`. **Purpose:** Skill 3 v1.5.0+ uses this value to populate `IntentParameters[].CreatedBy` in the emitted JSON (production-required audit field).
11. **Max call duration (seconds):** integer. Default `1200`. Prompt via `AskUserQuestion` per Section 2.4.B (header: "Max call duration", 2 options: "Use default 1200 *(Recommended)*" / "Set a different value"). If different, capture as free-text integer. Written to spec section 1 as `**Max call duration:**`.
12. **Max duration sentence (v1.14.0):** prompt via `AskUserQuestion` (header: "Max duration sentence"): *"When the call hits max duration, the bot says: 'נראה שהגענו לזמן שיחה מקסימלי, אנא נסה שנית'. Keep this default?"* Options: "Use default *(Recommended)*" / "Write my own" (free-text capture). Written to spec section 1 as `**Max duration sentence:**` (omit the field when the default is kept — Skill 3 emits the default).
13. **Max duration layer (v1.14.0):** if MCP is available per §2.4.A, call `voicenter-mcp.list_resources` with `entityFilter: ["Layers"]`, display the layers as an id+name table, then prompt via `AskUserQuestion` (header: "Max-duration layer"): *"Which layer should receive the call when max duration is reached?"* Written to spec section 1 as `**Max duration layer:**`. If MCP is unavailable or the user already declined MCP: **silently default `0`** — do NOT ask, do NOT re-run the §2.4.A install/auth offer; log to 7.3. `dailyLimitLayerId` and `IVRLayerSelect_2` are NOT asked and keep their default `3` (out of scope).
14. **Record agent calls:** boolean. Default `false`. Prompt via `AskUserQuestion` per Section 2.4.B (header: "Record calls", 2 options: "No — do not record *(Recommended)*" / "Yes — record"). Written to spec section 1 as `**Record agent calls:**`. **Note:** Skill 3 emits this in the JSON as the **string** `"false"` / `"true"` (not a JSON boolean) — production export shape.
15. **Negative instructions (v1.16.0):** optional free text — the UI's AI Security Settings field: what the agent must never say or commit to (legally, medically, financially — e.g., "never promise a refund", "never give medical advice"). Prompt once via `AskUserQuestion` per Section 2.4.B (header: "Guardrails", 2 options: "Skip — none *(Recommended)*" / "Add never-say rules" with free-text capture). Written to spec section 1 as `**Negative instructions:**`; omit the field entirely when skipped. **NOT emitted to the wire JSON** — the wire field name is unverified; Skill 3 surfaces it as a MANDATORY POST-IMPORT banner step (paste into the UI's AI Security Settings → Negative Instructions). Check 15 may also relocate must-never-say content here from prompt fields.

**Write at end of Phase 1:** spec sections 1, 3, and 4.6 (only if the user supplied a catalog intent).

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
| Call-wide rules stated ONCE, in persona (v1.13.0, FP-6). | FP-6 | The persona must state, exactly once each: (a) the turn-taking rule — canonical wording: **"You should always act only after the customer answers and only by the instructions you got. You should never act without the customer's specific answer."**; (b) human-rep request handling (what to say via the FP-4 quote convention + where to route) whenever a human-rep `global` exists; (c) disapproval/decline handling (same shape) whenever a decline terminal exists; (d) **off-topic handling (v1.14.0 — MANDATORY on every bot)** — authored in §3.2.5 from the user's answers. These rules are NEVER repeated in per-intent fields — enforced by check 20. Rules (b)/(c) are finalized at the Phase 3→close-out boundary when the globals/terminals are known; stage a 7.3 note if authored earlier. |

**Compass doctrine note (rules 3 and 7).** For non-English bots, the doctrine recommends writing operational prose in English (~3× token savings on the static prompt; preserves function-calling and instruction-following accuracy that degrades in Hebrew/Arabic/CJK). Verbatim utterances the agent must speak stay in the target language. Skill 1's self-validation check 11 fires advisory if a bot-level prompt field is ≥30% non-Latin characters. Independently, check 15 flags generic GDPR/HIPAA/PII boilerplate that isn't derived from the bot's domain — these belong in the data plane (Presidio, dialplan, etc.), not the persona. See `${CLAUDE_PLUGIN_ROOT}/references/voice-prompt-doctrine.md` rules 3, 4, 7 for fix recipes.

#### 3.2.2 Elicit channel-specific behavior

For each **active** channel:

- **Voice:** ask about pacing, pronunciation (especially for street names and numbers), interruption handling, audio cues, pauses.
- **Chat:** ask about formatting (markdown vs plain), message length, emoji policy, confirmation patterns.

For each **inactive** channel: emit the templated default automatically per `templates/voice-default.md` or `templates/chat-default.md`. Substitute `[[PERSONA_IDENTITY]]` (extracted from the just-authored persona — first sentence or two establishing identity) and `[[PRIMARY_LANGUAGE]]` (mapped from the language code in section 1 to a human-readable name, e.g., `he-IL` → "Hebrew"). Show the result to the user. Prompt via `AskUserQuestion` per Section 2.4.B (header: "Channel default", 2 options: "Accept default" / "Override").

If user accepts: write to spec preceded by `[default — not user-authored]`.
If user overrides: capture the override; do not include the marker.

#### 3.2.3 Draft `prompts.openingAnnouncement`

This is the **first audible message** the caller hears (Doc 1 §3). One short utterance. It is elicited **before** the opening behavior (§3.2.4) because the opening behavior is authored around this announcement's closing question. (Interview order only — the spec still writes it to section 2.5, after section 2.4.)

**IRON RULE (house rule, v1.12.1 — hard, no override):** the opening announcement MUST end with a question mark (`?`; `؟` for Arabic bots — Hebrew uses `?`). Trailing quotes or whitespace after the mark are fine. Any engaging question passes; a statement never does. The question should **preferably ask for the first detail the bot collects** (typically the entry intent's first slot — caller's name, identity confirmation, "is it a good time to talk"), so the caller's very first answer is already useful data. Canonical examples:

- "Hello, this is X's virtual assistant. Who am I speaking with?"
- "Hey there, this is the virtual assistant of Y. Is it a good time to talk?"
- "Hello, am I speaking with Z?"

Ask: "What does the caller hear at the moment of pickup? It must end with a question — ideally asking for the first thing the bot needs from the caller (e.g., 'Hello, this is X. Who am I speaking with?')."

Draft and show. If the user supplies a statement (no closing question), do NOT accept it — explain the iron rule, propose a question-ending rewrite that preserves their wording, and re-prompt. Prompt via `AskUserQuestion` per Section 2.4.B (header: "Opening line", 2 options: "Accept draft" / "Edit"). If "Edit", capture revisions as free text, re-apply the iron rule, and re-prompt until accepted.

**Staggered-pipeline note (v1.13.0, FP-2):** the opening question is pipeline question #1 — its answer is captured by the FIRST flow intent's slots, not by any "opening gate" intent. Record it later as that intent's `**Captures answer to:**` (§3.4.3). A dedicated yes/no intent whose only job is the opening question is forbidden (check 18).

#### 3.2.4 Draft `prompts.intentInstructions` (bot-level Opening Behavior)

This is **pre-intent** — what the bot does at the very start of the call, before any specific intent has fired. It contains the handling of the caller's answer to the opening question, routing logic, and disambiguation rules. (Per Doc 1 §14.3.11, this is one of the most-misused fields.)

**IRON RULE (house rule, v1.12.1):** the opening announcement (§3.2.3) already greeted the caller and asked a question. The opening behavior's **first numbered step must handle the caller's answer to that question** (capture the name, branch on yes/no, confirm identity). The routine never greets again and never re-asks the opening question. Escape hatch: if the caller ignores the question and states a request directly, the routine routes on that request immediately and collects the skipped detail later if still needed.

**IRON RULE extension (v1.13.0, FP-2/FP-4/FP-12):**

- **Staggered branch content:** when the flow staggers off the opening (FP-2), §2.4 carries the full branch logic — including any read-back the caller must hear on the "proceed" branch and the next question the first flow intent will capture (e.g., the identity read-back with `{{CustomData}}` vars ending in `Ask the customer : "האם הפרטים נכונים?"`).
- **Opening-question merge:** a flow must NOT start with a dedicated yes/no gate intent (e.g., "is now a convenient time?"). The question is the last sentence of §2.5, and the yes/no branch lives here in §2.4 (good time → proceed with the read-back; can't talk → the callback branch). Enforced by check 18.
- **Quote convention (FP-4):** any spoken line mandated in this routine uses `<instruction text> : "<verbatim line>"` — e.g., `Ask the customer : "אין שום בעיה, מתי תרצה שנחזור אליך ?"`.
- **Callback machinery (FP-12):** whenever the flow collects a callback/scheduling time, this routine must include the canonical date/time interpretation block (anchor on `{{todayHe}}`/`{{timeHe}}`; relative time → compute silently; day without hour → ask only `"באיזו שעה ?"`; never re-ask provided info). Enforced by check 21.

Ask: "The opening announcement just asked '[the §3.2.3 closing question]'. What should the bot do with the caller's answer, and how does it route to intents from there? What if the caller says something unclear?"

Draft in **Conversation Routines style** (ALL-CAPS headers, numbered steps, IF/ELSE, IRON RULES). Example shape:

```
OPENING BEHAVIOR
(Opening announcement already played: "Hello, this is X's assistant. Who am I speaking with?")
1. Capture the caller's answer to the opening question (the caller's name).
2. Route based on what the caller needs:
   - Scheduling → trigger validate_customer_address.
   - Rescheduling → trigger reschedule_existing.
   - General questions → trigger general_inquiry.

IF caller ignores the opening question and states a request directly:
  - Proceed with routing; collect the skipped detail later if still needed.

IF caller's intent is unclear:
  - Ask once for clarification.
  - If still unclear, route to transfer_to_human.

IRON RULE: Never greet again or repeat the opening question.
IRON RULE: Stay in scope. For pricing/billing/technical, route to transfer_to_human.
```

Show the draft, then prompt via `AskUserQuestion` per Section 2.4.B (header: "Opening behavior", 2 options: "Accept draft" / "Edit"). If "Edit", capture revisions as free text and re-prompt until accepted.

**Compass doctrine note (rule 5 — recency-slot language-lock).** The bot-level `intentInstructions` is the recency slot of the assembled systemInstruction (per "Lost in the Middle" + "Found in the Middle" U-shaped attention bias). For non-English bots, a known production bug (Gemini cookbook #1197) causes the model to code-switch based on the caller's name or accent even with English-only instructions. The doctrine's mitigation is to place an extreme negative constraint — equivalent to `"NEVER infer language from caller's name, accent, or tone."` — in the final third of `prompts.intentInstructions`. Skill 1's self-validation check 13 detects whether this constraint is present in the recency slot and, if not, offers to inject the standard line. See `${CLAUDE_PLUGIN_ROOT}/references/voice-prompt-doctrine.md` rule 5 for the detection pattern and fix recipe.

#### 3.2.5 Off-topic policy (v1.14.0, FP-6(d) — MANDATORY on every bot)

Every bot gets a persona rule for callers who talk about subjects the bot must not discuss, plus a dedicated global terminal that ends the loop. Elicit it with three one-per-turn prompts:

1. **Forward outcome.** `AskUserQuestion` (header: "Off-topic outcome"): *"If the caller keeps raising unrelated topics after the bot's redirects, where should the call end up?"* Options: "Human representative *(Recommended)*" / "Hang up" / "Other ending" (Other captures a custom outcome).
2. **Loop count.** `AskUserQuestion` (header: "Off-topic loops"): *"How many off-topic deflections before the bot says the ending line and forwards?"* Options: "2 *(Recommended)*" / "3" (Other for a custom count).
3. **Example wording.** OFFER a drafted persona block, templated on the production reference bots, adjusted to the bot's domain, persona register, and grammatical gender — deflection line + redirect question for the first occurrence, ending line for loop exhaustion. Model (Hebrew, masculine):

   ```
   איסור דיבור על נושאים אחרים
   אסור לך, תחת שום נסיבות, לדבר על נושאים שאינם קשורים ל-[domain]
   (לדוגמא : "פוליטיקה", "עניינים רפואיים", "צבא").
   כאשר המתקשר מעלה נושא כזה, tell the customer : "מתנצל, אבל אני כאן לעזור רק לגביי [domain]. תרצה שנמשיך ?"
   אם המתקשר ממשיך לדבר על נושאים לא קשורים [N] פעמים, you must say : "[ending line]"
   ואז להעביר את השיחה אל [the off-topic terminal, referenced by its Description].
   שים לב לא להתבלבל בין מילה מתחום ה-[domain] לבין נושא שאינו קשור.
   ```

   Prompt via `AskUserQuestion` (header: "Off-topic wording", 2 options: "Accept example *(Recommended)*" / "Edit" — free-text capture, re-prompt until accepted). Inject the accepted block into §2.1 persona (it is FP-6 rule (d) — stated once, never per-intent).

**Structural companion (materialized in Phase 3):** Skill 1 ALWAYS adds a **dedicated off-topic global intent** — role `global` (⇒ `botIntents` type 2, reachable from anywhere), RT=1 with the layer matching the chosen outcome (captured via MCP in Phase 4), display name modeled on the production reference (`"סיום השיחה במקרה של דיבור על נושא לא קשור יותר מ-[N] פעמים"`), short loading announcement only (default `"יום טוב !"`), per the FP-8 terminal rules. Enforced by check 22.

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
- **Description:** a **short semantic English label naming the business step** (v1.13.0, FP-10) — e.g., "Verification of plan and premia", "confirming health declaration". It is both the LLM's intent-recognition anchor and the name other intents' instructions use for routing (FP-9). **Forbidden:** stage/workflow markers ("Stage 2", "Gate C"), dialogue imperatives ("Ask…", "Read back…", "Explain…"), business logic ("premium may change after further review"). Specific data points belong in slot Descriptions; conversational content belongs in announcement/instructions (Skill 2); business logic belongs in §2.4 or persona. If the user supplies a long descriptive sentence, distill it to the semantic label and confirm. (Check 12's English preference remains advisory; FP-10 recommends English by default.)
- **Tool name:** same as identifier.
- **Captures answer to / Asks next (v1.13.0, FP-2):** while walking the happy path, fill the stagger fields for each flow intent: "the caller answers question Q(n-1) — asked by the previous intent's announcement or by the opening — and this intent's slots capture that answer; this intent's announcement will ask Q(n)." Record Q(n-1) as `**Captures answer to:**` and Q(n) as `**Asks next:**` (terminals: `[none — terminal]`). Omit both on globals. Skill 1 records only the question text as a structural pointer — the announcement wording itself is Skill 2 territory.
- **Terminal outcome (v1.13.0, FP-8):** for each RT=1 terminal, capture the outcome slot and its **value mode** — *fixed* (one exact string, e.g., `shikuf_status = "הלקוח ביקש נציג אנושי"`), *captured* (save what the customer said), or *dynamic* (text composed per call). **Infer the mode from the characterization/requirements material the user provided when it determines the answer; ask (or confirm the inference) only when it doesn't.** Write the spec field per the two-mode grammar in `spec-skeleton.md` §4.
- **Response Type:** prompt via `AskUserQuestion` per Section 2.4.B (header: "Response type", 4 options: "RT=1 — Transfer the call", "RT=2 — Call an external API", "RT=3 — Collect info and continue", "RT=4 — Initiate an outbound dial"). *(Note for cross-referencing the schema: RT=3 is stored as `ResponseTypeId=3` and the DB seed name is "Message" / "Update Bot Configuration" — but operationally, RT=3 is what every conversational data-collection intent uses. Match the operational semantic, not the seed label.)*
  - For RT=4: surface the rarity warning per Doc 1 §11.4: "RT=4 (outbound dial) is uncommon. Confirm you actually need to initiate an outbound call from this intent, not transfer the existing call."
- **Transitions out:** ordered list of (target intent, role). Role is "success path" / "fallback" / "escalation". **Do NOT hand-author transitions to `global` intents** (e.g. transfer-to-human) — a `global` is reachable from anywhere via its `botIntents[]` type-2 registration, so no explicit transition edge is needed (v1.12.0 — Skill 3 no longer fans out edges to globals). List only flow transitions to entry/chained intents.
- **Bot-intent role:** `entry` | `global` | `chained` (default `chained`). Captured here as a first pass — **infer from context; do NOT prompt the user for this field per-intent during Phase 3.** It is confirmed in one batch at §3.6. `entry` = the §2.4 opening behaviour routes to it directly; `global` = triggerable from anywhere (transfer-to-human, WhatsApp); `chained` = reached only via another intent's transition. `global` supersedes `entry`.
- **Hard-intent flag:** Skill 1 evaluates per the four criteria below; mark `true` or `false`.
- **Sensitive (v1.14.0):** when an intent COLLECTS truly sensitive data — ID / national-ID number, credit card (number, CVV, expiry, cardholder ID), or medical information — set `**Sensitive:** true` on that intent. Placement rule: the flag goes ONLY on the intent where the collection is configured (in the FP-2 ask-in-N / collect-in-N+1 stagger, that is the collecting intent N+1 — never the asking intent), and only for genuinely sensitive data. When setting it, **ALWAYS proactively tell the user** (do not wait to be asked): *"Because this intent collects sensitive details, I'm enabling sensitive-data handling on it (`sensitive: true`) to keep Information Security. The details can still be used in API calls configured on this same intent, but they will NOT be saved in the LOGS/TRACES."* Never flag intents collecting non-sensitive data.
- **Max turns (v1.14.0 — NEVER ask the user; decide autonomously):** default is `5` for every intent (Skill 3 emits it). Set `**Max turns:** 10` on **conversation-heavy intents** — where extended speaking back-and-forth between the bot and the caller is expected: multi-slot collection, search/retry loops, sensitive-detail collection. The `10` goes on the intent where the actual conversation happens — in the FP-2 stagger, the asking/speaking intent, not automatically the downstream collecting intent. A turn counts each side's utterance; 5 or 10 covers both together. Do NOT prompt the user for this field.

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
| Per-outcome terminals (v1.13.0, FP-8; farewell placement reworked v1.14.0). | FP-8 | Every distinct call outcome named in the interview gets its OWN RT=1 terminal that owns an outcome slot (`**Terminal outcome:**`) and ends the call in one hop. **Forbidden:** a finalize→end_call two-intent chain; a single intent that computes the outcome via IF/ELSE-IF prose (non-deterministic — depends on LLM recall). On detection: propose the per-terminal decomposition (one terminal per outcome; the closing line lives in each terminal's PREDECESSOR intent's `intentInstructions` per the v1.14.0 RT=1 farewell trigger rule — the terminal itself keeps only a short loading announcement). Block until resolved. |
| Pre-IVR farewell placement (v1.14.0, FP-3 corollary / FP-8). | FP-8 | For EVERY intent that transitions into an RT=1 terminal, the ending sentence must be planned as the last spoken line of that predecessor's `intentInstructions` (Skill 2 authors the wording). If the predecessor has splits/transitions to other intents, Skill 1 must create a **dedicated pre-IVR intent whose only job is the ending sentence** before the terminal. Block until the structure supports the placement. |
| Mandatory structural intents (v1.14.0). | FP-6/FP-8 | The bot must contain: the dedicated **off-topic global** intent (§3.2.5), the dedicated **silence-forwarding** intent (§3.1 step 9 — unless the user chose an existing flow intent), and the dedicated **API-timeout forwarding** intent (§3.5.1 — when any RT=2 exists; unless the user chose an existing flow intent). Block until present. |
| Status ownership (v1.13.0, FP-8). | FP-8 | The outcome/status parameter appears ONLY on terminals. Gates never carry, set, or mention it — an intent can only set its own slots; "Set status_X to …" on a gate is un-executable at runtime. Block until resolved. |
| Minimal graph (v1.13.0, FP-9). | FP-9 | Transitions exist only for the linear happy-path spine + true branches. Exception outcomes (human-rep request, decline/not-confirmed) are `global` terminals reachable from anywhere, driven by the persona's FP-6 call-wide rules — never wire an explicit edge from every gate (reinforces the v1.12.0 no-fan-out rule in §3.4.3). Block until resolved. |

#### 3.4.5 Available-variables interview (4.5.1, 4.5.2, 4.5.4 stubs)

Ask:

- **4.5.1 Call-context variables:** "What platform-supplied variables does your account expose at call start? Common entries: `caller_phone`, `TimeNow`, `caller_name`, `account_id`." If the user can't enumerate: emit defaults `caller_phone` and `TimeNow`, mark section `<INCOMPLETE: user to verify with platform>`.
- **4.5.2 Environment variables:** "Are there any deployment-time secrets you'll reference, like `{{ENV.API_TOKEN}}`?" Capture by name. v1 trusts the user's declaration; no validation that the secret exists.
- **4.5.5 CustomData keys (v1.13.0, FP-11):** "List the EXACT per-call CustomData keys your pipeline sends with each call (e.g., `firstnamelastname`, `nationalid`, `policies`, `insurer`, `monthlypremiumafterdiscount`). I will never invent key names — any `{{placeholder}}` not on this list blocks assembly at CHK-07." Record verbatim in §4.5.5. If the user cannot enumerate: write `<INCOMPLETE: CustomData keys unverified>`. When the flow reads per-call data or collects a callback time (Hebrew bots especially), also confirm the platform context vars `{{todayHe}}` / `{{timeHe}}` are available and add them to 4.5.1.
- **4.5.4 API response shapes:** for each RT=2 intent, ask: "What dotted paths will you reference in the API response announcement? E.g., `available_slots.0.display`, `response.order.status`." Capture per intent. The declared shape is **provisional** — Skill 2 hard-verifies it against the live API (real `curl`, 2xx + every declared path present) before the intent can be detailed; an unverifiable endpoint blocks. Skill 3 also validates `announcement` (was `apiResponseAnnouncement` pre-v1.5.0) references against this allowlist.

(Section 4.5.3 is auto-derived from section 5 slots — generated in Phase 4 close-out.)

**Runtime fallback (voice-agent-llm v1.0.3+):** if an emitted RT=2 `announcement` is empty at runtime, the service substitutes the sentinel `[START THE CONVERSATION]` as an LLM instruction telling the bot to open from persona — the literal string is **not** spoken aloud. Skill 2 still requires authored text for RT=2 (Check 10 remains blocking); the fallback is a production safety net, not an authoring choice.

**Write at end of Phase 3:** spec section 4 (intent rows with all structural fields except the per-RT specifics, which Phase 4 fills) and spec section 4.5.1, 4.5.2, 4.5.4.

### 3.5 Phase 4 — Per-intent structural fields

**Goal:** finalize section 4 entries with per-RT structural fields. Create section 5 stubs. Run advisory Mustache pre-check.

#### 3.5.1 Per-RT capture

**For all RTs:** capture slot list — name (free text), `ParameterTypeId` (closed set per Appendix B → prompt via `AskUserQuestion`, header "Slot type", 4 options: STRING / PHONE / BOOLEAN / ENUM, with Other for the unsupported-type fallback path), `IsRequired` (yes/no → prompt via `AskUserQuestion`, header "Required?"), `CollectionOrder` (integer, free text), `OptionList` for ENUM (free-text capture of `{Value, Label}` pairs), and `DefaultValue` (optional, v1.16.0 — NEVER prompted; record on the slot line only when the user volunteers a pre-filled value, most commonly `true`/`false` on a BOOLEAN slot. Omitted ⇒ Skill 3 emits `""`).

For unsupported types (number, integer, date, email — captured via the `ParameterTypeId` Other branch): emit STRING (ParameterTypeId 1) and flag the slot for Skill 2 to author a `validationPrompt` enforcing format. Note in section 7.3: "Slot `[name]` requires natural-language validation (v1 type fallback: STRING)."

**RT=1:** Layer ID. **Always use the real layer number.** Per Section 2.4.A, call `voicenter-mcp.list_resources` with `entityFilter: ["Layers"]`, display the returned layers to the user as an id+name table, then prompt via `AskUserQuestion` per Section 2.4.B (header: "Layer") and record the selected layer number. Only if MCP is not connected **and** the user genuinely doesn't know the layer: default the layer to `0` (root layer) — do **not** mark `<UNKNOWN: layer ID>` and do not emit a sentinel (v1.12.0). The MCP-fetched number is the rule; `0` is the last-resort fallback.

Additionally for RT=1 terminals (v1.13.0, FP-8): ensure the outcome slot named in `**Terminal outcome:**` (§3.4.3) appears in this intent's slot list — typically STRING (ParameterTypeId 1) per FP-13; ENUM (19, with OptionList) only when the slot selects among multiple fixed values.

**RT=2:**
- URL (user-supplied; `<UNKNOWN: webhook URL>` if not known)
- Method — prompt via `AskUserQuestion` (POST / GET, header: "HTTP method")
- Headers structure (user-described; defaults to `{}`)
- Body structure with Mustache references (user-described)
- API response shape declaration → already captured in 4.5.4 (provisional; Skill 2 hard-verifies it against the live API before the intent can be detailed)
- API silence behavior fields: `silence_duration`, `silence_loops`, `silence_sentence`, `silence_ending_sentence`, `silence_instructions` (text or empty), and **fallback intent reference**. **v1.14.0 default: the dedicated API-timeout forwarding intent.** The FIRST time any RT=2 intent is captured, ask once per bot via `AskUserQuestion` (header: "API-timeout forward"): *"When an API call stalls and the silence loops exhaust, where should calls go by default?"* Options: "Human representative *(Recommended)*" / "Hang up" / "An existing flow intent (e.g., main menu)". The first two ⇒ Skill 1 ALWAYS creates ONE dedicated bot-own API-timeout forwarding intent (RT=1, role `chained` free-floating, layer via MCP in Phase 4, short loading announcement only) and defaults every RT=2 intent's fallback to it. The third ⇒ point at the chosen existing intent; NO new intent. A per-intent override remains possible via `AskUserQuestion` (header: "Fallback intent") when the user wants a specific RT=2 intent to fall back elsewhere (e.g., a retry/continue intent).
- **Max turns / Max turns sentence (per-intent turn cap, v1.14.0):** NEVER captured from the user. Skill 3 emits `additional.max_turns: 5` for ALL RTs by default; Skill 1 autonomously sets `**Max turns:** 10` on conversation-heavy intents per §3.4.3. `**Max turns sentence:**` is authored by Skill 2 (persona-register, gender-matched); Skill 3 falls back to the masculine model sentence when absent. Spec authors hand-editing the spec may still override either field per `spec-skeleton.md` §4.

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
