---
description: Implement a Pop-Up Screen endpoint that Voicenter calls during incoming calls to display caller CRM data to agents
---

Help the developer build the **Pop-Up Screen** endpoint — a server-side URL that Voicenter calls when an incoming call rings, answers, or hangs up, so the agent's CRM can display the caller's details automatically.

## How it works

1. An inbound call arrives. Voicenter looks up your configured endpoint URL.
2. Voicenter sends the call data (caller phone, extension, DID, status) to your endpoint via HTTP.
3. Your server looks up the caller in your CRM and responds with the caller's name, company, and a URL to open.
4. The **Voicenter Chrome Extension** pops up a notification showing that data and opens the CRM URL when clicked.

Configure your endpoint URL in the Voicenter CPanel under the extension or DID settings.

## Requests Voicenter sends you

Voicenter POSTs JSON to your endpoint at three call phases: **Ringing**, **Talking** (answered), and **Hangup**.

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
  "recordFile": "20220916103546022555eb61e755c08a-nikitaapi-972722776772-0776707528.mp3",
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

Same payload with `"cause": "Normal hangup"` added.

## Key incoming fields

| Field | Description |
|---|---|
| `phone` | Caller's phone number (with country prefix) |
| `extenUser` | SIP code of the agent's extension receiving the call |
| `did` | The DID (virtual number) the caller dialed |
| `ivrid` | Unique call ID — use to correlate with CDR Notification and Call Log |
| `status` | `Ringing` / `Talking` |
| `direction` | `Incoming` / `Outgoing` |
| `isMuted` | Whether recording is currently muted |

## Your response (JSON)

| Field | Required | Description |
|---|---|---|
| `STATUS` | ✅ | Must be `"OK"` (uppercase). Any other value = error. |
| `URL` | ❌ | CRM page URL to open when the agent clicks the notification |
| `CLIENTNAME` | ❌ | Caller's name from your CRM |
| `TOTAL` | ❌ | Number of CRM matches found |
| `COMPANY` | ❌ | Caller's company from your CRM |

### Response Example

```json
{
  "STATUS": "OK",
  "URL": "https://yourcrm.com/contacts?phone=0722776772",
  "CLIENTNAME": "John Doe",
  "TOTAL": 1,
  "COMPANY": "Acme Corp"
}
```

## TypeScript Implementation (Express)

```typescript
import express, { Request, Response } from 'express';

const app = express();
app.use(express.json());

interface PopupRequest {
  phone: string;
  extenUser: string;
  did: string;
  ivrid: string;
  status: 'Ringing' | 'Talking';
  direction: string;
  isAnswered: boolean;
  callAnswered: number;
}

interface PopupResponse {
  STATUS: 'OK' | string;
  URL?: string;
  CLIENTNAME?: string;
  TOTAL?: number;
  COMPANY?: string;
}

async function lookupCallerInCRM(phone: string): Promise<{ name: string; company: string; url: string } | null> {
  // Replace with your actual CRM lookup logic
  const normalized = phone.replace(/^972/, '0'); // Convert 972XXXXXXXXX → 0XXXXXXXXX
  const contact = await yourCRM.findByPhone(normalized);
  if (!contact) return null;
  return {
    name: contact.name,
    company: contact.company,
    url: `https://yourcrm.com/contacts/${contact.id}`,
  };
}

app.post('/webhooks/voicenter/popup', async (req: Request, res: Response) => {
  const payload = req.body as PopupRequest;

  // Only act on Ringing — ignore Talking/Hangup if not needed
  if (payload.status !== 'Ringing') {
    return res.json({ STATUS: 'OK' });
  }

  const caller = await lookupCallerInCRM(payload.phone);

  const response: PopupResponse = caller
    ? { STATUS: 'OK', URL: caller.url, CLIENTNAME: caller.name, COMPANY: caller.company, TOTAL: 1 }
    : { STATUS: 'OK', TOTAL: 0 };

  res.json(response);
});

app.listen(3000);
```

## CORS for the Chrome Extension

The Voicenter Chrome Extension calls your endpoint from the browser. Add this header to your server responses:

```typescript
app.use((req, res, next) => {
  res.setHeader('Access-Control-Allow-Origin', 'chrome-extension://ifiaikfdhcagbagdeflffjdammidpbio');
  next();
});
```

**NGINX:**
```nginx
location /webhooks/voicenter/popup {
  add_header 'Access-Control-Allow-Origin' 'chrome-extension://ifiaikfdhcagbagdeflffjdammidpbio';
}
```

## GET format (legacy)

Voicenter can also call your endpoint as a GET request:
```
https://yourcrm.com/popup?phone=0722776772&ivrid=20241001abc&extenUser=SIPSIP&did=0776707528&statusCall=Ringing
```

## Tips

- Respond within **3 seconds** or Voicenter will time out and show no popup.
- Normalize the incoming `phone` field — Voicenter sends it with country prefix (`972XXXXXXXXX`), but your CRM may store it as `0XXXXXXXXX`.
- Use `ivrid` to link this popup event to the CDR you'll receive later from the CDR Notification API.
- Handle all three phases (`Ringing`, `Talking`, `Hangup`) — use them to open, update, and close the CRM tab.
