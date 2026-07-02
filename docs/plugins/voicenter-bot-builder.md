# Plugin: `voicenter-bot-builder`

Three-skill pipeline that turns a conversational interview into deployable Voicenter Bot JSON. This is an **authoring** plugin — you use it once per bot, not per call.

The output is a single `bot-<identifier>-<date>.json` file plus a generation banner, ready to import into the Voicenter platform UI. Use this plugin when you want Claude to **design and emit a new bot**, not when you want Claude to operate an existing one (that's the [`voicenter-mcp`](voicenter-mcp.md) plugin) or to write integration code against the platform APIs (that's [`voicenter-api`](voicenter-api.md)).

---

## Manifest

[`plugins/voicenter-bot-builder/.claude-plugin/plugin.json`](../../plugins/voicenter-bot-builder/.claude-plugin/plugin.json):

```json
{
  "name": "voicenter-bot-builder",
  "description": "Three-skill pipeline for designing and generating Voicenter Bot JSON: Agent Spec Designer (interview), Intent Detail Author (per-intent language), JSON Assembler (wire-format projection). Produces a deployable bot-<name>-<date>.json.",
  "version": "1.0.0",
  "keywords": ["voicenter", "voicebot", "voice-ai", "agent-spec", "bot-builder", "conversational-ai", "ivr", "intent-design", "json-emitter", "skill-suite"]
}
```

Skills auto-discover from [`plugins/voicenter-bot-builder/skills/`](../../plugins/voicenter-bot-builder/skills/). Three skill folders, each with a `SKILL.md`.

---

## The pipeline

```text
        ┌──────────────────────────┐
        │  Skill 1                 │
        │  voicenter-bot-          │      writes
        │  spec-designer           │ ──────────────▶ agent-spec.md
        │                          │   sections 1-4, 4.5,
        │  Interview-driven        │   5 stubs, 6 init, 7 init
        └────────────┬─────────────┘
                     │
                     ▼
        ┌──────────────────────────┐
        │  Skill 2                 │
        │  voicenter-bot-          │      updates
        │  intent-detail-author    │ ──────────────▶ agent-spec.md
        │                          │   section 5 detail per intent;
        │  Per-intent language     │   section 4.5.3 + section 6.1
        │  in batches              │   regenerated
        └────────────┬─────────────┘
                     │
                     ▼
        ┌──────────────────────────┐
        │  Skill 3                 │
        │  voicenter-bot-          │      emits
        │  json-assembler          │ ──────────────▶ bot-<id>-<date>.json
        │                          │ ──────────────▶ bot-<id>-<date>.banner.md
        │  Strict-template parse   │   plus 7.3 log entry
        │  + §15.4 cross-ref       │
        └──────────────────────────┘
```

The three skills hand off through one shared file: **`agent-spec.md`**. Each skill knows what it owns and what it doesn't. Status markers per intent (`[structural]` → `[detailed]` → `[detailed-revisit]`) drive when each skill is allowed to run.

---

## Skill index

| Skill | Phase | Doc |
|---|---|---|
| `voicenter-bot-spec-designer` | 1 — Structural design via interview | [docs](../skills/voicenter-bot-spec-designer/README.md) |
| `voicenter-bot-intent-detail-author` | 2 — Per-intent language content | [docs](../skills/voicenter-bot-intent-detail-author/README.md) |
| `voicenter-bot-json-assembler` | 3 — Mechanical wire-format projection | [docs](../skills/voicenter-bot-json-assembler/README.md) |

### Voice prompt doctrine

The plugin includes a shared doctrine reference at `plugins/voicenter-bot-builder/references/voice-prompt-doctrine.md`, distilled from the Gemini Live 3.1 voice agent engineering guideline. Each of the three skills enforces a subset of the 13 doctrine rules at the right authoring phase:

- **Skill 1** (rules 3, 4, 5, 6, 7, 11-mirror) — bot-level prompt content: language posture, intent description language, recency-slot guardrail, contradictory tone/length, generic-policy boilerplate.
- **Skill 2** (rules 8, 9, 10, 11) — per-intent text: TTS-safe formatting, date math in prompt, few-shot example cap, Hebrew-utterance isolation.
- **Skill 3** (rules 1, 2, 12, 13) — final assembly: token budget, session-resumption ceiling, model-config doctrine, doctrine banner sentinels.

Gating on `AiModelConfigID=139` (Gemini Live 3.1) — rules tied to model-specific behavior skip silently on other models. Universal voice principles (language posture, TTS safety) apply broadly.

---

## When to use this plugin

- You are launching a new Voicenter voice or chat bot from scratch.
- You want a deployable bot JSON without hand-crafting the wire format.
- You need an iterable design artifact (`agent-spec.md`) that survives between sessions and Claude can pick up later.
- You are refactoring an existing bot — patch mode in Skill 1 takes an existing `agent-spec.md` as input.

You should **not** use this plugin to:

- Operate a deployed bot (use [`voicenter-mcp`](voicenter-mcp.md) for live MCP access).
- Hand-edit Bot JSON to fix a single field (smaller surgical edits don't need the pipeline).
- Build CRM-side integrations against Voicenter APIs (use [`voicenter-api`](voicenter-api.md)).

---

## Installation

```text
/plugin marketplace add VoicenterTeam/claude-marketplace
/plugin install voicenter-bot-builder@voicenter
```

Verify:

```text
/plugin
```

`voicenter-bot-builder` should be **Enabled** with **3 skills** registered.

---

## End-to-end example

A typical session looks like:

```text
You: design a Voicenter bot for an installation-scheduling flow

Claude: [invokes voicenter-bot-spec-designer]
        — runs 4-phase interview (Identity, Persona, Flow Graph, Per-intent structural)
        — writes agent-spec.md with 6 intents marked [structural]

You: run Skill 2

Claude: [invokes voicenter-bot-intent-detail-author]
        — walks the 6 intents in two batches of 3, with confirmation between batches
        — writes section 5 detail; flips each intent to [detailed]

You: assemble the JSON

Claude: [invokes voicenter-bot-json-assembler]
        — parses the spec strictly
        — runs §15.4 cross-reference (14 checks (checks 1–7 and 11–13 blocking))
        — emits bot-<identifier>-2026-05-01.json + bot-<identifier>-2026-05-01.banner.md
```

The banner lists every sentinel (e.g., `<USER_TO_FILL: bot description>`, `AccountID: -999`) the user must replace before importing to the Voicenter platform.

---

## Source-of-truth contract

This plugin's `SKILL.md` files are short and Claude-loadable — they are the runtime spec the model follows. The pages under `docs/skills/voicenter-bot-*/` extend each section with deeper context, troubleshooting, and design rationale. When a `SKILL.md` changes, the matching `docs/skills/<skill>/README.md` must change in lockstep (same fields, same examples, same error codes). See [CLAUDE.md](../../CLAUDE.md).

---

## Related documentation

- [Companion plugin: voicenter-api](voicenter-api.md) — integration skills for the same telephony platform
- [Companion plugin: voicenter-mcp](voicenter-mcp.md) — live MCP access (operate a deployed bot)
- [Authentication](../authentication.md)
- [Glossary](../glossary.md)
