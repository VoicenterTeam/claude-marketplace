---
description: Handle and verify incoming Voicenter webhook events in your server
---

Help the developer **build a webhook handler** that receives, verifies, and processes Voicenter events.

## Payload structure

Every Voicenter webhook POST has this shape:

```json
{
  "event": "call.ended",
  "timestamp": "2024-06-01T10:04:30Z",
  "accountId": "YOUR_ACCOUNT_ID",
  "data": {
    "callId": "abc-123",
    "src": "1001",
    "dst": "+972501234567",
    "duration": 270,
    "status": "answered",
    "agentName": "John Doe",
    "recordingUrl": "https://recordings.voicenter.com/abc-123.mp3"
  },
  "signature": "sha256=HMAC_SIGNATURE"
}
```

## Signature verification

Always verify the `X-Voicenter-Signature` header before processing events.

**Node.js / TypeScript (Express)**
```typescript
import crypto from 'crypto';
import express from 'express';

const app = express();
app.use(express.raw({ type: 'application/json' })); // must use raw body for HMAC

const WEBHOOK_SECRET = process.env.VOICENTER_WEBHOOK_SECRET!;

function verifySignature(rawBody: Buffer, signature: string): boolean {
  const expected = 'sha256=' + crypto
    .createHmac('sha256', WEBHOOK_SECRET)
    .update(rawBody)
    .digest('hex');
  return crypto.timingSafeEqual(Buffer.from(expected), Buffer.from(signature));
}

app.post('/webhooks/voicenter', (req, res) => {
  const sig = req.headers['x-voicenter-signature'] as string;
  if (!sig || !verifySignature(req.body, sig)) {
    return res.status(401).send('Invalid signature');
  }

  const event = JSON.parse(req.body.toString());
  handleEvent(event);
  res.sendStatus(200); // respond quickly, process async
});

async function handleEvent(event: { event: string; data: any }) {
  switch (event.event) {
    case 'call.ended':
      console.log(`Call ${event.data.callId} lasted ${event.data.duration}s`);
      // update CRM, save recording URL, etc.
      break;
    case 'sms.received':
      console.log(`Inbound SMS from ${event.data.from}: ${event.data.text}`);
      break;
    case 'agent.status_change':
      console.log(`Agent ${event.data.agentName} is now ${event.data.presence}`);
      break;
    default:
      console.log('Unhandled event:', event.event);
  }
}
```

**Python (Flask)**
```python
import hmac, hashlib, os
from flask import Flask, request, abort

app = Flask(__name__)
WEBHOOK_SECRET = os.environ["VOICENTER_WEBHOOK_SECRET"].encode()

def verify(raw_body, signature):
    expected = "sha256=" + hmac.new(WEBHOOK_SECRET, raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)

@app.post("/webhooks/voicenter")
def webhook():
    sig = request.headers.get("X-Voicenter-Signature", "")
    if not verify(request.get_data(), sig):
        abort(401)
    event = request.json
    print(f"Received event: {event['event']}")
    # process event...
    return "", 200
```

## Local development with tunnels

Use a tunnel to expose your local server during development:

```bash
# ngrok
ngrok http 3000
# Then register: https://abc123.ngrok.io/webhooks/voicenter

# cloudflared
cloudflare tunnel --url http://localhost:3000
```

## Best practices

- **Respond with 200 immediately**, then process async (use a queue like BullMQ or Celery).
- **Idempotency**: Voicenter may retry failed deliveries — store `callId`/`messageId` to deduplicate.
- **Log everything**: store the raw payload before processing to replay events during debugging.
- **Use the MCP server** (`voicenter-mcp` plugin) if you want Claude to act on events in real time — e.g., "When a call ends, pull the recording and summarize it."
