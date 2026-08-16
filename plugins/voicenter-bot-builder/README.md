# Voicenter Bot Builder

Design, detail and assemble deployable **Voicenter voice/chat bot JSON** through a
three-skill authoring pipeline — from an interview about your business flow to a JSON file you
can import into the Voicenter platform.

Built and maintained by [Voicenter](https://www.voicenter.com). Not affiliated with or
endorsed by Anthropic.

---

## What it does

Authoring a Voicenter bot by hand means writing a large JSON document with six
cross-referenced collections, negative-integer placeholder IDs, and a set of field-placement
rules where putting the right sentence in the wrong field silently breaks the call. This
plugin splits that work into three stages, each with its own guardrails:

| Stage | Skill | Produces |
|---|---|---|
| 1 | **Agent Spec Designer** | The structural skeleton — identity, persona, flow graph, intents, slots — via interview. Writes an Agent Spec markdown file. |
| 2 | **Intent Detail Author** | The language content per intent: what the bot says, how it captures answers, what it does next. Walks intents in batches with checkpoints. |
| 3 | **JSON Assembler** | A mechanical projection of the finished spec into wire-format JSON, gated behind a 26-check verification pass. |

The **Agent Spec markdown is the source of truth** at every stage. No skill invents a value:
anything the interview didn't establish is emitted as a fail-loud sentinel and listed in the
generation banner for you to fill in before import.

Stage 3 refuses to emit JSON if any blocking check fails, and tells you which stage to go back
to. That is the point — a bot that imports cleanly but can't hold a conversation is worse than
one that doesn't import.

## Install

```
/plugin marketplace add VoicenterTeam/claude-marketplace
/plugin install voicenter-bot-builder@voicenter
```

## Slash commands *(Claude Code / Cowork)*

Three commands give deterministic entry points into the pipeline:

| Command | Runs |
|---|---|
| `/voicenter-bot-builder:bot-spec` | Skill 1 — the skill's own mode detection picks greenfield or patch |
| `/voicenter-bot-builder:bot-detail` | Skill 2 — rebuilds its queue from the spec's section-5 markers |
| `/voicenter-bot-builder:bot-assemble` | Skill 3 — parse, assemble, verify, emit |

Plugin commands are **namespaced** — the bare form (`/bot-spec`) does not resolve on its own.
Typing `/bot` and picking from autocomplete inserts the full name for you; typing the short
form literally does nothing.

The commands carry no logic of their own; they hand straight over. Plain-language requests
("design a bot", "assemble the JSON") still work everywhere, including claude.ai, where slash
commands don't exist.

## Example prompts

**Design a new bot from scratch**

> Design a Voicenter voice bot for a dental clinic. Callers should be able to book a new
> appointment, reschedule an existing one, or reach a human. Hebrew, voice only.

Runs the Skill 1 interview — identity and channel, persona, opening line, the flow graph, then
per-intent slots. Produces `agent-spec.md`.

**Fill in the per-intent language**

> Detail the intents in agent-spec.md.

Runs Skill 2 over every intent marked `[structural]`, in batches, pausing at each checkpoint.
Resumable: re-invoke it any time and it rebuilds the queue from the spec's section-5 status
markers.

**Assemble the deployable JSON**

> Assemble the JSON for agent-spec.md.

Runs Skill 3 — parse, assemble, verify, emit. You get `bot-<name>-<date>.json` plus a banner
listing every default applied, every unknown you must replace, and any mandatory post-import
step.

**Change an existing bot**

> Here's my agent-spec.md — add an intent that checks insurance coverage before booking.

Skill 1 enters patch mode, computes which already-detailed intents the change invalidates,
shows you that cascade, and waits for confirmation before applying it.

**Verify a spec without assembling** *(Claude Code / Cowork)*

> @voicenter-bot-builder:spec-verifier verify agent-spec.md

Runs the 26-check pass in an isolated read-only context and returns a pass/fail report with
routing recommendations. Never modifies anything.

## Data handling

**This plugin makes no network calls of its own and transmits nothing.**

- No telemetry, no analytics, no logging to any Voicenter or third-party endpoint.
- Everything you say in the interview stays in your local Claude session.
- The only artifacts written are files in your own workspace: the Agent Spec markdown and the
  generated bot JSON (plus a banner sidecar in Claude Code).
- No credentials are requested, stored, or needed. The plugin never contacts the Voicenter
  platform to build a bot; you import the generated JSON yourself.

Two things to be aware of, because they involve *your* choices rather than the plugin's:

- If you have the separate **`voicenter-mcp`** plugin installed, Skill 1 will offer to fetch
  your live account and layer lists so you can pick from real values instead of typing IDs.
  That is an explicit, promptable step and it uses that plugin's own authenticated connection —
  decline it and the interview captures the values as text instead.
- If your bot design includes an **external API intent (RT=2)**, Skill 2 verifies that endpoint
  is real by calling it once with sample values you supply. The URL is yours; nothing is sent
  to Voicenter. Secrets are never written to the spec — only the status code, the confirmed
  field paths, and a redacted echo of the request.

## Known limitations

- **RTL rendering in terminal surfaces.** Hebrew and Arabic do not render reliably in the
  Claude Code CLI, VS Code, or Desktop terminals; claude.ai web is better. Machine-critical
  output (JSON keys, identifiers, filenames, check IDs) is deliberately ASCII/LTR, so what is
  *generated* is correct even where the *display* is confusing. Read generated JSON from the
  file rather than the terminal if the direction looks scrambled.
- **Subagent verification is a Claude Code / Cowork enhancement.** There, the 26-check pass can
  run in a fresh isolated context, which catches more than a verifier that watched the spec get
  written. In claude.ai consumer chat, subagents are inert, so the *identical* checks run
  inline from the same procedure file. No feature is lost — only the context isolation.
- **A bot with an RT=2 intent cannot be completed without a reachable endpoint.** Skill 2's
  live verification is a hard block with no waiver, by design: an unverified API contract is
  the most expensive thing to discover after deployment.
- **`silence_behaviour.intent` needs one manual step after import.** The Voicenter import
  procedure does not remap that particular placeholder, so the generated banner tells you which
  intent to select in the UI. This is a platform limitation, not a plugin bug.
- **Negative instructions are not emitted to the JSON.** The wire field is unverified, so the
  banner surfaces the text for you to paste into the UI's AI Security Settings instead.
- **The Assembler pins `model: haiku`; the other two skills don't.** Assembly is a
  deterministic projection — a parser, not an interpreter — so it runs on a cheaper model. The
  interview and language-authoring skills inherit your session's model, because those genuinely
  need reasoning. `model` is a Claude Code extension: **claude.ai ignores it**, so the same
  assembly costs more there. No behavioural difference either way, only cost.
- **Slash commands are Claude Code / Cowork only.** In claude.ai the skills trigger from plain
  language instead. Nothing is lost — the commands are convenience, not capability.

## Troubleshooting

**"Skill 3 refuses to assemble — gate A says the spec is incomplete."**
Some intents are still `[structural]` or `[detailed-revisit]`. Run Skill 2 again; it picks up
exactly those.

**"Gate C says an RT=2 intent is unverified."**
That intent has no section-7.6 verification record. Re-run Skill 2 on it with real sample
values for the request body. If the endpoint isn't reachable yet, the bot cannot be completed —
that is deliberate.

**"The cross-reference pass failed and I don't know which stage to fix."**
Every failure names its route. Structural problems (dangling references, roles, graph shape)
go to Skill 1 patch mode; language problems (a wrong `{{variable}}`, a script in the wrong
field, a missing filler) go to Skill 2. Ambiguous cases list both.

**"The bot says the same sentence twice on a real call."**
A duplicated speak-obligation — the same line mandated in two fields. Check 19 catches this at
assembly; if it reached production, re-assemble and it will be flagged.

**"The bot goes quiet and then asks if I'm still there."**
Usually a non-empty `announcement` on an intent that asks nothing: the bot says it, waits for
an answer that never comes, and the silence loop fires. Check 24 catches this.

**"The generated filename looks wrong for a Hebrew bot name."**
Known gap, tracked separately. The spec's `**Identifier:**` field controls the filename — set
it to the ASCII slug you want.

**"My plugin seems to be running an older version of a skill."**
Plugin caches are sticky. `/reload-plugins`, and check `/plugin` reports the version you
expect.

## Support

- Developer support: [api@voicenter.com](mailto:api@voicenter.com)
- Voicenter API portal: <https://www.voicenter.com/API>
- Issues: <https://github.com/VoicenterTeam/claude-marketplace/issues>

## Reviewer test kit

`examples/` contains a complete, self-contained fixture — no login or account needed:

| File | Purpose |
|---|---|
| `sample-spec-detailed.md` | A finished Agent Spec for a fictional clinic: 10 intents covering every response type |
| `expected-output.json` | That spec's assembly output, frozen at the v1.17.0 wire baseline |
| `expected-output-shipping.json` | That spec's assembly output under current emission rules |
| `expected-banner.txt` | Its generation banner |
| `sample-spec-seeded.md` | The same spec with three deliberate defects |
| `expected-violations-report.md` | Which checks those defects trip, and why |
| `stub-api-server.py` | A local stand-in for the fictional clinic's API, so the RT=2 verification step can run |

`examples/README.md` has the exact commands to reproduce all of it.

## License

MIT — see [LICENSE](LICENSE).

> **Pre-release note:** distribution rights on the bundled reference material (which describes
> Voicenter's bot wire format in field-level detail) are still pending sign-off. See
> `docs/planning/license-decision.md`.
