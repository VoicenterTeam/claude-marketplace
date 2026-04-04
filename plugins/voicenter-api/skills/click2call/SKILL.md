---
description: Initiate or terminate outgoing calls using the Voicenter Click2Call API
---

Help the developer integrate **Click2Call** into their CRM or application using the real Voicenter Click2Call API.

## How it works

Click2Call creates **two call legs**:
- **Leg 1** — Voicenter calls the agent's extension (`phone` param). The agent picks up.
- **Leg 2** — Once Leg 1 is answered, Voicenter dials the customer (`target` param) and bridges the calls.

## Endpoint

```
https://api.voicenter.com/ForwardDialer/click2call.aspx
```

Accepts: `GET` or `POST-JSON`
Response: `XML` (default) or `JSON` (add `format=json`)

## Authentication

The `code` parameter is your personal API token, provided by the Voicenter back office.

## Call Action Parameters

| Parameter | Required | Description |
|---|---|---|
| `phone` | ✅ | Agent extension or phone number (E164 without `+`, or Israeli `0*****`). For SIP Trunk: `phone=SIPTRUNK`. For login-dependent extension: `phone=logincode&phonelogincode=XXXX` |
| `target` | ✅ | Customer phone number or extension (E164 without `+`) |
| `code` | ✅ | API authentication token |
| `action` | ✅ | `call` |
| `record` | ❌ | `true` / `false` (default: `false`) |
| `phonecallerid` | ❌ | Caller ID shown on agent's phone |
| `targetcallerid` | ❌ | Caller ID shown to customer |
| `phonemaxdialtime` | ❌ | Leg 1 max ring time in seconds (default: 60) |
| `targetmaxdialtime` | ❌ | Leg 2 max ring time in seconds (default: 60) |
| `maxduration` | ❌ | Max call duration in seconds (default: 7200) |
| `phoneautoanswer` | ❌ | `true` / `1` — auto-answer Leg 1 (Voicenter extensions only) |
| `targetautoanswer` | ❌ | `true` / `1` — auto-answer Leg 2 (Voicenter extensions only) |
| `checkphonedevicestate` | ❌ | Block call if agent extension is offline |
| `checktargetdevicestate` | ❌ | Block call if target extension is offline |
| `language` | ❌ | Language for system prompts: `he`, `en`, `ru`, etc. |
| `format` | ❌ | `json` for JSON response (default: XML) |
| `var_*` | ❌ | Up to 10 custom params (e.g. `var_clientID=123`). Used in CDR, pop-up, and Chrome extension. |
| `ignoredncstatus` | ❌ | `1`=ignore DNC on phone, `2`=ignore on target, `3`=both |

## GET Request Example

```
https://api.voicenter.com/ForwardDialer/click2call.aspx?phone=SIPSIP&target=0501234567&code=XXXXXXXXXXXX&action=call&format=json
```

## POST-JSON Request Example

```json
{
  "code": "XXXXXXXXXXXX",
  "phone": "SIPSIP",
  "target": "0501234567",
  "action": "call",
  "record": "true",
  "format": "json",
  "var_clientID": "CRM-9876"
}
```

## JSON Response

```json
{
  "ERRORCODE": 0,
  "ERRORMESSAGE": "OK",
  "CALLID": "20240601abc123def456"
}
```

| ERRORCODE | Meaning |
|---|---|
| 0 | Success |
| 1 | Invalid request parameters |
| 2 | Application error |
| 3 | Agent extension is offline |
| 4 | Extension blocked for Click2Call |

## Terminate Action

To hang up an active call on an extension:

```json
{
  "code": "XXXXXXXXXXXX",
  "phone": "SIPSIP",
  "action": "terminate"
}
```

## TypeScript Implementation

```typescript
const C2C_URL = 'https://api.voicenter.com/ForwardDialer/click2call.aspx';

interface Click2CallResponse {
  ERRORCODE: number;
  ERRORMESSAGE: string;
  CALLID: string;
}

async function click2call(
  code: string,
  phone: string,
  target: string,
  options?: {
    record?: boolean;
    phonecallerid?: string;
    targetcallerid?: string;
    maxduration?: number;
    customData?: Record<string, string>;
  }
): Promise<Click2CallResponse> {
  const body: Record<string, unknown> = {
    code,
    phone,
    target,
    action: 'call',
    format: 'json',
    record: options?.record ? 'true' : 'false',
    ...(options?.phonecallerid && { phonecallerid: options.phonecallerid }),
    ...(options?.targetcallerid && { targetcallerid: options.targetcallerid }),
    ...(options?.maxduration && { maxduration: options.maxduration }),
    ...options?.customData,
  };

  const res = await fetch(C2C_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });

  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const data: Click2CallResponse = await res.json();
  if (data.ERRORCODE !== 0) throw new Error(`Click2Call error ${data.ERRORCODE}: ${data.ERRORMESSAGE}`);
  return data;
}

async function terminateCall(code: string, phone: string): Promise<Click2CallResponse> {
  const res = await fetch(C2C_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ code, phone, action: 'terminate', format: 'json' }),
  });
  return res.json();
}

// Usage
const result = await click2call('MY_CODE', 'SIPSIP', '0501234567', {
  record: true,
  customData: { var_clientID: 'CRM-9876', var_campaignID: 'SUMMER2024' },
});
console.log('Call ID:', result.CALLID);
```

## Tips

- Save the returned `CALLID` — use it to correlate CDR records (via Call Log API) and real-time events (via Real-Time API).
- Pass `var_*` custom params to surface CRM data in the Pop-Up Screen and CDR Notification.
- Use `checkphonedevicestate=true` to avoid wasted calls when agents are offline.
- The IP of the server making requests must be authorized in the Voicenter CPanel.
