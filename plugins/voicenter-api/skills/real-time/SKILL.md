---
name: real-time
description: Connect to Voicenter real-time call and agent events via the EventsSDK (socket.io)
---

Help the developer integrate the **Voicenter Real-Time API** — a socket.io-based SDK that streams live call events, queue changes, and agent status updates continuously.

## When to use this skill

Use this skill when the user wants to:
- Build a live wallboard showing real-time call activity and agent statuses
- React to calls as they happen — ringing, answered, hold, hangup
- Monitor queue depth in real time and alert supervisors when thresholds are exceeded
- Trigger actions when a caller abandons a queue (send callback SMS)
- Confirm an agent's status change propagated (after Login/Logout API call)
- Build a real-time CRM integration that opens/closes screens as calls progress
- Get the monitor server hostname (needed for Mute Recording API)

**Use Active Calls API instead** when you only need on-demand snapshots without a persistent connection.

## Environment Variables

```env
VOICENTER_TOKEN=your_realtime_token_here
# Token type depends on your login method:
# - Token login: use VOICENTER_TOKEN
# - Account login: use VOICENTER_USERNAME + VOICENTER_PASSWORD
# - User login: use VOICENTER_EMAIL + VOICENTER_PASSWORD
```

## SDK

- **Browser/Node CDN:** `https://cdn.voicenter.co/cdn/events-sdk/voicenter-events-sdk.umd.js`
- **GitHub examples:** `https://github.com/VoicenterTeam/VoicenterEventsSDK/tree/next/examples/js`
- **.NET NuGet:** `VoicenterEventsSDK.NET`

## Login Types

| Type | Use case | Required credentials |
|---|---|---|
| `token` | Server-side — entire account events | `token` from Voicenter |
| `account` | Server-side — entire account events | `username` + `password` |
| `user` | Per-agent — events for one user/extension | `email` + `password` from CPanel |

## Connection Examples

```typescript
// Token login (recommended for server-side integrations)
const sdk = new EventsSDK({
  loginType: 'token',
  useLoginApi: true,
  token: process.env.VOICENTER_TOKEN,
});

// Account login
const sdk = new EventsSDK({
  loginType: 'account',
  username: process.env.VOICENTER_USERNAME,
  password: process.env.VOICENTER_PASSWORD,
});

// User login (single agent)
const sdk = new EventsSDK({
  loginType: 'user',
  email: process.env.VOICENTER_EMAIL,
  password: process.env.VOICENTER_PASSWORD,
});

sdk.init();
```

---

## Events Reference

### `loginSuccess` — Connection confirmed

```typescript
sdk.on('loginSuccess', (response) => {
  // { errorCode: 0, errorDesc: "OK", servertime: 1597930812, servertimeoffset: 180 }
  console.log('Connected to Voicenter Real-Time');
});
```

### `loginStatus` — Initial queue state on connect

```typescript
sdk.on('loginStatus', (response) => {
  // { errorCode: 0, Queues: [{ QueueID, QueueName, Calls: [...] }] }
  response.Queues.forEach(q => {
    console.log(`Queue: ${q.QueueName}, waiting: ${q.Calls.length}`);
  });
});
```

### `AllExtensionsStatus` — Full extension snapshot on connect

```typescript
sdk.on('AllExtensionsStatus', (response) => {
  response.extensions.forEach(ext => {
    console.log(`${ext.userName} (${ext.extenUser}): status=${ext.representativeStatus}, calls=${ext.calls.length}`);
  });
});
```

Extension fields: `userID`, `userName`, `extenUser`, `number`, `onlineUserID`, `representativeStatus` (1–13), `calls` (active calls array), `lastCallEventEpoch`, `lastAnsweredCallEventEpoch`.

### `QueueEvent` — Call enters or exits a queue

```typescript
sdk.on('QueueEvent', (response) => {
  const { reason, data, ivruniqueid } = response;
  // reason: "JOIN" | "EXIT" | "ABANDONED"

  if (reason === 'JOIN') {
    console.log(`New call in queue ${data.QueueName}: ${data.Calls[0]?.CallerID}`);
  }
  if (reason === 'ABANDONED') {
    const callerID = data.Calls[0]?.CallerID ?? '';
    if (callerID) sendSms(callerID, "We missed your call. We'll call you back!");
  }
});
```

QueueEvent fields: `QueueID`, `QueueName`, `Calls` array of `{ CallerID, CallerName, IvrUniqueID, JoinTimeStamp }`.

### `ExtensionEvent` — Call lifecycle and agent status changes

