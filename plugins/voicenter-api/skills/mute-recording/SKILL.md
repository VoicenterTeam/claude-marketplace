---
name: mute-recording
description: Mute or unmute call recording in real time via the Voicenter Mute Call Recording API
---

> **Language.** Reply in the user's language: detect what they write — Hebrew→Hebrew, English→English — and mirror it, switching if they switch mid-conversation. This shapes your prose, your questions, and your `AskUserQuestion` option labels only. It does **not** change the artifacts you produce — identifiers, JSON keys, BCP-47 language codes, API field names, and other data stay exactly as specified.

Help the developer integrate **real-time recording mute/unmute** into their CRM — so agents can pause recording when a customer provides sensitive information (credit card, ID number, etc.).

## When to use this skill

Use this skill when the user wants to:
- Add a "Pause Recording" button in their CRM for PCI-DSS compliance
- Automatically pause recording when an agent opens a payment form
- Mute recording for a specific call by its ID (`ivrid`)
- Mute all calls on an extension (when the agent enters a sensitive mode)
- Resume recording after sensitive data entry is complete

## Environment Variables

```env
VOICENTER_MONITOR_SERVER=https://monitor1.voicenter.co
# Replace "monitor1" with your account's actual monitor server.
# Get the dynamic server from the Real-Time API connection URL, or contact Voicenter support.
```

## How it works

- Send a mute request **by extension** to mute all active calls on that extension.
- Send a mute request **by call ID (`ivrid`)** to mute one specific call.
- Set `state: "0"` to unmute and resume recording.

## ⚠️ Dynamic Monitor Server

The endpoint uses a **dynamic monitor server** assigned to your account.
URL format: `https://<monitorX>.voicenter.co/api/MuteUnmuteCalls`

To get your account's monitor server:
- From the **Real-Time API**: the socket connection URL contains your monitor server hostname
- Or contact Voicenter support to get your static monitor server name (e.g. `monitor1`, `monitor2`)

---

## Mute by Extension

Mutes all active calls on the given extension SIP code.

**Note:** If the agent makes a new call after this request, that new call will **not** be muted automatically — send another mute request.

### POST-JSON

```json
{
  "extension": "SIPSIP",
  "state": "1"
}
```

### GET

```
https://YOUR_MONITOR.voicenter.co/api/MuteUnmuteCalls?extension=SIPSIP&state=1
```

| Field | Required | Values |
|---|---|---|
| `extension` | ✅ | SIP code of the extension |
| `state` | ✅ | `"1"` = Mute, `"0"` = Unmute |

---

## Mute by Call ID (ivrid)

Mutes one specific call by its unique Voicenter call ID.

### POST-JSON

```json
{
  "ivrid": "202406011200abc123def456",
  "state": "1"
}
```

### GET

```
https://YOUR_MONITOR.voicenter.co/api/MuteUnmuteCalls?ivrid=202406011200abc123def456&state=1
```

| Field | Required | Values |
|---|---|---|
| `ivrid` | ✅ | Unique call ID from Click2Call response, CDR Notification, or Real-Time events |
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
const MONITOR_SERVER = process.env.VOICENTER_MONITOR_SERVER!; // e.g. 'https://monitor1.voicenter.co'

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

## PCI-DSS Payment Flow Pattern

```typescript
// 1. Agent clicks "Enter Payment Details" in CRM
async function onPaymentFormOpen(agentExtension: string) {
  await muteByExtension(agentExtension, true);
  console.log('Recording paused — payment data not recorded');
}

// 2. Agent collects credit card info (this portion is not recorded)

// 3. Agent clicks "Done" in CRM
async function onPaymentFormClose(agentExtension: string) {
  await muteByExtension(agentExtension, false);
  console.log('Recording resumed');
}
```

## Tips

- Use **mute by ivrid** for precision when an agent has multiple concurrent calls (conference, attended transfer).
- Use **mute by extension** for simple single-call scenarios where you don't have the ivrid handy.
- The `ivrid` for a live call is available from the **Real-Time API** (`ExtensionEvent`) or from the **Click2Call** response `CALLID`.
- Mute state is reflected in:
  - `recording.IsMuted` field in Real-Time `ExtensionEvent`
  - `isMuted` field in Pop-Up Screen webhook payload
  - The CDR recording metadata after the call ends
- Compliant with **PCI-DSS** requirements for protecting cardholder data during voice transactions.

## Related Skills

- **Real-Time API** — Get `ivrid` of the current live call and monitor mute state changes
- **Click2Call** — The `CALLID` returned is the same as `ivrid` for mute requests
- **Active Calls** — `recording.IsMuted` field shows current mute state per extension
- **Pop-Up Screen** — `isMuted` field in the popup payload reflects real-time recording state
