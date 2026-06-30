---
name: get-call-history
description: Pull specific call data by CallID with AI analysis — summary, emotions, personality traits, and insights. Does NOT include full transcription (CDR Notification only). Use for on-demand AI enrichment, CRM quality reviews, and retroactive summary retrieval via the two-step Call Log → GetCallHistory flow.
---

> **Language.** Reply in the user's language: detect what they write — Hebrew→Hebrew, English→English — and mirror it, switching if they switch mid-conversation. This shapes your prose, your questions, and your `AskUserQuestion` option labels only. It does **not** change the artifacts you produce — identifiers, JSON keys, BCP-47 language codes, API field names, and other data stay exactly as specified.

Help the developer retrieve **AI-enriched call data by CallID** — on-demand access to call summaries, emotion analysis, personality traits, and insights for a specific call.

## When to use this skill

Use this skill when the user wants to:

- Retrieve AI analysis (summary, emotions, personality, insights) for a specific call using its CallID
- Build a "View Analysis" button in a CRM after a call ends
- Enrich existing call records with AI data retroactively
- Run quality assurance reviews on specific calls with sentiment and personality data
- Retrieve all AI summaries for a phone number over a time range (two-step flow: Call Log → GetCallHistory)

> **Not the right skill if:** the user needs full transcription. Transcription is only available via **CDR Notification** (push/webhook). Redirect to the cdr-notification skill in that case.

## Environment Variables

```
VOICENTER_BEARER_TOKEN=vcToken_here
# Note: this API uses Bearer token auth — NOT the 'code' param used by other Voicenter APIs
# You need both VOICENTER_BEARER_TOKEN (for GetCallHistory) and VOICENTER_API_CODE (for Call Log)
# if you are implementing the two-step retroactive lookup flow.
```

## How it works

Send a GET request with the `CallID` in the URL path and a `Bearer` token in the `Authorization` header. The API returns the full call record plus all available AI analysis for that call — everything except the full transcription.

**Authentication differs from other Voicenter APIs:** most APIs use a `code` query parameter. GetCallHistory uses `Authorization: Bearer {token}`.

## Endpoint

```
GET https://api-manager.voicenter.co/api-manager-v1/Call/History/{CALLID}
```

Replace `{CALLID}` with the `ivruniqueid` or `CallID` value from the call.

## Headers

| Header | Value | Required |
|--------|-------|----------|
| `Accept` | `application/json` | ✅ |
| `Authorization` | `Bearer {token}` | ✅ |

## AI Data Returned

| Data | Included | Notes |
|------|----------|-------|
| Call Summary | ✅ | AI-generated text summary of the call |
| Emotion Analysis | ✅ | Per-sentence: emotion, direction, intensity, confidence |
| Personality Traits | ✅ | Speaker personality with confidence scores |
| Call Insights | ✅ | Key topics, issues, action items |
| **Full Transcription** | ❌ | Available only via CDR Notification |

## TypeScript Implementation

```typescript
const BASE_URL = 'https://api-manager.voicenter.co/api-manager-v1/Call/History';
const TOKEN = process.env.VOICENTER_BEARER_TOKEN!;

interface EmotionEntry {
  sentence_id: number;
  emotion: string;
  emotion_direction: number;  // -1 (negative) to 1 (positive)
  intensity_emotion: number;  // 0 (weak) to 1 (strong)
  confidence_emotion: number; // 0 to 1
}

interface PersonalityTrait {
  personality_trait: string;
  confidence_trait: number;
}

interface CallHistory {
  callID: string;
  direction: string;
  caller: string;
  target: string;
  duration: number;
  status: string;
  record: string;             // recording URL
  queuename: string;
  representative_name: string;
  summary?: string;
  emotions?: EmotionEntry[];
  personality_traits?: PersonalityTrait[];
  insights?: string;
}

async function getCallHistory(callID: string): Promise<CallHistory> {
  const res = await fetch(`${BASE_URL}/${encodeURIComponent(callID)}`, {
    headers: {
      'Accept': 'application/json',
      'Authorization': `Bearer ${TOKEN}`,
    },
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

// ── Two-step: retroactive AI summaries for a phone number ──────────────────

// Step 1 — get CallIDs from Call Log API (uses 'code', not Bearer token)
async function getCallIDs(
  code: string,
  phone: string,
  fromDate: string, // "YYYY-MM-DD HH:mm:ss" GMT+0
  toDate: string
): Promise<string[]> {
  const res = await fetch('https://api.voicenter.com/hub/cdr/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      code,
      fromdate: fromDate,
      todate: toDate,
      phones: [phone],
      fields: ['CallID', 'Date', 'Direction', 'Duration'],
    }),
  });
  if (!res.ok) throw new Error(`Call Log HTTP ${res.status}`);
  const data = await res.json();
  return (data.calls ?? []).map((c: { CallID: string }) => c.CallID);
}

// Step 2 — fetch AI analysis for each CallID
async function getAISummariesForPhone(
  code: string,
  phone: string,
  fromDate: string,
  toDate: string
): Promise<CallHistory[]> {
  const ids = await getCallIDs(code, phone, fromDate, toDate);
  return Promise.all(ids.map(id => getCallHistory(id)));
}

// Usage — single call
const history = await getCallHistory('20220518100502024636...');
console.log('Summary:', history.summary);
console.log('Top emotion:', history.emotions?.[0]?.emotion);

// Usage — all summaries for a number over a range
const summaries = await getAISummariesForPhone(
  process.env.VOICENTER_API_CODE!,
  '0501234567',
  '2026-06-01 00:00:00',
  '2026-06-30 23:59:59'
);
```

## Where to Get the CallID

| Source | Field name |
|--------|------------|
| CDR Notification (webhook) | `ivruniqueid` |
| Call Log API response | `CallID` |
| Real-Time Events SDK | `ivruniqueid` |
| Click2Call response | `CALLID` |

## Tips

- **Bearer token ≠ code param** — if you mix them up the request silently fails. GetCallHistory needs `Authorization: Bearer`, Call Log needs `code` in the body.
- **No transcription** — if the customer needs full transcription they must capture it from the CDR Notification webhook and store it themselves.
- **Retroactive by phone number requires two steps** — there is no single endpoint that returns AI summaries filtered by phone. Use Call Log first to get the CallIDs, then GetCallHistory per ID.
- Dates in the Call Log step are **GMT+0**, format `"YYYY-MM-DD HH:mm:ss"`.
- AI data is only present if AI processing is enabled on the Voicenter account.

## Related Skills

- **CDR Notification** — push webhook after each call; the only source for full transcription; also returns all AI data automatically
- **Call Log** — use as Step 1 to get CallIDs when doing retroactive phone-number lookups
- **Click2Call** — the `CALLID` in its response is the same ID passed here
- **Real-Time Events** — the `ivruniqueid` in real-time events is the same ID passed here