```typescript
sdk.on('ExtensionEvent', (response) => {
  const { reason, cause, data } = response;
  // reason: "NEWCALL" | "ANSWER" | "HOLD" | "UNHOLD" | "HANGUP" | "userStatusUpdate"

  const call = data.currentCall;

  switch (reason) {
    case 'NEWCALL':
      console.log(`${data.userName}: new ${call.direction} call from ${call.callerphone}`);
      break;
    case 'ANSWER':
      console.log(`${data.userName}: answered — ivrid: ${call.ivrid}`);
      break;
    case 'HANGUP':
      console.log(`${data.userName}: call ended (${cause}) — ivrid: ${data.ivruniqueid}`);
      break;
    case 'userStatusUpdate':
      console.log(`${data.userName}: status → ${data.representativeStatus}`);
      break;
  }
});
```

### `ExtensionEvent` reasons

| Reason | Trigger |
|---|---|
| `NEWCALL` | Incoming ringing or outgoing dialing |
| `ANSWER` | Call answered |
| `HOLD` | Call placed on hold |
| `UNHOLD` | Call taken off hold |
| `HANGUP` | Call ended |
| `userStatusUpdate` | Agent changed status (Login/Logout/Lunch etc.) |

### `ExtensionEvent` HANGUP cause values

| Cause | Meaning |
|---|---|
| `Normal hangup` | Call ended normally |
| `Answered elsewhere` | Call rang on multiple extensions, answered by another |
| `Call Rejected` | Click2Call Leg1 was not answered |

### `currentCall` fields

`callStarted`, `callAnswered`, `answered` (0/1), `callerphone`, `callstatus` (`Ringing`/`Dialing`/`Talking`/`Hold`), `direction` (`Incoming`/`Outgoing`/`Click2Call`/`Spy`), `ivrid`, `recording.IsMuted`, `c2cdirection` (1=Leg1, 2=Leg2), `did`, `customdata`.

---

## Full TypeScript Implementation (Wallboard)

```typescript
declare const EventsSDK: any;

interface ExtState {
  name: string;
  status: number;
  activeCalls: number;
}

const state = {
  extensions: new Map<string, ExtState>(),
  queues: new Map<string, { name: string; waiting: number }>(),
};

const sdk = new EventsSDK({
  loginType: 'token',
  useLoginApi: true,
  token: process.env.VOICENTER_TOKEN!,
});

sdk.init().then(() => {
  sdk.on('loginSuccess', () => console.log('Connected to Voicenter Real-Time'));

  sdk.on('AllExtensionsStatus', (res: any) => {
    res.extensions.forEach((ext: any) => {
      state.extensions.set(ext.extenUser, {
        name: ext.userName,
        status: ext.representativeStatus,
        activeCalls: ext.calls.length,
      });
    });
    console.log(`Initialized ${state.extensions.size} extensions`);
  });

  sdk.on('loginStatus', (res: any) => {
    res.Queues.forEach((q: any) => {
      state.queues.set(String(q.QueueID), { name: q.QueueName, waiting: q.Calls.length });
    });
  });

  sdk.on('QueueEvent', (event: any) => {
    const { reason, data } = event;
    state.queues.set(String(data.QueueID), { name: data.QueueName, waiting: data.Calls.length });

    if (reason === 'ABANDONED') {
      const caller = data.Calls[0]?.CallerID;
      if (caller) sendSms(caller, "We missed your call. We'll call you back shortly!");
    }
  });

  sdk.on('ExtensionEvent', (event: any) => {
    const { reason, data } = event;
    const ext = state.extensions.get(data.extenUser);
    if (ext) {
      ext.status = data.representativeStatus;
      ext.activeCalls = data.calls?.length ?? 0;
    }

    if (reason === 'HANGUP' && data.currentCall?.direction === 'Incoming') {
      notifyCRM('call_ended', { ivrid: data.ivruniqueid, ext: data.extenUser });
    }
  });
});
```

---

## Agent Status Codes (`representativeStatus`)

| Code | Status |
|---|---|
| 1 | Login |
| 2 | Logout |
| 3 | Lunch |
| 5 | Administrative |
| 7 | Private |
| 9 | Other |
| 11 | Training |
| 12 | Team meeting |
| 13 | Brief |

## Tips

- **Initialize state** with `AllExtensionsStatus` + `loginStatus` on connect, then apply incremental `ExtensionEvent` and `QueueEvent` updates.
- `QueueEvent reason: ABANDONED` and CDR Notification `status: ABANDONE` both fire for the same event — deduplicate by `ivruniqueid`.
- `c2cdirection: 1` = Leg1 (agent connection), `c2cdirection: 2` = Leg2 (customer connection).
- On `userStatusUpdate`, `data.calls` will be empty — only `representativeStatus` has changed.
- The Real-Time API connection URL contains your **monitor server hostname** — the same server required for the **Mute Recording API**.

## Related Skills

- **Active Calls** — For on-demand snapshots without a persistent connection
- **Mute Recording** — Uses the monitor server hostname from this SDK's connection URL
- **Login/Logout** — Use `userStatusUpdate` events to confirm status changes set via the API
- **CDR Notification** — Complements Real-Time: CDR fires after call ends with full details
