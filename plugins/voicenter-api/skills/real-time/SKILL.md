---
description: Connect to Voicenter real-time call and agent events via the EventsSDK (socket.io)
---

Help the developer integrate the **Voicenter Real-Time API** — a socket.io-based SDK that streams live call events, queue changes, and agent status updates.

## How it works

The Real-Time API uses the **VoicenterEventsSDK** built on top of `socket.io`. You connect once and receive a stream of events for every call and agent status change in your organization.

- **SDK (browser/Node):** `https://cdn.voicenter.co/cdn/events-sdk/voicenter-events-sdk.umd.js`
- **GitHub examples:** `https://github.com/VoicenterTeam/VoicenterEventsSDK/tree/next/examples/js`
- **.NET NuGet:** `VoicenterEventsSDK.NET`

## Login Types

| Type | Use case | Credentials |
|---|---|---|
| `user` | Receive events for one specific user/extension | `email` + `password` from CPanel |
| `account` | Receive events for the entire account | `username` + `password` |
| `token` | Receive events for the entire account | `token` from Voicenter |

## Installation (Node.js)

```bash
npm install socket.io-client
# SDK loaded from CDN or via VoicenterEventsSDK package
```

## Connection Examples

### Token login (recommended for server-side)

```typescript
const sdk = new EventsSDK({
  loginType: 'token',
  useLoginApi: true,
  token: 'YOUR_VOICENTER_TOKEN',
});
```

### Account login

```typescript
const sdk = new EventsSDK({
  loginType: 'account',
  username: 'your_username',
  password: 'your_password',
});
```

### User login

```typescript
const sdk = new EventsSDK({
  loginType: 'user',
  email: '[email protected]',
  password: 'your_password',
});
```

## Events

### 1. `loginSuccess` — Connection confirmed

```typescript
sdk.on('loginSuccess', (response) => {
  // { errorCode: 0, errorDesc: "OK", servertime: 1597930812, servertimeoffset: 180 }
  console.log('Connected to Voicenter Real-Time');
});
```

### 2. `loginStatus` — Queue list on connect

```typescript
sdk.on('loginStatus', (response) => {
  // { errorCode: 0, Queues: [{ QueueID, QueueName, Calls: [...] }] }
  response.Queues.forEach(q => console.log(`Queue: ${q.QueueName}, waiting: ${q.Calls.length}`));
});
```

### 3. `AllExtensionsStatus` — Snapshot of all extensions on connect

```typescript
sdk.on('AllExtensionsStatus', (response) => {
  // Array of extension objects
  response.extensions.forEach(ext => {
    console.log(`${ext.userName} (${ext.extenUser}): status=${ext.representativeStatus}, calls=${ext.calls.length}`);
  });
});
```

Extension fields: `userID`, `userName`, `extenUser`, `number`, `onlineUserID`, `representativeStatus` (1–13), `calls` (active calls array), `lastCallEventEpoch`, `lastAnsweredCallEventEpoch`.

### 4. `QueueEvent` — Call enters or exits a queue

```typescript
sdk.on('QueueEvent', (response) => {
  const { reason, data, ivruniqueid } = response;
  // reason: "JOIN" | "EXIT" | "ABANDONED"
  
  if (reason === 'JOIN') {
    console.log(`New call in queue ${data.QueueName}: ${data.Calls[0]?.CallerID}`);
    // Trigger wallboard update
  }
  if (reason === 'ABANDONED') {
    console.log(`Caller abandoned queue ${data.QueueName}: ${ivruniqueid}`);
    // Trigger callback SMS
  }
});
```

QueueEvent fields: `QueueID`, `QueueName`, `Calls` (array of `{ CallerID, CallerName, IvrUniqueID, JoinTimeStamp }`).

### 5. `ExtensionEvent` — Call and agent status changes

