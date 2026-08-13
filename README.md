# Voicenter Claude Code Plugin Marketplace

Official Claude Code plugins for integrating the Voicenter telephony platform into your application or CRM.

## Plugins in this repository

This repo is a **marketplace** (a monorepo of plugins), not a single plugin. `voicenter` is the
name of the *marketplace* — it is the `@marketplace` suffix in an install command and the MCP
server key, and it is **not** a plugin. Each plugin below lives in its own subdirectory with its
own `plugin.json`, and installs under its own name:

| Plugin | Directory | Install |
|---|---|---|
| **voicenter-mcp** | [`plugins/voicenter-mcp`](plugins/voicenter-mcp) | `/plugin install voicenter-mcp@voicenter` |
| **voicenter-api** | [`plugins/voicenter-api`](plugins/voicenter-api) | `/plugin install voicenter-api@voicenter` |
| **voicenter-bot-builder** | [`plugins/voicenter-bot-builder`](plugins/voicenter-bot-builder) | `/plugin install voicenter-bot-builder@voicenter` |

> **Indexing this repo?** Read the three `plugins/*/.claude-plugin/plugin.json` manifests, not the
> root `.claude-plugin/marketplace.json` `name`. There is deliberately no plugin named `voicenter`.

## Quick Start

```bash
# 1. Add the Voicenter marketplace
/plugin marketplace add VoicenterTeam/claude-marketplace

# 2. Install the live MCP plugin (direct API access from Claude)
/plugin install voicenter-mcp@voicenter

# 3. Install the API skills plugin (integration guides for all 16 API skills)
/plugin install voicenter-api@voicenter

# 4. (Optional) Install the bot-builder plugin (design Voicenter Bots end-to-end)
/plugin install voicenter-bot-builder@voicenter

```

---

## Plugins

### `voicenter-mcp` — Live API Access

Connects Claude Code directly to `https://mcp01.voicenter.co/mcp`. Authentication is handled via **OAuth** — no tokens or environment variables to configure. Claude Code launches the OAuth browser flow automatically on first use.

**Skills:** `/setup` — OAuth connection guide.

---

### `voicenter-api` — 16 API Integration Skills

Each skill teaches Claude exactly how to help you build a specific Voicenter API integration — correct endpoints, real request/response examples, and TypeScript code.

| Skill | API Type | Description |
|---|---|---|
| `/voicebot` | In/Out (push) | Build the endpoint the Voice Agent calls mid-conversation to fetch CRM data |
| `/click2call` | Outgoing | Initiate 2-leg calls from your CRM |
| `/popup-screen` | Incoming (push) | Build the endpoint Voicenter calls to display caller data to agents |
| `/cdr-notification` | In/Out (push) | Receive call records + AI analysis after every call ends |
| `/external-layer` | Incoming (push) | Route inbound calls based on your CRM business logic |
| `/call-log` | In/Out | Pull CDR records with filters (up to 10,000 per request) |
| `/blacklist` | Outgoing | Add/remove numbers from the dialing blacklist |
| `/mute-recording` | In/Out | Pause/resume call recording in real time (PCI compliance) |
| `/extension-list` | In/Out | List all SIP extensions, users, and departments |
| `/real-time` | In/Out | Stream live call and agent events via socket.io SDK |
| `/productive-dialer` | Outgoing | Manage campaigns, upload leads, control dialing |
| `/login-logout` | In/Out | Set agent login/logout and status from your CRM |
| `/lead-tracker` | Incoming | Track which marketing campaign generated each call (JS SDK) |
| `/active-calls` | In/Out | Snapshot of all live calls and queue activity |
| `/get-call-history` | In/Out | Pull one call by `CallID` with AI analysis — summary, emotions, personality traits, insights |
| `/crm-onboarding` | Playbook | Scoping a new CRM integration: API vs extension, Push vs Pull, screen-pop ownership, station codes |

---

### `voicenter-bot-builder` — 3-skill Bot Authoring Pipeline

Design and emit deployable Voicenter Bot JSON through a guided interview. Build-time tooling — used once per bot, not per call. Hands off through one shared `agent-spec.md` file.

| Skill | Phase | Purpose |
|---|---|---|
| `/voicenter-bot-spec-designer` | 1 — Structural | Interview-driven design: identity, persona, intent graph, slots, RT specifics |
| `/voicenter-bot-intent-detail-author` | 2 — Per-intent language | Slot descriptions, validationPrompt, RT-specific announcements, post-execution instructions (Conversation Routines style) |
| `/voicenter-bot-json-assembler` | 3 — Wire-format projection | Mechanical projection of the spec into Bot JSON; runs the §15.4 cross-reference pass (25 checks, most blocking); emits `bot-<id>-<date>.json` plus a banner of fail-loud sentinels |

---


## Authentication

**MCP plugin:** OAuth — Claude Code handles the browser flow automatically on first connection. No tokens or environment variables required.

**Code-based APIs (skill plugins):** Use the `code` parameter — your organization's API token provided by the Voicenter back office. The requesting server's IP must be authorized in CPanel.

**Push APIs (VoiceBot, Pop-Up Screen, CDR Notification, External Layer):** Voicenter calls *your* endpoint. Configure your URL in the Voicenter CPanel.

---

## API Quick Reference

| API | Base URL | Auth |
|---|---|---|
| Click2Call | `https://api.voicenter.com/ForwardDialer/click2call.aspx` | `code` param |
| Call Log | `https://api.voicenter.com/hub/cdr/` | `code` param |
| Blacklist | `https://api.voicenter.com/Blacklist/` | `Code` param |
| Extension List | `https://monitor.voicenter.co.il/Comet/api/GetExtensions` | `code` param |
| Productive Dialer | `https://api.voicenter.com/ForwardDialer/Dialer/` | `Code` param |
| Login/Logout | `https://api.voicenter.com/UserLogin/SetStatusFromAPI` | `Code` param |
| Active Calls | `https://monapisec.voicenter.co.il/comet/API/` | `code` param |
| Mute Recording | `https://<monitorX>.voicenter.co/api/MuteUnmuteCalls` | no auth param |
| Real-Time | EventsSDK (socket.io) | token / user / account |
| Lead Tracker | JS CDN script | token param |
| VoiceBot | Your endpoint (Voicenter calls you) | — |
| Pop-Up Screen | Your endpoint (Voicenter calls you) | — |
| CDR Notification | Your endpoint (Voicenter calls you) | — |
| External Layer | Your endpoint (Voicenter calls you) | — |

---

## Resources

- **API Documentation:** https://www.voicenter.com/API
- **CPanel:** https://cpanel.voicenter.com
- **Real-Time SDK:** https://github.com/VoicenterTeam/VoicenterEventsSDK
- **Developer Support:** [api@voicenter.com](mailto:api@voicenter.com)

---

## License

MIT © Voicenter
