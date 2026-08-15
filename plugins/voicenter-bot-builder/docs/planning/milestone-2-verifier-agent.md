# Milestone 2 — Verifier Agent + Soft Dual-Path Dispatch

**Objective:** in Claude Code / Cowork, the 25-check pass (24 at MS2 time) runs in a
fresh-context, read-only subagent. Everywhere else (claude.ai consumer chat),
it runs inline with an explicit anti-anchoring discipline. Neither path is
gated on detecting the other.

**Why:** a verifier inside the context that built the spec is anchored on
intent, not text. Anthropic's own multi-agent findings and our Agent Generator
Verifier design both rest on fresh-context isolation. The dispatch must be
soft because no documented capability probe exists (constraint C1, locked
decision Q).

**Files touched:**
- `agents/spec-verifier.md` (NEW)
- `skills/voicenter-bot-json-assembler/SKILL.md` (§6.0–6.2 written; §8 anti-list +2 rules)

## Steps

### 2.1 Create `agents/spec-verifier.md`

Frontmatter (exactly these fields — see constraint C4; `hooks`/`mcpServers`/
`permissionMode` are silently ignored in plugin agents, do not include them):

```yaml
---
name: spec-verifier
description: Read-only cross-reference verifier for Voicenter Agent Specs.
  Executes the 26-check verification procedure against a fully-detailed spec
  and returns a structured pass/fail report with routing recommendations.
  Use when the JSON Assembler reaches its cross-reference pass, or when the
  user asks to verify a spec / run the checks before assembly.
model: sonnet
tools: Read, Grep, Glob
disallowedTools: Write, Edit, Bash
---
```

Notes:
- `name` must not contain `:` (reserved for plugin scoping); invocable as
  `voicenter-bot-builder:spec-verifier`.
- `model: sonnet` — mechanical pattern-matching; main-model cost is waste.
  (Do not go to haiku for the *verifier* without an eval — the semantic
  checks CHK-04/07-class need reading comprehension. Assembly-stage haiku
  pinning is MS5 and applies to the skill, not this agent.)
- Description is written for **auto-delegation** — plugin agents are both
  @-mentionable and description-triggered.

Body — keep short, the procedure lives in the reference file:
1. Read `${CLAUDE_PLUGIN_ROOT}/references/verification-procedure.md` first,
   then both doctrine files, then the spec at the path given in the prompt.
2. Execute CHK-01…CHK-26 in order. Emit exactly the output contract.
   (MS2 shipped with 24; CHK-25 was appended by MS7 with the functional v1.18.0 merge.)
3. Iron rules: **report only, never fix**; if the spec path is missing or
   unreadable, return the contract's structured-error form — do not hunt for
   files; verify what is written, not what seems intended; you have no
   conversation history and need none — everything required is the spec, the
   procedure, and the doctrines.

### 2.2 Write Skill 3 §6.0 — execution mode

Replace the MS1 stub. Required semantics (wording may be tuned, semantics may
not):

> Inline execution is the default and authoritative path. If you are able to
> delegate to the `voicenter-bot-builder:spec-verifier` agent, do so — the
> fresh-context verifier is preferred where available. Otherwise — including
> whenever you are uncertain the agent is available — execute
> `${CLAUDE_PLUGIN_ROOT}/references/verification-procedure.md` yourself,
> inline, per §6.2. Never block on delegation availability. Never ask the
> user which path to use.

Delegation prompt template (fixed — mitigates C3, the subagent sees nothing
but this prompt):

```
Verify the Agent Spec at: <absolute spec path>
Plugin root: <resolved plugin root path>
Execute the verification procedure at
<plugin root>/references/verification-procedure.md and return the report in
its Output Contract format. Report only; do not modify any file.
```

### 2.3 Write §6.1 — delegated path

- Consume the returned report **verbatim** — apply blocking/advisory handling
  and Appendix B routing exactly as v1.17.0 did with its own inline results.
- Contract guard: if the returned report does not match the output contract
  (missing verdict table, unknown CHK IDs, free-prose instead of structure),
  **discard it and fall back to §6.2 inline**. This defends against a stale or
  foreign verifier version.

### 2.4 Write §6.2 — inline path (degraded mode)

Fresh-eyes discipline, verbatim intent:

> Before checking, re-read the spec in full from the artifact — not from
> memory of this conversation. Verify against what is written, not what was
> intended. Treat the spec as if authored by someone else.

Then: execute the procedure file's checks in order; emit the same output
contract. Label this subsection **degraded mode** in-file, with one sentence
explaining the asymmetry (no context isolation → possible anchoring residue),
so future maintainers aren't surprised by a runtime sensitivity gap.

### 2.5 Extend Skill 3 anti-list (§8)

Add two rules:
- Do not skip verification because delegation is unavailable — inline is not
  optional.
- Do not summarize, soften, or reinterpret the verifier's report — consume it
  verbatim.

## Done criteria

- [ ] Agent loads: `@voicenter-bot-builder:spec-verifier` appears in typeahead
      after marketplace install (V-C1)
- [ ] Clean fixture: delegation occurs in Claude Code; report matches contract;
      assembly proceeds; JSON byte-comparable to v1.17.0 (V-C2)
- [ ] Seeded fixture: all 3 seeded violations caught with correct severity and
      routing (V-C3)
- [ ] Force-inline (rename `agents/` temporarily): identical verdicts (V-C4)
- [ ] Agent frontmatter lint passes (V-S4)
- [ ] claude.ai: dispatch point produces no delegation attempt, no error, no
      user-visible hesitation (V-A1 partial)
