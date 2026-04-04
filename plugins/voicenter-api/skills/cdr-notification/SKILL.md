---
description: Receive and handle CDR push notifications from Voicenter after every call ends
---

Help the developer implement a **CDR Notification** endpoint — a webhook that Voicenter POSTs to after every call ends, containing full call detail records including AI analysis.

## How it works

1. A call ends in your Voicenter account.
2. Voicenter converts the call data into a CDR and POSTs it as JSON/XML/form-encoded to your configured endpoint.
3. Your server processes the CDR and responds with `{"Err": 0, "Errdesc": "OK"}`.

Configure your endpoint URL in the Voicenter CPanel under **Integrations → CDR Notification**.

## CDR Request Fields

| Field | Description |
|---|---|
| `direction` | `incoming` / `outgoing` / `internal` |
| `extenUser` | Agent's SIP extension code (empty if call never reached an agent) |
| `callerPhone` | Client's caller ID |
| `isAnswer` | `1` = answered, `0` = not answered |
| `actualCallDuration` | Talk time in seconds (excludes ringing) |
| `actualCallDialtime` | Ringing duration in seconds |
| `caller` | Phone number shown to destination |
| `target` | Call destination (phone or SIP) |
| `time` | Call start time (Epoch, Israel timezone) |
| `duration` | Total call duration in seconds (for queue calls includes wait time) |
| `ivruniqueid` | **Unique call ID** — use to correlate with Pop-Up, Call Log, Real-Time |
| `type` | Call type (see table below) |
| `status` | Call status: `ANSWER`, `ABANDONE`, `NOANSWER`, `CANCEL`, `BUSY`, `TE`, etc. |
| `did` | DID (virtual number) dialed — only on incoming calls |
| `queueid` / `queuename` | Queue details (if call went through a queue) |
| `record` | URL to the call recording MP3 |
| `price` | Call cost in ILS cents (Agorot) |
| `dialtime` | Ringing duration in seconds |
| `representative_name` | Agent's display name |
| `representative_code` | Agent's user ID |
| `target_country` / `caller_country` | Country names |
| `seconds_waiting_in_queue` | Queue wait time in seconds (queue calls only) |
| `OriginalIvrUniqueID` | Original call ID (for transferred calls) |
| `DepartmentName` / `DepartmentID` | Account/department info |
| `IVR` | Array of IVR layers the call traversed (layer ID, name, DTMF pressed) |
| `aiData` | Full AI analysis (see below — only if AI is enabled on your account) |

### Call Types

| Type Name | Description |
|---|---|
| `Incoming Call` | Inbound call that ended in IVR or extension (not a queue) |
| `Queue` | Inbound call received by a queue |
| `Extension Outgoing` | Manual outgoing call from extension |
| `Click2Call leg1` | Click2Call — Leg 1 (connection to agent) |
| `Click2Call leg2` | Click2Call — Leg 2 (connection to customer, has recording) |
| `ProductiveCall Leg1/Leg2` | Agent Auto Dialer calls |
| `Click 2 IVR` / `Click 2 IVR Incoming` | Predictive Dialer calls |
| `XferCDR` | Manually transferred call |
| `VoiceMail` | Call answered by voicemail |

### Call Statuses

`ANSWER`, `NOANSWER`, `BUSY`, `CANCEL`, `ABANDONE`, `TIMEOUT`, `FULL`, `EXIT`, `JOINEMPTY`, `VOEND`, `TE`, `NOTCALLED`, `VOICEMAIL`

## Full JSON Example (Outgoing Call)

```json
{
  "caller": "0722776772",
  "target": "0501234567",
  "time": 1595960350,
  "duration": 11,
  "ivruniqueid": "2020072818dcDHFJcc804",
  "type": "Extension Outgoing",
  "status": "ANSWER",
  "targetextension": "",
  "callerextension": "SIPSIP",
  "did": "",
  "queueid": 0,
  "queuename": "",
  "record": "https://cpanel.voicenter.co.il/CallsHistory/PlayRecord/2020072818dcDHFJcc804-aws.mp3",
  "price": 0,
  "dialtime": 2,
  "representative_name": "John Doe",
  "representative_code": "12345678",
  "DepartmentID": 12345678,
  "DepartmentName": "Voicenter Sales"
}
```

