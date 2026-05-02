# Skill: `real-time`

Connect to Voicenter real-time call and agent events via the EventsSDK (socket.io).

> Source: [`plugins/voicenter-api/skills/real-time/SKILL.md`](../../../plugins/voicenter-api/skills/real-time/SKILL.md)
> Plugin: [voicenter-api](../../plugins/voicenter-api.md) · Direction: **In/Out** · Transport: **Socket.io SDK**

---

## When to use this skill

- Build a live wallboard showing real-time call activity and agent statuses
- React to calls as they happen — ringing, answered, hold, hangup
- Monitor queue depth in real time and alert supervisors above thresholds
- Trigger callback SMS when a caller abandons a queue
- Confirm an agent's status change propagated (after [Login/Logout](../login-logout/README.md))
- Build a real-time CRM integration that opens/closes screens as calls progress
- Discover the **monitor server hostname** needed for [Mute Recording](../mute-recording/README.md)

> Use the [Active Calls](../active-calls/README.md) skill instead when you need on-demand snapshots without a persistent connection.

---

## SDK

| Distribution | URL |
|---|---|
| Browser / Node CDN | `https://cdn.voicenter.co/cdn/events-sdk/voicenter-events-sdk.umd.js` |
| GitHub examples | https://github.com/VoicenterTeam/VoicenterEventsSDK/tree/next/examples/js |
| .NET NuGet | `VoicenterEventsSDK.NET` |

---

## Login types

| Type | Use case | Required credentials |
|---|---|---|
| `token` | Server-side, account-wide events (recommended) | `token` from Voicenter |
| `account` | Server-side, account-wide events | `username` + `password` |
| `user` | Per-agent — events for one user/extension | `email` + `password` from CPanel |

```env
VOICENTER_TOKEN=your_realtime_token
# or
VOICENTER_USERNAME=...
VOICENTER_PASSWORD=...
# or
[email protected]
VOICENTER_PASSWORD=...
```

---

## Connect

```typescript
const sdk = new EventsSDK({
  loginType: 'token',
  useLoginApi: true,
  token: process.env.VOICENTER_TOKEN,
});

sdk.init();
```

The SDK auto-reconnects on socket disconnects. On reconnect, fresh `AllExtensionsStatus` / `loginStatus` snapshots are emitted — re-initialize state from those events.

---

## Events

### `loginSuccess` — connection confirmed

```typescript
sdk.on('loginSuccess', (response) => {
  // { errorCode: 0, errorDesc: "OK", servertime: 1597930812, servertimeoffset: 180 }
});
```

### `loginStatus` — initial queue state

```typescript
sdk.on('loginStatus', (response) => {
  // { errorCode: 0, Queues: [{ QueueID, QueueName, Calls: [...] }] }
});
```

### `AllExtensionsStatus` — full extension snapshot

```typescript
sdk.on('AllExtensionsStatus', (response) => {
  response.extensions.forEach(ext => {
    console.log(`${ext.userName} (${ext.extenUser}): status=${ext.representativeStatus}, calls=${ext.calls.length}`);
  });
});
```

Extension fields: `userID`, `userName`, `extenUser`, `number`, `onlineUserID`, `representativeStatus`, `calls`, `lastCallEventEpoch`, `lastAnsweredCallEventEpoch`.

### `QueueEvent` — call enters or exits a queue

```typescript
sdk.on('QueueEvent', (response) => {
  const { reason, data, ivruniqueid } = response;
  // reason: "JOIN" | "EXIT" | "ABANDONED"
});
```

QueueEvent fields: `QueueID`, `QueueName`, `Calls[]` of `{ CallerID, CallerName, IvrUniqueID, JoinTimeStamp }`.

### `ExtensionEvent` — call lifecycle and agent status

```typescript
sdk.on('ExtensionEvent', (response) => {
  const { reason, cause, data } = response;
  const call = data.currentCall;
  // reason: "NEWCALL" | "ANSWER" | "HOLD" | "UNHOLD" | "HANGUP" | "userStatusUpdate"
});
```

#### `ExtensionEvent` reasons

| Reason | Trigger |
|---|---|
| `NEWCALL` | Incoming ringing or outgoing dialing |
| `ANSWER` | Call answered |
| `HOLD` | Placed on hold |
| `UNHOLD` | Off hold |
| `HANGUP` | Call ended |
| `userStatusUpdate` | Agent changed status |

#### `HANGUP` cause values

| Cause | Meaning |
|---|---|
| `Normal hangup` | Ended normally |
| `Answered elsewhere` | Rang on multiple extensions, picked up elsewhere |
| `Call Rejected` | Click2Call Leg1 not answered |

#### `currentCall` fields

`callStarted`, `callAnswered`, `answered` (0/1), `callerphone`, `callstatus` (`Ringing`/`Dialing`/`Talking`/`Hold`), `direction` (`Incoming`/`Outgoing`/`Click2Call`/`Spy`), `ivrid`, `recording.IsMuted`, `c2cdirection` (1=Leg1, 2=Leg2), `did`, `customdata`.

---

## Agent status codes (`representativeStatus`)

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

---

## Full TypeScript implementation (wallboard)

```typescript
declare const EventsSDK: any;

interface ExtState { name: string; status: number; activeCalls: number; }

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
  sdk.on('loginSuccess', () => console.log('Connected'));

  sdk.on('AllExtensionsStatus', (res: any) => {
    res.extensions.forEach((ext: any) => {
      state.extensions.set(ext.extenUser, {
        name: ext.userName,
        status: ext.representativeStatus,
        activeCalls: ext.calls.length,
      });
    });
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
      if (caller) sendSms(caller, "We missed your call. We'll call you back!");
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

## Tips & best practices

- **Initialize state** on connect with `AllExtensionsStatus` + `loginStatus`, then apply incremental `ExtensionEvent` and `QueueEvent` updates.
- `QueueEvent reason: ABANDONED` and CDR `status: ABANDONE` fire for the same event — deduplicate by `ivruniqueid`.
- `c2cdirection: 1` = Click2Call Leg1, `c2cdirection: 2` = Leg2.
- On `userStatusUpdate`, `data.calls` is empty — only `representativeStatus` changed.
- The connection URL contains your **monitor server hostname** — required for [Mute Recording](../mute-recording/README.md). Log it on connect.
- Treat reconnects as a state reset — re-initialize from the next `AllExtensionsStatus` snapshot.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Login fails | Wrong `token` / `email` / `password` | Reset credentials with Voicenter |
| Repeated reconnects | Network drops or token expiry | Re-issue `init()` and re-subscribe; reset state |
| Missing events | Wrong `loginType` (e.g. `user` only sees that user) | Switch to `token` for account-wide |
| Cannot find monitor host | Connection URL not logged | Add `console.log(sdk.connectionUrl)` after connect |

---

## Related skills

- [Active Calls](../active-calls/README.md) — on-demand snapshot alternative
- [Mute Recording](../mute-recording/README.md) — uses the monitor server hostname surfaced here
- [Login/Logout](../login-logout/README.md) — confirm via `userStatusUpdate`
- [CDR Notification](../cdr-notification/README.md) — fires after the call ends, complements live events
