# Skill: `external-layer`

Build an External Layer IVR endpoint that lets Voicenter route inbound calls based on your CRM business logic.

> Source: [`plugins/voicenter-api/skills/external-layer/SKILL.md`](../../../plugins/voicenter-api/skills/external-layer/SKILL.md)
> Plugin: [voicenter-api](../../plugins/voicenter-api.md) · Direction: **Incoming** · Transport: **Webhook (push)**

---

> **Language.** Reply in the user's language: detect what they write — Hebrew→Hebrew, English→English — and mirror it, switching if they switch mid-conversation. This shapes your prose, your questions, and your `AskUserQuestion` option labels only. It does **not** change the artifacts you produce — identifiers, JSON keys, BCP-47 language codes, API field names, and other data stay exactly as specified.

## When to use this skill

- Route VIP customers directly to their account manager, bypassing the queue
- Route callers with open support tickets directly to the assigned agent
- Show a custom greeting (SAY_DIGITS) using the caller's name from CRM
- Route by time of day, agent availability, or arbitrary business rules
- Pass CRM data (customer ID, tier, ticket info) downstream into Pop-Up and CDR
- Build smart IVR routing **without** reprogramming Voicenter IVR layers

---

## How it works

1. An inbound call reaches a Voicenter IVR layer with **"Allow Mini External IVR"** enabled.
2. Voicenter POSTs the call details to your endpoint.
3. Your server queries CRM/DB and replies with a **routing action**.
4. Voicenter executes the action immediately.

> **Hard timeout: 5 seconds.** If your server is slow or returns `STATUS: 1`, Voicenter falls back to the layer configured under `MiniExternalDefaultMethodData`.

CPanel path: **Incoming → IVR → select layer → Layer Settings → "Allow mini external IVR"**.

---

## Request Voicenter sends you

```json
{
  "METHOD": "IVR_LAYER_INPUT",
  "DATA": {
    "DID": "0722776772",
    "CALLER_ID": "0501234567",
    "IVR_UNIQUE_ID": "1bcd7954224861f85a2d70612f2",
    "DTMF": "1234",
    "LAYER_ID": "5",
    "PREVIOUS_LAYER_ID": "5"
  }
}
```

| Field | Description |
|---|---|
| `DID` | The DID the caller dialed |
| `CALLER_ID` | Caller's phone — use to look them up |
| `IVR_UNIQUE_ID` | Universal call ID |
| `DTMF` | Digits collected (default `"0"`) |
| `LAYER_ID` | Current layer ID |
| `PREVIOUS_LAYER_ID` | Previous layer ID |

---

## Response actions

### `GO_TO_LAYER` — route to a Voicenter IVR layer

```json
{ "STATUS": 0, "ACTION": "GO_TO_LAYER", "LAYER": 12 }
```

With CRM context attached (flows to Pop-Up and CDR):

```json
{
  "STATUS": 0,
  "ACTION": "GO_TO_LAYER",
  "LAYER": 22,
  "CALLER_NAME": "John Doe",
  "CUSTOM_DATA": {
    "CRM_client_ID": "12345",
    "Last_ticket_ID": "222",
    "Last_representative": "Jane Smith"
  }
}
```

### `SAY_DIGITS` — announce dynamic data, then route

```json
{
  "STATUS": 0,
  "ACTION": "SAY_DIGITS",
  "NEXT_LAYER": 2,
  "LANGUAGE": "EN",
  "DATA": [
    { "RecordType": "Recording", "Content": "greeting_audio_file.mp3" },
    { "RecordType": "Digits",   "Content": "0501234567" },
    { "RecordType": "Number",   "Content": "42" },
    { "RecordType": "Date",     "Content": "2024-06-01" },
    { "RecordType": "DateTime", "Content": "2024-06-01T10:00:00" }
  ]
}
```

`LANGUAGE`: `HE`, `EN`, `AR`, `RU` (others on request).
`RecordType`: `Recording`, `Digits`, `Number`, `Date`, `DateTime`.

### `DIAL` — call an external phone or extension directly

```json
{
  "STATUS": 0,
  "ACTION": "DIAL",
  "CALLER_ID": "0722776772",
  "CALLER_NAME": "Voicenter",
  "MAX_CALL_DURATION": 1800,
  "MAX_DIAL_DURATION": 60,
  "NEXT_VO_ID": 15,
  "RECORDING": "yes",
  "TARGETS": [{ "TYPE": "PHONE", "TARGET": "0501234567" }],
  "CUSTOM_DATA": { "CRM_client_ID": "12345" }
}
```

