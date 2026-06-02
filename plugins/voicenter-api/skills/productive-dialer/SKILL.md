---
name: productive-dialer
description: Manage auto-dialer campaigns via the Voicenter Dialer API — add/remove destinations, control campaigns, manage agents
---

> **Language.** Reply in the user's language: detect what they write — Hebrew→Hebrew, English→English — and mirror it, switching if they switch mid-conversation. This shapes your prose, your questions, and your `AskUserQuestion` option labels only. It does **not** change the artifacts you produce — identifiers, JSON keys, BCP-47 language codes, API field names, and other data stay exactly as specified.

Help the developer integrate the **Voicenter Productive Dialer API** — manage campaigns, upload call destinations, control campaign state, and manage agent assignments from their CRM.

## When to use this skill

Use this skill when the user wants to:
- Add leads or contacts to a dialer campaign from their CRM
- Upload a bulk list of numbers to dial (up to 100,000 at once)
- Start or stop a dialer campaign programmatically
- Schedule callbacks for specific times ("call this customer at 3 PM")
- Add or remove agents from a campaign
- Check how many calls are still pending in a campaign
- Clear all pending calls from a campaign
- Pass CRM lead data (lead ID, campaign source) into the call for reporting

## Environment Variables

```env
VOICENTER_API_CODE=your_api_token_here
```

## Base URL

```
https://api.voicenter.com/ForwardDialer/Dialer/
```

All methods use `POST-JSON`. Authentication via `Code` field.

## Workflow

1. Call **GetCampaignList** to get campaign codes.
2. Use the campaign `Code` (not the name) in all subsequent calls.
3. Upload destinations with **AddCall** or **AddCallsBulk**.
4. Control execution with **StartCampaign** / **StopCampaign**.

---

## GetCampaignList — Get all campaigns

```json
// Request
{ "Code": "MY_API_CODE" }
```

```json
// Response
{
  "ErrorCode": 0,
  "Description": "OK",
  "Data": [
    {
      "Name": "Campaign1",
      "StatusName": "Enabled",
      "TotalPendingCalls": 23,
      "TotalAwaitingCalls": 23,
      "MaxPriority": 1,
      "MinPriority": 1,
      "Code": "CAMPAIGN_CODE_HERE"
    }
  ]
}
```

`StatusName`: `"Enabled"` = active, `"Disabled"` = stopped.
- For **IVR/Predictive Dialer** campaigns: use `TotalAwaitingCalls` for queue depth.
- For **Agent Dialer** campaigns: use `TotalPendingCalls`.

---

## AddCall — Add a single destination

```
URI: https://api.voicenter.com/ForwardDialer/Dialer/AddCall
```

```json
{
  "Campaign": "CAMPAIGN_CODE",
  "Target": "972501234567",
  "CustomerName": "John Doe",
  "CallerID": "0722776772",
  "Priority": 42,
  "OriginateTime": 1702750000,
  "IsDateLocal": "true",
  "IgnoreDncStatus": "true",
  "CustomData": {
    "var_LeadID": 1234567,
    "var_LeadSource": "Facebook"
  }
}
```

| Field | Required | Description |
|---|---|---|
| `Campaign` | ✅ | Campaign code from `GetCampaignList` |
| `Target` | ✅ | Phone number (E.164 format; international prefix required for non-Israeli numbers) |
| `Code` | ✅ | API authentication token |
| `CustomerName` | ❌ | Customer name shown to agent |
| `CallerID` | ❌ | Outbound caller ID shown to customer — must be a number in your account |
| `Priority` | ❌ | Higher value = dialed first |
| `OriginateTime` | ❌ | Schedule for future dial (Epoch time). Must include `IsDateLocal`. |
| `IsDateLocal` | ❌ | `"true"` = use account's local timezone. `"false"` = GMT+0. Recommended: `"true"`. |
| `IgnoreDncStatus` | ❌ | `"true"` = bypass Do-Not-Call service |
| `CustomData` | ❌ | Key-value pairs passed to Pop-Up Screen and CDR records |

---

## AddCallsBulk — Upload up to 100,000 destinations

```
URI: https://api.voicenter.com/ForwardDialer/Dialer/AddCallsBulk
```

Send an array of destination objects (same fields as `AddCall`):

```json
[
  {
    "Campaign": "CAMPAIGN_CODE",
    "Code": "MY_API_CODE",
    "Target": "972501234567",
    "CustomerName": "John Doe",
    "Priority": 1,
    "CustomData": { "var_LeadID": 111 }
  },
  {
    "Campaign": "CAMPAIGN_CODE",
    "Code": "MY_API_CODE",
    "Target": "972501234568",
    "CustomerName": "Jane Doe"
  }
]
```

**Limits:**
- Up to 100,000 destinations per request
- Detailed per-destination results returned only for ≤ 3,000 destinations
- Add `"async": true` to force detailed response (max 3,000)

```json
// Response
{
  "ErrorCode": 0,
  "Description": "OK",
  "AddResult": [
    { "Target": "972501234567", "ErrorCode": 0, "Description": "OK" },
    { "Target": "972501234568", "ErrorCode": 0, "Description": "OK" }
  ]
}
```

