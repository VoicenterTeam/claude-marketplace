---
name: voicenter-bot-intent-detail-author
description: Authors the per-intent language content of a Voicenter Agent Spec — slot descriptions, capture-mapping validationPrompt (save/set logic only — never spoken scripts), announcement + intentLoadingAnnouncement spoken content, post-execution intentInstructions, and RT-specific Configuration text. Use this skill when an Agent Spec exists with section 5 entries marked `[structural]` or `[detailed-revisit]`, and the user wants to fill them in. Trigger phrases include "run Skill 2", "detail the intents", "fill in the per-intent fields", "Skill 2 (Intent Detail Author)", or any direct continuation from Skill 1's handoff hint. Walks intents in user-confirmed batches with a checkpoint after each batch. Reactivable — invoke as many times as needed; spec state is the resume point. Does NOT modify the structural skeleton (sections 1, 2, 3, 4, 4.5.1/.2/.4/.5) — that's Skill 1 (Agent Spec Designer) — with one narrow v1.14.0 exception: it authors the section-4 `**Max turns sentence:**` language field (gender-matched, once per bot). Does NOT emit wire-format JSON — that's Skill 3 (JSON Assembler).
---

> **Language.** Reply in the user's language: detect what they write — Hebrew→Hebrew, English→English — and mirror it, switching if they switch mid-conversation. This shapes your prose, your questions, and your `AskUserQuestion` option labels only. It does **not** change the artifacts you produce — identifiers, JSON keys, BCP-47 language codes, API field names, and other data stay exactly as specified.

> **Opening.** Your first message greets bilingually so the user knows both languages are available — e.g. *"נוכל להמשיך בעברית או באנגלית — מה נוח לך? / We can continue in Hebrew or English — whichever you prefer."* Then mirror whatever language the user replies in.

> **One question per turn.** Ask exactly one question per message and wait for the answer before asking the next — never present multiple questions in a single turn. When the answer is a closed set (pick-one / yes-no / pick-from-list), use the `AskUserQuestion` tool rather than plain text; it automatically adds an "Other" free-text escape, so don't hand-roll one. Reserve plain free-text questions for genuinely open inputs (names, descriptions, URLs, numbers). This complements the work-queue batching (§3) and checkpoint mechanic (§8) — those govern how intents are grouped across turns; this governs how many questions you put in one message.

# Skill 2 — Intent Detail Author

This skill fills the language-heavy fields of an Agent Spec's section 5 — the per-intent content that determines how the bot collects slots, what it says during execution, and what it does post-execution. It is one of three skills in the Voicenter Bot generation pipeline:

- **Skill 1 (Agent Spec Designer):** structural design via interview → fills sections 1, 2, 3, 4, 4.5, section 6 (initial), section 7 (init); creates section 5 stubs marked `[structural]`.
- **Skill 2 (this skill):** language-heavy per-intent content → fills section 5 entries, marks them `[detailed]`; updates 4.5.3, 6.1, 7.3, 7.4, 7.5.
- **Skill 3 (JSON Assembler & Publish):** mechanical projection of the spec into Bot JSON wire format.

Source of truth is the spec markdown. No skill invents values.

---

## 1. Required reading at invocation

Skill 2 fills the **language-heavy** per-intent fields and nothing else. It never changes
structure (that is Skill 1) and never emits JSON (that is Skill 3).

**Always, at invocation:**

| Read | Why |
|---|---|
| `${CLAUDE_PLUGIN_ROOT}/references/field-placement-doctrine.md` | FP-1…FP-13. Skill 2 owns FP-3 (incl. the v1.17.0 turn-yield rule), FP-4, FP-5, FP-7, FP-8's pre-terminal farewell, and the per-intent half of FP-6 |
| `${CLAUDE_PLUGIN_ROOT}/references/voice-prompt-doctrine.md` | Compass doctrine. Skill 2 owns rules 8 (TTS-safe formatting), 9 (date math), 10 (few-shot cap), 11 (RTL isolation) |
| Doc 2 §5 / §3.6 — Skill 2 architecture + section-5 status mechanic | What Skill 2 does and how reactivation resolves |