```typescript
sdk.on('ExtensionEvent', (response) => {
  const { reason, cause, data } = response;
  // reason: "NEWCALL" | "ANSWER" | "HOLD" | "UNHOLD" | "HANGUP" | "userStatusUpdate"

  const ext = data;
  const call = ext.currentCall;

  switch (reason) {
    case 'NEWCALL':
      console.log(`${ext.userName}: new ${call.direction} call from ${call.callerphone}`);
      break;
    case 'ANSWER':
      console.log(`${ext.userName}: answered call ${call.ivrid}`);
      break;
    case 'HANGUP':
      console.log(`${ext.userName}: call ended (${cause}) — ivrid: ${data.ivruniqueid}`);
      break;
    case 'userStatusUpdate':
      console.log(`${ext.userName}: status changed to ${ext.representativeStatus}`);
      break;
  }
});
```

**`reason` values:**

| Reason | Trigger |
|---|---|
| `NEWCALL` | Incoming call ringing or outgoing call dialing |
| `ANSWER` | Call answered |
| `HOLD` | Call placed on hold |
| `UNHOLD` | Call taken off hold |
| `HANGUP` | Call ended |
| `userStatusUpdate` | Agent changed their status |

**`cause` (HANGUP only):**

| Cause | Meaning |
|---|---|
| `Normal hangup` | Call ended normally |
| `Answered elsewhere` | Call rang on multiple extensions, answered by another |
| `Call Rejected` | Click2Call Leg1 was not answered |

**`currentCall` fields:** `callStarted`, `callAnswered`, `answered` (0/1), `callerphone`, `callstatus` (`Ringing`/`Dialing`/`Talking`/`Hold`), `direction` (`Incoming`/`Outgoing`/`Click2Call`/`Spy`), `ivrid`, `recording.IsMuted`, `c2cdirection` (1=Leg1, 2=Leg2), `did`, `customdata`.

## Full TypeScript Implementation

```typescript
// Load SDK (Node.js — adjust for your environment)
// Browser: include <script src="https://cdn.voicenter.co/cdn/events-sdk/voicenter-events-sdk.umd.js">
declare const EventsSDK: any;

interface WallboardState {
  extensions: Map<string, { name: string; status: number; activeCalls: number }>;
  queues: Map<string, { name: string; waiting: number }>;
}

const state: WallboardState = {
  extensions: new Map(),
  queues: new Map(),
};

const sdk = new EventsSDK({
  loginType: 'token',
  useLoginApi: true,
  token: process.env.VOICENTER_TOKEN!,
});

sdk.init().then(() => {
  sdk.on('loginSuccess', () => console.log('✅ Connected to Voicenter Real-Time'));

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

  sdk.on('QueueEvent', (event: any) => {
    const { reason, data } = event;
    state.queues.set(String(data.QueueID), {
      name: data.QueueName,
      waiting: data.Calls.length,
    });

    if (reason === 'ABANDONED') {
      // Auto SMS callback for abandoned queue calls
      const caller = event.data.Calls[0]?.CallerID ?? '';
      if (caller) sendSms(caller, 'We missed your call. We\'ll call you back shortly!');
    }
  });

  sdk.on('ExtensionEvent', (event: any) => {
    const { reason, data } = event;
    const current = state.extensions.get(data.extenUser);
    if (current) {
      current.status = data.representativeStatus;
      current.activeCalls = data.calls?.length ?? 0;
    }

    if (reason === 'HANGUP' && data.currentCall?.direction === 'Incoming') {
      // Trigger CRM screen pop close
      notifyCRM('call_ended', { ivrid: data.ivruniqueid, ext: data.extenUser });
    }
  });
});
```

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

- Use `AllExtensionsStatus` to initialize your wallboard state, then apply incremental `ExtensionEvent` and `QueueEvent` updates.
- `QueueEvent reason: ABANDONED` + CDR Notification `status: ABANDONE` both fire — deduplicate by `ivruniqueid`.
- `c2cdirection: 1` = Leg1 (agent connection), `c2cdirection: 2` = Leg2 (customer connection).
- On `userStatusUpdate`, `data.calls` will be empty — only `representativeStatus` has changed.
- The Real-Time API gives you the **monitor server hostname** dynamically (in the socket connection URL), which is the same server needed for the Mute Recording API.
