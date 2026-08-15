---
name: voicenter-bot-spec-designer
description: Use when the user wants to design, scope, or patch a Voicenter voice/chat bot spec — "design a bot", "add an intent", "patch this bot". Does NOT author per-intent language or emit JSON.
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

Skill 1 designs the **structural skeleton** only. It never invents a value the user did not
give, and never authors per-intent language (that is Skill 2).

**Always, at invocation:**

| Read | Why |
|---|---|
| `${CLAUDE_PLUGIN_ROOT}/references/field-placement-doctrine.md` | FP-1…FP-13. Skill 1 owns FP-2, FP-8, FP-9, FP-11 (interview), FP-12 and the persona half of FP-6 (incl. the v1.14.0 off-topic rule) |
| `${CLAUDE_PLUGIN_ROOT}/references/voice-prompt-doctrine.md` | Compass doctrine. Skill 1 owns rules 3–7 (self-val checks 11–15) and the rule 11 mirror |
| `spec-skeleton.md` | The strict template Skill 1 writes — the shape Skill 3 parses deterministically |
| Doc 2 §3 / §4 — Agent Spec template + Skill 1 architecture | What Skill 1 writes, and what it does |

**On demand, at the phase that needs it** (progressive disclosure — do not preload):

| Read | Load at |
|---|---|
| `stages/phase-interview.md` | Greenfield §3 — Phases 1–4 in order, per-RT structural capture, and the full enumeration of `AskUserQuestion` prompt sites |
| `stages/phase-graph-and-spec.md` | Close-out §3.6 — role classification, section 6 generation, section 7 init, soft caps, the Mermaid diagram and refinement loop |
| `stages/self-validation.md` | §5 — the 24 self-validation checks; run at greenfield close-out and after every patch |
| `stages/patch-mode.md` | §4 — when a prior spec is attached |
| `model-catalog.md` | Phase 1 — AI model configs and the voice catalog (hardcoded per decision F) |
| `trigger-detection-rules.md` | The Phase 2/3 boundary — Deep Research nudge triggers |
| `templates/voice-default.md`, `templates/chat-default.md` | Phase 2 — templated defaults for an inactive channel |

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

Two conventions govern every question Skill 1 asks. Both are guardrails, so they live here
rather than in the stage file; the full enumeration of prompt sites is in
`stages/phase-interview.md` §Tool conventions.

**A. Live resource lookup via `voicenter-mcp.list_resources`.** For Voicenter platform
resources — Customer Account ID (Phase 1) and layer IDs (Phase 1/Phase 4) — the default is to
fetch the live list, display it as an id+name table, and prompt from it. When MCP is
unavailable, **never silently fall back to manual entry**: offer to install, then to
authenticate, and only then capture as free text. Once the user declines, respect that for the
rest of the session and log it once to spec section 7.3. The model and voice catalogs are
**not** fetched live — they stay hardcoded in `model-catalog.md` per decision F.

**B. Menu prompts via `AskUserQuestion`.**

> **Iron rule:** if the user can answer with one of a fixed set of strings, route through
> `AskUserQuestion` — never plain free text. The only acceptable free-text prompts are
> genuinely open ones: names, descriptions, free-form content, and numeric values.

> **Ask exactly one question per turn.** One `AskUserQuestion` (or one free-text prompt) per
> message, then wait for the answer. Never batch questions.

`AskUserQuestion` adds an **Other** escape automatically, so the user can always type a custom
value — do not hand-roll one. It accepts 2–4 options; when a list exceeds four items, show the
full list as a reference table first, then prompt with the three most likely candidates and let
**Other** cover the tail. When a recommended option exists, put it first and append
*(Recommended)*.

Three fields are **never** prompted: the identifier (auto-derived from the bot name), the AI
model config (silently defaults to Gemini 3.1 - LLM driven), and per-intent `max_turns` (the
skills decide autonomously).

**Bidi safety in prompts.** Terminal surfaces (Claude Code CLI, VS Code, Desktop) do not render
RTL reliably. Keep every `AskUserQuestion` option **label/value LTR-stable** — an ASCII or
otherwise LTR-leading string the user can read unambiguously — and put Hebrew or Arabic in the
option's *description* text, not in the value being selected. The same applies to anything the
skill echoes back as an identifier, filename, or status marker: those stay ASCII. Target-language
text belongs in the *content* the bot will speak, never in a machine-critical field.