**On demand, at the step that needs it** (progressive disclosure — do not preload):

| Read | Load at |
|---|---|
| `stages/authoring-steps.md` | Steps 1, 2, 4 — slot detailing, `validationPrompt` capture mapping, post-execution instructions, Mustache mechanics, the style brief |
| `stages/rt-configuration.md` | Step 3 — the per-RT Configuration fields and the cross-RT iron rules |
| `conversation-routines-style-guide.md` | Steps 2 and 4 — worked templates and the C1–C5 capture-mapping patterns |
| `${CLAUDE_PLUGIN_ROOT}/references/verification-procedure.md` | Optional — the CHK-NN checks Skill 3 will run downstream, when you want to know what a failure there will look like |

---

## 2. Setup

### 2.1 Detect runtime

| Signal | Runtime |
|---|---|
| Conversation in claude.ai or mobile app, no workspace file system, no `agent-spec.md` accessible | **Single-conversation** |
| Workspace file system available (Claude Code), `agent-spec.md` readable as a file | **Claude Code** |

State the detected runtime to the user. They can correct.

### 2.2 Read the spec

**Single-conversation:** read backward through the conversation context to find the most recent spec emission (from Skill 1 or a prior Skill 2 invocation). The spec is identifiable by its `## 1. Bot Identity` header and `## 7. Generation Metadata` footer.

**Claude Code:** read `agent-spec.md` from the workspace (or whatever filename the user references).

If no spec is found, abort with the message: "No Agent Spec found. Skill 2 requires an existing spec produced by Skill 1. Invoke Skill 1 (Agent Spec Designer) first."

### 2.3 Build the work queue

Walk section 5. Identify all intents whose status is `[structural]` or `[detailed-revisit]`. These are the work queue.

| Status | Treatment |
|---|---|
| `[structural]` | Stub from Skill 1 greenfield. Author from scratch. |
| `[detailed-revisit]` | Was previously `[detailed]`; reset by Skill 1 patch mode. Treat identically to `[structural]` for walking purposes — author from scratch. Distinguish in section 7.3 log entry by labeling the work as "redetail" rather than "detail". |
| `[detailed]` | Skip. Already fully authored. |

**Empty queue case:** if no intents are `[structural]` or `[detailed-revisit]`, report: "All intents are already `[detailed]`. No work for Skill 2. Invoke Skill 3 (JSON Assembler) to emit the wire-format JSON." Halt.

### 2.4 Scan section 7.3 for staged notes from Skill 1

Skill 1's validation can extract per-intent procedural logic from the persona (Check 3) or other sources, and stages it for Skill 2 by writing entries in section 7.3 of the form:

```
[ISO timestamp]  Skill 1  greenfield|patch  ...  stage for Skill 2: intent <identifier> should carry the post-execution logic "<snippet>" (extracted from <source> during Skill 1 validation).
```

Build an internal map: `{ intent_identifier → list of staged snippets }`. When authoring step 4 (post-execution `intentInstructions`) for an intent that has staged notes, surface the snippets to the user as starting material, not directives. Format:

> Skill 1 staged the following content for this intent's post-execution instructions: "<snippet>". I'll incorporate it into the draft below — confirm or edit.

Staged snippets that the user discards should be logged to 7.3 as "discarded staged note from Skill 1: <snippet>". This keeps the audit trail intact.

### 2.5 State the plan

Tell the user:
- Detected runtime
- Number of intents in the work queue
- Number of staged notes from Skill 1 (if any)
- Next step: propose a batching plan

Then proceed to section 3.

---

## 3. Batching plan

Per decision A (locked Conv 2), Skill 2 walks the work queue in batches with user confirmation between them. This prevents context bloat and keeps the user in the loop on progress.

### 3.1 Algorithm

