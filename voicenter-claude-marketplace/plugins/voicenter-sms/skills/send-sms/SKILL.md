---
description: Send an SMS message via the Voicenter SMS API
---

Help the developer **send SMS messages** through Voicenter — single messages, bulk sends, or programmatic notifications.

## What to do

1. Ask what they are building: one-time notification, OTP, bulk campaign, or a triggered alert.
2. Build the correct request for their use case.
3. Explain sender ID rules and character limits.

## Voicenter SMS API

**Endpoint:** `POST https://api.voicenter.com/v2/sms/send`

**Authentication:** Bearer token in `Authorization` header.

**Request body:**
```json
{
  "from": "SENDER_ID_OR_DID",
  "to": "+972501234567",
  "text": "Your OTP is 8421",
  "accountId": "ACCOUNT_ID"
}
```

| Field | Required | Notes |
|---|---|---|
| `from` | Yes | Approved sender ID or DID number |
| `to` | Yes | E.164 format e.g. `+972501234567` |
| `text` | Yes | Max 160 chars for one SMS segment; longer messages split automatically |
| `accountId` | Yes | Your Voicenter account ID |
| `scheduleAt` | No | ISO 8601 — schedule for future delivery |
| `callbackUrl` | No | Webhook URL for delivery status updates |

**Response:**
```json
{
  "messageId": "sms-uuid-here",
  "status": "queued",
  "segments": 1
}
```

## Example — TypeScript

```typescript
interface SmsSendResult {
  messageId: string;
  status: 'queued' | 'sent' | 'failed';
  segments: number;
}

async function sendSms(
  token: string,
  accountId: string,
  from: string,
  to: string,
  text: string
): Promise<SmsSendResult> {
  const res = await fetch('https://api.voicenter.com/v2/sms/send', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ from, to, text, accountId }),
  });
  if (!res.ok) throw new Error(`SMS failed: ${res.status} ${await res.text()}`);
  return res.json();
}
```

## Bulk SMS — send to multiple recipients

```typescript
async function bulkSend(token: string, accountId: string, from: string, recipients: string[], text: string) {
  const results = await Promise.allSettled(
    recipients.map(to => sendSms(token, accountId, from, to, text))
  );
  const failed = results.filter(r => r.status === 'rejected');
  if (failed.length) console.warn(`${failed.length} messages failed`);
  return results;
}
```

## Example — Python

```python
import requests

def send_sms(token, account_id, from_id, to, text):
    r = requests.post(
        "https://api.voicenter.com/v2/sms/send",
        headers={"Authorization": f"Bearer {token}"},
        json={"from": from_id, "to": to, "text": text, "accountId": account_id}
    )
    r.raise_for_status()
    return r.json()  # {"messageId": ..., "status": "queued", "segments": 1}
```

## Tips

- **Sender ID**: must be pre-approved in your Voicenter account. Alphanumeric IDs (e.g. `MyApp`) are supported in most countries.
- **OTP messages**: keep them under 160 characters to avoid multi-segment billing.
- **Delivery receipts**: pass a `callbackUrl` and use the `voicenter-webhooks` plugin to handle `sms.delivered` / `sms.failed` events.
- **Opt-outs**: respect STOP requests — use the SMS history API to check for opt-out replies before sending.
