# Voicenter Claude Code Plugin Marketplace

Official Claude Code plugins for integrating the Voicenter telephony platform into your development workflow.

## Quick Start

```bash
# Add the Voicenter marketplace to Claude Code
/plugin marketplace add VoicenterTeam/claude-marketplace

# Install the live MCP plugin (recommended)
/plugin install voicenter-mcp@voicenter

# Or install individual API skill plugins
/plugin install voicenter-telephony@voicenter
/plugin install voicenter-sms@voicenter
/plugin install voicenter-webhooks@voicenter
```

---

## Plugins

### 🔴 `voicenter-mcp` — Live API Access (Recommended)

Connects Claude Code to **`mcp.voicenter.co`** — a live MCP server that gives Claude real-time access to all Voicenter APIs. No code needed: just ask Claude in plain English.

**Setup:** Set your API token as an environment variable:
```bash
export VOICENTER_API_TOKEN="your-token-here"
```

**Example prompts once connected:**
- *"Call extension 1001 from +972031234567"*
- *"Send an SMS to +972501234567 saying 'Your order is ready'"*
- *"Show me all missed calls from today"*
- *"What's the current queue wait time for Support?"*
- *"Build me an IVR that routes sales to queue q-sales"*

Skills included:
- `/setup` — Authentication setup and connection guide

---

### 📞 `voicenter-telephony` — Calls API

Skills for integrating calling into your application code.

| Skill | What it does |
|---|---|
| `/make-call` | Click-to-call integration with code examples |
| `/call-history` | Query CDR records with filtering and pagination |
| `/call-recordings` | Access, stream, and download recordings |

---

### 💬 `voicenter-sms` — SMS API

| Skill | What it does |
|---|---|
| `/send-sms` | Send messages and bulk SMS with delivery callbacks |
| `/sms-history` | Query sent/received SMS and delivery stats |

---

### 👥 `voicenter-users` — Users & Extensions API

| Skill | What it does |
|---|---|
| `/list-extensions` | List and search agents, check presence status |
| `/manage-agents` | Create, update, and deactivate extensions |

---

### 📊 `voicenter-reports` — Reports & Analytics API

| Skill | What it does |
|---|---|
| `/call-report` | Summary reports by agent, queue, or time period |
| `/queue-stats` | Real-time and historical queue statistics + SLA |

---

### 🤖 `voicenter-ivr` — IVR & Voice Bots API

| Skill | What it does |
|---|---|
| `/build-ivr` | Design multi-node IVR flows with menus, routing, and schedules |
| `/voicebot-config` | Create and configure AI Voice Bots with intents |

---

### 🔔 `voicenter-webhooks` — Webhooks & Events API

| Skill | What it does |
|---|---|
| `/setup-webhook` | Register webhooks for real-time event delivery |
| `/handle-events` | Verify signatures and process webhook payloads |

---

## Authentication

All API calls require a Bearer token. Obtain it from **Voicenter Portal → Settings → API Access**.

For the **MCP plugin**, set `VOICENTER_API_TOKEN` in your environment.

For **code you write** using the skill plugins, generate a token programmatically:
```
POST https://api.voicenter.com/v2/auth/token
{ "username": "...", "password": "...", "accountId": "..." }
```

---

## Requirements

- [Claude Code](https://claude.ai/code) (any plan)
- A Voicenter account with API access enabled
- For `voicenter-mcp`: `VOICENTER_API_TOKEN` environment variable set

---

## Support

- **Voicenter API Docs:** https://developers.voicenter.com
- **MCP Server:** https://mcp.voicenter.co
- **Issues:** https://github.com/VoicenterTeam/claude-marketplace/issues
- **Email:** [devs@voicenter.com](mailto:devs@voicenter.com)

---

## License

MIT © Voicenter
