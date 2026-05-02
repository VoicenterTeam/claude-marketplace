# Voicenter Bot JSON Skill Project — Locked Decisions Registry

**Purpose:** append-only record of every architectural decision locked across the project. Decisions never get unlocked silently. If a future conversation needs to revise a decision, it's added as a new entry that supersedes the prior one.

**Conventions:**
- Each decision has a letter ID (A, B, C, ...) for quick reference
- Decisions are listed in the order they were locked
- Each entry has: ID, locked-in-conversation, short statement, full statement, rationale
- Decisions reference Doc 1 sections where applicable

---

## Top-level architecture (locked Conv 2)

### Three-skill spec-driven pipeline

**Three skills, sequenced:**
- **Skill 1 — Agent Spec Designer:** interview-driven structural design. Greenfield + patch modes.
- **Skill 2 — Intent Detail Author:** language-heavy per-intent fields. State-based, reactivable.
- **Skill 3 — JSON Assembler & Publish:** mechanical projection of spec into wire-format JSON. Zero creative decisions.

**Source of truth:**
- Single Agent Spec (markdown), 7 sections + 4.5
- Skills 1 and 2 progressively fill the spec
- Skill 3 emits JSON as mechanical projection
- No invented values; unknowns marked explicitly; fail-loud sentinels in JSON

**Runtime model:**
- Claude UI single-conversation: bots up to ~8 intents
- Claude Code workspace-based: bots up to ~20 intents
- Same skills, same spec format, different state mechanics

---

## Decision A — Skill 2 batching (locked Conv 2)

**Statement:** Hybrid batching with adaptive sizing. 3-4 checkpoints by default, scaling for very large bots. Hard intents become singleton batches.

**Full mechanism:**
- Default: 3-4 checkpoints across the full intent set
- Adaptive sizing: ~5-6 intents per batch at the upper bound (20 intents)
- Hard intents (RT=2 with >3 slots, conditional branching, >4 transitions, complex validation) get their own checkpoint
- For small bots (≤5 intents), 2 checkpoints with hard intent isolated
- For very large bots (>20), batches stay at 5-6, checkpoint count grows beyond 4
- Skill 1 marks hard intents during structural design
- Skill 2 proposes batching plan derived from flags
- User confirms or overrides at start of Skill 2 invocation

**Rationale:** Pure serial walk risks context bloat. Pure per-intent loses momentum. Hybrid balances explicit checkpoints with batch progress. Hard-intent isolation prevents complex intents from contaminating focus.

---

## Decision B — Spec format and unknown handling (locked Conv 2)

**Statement:** Markdown spec is single source of truth. No invented values. Unknowns marked explicitly; Skill 3 emits fail-loud sentinels.

**Full mechanism:**
- Agent Spec is markdown, strict structural template, 7 top-level sections + 4.5
- Skills produce/modify spec; Skill 3 reads spec via deterministic parser
- Spec wins over any other artifact in case of conflict
- No skill invents values
- Unknowns marked: `<UNKNOWN: description>` for required fields, `<INCOMPLETE: ...>` for partial sections, `[not configured]` for optional whole-section omissions
- Skill 3 propagates unknowns to wire format as fail-loud sentinels:
  - String fields: `"<USER_TO_FILL: field_name>"`
  - Integer ID fields: `-999`
  - Object fields: `{}` with metadata warning
- Skill 3 prepends a banner comment to the JSON listing all sentinels emitted

**Rationale:** Quiet defaults (e.g., empty string, 0) would import successfully and break at runtime. Fail-loud sentinels surface unknowns at import time; user must replace before deploying.

---

## Decision C — Validation placement (locked Conv 2)

**Statement:** Iron rules and cross-reference checks distributed across the three skills based on which has the data.

**Full mechanism:**
- **Skill 1 owns structural rules and persona-coherence rules (blocking):** §14.3.1 (persona content), §14.3.4 (escalation), §14.3.7 (capabilities ⊆ intents), §14.3.8 (naming), §14.3.9 (channel content), §14.3.10 (per-intent logic in persona), §14.3.13 (persistent policy)
- **Skill 2 owns content-shape rules and per-intent misplacement rules (blocking):** §14.3.2 (Conversation Routines), §14.3.3 (slot validation), §14.3.5 (Mustache, blocking at this level), §14.3.6 (RT=2 completeness), §14.3.11/12/13 (per-intent misplacement)
- **Skill 3 owns the §15.4 cross-reference pass (all 7 checks, blocking)**

**Severity model:**
- Blocking: skill does not advance until resolved
- Advisory: skill records, continues. Used for Skill 1's Mustache pre-check (false positives possible). Skill 3's Mustache check is the authoritative blocking version.

**Failure routing from Skill 3:**
- Structural violations → Skill 1 patch mode
- Content violations → Skill 2 reactivation
- See Doc 2 §7.5 routing table

