# Runtime Constraints — Verified Platform Facts

Verified against official Anthropic documentation as of **2026-08-08**
(code.claude.com/docs, platform.claude.com/docs, support.claude.com,
agentskills.io spec, anthropics/* repos). Items marked ⚠ have changed within
recent minor versions — re-verify before relying on them at ship time.

These are **constraints, not suggestions**. Implementation choices that
conflict with this file are wrong; if this file seems wrong, stop and ask.

## C1 — No capability probe exists (basis of locked decision Q)

There is **no documented mechanism** for a skill to detect its runtime or to
probe whether the Task/Agent tool is available. The Agent Skills spec offers
only: `compatibility` frontmatter (a *static human-readable declaration*, not
a probe) and experimental `allowed-tools` (a permission narrowing list, not a
query). Official cross-environment guidance covers package/network
differences only.

**Consequence:** dispatch must be soft. Inline execution is the default,
authoritative path; delegation is phrased as an opportunistic escalation
("if you are able to delegate… otherwise execute inline"). No branch may
block on availability; no skill text may instruct probing.

## C2 — Subagents are headless

`AskUserQuestion` is on the list of tools **removed from every subagent**,
regardless of the `tools` field. Also removed: `EndConversation`,
`EnterPlanMode`/`ExitPlanMode` (unless `permissionMode: plan`),
`ScheduleWakeup`, `TaskOutput`, `WaitForMcpServers`, `Workflow`. A subagent
runs autonomously to completion and returns a single text result.

**Consequence:** the verifier must need zero user interaction. Any
clarification happens in the parent skill *before* delegation.

## C3 — Subagents see only their delegation prompt

A (non-fork) subagent starts with a fresh, isolated context window. It does
not see the parent conversation, previously invoked skills, or files the
parent read. Inputs: the delegation prompt + the CLAUDE.md hierarchy (+ a git
snapshot for most agents). Output back to parent: the final message only.

**Consequence:** the delegation prompt must carry the spec's absolute path,
the plugin root, and the output-contract pointer. Fixed template in MS2 §2.2.

## C4 — Plugin-agent frontmatter restrictions

Plugin-shipped agents support: `name`, `description`, `model`, `effort`,
`maxTurns`, `tools`, `disallowedTools`, `skills`, `memory`, `background`,
`isolation` (`"worktree"` only). **`hooks`, `mcpServers`, `permissionMode`
are silently ignored** in plugin agents (security). Agent `name` must not
contain `:` (reserved for `plugin:agent` scoping).

## C5 — Path resolution

`${CLAUDE_PLUGIN_ROOT}` resolves to the plugin's absolute install directory
and substitutes anywhere in skill and agent content. Marketplace installs are
copied to `~/.claude/plugins/cache`; relative paths that traverse **outside**
the plugin root break after install (external files are not copied).

**Consequence:** every shared-file pointer (skills → `references/`, agent →
`references/`) uses `${CLAUDE_PLUGIN_ROOT}/…`.

## C6 — Skill structure limits

- SKILL.md body: **≤ 500 lines** for optimal performance (official guidance;
  v1.19.0 target 400 for headroom).
- Bundled references: keep **one level deep** from SKILL.md — deep chains
  (SKILL.md → a.md → b.md) risk partial reads (`head -100`-style previews).
- **Table of contents required** in any reference file > 100 lines.
- Skill `name`: ≤ 64 chars, lowercase/numbers/hyphens, **no reserved words
  "anthropic"/"claude"**. `description`: spec max 1,024 chars (but see C9).

## C7 — TodoWrite

Exists in Claude Code as a built-in; available to skills and retained by
subagents. **Ephemeral and in-session** — not durable, and not assumed present
in claude.ai chat.

**Consequence:** mirror only. The spec's section-5 status markers remain the
sole source of truth; queue reconstruction always reads section 5.

## C8 — claude.ai runs the skills portion of a plugin only

Plugins install in claude.ai chat, Claude Desktop chat, and Cowork — but
**hooks and sub-agents run only in Cowork**; in plain consumer chat they are
inert (grayed out). Skills work on **all plans including Free** (since
2026-02-11), gated on "Code execution and file creation" being enabled. The
claude.ai skills runtime = code-execution container (bash, filesystem, file
creation, web search, connectors). No Task/Agent tool, no hooks, no slash
commands.

**Consequence:** everything load-bearing must function skills-only. Agents,
commands, hooks, and `model` pinning are progressive enhancements.

## C9 — Description budgets ⚠

- **claude.ai truncates skill descriptions at ~200 characters.**
- Agent Skills spec allows 1,024 chars.
- Claude Code truncates the combined skills listing at 1,536 chars and shrinks
  descriptions under context pressure (least-used dropped first); `/doctor`
  detects overflow.

**Consequence:** descriptions written trigger-first at ≤ 200 chars (MS3 §3.5).

## Supplementary facts (design-relevant, not constraints)

- **Subagent nesting** ⚠: allowed by default up to 3 layers
  (`CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH`); changed multiple times within
  2.1.x. The verifier is a leaf — nesting is irrelevant to this design, but
  do not write "subagents cannot nest" anywhere.
- **Tool naming** ⚠: the Task tool was renamed `Agent` (v2.1.63); `Task`
  remains an alias. Skill text should say "delegate to the … agent," not name
  the tool.
- **Concurrency** ⚠: default 20 concurrent subagents; background execution is
  the default (v2.1.198+).
- **Skill `model` frontmatter**: Claude Code switches the active model for
  that skill's execution; accepts aliases (`haiku`/`sonnet`/`opus`) —
  **Claude Code extension, ignored by claude.ai** (graceful).
- **Plugin agents** are both @-mentionable (`plugin:agent`) and
  auto-delegated on description match.
- **Fresh-context rationale** (design basis for MS2): Anthropic's multi-agent
  research system post reports isolated-context subagents materially
  outperforming single-context agents on research evals; only the final
  report returns to the parent, keeping the main context clean.