---

## 3. Greenfield mode

Four phases, in order. Phase boundaries are not strict — revisit an earlier phase if a later
answer reveals an omission.

| Phase | Produces | Load |
|---|---|---|
| 1 — Identity, channels, model, caller-silence | Spec sections 1, 3, and 4.6 if a catalog intent was supplied | `stages/phase-interview.md` §3.1 |
| 2 — Persona bundle | Spec section 2 (all five `prompts` fields), incl. the mandatory off-topic rule | `stages/phase-interview.md` §3.2 |
| 2/3 boundary — Deep Research nudge | A 7.3 log entry either way | `stages/phase-interview.md` §3.3 + `trigger-detection-rules.md` |
| 3 — Flow graph and intent list | Spec section 4 and the 4.5.1/4.5.2/4.5.4 stubs | `stages/phase-interview.md` §3.4 |
| 4 — Per-intent structural fields | Section 4 finalised, 4.5.3 derived, section 5 stubs created | `stages/phase-interview.md` §3.5 |
| Close-out | Sections 6 and 7, role classification, the flow diagram, self-validation | `stages/phase-graph-and-spec.md` + `stages/self-validation.md` |

Three structural intents are **mandatory on every bot** and are created by Skill 1, not
requested by the user: the dedicated off-topic global (§3.2.5), the silence-forwarding intent
(§3.1 step 9), and the API-timeout forwarding intent (§3.5.1, whenever any RT=2 exists). For
the latter two the user may instead point the failover at an existing flow intent — that
choice is explicit and logged to 7.3, never assumed.

---

## 4. Patch mode

Skill 1 enters patch mode when invoked with a prior spec attached. Read
`stages/patch-mode.md` for the full procedure.

The load-bearing rule, which stays here: **never discard `[detailed]` content silently.** A
hard change (response type, slots, deletions, graph edits, terminal outcome, staggering
fields) cascades — affected intents reset from `[detailed]` to `[detailed-revisit]`, and the
user sees and confirms that reset before it is applied. Never invent values to fill a gap a
deletion introduced; mark `<UNKNOWN>` and surface it in 7.4.

---

## 5. Self-validation checklist

Run on **every greenfield close-out** and **after every patch**, before declaring the spec
ready. Read `stages/self-validation.md` for the 24 checks and their exact failure messages.

These are Skill 1's checks on its own output. They are **not** Skill 3's CHK-01…CHK-26
cross-reference pass, which validates the assembled JSON — the two numbering schemes are
unrelated and must not be cross-referenced by number.

Severity handling:

- **Blocking** — do not declare the spec ready until the user resolves it. Surface failures
  one at a time, in order, using the exact message the check specifies.
- **Advisory** — record the user's resolution in spec section 7.3 and continue. Never block.
- **Structural-correctness** — auto-fix, log to 7.3, continue. No user prompt.

---

## 6. Output contract

### 6.1 What Skill 1 writes to the spec

**On greenfield completion:**
- Sections 1, 2, 3, 4, 4.5 fully filled — including (v1.13.0) the §1 limit fields (or defaults), the per-intent staggering fields (`**Captures answer to:**` / `**Asks next:**`), `**Terminal outcome:**` on RT=1 terminals, and §4.5.5 CustomData keys; and (v1.14.0) the persona off-topic rule + dedicated off-topic global intent, the dedicated silence-forwarding intent (`**IsSilenceIntent:** true`) and API-timeout forwarding intent (or the user-chosen existing targets), `**Sensitive:** true` on sensitive-collecting intents, and autonomous `**Max turns:** 10` on conversation-heavy intents
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
- Write per-intent `announcement` / `intentLoadingAnnouncement` text (Skill 2's territory) — Skill 1 records only the `**Asks next:**` question text as a structural pointer (v1.13.0)
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
| "pick one from a list" (MULTIPLE fixed values; v1.13.0, FP-13) | 19 (ENUM) + populate `OptionList` |
| single-value status/outcome slot on a terminal (v1.13.0, FP-13) | **1 (STRING)** + `**Terminal outcome:**` declares the value mode (fixed / captured / dynamic); Skill 2 writes the matching outcome-value validationPrompt |
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

The doctrine catalog lives in `${CLAUDE_PLUGIN_ROOT}/references/voice-prompt-doctrine.md`. Skill 1 owns the rules below; Skills 2 and 3 own the remainder.

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
