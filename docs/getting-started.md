# Getting started

This guide takes you from zero to a verified Voicenter integration in under 30 minutes.

---

## 1. Prerequisites

Before installing the plugins, confirm you have:

| Requirement | Where to get it |
|---|---|
| A Voicenter account with API access enabled | Contact your Voicenter account manager |
| At least one configured extension (SIP code) | [CPanel](https://cpanel.voicenter.com) → Extensions |
| An organization API token (`code`) — for REST APIs | Voicenter back office / your account manager |
| The public IP of every server that will call REST APIs | Whitelist it in CPanel → API Settings |
| Claude Code installed and signed in | [claude.com](https://claude.com) |
| (Optional) A public HTTPS endpoint for webhooks | Use [ngrok](https://ngrok.com) or your own host |

> **IP whitelisting is mandatory** for every REST API in this marketplace. Calls from non-whitelisted IPs fail with `ERROR_NUMBER 4` / `403 Unauthorized`.

---

## 2. Install the marketplace and plugins

In Claude Code:

```text
/plugin marketplace add VoicenterTeam/claude-marketplace
/plugin install voicenter-mcp@voicenter
/plugin install voicenter-api@voicenter
/plugin install voicenter-bot-builder@voicenter   # optional — only needed if you'll design bots
```

Verify the plugins are loaded:

```text
/plugin
```

Expected output: `voicenter-mcp`, `voicenter-api`, and (if installed) `voicenter-bot-builder` all **Enabled**, with **18 skills** registered in total (1 + 14 + 3). The bot-builder plugin is optional; if you only need API integrations, skip the third install line and you'll see **15 skills** registered.

---

## 3. Pick your auth path

The marketplace supports **two parallel authentication paths**. Most teams use both.

### Path A — Live MCP (OAuth)

Use this when you want Claude to call Voicenter APIs directly from a chat conversation, with no boilerplate.

1. Trigger any Voicenter action ("List my extensions").
2. Claude Code launches the OAuth browser flow automatically.
3. Sign in to Voicenter, approve, return.

That's it — no environment variables, no tokens to manage. See [skills/setup/README.md](skills/setup/README.md) for the complete walkthrough and troubleshooting.

### Path B — REST APIs (`code` parameter)

Use this when you are writing your own application code that calls Voicenter from a server.

Set these environment variables in your application:

```env
VOICENTER_API_CODE=your_organization_api_token
# Optional, only needed for the Mute Recording skill:
VOICENTER_MONITOR_SERVER=https://monitor1.voicenter.co
# Optional, only needed for the Real-Time skill:
VOICENTER_TOKEN=your_realtime_token
# Optional, only needed for the Lead Tracker skill:
VOICENTER_LEAD_TRACKER_TOKEN=your_did_pool_token
```

See [authentication.md](authentication.md) for the full auth-method matrix.

---

## 4. Configure CPanel

Depending on which skills you intend to use, configure the matching settings in [CPanel](https://cpanel.voicenter.com):

| Skill | CPanel setting |
|---|---|
| All REST skills (`code` param) | API Settings → add server IP to whitelist |
| Pop-Up Screen | Extension or DID settings → "Pop-Up Screen URL" |
| External Layer | IVR layer settings → enable "Allow Mini External IVR" → set endpoint URL + fallback layer |
| CDR Notification | Integrations → CDR Notification → set webhook URL |
| VoiceBot | Voice Agent intent settings → set "URL" field |
| Lead Tracker | Voicenter provisions a DID pool tied to the token |

---

## 5. Send your first request

The Click2Call skill is the quickest way to validate that everything works end-to-end. It will literally make a phone ring.

### Option A — Ask Claude (using the MCP plugin)

```text
Initiate a click2call from extension SIPSIP to 0501234567 with recording on.
```

Claude calls the MCP server, the API, and reports the resulting `CALLID`.

### Option B — Curl (using your `code` token)

```bash
curl -X POST https://api.voicenter.com/ForwardDialer/click2call.aspx \
  -H "Content-Type: application/json" \
  -d '{
    "code": "YOUR_API_CODE",
    "phone": "SIPSIP",
    "target": "0501234567",
    "action": "call",
    "format": "json",
    "record": "true"
  }'
```

A successful response returns `ERRORCODE: 0` and a `CALLID`. The agent extension rings first; once the agent picks up, the customer is dialed and bridged.

If you get an error, see the [Click2Call skill page](skills/click2call/README.md#error-codes) for the full error matrix.

---

## 6. Pick your next integration

The marketplace is designed so you adopt skills incrementally. Common starter combinations:

| Use case | Skills to read next |
|---|---|
| "Call" button in our CRM | [click2call](skills/click2call/README.md) → [extension-list](skills/extension-list/README.md) → [cdr-notification](skills/cdr-notification/README.md) |
| Screen-pop CRM on incoming calls | [popup-screen](skills/popup-screen/README.md) → [external-layer](skills/external-layer/README.md) |
| Live wallboard / supervisor dashboard | [real-time](skills/real-time/README.md) → [active-calls](skills/active-calls/README.md) |
| AI voice agent with CRM data | [voicebot](skills/voicebot/README.md) → [external-layer](skills/external-layer/README.md) → [cdr-notification](skills/cdr-notification/README.md) |
| Outbound campaigns | [productive-dialer](skills/productive-dialer/README.md) → [blacklist](skills/blacklist/README.md) → [call-log](skills/call-log/README.md) |
| Marketing call attribution | [lead-tracker](skills/lead-tracker/README.md) → [cdr-notification](skills/cdr-notification/README.md) |
| PCI-DSS compliance | [mute-recording](skills/mute-recording/README.md) → [real-time](skills/real-time/README.md) |
| Workforce management / agent status | [login-logout](skills/login-logout/README.md) → [real-time](skills/real-time/README.md) |

[architecture.md](architecture.md) explains how these skills compose into the canonical Voicenter flows.

---

## 7. Common first-run errors

| Symptom | Likely cause | Fix |
|---|---|---|
| `ERROR_NUMBER 4`, `403` | Server IP not whitelisted | Add IP in CPanel → API Settings |
| `ERROR_NUMBER 2`, `Authorization Failed` | Wrong `code` value | Check the token from your Voicenter back office |
| Click2Call returns `ERRORCODE 3` | Agent extension offline | Verify SIP registration, or set `checkphonedevicestate=false` for testing |
| Response is XML instead of JSON | Missing `format=json` | Always include `format=json` in Click2Call requests |
| Phone "doesn't dial" | Number is in wrong format | Use **E.164 without `+`** — `972501234567`, not `+972501234567` or `0501234567` |
| Webhook never fires | Endpoint not configured in CPanel, or HTTPS cert invalid | Set the URL in CPanel; verify the cert chain |
| Pop-Up doesn't appear in browser | Missing CORS header or Chrome Extension not installed | Add `Access-Control-Allow-Origin: chrome-extension://ifiaikfdhcagbagdeflffjdammidpbio` |
| MCP OAuth never launches | Account does not have MCP enabled | Email [[email protected]](mailto:[email protected]) |

---

## 8. Where to go next

- [Architecture & call flows](architecture.md) — how the APIs fit together
- [Authentication](authentication.md) — every auth model in detail
- [Glossary](glossary.md) — Voicenter-specific terminology
- [Per-plugin documentation](plugins/voicenter-api.md)