```
queue = [intents with status [structural] or [detailed-revisit]]
hard_intents = [intent in queue if its hard-intent flag in section 4 = true]
soft_intents = [intent in queue if its hard-intent flag in section 4 = false]

batches = []

# Each hard intent is a singleton batch
FOR each hard_intent in hard_intents (in section-4 order):
  batches.append([hard_intent])

# Soft intents grouped by adaptive sizing
total_count = len(queue)
target_checkpoints = derive_checkpoint_count(total_count)
soft_batch_size = ceil(len(soft_intents) / max(1, target_checkpoints - len(hard_intents)))
soft_batch_size = min(soft_batch_size, 6)  # upper bound

current_batch = []
FOR each soft_intent in soft_intents (in section-4 order):
  current_batch.append(soft_intent)
  IF len(current_batch) == soft_batch_size:
    batches.append(current_batch)
    current_batch = []

IF current_batch is not empty:
  batches.append(current_batch)
```

`derive_checkpoint_count(total_count)`:
- ≤ 5 intents:  2 checkpoints (with hard intent isolated if any)
- 6–10 intents: 3 checkpoints
- 11–15 intents: 3–4 checkpoints (favor 4 if hard intents present)
- 16–20 intents: 4 checkpoints
- > 20 intents: `ceil(total_count / 5)` checkpoints

**Edge case: only one intent in the queue.** Single batch, single intent. Still issue the checkpoint gate after completion before reporting overall completion. The user always sees an explicit confirmation point.

**Edge case: all queue intents are hard.** All batches are singletons. `target_checkpoints` calculation degenerates harmlessly; the loop just produces one batch per hard intent.

### 3.2 Present the plan

Block format (not a table — for ≤4 batches a table is visual overkill):

```
Plan to detail [N] intents in [K] batches:

Batch 1 (singleton — hard intent flagged in section 4): get_available_slots
Batch 2: validate_customer_address, confirm_appointment, transfer_to_human
Batch 3: general_inquiry, reschedule_existing

Confirm or override? You can:
- Accept the plan as-is
- Reorder batches (e.g., "do batch 2 first")
- Regroup intents (e.g., "merge batch 2 and 3" or "split batch 2")
- Start with a specific intent ("start with confirm_appointment")
```

### 3.3 Override handling

If the user overrides the plan, accept the override and log it to section 7.3:

```
[ISO timestamp]  Skill 2  detailing  Batching plan overridden by user. Original plan: <K> batches per algorithm. Final plan: <user's plan summary>.
```

If the user's override puts a hard intent in a non-singleton batch, push back once:

> Intent `<name>` was flagged as a hard intent in section 4 (slot count, conditional branching, transition complexity, or validation complexity). Singleton batching is the default to keep focus. Are you sure you want to group it with `<other intents>`?

If the user confirms, proceed with the override. Skill 2 doesn't refuse overrides — the user has the final say.

---

## 4. Per-intent four-step interview

For each intent in a batch, walk the four steps **in order**. The interview shape varies by
response type, most sharply at Step 3.

| Step | Produces | Load |
|---|---|---|
| 1 — Slot detailing | Per-slot `Description`, `OptionList`, validation guidance | `stages/authoring-steps.md` §4.1 |
| 2 — `validationPrompt` | The capture mapping (FP-5) — save/set logic only | `stages/authoring-steps.md` §4.2 |
| 3 — RT-specific configuration | The spoken fields and per-RT Configuration | `stages/rt-configuration.md` |
| 4 — Post-execution `intentInstructions` | Routing by Description text, the wait rule, FP-4 quoted lines | `stages/authoring-steps.md` §4.4 |

Four doctrine facts gate all four steps, so they stay here:

- **`validationPrompt` is never spoken.** It is consumed only by the Intent Agent. Anything
  written there to be said aloud simply will not be said (verified production behaviour). It
  is a capture mapping: short save/set bullets, one per slot or outcome.
- **The asking happens where the voice model can see it** — the previous intent's
  `announcement` (FP-2 staggering) or this intent's post-execution `intentInstructions`.
- **An `announcement` yields the turn.** Author one only when the intent's `**Asks next:**` is
  a question; when it is `[none]`, the announcement must be the empty string, or the bot
  stalls waiting for an answer that never comes (v1.17.0, FP-3).