**Rationale:** Validate at the earliest skill that has the information. Earlier validation catches errors closer to source; late validation forces backward routing.

---

## Decision D — Channel scope behavior (locked Conv 2)

**Statement:** Skill 1 asks channel scope at start. Active channels get full interview; inactive channels get templated defaults marked as not user-authored.

**Full mechanism:**
- Skill 1 phase 1 question: voice-only, chat-only, or both
- Active channel: full interview for that channel's `prompts.{voice,chat}Instructions`
- Inactive channel: templated default emitted automatically; marked `[default — not user-authored]` in spec
- Templates live in Skill 1's SKILL.md package, identity-injected from persona
- Future channel activation (e.g., adding chat to a voice bot) handled via Skill 1 patch mode

**Templated defaults are a carve-out from the "no invented values" rule:**
- Defaults are explicit, predictable, marked
- User can override at any time
- Mark in spec distinguishes from authored content

**Rationale:** Voice-only is the dominant case in production. Asking about chat for every voice bot wastes time. Inactive-channel defaults keep the bot deployable on the inactive channel later without re-interviewing.

---

## Decision E — Soft cap with thresholds (locked Conv 2)

**Statement:** No hard refusal of bot size; advisory warnings at thresholds. Different thresholds per runtime.

**Full mechanism:**
- **Single-conversation runtime (Claude UI):**
  - Silent: <6 intents
  - Advisory: 7-8 intents
  - "Consider Claude Code" warning: >8 intents
- **Claude Code runtime:**
  - Silent: <12 intents
  - Advisory: 12-20 intents
  - Stronger advisory ("consider splitting bot"): >20 intents
- A's "3-4 checkpoints" stays as soft target, batches scale up for very large bots
- No hard refusal at any size — user decides

**Rationale:** Schema doesn't constrain bot size. Refusal is artificial. Advisories let users walk into known territory eyes-open.

---

## Decision F — Model config selection (locked Conv 2)

**Statement:** v1 uses small hardcoded catalog of known AI model configs in Skill 1, with raw ID override path. v3 replaces with MCP query.

**Full mechanism:**
- v1: Skill 1 presents hardcoded list of known AIModelConfigs by name during interview
- User picks by name → Skill 1 maps to underlying `AIModelConfigID` + `AIModelTypeId`
- Override path: user supplies raw IDs directly for custom configs not in catalog
- If user skips, spec marks `<UNKNOWN>`; Skill 3 emits fail-loud sentinels
- Catalog is part of Skill 1's SKILL.md package, version-controlled with the skill
- v3: MCP read replaces hardcoded list with live query against platform's model registry

**Rationale:** Asking for raw integer IDs in interview is bad UX. Hardcoded list is small, stable, easy to maintain in v1. MCP integration in v3 obviates maintenance.

---

## Decision G — Patch mode in v1 (locked Conv 2)

**Statement:** v1 supports patch mode for current-pipeline artifacts. Deployed-bot updates wait for v3.

**Full mechanism:**
- Two named entry modes for Skill 1: greenfield (no spec) and patch (spec attached)
- Patch mode reads existing spec, asks for change, classifies as easy/hard, computes cascade impact, surfaces affected intents, applies after user confirms
- Easy changes: persona/channel/announcement edits, new intent addition, intent rename, non-structural metadata, channel scope expansion
- Hard changes: RT change, slot modification, intent deletion, transition modification, bot-level intentInstructions routing change, channel scope reduction
- Cascade impact algorithm: directly modified intent + transitively-affected intents marked `[detailed-revisit]`
- v1 patch mode operates only on spec-and-artifact in current pipeline; never on deployed bots
- v3 adds deployed-bot updates per Doc 1 §18.3

**Rationale:** Patch mode is real engineering work but valuable in v1. Deployed-bot updates require MCP and are deferred. Cleanly separated.

---

## Decision H — Deep Research nudge timing (locked Conv 2)

**Statement:** Nudge fires at end of phase 2 (after persona, before flow graph) if any trigger detected.

**Rationale:** End of phase 2 has enough context for query construction, but before language-heavy flow graph decisions are locked, so research findings can still meaningfully inform design.

---

## Decision I — Deep Research nudge triggers (locked Conv 2)

**Statement:** Four triggers in v1, structured for v2 extension. Single nudge workflow with parameterized query template.

**Full mechanism:**
- **Triggers detected during phases 1-2:**
  1. Regulated industry (medical, financial, legal, insurance, pharmaceutical)
  2. Expressed uncertainty (user asks what's standard, doesn't know patterns)
  3. Competitor question (user asks how others do it)
  4. Unrecognized niche domain (Skill 1 has no priors)
- If any cue fires: nudge activates at end of phase 2
- Single workflow, parameterized query (decision J)
- v2-friendly: append new triggers to the list with detection rule + injection content; no workflow rewrite

**Rationale:** Reading 1 of "multi-layer trigger skill" — extensible trigger list without speculative workflow branching. Reading 2 (multiple workflows) is solving a problem we don't have evidence for yet.

