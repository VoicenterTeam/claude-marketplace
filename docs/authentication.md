# Authentication

The Voicenter marketplace exposes five distinct authentication models. Pick the one that matches the skill you are integrating.

---

## At-a-glance matrix

| Auth model | Used by | Where credentials come from | Server IP whitelist required? |
|---|---|---|---|
| OAuth (MCP) | `voicenter-mcp` plugin | Browser flow on first use | No |
| `code` parameter (REST) | Click2Call, Call Log, Blacklist, Extension List, Productive Dialer, Login/Logout, Active Calls | Voicenter back office | **Yes** |
| Webhook (no inbound auth) | VoiceBot, Pop-Up Screen, CDR Notification, External Layer | Voicenter calls *your* endpoint | No (Voicenter's IPs reach you) |
| Socket.io token / account / user | Real-Time | Voicenter back office (token) or CPanel user (email/password) | No |
| Browser JS token | Lead Tracker | Voicenter back office (DID-pool token) | No |
| Dynamic monitor server | Mute Recording | Comes from Real-Time SDK connection URL or Voicenter support | Implicit (must be reachable from your server) |

---

## 1. OAuth (`voicenter-mcp`)

Used only by the live MCP plugin. There is **nothing to configure**.

- The first time Claude Code calls a Voicenter MCP tool, it launches your default browser to the Voicenter authorization page.
- You sign in, approve the requested scopes, and Claude stores the token securely.
- Tokens are refreshed automatically.

If the token expires or you switch accounts, the next API call re-triggers the OAuth flow.

See [skills/setup/README.md](skills/setup/README.md) for the full walkthrough and troubleshooting.

---

## 2. `code` parameter (REST APIs)

The most common server-side model. Every REST skill in `voicenter-api` uses the same idea: send your organization API token as either `code` (lowercase) or `Code` (uppercase) in the request body / query string.

### Where to put the token

| Skill | Field name | Position |
|---|---|---|
| Click2Call | `code` | body / query |
| Call Log | `code` | body |
| Blacklist | `Code` | body |
| Extension List | `code` | body / query |
| Productive Dialer | `Code` | body |
| Login/Logout | `Code` | body |
| Active Calls | `code` | body / query |

> The case difference (`code` vs `Code`) is intentional and not interchangeable on every endpoint. Match exactly what each skill page documents.

### Recommended environment variable

```env
VOICENTER_API_CODE=your_organization_api_token_here
```

### IP whitelisting

Every REST endpoint above also requires the **public IP of the calling server** to be whitelisted in:

> **CPanel → API Settings → Authorized IPs**

If the IP is not whitelisted, you receive `ERROR_NUMBER 4` (or equivalent per skill) with a `403`.

For local development, either:
- Whitelist your home/office IP temporarily, **or**
- Whitelist a fixed proxy IP and route through it.

---

## 3. Webhook endpoints (no inbound auth)

Four skills are **inbound** — Voicenter POSTs to your endpoint:

- [VoiceBot](skills/voicebot/README.md)
- [Pop-Up Screen](skills/popup-screen/README.md)
- [CDR Notification](skills/cdr-notification/README.md)
- [External Layer](skills/external-layer/README.md)

Voicenter does **not** send a shared secret or signature with these requests. Your protection options:

| Option | Notes |
|---|---|
| Restrict by source IP at your edge | Ask Voicenter support for the up-to-date list of egress IPs |
| Require a secret query parameter you set in CPanel | Treat the URL itself as a secret (HTTPS only) |
| Validate payload shape | Reject malformed payloads early |

Always:

- Serve the endpoint over **HTTPS** with a valid certificate.
- Reply `200 OK` quickly. CDR/External-Layer have hard timeouts (5 s for External Layer, 3 s for Pop-Up).
- Treat `ivruniqueid` as the idempotency key — Voicenter retries on transient failures.

### CORS gotcha (Pop-Up Screen only)

Pop-Up Screen is called from the Voicenter Chrome Extension running in the agent's browser, not from a Voicenter server. You must add:

```http
Access-Control-Allow-Origin: chrome-extension://ifiaikfdhcagbagdeflffjdammidpbio
Access-Control-Allow-Headers: Content-Type
```

---

## 4. Real-Time SDK (socket.io)

The Real-Time skill supports three login modes via the EventsSDK:

| Mode | Credentials | When to use |
|---|---|---|
| `token` | `token` from Voicenter back office | Server-side, account-wide events (recommended) |
| `account` | `username` + `password` | Server-side, account-wide events |
| `user` | `email` + `password` (CPanel user) | One specific agent's events |

```env
VOICENTER_TOKEN=your_realtime_token
# or
VOICENTER_USERNAME=...
VOICENTER_PASSWORD=...
# or
[email protected]
VOICENTER_PASSWORD=...
```

The SDK auto-reconnects on socket disconnects. On reconnect you receive fresh `AllExtensionsStatus` and `loginStatus` snapshots — re-initialize your in-memory state from those events.

See [skills/real-time/README.md](skills/real-time/README.md).

---

## 5. Lead Tracker JS token

Lead Tracker is **client-side only** — the token lives in your HTML and is exposed to visitors. It is bound to a specific DID pool, not your full account, so this is intentional and safe.

```env
VOICENTER_LEAD_TRACKER_TOKEN=your_did_pool_token
```

Initialize in the browser:

```javascript
VC_DID_TRACKER.init(LEAD_TRACKER_TOKEN, { /* visitor info */ });
```

See [skills/lead-tracker/README.md](skills/lead-tracker/README.md).

---

## 6. Mute Recording — dynamic monitor server

Mute Recording does **not** use a `code` parameter at all. Instead, the request goes directly to your account's **monitor server**, which is implicitly authenticated by:

- Calling the correct hostname (per-account, e.g. `monitor1.voicenter.co`).
- Originating from a server that can reach that monitor.

Two ways to obtain the hostname:

1. The Real-Time SDK connection URL — log it on connect, the host portion is your monitor server.
2. Ask Voicenter support for the static name assigned to your account.

```env
VOICENTER_MONITOR_SERVER=https://monitor1.voicenter.co
```

See [skills/mute-recording/README.md](skills/mute-recording/README.md).

---

## Recommended `.env` template

A complete environment for an integration that uses every skill:

```env
# Server-side REST APIs
VOICENTER_API_CODE=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Real-Time SDK (pick one mode)
VOICENTER_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# VOICENTER_USERNAME=...
# VOICENTER_PASSWORD=...

# Mute Recording
VOICENTER_MONITOR_SERVER=https://monitor1.voicenter.co

# Browser-side Lead Tracker (separate token, scoped to a DID pool)
VOICENTER_LEAD_TRACKER_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

Webhook skills (VoiceBot, Pop-Up Screen, CDR Notification, External Layer) need **no env vars** — only a URL configured in CPanel.

---

## Security checklist

- [ ] Treat `VOICENTER_API_CODE` as a top-tier secret. Rotate via Voicenter back office.
- [ ] Never put the API code in client-side JS — it is a server-only credential.
- [ ] Whitelist the **minimum** set of server IPs needed.
- [ ] Serve all webhook endpoints over HTTPS with a valid cert.
- [ ] Apply rate limiting on inbound webhooks to absorb retry storms.
- [ ] Log the call ID (`ivruniqueid`) on every event for traceability.
- [ ] Deduplicate webhook payloads on `ivruniqueid` before side-effects.
- [ ] For Pop-Up Screen, restrict CORS to the Voicenter Chrome Extension origin only.
- [ ] For PCI-DSS scope: pair Click2Call recording with [Mute Recording](skills/mute-recording/README.md) for sensitive sections.
