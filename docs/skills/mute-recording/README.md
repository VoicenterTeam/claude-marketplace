# Skill: `mute-recording`

Mute or unmute call recording in real time via the Voicenter Mute Call Recording API.

> Source: [`plugins/voicenter-api/skills/mute-recording/SKILL.md`](../../../plugins/voicenter-api/skills/mute-recording/SKILL.md)
> Plugin: [voicenter-api](../../plugins/voicenter-api.md) · Direction: **In/Out** · Transport: **REST (dynamic monitor server)**

---

## When to use this skill

- Add a "Pause Recording" button for **PCI-DSS** compliance
- Auto-pause recording when the agent opens a payment form
- Mute one specific call by `ivrid`
- Mute all calls on an extension (sensitive mode)
- Resume recording after sensitive entry is complete

---

## How it works

- Mute **by extension** to mute all currently active calls on that extension.
- Mute **by call ID (`ivrid`)** to mute one specific call.
- Set `state: "0"` to unmute.

> If the agent makes a **new** call after a per-extension mute request, the new call is **not** automatically muted — send another request.

---

## Dynamic monitor server

This API does not live on `api.voicenter.com`. It lives on your account's **monitor server**:

```
https://<monitorX>.voicenter.co/api/MuteUnmuteCalls
```

Two ways to obtain your monitor hostname:

1. **From the [Real-Time](../real-time/README.md) SDK** — log the connection URL on connect; the host is your monitor server.
2. **Voicenter support** — request the static name (e.g. `monitor1`, `monitor2`).

```env
VOICENTER_MONITOR_SERVER=https://monitor1.voicenter.co
```

---

## Request — by extension

POST-JSON:

```json
{ "extension": "SIPSIP", "state": "1" }
```

GET:

```
https://YOUR_MONITOR.voicenter.co/api/MuteUnmuteCalls?extension=SIPSIP&state=1
```

| Field | Required | Values |
|---|---|---|
| `extension` | ✅ | SIP code |
| `state` | ✅ | `"1"` mute, `"0"` unmute |

## Request — by call ID

POST-JSON:

```json
{ "ivrid": "202406011200abc123def456", "state": "1" }
```

GET:

```
https://YOUR_MONITOR.voicenter.co/api/MuteUnmuteCalls?ivrid=202406011200abc123def456&state=1
```

| Field | Required | Values |
|---|---|---|
| `ivrid` | ✅ | Universal call ID (Click2Call `CALLID`, CDR `ivruniqueid`, Real-Time `currentCall.ivrid`) |
| `state` | ✅ | `"1"` mute, `"0"` unmute |

---

## Response

```json
{
  "ErrorCode": "200",
  "Message": "Success",
  "ActionID": "14d3b31988b247be8ff5818d1cadc3d3"
}
```

| Field | Description |
|---|---|
| `ErrorCode` | `"200"` success |
| `Message` | `"Success"`, `"UniqueIvrID not found"`, `"Parameters are not valid..."` |
| `ActionID` | Unique ID of this mute action |

---

## TypeScript implementation

```typescript
const MONITOR_SERVER = process.env.VOICENTER_MONITOR_SERVER!;

interface MuteResponse {
  ErrorCode: string;
  Message: string;
  ActionID: string;
}

async function muteByExtension(extension: string, mute: boolean): Promise<MuteResponse> {
  const res = await fetch(`${MONITOR_SERVER}/api/MuteUnmuteCalls`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ extension, state: mute ? '1' : '0' }),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const data: MuteResponse = await res.json();
  if (data.ErrorCode !== '200') throw new Error(`Mute failed: ${data.Message}`);
  return data;
}

async function muteByCallId(ivrid: string, mute: boolean): Promise<MuteResponse> {
  const res = await fetch(`${MONITOR_SERVER}/api/MuteUnmuteCalls`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ivrid, state: mute ? '1' : '0' }),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const data: MuteResponse = await res.json();
  if (data.ErrorCode !== '200') throw new Error(`Mute failed: ${data.Message}`);
  return data;
}
```

### PCI-DSS payment flow

```typescript
async function onPaymentFormOpen(agentExtension: string) {
  await muteByExtension(agentExtension, true);
}

// agent collects card data — not recorded

async function onPaymentFormClose(agentExtension: string) {
  await muteByExtension(agentExtension, false);
}
```

---

## Where mute state is reflected

| Surface | Field |
|---|---|
| [Real-Time](../real-time/README.md) `ExtensionEvent` | `currentCall.recording.IsMuted` |
| [Pop-Up Screen](../popup-screen/README.md) | `isMuted` |
| [Active Calls](../active-calls/README.md) | `recording.IsMuted` |
| CDR (after the call) | recording metadata |

---

## Tips & best practices

- Use **mute by ivrid** when an agent has multiple concurrent calls (conferences, attended transfers).
- Use **mute by extension** for simple single-call PCI flows.
- The `ivrid` for a live call is available from the Real-Time `ExtensionEvent` or the Click2Call response `CALLID`.
- Compliant with **PCI-DSS** for protecting cardholder data during voice transactions.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `UniqueIvrID not found` | Wrong `ivrid` (call already ended, typo) | Verify against Real-Time / Active Calls |
| Hostname does not resolve | Wrong monitor server | Pull from Real-Time SDK connect URL |
| New calls not muted | Per-extension mute applies only to currently active calls | Re-issue per call as new ones start |
| `403` / network error | Monitor server reachable only from whitelisted egress | Coordinate with Voicenter support |

---

## Related skills

- [Real-Time](../real-time/README.md) — get `ivrid` of the live call and discover monitor hostname
- [Click2Call](../click2call/README.md) — `CALLID` returned is the same as `ivrid` for muting
- [Active Calls](../active-calls/README.md) — `recording.IsMuted` shows current mute state
- [Pop-Up Screen](../popup-screen/README.md) — `isMuted` reflects the current state in the popup payload
