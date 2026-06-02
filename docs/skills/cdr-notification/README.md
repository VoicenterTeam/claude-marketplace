# Skill: `cdr-notification`

Receive and handle CDR push notifications from Voicenter after every call ends.

> Source: [`plugins/voicenter-api/skills/cdr-notification/SKILL.md`](../../../plugins/voicenter-api/skills/cdr-notification/SKILL.md)
> Plugin: [voicenter-api](../../plugins/voicenter-api.md) · Direction: **In/Out** · Transport: **Webhook (push)**

---

> **Language.** Reply in the user's language: detect what they write — Hebrew→Hebrew, English→English — and mirror it, switching if they switch mid-conversation. This shapes your prose, your questions, and your `AskUserQuestion` option labels only. It does **not** change the artifacts you produce — identifiers, JSON keys, BCP-47 language codes, API field names, and other data stay exactly as specified.

## When to use this skill

- Save call records to your database automatically after every call
- Trigger follow-up actions when a call ends (SMS, CRM update, ticket)
- React to missed/abandoned calls in real time
- Process AI call analysis (transcripts, emotions, summaries, Q&A)
- Build a real-time call activity feed
- Sync call history with BI / reporting

---

## How it works

1. A call ends in your Voicenter account.
2. Voicenter POSTs the CDR as JSON to your configured endpoint URL.
3. Your server responds **immediately** with `{"Err": 0, "Errdesc": "OK"}`.
4. Process the CDR asynchronously after responding.

Configure your endpoint URL in: **CPanel → Integrations → CDR Notification**.

There is no inbound auth header — the URL itself is the secret. Use HTTPS only.

---

## CDR request fields

| Field | Description |
|---|---|
| `direction` | `incoming` / `outgoing` / `internal` |
| `extenUser` | Agent's SIP code (empty if call never reached an agent) |
| `callerPhone` | Client's caller ID |
| `isAnswer` | `1` answered, `0` not |
| `actualCallDuration` | Talk time in seconds (no ringing) |
| `actualCallDialtime` | Ringing duration in seconds |
| `caller` | Phone shown to destination |
| `target` | Call destination (phone or SIP) |
| `time` | Call start time, Epoch, **account local timezone** |
| `duration` | Total call duration (queue calls include wait) |
| `ivruniqueid` | **Universal call ID** |
| `type` | Call type (see table below) |
| `status` | `ANSWER` / `ABANDONE` / `NOANSWER` / `CANCEL` / `BUSY` / `TE` / etc. |
| `did` | DID dialed (incoming only) |
| `queueid` / `queuename` | Queue, if any |
| `record` | URL to recording MP3 |
| `price` | Call cost in ILS Agorot |
| `dialtime` | Ringing duration |
| `representative_name` / `representative_code` | Agent identity |
| `target_country` / `caller_country` | Country names |
| `seconds_waiting_in_queue` | Queue wait, queue calls only |
| `OriginalIvrUniqueID` | Original ID for transferred calls |
| `DepartmentName` / `DepartmentID` | Account/department |
| `IVR` | Layers traversed (id, name, DTMF) |
| `aiData` | AI analysis (only if enabled) |
| `CustomData` | All `var_*` and `CUSTOM_DATA` fields gathered during the call |

### Call types

| Type | Description |
|---|---|
| `Incoming Call` | Inbound, ended in IVR / extension |
| `Queue` | Inbound through a queue |
| `Extension Outgoing` | Manual outgoing |
| `Click2Call leg1` / `Click2Call leg2` | C2C legs (Leg2 has the recording) |
| `ProductiveCall Leg1` / `Leg2` | Auto-dialer calls |
| `Click 2 IVR` / `Click 2 IVR Incoming` | Predictive dialer |
| `XferCDR` | Manually transferred |
| `VoiceMail` | Hit voicemail |

### Statuses

`ANSWER`, `NOANSWER`, `BUSY`, `CANCEL`, `ABANDONE`, `TIMEOUT`, `FULL`, `EXIT`, `JOINEMPTY`, `VOEND`, `TE`, `NOTCALLED`, `VOICEMAIL`

---

## Example: outgoing call

```json
{
  "caller": "0722776772",
  "target": "0501234567",
  "time": 1595960350,
  "duration": 11,
  "ivruniqueid": "2020072818dcDHFJcc804",
  "type": "Extension Outgoing",
  "status": "ANSWER",
  "callerextension": "SIPSIP",
  "did": "",
  "record": "https://cpanel.voicenter.co.il/CallsHistory/PlayRecord/2020072818dcDHFJcc804-aws.mp3",
  "price": 0,
  "dialtime": 2,
  "representative_name": "John Doe",
  "representative_code": "12345678",
  "DepartmentID": 12345678,
  "DepartmentName": "Voicenter Sales"
}
```

## Example: incoming queue call

```json
{
  "caller": "0501234567",
  "time": 1595333610,
  "duration": 20,
  "ivruniqueid": "202007211213270124c",
  "type": "Queue",
  "status": "ANSWER",
  "did": "0722776772",
  "queueid": 123456789,
  "queuename": "Sales Queue",
  "record": "https://cpanel.voicenter.co.il/CallsHistory/PlayRecord/202007211213270124c-aws.mp3",
  "seconds_waiting_in_queue": 20,
  "IVR": [
    { "layer_id": 1234, "layer_name": "Main IVR", "Dtmf": 2, "dtmf_order": 1 },
    { "layer_id": 4321, "layer_name": "Sales Department", "Dtmf": 0, "dtmf_order": 2 }
  ]
}
```

