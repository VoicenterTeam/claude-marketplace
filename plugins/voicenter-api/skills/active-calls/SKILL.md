---
description: Get a real-time snapshot of all active calls and queue activity via the Voicenter Active Calls API
---

Help the developer query **live call state** — who is on a call right now, what extensions are active, and how many callers are waiting in queues — using simple HTTP requests (no socket connection required).

## When to use this skill

Use this skill when the user wants to:
- Show a wallboard or dashboard with current call activity
- Check if a specific agent is currently on a call before routing or assigning a task
- Display live queue depth (how many callers are waiting)
- Build a CRM screen that shows an agent's current call when they open a customer record
- Poll for call state on-demand (not continuously — use Real-Time API for streaming)

## Environment Variables

```env
VOICENTER_API_CODE=your_api_token_here
```

## Endpoints

| Method | URI |
|---|---|
| Active calls per extension | `https://monapisec.voicenter.co.il/comet/API/GetExtensionsCalls` |
| Callers waiting in queues | `https://monapisec.voicenter.co.il/comet/API/GetQueuesCallers` |

Both accept: `GET` or `POST-JSON`
Response: `JSON`

Authentication: `code` field in the request body.

---

## GetExtensionsCalls

Returns the current call state for all extensions (or one specific extension).

### Request

```json
{
  "code": "XXXXXXXXXXXXX",
  "extension": "SIPSIP1"
}
```

Omit `extension` to get all extensions.

### GET Request

```
https://monapisec.voicenter.co.il/comet/API/GetExtensionsCalls?code=XXXXX&extension=SIPSIP1
```

### Response

```json
{
  "ERR": 0,
  "DESC": "OK",
  "EXTENSIONS": [
    {
      "name": "User 1",
      "representative": "User 1",
      "username": "SIPSIP1",
      "extensionID": 875756567,
      "userID": 6946792,
      "onlineUserID": 0,
      "onlineUserStatus": 2,
      "calls": []
    },
    {
      "name": "User 2",
      "representative": "User 2",
      "username": "SIPSIP2",
      "extensionID": 97483478,
      "userID": 46454322,
      "onlineUserID": 46454322,
      "onlineUserStatus": 1,
      "calls": [
        {
          "callStarted": 1602465818,
          "callAnswered": 1602465819,
          "answered": 1,
          "callername": "Voicenter",
          "callerphone": "0722776772",
          "callstatus": "Talking",
          "customdata": {},
          "direction": "Outgoing",
          "ivrid": "2020101201cc7b38df",
          "recording": { "Filename": "2020101201cc7b38df-aws-SIPSIP2-972722776772.mp3", "IsMuted": 0 },
          "did": ""
        }
      ]
    }
  ]
}
```

### Extension Fields

| Field | Description |
|---|---|
| `username` | SIP code of the extension |
| `name` | User name assigned to the extension |
| `representative` | Currently logged-in user name |
| `onlineUserID` | User ID of currently logged-in user (0 if no one logged in) |
| `onlineUserStatus` | Agent status: 1=Login, 2=Logout, 3=Lunch, 5=Admin, 7=Private, 9=Other, 11=Training, 12=Team meeting, 13=Brief |
| `calls` | Array of active calls (empty if no active calls) |

### Active Call Fields

| Field | Description |
|---|---|
| `callStarted` | Call start time (Epoch) |
| `callAnswered` | Call answer time (Epoch), `0` if not yet answered |
| `answered` | `0` = ringing/dialing, `1` = answered |
| `callerphone` | Caller's phone number |
| `callstatus` | `Ringing`, `Dialing`, `Talking`, `Hold` |
| `direction` | `Incoming` or `Outgoing` |
| `ivrid` | Unique call ID |
| `recording.IsMuted` | `0` = recording, `1` = muted |
| `did` | DID dialed (incoming calls only) |

---

## GetQueuesCallers

Returns the callers currently waiting in queues.

### Request

```json
{
  "code": "XXXXXXXXXXXXX",
  "queue": "12345678"
}
```

Omit `queue` to get all queues.

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
        {
          "Phone": "0722776772",
          "CallID": "202010131430590714966",
          "JoinTime": 1602599565,
          "Duration": 21
        }
      ]
    },
    {
      "Name": "Support Queue",
      "ID": 87654321,
      "Weight": 0,
      "Callers": []
    }
  ]
}
```

### Queue Fields

| Field | Description |
|---|---|
| `Name` | Queue name |
| `ID` | Queue ID |
| `Weight` | Queue priority weight |
| `Callers` | Array of waiting callers |
| `Callers[].Phone` | Caller's phone number |
| `Callers[].CallID` | Unique call ID |
| `Callers[].JoinTime` | When caller entered the queue (Epoch) |
| `Callers[].Duration` | Seconds the caller has been waiting |

### Error Codes

| ERR | DESC |
|---|---|
| 0 | OK |
| 1 | Invalid request format |
| 2 | Invalid parameters or internal error |

---

## TypeScript Implementation

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

interface QueueCaller {
  Phone: string;
  CallID: string;
  JoinTime: number;
  Duration: number;
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

// Wallboard: poll every 10 seconds
async function updateWallboard() {
  const [extensions, queues] = await Promise.all([
    getExtensionCalls(),
    getQueueCallers(),
  ]);

  const activeCalls = extensions.filter(e => e.calls.length > 0);
  const totalWaiting = queues.reduce((sum: number, q: any) => sum + q.Callers.length, 0);

  console.log(`Active calls: ${activeCalls.length} | Waiting in queues: ${totalWaiting}`);
  return { extensions, queues };
}

setInterval(updateWallboard, 10_000);

// CRM: check if agent is currently on a call when they open a customer record
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

## Tips

- **Poll vs. stream** — This API gives a point-in-time snapshot. For real-time streaming use the **Real-Time API** (socket.io). Use this API when you need an on-demand check (e.g., agent opens a CRM record).
- `onlineUserStatus: 2` (Logout) is the default for extensions with no logged-in user.
- Use `Callers[].Duration` to detect long-waiting callers and trigger supervisor alerts.
- `recording.IsMuted: 1` combined with the **Mute Recording API** lets you toggle recording from a CRM button.
- The `ivrid` field links this call to CDR Notification, Call Log, and Pop-Up Screen events.

## Related Skills

- **Real-Time API** — For continuous streaming of call events instead of polling
- **Mute Recording** — Toggle recording mute state using the `ivrid` from this API
- **Extension List** — Get all SIP codes to know which extensions exist
- **CDR Notification / Call Log** — Correlate live calls with historical records using `ivrid`
