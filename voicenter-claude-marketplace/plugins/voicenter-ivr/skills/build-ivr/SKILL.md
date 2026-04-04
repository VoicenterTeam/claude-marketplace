---
description: Design and manage IVR call flows via the Voicenter IVR API
---

Help the developer **create or modify an IVR flow** using the Voicenter IVR API — menu trees, routing rules, time conditions, and prompts.

## What to do

1. Ask what the IVR should do: simple menu, hours-based routing, language selection, or queue routing.
2. Design the flow structure with them.
3. Generate the API calls to create or update the IVR.

## List existing IVRs

**Endpoint:** `GET https://api.voicenter.com/v2/ivr`

Returns an array of IVR configurations with `ivrId`, `name`, and `did`.

## Get a specific IVR

**Endpoint:** `GET https://api.voicenter.com/v2/ivr/{ivrId}`

## Create / update an IVR

**Endpoint:** `POST https://api.voicenter.com/v2/ivr` (create) or `PUT https://api.voicenter.com/v2/ivr/{ivrId}` (update)

**IVR flow structure:**
```json
{
  "name": "Main Menu",
  "language": "en",
  "nodes": [
    {
      "id": "welcome",
      "type": "prompt",
      "text": "Welcome to Acme Corp. Press 1 for Sales, 2 for Support, or stay on the line.",
      "tts": true,
      "next": "main-menu"
    },
    {
      "id": "main-menu",
      "type": "menu",
      "timeout": 5,
      "options": {
        "1": { "action": "queue", "target": "q-sales" },
        "2": { "action": "queue", "target": "q-support" },
        "0": { "action": "transfer", "target": "1000" }
      },
      "onTimeout": { "action": "queue", "target": "q-support" }
    }
  ],
  "entryNode": "welcome"
}
```

## Node types

| Type | Description |
|---|---|
| `prompt` | Play a TTS or audio file message |
| `menu` | Wait for DTMF input and route accordingly |
| `queue` | Route to a call queue |
| `transfer` | Blind transfer to an extension or DID |
| `voicebot` | Hand off to an AI Voice Bot (see voicebot-config skill) |
| `hangup` | End the call with an optional message |
| `condition` | Branch based on time, caller ID, or custom data |

## Example — TypeScript

```typescript
async function createIvr(token: string, ivrConfig: object) {
  const res = await fetch('https://api.voicenter.com/v2/ivr', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(ivrConfig),
  });
  if (!res.ok) throw new Error(`IVR create failed: ${res.status} ${await res.text()}`);
  return res.json(); // { ivrId, name, status: "active" }
}
```

## Business hours condition example

```json
{
  "id": "hours-check",
  "type": "condition",
  "conditions": [
    {
      "type": "schedule",
      "timezone": "Asia/Jerusalem",
      "ranges": [
        { "days": ["mon","tue","wed","thu"], "from": "08:00", "to": "18:00" },
        { "days": ["fri"], "from": "08:00", "to": "14:00" }
      ],
      "match": { "action": "goto", "target": "welcome" },
      "noMatch": { "action": "prompt", "text": "We are currently closed. Goodbye.", "tts": true, "next": "hangup" }
    }
  ]
}
```

## Tips

- Test IVR changes in a staging DID before assigning to production.
- Use `tts: true` for quick iteration — switch to pre-recorded audio files before launch for best quality.
- Combine with the `voicenter-webhooks` plugin to track which menu options callers choose (`ivr.dtmf` event).