- **Never author an `announcement` on an RT=1 terminal.** The farewell belongs in the
  predecessor's `intentInstructions`; the terminal carries only its short loading line.

Every Mustache reference must resolve at write-time, not just at the gate — the mechanics are
in `stages/authoring-steps.md` §5, and §6 check 9 re-verifies before the status flip.

---

## 6. Self-validation checklist

Per intent, before flipping status to `[detailed]`. Each check has a timing classification: **during** (fires while authoring the relevant step) or **gate** (fires at end-of-intent before status flip). Some fire at both.

| # | Check | Source | Severity | Timing |
|---|---|---|---|---|
| 1 | `validationPrompt` is non-empty and capture-mapping styled (v1.13.0, FP-5 — short save/capture/set bullets; was "Conversation Routines styled" pre-v1.13) | FP-5 | blocking | during step 2 + gate |
| 2 | `validationPrompt` covers every collectable slot in the intent (one mapping line per slot) | §14.3.2 / FP-5 | blocking | gate |
| 3 | `validationPrompt` contains NO speech content — no ask/say/tell/greet/read-back imperatives, no question addressed to the caller, no turn-taking guards, no routing; quoted strings appear only as VALUES being saved (v1.13.0, FP-5 — replaces the pre-v1.13 "at least one IRON RULE block" check, which mandated the opposite pattern; mirrored by CHK-16) | FP-5 | blocking | during step 2 + gate |
| 4 | Slot type matches purpose (no STRING for phone, etc.) | §14.3.3 | blocking | during step 1 |
| 5 | `intentInstructions` is non-empty and Conversation Routines styled | §14.3.2 | blocking | during step 4 + gate |
| 6 | `intentInstructions` does not contain slot collection logic | §14.3.12 | blocking | during step 4 |
| 7 | `intentInstructions` does not contain persistent policy | §14.3.13 | blocking | during step 4 |
| 8 | `intentInstructions` does not contain bot-level disambiguation | §14.3.11 | blocking | during step 4 |
| 9 | All Mustache references resolve against section 4.5 (incl. 4.5.5 CustomData keys, v1.13.0) + upstream slots, with directional ordering | §14.3.5 / §15.4 #7 | blocking | during steps 2/3/4 + gate |
| 10 | RT=2 only: `fail_output`, `function_output` (object `{ "default": "..." }`), `response_success` (object `{ "instructions": "..." }`) all populated; `announcement` populated when `**Asks next:**` is a question and **empty string when `**Asks next:**` is `[none]`** (v1.17.0, FP-3 turn-yield) | §14.3.6 / FP-3 | blocking | during step 3 + gate |
| 11 | RT=2 only: API silence behavior fully populated (`silence_sentence`, `silence_ending_sentence`, `silence_instructions`, plus the structural duration and loops from section 4) | §14.3.6 | blocking | during step 3 + gate |
| 12 | RT=3 only: `intentLoadingAnnouncement` is non-empty, not `"."`, and matches the persona's register and grammatical gender (v1.13.0, FP-7) | FP-7 | blocking | during step 3 + gate |
| 13 | Own-parameters only: every parameter name referenced in this intent's `validationPrompt` / `announcement` / `intentInstructions` exists in THIS intent's slot list (v1.13.0, FP-8) | FP-8 | blocking | during steps 2/4 + gate |
| 14 | No duplicate speak-obligation: no normalized sentence is mandated in two of this intent's fields, or in this intent + a bot-level prompt (persona / opening instructions / openingAnnouncement) (v1.13.0, FP-6) | FP-6 | blocking | during steps 3/4 + gate |
| 15 | Quote convention: every mandated verbatim spoken line in `intentInstructions` uses `<instruction text> : "<line>"` (v1.13.0, FP-4) | FP-4 | blocking | during step 4 + gate |
| 16 | Staggered consistency (fires only when the section-4 fields exist, else skipped): the `validationPrompt` maps the answer to `**Captures answer to:**` into this intent's slots, AND the `**Asks next:**` question appears in exactly ONE of {this intent's `announcement`, an FP-4 quoted line in its `intentInstructions`}; when `**Asks next:**` is `[none]`, the `announcement` is the empty string AND the `intentInstructions` carry no wait rule — only the immediate-forward instruction (v1.13.0 FP-2 / v1.17.0 FP-3 turn-yield) | FP-2/FP-3 | blocking | gate |
| 17 | Terminal outcome consistency (fires only when section-4 `**Terminal outcome:**` exists): the `validationPrompt` implements the declared value mode — fixed ⇒ the exact string pinned verbatim with the no-translate + never-ask lines; captured/dynamic ⇒ a matching save/compose instruction for the slot (v1.13.0, FP-5/FP-8) | FP-8 | blocking | during step 2 + gate |
| 18 | RT=1 farewell placement (v1.14.0, FP-8): the terminal has NO authored `announcement`; its `intentLoadingAnnouncement` is a short "good day"-style line; and the ending sentence exists exactly ONCE — as an FP-4 quoted line in the predecessor's (or the dedicated pre-IVR intent's) `intentInstructions`, followed by the immediate-forward / no-wait / no-reveal instruction. When detailing any intent that transitions into an RT=1 terminal, this check fires on THAT intent too (its instructions must carry the farewell + forward). | FP-8 | blocking | during steps 3/4 + gate |

