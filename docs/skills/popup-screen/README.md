# Skill: `popup-screen`

Implement a Pop-Up Screen endpoint that Voicenter calls during incoming calls to display caller CRM data to agents.

> Source: [`plugins/voicenter-api/skills/popup-screen/SKILL.md`](../../../plugins/voicenter-api/skills/popup-screen/SKILL.md)
> Plugin: [voicenter-api](../../plugins/voicenter-api.md) · Direction: **Incoming** · Transport: **Webhook (push)**

---

> **Language.** Reply in the user's language: detect what they write — Hebrew→Hebrew, English→English — and mirror it, switching if they switch mid-conversation. This shapes your prose, your questions, and your `AskUserQuestion` option labels only. It does **not** change the artifacts you produce — identifiers, JSON keys, BCP-47 language codes, API field names, and other data stay exactly as specified.

## When to use this skill

- Open a CRM contact page in the agent's browser when a call rings
- Show caller name, company, and account info before the agent picks up
- Open a "new contact" form when the caller is unknown
- Track answered vs missed calls in the CRM in real time
- Build screen-pop using the Voicenter Chrome Extension
- Pre-fill call log entries with `ivrid`, `did`, and extension metadata

---

## How it works

1. An inbound call arrives at an agent's extension.
2. Voicenter POSTs the call data to your configured endpoint URL (Ringing → Talking → Hangup).
3. Your server looks up the caller in CRM and replies with `STATUS: "OK"`, `URL`, `CLIENTNAME`, `COMPANY`, `TOTAL`.
4. The **Voicenter Chrome Extension** displays a notification and opens the URL when clicked.

> Configure the URL under: **CPanel → Extension or DID settings → "Pop-Up Screen URL"**.
> The agent's browser must have the **Voicenter Chrome Extension** installed.

---

## Phases

Voicenter POSTs three times per call (Ringing, Talking, Hangup) — same payload shape, different `status` and added fields.

### Ringing

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

### Talking

Same payload with `"status": "Talking"`, `"isAnswered": true`, and `"callAnswered"` set to the answer epoch.

### Hangup

Same payload with `"status": "Hangup"` and `"cause": "Normal hangup"` added.

---

## Key incoming fields

| Field | Description |
|---|---|
| `phone` | Caller's number with country prefix (`972XXXXXXXXX`) |
| `extenUser` | SIP code of the receiving extension |
| `did` | DID dialed |
| `ivrid` | Universal call ID |
| `status` | `Ringing`, `Talking`, `Hangup` |
| `direction` | `Incoming` or `Outgoing` |
| `isMuted` | Recording mute state |
| `isAnswered` | `true` after pickup |
| `currentCall.customdata` | `CUSTOM_DATA` set in [External Layer](../external-layer/README.md) lands here |

---

## Your response (JSON)

| Field | Required | Description |
|---|---|---|
| `STATUS` | ✅ | Must be `"OK"` (uppercase string). Anything else = error. |
| `URL` | ❌ | CRM page URL to open when the popup is clicked |
| `CLIENTNAME` | ❌ | Caller's name from CRM |
| `TOTAL` | ❌ | Number of CRM matches (`0` for unknown) |
| `COMPANY` | ❌ | Caller's company |

### Known caller

```json
{
  "STATUS": "OK",
  "URL": "https://yourcrm.com/contacts/12345",
  "CLIENTNAME": "John Doe",
  "TOTAL": 1,
  "COMPANY": "Acme Corp"
}
```

### Unknown caller

```json
{
  "STATUS": "OK",
  "URL": "https://yourcrm.com/contacts/new?phone=0722776772",
  "CLIENTNAME": "",
  "TOTAL": 0
}
```

---

## TypeScript implementation (Express)

```typescript
import express, { Request, Response } from 'express';

const app = express();
app.use(express.json());

// Required for the Voicenter Chrome Extension to call your endpoint
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

  // Voicenter sends 972XXXXXXXX, CRM may store 0XXXXXXXX
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
    return res.json({
      STATUS: 'OK',
      URL: `https://yourcrm.com/contacts/new?phone=${normalizedPhone}&ivrid=${payload.ivrid}`,
      TOTAL: 0,
    });
  }

  return res.json({ STATUS: 'OK' });
});

app.listen(3000);
```

---

## NGINX CORS

```nginx
location /webhooks/voicenter/popup {
  add_header 'Access-Control-Allow-Origin' 'chrome-extension://ifiaikfdhcagbagdeflffjdammidpbio';
  add_header 'Access-Control-Allow-Headers' 'Content-Type';
}
```

---

## Legacy GET format

```
https://yourcrm.com/popup?phone=0722776772&ivrid=20241001abc&extenUser=SIPSIP&did=0776707528&statusCall=Ringing
```

---

## Tips & best practices

- **Respond within 3 seconds** — slower replies skip the popup entirely.
- **Normalize the `phone` field** before CRM lookup. Voicenter sends with the country prefix; your CRM may store local format.
- **Handle all three phases** — Ringing opens the CRM, Talking can update it, Hangup can close/log.
- Use `ivrid` to link to the CDR delivered later via [CDR Notification](../cdr-notification/README.md).
- The **CORS header is mandatory** — the Voicenter Chrome Extension calls your endpoint from the browser.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Popup never appears | Chrome extension missing on agent's browser | Install from Chrome Web Store / corporate policy |
| Popup appears but URL is `chrome-extension://...` blocked by your CSP | Missing CORS header | Add `Access-Control-Allow-Origin` per the snippet |
| Phase missing (e.g. only Ringing fires) | URL not configured for both extension and DID | Configure on both surfaces in CPanel |
| Slow popup | Endpoint exceeds 3 s | Profile and offload heavy work async |

---

## Related skills

- [CDR Notification](../cdr-notification/README.md) — correlate by `ivrid` after the call ends
- [External Layer](../external-layer/README.md) — `CUSTOM_DATA` you set there appears here as `customdata`
- [Active Calls](../active-calls/README.md) — verify state if you need it
- [Mute Recording](../mute-recording/README.md) — `isMuted` reflects current recording state
