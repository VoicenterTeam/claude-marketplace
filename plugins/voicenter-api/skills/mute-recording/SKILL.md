---
description: Mute or unmute call recording in real time via the Voicenter Mute Call Recording API
---

Help the developer integrate **real-time recording mute/unmute** into their CRM — so agents can pause recording when a customer provides sensitive information (credit card, personal ID, etc.).

## How it works

- Send a mute request **by extension** to mute all active calls on that extension.
- Or send a mute request **by call ID (`ivrid`)** to mute one specific call.
- Send `state: 0` to unmute and resume recording.

## ⚠️ Monitor Server

The endpoint uses a **dynamic monitor server** assigned to your account, not a fixed hostname.  
The URL format is: `https://<monitorX>.voicenter.co/api/MuteUnmuteCalls`

To get your account's monitor server dynamically, use the [Real-Time API](https://www.voicenter.com/API/real-time).  
Alternatively, contact Voicenter support to get your static monitor server name (e.g. `monitor1`, `monitor2`).

---

## Mute by Extension

Mutes all active calls on the given extension SIP code.

**Note:** If the agent makes a new call after this mute request, that new call will **not** be muted automatically — you must send another mute request.

### GET

```
https://YOUR_MONITOR.voicenter.co/api/MuteUnmuteCalls?extension=SIPSIP&state=1
```

### POST-JSON

```json
{
  "extension": "SIPSIP",
  "state": "1"
}
```

| Field | Required | Values |
|---|---|---|
| `extension` | ✅ | SIP ID of the extension (from CPanel) |
| `state` | ✅ | `"1"` = Mute, `"0"` = Unmute |

---

## Mute by Call ID (ivrid)

Mutes one specific call by its unique Voicenter call ID.

### GET

```
https://YOUR_MONITOR.voicenter.co/api/MuteUnmuteCalls?ivrid=XXXXXXXXXXXXXXXX&state=1
```

### POST-JSON

```json
{
  "ivrid": "202406011200abc123def456",
  "state": "1"
}
```

| Field | Required | Values |
|---|---|---|
| `ivrid` | ✅ | Unique call ID (from Click2Call response, CDR Notification, or Real-Time events) |
| `state` | ✅ | `"1"` = Mute, `"0"` = Unmute |

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
| `ErrorCode` | `"200"` = success |
| `Message` | `"Success"` on success; `"UniqueIvrID not found"` if ivrid is wrong; `"Parameters are not valid..."` if params are malformed |
| `ActionID` | Unique ID of this mute action |

---

## TypeScript Implementation

```typescript
// Replace with your account's actual monitor server
const MONITOR_SERVER = 'https://monitor1.voicenter.co';

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

// CRM button: "Pause Recording" clicked by agent
async function onPauseRecordingClick(extensionSip: string) {
  await muteByExtension(extensionSip, true);
  console.log('Recording paused');
}

// CRM button: "Resume Recording" clicked by agent
async function onResumeRecordingClick(extensionSip: string) {
  await muteByExtension(extensionSip, false);
  console.log('Recording resumed');
}
```

## CRM Integration Pattern

The most common pattern is a **Mute/Unmute button** in the CRM agent interface:

```typescript
// When agent clicks "Take credit card" button in CRM:
// 1. Mute recording
await muteByExtension(agentExtension, true);
// 2. Agent collects credit card info (not recorded)
// 3. Agent clicks "Done" button
await muteByExtension(agentExtension, false);
// 4. Recording resumes
```

## Tips

- The `ivrid` for a live call comes from the **Real-Time API** (`ExtensionEvent`) or from the **Click2Call** response `CALLID`.
- Mute state is visible in the CDR Notification payload — `isMuted: true` and in the `recording.IsMuted` field of Real-Time events.
- Use **mute by ivrid** for precision when an agent has multiple concurrent calls (conference, attended transfer).
- Use **mute by extension** for simplicity in single-call scenarios.
- Compliant with PCI-DSS requirements for payment data protection.
