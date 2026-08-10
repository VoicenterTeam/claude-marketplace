# Skill 1 stage — Close-out: graph, cross-references and spec emission

*Load at greenfield close-out (after Phase 4) and after applying a patch. Carries role
classification, section 6 generation, section 7 initialisation, the soft-cap warnings, the
Mermaid flow diagram and the refinement loop.*

*Run the self-validation checklist as part of close-out — SKILL.md §5 dispatches to it.*

## Table of contents

- [Greenfield close-out](#36-greenfield-close-out)
- [Intent flow diagram (spec section 6.6)](#361-intent-flow-diagram-spec-section-66)

---

### 3.6 Greenfield close-out

1. **Role classification (Approach B, D2/D7).** Propose a `**Bot-intent role:**` for every section-4 intent:
   - `entry` for each intent named as a routing target in the OPENING BEHAVIOR block (spec section 2.4, drafted in Phase 2 §3.2.4).
   - `global` for each intent the user described as always-available / triggerable from anywhere (transfer-to-human, WhatsApp). `global` supersedes `entry`. **The dedicated off-topic intent (§3.2.5) is ALWAYS `global` (v1.14.0).**
   - `chained` for all others. **The dedicated silence-forwarding and API-timeout forwarding intents (v1.14.0) are `chained` free-floating** — reachable only via `silence_behaviour.intent` / `api_silence_behaviour.intent`, never via `botIntents[]` or transitions.
   Present the full proposed classification in one `AskUserQuestion` (per §2.4 tool conventions) for confirmation; on approval, write the explicit `**Bot-intent role:**` field into every section-4 intent. The inference lives here in Skill 1 — Skill 3 only reads the written field.
   Then revisit §3 `silence_ending_sentence` (D8): if a transfer-to-human `global` exists and the current ending is a hang-up, offer to switch it to a failover-to-representative line.
2. Run the **self-validation checklist** (Section 5 of this SKILL.md).
3. Generate **spec section 6** initial pass:
   - 6.1: Mustache variable usage (every `{{...}}` reference, where used, what it resolves via).
   - 6.2: Intent transition graph — list the authored `(origin → next)` pairs **only**, so section 6 matches what Skill 3 will emit (v1.12.0 — no global fan-out; a `global`, including a `triggerable global` catalog intent, is reachable from anywhere via its `botIntents[]` type-2 registration, so no edges to it are listed). The dedicated silence-forwarding and API-timeout forwarding intents (v1.14.0), like any `silence-forward only` catalog intent, produce NO transition rows — they are reachable only via `silence_behaviour.intent` / `api_silence_behaviour.intent`.
   - 6.3: RT=2 API silence pairings (per RT=2 intent: Skill 3 will pair its embedded `api_silence_behaviour` with an `apiSilenceRelations[]` registry entry; section 6.3 lists which RT=2 intents need pairing).
   - 6.4: Escalation paths — when a `global` transfer-to-human exists, it is every non-global intent's escalation path by virtue of being reachable from anywhere (no explicit edge; v1.12.0). This satisfies §5 Check 7 for every intent whenever a global exists.
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