---

## RemoveCall — Remove a specific destination

```
URI: https://api.voicenter.com/ForwardDialer/Dialer/RemoveCall
```

```json
{ "Campaign": "CAMPAIGN_CODE", "Code": "MY_API_CODE", "Target": "972501234567" }
```

---

## ClearCampaignCalls — Remove ALL pending destinations

```
URI: https://api.voicenter.com/ForwardDialer/Dialer/ClearCampaignCalls
```

```json
{ "Campaign": "CAMPAIGN_CODE", "Code": "MY_API_CODE" }
```

---

## StartCampaign / StopCampaign

```json
// Start
// URI: https://api.voicenter.com/ForwardDialer/Dialer/StartCampaign
{ "Campaign": "CAMPAIGN_CODE", "Code": "MY_API_CODE" }

// Stop
// URI: https://api.voicenter.com/ForwardDialer/Dialer/StopCampaign
{ "Campaign": "CAMPAIGN_CODE", "Code": "MY_API_CODE" }
```

---

## Agent Management

### GetMembersList
```json
// Request: { "Campaign": "CAMPAIGN_CODE", "Code": "MY_API_CODE" }
// Response: { "Data": [{ "Member": "SIPSIP1", "DisplayName": "John Doe" }], "ErrorCode": 0 }
```

### AddMember
```json
// URI: /AddMember
{ "Campaign": "CAMPAIGN_CODE", "Code": "MY_API_CODE", "Member": "SIPSIP1" }
// Response: { "Data": { "TotalAdded": 1 }, "ErrorCode": 0 }
```

### RemoveMember
```json
// URI: /RemoveMember
{ "Campaign": "CAMPAIGN_CODE", "Code": "MY_API_CODE", "Member": "SIPSIP1" }
// Response: { "Data": { "TotalRemoved": 1 }, "ErrorCode": 0 }
```

---

## GetCampaignPendingCalls — List waiting destinations

```
URI: https://api.voicenter.com/ForwardDialer/Dialer/GetCampaignPendingCalls
```

```json
// Response
{
  "ErrorCode": 0,
  "Data": {
    "Campaign": { "Name": "Campaign1", "StatusName": "Enabled", "TotalPendingCalls": 4, "Code": "..." },
    "Calls": [
      {
        "Phone": "972501234567",
        "CustomerName": "John Doe",
        "Priority": 42,
        "OriginateTime": 1602819000,
        "CallStatus": { "Status": 1, "Description": "Pending" },
        "CustomData": { "var_LeadID": "1234567" }
      }
    ]
  }
}
```

---

## TypeScript Implementation

```typescript
const DIALER_BASE = 'https://api.voicenter.com/ForwardDialer/Dialer';
const CODE = process.env.VOICENTER_API_CODE!;

async function dialerRequest<T>(method: string, body: object): Promise<T> {
  const res = await fetch(`${DIALER_BASE}/${method}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ Code: CODE, ...body }),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const data = await res.json();
  if (data.ErrorCode !== 0) throw new Error(`Dialer ${method} error: ${data.Description}`);
  return data;
}

// Full campaign workflow: get campaigns → upload leads → start
const { Data: campaigns } = await dialerRequest<any>('GetCampaignList', {});
const campaignCode = campaigns[0].Code;

const leads = [
  { Campaign: campaignCode, Target: '972501234567', CustomerName: 'John', Priority: 1, CustomData: { var_LeadID: '101' } },
  { Campaign: campaignCode, Target: '972501234568', CustomerName: 'Jane', Priority: 2, CustomData: { var_LeadID: '102' } },
];
await dialerRequest('AddCallsBulk', leads);
await dialerRequest('StartCampaign', { Campaign: campaignCode });

// Later — stop and clear
await dialerRequest('StopCampaign', { Campaign: campaignCode });
await dialerRequest('ClearCampaignCalls', { Campaign: campaignCode });
```

## Error Codes

| ErrorCode | Description |
|---|---|
| 0 | OK |
| 1 | Invalid campaign code |
| 2 | Missing required field |
| -2 | Phone number format invalid |

## Tips

- **Always call `GetCampaignList` first** — the `Code` in the response is the campaign identifier, not the name.
- `OriginateTime` + `IsDateLocal: "true"` lets you schedule future callbacks — great for "call me back at 3 PM" CRM features.
- `CustomData` values flow through to the **Pop-Up Screen** and **CDR Notification** — use them to carry CRM lead IDs and source attribution.
- CDR records for dialer calls have `type: "ProductiveCall Leg1/Leg2"` — filter with `cdrTypes: [14, 15]` in the **Call Log API**.

## Related Skills

- **Extension List** — Get valid SIP codes to use as `Member` when adding agents to a campaign
- **Call Log** — Retrieve dialer call results using `cdrTypes: [14, 15]`
- **CDR Notification** — Receive dialer call CDRs in real time via webhook
- **Blacklist** — Blacklisted numbers are automatically skipped by the dialer
