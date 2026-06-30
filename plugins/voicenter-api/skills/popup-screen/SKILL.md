---
name: popup-screen
description: Implement a Pop-Up Screen endpoint that Voicenter calls during incoming calls to display caller CRM data to agents
---

> **Language.** Reply in the user's language: detect what they write — Hebrew→Hebrew, English→English — and mirror it, switching if they switch mid-conversation. This shapes your prose, your questions, and your `AskUserQuestion` option labels only. It does **not** change the artifacts you produce — identifiers, JSON keys, BCP-47 language codes, API field names, and other data stay exactly as specified.

> **CRM integration context.** When the user is building a full CRM integration — not just this API in isolation — always invoke the **`crm-onboarding`** skill alongside this one and frame the answer covering all three core services: Click2Call, Screen Pop, and Call History.

Help the developer build the **Pop-Up Screen** endpoint — a server-side URL that Voicenter calls when an incoming call rings, answers, or hangs up, so the agent's CRM opens automatically with the caller's details.

## When to use this skill

Use this skill when the user wants to:
- Automatically open a CRM contact page in the agent's browser when a call rings
- Show caller name, company, and account information to the agent before they pick up
- Open a "new contact" form when the caller is not found in the CRM
- Track which calls were answered vs missed in the CRM in real time
- Build screen-pop functionality using the Voicenter Chrome Extension
- Pass call metadata (ivrid, DID, extension) to the CRM to pre-fill call log entries

## Environment Variables

```env
# No outbound API token needed — Voicenter sends requests TO your server.
# Configure your endpoint URL in: Voicenter CPanel → Extension settings or DID settings → "Pop-Up Screen URL"
# The Voicenter Chrome Extension must be installed on the agent's browser for the popup to appear.
```

## How it works

1. An inbound call arrives at an agent's extension.
2. Voicenter sends the call data (caller phone, extension, DID, status) to your configured endpoint URL.
3. Your server looks up the caller in your CRM and responds with caller name, company, and CRM URL.
4. The **Voicenter Chrome Extension** pops up a notification and opens the CRM URL when clicked.

## Requests Voicenter sends you

Voicenter POSTs JSON to your endpoint at three call phases.

### Ringing Phase

```json
{
  "phone": "972722776772",
  "callerName": "Queue Testing",
  "ivrid": "20220916103546022555eb61e755c08a",
  "extenUser": "KGpK4iWq",
  "did": "0776707528",
  "status": "Ringing",
  "direction": "Incoming",
  "recordFile": "20220916103546022555eb61e755c08a-agent-972722776772-0776707528.mp3",
  "isMuted": false,
  "callStarted": 1663324548,
  "isAnswered": false,
  "callAnswered": 0,
  "currentCall": {
    "callStarted": 1663324548,
    "callAnswered": 0,
    "answered": 0,
    "callername": "Queue Testing",
    "callerphone": "972722776772",
    "callstatus": "Ringing",
    "direction": "Incoming",
    "ivrid": "20220916103546022555eb61e755c08a",
    "did": "0776707528",
    "originalCallerID": "0722776772",
    "isInternal": false
  }
}
```

### Talking Phase (answered)

Same payload with `"status": "Talking"`, `"isAnswered": true`, and `"callAnswered"` set to the answer epoch timestamp.

### Hangup Phase

Same payload with `"status": "Hangup"` and `"cause": "Normal hangup"` added.

## Key Incoming Fields

| Field | Description |
|---|---|
| `phone` | Caller's phone number (with country prefix, e.g. `972XXXXXXXXX`) |
| `extenUser` | SIP code of the agent's extension receiving the call |
| `did` | The DID (virtual number) the caller dialed |
| `ivrid` | Unique call ID — correlates with CDR Notification and Call Log |
| `status` | `Ringing`, `Talking`, or `Hangup` |
| `direction` | `Incoming` or `Outgoing` |
| `isMuted` | Whether recording is currently muted |
| `isAnswered` | `true` once the agent picks up |

## Your Response (JSON)

