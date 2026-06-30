---
name: click2call
description: Initiate or terminate outgoing calls using the Voicenter Click2Call API
---

> **Language.** Reply in the user's language: detect what they write — Hebrew→Hebrew, English→English — and mirror it, switching if they switch mid-conversation. This shapes your prose, your questions, and your `AskUserQuestion` option labels only. It does **not** change the artifacts you produce — identifiers, JSON keys, BCP-47 language codes, API field names, and other data stay exactly as specified.

> **CRM integration context.** When the user is building a full CRM integration — not just this API in isolation — always invoke the **`crm-onboarding`** skill alongside this one and frame the answer covering all three core services: Click2Call, Screen Pop, and Call History.

Help the developer integrate **Click2Call** — initiate outbound calls directly from a CRM or web application with a single API request.

## When to use this skill

Use this skill when the user wants to:
- Add a "Call" button to their CRM that dials a customer from an agent's extension
- Initiate outbound calls programmatically from any web application
- Schedule or automate outbound calls from a backend service
- Terminate (hang up) an active call on an extension programmatically
- Pass custom CRM data into the call (for CDR records and screen pop)
- Control caller ID shown to the customer

## Environment Variables

```env
VOICENTER_API_CODE=your_api_token_here
# The server's IP must be authorized in Voicenter CPanel
```

## How it works

Click2Call creates **two sequential call legs**:
- **Leg 1** — Voicenter calls the agent's extension (`phone` param). The agent picks up.
- **Leg 2** — Once Leg 1 is answered, Voicenter dials the customer (`target` param) and bridges both legs.

## Endpoint

```
https://api.voicenter.com/ForwardDialer/click2call.aspx
```

Accepts: `GET` or `POST-JSON`
Response: `XML` by default, or `JSON` when `format=json` is included (always use `format=json`)

## Request Parameters

| Parameter | Required | Description |
|---|---|---|
| `code` | ✅ | API authentication token |
| `phone` | ✅ | Agent's extension SIP code or phone number (E.164 without `+`). For login-dependent extension: `phone=logincode&phonelogincode=XXXX` |
| `target` | ✅ | Customer phone number (E.164 without `+`) or extension SIP |
| `action` | ✅ | `call` to initiate, `terminate` to hang up |
| `format` | ✅ | Always set to `json` to get JSON response instead of XML |
| `record` | ❌ | `true` / `false` — enable call recording (default: `false`) |
| `phonecallerid` | ❌ | Caller ID shown on agent's phone |
| `targetcallerid` | ❌ | Caller ID shown to the customer |
| `phonemaxdialtime` | ❌ | Leg 1 max ring time in seconds (default: 60) |
| `targetmaxdialtime` | ❌ | Leg 2 max ring time in seconds (default: 60) |
| `maxduration` | ❌ | Max call duration in seconds (default: 7200) |
| `phoneautoanswer` | ❌ | `true` / `1` — auto-answer Leg 1 (Voicenter extensions only) |
| `checkphonedevicestate` | ❌ | Block call if agent extension is offline |
| `checktargetdevicestate` | ❌ | Block call if target extension is offline |
| `language` | ❌ | Language for system prompts: `he`, `en`, `ru`, etc. |
| `var_*` | ❌ | Up to 10 custom CRM params (e.g. `var_clientID=123`). Appear in CDR and Pop-Up Screen. |
| `ignoredncstatus` | ❌ | `1`=ignore DNC on phone, `2`=ignore on target, `3`=both |

## POST-JSON Request Example

```json
{
  "code": "XXXXXXXXXXXX",
  "phone": "SIPSIP",
  "target": "0501234567",
  "action": "call",
  "format": "json",
  "record": "true",
  "var_clientID": "CRM-9876",
  "var_campaignID": "SUMMER2024"
}
```

## GET Request Example

```
https://api.voicenter.com/ForwardDialer/click2call.aspx?phone=SIPSIP&target=0501234567&code=XXXX&action=call&format=json&record=true
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

## Terminate a Call

To hang up an active call on an extension:

```json
{
  "code": "XXXXXXXXXXXX",
  "phone": "SIPSIP",
  "action": "terminate",
  "format": "json"
}
```

## TypeScript Implementation

```typescript
const C2C_URL = 'https://api.voicenter.com/ForwardDialer/click2call.aspx';
const CODE = process.env.VOICENTER_API_CODE!;

interface Click2CallResponse {
  ERRORCODE: number;
  ERRORMESSAGE: string;
  CALLID: string;
}

async function click2call(
  phone: string,
  target: string,
  options?: {
    record?: boolean;
    phonecallerid?: string;
    targetcallerid?: string;
    maxduration?: number;
    customData?: Record<string, string>; // keys must start with var_
  }
): Promise<Click2CallResponse> {
  const body: Record<string, unknown> = {
    code: CODE,
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

async function terminateCall(phone: string): Promise<void> {
  await fetch(C2C_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ code: CODE, phone, action: 'terminate', format: 'json' }),
  });
}

// CRM "Call" button — agent clicks to dial customer
const result = await click2call('SIPSIP', '0501234567', {
  record: true,
  customData: { var_clientID: 'CRM-9876', var_campaignID: 'SUMMER2024' },
});
console.log('Call started, CALLID:', result.CALLID);
```

## Tips

- **Always include `format=json`** — without it the response is XML.
- **Save the `CALLID`** — use it to correlate CDR records (Call Log API) and real-time events (Real-Time API).
- **Pass `var_*` custom params** to surface CRM data in the Pop-Up Screen and CDR Notification webhook.
- **Use `checkphonedevicestate=true`** to avoid Leg 1 failures when agents are offline.
- The server IP making requests must be authorized in the Voicenter CPanel.
- Phone numbers must be in **E.164 format without `+`** — e.g. `972501234567` not `+972501234567`.

## Related Skills

- **Active Calls** — Check if an agent is already on a call before initiating Click2Call
- **CDR Notification / Call Log** — Retrieve the CDR for this call using the returned `CALLID`
- **Pop-Up Screen** — The `var_*` params you pass here appear in the Pop-Up Screen response
- **Mute Recording** — Use the `CALLID` as `ivrid` to mute recording on this specific call
- **Extension List** — Get valid SIP codes to use as the `phone` parameter
