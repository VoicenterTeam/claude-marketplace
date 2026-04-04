---
description: Configure and manage AI Voice Bots via the Voicenter API
---

Help the developer **create, update, or connect an AI Voice Bot** to an IVR flow using the Voicenter API.

## What to do

1. Ask about the bot's purpose: FAQ answering, appointment booking, lead qualification, or custom flow.
2. Help design the bot's persona, language, and intents.
3. Generate the API calls to create the bot and link it to an IVR node.

## Create a Voice Bot

**Endpoint:** `POST https://api.voicenter.com/v2/voicebots`

```json
{
  "name": "Support Bot",
  "language": "en",
  "persona": "You are a helpful support assistant for Acme Corp. Keep responses under 20 words.",
  "fallbackExtension": "1000",
  "maxTurns": 6,
  "intents": [
    {
      "name": "transfer_to_human",
      "phrases": ["agent", "human", "speak to someone", "representative"],
      "action": { "type": "transfer", "target": "q-support" }
    },
    {
      "name": "get_hours",
      "phrases": ["hours", "when are you open", "opening times"],
      "action": { "type": "tts", "text": "We are open Sunday to Thursday 8am to 6pm." }
    }
  ]
}
```

**Response:** `{ "botId": "bot-uuid", "name": "Support Bot", "status": "active" }`

## Link a bot to an IVR node

In your IVR flow, use a `voicebot` node:

```json
{
  "id": "ai-support",
  "type": "voicebot",
  "botId": "bot-uuid",
  "onEscalate": { "action": "queue", "target": "q-support" },
  "onComplete": { "action": "hangup" }
}
```

## Update a bot

**Endpoint:** `PATCH https://api.voicenter.com/v2/voicebots/{botId}`

Send only the fields to update:
```json
{ "persona": "Updated persona text", "maxTurns": 8 }
```

## Example — TypeScript

```typescript
interface VoiceBotPayload {
  name: string;
  language: string;
  persona: string;
  fallbackExtension: string;
  maxTurns?: number;
  intents?: object[];
}

async function createVoiceBot(token: string, payload: VoiceBotPayload) {
  const res = await fetch('https://api.voicenter.com/v2/voicebots', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(`VoiceBot create failed: ${res.status}`);
  return res.json();
}
```

## Bot design best practices

- **Keep the persona concise** — 1–2 sentences. The bot uses it as a system prompt.
- **Define a `fallbackExtension`** — always give callers an escape to a human agent.
- **Set `maxTurns`** — prevents infinite loops; after the limit the call escalates.
- **Use the `transfer_to_human` intent** with common escalation phrases as a safety net.
- **Listen to `voicebot.session` webhooks** (via `voicenter-webhooks`) to log conversation transcripts for quality review.