## Full JSON Example (Incoming Queue Call)

```json
{
  "caller": "0501234567",
  "target": "",
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
    { "layer_id": 1234, "layer_name": "Main IVR", "layer_number": 0, "Dtmf": 2, "dtmf_order": 1 },
    { "layer_id": 4321, "layer_name": "Sales Department", "layer_number": 2, "Dtmf": 0, "dtmf_order": 2 }
  ]
}
```

## AI Data (if enabled)

When AI analysis is enabled on the account, `aiData` contains:

```json
{
  "aiData": {
    "insights": {
      "questions": [
        { "key": "category", "question": "Categorize the call...", "data_type": "string", "answer": "technical issue" },
        { "key": "issue_resolved", "question": "Was the issue resolved?", "data_type": "boolean", "answer": "false" }
      ],
      "participants": {
        "caller": { "name": null, "personality_traits": [] },
        "callee": { "name": "Steve", "personality_traits": ["professional", "patient"] }
      },
      "summary": "The caller reported dropped calls. The agent ran through troubleshooting steps..."
    },
    "emotions": {
      "sentences": [
        { "sentence_id": 21, "emotion": "frustrated", "emotion_direction": -1, "confidence_emotion": 0.92, "intensity_emotion": 0.85, "personality_trait": "impatient", "confidence_trait": 0.9 },
        { "sentence_id": 34, "emotion": "professional", "emotion_direction": 1, "confidence_emotion": 0.92, "intensity_emotion": 0.85, "personality_trait": "helpful", "confidence_trait": 0.88 }
      ]
    },
    "transcript": [
      { "speaker": "Speaker0", "text": "Good afternoon, thank you for calling support", "startTime": 1.87, "endTime": 5.2, "sentence_id": 0 },
      { "speaker": "Speaker1", "text": "Hi, I'm having issues with my phone service", "startTime": 13.46, "endTime": 16.6, "sentence_id": 1 }
    ]
  }
}
```

- `Speaker0` = agent (callee), `Speaker1` = customer (caller)
- `emotion_direction`: `1` = positive, `-1` = negative, `0` = neutral

## TypeScript Implementation (Express)

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
  record: string;
  representative_name: string;
  did: string;
  queuename: string;
  aiData?: {
    insights?: { summary: string; questions: Array<{ key: string; answer: unknown }> };
    transcript?: Array<{ speaker: string; text: string; startTime: number }>;
  };
}

app.post('/webhooks/voicenter/cdr', async (req: Request, res: Response) => {
  const cdr = req.body as CdrPayload;

  // 1. Acknowledge immediately — Voicenter needs a response
  res.json({ Err: 0, Errdesc: 'OK' });

  // 2. Process asynchronously
  setImmediate(async () => {
    try {
      // Save CDR to database
      await db.calls.upsert({ callId: cdr.ivruniqueid, ...cdr });

      // If call was abandoned in queue — trigger follow-up
      if (cdr.status === 'ABANDONE' && cdr.queuename) {
        await sendFollowUpSms(cdr.caller, 'We missed your call. We will call you back shortly.');
      }

      // Save AI summary if available
      if (cdr.aiData?.insights?.summary) {
        await db.callInsights.create({
          callId: cdr.ivruniqueid,
          summary: cdr.aiData.insights.summary,
          questions: cdr.aiData.insights.questions,
        });
      }
    } catch (err) {
      console.error('CDR processing failed:', err);
    }
  });
});

app.listen(3000);
```

## Your required response

```json
{ "Err": 0, "Errdesc": "OK" }
```

| Err | Meaning |
|---|---|
| 0 | OK |
| 1 | Parse error |
| 2 | Application error |

## Tips

- **Respond immediately** before processing — Voicenter waits for your `200 OK`. Heavy processing should be async (queue job, `setImmediate`, etc.).
- **Idempotency** — Voicenter may retry. Store `ivruniqueid` as a unique key and skip duplicates.
- **Recording URL** — The `record` field is a direct link to the MP3. Store it in your CRM for playback.
- **Queue abandons** — `status: ABANDONE` + `queuename` set means a customer hung up while waiting. Send them an SMS/WhatsApp callback offer.
- **AI data** — `data_type` values: `1`=boolean, `2`=string, `3`=number, `4`=json array, `5`=json object list, `6`=json object.