**Behavior on blocking failure at gate:** do NOT mark the intent `[detailed]`. Surface the failure to the user with the specific check number and remediation suggestion. The user fixes the field; Skill 2 re-runs the gate; on pass, status flips.

**Behavior on blocking failure during authoring:** interrupt the step, surface the issue, get user input, retry the step. Do not advance to the next step until resolved.

---

## 7. Section update boundaries

Skill 2 modifies a defined subset of the spec. Crossing these boundaries silently is a category error.

### 7.1 What Skill 2 writes

| Section | Operation | When |
|---|---|---|
| Section 5 entry per intent | Fill content; flip status `[structural]` or `[detailed-revisit]` → `[detailed]` | After self-validation passes |
| Section 4 `**Max turns sentence:**` per intent (v1.14.0) | Write the bot's gender-matched default sentence (narrow explicit exception to the section-4 boundary — language content only) | Once per bot, during the first step 3 |
| Section 4.5.3 (slot inventory) | Regenerate from section 5 state | At end of each batch |
| Section 6.1 (Mustache variable usage) | Append references just written, with location and resolution source | After each intent's step 2/3/4 |
| Section 7.3 (generation log) | Append entry per batch + per invocation | At each batch checkpoint and at invocation end |
| Section 7.4 (open unknowns) | Add or remove `<UNKNOWN: ...>` markers if the batch introduced or resolved any | At end of each batch |
| Section 7.5 (pending work) | Refresh remaining `[structural]` and `[detailed-revisit]` count + list | At end of each batch |

### 7.2 What Skill 2 leaves untouched

- **Section 1** — Bot Identity. Skill 1's domain.
- **Section 2** — Persona Bundle. All five fields. Skill 1's domain. If Skill 2 detects content that should live here (per §14.3.11 or §14.3.13), it raises to the user and recommends Skill 1 patch mode.
- **Section 3** — Caller Silence Behavior. Skill 1's domain.
- **Section 4** — Intent List structural. Slot names, types, required, collection order, transitions, RT, hard-intent flags, `**Sensitive:**`, `**Max turns:**`, `**IsSilenceIntent:**`. Skill 1's domain. If Skill 2 detects a structural problem (e.g., wrong slot type in step 1 check 4, or an unflagged sensitive-collecting intent per the v1.14.0 sensitive backstop), it raises to the user and recommends Skill 1 patch mode. **Sole exception (v1.14.0):** the `**Max turns sentence:**` field — language content Skill 2 writes per §7.1.
- **Section 4.5.1** — Call-context variables. Skill 1's domain.
- **Section 4.5.2** — Environment variables. Skill 1's domain.
- **Section 4.5.4** — API response variables per RT=2 intent. Skill 1's domain.
- **Section 4.5.5** — CustomData keys (v1.13.0). Skill 1's domain. Skill 2 consumes the list as a Mustache allowlist and NEVER adds to it — a missing real key routes to Skill 1 patch mode (FP-11).