`TARGET TYPE`: `PHONE` or `EXTENSION` (Voicenter SIP code). International numbers require the country prefix.

### Error response — triggers configured fallback layer

```json
{ "STATUS": 1 }
```

---

## TypeScript implementation (Express)

```typescript
import express, { Request, Response } from 'express';

const app = express();
app.use(express.json());

const LAYERS = { SALES: 10, SUPPORT: 11, VIP: 12, GENERIC: 1 };

interface ExternalLayerRequest {
  METHOD: string;
  DATA: {
    DID: string;
    CALLER_ID: string;
    IVR_UNIQUE_ID: string;
    DTMF: string;
    LAYER_ID: string;
    PREVIOUS_LAYER_ID: string;
  };
}

app.post('/webhooks/voicenter/external-layer', async (req: Request, res: Response) => {
  const { DATA } = req.body as ExternalLayerRequest;

  try {
    const contact = await crm.findByPhone(DATA.CALLER_ID);

    if (!contact) {
      return res.json({ STATUS: 0, ACTION: 'GO_TO_LAYER', LAYER: LAYERS.GENERIC });
    }

    if (contact.tier === 'VIP') {
      return res.json({
        STATUS: 0,
        ACTION: 'GO_TO_LAYER',
        LAYER: LAYERS.VIP,
        CALLER_NAME: contact.name,
        CUSTOM_DATA: { CRM_client_ID: contact.id, Account_manager: contact.accountManager },
      });
    }

    if (contact.openTicket?.assignedExtension) {
      return res.json({
        STATUS: 0,
        ACTION: 'DIAL',
        CALLER_ID: DATA.DID,
        CALLER_NAME: contact.name,
        MAX_CALL_DURATION: 1800,
        MAX_DIAL_DURATION: 45,
        NEXT_VO_ID: LAYERS.SUPPORT,
        RECORDING: 'yes',
        TARGETS: [{ TYPE: 'EXTENSION', TARGET: contact.openTicket.assignedExtension }],
        CUSTOM_DATA: { CRM_client_ID: contact.id, Ticket_ID: contact.openTicket.id },
      });
    }

    return res.json({
      STATUS: 0,
      ACTION: 'GO_TO_LAYER',
      LAYER: LAYERS.SUPPORT,
      CALLER_NAME: contact.name,
      CUSTOM_DATA: { CRM_client_ID: contact.id },
    });

  } catch (err) {
    console.error('External layer error:', err);
    return res.json({ STATUS: 1 });
  }
});

app.listen(3000);
```

---

## CPanel configuration

| Setting | Description |
|---|---|
| **MiniExternalDTMFLen** | Max DTMF digits to collect before calling your endpoint (e.g. `8` for an 8-digit account ID). `0` = no DTMF. |
| **Delay** | Seconds to wait for DTMF input after the prompt plays (1–9) |
| **MiniExternalDefaultMethodData** | **Fallback layer ID** — used when your endpoint times out or returns `STATUS: 1`. **Always set this.** |

---

## Tips & best practices

- **Respond within 5 seconds** or Voicenter falls back. Aim for < 1 second.
- **Normalize `CALLER_ID`** — Israeli numbers may arrive without country prefix. Add `972` and strip leading `0` for CRM lookup.
- **Use `CUSTOM_DATA`** to carry CRM context through the entire call. It appears in the Pop-Up Screen, VoiceBot, and CDR Notification payloads.
- **Multiplex on `LAYER_ID`** — multiple layers can share one endpoint. Switch logic based on `DATA.LAYER_ID`.
- **Always set the CPanel fallback** — your endpoint will go down eventually.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Calls always go to fallback layer | Your endpoint > 5s, or wrong CPanel URL | Profile latency; verify URL |
| `CUSTOM_DATA` not visible in Pop-Up | Pop-Up reads `customdata` (lowercase) inside `currentCall` | The mapping is automatic — check spelling |
| 5xx in your logs from Voicenter UA | Endpoint is down | Add health checks; load test |
| Wrong routing | Misuse of `LAYER_ID` vs `PREVIOUS_LAYER_ID` | Use `LAYER_ID` for current routing key |

---

## Related skills

- [Pop-Up Screen](../popup-screen/README.md) — receives `CUSTOM_DATA` you pass here
- [CDR Notification](../cdr-notification/README.md) — `CUSTOM_DATA` also lands here, after the call ends
- [VoiceBot](../voicebot/README.md) — runs mid-conversation; External Layer runs at call start
- [Active Calls](../active-calls/README.md) — check queue depth before deciding where to route
