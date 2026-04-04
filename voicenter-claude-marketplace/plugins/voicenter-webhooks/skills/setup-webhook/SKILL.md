---
description: Register and manage Voicenter webhooks for real-time event delivery
---

Help the developer **register a webhook endpoint** so Voicenter can push real-time events — call answered, call ended, SMS delivered, queue events, etc.

## Register a webhook

**Endpoint:** `POST https://api.voicenter.com/v2/webhooks`

```json
{
  "url": "https://yourapp.com/webhooks/voicenter",
  "events": ["call.initiated", "call.answered", "call.ended", "sms.delivered", "sms.failed"],
  "secret": "your-signing-secret",
  "accountId": "ACCOUNT_ID"
}
```

**Available events:**

| Event | Trigger |
|---|---|
| `call.initiated` | A call starts (click-to-call or inbound) |
| `call.answered` | Agent or callee picks up |
| `call.ended` | Call hangs up (includes duration, recording URL) |
| `call.missed` | Inbound call not answered |
| `queue.call_waiting` | A call enters a queue |
| `queue.call_abandoned` | Caller hangs up while waiting |
| `sms.delivered` | Outbound SMS confirmed delivered |
| `sms.failed` | Outbound SMS delivery failed |
| `sms.received` | Inbound SMS received |
| `ivr.dtmf` | Caller presses a key in an IVR menu |
| `voicebot.session` | AI Voice Bot conversation completed |
| `agent.status_change` | Agent changes presence (available → busy → away) |

## List and manage webhooks

```
GET  /v2/webhooks          — list all registered webhooks
GET  /v2/webhooks/{id}     — get one webhook
PATCH /v2/webhooks/{id}    — update URL or events
DELETE /v2/webhooks/{id}   — remove a webhook
```

## Example — TypeScript (register)

```typescript
async function registerWebhook(
  token: string,
  accountId: string,
  url: string,
  events: string[],
  secret: string
) {
  const res = await fetch('https://api.voicenter.com/v2/webhooks', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ url, events, secret, accountId }),
  });
  if (!res.ok) throw new Error(`Webhook registration failed: ${res.status}`);
  return res.json(); // { webhookId, url, events, status: "active" }
}
```