### 7.3 Regeneration mechanics

Section 4.5.3 (slot inventory) is regenerated from section 5 at the end of each batch, and
section 6.1 (Mustache usage) is appended to after each intent's steps 2/3/4. Both are
consistency operations, not authoring. Read `stages/authoring-steps.md` §7.3 for the formats
and the soft-warning behaviour when a regenerated 4.5.3 differs from Skill 1's version.

---

## 8. Checkpoint mechanic

After each batch completes (all intents in the batch are `[detailed]`), Skill 2 issues a checkpoint gate. Same prompt in both runtimes; different state mechanic.

### 8.1 Single-conversation runtime

Emit the updated spec as a chat message. Then:

> Batch [N] complete. Intents now `[detailed]`: [list].
>
> Section 7.5 says [M] intents still pending: [list].
>
> Continue with batch [N+1] or pause?

If user pauses: halt. The spec is in the conversation; user re-invokes Skill 2 in the same conversation or a new one. Reactivation re-reads the spec and rebuilds the work queue from current `[structural]` / `[detailed-revisit]` markers.

### 8.2 Claude Code runtime

Write the updated spec to `agent-spec.md` in the workspace. Then:

> Batch [N] complete. Spec written to `agent-spec.md`. Intents now `[detailed]`: [list].
>
> Section 7.5 says [M] intents still pending: [list].
>
> Continue with batch [N+1] or pause?

If user pauses: halt. The spec file is the durable state. User re-invokes Skill 2 in this session or a future one — same skill reads the same file, rebuilds the work queue.

### 8.3 The spec is the state

There is no session token, no "continue command", no internal flag. The work queue is computed at the start of every invocation by scanning section 5. If a previous invocation marked some intents `[detailed]` and the user paused, the next invocation sees those intents as `[detailed]` and skips them.

This means: the user can edit the spec between invocations (e.g., manually flip an intent back to `[structural]` to redo it, or add a new intent via Skill 1 patch mode). Skill 2 picks up from whatever the spec currently says.

### 8.4 Single-batch case

If the work queue is exactly one intent (one batch with one intent), the checkpoint gate still fires. The user always sees an explicit confirmation point, even when there's nothing left to do.

> Batch 1 complete (single intent). Intent `<name>` is now `[detailed]`. All intents in this invocation are detailed. Invoke Skill 3 (JSON Assembler) to emit the wire-format JSON.

---

## 9. Output contract

### 9.1 Per batch

- Updated spec: this batch's intents now `[detailed]`, content fully filled
- Section 4.5.3 regenerated
- Section 6.1 appended with this batch's Mustache references
- Section 7.3 generation log entry for the batch
- Section 7.4 updated if unknowns changed
- Section 7.5 updated to reflect remaining work
- Checkpoint gate prompt (§8)

Section 7.3 entry format:

```
[ISO timestamp]  Skill 2  detailing  Batch <N>: detailed <count> intents (<list>). <H> hard intents (<list>) handled as singletons. <D> redetailed (<detailed-revisit list>). Self-validation passed for all.
```

### 9.2 Invocation completion

At the end of an invocation report how many intents were detailed and how many remain, and
route the user to the next step — re-invoke Skill 2 while any remain, Skill 3 once none do.
When the queue is fully exhausted, log `Skill 2 detailing complete. All intents [detailed].
Spec ready for Skill 3.` to section 7.3 and set 7.5 to zero pending.

Read `stages/authoring-steps.md` §9.2 for the exact closing-message wording per runtime.

## 10. Anti-list — what Skill 2 does NOT do