---

## AI Data (`aiData`)

Delivered when AI analysis is enabled on the account. AI data is **only available via this webhook** — the [Call Log](../call-log/README.md) API does not return it.

```json
{
  "aiData": {
    "insights": {
      "questions": [
        { "key": "category", "answer": "technical issue", "data_type": "string" },
        { "key": "issue_resolved", "answer": "false", "data_type": "boolean" }
      ],
      "participants": {
        "caller": { "name": null, "personality_traits": [] },
        "callee": { "name": "Steve", "personality_traits": ["professional", "patient"] }
      },
      "summary": "The caller reported dropped calls. The agent ran through troubleshooting..."
    },
    "emotions": {
      "sentences": [
        { "sentence_id": 21, "emotion": "frustrated", "emotion_direction": -1, "confidence_emotion": 0.92 }
      ]
    },
    "transcript": [
      { "speaker": "Speaker0", "text": "Good afternoon, support.", "startTime": 1.87, "endTime": 5.2 },
      { "speaker": "Speaker1", "text": "I'm having issues with my phone service.", "startTime": 13.46 }
    ]
  }
}
```

- `Speaker0` = agent (callee), `Speaker1` = customer (caller)
- `emotion_direction`: `1` positive, `-1` negative, `0` neutral
- `data_type`: `1`=boolean, `2`=string, `3`=number, `4`=json array, `5`=json object list, `6`=json object

---

## Required response

```json
{ "Err": 0, "Errdesc": "OK" }
```

| Err | Meaning |
|---|---|
| 0 | OK |
| 1 | Parse error |
| 2 | Application error |

> Always reply quickly. Voicenter does not stream — it waits for your `200`. Heavy work belongs in a background job.

---

## TypeScript implementation (Express)

```typescript
import express, { Request, Response } from 'express';

const app = express();
app.use(express.json());

interface CdrPayload {
  ivruniqueid: string;
  caller: string;
  target: string;
  type: string;
  status: string;
  duration: number;
  actualCallDuration: number;
  record: string;
  representative_name: string;
  representative_code: string;
  did: string;
  queuename: string;
  seconds_waiting_in_queue?: number;
  IVR?: Array<{ layer_id: number; layer_name: string; Dtmf: number }>;
  aiData?: {
    insights?: { summary: string; questions: Array<{ key: string; answer: unknown }> };
    transcript?: Array<{ speaker: string; text: string; startTime: number }>;
    emotions?: { sentences: Array<{ emotion: string; emotion_direction: number }> };
  };
  CustomData?: Record<string, unknown>;
}

app.post('/webhooks/voicenter/cdr', async (req: Request, res: Response) => {
  const cdr = req.body as CdrPayload;

  // 1. Acknowledge immediately
  res.json({ Err: 0, Errdesc: 'OK' });

  // 2. Process asynchronously
  setImmediate(async () => {
    try {
      const exists = await db.calls.findOne({ callId: cdr.ivruniqueid });
      if (exists) return;
      await db.calls.create({ callId: cdr.ivruniqueid, ...cdr });

      if (cdr.status === 'ABANDONE' && cdr.queuename) {
        await sendSms(cdr.caller, "We missed your call. We'll call you back shortly.");
      }

      if (cdr.aiData?.insights?.summary) {
        await db.callInsights.create({
          callId: cdr.ivruniqueid,
          summary: cdr.aiData.insights.summary,
          questions: cdr.aiData.insights.questions,
          transcript: cdr.aiData.transcript,
        });
      }
    } catch (err) {
      console.error('CDR processing failed:', err);
    }
  });
});

app.listen(3000);
```

---

## Tips & best practices

- **Reply immediately**, then process — `setImmediate`, a queue, or a worker.
- **Idempotency** — Voicenter retries on transient failure. Treat `ivruniqueid` as a unique key.
- **Recording URL** — direct MP3, store in CRM for playback.
- **Queue abandons** — `status: ABANDONE` + `queuename` set = caller hung up while waiting. Send a callback offer.
- **Phone normalization** — `caller` may arrive in various formats. Normalize before CRM lookup.
- **Custom data flow** — `CustomData` aggregates `var_*` from Click2Call, `CUSTOM_DATA` from External Layer, and Productive Dialer custom data.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Webhook never fires | URL not configured in CPanel | Set under Integrations → CDR Notification |
| Voicenter retries the same CDR | Your endpoint took > a few seconds or returned non-200 | Reply `{"Err":0,"Errdesc":"OK"}` first, then process |
| Duplicate rows in DB | No idempotency check | Treat `ivruniqueid` as unique key |
| `aiData` missing | AI not enabled on the account | Contact Voicenter to enable |
| 5xx in your logs from Voicenter user agent | Your endpoint is down | Add health checks; load test |

---

## Related skills

- [Call Log](../call-log/README.md) — query historical CDRs (no `aiData`)
- [Pop-Up Screen](../popup-screen/README.md) — uses `ivrid` to correlate with the ringing-phase popup
- [Real-Time](../real-time/README.md) — receive call events live (before the call ends)
- [Blacklist](../blacklist/README.md) — auto-blacklist on opt-out DTMF detected here
