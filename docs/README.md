# Voicenter Claude Code Plugin Marketplace — Documentation

This is the holistic, professional reference for every plugin and skill shipped by the Voicenter Claude Code marketplace.

It is organized so you can:

- **Get productive fast** — install the plugins and run your first integration in minutes.
- **Understand the architecture** — see how the 14 Voicenter APIs fit together as a single telephony platform.
- **Drill into any skill** — every skill has its own dedicated subfolder with API reference, examples, error handling, and troubleshooting.

---

## Documentation map

### Top-level guides

| Document | Purpose |
|---|---|
| [Getting started](getting-started.md) | Install plugins, configure CPanel, send your first request |
| [Architecture & call flows](architecture.md) | How the 14 APIs compose into incoming, outgoing, dialer, and dashboard flows |
| [Authentication](authentication.md) | OAuth, `code` parameter, webhooks, socket.io, and JS SDK auth — all in one place |
| [Glossary](glossary.md) | Voicenter terminology (DID, CDR, ivrid, queue, layer, monitor server, …) |

### Plugins

| Plugin | Documentation |
|---|---|
| `voicenter-mcp` (live MCP server) | [plugins/voicenter-mcp.md](plugins/voicenter-mcp.md) |
| `voicenter-api` (14 integration skills) | [plugins/voicenter-api.md](plugins/voicenter-api.md) |
| `voicenter-bot-builder` (3-skill bot authoring pipeline) | [plugins/voicenter-bot-builder.md](plugins/voicenter-bot-builder.md) |

### Skills

Every skill ships its own subfolder with a complete reference.

| Skill | Plugin | Direction | Type | Doc |
|---|---|---|---|---|
| Setup (MCP) | voicenter-mcp | — | OAuth | [skills/setup/README.md](skills/setup/README.md) |
| VoiceBot | voicenter-api | In/Out | Webhook (push) | [skills/voicebot/README.md](skills/voicebot/README.md) |
| Click2Call | voicenter-api | Outgoing | REST | [skills/click2call/README.md](skills/click2call/README.md) |
| Pop-Up Screen | voicenter-api | Incoming | Webhook (push) | [skills/popup-screen/README.md](skills/popup-screen/README.md) |
| CDR Notification | voicenter-api | In/Out | Webhook (push) | [skills/cdr-notification/README.md](skills/cdr-notification/README.md) |
| External Layer | voicenter-api | Incoming | Webhook (push) | [skills/external-layer/README.md](skills/external-layer/README.md) |
| Call Log | voicenter-api | In/Out | REST (query) | [skills/call-log/README.md](skills/call-log/README.md) |
| Blacklist | voicenter-api | Outgoing | REST | [skills/blacklist/README.md](skills/blacklist/README.md) |
| Mute Recording | voicenter-api | In/Out | REST | [skills/mute-recording/README.md](skills/mute-recording/README.md) |
| Extension List | voicenter-api | In/Out | REST | [skills/extension-list/README.md](skills/extension-list/README.md) |
| Real-Time | voicenter-api | In/Out | Socket.io SDK | [skills/real-time/README.md](skills/real-time/README.md) |
| Productive Dialer | voicenter-api | Outgoing | REST | [skills/productive-dialer/README.md](skills/productive-dialer/README.md) |
| Login / Logout | voicenter-api | In/Out | REST | [skills/login-logout/README.md](skills/login-logout/README.md) |
| Lead Tracker | voicenter-api | Incoming | JS SDK (browser) | [skills/lead-tracker/README.md](skills/lead-tracker/README.md) |
| Active Calls | voicenter-api | In/Out | REST | [skills/active-calls/README.md](skills/active-calls/README.md) |
| CRM Onboarding | voicenter-api | Guided | Conversational (authoring) | [skills/crm-onboarding/README.md](skills/crm-onboarding/README.md) |
| GetCallHistory | voicenter-api | In/Out | REST | [skills/get-call-history/README.md](skills/get-call-history/README.md) |
| Agent Spec Designer (Skill 1) | voicenter-bot-builder | — | Authoring (interview) | [skills/voicenter-bot-spec-designer/README.md](skills/voicenter-bot-spec-designer/README.md) |
| Intent Detail Author (Skill 2) | voicenter-bot-builder | — | Authoring (per-intent language) | [skills/voicenter-bot-intent-detail-author/README.md](skills/voicenter-bot-intent-detail-author/README.md) |
| JSON Assembler (Skill 3) | voicenter-bot-builder | — | Authoring (wire-format projection) | [skills/voicenter-bot-json-assembler/README.md](skills/voicenter-bot-json-assembler/README.md) |

---

## How to use this documentation

### If you are new to Voicenter
Start with [getting-started.md](getting-started.md), then read [architecture.md](architecture.md). After that, pick the skill that matches your use case and read its dedicated page.

### If you are an AI coding agent (Claude / Copilot / Cursor)
The `SKILL.md` files inside [`plugins/`](../plugins) are your runtime instruction set — they are short and Claude-loadable.
The pages under `docs/skills/<skill>/` are deeper references for humans and for retrieval-augmented exploration when a SKILL.md is not enough.

### If you are integrating one specific API
Jump directly to that skill's page. Each skill page is self-contained: configuration, full request/response, error matrix, TypeScript example, and troubleshooting.

### If you are designing an end-to-end CRM integration
Read [architecture.md](architecture.md) — it shows the four canonical call flows and which skills compose into each.

---

## Versioning

The marketplace is at **v1.12.0**. `voicenter-mcp` and `voicenter-api` are at v1.1.2; `voicenter-bot-builder` is at v1.0.1. See the project [CHANGELOG.md](../CHANGELOG.md) for release history.

The skill documentation under this `docs/` tree is kept in lockstep with the source `SKILL.md` files in [`plugins/voicenter-api/skills/`](../plugins/voicenter-api/skills), [`plugins/voicenter-mcp/skills/`](../plugins/voicenter-mcp/skills), and [`plugins/voicenter-bot-builder/skills/`](../plugins/voicenter-bot-builder/skills). When a SKILL.md changes, update the corresponding `docs/skills/<skill>/README.md`.

---

## External resources

- [Voicenter API portal](https://www.voicenter.com/API)
- [Voicenter CPanel](https://cpanel.voicenter.com)
- [Real-Time SDK on GitHub](https://github.com/VoicenterTeam/VoicenterEventsSDK)
- [MCP server homepage](https://mcp01.voicenter.co/mcp)
- Developer support: [[email protected]](mailto:[email protected])
