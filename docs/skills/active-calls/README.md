# Skill: `active-calls`

Get a real-time snapshot of all active calls and queue activity, on demand.

> Source: [`plugins/voicenter-api/skills/active-calls/SKILL.md`](../../../plugins/voicenter-api/skills/active-calls/SKILL.md)
> Plugin: [voicenter-api](../../plugins/voicenter-api.md) · Direction: **In/Out** · Transport: **REST**

---

> **Language.** Reply in the user's language: detect what they write — Hebrew→Hebrew, English→English — and mirror it, switching if they switch mid-conversation. This shapes your prose, your questions, and your `AskUserQuestion` option labels only. It does **not** change the artifacts you produce — identifiers, JSON keys, BCP-47 language codes, API field names, and other data stay exactly as specified.

## When to use this skill

- Show a wallboard or dashboard of current call activity
- Check whether a specific agent is on a call before routing or initiating Click2Call
- Display live queue depth (how many callers are waiting)
- Show an agent's current call when a CRM record opens
- Poll for call state on-demand (use [Real-Time](../real-time/README.md) when you need streaming instead)

---

## Endpoints

| Action | URL |
|---|---|
| Active calls per extension | `https://monapisec.voicenter.co.il/comet/API/GetExtensionsCalls` |
| Callers waiting in queues | `https://monapisec.voicenter.co.il/comet/API/GetQueuesCallers` |

Both accept `GET` or `POST-JSON`. Response is JSON.

---

## Authentication

| Field | Notes |
|---|---|
| `code` | Lowercase. Body or query. |
| Server IP | Must be whitelisted in CPanel → API Settings. |

```env
VOICENTER_API_CODE=your_api_token_here
```

---

## `GetExtensionsCalls` — current call state per extension

### Request

```json
{ "code": "XXXXXXXXXXXXX", "extension": "SIPSIP1" }
```

Omit `extension` to retrieve all extensions.

GET form:
```
https://monapisec.voicenter.co.il/comet/API/GetExtensionsCalls?code=XXXXX&extension=SIPSIP1
```

### Response (truncated)

```json
{
  "ERR": 0,
  "DESC": "OK",
  "EXTENSIONS": [
    {
      "name": "User 2",
      "username": "SIPSIP2",
      "userID": 46454322,
      "onlineUserStatus": 1,
      "calls": [
        {
          "callStarted": 1602465818,
          "callAnswered": 1602465819,
          "answered": 1,
          "callerphone": "0722776772",
          "callstatus": "Talking",
          "direction": "Outgoing",
          "ivrid": "2020101201cc7b38df",
          "recording": { "Filename": "...mp3", "IsMuted": 0 },
          "did": ""
        }
      ]
    }
  ]
}
```

### Extension fields

| Field | Description |
|---|---|
| `username` | SIP code |
| `name` | Extension display name |
| `representative` | Currently logged-in user name |
| `onlineUserID` | User ID currently logged in (`0` if none) |
| `onlineUserStatus` | 1=Login, 2=Logout, 3=Lunch, 5=Admin, 7=Private, 9=Other, 11=Training, 12=Team meeting, 13=Brief |
| `calls` | Array of active calls (empty if idle) |

### Active call fields

| Field | Description |
|---|---|
| `callStarted` / `callAnswered` | Epoch seconds (`callAnswered` is `0` until pickup) |
| `answered` | `0` ringing/dialing, `1` answered |
| `callerphone` | Caller's number |
| `callstatus` | `Ringing`, `Dialing`, `Talking`, `Hold` |
| `direction` | `Incoming` or `Outgoing` |
| `ivrid` | Universal call ID — links to CDR / Pop-Up / Real-Time / Mute |
| `recording.IsMuted` | `0` recording, `1` muted |
| `did` | DID dialed (incoming only) |

---

## `GetQueuesCallers` — callers currently waiting in queues

### Request

```json
{ "code": "XXXXXXXXXXXXX", "queue": "12345678" }
```

Omit `queue` to retrieve all queues.

### Response

```json
{
  "ERR": 0,
  "DESC": "OK",
  "QUEUES": [
    {
      "Name": "Sales Queue",
      "ID": 12345678,
      "Weight": 5,
      "Callers": [
        { "Phone": "0722776772", "CallID": "202010131430590714966", "JoinTime": 1602599565, "Duration": 21 }
      ]
    },
    { "Name": "Support Queue", "ID": 87654321, "Weight": 0, "Callers": [] }
  ]
}
```

