---
name: voicenter-bot-json-assembler
description: Assembles a fully-detailed Voicenter Agent Spec into Bot JSON wire format — the final mechanical step in the three-skill pipeline. Use this skill when an Agent Spec exists with all section 5 entries marked `[detailed]` and the user wants the deployable JSON. Trigger phrases include "run Skill 3", "assemble the JSON", "emit the bot JSON", "publish the bot", "build the wire-format", "Skill 3 (JSON Assembler)", or any direct continuation from Skill 2's completion handoff. Produces a single `bot-<name>-<date>.json` file plus a banner identifying every fail-loud sentinel and any drift between spec section 6 and what Skill 3 regenerated. Refuses to assemble if any intent is still `[structural]` or `[detailed-revisit]`, or if the spec deviates from the strict template (Doc 2 §3.7). Runs the §15.4 cross-reference pass — 24 checks (8 §15.4 + 3 Compass + 3 botIntents-role + 1 duplicate-global-intent + 9 field-placement doctrine), checks 1–7, 11–13, 15, 16–21, and 24 blocking. Does NOT author any text content (Skills 1 and 2 only). Does NOT make creative decisions, interpret deviations, fix violations, or invoke other skills (it reports routing recommendations; the user invokes the relevant skill).
---

> **Language.** Reply in the user's language: detect what they write — Hebrew→Hebrew, English→English — and mirror it, switching if they switch mid-conversation. This shapes your prose, your questions, and your `AskUserQuestion` option labels only. It does **not** change the artifacts you produce — identifiers, JSON keys, BCP-47 language codes, API field names, and other data stay exactly as specified.

> **Opening.** Your first message greets bilingually so the user knows both languages are available — e.g. *"נוכל להמשיך בעברית או באנגלית — מה נוח לך? / We can continue in Hebrew or English — whichever you prefer."* Then mirror whatever language the user replies in.

> **One question per turn.** Ask exactly one question per message and wait for the answer before asking the next — never present multiple questions in a single turn. When the answer is a closed set (pick-one / yes-no / pick-from-list), use the `AskUserQuestion` tool rather than plain text; it automatically adds an "Other" free-text escape, so don't hand-roll one. Reserve plain free-text questions for genuinely open inputs (names, descriptions, URLs, numbers).

# Skill 3 — JSON Assembler & Publish

This skill produces the **deployable Bot JSON** by mechanically projecting a fully-detailed Agent Spec into Voicenter wire-format. It is the third and final skill in the Voicenter Bot generation pipeline:

- **Skill 1 (Agent Spec Designer):** structural design via interview → fills sections 1, 2, 3, 4, 4.5; creates section 5 stubs marked `[structural]`.
- **Skill 2 (Intent Detail Author):** language-heavy per-intent content → fills section 5 entries, marks them `[detailed]`.
- **Skill 3 (this skill):** mechanical assembly of spec → wire-format JSON.

**Operating principle: pure parser, not interpreter.** Skill 3 makes no creative decisions. It does not best-effort interpret ambiguous spec content; if the spec deviates from the strict template, Skill 3 reports a structured parse error and refuses to assemble. The entire skill architecture depends on Skill 3 being deterministic — if Skill 3 interprets, "what JSON does this spec produce?" depends on Skill 3's mood, and the source-of-truth contract dies. Discipline is the design.

The risk vector for this skill is **doing too much**: filling in plausible-looking values for unknowns, smoothing over template deviations, auto-fixing cross-reference violations, deciding RT-specific defaults the spec didn't specify. The anti-list (§8) is the longest and most opinionated section — read it before doing anything else.

---

## 1. Required reading at invocation

Skill 3 is a mechanical projection: every emitted field traces to a spec field, a documented
constant, or a fail-loud sentinel. Load the authorities below before touching the spec.

**Always, at invocation:**

| Read | Why |
|---|---|
| `${CLAUDE_PLUGIN_ROOT}/references/verification-procedure.md` | **The 24 checks (CHK-01…CHK-24) — read and execute this file; §6 only decides which path runs it** |
| `${CLAUDE_PLUGIN_ROOT}/references/field-placement-doctrine.md` | FP-1…FP-13 incl. the FP-3 turn-yield rule; verified by CHK-16…CHK-24 |
| `${CLAUDE_PLUGIN_ROOT}/references/voice-prompt-doctrine.md` | Compass doctrine; Skill 3 owns CHK-08 (rule 1), CHK-09 (rule 2), CHK-10 (rule 12) and the banner sentinels (rule 13) |
| Doc 2 §3.7 — Strict-template enforcement | The §3 parse rules |
| Doc 2 §6 — Skill 3 architecture | What this file implements |