- Modify spec sections 1, 2, 3, 4, 4.5.1, 4.5.2, 4.5.4, 4.5.5 — Skill 1's domain. If a structural change is needed, raise to user, recommend Skill 1 patch mode, halt the current intent's authoring. *(Sole v1.14.0 exception: the section-4 `**Max turns sentence:**` field — language content per §7.1.)*
- Author an `announcement` on an RT=1 terminal (v1.14.0, FP-8) — the farewell lives in the predecessor's `intentInstructions`; the terminal carries only its short loading announcement (check 18).
- Write speech content into `validationPrompt` — no scripts, questions, greetings, turn-taking guards, or routing (v1.13.0, FP-5). It is a capture mapping only.
- Paste turn-taking / human-rep / disapproval rules into per-intent fields — call-wide rules live once, in persona (FP-6; Skill 1's domain).
- Invent `{{…}}` placeholder names — only keys declared in 4.5.1–4.5.5 (FP-11).
- Mandate the same sentence as speech in two fields (FP-6 — check 14).
- Change an intent's Response Type. Structural — Skill 1 patch mode.
- Add or remove intents. Skill 1.
- Modify transitions. Skill 1.
- Run the §15.4 cross-reference pass. Skill 3.
- Emit wire-format JSON. Skill 3.
- Walk past a batch checkpoint without explicit user confirmation.
- Mark an intent `[detailed]` without passing the §6 self-validation checklist.
- Invent values for unknowns. Mark `<UNKNOWN: ...>` instead and aggregate to section 7.4.
- Auto-fix structural issues caught during authoring (wrong slot type, missing transitions, etc.). Raise to user, recommend Skill 1 patch.
- Discard staged notes from Skill 1 silently. Surface them to the user; if discarded, log to 7.3.
- Constrain `validationPrompt` length or character set. Doc 1 v1 doesn't constrain; trust the platform to reject if it has limits.
- Refuse user overrides to the batching plan. Push back once for hard-intent-in-non-singleton-batch, then accept.

---

## Appendix A — Doc 1 §14.3 anti-patterns Skill 2 enforces

| § | Name | Skill 2 enforcement |
|---|---|---|
| 14.3.2 | Free prose instead of Conversation Routines (intentInstructions; validationPrompt is capture-mapping styled since v1.13.0) | Steps 2 + 4 authoring + checks 1 and 5 |
| 14.3.3 | Slot definition missing validation guidance | Step 1 + check 4 + the per-slot constraint lines in the capture mapping (v1.13.0) |
| 14.3.5 | Mustache referencing slots before collection | Section 5 (Mustache resolvability) + check 9 |
| 14.3.6 | RT=2 missing api_silence_behaviour | Step 3 RT=2 branch + checks 10 and 11 |
| 14.3.11 | Bot-level disambiguation in per-intent fields | Step 4 + check 8 |
| 14.3.12 | Slot validation in intentInstructions | Step 4 + check 6 |
| 14.3.13 | Persistent policy in single intent | Step 4 + check 7 |
| FP-5 | Spoken script inside validationPrompt (v1.13.0) | Step 2 doctrine + check 3; CHK-16 |
| FP-6 | Duplicate speak-obligation (v1.13.0) | Step 3 say-once iron rule + check 14; CHK-19 |
| FP-7 | Missing RT=3 intentLoadingAnnouncement (v1.13.0) | Step 3 RT=3 table + check 12; CHK-17 |
| FP-8 | Foreign-parameter reference (v1.13.0) | Step 4 own-parameters rule + check 13; CHK-18 |
| FP-8 | Farewell inside an RT=1 terminal / missing pre-terminal farewell (v1.14.0) | Step 3 RT=1 hard rule + step 4 predecessor authoring + check 18; CHK-20 |

Skill 1 owns: §14.3.1 (persona content), §14.3.4 (escalation transitions), §14.3.7 (capabilities ⊆ intents), §14.3.8 (naming), §14.3.9 (channel content placement), §14.3.10 (per-intent logic in persona).

Skill 3 owns: §14.3.5 authoritative cross-reference (§15.4 #7), plus all 7 cross-reference checks.

---
