# Plugin: `voicenter-api`

Integration skills for all 14 Voicenter APIs — VoiceBot, Click2Call, Pop-Up Screen, CDR Notification, External Layer, Call Log, Blacklist, Mute Recording, Extension List, Real-Time, Productive Dialer, Login/Logout, Lead Tracker, Active Calls.

Each skill teaches Claude exactly how to help you build one specific integration: correct endpoints, real request/response examples, error matrices, and TypeScript scaffolding. Use this plugin when you want Claude to **write production code** that talks to Voicenter directly (as opposed to operating Voicenter live, which is the [`voicenter-mcp`](voicenter-mcp.md) plugin's job).

---

## Manifest

[`plugins/voicenter-api/.claude-plugin/plugin.json`](../../plugins/voicenter-api/.claude-plugin/plugin.json):

```json
{
  "name": "voicenter-api",
  "description": "Skills for all 14 Voicenter APIs: VoiceBot, Click2Call, Pop-Up Screen, CDR Notification, External Layer, Call Log, Blacklist, Mute Recording, Extension List, Real-Time, Productive Dialer, Login/Logout, Lead Tracker, Active Calls",
  "version": "1.1.1",
  "keywords": ["voicenter", "telephony", "crm", "integration", "click2call", "cdr", "dialer", "voip", "click-to-call", "pbx", "ccaas", "cti", "voicebot", "voiceai", "voice-ai", "callcenter", "contact-center"]
}
```

Skills auto-discover from `plugins/voicenter-api/skills/`. There are 14 skill folders, each containing exactly one `SKILL.md`.

---

## Skill index

Sorted by category. Each link goes to the dedicated docs page; the source SKILL.md lives under [`plugins/voicenter-api/skills/`](../../plugins/voicenter-api/skills).

### Incoming call routing & enrichment

| Skill | Description | Doc |
|---|---|---|
| `external-layer` | Decide where an inbound call goes mid-IVR by calling your endpoint | [docs](../skills/external-layer/README.md) |
| `popup-screen` | Screen-pop a CRM URL on the agent's browser when a call rings | [docs](../skills/popup-screen/README.md) |
| `voicebot` | Feed dynamic CRM data to the Voicenter Voice Agent during a conversation | [docs](../skills/voicebot/README.md) |

### Outgoing call control

| Skill | Description | Doc |
|---|---|---|
| `click2call` | Initiate (or terminate) a 2-leg outbound call from your CRM | [docs](../skills/click2call/README.md) |
| `mute-recording` | Mute / unmute call recording in real time for PCI-DSS compliance | [docs](../skills/mute-recording/README.md) |

### Call data & analytics

| Skill | Description | Doc |
|---|---|---|
| `cdr-notification` | Receive each CDR (with optional AI analysis) via webhook the moment a call ends | [docs](../skills/cdr-notification/README.md) |
| `call-log` | Query historical CDRs by date, phone, extension, type, campaign, queue | [docs](../skills/call-log/README.md) |
| `lead-tracker` | Browser SDK that assigns dynamic DIDs per visitor for marketing attribution | [docs](../skills/lead-tracker/README.md) |

### Agent & extension management

| Skill | Description | Doc |
|---|---|---|
| `extension-list` | Full directory of extensions, users, departments, SIP codes | [docs](../skills/extension-list/README.md) |
| `login-logout` | Set agent status (Login/Logout/Lunch/...) from your CRM | [docs](../skills/login-logout/README.md) |
| `real-time` | Socket.io stream of live call & agent events (EventsSDK) | [docs](../skills/real-time/README.md) |

### Outbound dialer & compliance

| Skill | Description | Doc |
|---|---|---|
| `productive-dialer` | Manage auto-dialer campaigns, upload up to 100k destinations, manage agents | [docs](../skills/productive-dialer/README.md) |
| `blacklist` | Add or remove numbers from the dialing blacklist | [docs](../skills/blacklist/README.md) |

### Live monitoring

| Skill | Description | Doc |
|---|---|---|
| `active-calls` | One-shot snapshot of all live calls and queue depth | [docs](../skills/active-calls/README.md) |

---

## Authentication

This plugin's skills span four auth models. The skill page documents which one applies; full reference in [authentication.md](../authentication.md).

| Auth | Skills |
|---|---|
| `code` parameter (REST) + IP whitelist | `click2call`, `call-log`, `blacklist`, `extension-list`, `productive-dialer`, `login-logout`, `active-calls` |
| Webhook (no inbound auth) | `voicebot`, `popup-screen`, `cdr-notification`, `external-layer` |
| Socket.io token / account / user | `real-time` |
| Browser JS token | `lead-tracker` |
| Dynamic monitor server | `mute-recording` |

---

## Recommended environment variables

Aggregated `.env` if you intend to use the full plugin:

```env
# Server-side REST APIs
VOICENTER_API_CODE=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Real-Time SDK (pick one mode)
VOICENTER_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Mute Recording
VOICENTER_MONITOR_SERVER=https://monitor1.voicenter.co

# Browser-side Lead Tracker (separate token, scoped to a DID pool)
VOICENTER_LEAD_TRACKER_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

---

## Installation

```text
/plugin marketplace add VoicenterTeam/claude-marketplace
/plugin install voicenter-api@voicenter
```

Verify:

```text
/plugin
```

`voicenter-api` should be **Enabled** with **14 skills** registered.

---

## How a skill is structured

Each `SKILL.md` follows the same template (kept short for fast Claude loading):

1. YAML frontmatter (`name`, `description`)
2. *When to use this skill* — bullet list of triggers
3. *Environment variables* — what to set
4. *Endpoint* — URL and accepted methods
5. *Authentication* — exact field name and casing
6. *Request* — fields, examples (POST-JSON and GET when relevant)
7. *Response* — fields and full example
8. *Error codes* — matrix with meanings
9. *TypeScript implementation* — runnable example
10. *Tips* — gotchas and best practices
11. *Related skills* — cross-links

The dedicated page under `docs/skills/<skill>/` mirrors and extends each section with deeper troubleshooting and additional patterns.

---

## Versioning

The plugin and the marketplace are released together. Current version: **1.1.1**. See [CHANGELOG.md](../../CHANGELOG.md).

---

## Related documentation

- [Companion plugin: voicenter-mcp](voicenter-mcp.md)
- [Architecture & call flows](../architecture.md)
- [Authentication](../authentication.md)
- [Glossary](../glossary.md)
