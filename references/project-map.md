# Voicenter Bot JSON Skill Project — Conversation Map

**Project goal:** Build the v1 Bot JSON generation skills for the Voicenter platform. A user-driven skill suite (no MCP, no autonomy) that produces deployable Bot JSON from interview-driven design.

**Slicing strategy:** Option α — one conversation per artifact. Six conversations total.

**Runtime model:** Two runtimes share the same skills:
- **Claude UI (single-conversation):** small/medium bots, ≤8 intents
- **Claude Code (workspace-based):** larger bots, up to ~20 intents

**Last updated:** End of Conv 4 (May 2026)

---

## Conversation map

### Conv 1 — Doc 1: Schema Audit ✅ DONE
**Goal:** Author the wire-format reference for Voicenter Bot JSON.
**Output:** `voicenter-bot-json-schema-audit-v1.md` (15K words, 18 sections)
**Status:** Locked, immutable.
**Memory slot:** previously 28; now overwritten by Conv 2 state. Doc 1 details preserved in slot 30 (Bot JSON Yuval structural details).

### Conv 2 — Doc 2: Skill Architecture ✅ DONE
**Goal:** Design the three-skill architecture, the Agent Spec format, and validation strategy.
**Inputs:** Doc 1
**Outputs:**
- `voicenter-bot-skills-architecture-v1.md` (Doc 2)
- `project-map.md` (this document)
- `locked-decisions.md` (decision registry, 12 decisions A-L)
- `handoff-doc-template.md` (the standardized template)
- `handoff-conv-2-to-3.md` (this conversation's handoff)
**Memory slot:** 28
**Status:** Locked at end of Conv 2.

### Conv 3 — Skill 1 SKILL.md: Agent Spec Designer ✅ DONE
**Goal:** Author the Skill 1 SKILL.md and supporting templates.
**Inputs:** Doc 1, Doc 2, project-map, locked-decisions, handoff-conv-2-to-3
**Scope coverage:**
- Greenfield + patch modes
- Four-phase interview (identity/channels, persona, flow graph, per-intent structural)
- Deep Research nudge with four triggers and parameterized query
- Channel scope behavior with templated defaults
- Model config catalog (hardcoded list + raw ID override)
- Available variables interview (sections 4.5.1, 4.5.2, 4.5.4)
- Dual-runtime mechanics (single-conversation vs Claude Code state handling)
- Structural validation rules (§14.3.1, .4, .7, .8, .9, .10, .13)
- Cascade impact algorithm for patch mode
**Outputs:**
- `skills/voicenter-bot-spec-designer/SKILL.md`
- Supporting files: agent-spec template skeletons, model catalog data, trigger detection rules
- `handoff-conv-3-to-4.md`
**Notes:**
- Largest of the three SKILL.md files (densest skill — patch mode + Deep Research + multi-mode + interview + validation)
- If context strains during drafting, split mid-stream to Conv 3a/Conv 3b is permitted
- Doc 2 §4 is the primary input; everything in §4 must be implementable from the SKILL.md

### Conv 4 — Skill 2 SKILL.md: Intent Detail Author ✅ DONE
**Goal:** Author the Skill 2 SKILL.md.
**Inputs:** Doc 1, Doc 2, project-map, locked-decisions, handoff-conv-3-to-4 (carries Skill 1 deliverables)
**Scope coverage:**
- State-based reactivation
- Hybrid batching with adaptive sizing
- Singleton hard intents
- Per-intent four-step interview (slot detailing, validationPrompt, RT-specific, intentInstructions)
- Content-shape validation rules (§14.3.2, .3, .5, .6, .11, .12, .13)
- Mustache reference resolution (blocking)
- Dual-runtime checkpoint mechanic
**Outputs:**
- `skills/voicenter-bot-intent-detail-author/SKILL.md`
- `handoff-conv-4-to-5.md`
**Notes:**
- Doc 2 §5 drives this directly
- Smaller than Skill 1; one conversation should fit comfortably

### Conv 5 — Skill 3 SKILL.md: JSON Assembler & Publish (NEXT)
**Goal:** Author the Skill 3 SKILL.md.
**Inputs:** Doc 1, Doc 2, project-map, locked-decisions, handoff-conv-4-to-5
**Scope coverage:**
- Strict-template parser (no interpretation)
- Mechanical mapping per Doc 1 §4-13
- §15.4 cross-reference pass (7 checks, all blocking)
- ID placeholder strategy (Doc 1 §15.3 Option A)
- Quirk preservation per Doc 1 §16
- Fail-loud sentinel emission for unknowns
- Banner/sidecar metadata documenting sentinels
- Anti-list of what Skill 3 does NOT do
**Outputs:**
- `skills/voicenter-bot-json-assembler/SKILL.md`
- `handoff-conv-5-to-6.md`
**Notes:**
- Smallest of the three SKILL.md files (mechanical, no interview)
- The hard part is being explicit about what Skill 3 doesn't do
- Doc 2 §6 drives this directly

### Conv 6 — End-to-end Testing
**Goal:** Validate the full pipeline against known-good production samples.
**Inputs:** All three SKILL.md files, Doc 1 with sample references (Yuval, Refua), all project artifacts
**Test targets (per Conv 2 evidence-based selection):**
- **Primary test:** Yuval (יובל). Reverse-engineer the spec, run Skill 1 → Skill 2 → Skill 3, compare emitted JSON to Doc 1 §14.1.1 ground truth. Yuval was selected because it has fully documented all 5 prompts fields, full caller-silence config, conditional branching, and richer documentation in Doc 1.
- **Secondary test:** Refua (חברים לרפואה), focused on multi-field dotted-path Mustache validation in `get_nearest_collection_points`. Run only if primary test passes.
**Process:**
1. Reverse-engineer an Agent Spec for Yuval from Doc 1 §14.1.1
2. Run the spec through Skill 1 patch mode (or skip — Skill 1 isn't authoring; this validates Skill 3 directly)
3. Run Skill 3 to emit JSON
4. Compare emitted JSON to the actual production export structure documented in Doc 1
5. Surface gaps
**Outputs:**
- `test-bot-spec-yuval.md` (the reverse-engineered Agent Spec)
- `test-emitted-json-yuval.json` (skill output)
- `validation-report.md` (gaps, anomalies, fixes needed)
- `handoff-back-to-skills.md` (if fixes needed) — feedback loop into Conv 3/4/5
**Outcome:**
- v1 skills validated, ready for production use, OR
- Fixes identified and routed back to relevant skill conversation (Conv 3a, 4a, or 5a)
**Notes:**
- Conv 6 may iterate. If gaps require skill changes, fix conversations spawn before validation completes.

---

## File ownership matrix

| File | Owned by | Mutable | Versioned |
|---|---|---|---|
| `voicenter-bot-json-schema-audit-v1.md` (Doc 1) | Conv 1 | No (locked) | v1 |
| `voicenter-bot-skills-architecture-v1.md` (Doc 2) | Conv 2 | No (locked at end of Conv 2) | v1 |
| `project-map.md` | Conv 2 author, all convs read | Yes — updated when project shape changes | rolling |
| `locked-decisions.md` | Conv 2 author, all convs append | Append-only | rolling |
| `handoff-doc-template.md` | Conv 2 | No (locked template) | v1 |
| `skills/voicenter-bot-spec-designer/SKILL.md` | Conv 3 | Updated only via Conv 3 reopens | rolling |
| `skills/voicenter-bot-intent-detail-author/SKILL.md` | Conv 4 | Updated only via Conv 4 reopens | rolling |
| `skills/voicenter-bot-json-assembler/SKILL.md` | Conv 5 | Updated only via Conv 5 reopens | rolling |
| Test artifacts | Conv 6 | n/a | n/a |

---

## Persistent docs that travel between every conversation

These files are attached to **every** conversation from Conv 3 onward:

1. `voicenter-bot-json-schema-audit-v1.md` — Doc 1, wire-format contract
2. `voicenter-bot-skills-architecture-v1.md` — Doc 2, skill architecture
3. `project-map.md` — this document
4. `locked-decisions.md` — decision registry

Plus the conversation-specific handoff doc (`handoff-conv-N-to-N+1.md`).

---

## Conversation-end protocol (locked in Conv 2)

At the end of every conversation:

1. **Bundle all relevant files into one zip** — every persistent doc plus the new handoff doc, ready to download
2. **Provide a clear conversation-start prompt for the next conversation** — copy-paste-ready first message
3. **Reference the relevant memory slot(s)** — explicit pointer to where context lives in Claude's memory

The user copies the prompt to a new conversation, attaches the zip, and the next Claude has everything needed.

---

## Open meta-questions

None at this time. The project shape is locked. Reopen this section if a structural change is needed.
