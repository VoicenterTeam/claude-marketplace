# Skill: `click2call`

Initiate or terminate outgoing calls using the Voicenter Click2Call API.

> Source: [`plugins/voicenter-api/skills/click2call/SKILL.md`](../../../plugins/voicenter-api/skills/click2call/SKILL.md)
> Plugin: [voicenter-api](../../plugins/voicenter-api.md) · Direction: **Outgoing** · Transport: **REST**

---

## When to use this skill

- Add a "Call" button to a CRM that dials a customer from an agent's extension
- Initiate outbound calls programmatically from any backend
- Schedule or automate outbound calls
- Terminate (hang up) an active call on an extension
- Pass custom CRM data into the call so it appears in the CDR and Pop-Up Screen
- Control caller ID shown to the customer

---

## How it works (2-leg model)

Click2Call creates **two sequential call legs**:

| Leg | What happens |
|---|---|
| Leg 1 | Voicenter calls the agent's extension (`phone`). The agent picks up. |
| Leg 2 | Once Leg 1 is answered, Voicenter dials the customer (`target`) and bridges both legs. |

The two legs appear as separate CDRs (`CdrType` 9 and 10).

---

## Endpoint

```
POST https://api.voicenter.com/ForwardDialer/click2call.aspx
GET  https://api.voicenter.com/ForwardDialer/click2call.aspx?...
```

Response is XML by default — **always include `format=json`** to get JSON.

---

## Authentication

| Field | Notes |
|---|---|
| `code` | Lowercase. Sent in the body (POST-JSON) or query string (GET). |
| Server IP | Must be whitelisted in CPanel → API Settings. |

```env
VOICENTER_API_CODE=your_api_token_here
```

---

## Request parameters

| Parameter | Required | Description |
|---|---|---|
| `code` | ✅ | API authentication token |
| `phone` | ✅ | Agent's extension SIP code or phone number (E.164 without `+`). For login-dependent extensions: `phone=logincode&phonelogincode=XXXX` |
| `target` | ✅ | Customer phone number (E.164 without `+`) or extension SIP |
| `action` | ✅ | `call` to initiate, `terminate` to hang up |
| `format` | ✅ | Set to `json` to get JSON response |
| `record` | ❌ | `true` / `false` — enable call recording (default `false`) |
| `phonecallerid` | ❌ | Caller ID shown on agent's phone |
| `targetcallerid` | ❌ | Caller ID shown to the customer |
| `phonemaxdialtime` | ❌ | Leg 1 max ring time in seconds (default 60) |
| `targetmaxdialtime` | ❌ | Leg 2 max ring time in seconds (default 60) |
| `maxduration` | ❌ | Max call duration in seconds (default 7200) |
| `phoneautoanswer` | ❌ | `true` / `1` — auto-answer Leg 1 (Voicenter extensions only) |
| `checkphonedevicestate` | ❌ | Block call if agent extension is offline |
| `checktargetdevicestate` | ❌ | Block call if target extension is offline |
| `language` | ❌ | System-prompt language: `he`, `en`, `ru`, etc. |
| `var_*` | ❌ | Up to 10 custom CRM params (e.g. `var_clientID=123`). Surface in CDR and Pop-Up Screen. |
| `ignoredncstatus` | ❌ | `1`=ignore DNC on `phone`, `2`=on `target`, `3`=both |

### POST-JSON request

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

### GET request

```
https://api.voicenter.com/ForwardDialer/click2call.aspx?phone=SIPSIP&target=0501234567&code=XXXX&action=call&format=json&record=true
```

---

## Response

```json
{
  "ERRORCODE": 0,
  "ERRORMESSAGE": "OK",
  "CALLID": "20240601abc123def456"
}
```

`CALLID` is the universal call ID — use it as the correlation key for CDR Notification, Call Log, Real-Time, and Mute Recording.

---

## Error codes

| ERRORCODE | Meaning |
|---|---|
| 0 | Success |
| 1 | Invalid request parameters |
| 2 | Application error |
| 3 | Agent extension is offline |
| 4 | Extension blocked for Click2Call |

---

## Terminate a call

```json
{
  "code": "XXXXXXXXXXXX",
  "phone": "SIPSIP",
  "action": "terminate",
  "format": "json"
}
```

This hangs up whatever is active on that extension.

---

## TypeScript implementation

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
  if (data.ERRORCODE !== 0) {
    throw new Error(`Click2Call error ${data.ERRORCODE}: ${data.ERRORMESSAGE}`);
  }
  return data;
}

async function terminateCall(phone: string): Promise<void> {
  await fetch(C2C_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ code: CODE, phone, action: 'terminate', format: 'json' }),
  });
}
```

### CRM "Call" button example

```typescript
const result = await click2call('SIPSIP', '0501234567', {
  record: true,
  customData: { var_clientID: 'CRM-9876', var_campaignID: 'SUMMER2024' },
});
console.log('Call started, CALLID:', result.CALLID);
```

---

## Tips & best practices

- **Always include `format=json`** — without it the response is XML.
- **Save the `CALLID`** the moment you receive it. It is the only key that links this call across CDR Notification, Call Log, Real-Time, and Mute Recording.
- **Pass `var_*` params** to surface CRM context in the Pop-Up Screen and CDR Notification webhook payloads.
- **Check the agent first** — call the [Active Calls](../active-calls/README.md) skill or use `checkphonedevicestate=true` to skip dialing if the extension is offline or already busy.
- **Use E.164 without `+`** — `972501234567`, never `+972501234567` or `0501234567`.
- **Server IP must be whitelisted** in Voicenter CPanel.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Response is XML | Missing `format=json` | Add `format=json` to every request |
| `ERRORCODE 1` | Missing or malformed parameter | Verify `phone`, `target`, `action`, and `code` |
| `ERRORCODE 3` | Agent SIP is offline | Have the agent register; or test with `checkphonedevicestate=false` |
| `ERRORCODE 4` | Extension blocked from Click2Call | Enable Click2Call on that extension in CPanel |
| `403`/`401` from Voicenter | Server IP not whitelisted | Add IP in CPanel → API Settings |

---

## Related skills

- [Active Calls](../active-calls/README.md) — pre-check whether the agent is busy
- [CDR Notification](../cdr-notification/README.md) / [Call Log](../call-log/README.md) — retrieve the CDR using `CALLID`
- [Pop-Up Screen](../popup-screen/README.md) — `var_*` params surface here as `customdata`
- [Mute Recording](../mute-recording/README.md) — use `CALLID` as `ivrid` to mute this call
- [Extension List](../extension-list/README.md) — get valid SIP codes for the `phone` parameter
