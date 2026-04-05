---
description: Build an External Layer IVR endpoint that lets Voicenter route inbound calls based on your CRM business logic
---

Help the developer implement an **External Layer** endpoint — a URL that Voicenter's IVR calls mid-flow, so the developer's server can decide where to route each incoming call dynamically based on CRM data.

## When to use this skill

Use this skill when the user wants to:
- Route VIP customers directly to their account manager, bypassing the general queue
- Route callers with open support tickets directly to the assigned agent
- Show a custom greeting (SAY_DIGITS) using the caller's name fetched from CRM
- Route calls differently based on time of day, agent availability, or business rules in their system
- Pass CRM data (customer ID, tier, open ticket) into the call for use by Pop-Up Screen and CDR Notification
- Build smart IVR routing without reprogramming the Voicenter IVR layers

## Environment Variables

```env
# No outbound API token needed — Voicenter sends requests TO your server.
# Configure your endpoint URL in: Voicenter CPanel → Incoming → IVR → select layer → Layer Settings → "Allow mini external IVR"
```

## How it works

1. An inbound call reaches a Voicenter IVR layer configured with "Allow Mini External IVR" and your endpoint URL.
2. Voicenter POSTs the call details (caller ID, DTMF input, layer info) to your endpoint.
3. Your server queries its CRM/database and responds with a routing action.
4. Voicenter executes the action immediately.

**Critical:** Respond within **5 seconds** or Voicenter times out and uses the configured fallback layer.

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
| `IVR_UNIQUE_ID` | Unique call ID — correlates with CDR Notification and Pop-Up Screen |
| `DTMF` | Digits the caller pressed. Default `"0"` if no input collected. |
| `LAYER_ID` | Current IVR layer ID |
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

With CRM context (appears in Pop-Up Screen and CDR Notification):

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

`LANGUAGE` options: `HE`, `EN`, `AR`, `RU` (more available on request).
`RecordType` options: `Recording` (play audio file), `Digits` (digit-by-digit), `Number`, `Date`, `DateTime`.

### DIAL — Call an external phone number or extension directly

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

### Error Response — triggers configured fallback layer

```json
{ "STATUS": 1 }
```

## TypeScript Implementation (Express)

```typescript
import express, { Request, Response } from 'express';

const app = express();
app.use(express.json());

// Map your Voicenter IVR layer IDs here
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
    const contact = await crm.findByPhone(DATA.CALLER_ID);

    if (!contact) {
      // Unknown caller → generic queue
      return res.json({ STATUS: 0, ACTION: 'GO_TO_LAYER', LAYER: LAYERS.GENERIC });
    }

    // VIP → skip queue, route directly to account manager
    if (contact.tier === 'VIP') {
      return res.json({
        STATUS: 0,
        ACTION: 'GO_TO_LAYER',
        LAYER: LAYERS.VIP,
        CALLER_NAME: contact.name,
        CUSTOM_DATA: {
          CRM_client_ID: contact.id,
          Account_manager: contact.accountManager,
        },
      });
    }

    // Has open ticket with assigned agent → dial directly
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

    // Known contact → support queue with CRM context
    return res.json({
      STATUS: 0,
      ACTION: 'GO_TO_LAYER',
      LAYER: LAYERS.SUPPORT,
      CALLER_NAME: contact.name,
      CUSTOM_DATA: { CRM_client_ID: contact.id },
    });

  } catch (err) {
    console.error('External layer error:', err);
    return res.json({ STATUS: 1 }); // Voicenter uses configured fallback layer
  }
});

app.listen(3000);
```

## CPanel Configuration

| Setting | Description |
|---|---|
| **MiniExternalDTMFLen** | Max DTMF digits to collect before calling your endpoint (e.g. `8` for an 8-digit account ID). Set to `0` if no DTMF needed. |
| **Delay** | Seconds to wait for DTMF input after the prompt plays (1–9). |
| **MiniExternalDefaultMethodData** | **Fallback layer ID** — always set this. It is used when your endpoint is unreachable or returns `STATUS: 1`. |

## Tips

- **Respond within 5 seconds** or Voicenter times out and uses the fallback layer.
- **Normalize `CALLER_ID`** — Israeli numbers may arrive without country prefix. Add `972` prefix if missing and strip the leading `0`.
- **Use `CUSTOM_DATA`** to carry CRM context (customer ID, tier, open ticket ID) through the entire call — it appears in CDR Notification and Pop-Up Screen payloads.
- For DTMF-driven flows ("press 1 for Sales"), read `DATA.DTMF` and map it to the appropriate layer.

## Related Skills

- **Pop-Up Screen** — Receives `CUSTOM_DATA` you pass here to display caller info to the agent
- **CDR Notification** — `CUSTOM_DATA` also appears in the CDR after the call ends
- **VoiceBot API** — Combine with External Layer: External Layer runs at call start, VoiceBot runs mid-conversation
- **Active Calls** — Check queue depth before routing to decide between queues