**On demand, at the step that needs it** (progressive disclosure — do not preload):

| Read | Load at |
|---|---|
| `stages/assembly-mapping.md` | §4 — the complete spec→wire field mapping, ID ranges, per-RT `Configuration` shapes, §16 quirks, static reference data. Also carries the Doc 1 §4–§13 and §15.3/§16 mappings it implements. |
| `stages/sentinels-and-banner.md` | §4.6 / §5 / §7.2 — sentinel bookkeeping, section-6 drift reporting, banner format |
| `stages/parse-errors.md` | §3 — only when the parse fails: error format and worked deviation examples |
| `skills/voicenter-bot-spec-designer/model-catalog.md` | §4.2.3 — resolving a named model entry to `AIModelConfigID` / `AIModelTypeId` / provider model string |

Skill 3 does **not** load Skill 2's `conversation-routines-style-guide.md`. The style of
`validationPrompt` and `intentInstructions` is Skill 2's concern; Skill 3 emits that text
verbatim from the spec regardless of style.

---

## 2. Setup

### 2.1 Detect runtime

| Signal | Runtime |
|---|---|
| Conversation in claude.ai or mobile app, no workspace file system, no `agent-spec.md` accessible | **Single-conversation** |
| Workspace file system available (Claude Code), `agent-spec.md` readable as a file | **Claude Code** |

State the detected runtime. The user can correct.

### 2.2 Read the spec