| Field | Required | Description |
|---|---|---|
| `STATUS` | ✅ | Must be `"OK"` (uppercase string). Any other value = error. |
| `URL` | ❌ | CRM page URL to open when the agent clicks the popup notification |
| `CLIENTNAME` | ❌ | Caller's name from your CRM |
| `TOTAL` | ❌ | Number of CRM matches found (use `0` for unknown callers) |
| `COMPANY` | ❌ | Caller's company name from your CRM |

### Response — Known caller

```json
{
  "STATUS": "OK",
  "URL": "https://yourcrm.com/contacts/12345",
  "CLIENTNAME": "John Doe",
  "TOTAL": 1,
  "COMPANY": "Acme Corp"
}
```

### Response — Unknown caller

```json
{
  "STATUS": "OK",
  "URL": "https://yourcrm.com/contacts/new?phone=0722776772",
  "CLIENTNAME": "",
  "TOTAL": 0
}
```

## TypeScript Implementation (Express)

```typescript
import express, { Request, Response } from 'express';

const app = express();
app.use(express.json());

// Allow the Voicenter Chrome Extension to call your endpoint
app.use((req, res, next) => {
  res.setHeader('Access-Control-Allow-Origin', 'chrome-extension://ifiaikfdhcagbagdeflffjdammidpbio');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  next();
});

interface PopupRequest {
  phone: string;
  extenUser: string;
  did: string;
  ivrid: string;
  status: 'Ringing' | 'Talking' | 'Hangup';
  direction: string;
  isAnswered: boolean;
  isMuted: boolean;
}

app.post('/webhooks/voicenter/popup', async (req: Request, res: Response) => {
  const payload = req.body as PopupRequest;

  // Normalize phone: Voicenter sends 972XXXXXXXXX, CRM may store as 0XXXXXXXXX
  const normalizedPhone = payload.phone.replace(/^972/, '0');

  if (payload.status === 'Ringing') {
    const contact = await crm.findByPhone(normalizedPhone);

    if (contact) {
      return res.json({
        STATUS: 'OK',
        URL: `https://yourcrm.com/contacts/${contact.id}`,
        CLIENTNAME: contact.name,
        COMPANY: contact.company,
        TOTAL: 1,
      });
    }

    // Unknown caller — open new contact form
    return res.json({
      STATUS: 'OK',
      URL: `https://yourcrm.com/contacts/new?phone=${normalizedPhone}&ivrid=${payload.ivrid}`,
      TOTAL: 0,
    });
  }

  // Talking / Hangup — acknowledge without action (or handle as needed)
  return res.json({ STATUS: 'OK' });
});

app.listen(3000);
```

## NGINX CORS Configuration

```nginx
location /webhooks/voicenter/popup {
  add_header 'Access-Control-Allow-Origin' 'chrome-extension://ifiaikfdhcagbagdeflffjdammidpbio';
  add_header 'Access-Control-Allow-Headers' 'Content-Type';
}
```

## GET format (legacy)

Voicenter can also call your endpoint as a GET request:
```
https://yourcrm.com/popup?phone=0722776772&ivrid=20241001abc&extenUser=SIPSIP&did=0776707528&statusCall=Ringing
```

## Tips

- **Respond within 3 seconds** or Voicenter times out and shows no popup.
- **Normalize the `phone` field** — Voicenter sends with country prefix (`972XXXXXXXXX`); your CRM likely stores `0XXXXXXXXX`.
- **Handle all three phases** — use `Ringing` to open the CRM, `Talking` to update it (call answered), `Hangup` to close/log it.
- Use `ivrid` to link this event to the CDR you receive later from CDR Notification.
- The **CORS header is required** — the Voicenter Chrome Extension calls your endpoint from the browser.

## Related Skills

- **CDR Notification** — Correlate with the CDR using `ivrid` after the call ends
- **External Layer** — `CUSTOM_DATA` passed in External Layer appears in the popup payload as `customdata`
- **Active Calls** — Check current call state if you need to verify before updating your CRM
- **Mute Recording** — `isMuted` in the popup payload reflects current recording state