---

## Decision J — Deep Research query construction (locked Conv 2)

**Statement:** Templated query with conditional sections based on which trigger fired. User reviews before launch. Pause-or-skip user choice.

**Full mechanism:**
- Query has four sections:
  - **Domain context** (always populated): industry and use case
  - **Regional/language context** (always populated): location and primary language
  - **Intent-derived focus** (always populated): rough intent set sketched so far
  - **Regulatory/competitive context** (conditional): populated only if regulated or competitor cues fired
- Skill 1 generates query, presents to user for review
- User chooses pause-and-research (copy query, open Deep Research separately, return with findings) or skip (proceed to phase 3 without research)
- If pause: spec state saved (in-conversation message or workspace file), user instructed how to return
- If skip: §7.3 generation log records nudge offered + skipped

**Rationale:** User retains final say on whether to pursue research. Templated structure is predictable and editable.

---

## Decision K — Doc 2 spec format (locked Conv 2)

**Statement:** Doc 2 §3 documents the Agent Spec template using prose-with-illustrative-snippets, not full grammar.

**Rationale:** Doc 2 is architecture-level. Full template grammars belong in the SKILL.md files (Conv 3-5), not duplicated in Doc 2.

---

## Decision L — Handoff and runtime model (locked Conv 2)

**Statement:** Dual-runtime support. Single-conversation runtime (Claude UI) and Claude Code runtime (workspace-based) share the same skills and same spec format. Different state mechanics.

**Full mechanism:**
- Single-conversation: spec lives as conversation message; user invokes next skill in same conversation
- Claude Code: spec lives as `agent-spec.md` workspace file; user invokes skills across one or more sessions
- Skills detect runtime at invocation and adjust state-handling
- Skill 2 checkpoint mechanic: explicit user confirmation after each batch in both runtimes ("continue or pause?")

**Rationale:** Single-conversation is best for medium bots; Claude Code is best for larger or engineer-driven workflows. Same skills shouldn't have to be rewritten for different runtimes.

---

## Decision M — Variable inventory in spec (locked Conv 2)

**Statement:** Section 4.5 of the Agent Spec enumerates all variables available to the bot at runtime. Drives both advisory and authoritative Mustache resolvability checks.

**Full mechanism:**
- Section 4.5.1: call-context variables (platform-supplied at call start)
- Section 4.5.2: environment variables (config-time secrets via `{{ENV.*}}`)
- Section 4.5.3: slot variables (auto-derived from section 5 intent definitions)
- Section 4.5.4: API response variables (per-intent, RT=2 only — dotted paths)
- 4.5.1 and 4.5.2 populated by Skill 1 interview in v1 (no MCP); v2+ MCP query
- 4.5.3 auto-derived by skills, regenerated as section 5 evolves
- 4.5.4 captured per RT=2 intent during Skill 1 phase 4

**Rationale:** Without enumerated variable inventory, Mustache resolvability check has no allowlist. Section 4.5 is the canonical source for both Skill 1's advisory check and Skill 3's authoritative check.

---

## Decision N — Test sample priority (locked Conv 2)

**Statement:** Yuval as primary test target in Conv 6. Refua as optional secondary, focused on multi-field dotted-path Mustache.

**Rationale:** Evidence-based comparison from Doc 1: Yuval has richer documentation (~250 lines vs ~75), exercises every `prompts` bundle field, has full caller-silence config, demonstrates conditional post-execution behavior, is referenced in §14.3 anti-patterns. Refua's main strength (multi-field dotted-path Mustache in `get_nearest_collection_points`) is a focused secondary stress test.

---

## Decision O — Three-category artifact model (locked Conv 2)

**Statement:** Project artifacts fall in three categories: persistent project documents, per-conversation handoff docs, per-conversation working artifacts.

**Full mechanism:**
- **Persistent docs** (survive across all conversations, evolve as project grows): Doc 1, Doc 2, project-map.md, locked-decisions.md, handoff-doc-template.md
- **Handoff docs** (produced at end of each conv, consumed at start of next): handoff-conv-N-to-N+1.md
- **Working artifacts** (local to one conversation): drafts, scratch
- Handoff docs reference persistent docs; don't duplicate state

**Rationale:** Avoid drift by keeping decision registry in one place. Handoff docs stay focused on transition, not exhaustive state.

---

## Decision P — Conversation-end protocol (locked Conv 2)

**Statement:** Every conversation ends with: zip bundle of files, copy-paste-ready start prompt for next conversation, explicit memory slot reference.

**Full mechanism:**
1. Bundle all relevant files into one zip (persistent docs + new handoff doc + Doc 1)
2. Provide a clear conversation-start prompt for the next conversation
3. Reference the relevant memory slot(s) explicitly

**Rationale:** Eliminates the friction of starting a new conversation. The next Claude knows what to read and where to look in <30 seconds.