**Single-conversation:** read backward through the conversation context to find the most recent spec emission. The spec is identifiable by its `## 1. Bot Identity` header and `## 7. Generation Metadata` footer. If both Skill 1 and Skill 2 ran in this conversation, take the most recent (Skill 2's output).

**Claude Code:** read `agent-spec.md` from the workspace (or whatever filename the user references).

**No spec found:** abort with: *"No Agent Spec found. Skill 3 requires a fully-detailed spec produced by Skill 1 → Skill 2. Invoke Skill 1 (Agent Spec Designer) first."*

### 2.3 Pre-flight gates

Three gates run before any assembly work. All are blocking. Refusal at any gate emits a clear message and halts; no JSON is produced.

#### Gate A — Completeness

Walk section 5. Count entries with status `[structural]` or `[detailed-revisit]`. If the count is greater than zero, refuse:

> Skill 3 will not assemble an incomplete spec. Section 5 has [N] intents still pending: [list with status per intent]. Run **Skill 2 (Intent Detail Author)** to detail them, then re-invoke Skill 3.

The list shows identifier + status (e.g., `validate_customer_address [structural]`, `confirm_appointment [detailed-revisit]`), not detail level.

Cross-check against section 7.5 (which Skill 2 maintains). If 7.5 says zero pending but section 5 has pending entries, that's a Skill 2 bookkeeping bug — surface it: *"Spec inconsistency: section 7.5 reports 0 pending, but section 5 has [N] intents in non-detailed state. Re-run Skill 2 once to refresh, then re-invoke Skill 3."*

#### Gate B — Parseability

Run the strict-template parser (§3) over the spec. The first deviation halts parsing and produces a structured error. No partial assembly.

Parseability is checked before completeness in cases where the file is malformed at the section-header level (e.g., section headers missing entirely) — in that case, Skill 3 cannot even tell which intents are pending. Practical order: try a quick scan for the seven `## N.` section headers first; if they're missing, Gate B fires first. If headers are present, Gate A fires first.

#### Gate C — RT=2 verification

For every intent whose section-4 **Response Type** is 2 (RT=2 / API Call), verify a matching entry exists in spec section 7.6 (the RT=2 API verification log). If any RT=2 intent has no 7.6 entry, refuse:

> Skill 3 will not assemble an RT=2 intent whose API was never verified. Intent(s) missing a section 7.6 verification record: [list]. Re-run **Skill 2 (Intent Detail Author)** on each — it hard-verifies the live API (real `curl`, 2xx + every declared response path present) and writes the 7.6 record. There is no waiver.

This is a backstop: a hard-verified spec reaches Skill 3 with every RT=2 intent already `[detailed]` (Gate A) and logged in 7.6. Gate C catches a hand-edited spec that flipped an intent to `[detailed]` without verifying.

---

## 3. Strict-template parsing

### 3.1 The deterministic parse principle

The Agent Spec template is documented in Doc 2 §3 and codified in Skill 1's `spec-skeleton.md`. Skill 3 reads it as a fixed grammar — no synonyms, no flexibility, no creative tolerance.

Specifically, the parser expects:

- **Section headers exact:** `## 1. Bot Identity`, `## 2. Persona Bundle`, `## 3. Caller Silence Behavior`, `## 4. Intent List (Structural)`, `## 4.5 Available Variables`, `## 4.6 Global/System Catalog Intents`, `## 5. Intent Details`, `## 6. Cross-References`, `## 7. Generation Metadata`. Exact strings, exact numbering, exact punctuation. `## 1: Bot Identity` is a parse error. `## Bot Identity` is a parse error.
- **Section 4.6 (optional):** either the literal `[none]`, or one or more `### Catalog Intent: <IntentId> — <Name>` blocks, each with `**Wiring:** silence-forward only|triggerable global` and a `**Definition:**` fenced ```json block. The JSON block must parse and carry a positive-integer `IntentId` and an `IntentCategoryId`. A malformed block or a non-positive `IntentId` is a parse error (§3.2) — Skill 3 does NOT repair it.
- **Field labels exact:** `**Bot Name:**`, `**Identifier:**`, `**Description:**`, `**Account ID:**`, `**Primary Language:**`, `**Channels Active:**`, `**Voice Name:**`, `**AI Model Config:**`. Bold markdown around the colon-terminated label, exactly as written.
- **Section 1 optional limit fields (v1.13.0; maxDurationLayerId default revised v1.14.0):** `**Daily limit:**` (int), `**Daily limit layer:**` (int), `**Max duration layer:**` (int), `**Daily limit sentence:**` (free text), `**Max duration sentence:**` (free text), `**IVRLayerSelect_2:**` (int). All optional; absence parses to defaults 600 / 3 / **0** / production-default sentence / production-default Hebrew sentence / 3 (see §4.2.2). A non-integer where an int is expected is a parse error.
- **Section 1 `**Negative instructions:**` (v1.16.0, optional):** free text. **Parse-only — NOT emitted to the wire JSON** (the wire field name is unverified). When present, Skill 3 emits a MANDATORY POST-IMPORT banner step telling the operator to paste the text into the UI's AI Security Settings → Negative Instructions field (§7.2). Absence ⇒ no banner step.
- **Status markers exact:** `[structural]`, `[detailed]`, `[detailed-revisit]`. No synonyms (e.g., `[done]`, `[in progress]`).
- **Unknown markers exact:** `<UNKNOWN: <description>>`, `<INCOMPLETE: <description>>`, `[not configured]`. The angle-bracket format is not optional; `(UNKNOWN: ...)` is a parse error.
- **Intent header in section 4:** `### Intent N: <identifier>` where N is the 1-based ordinal and identifier is snake_case. The number determines section 4 ordering (used for first-intent start-marker logic in `botIntents[]`).
- **Bot-intent role in section 4:** `**Bot-intent role:** <value>` where `<value>` is exactly one of `entry`, `global`, `chained`. The field is **optional**; absence is parsed as `chained`. Any other value (e.g. `start`, `escalation`, a list) is a parse error per §3.2. This field drives §4.3.3 botIntents membership/type.
- **Staggering fields in section 4 (v1.13.0, optional):** `**Captures answer to:**` (free text) and `**Asks next:**` (free text, or the literal `[none — terminal]`). Absence ⇒ the staggering-dependent checks skip for that intent.
- **Terminal outcome in section 4 (v1.13.0, optional; RT=1 only):** `**Terminal outcome:** <slot_name> = <value-part>`. Two-mode grammar: a double-quoted `<value-part>` ⇒ **fixed** mode (the exact pinned string); an unquoted free-text `<value-part>` ⇒ **captured/dynamic** mode (a description of how the value is captured or composed). A line without `<slot_name> =` is a parse error. `<slot_name>` must be snake_case and is cross-checked against the intent's slot list in CHK-20.
- **Sensitive in section 4 (v1.13.0, optional):** `**Sensitive:** true|false` only. Absence parses as `false`. Any other value is a parse error.
- **IsSilenceIntent in section 4 (v1.14.0, optional):** `**IsSilenceIntent:** true|false` only. Absence parses as `false`. Any other value is a parse error. Drives the intent-root `IsSilenceIntent` integer (§4.3.1 row 13).
- **Intent header in section 5:** `### Intent: <identifier>` (no ordinal). Identifier matches a section 4 entry.
- **Section 4.5.5 (v1.13.0, optional):** header exact `### 4.5.5 CustomData keys (per-call payload)` under `## 4.5 Available Variables`; entries `- \`{{key}}\` — <meaning>`. Absence ⇒ empty CustomData key list (CHK-07 then allows only 4.5.1–4.5.4 references).
- **Slot lines in section 4:** numbered list under `**Slots:**` heading, format `[slot_name] — \`ParameterTypeId\` [N], Required [\`true\`|\`false\`], Order [N], OptionList [if ENUM], DefaultValue [value]`. The `DefaultValue` segment is optional (v1.16.0); absence parses to `""` (the pre-v1.16.0 slot-line format without the segment remains valid).
- **Transition lines in section 4:** numbered list under `**Transitions out:**` heading, each item is a target intent identifier optionally followed by a parenthetical role label (e.g., `1. get_available_slots (success path)`).
- **RT-specific sub-labels in section 4:** for RT=1 intents, `**Layer:**` followed by an integer. For RT=2 intents, `**URL:**`, `**Method:**`, `**Headers:**`, `**Body:**`, and `**API silence behavior:**` (the silence block has six sub-bullets exact: `silence_duration:`, `silence_loops:`, `silence_sentence:`, `silence_ending_sentence:`, `silence_instructions:`, `fallback intent:`). For RT=3 intents, the RT-specific block is empty (no sub-bullets). For RT=4 intents, `**Dial source:**` (`parameter` | `static`), then either `**Parameter phone:**` (slot identifier, when dial-source=parameter) or `**Phone1:** / **Phone2:** / **Phone3:**` (when dial-source=static); plus `**selectdial_option:**`, `**NEXT_VO_ID:**`, `**MAX_DIAL_DURATION:**`, `**Record:**`, optional `**Announcement:**` / `**Loading announcement:**` / `**Post-execution intent instructions:**`, and `**Response success:**` (object with `instructions` key).
### 3.2 Parse errors

A deviation from the strict template is a **parse error, not an interpretation
opportunity** — Skill 3 halts and reports rather than guessing at intent. Report every
deviation found in one pass, so the user fixes the spec once instead of iterating.

When a parse fails, read `stages/parse-errors.md` for the structured error format and the
worked examples of the deviations that occur in practice.

| Bot-intent role value off-grammar | `Expected: '**Bot-intent role:** entry\|global\|chained'. Found: '**Bot-intent role:** start'. Fix: use one of the three canonical role values (or omit for chained).` |
| Terminal outcome missing slot assignment (v1.13.0) | `Expected: '**Terminal outcome:** <slot_name> = "<fixed value>"' or '**Terminal outcome:** <slot_name> = <capture/compose description>'. Found: '**Terminal outcome:** הלקוח אישר הכל'. Fix: name the owning slot and use '=' (quote the value only when it is a fixed pinned string).` |
| Sensitive value off-grammar (v1.13.0) | `Expected: '**Sensitive:** true\|false'. Found: '**Sensitive:** yes'. Fix: use lowercase true or false (or omit for false).` |
| IsSilenceIntent value off-grammar (v1.14.0) | `Expected: '**IsSilenceIntent:** true\|false'. Found: '**IsSilenceIntent:** 1'. Fix: use lowercase true or false (or omit for false).` |

The transition-target check (last two rows) blurs into cross-reference territory — it's caught at parse time because it's a dangling identifier discoverable from sections 4-5 alone, and Skill 3 already has the data. Treating it as a parse error rather than waiting for §15.4 lets the user fix one thing at a time.

---

## 4. Spec-to-wire-format assembly

Run only if all three pre-flight gates pass and the parser succeeds. Assembly happens in
memory; nothing is emitted until §6 (cross-reference pass) also passes.

**Read `stages/assembly-mapping.md` before emitting any field.** It carries the whole
mapping and the emission order, which is part of the contract:

| Step | What it covers | Load |
|---|---|---|
| 4.1 | ID placeholder allocation — the negative-integer ranges per ID kind | `stages/assembly-mapping.md` §4.1, before allocating any ID |
| 4.2 | Top-level wrapper, `ActiveVersionInfo`, both `AIModelConfig` objects, the lean `created` payload, `prompts`, `silence_behaviour` | `stages/assembly-mapping.md` §4.2, before emitting model or bot-level fields |
| 4.3 | `intentList` — the six parallel collections and their field order | `stages/assembly-mapping.md` §4.3, before emitting intents |
| 4.4 | Per-RT `IntentResponces.Configuration` shapes (RT=1/2/3/4) | `stages/assembly-mapping.md` §4.4, when emitting each intent's response |
| 4.5 | Quirk preservation — verify the assembled structure against the §16 contract | `stages/assembly-mapping.md` §4.5 + Appendix A, after §4.4 |
| 4.6 | Sentinel bookkeeping for spec unknowns | `stages/sentinels-and-banner.md` §4.6, after §4.5 |

Two rules that gate the whole step and therefore stay here:

- **Never invent a value.** Every emitted field traces to a spec field, a documented
  constant, or a fail-loud sentinel. If the spec doesn't say, emit the sentinel and let the
  banner surface it — do not infer, and do not fall back to a plausible default.
- **Emission order is contractual.** The tables in the stage file are ordered to match the
  production export. Do not reorder keys for readability.

## 5. Section 6 regeneration sanity check

After §4 assembly and before §6: regenerate spec section 6 from sections 4-5 and compare it
against what the spec already carries. **Drift is a soft warning, never blocking** —
sections 4-5 are authoritative, section 6 is derivative. Record drift in the banner and in
spec section 7.3; do not auto-fix and do not halt.

Read `stages/sentinels-and-banner.md` §5 for the per-subsection regeneration sources and the
drift-reporting format.

## 6. The §15.4 cross-reference pass

After §4 assembly and §5 sanity check: run the **24-check cross-reference pass**.

**The checks live in exactly one place.** Read and execute
`${CLAUDE_PLUGIN_ROOT}/references/verification-procedure.md`. That file carries
CHK-01…CHK-24 with their run order, model gating, severity assignment, per-check failure
routing, and the output contract both execution paths emit. No check procedure text is
duplicated here — if you find yourself recalling a check from memory, re-read the file.

What stays in this SKILL.md is **decision logic**: which path executes the procedure
(§6.0–§6.2), and what Skill 3 does with the results (§6.4).

Coverage summary (the procedure file is authoritative): eight checks per Doc 1 §15.4,
three from Compass doctrine, three botIntents-role integrity checks, one
duplicate-global-intent check, and nine field-placement doctrine checks. CHK-01…CHK-07,
CHK-11…CHK-13, CHK-15, CHK-16…CHK-21 and CHK-24 are blocking; CHK-08 is banded by token
count; CHK-10 blocks on mismatch; CHK-09, CHK-14, CHK-22, CHK-23 are advisory.

### 6.0 Execution mode

**Inline execution is the default and authoritative path.** If you are able to delegate to
the `voicenter-bot-builder:spec-verifier` agent, do so — a fresh-context verifier reads what
the spec says rather than what it remembers intending, and is preferred wherever it is
available. Otherwise — **including whenever you are uncertain whether the agent is
available** — execute `${CLAUDE_PLUGIN_ROOT}/references/verification-procedure.md` yourself,
inline, per §6.2.

**Never block on delegation availability.** Do not probe for it, do not test for it, and do
not ask the user which path to use. Both paths run the same procedure file and emit the same
output contract, so the verdicts are comparable either way. A runtime without subagents
(claude.ai consumer chat) simply takes the inline path with no user-visible difference.

Delegation prompt — use this template verbatim. The subagent starts with a fresh, isolated
context and sees nothing but this prompt (C3), so every path it needs must be spelled out:

```
Verify the Agent Spec at: <absolute spec path>
Plugin root: <resolved plugin root path>
Execute the verification procedure at
<plugin root>/references/verification-procedure.md and return the report in
its Output Contract format. Report only; do not modify any file.
```

Resolve `<absolute spec path>` and `<plugin root>` before sending — the subagent cannot ask
a follow-up question.

### 6.1 Delegated path

When a report comes back from the verifier:

1. **Validate it against the contract** before trusting it. A report is valid iff the
   `## Verification Report` header is present, the Verdicts table contains exactly
   CHK-01…CHK-24 in order, and every verdict is in the allowed vocabulary
   (`pass` / `FAIL` / `error`).
2. **If valid: consume it verbatim.** Apply blocking/advisory handling (§6.4) and the
   report's routing recommendations exactly as the inline path would apply its own results.
   Do not summarize it, soften it, re-rank its findings, or re-derive severity.
3. **If invalid: discard it and fall back to §6.2 inline.** Log exactly one line to the
   user — `verifier report malformed — running checks inline` — and proceed. This guards
   against a stale or foreign verifier version returning a shape this Skill 3 cannot read.
4. **If the report is the structured-error form** (`## Verification Report — ERROR`), treat
   it as an unrunnable verification: surface the error and action lines to the user and halt.
   Do not assemble on an unverified spec.

### 6.2 Inline path (degraded mode)

This is **degraded mode** — not because the checks are weaker (they are the same 24 from the
same file), but because there is no context isolation. You watched this spec get built, so
your memory of what was intended can quietly substitute for what is written. That asymmetry
is the only difference between the two paths, and it is why the discipline below is
mandatory rather than advisory. Expect slightly lower sensitivity here on the judgement-heavy
checks (the CHK-07 and CHK-16…CHK-20 classes).

**Fresh-eyes discipline — do this before checking anything:**

> Re-read the spec in full from the artifact — not from memory of this conversation. Verify
> against what is written, not what was intended. Treat the spec as if someone else authored
> it.

Then execute `${CLAUDE_PLUGIN_ROOT}/references/verification-procedure.md`: run CHK-01…CHK-24
in its run order, apply its severity assignments, and emit the same output contract a
delegated run would produce. The contract is not optional on this path — MS6's equivalence
test compares the two paths' reports mechanically.

### 6.3 Failure routing

Per-check routing lives in the procedure file — every `CHK-NN` block carries its own
**On failure route to:** line, and the emitted report restates it under *Routing
recommendations*. Skill 3 consumes those recommendations verbatim; it does not re-derive
or reinterpret them.

Appendix B has the consolidated routing table.

### 6.4 Pass/fail behavior

**All checks pass (no blocking failures):** proceed to §7 emission.

**Any blocking check fails:** halt. Emit no JSON, append the failure log to spec section 7.3,
and report every failing check in one pass — the user should be able to fix everything at
once rather than re-running to discover the next problem. Read
`stages/sentinels-and-banner.md` §6.4 for the report format.

Skill 3 does not invoke Skill 1 or Skill 2 itself. The user reads the routing recommendation
and invokes the appropriate skill (locked decision C, architecture §9.1), then re-invokes
Skill 3.

---

## 7. Emission

Run only if §3 (parse), §5 (regen sanity check), and §6 (cross-reference pass) all complete. §5's drift is a soft warning, not a fail; §6 is the hard gate.

### 7.1 JSON output structure

A single JSON object per Doc 1 §4 (the top-level wrapper). Pretty-printed with 2-space indent, UTF-8, keys in the order Doc 1 documents them (Doc 1 ordering matters for human reading even though the platform parses by key not position).

The output is **valid JSON only** — no comments, no trailing commas, no JSONC extensions. The banner is delivered separately (§7.2).

### 7.2 Banner format

The banner is rendered **above** the JSON (single-conversation) or written as a sidecar file
(Claude Code). It is plain text and never embedded in the JSON, so the user can copy the
JSON code block straight into the importer without stripping anything.

Every banner section is emitted even when its content is "(none)" — a consistent shape
matters more than brevity, because operators learn to scan for specific headings.

Read `stages/sentinels-and-banner.md` §7.2 for the section-by-section format, the
DOCTRINE SENTINELS population rule, and Appendix C's worked example.

### 7.3 Filename convention

`bot-<bot-snake-name>-<YYYY-MM-DD>.json`

Where `<bot-snake-name>` is the spec section 1 `**Identifier:**` value (a snake_case ASCII identifier captured by Skill 1 at interview time). If the field is missing (legacy spec from before this patch), Skill 3 falls back to ASCII-folding `**Bot Name:**`, then to `bot`.

Companion banner file (Claude Code only): `bot-<bot-snake-name>-<YYYY-MM-DD>.banner.md`.

If the file already exists in the workspace (Claude Code), append `-<counter>` before `.json` (e.g., `bot-yuval-2026-05-01-2.json`). Single-conv runtime doesn't have files; just emit the code block.

### 7.4 Runtime-specific delivery

**Single-conversation runtime:**

1. Render the banner as plain text in the chat message.
2. Render the JSON in a fenced code block (` ```json `).
3. Append a closing message:

> Bot JSON ready. Copy the code block above, save as `bot-<name>-<date>.json`, replace any `<USER_TO_FILL: ...>` strings or `-999` IDs with real platform values listed in the banner, then import to Voicenter via the platform UI.

**Claude Code runtime:**

1. Write the JSON to `bot-<bot-snake-name>-<YYYY-MM-DD>.json` in the workspace.
2. Write the banner to `bot-<bot-snake-name>-<YYYY-MM-DD>.banner.md` in the workspace.
3. Append a closing message:

> Bot JSON written to `<filename>`. Banner sidecar at `<banner filename>`. Replace any `<USER_TO_FILL: ...>` strings or `-999` IDs (full list in the banner) with real platform values, then import to Voicenter.

### 7.5 Spec section 7.3 updates

Every Skill 3 invocation appends one entry to spec section 7.3 — on success and on failure
alike, so the spec carries a complete audit trail of assembly attempts. Read
`stages/sentinels-and-banner.md` §7.5 / §7.6 for the two entry formats.

## 8. Anti-list — what Skill 3 does NOT do

Skill 3's main risk is doing too much: filling in plausible-looking values for unknowns, smoothing over template deviations, auto-fixing cross-reference violations, deciding RT-specific defaults the spec didn't specify. This list is the guard.

- **Author any text content.** No `validationPrompt`, no `intentInstructions`, no persona, no announcements. All text is verbatim from the spec. If the spec has `<UNKNOWN>` for a text field, Skill 3 emits the sentinel — never invents.
- **Interpret deviations from the strict template.** First deviation halts the parser. Skill 3 does not best-effort guess what the user meant. Does not "smooth over" minor formatting issues. Does not accept synonyms for status markers. Does not tolerate alternate intent header conventions.
- **Auto-fix cross-reference violations.** Dangling IDs, missing API silence pairings, unresolvable Mustache references — none of these get repaired by Skill 3. The error report routes the user to the responsible skill (Skill 1 patch or Skill 2 reactivation per Doc 2 §7.5). The user invokes that skill; Skill 3 re-runs from scratch on the next invocation.
- **Modify the spec beyond appending to section 7.3.** No edits to sections 1-6. No changes to status markers. No regeneration of section 4.5.3 (Skill 2's job) or section 6 (Skill 1/2's job; Skill 3 only compares as a sanity check).
- **Skip the cross-reference pass.** Under any circumstance. Even if the user explicitly asks ("just give me the JSON, I'll fix it later") — the pass is non-negotiable per locked decision C. The cross-reference pass is the difference between a JSON that the platform can import but the runtime can't execute, and a JSON the runtime actually runs.
- **Skip verification because delegation is unavailable.** The `spec-verifier` agent is an enhancement, not a prerequisite. When it cannot be reached — or when you are simply unsure whether it can — run the procedure inline per §6.2. Inline is not optional, and "no subagent available" is never a reason to assemble unverified.
- **Summarize, soften, re-rank, or reinterpret the verifier's report.** A valid report is consumed verbatim (§6.1): its verdicts, severities and routing lines pass through unchanged. You may not downgrade a blocking failure to a note, merge findings, or substitute your own judgement about which failures matter. If the report is malformed, discard it entirely and re-run inline — never partially salvage it.
- **Suppress fail-loud sentinels.** They are the entire point of the unknown-value model (decision B). The banner makes them visible at import time so the user catches them before deploying. Quiet defaults (empty string, 0, null) would import successfully and break at runtime, which is much harder to diagnose. **Exception (v1.12.0): the RT=1 `Configuration.layer`** defaults to `0` (root layer) rather than a `-999` sentinel — Skill 1 fetches the real layer number from the MCP (§2.4.A), and `0` is itself a valid landing layer, so the quiet default does not break at runtime. Layer is the only field exempt from fail-loud.
- **Emit JSON if any blocking cross-reference check fails.** Partial emission is worse than no emission — a partial JSON looks deployable, the user might import it and find out at runtime that it's broken. Hard halt is the correct behavior.
- **Emit `max_turns` / `max_turns_sentence` as direct siblings of `prompts` inside `IntentConfig` (the pre-v1.13 shape).** Since v1.13.0 they live inside `IntentConfig.additional` together with `sensitive` (§4.3.1, golden-export shape).
- **Emit an `announcement` key on an RT=1 intent (v1.14.0).** RT=1 `Configuration` carries only `layer` + `intentLoadingAnnouncement`; the farewell lives in the predecessor's `intentInstructions` (§4.4 RT=1; check 20).
- **Run iteratively or repeatedly within a single invocation.** One parse, one assembly, one sanity check, one cross-reference pass, one emission. If something fails, halt and report. The user re-invokes after fixing.
- **Invoke Skill 1 or Skill 2.** Skill 3 reports routing recommendations; the user invokes the relevant skill manually (per architecture §9.1; skill-to-skill direct invocation is v3).
- **Validate content quality.** Whether the persona is good, whether the `validationPrompt` is well-styled, whether the slot collection logic makes sense — none of these are Skill 3's concern. Skills 1 and 2 own content quality. Skill 3 only validates structural/cross-reference correctness.
- **Test the bot at runtime.** No simulation, no behavior check, no deployment, no end-to-end flow. v1 lifecycle ends at "JSON ready for the user to import manually" per locked decision G.
- **Query the Voicenter platform.** No MCP in v1 (per architecture §9). The model catalog is hardcoded in `model-catalog.md`; the user's account-specific call-context variables come from spec section 4.5.1 (the user's claim, trusted at face value).
- **Modify quirk preservation.** Doc 1 §16 lists the base quirks and Appendix A extends them (v1.5.0 corrections; v1.13.0 golden-export rows 20–23); Skill 3 emits exactly what they prescribe. Any "this looks redundant, I'll skip it" reasoning is forbidden — the platform's import endpoint may strictly require these keys. When in doubt, emit what production samples emit.
- **Skip the banner.** Even on a spec with zero unknowns and zero drift, the banner is emitted with empty sections (`(none)`, `(in agreement)`). The banner contract is consistent regardless of spec state.
- **Use any sentinel value other than the ones in §4.6.** Strings → `<USER_TO_FILL: ...>`, IDs → `-999`, objects → `{}` with banner note. No alternate forms ("UNKNOWN", "TBD", "REPLACE_ME", `null` for IDs), no nuanced sentinels per field type. Consistency is the point.
- **Tolerate intent identifier collisions.** If two intents share an identifier across section 4 (which shouldn't happen post Skill 1 validation but could from a hand-edit), Skill 3 reports a parse error rather than silently reusing the cached ID. Identifier uniqueness is structurally required.
- **Rewrite or compress prompt text to meet the Compass rule 1 token budget.** When check 8 (token budget) fires at the blocking threshold (≥ 5,000 tok), Skill 3 halts and routes to Skill 1 / Skill 2 patch — it does not auto-trim, summarize, paraphrase, or re-section the user's prompt content. The user owns the prose; Skill 3's job is to measure and refuse, never to author.
- **Resolve Compass advisories without user input.** Rules 3, 4, 5, 6, 7, 9, 10 are all advisory-only at their owning skill. If a spec arrives at Skill 3 with unresolved advisories in section 7.3, Skill 3 emits the corresponding DOCTRINE SENTINELS banner lines (per rule 13) — it does not silently apply fixes. The user decides at authoring time; Skill 3 only reports.

---

## Appendix B — Doc 2 §7.5 routing table

When Skill 3 fails, it tells the user which skill to invoke for the fix.

**Cross-reference check routing is not duplicated here.** Every `CHK-NN` carries its own
**On failure route to:** line in `${CLAUDE_PLUGIN_ROOT}/references/verification-procedure.md`,
and the verification report restates it under *Routing recommendations*. Consume those
verbatim (§6.1). This table covers only the failure classes that arise **outside** the
cross-reference pass.

| Failure type | Source | Route |
|---|---|---|
| Parse error: section header / field label deviation | §3 | **Manual fix** — usually a spec hand-edit. Restore the strict-template form, re-invoke Skill 3. |
| Parse error: orphan section 5 entry / undeclared transition target | §3.3 | **Skill 1 patch mode** — structural issue (added/removed an intent, broke transition references). |
| Pre-flight gate A: incomplete spec | §2.3 | **Skill 2 reactivation** — detail the remaining `[structural]` / `[detailed-revisit]` intents. |
| Pre-flight gate C: RT=2 intent missing 7.6 verification | §2.3 | **Skill 2 reactivation** — re-run on the unverified RT=2 intent(s); Skill 2 curls the live API and writes the 7.6 record. |
| Quirk verification fail (§4.5) | stage file §4.5 | **Skill 3 internal bug** — emission code drifted from the §16 contract. Report, don't try to repair. |
| Section 6 regeneration drift | §5 | **Soft warning, not blocking** — recorded in the banner. User can fix via Skill 1 patch mode if it bothers them; Skill 3 emits anyway. |
| Verifier report malformed | §6.1 | **Not a user-facing failure** — discard the report, log one line, re-run the procedure inline per §6.2. |