### Queue fields

| Field | Description |
|---|---|
| `Name` | Queue name |
| `ID` | Queue ID |
| `Weight` | Priority weight |
| `Callers[].Phone` | Caller's phone |
| `Callers[].CallID` | Universal call ID |
| `Callers[].JoinTime` | Epoch seconds when caller entered the queue |
| `Callers[].Duration` | Seconds the caller has been waiting |

---

## Error codes

| ERR | DESC |
|---|---|
| 0 | OK |
| 1 | Invalid request format |
| 2 | Invalid parameters or internal error |

---

## TypeScript implementation

```typescript
const ACTIVE_CALLS_BASE = 'https://monapisec.voicenter.co.il/comet/API';
const CODE = process.env.VOICENTER_API_CODE!;

interface ActiveCall {
  callStarted: number;
  callAnswered: number;
  answered: 0 | 1;
  callerphone: string;
  callstatus: 'Ringing' | 'Dialing' | 'Talking' | 'Hold';
  direction: 'Incoming' | 'Outgoing';
  ivrid: string;
  recording: { Filename: string; IsMuted: 0 | 1 };
  did: string;
}

interface ExtensionCalls {
  name: string;
  representative: string;
  username: string;
  userID: number;
  onlineUserStatus: number;
  calls: ActiveCall[];
}

async function getExtensionCalls(extension?: string): Promise<ExtensionCalls[]> {
  const res = await fetch(`${ACTIVE_CALLS_BASE}/GetExtensionsCalls`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ code: CODE, ...(extension && { extension }) }),
  });
  const data = await res.json();
  if (data.ERR !== 0) throw new Error(`Active Calls error: ${data.DESC}`);
  return data.EXTENSIONS;
}

async function getQueueCallers(queue?: string) {
  const res = await fetch(`${ACTIVE_CALLS_BASE}/GetQueuesCallers`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ code: CODE, ...(queue && { queue }) }),
  });
  const data = await res.json();
  if (data.ERR !== 0) throw new Error(`Queue Callers error: ${data.DESC}`);
  return data.QUEUES;
}
```

### Wallboard polling

```typescript
async function updateWallboard() {
  const [extensions, queues] = await Promise.all([
    getExtensionCalls(),
    getQueueCallers(),
  ]);
  const activeCalls = extensions.filter(e => e.calls.length > 0);
  const totalWaiting = queues.reduce((s, q: any) => s + q.Callers.length, 0);
  console.log(`Active calls: ${activeCalls.length} | Waiting: ${totalWaiting}`);
}

setInterval(updateWallboard, 10_000);
```

### Pre-check before Click2Call

```typescript
async function checkAgentCurrentCall(extensionSip: string) {
  const [ext] = await getExtensionCalls(extensionSip);
  if (ext?.calls.length > 0) {
    const call = ext.calls[0];
    return {
      active: true,
      caller: call.callerphone,
      ivrid: call.ivrid,
      duration: Date.now() / 1000 - call.callStarted,
    };
  }
  return { active: false };
}
```

---

## Tips & best practices

- **Poll vs stream** — Active Calls is a point-in-time snapshot. Use [Real-Time](../real-time/README.md) for continuous streaming.
- `onlineUserStatus: 2` (Logout) is the default for extensions with no logged-in user.
- Use `Callers[].Duration` to alert supervisors on long-waiting callers.
- `recording.IsMuted: 1` combined with [Mute Recording](../mute-recording/README.md) lets you toggle from a CRM button.
- The `ivrid` field is the universal call ID — links this row to CDR / Pop-Up / Call Log.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `ERR: 1` | Bad JSON or wrong content type | Send `Content-Type: application/json` |
| Empty `EXTENSIONS` | Wrong `code` value | Verify the org token |
| `403` | IP not whitelisted | Add IP in CPanel |
| Stale data | You polled too quickly | Throttle to ≥ 5s between requests |

---

## Related skills

- [Real-Time](../real-time/README.md) — continuous streaming alternative
- [Mute Recording](../mute-recording/README.md) — toggle recording with the `ivrid`
- [Extension List](../extension-list/README.md) — full SIP roster
- [CDR Notification](../cdr-notification/README.md) / [Call Log](../call-log/README.md) — historical correlation by `ivrid`
