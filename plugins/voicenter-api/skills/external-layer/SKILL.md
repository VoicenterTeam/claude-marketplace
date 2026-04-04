---
description: Build an External Layer IVR endpoint that lets Voicenter route inbound calls based on your CRM business logic
---

Help the developer implement an **External Layer** endpoint — a URL that Voicenter's IVR calls mid-flow, so the developer's CRM can decide where to route each incoming call dynamically.

## How it works

1. An inbound call reaches a Voicenter IVR layer configured with "Allow Mini External IVR" and your endpoint URL.
2. Voicenter POSTs the call details (caller ID, DTMF input, layer info) to your endpoint.
3. Your server queries its CRM/database and responds with a routing action: go to a layer, say something, or dial a number.
4. Voicenter executes the action.

Configure the endpoint in Voicenter CPanel → **Incoming** → **IVR** → select a layer → **Layer Settings** → enable "Allow mini external IVR" → set your URL.

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
| `DID` | The virtual number (DID) the caller dialed |
| `CALLER_ID` | Caller's phone number — use this to look them up in your CRM |
| `IVR_UNIQUE_ID` | Unique call ID |
| `DTMF` | Digits the caller pressed (default `"0"` if none pressed) |
| `LAYER_ID` | Current IVR layer ID this request is sent from |
| `PREVIOUS_LAYER_ID` | Previous IVR layer ID |

## Response Actions

### GO_TO_LAYER — Route to a Voicenter IVR layer

```json
{
  "STATUS": 0,
  "ACTION": "GO_TO_LAYER",
  "LAYER": 12
}
```

With optional caller name and CRM data (shown in Pop-Up and CDR):

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

### SAY_DIGITS — Announce dynamic data then route

```json
{
  "STATUS": 0,
  "ACTION": "SAY_DIGITS",
  "NEXT_LAYER": 2,
  "LANGUAGE": "EN",
  "DATA": [
    { "RecordType": "Recording", "Content": "greeting_audio_file.mp3" },
    { "RecordType": "Digits", "Content": "0501234567" },
    { "RecordType": "Number", "Content": "42" },
    { "RecordType": "Date", "Content": "2024-06-01" },
    { "RecordType": "DateTime", "Content": "2024-06-01T10:00:00" }
  ]
}
```

`LANGUAGE` options: `HE`, `EN`, `AR`, `RU` (more on request).
`RecordType` options: `Recording` (play audio file), `Digits` (digit-by-digit), `Number`, `Date`, `DateTime`.

### DIAL — Call an external phone or extension

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
  "TARGETS": [
    { "TYPE": "PHONE", "TARGET": "0501234567" }
  ],
  "CUSTOM_DATA": {
    "CRM_client_ID": "12345"
  }
}
```

`TARGET TYPE`: `PHONE` or `EXTENSION` (Voicenter SIP code). International numbers require country prefix.

### Error response

```json
{ "STATUS": 1 }
```

Send `STATUS: 1` when an error occurs. Voicenter will use the configured fallback layer.

## TypeScript Implementation (Express)

```typescript
import express, { Request, Response } from 'express';

const app = express();
app.use(express.json());

// Map of IVR layers — define these based on your Voicenter IVR setup
const LAYERS = {
  SALES: 10,
  SUPPORT: 11,
  VIP: 12,
  GENERIC: 1,
};

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
    // Look up caller in CRM
    const contact = await crm.findByPhone(DATA.CALLER_ID);

    if (!contact) {
      // Unknown caller → generic queue
      return res.json({ STATUS: 0, ACTION: 'GO_TO_LAYER', LAYER: LAYERS.GENERIC });
    }

    // VIP client → skip queue, route directly to account manager
    if (contact.tier === 'VIP') {
      return res.json({
        STATUS: 0,
        ACTION: 'GO_TO_LAYER',
        LAYER: LAYERS.VIP,
        CALLER_NAME: contact.name,
        CUSTOM_DATA: { CRM_client_ID: contact.id, Account_manager: contact.accountManager },
      });
    }

    // Existing client with open ticket → route to assigned agent via DIAL
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

    // Existing client → support queue
    return res.json({
      STATUS: 0,
      ACTION: 'GO_TO_LAYER',
      LAYER: LAYERS.SUPPORT,
      CALLER_NAME: contact.name,
      CUSTOM_DATA: { CRM_client_ID: contact.id },
    });

  } catch (err) {
    console.error('External layer error:', err);
    return res.json({ STATUS: 1 }); // Trigger Voicenter fallback layer
  }
});

app.listen(3000);
```

## CPanel Configuration Tips

- **MiniExternalDTMFLen** — Max DTMF digits to wait for (e.g., `8` for an 8-digit ID). Set to `0` if no DTMF input is needed.
- **Delay** — Seconds to wait for DTMF after the prompt plays (1–9). Set appropriately for the prompt length.
- **MiniExternalDefaultMethodData** — Fallback layer ID if your endpoint is unreachable. Always set this to prevent calls being dropped.

## Tips

- **Respond within 5 seconds** or Voicenter will time out and use the fallback layer.
- **Normalize phone numbers** — `CALLER_ID` may come without country prefix for Israeli numbers.
- Use `CUSTOM_DATA` to pass CRM context into CDR Notification and Pop-Up Screen later in the call.
- For DTMF-driven flows (e.g., "press 1 for Sales"), read `DATA.DTMF` and route accordingly.
