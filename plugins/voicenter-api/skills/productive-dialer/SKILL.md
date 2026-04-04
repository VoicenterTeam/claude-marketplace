---
description: Manage auto-dialer campaigns via the Voicenter Dialer API — add/remove destinations, control campaigns, manage agents
---

Help the developer integrate the **Voicenter Productive Dialer API** — manage campaigns, upload call destinations, control campaign state, and manage agent assignments entirely from their CRM.

## Base URL

```
https://api.voicenter.com/ForwardDialer/Dialer/
```

All methods use `POST-JSON` (or `GET`). Authentication via `Code` field.

## Workflow

1. Call **GetCampaignList** to get your campaign codes.
2. Use the campaign `Code` (not name) in all subsequent calls.
3. Upload destinations with **AddCall** or **AddCallsBulk**.
4. Control execution with **StartCampaign** / **StopCampaign**.

---

## GetCampaignList

Returns all campaigns in your account.

```json
// Request
{ "Code": "MY_API_CODE" }

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
`TotalAwaitingCalls` is the reliable count for IVR Dialer campaigns. Use `TotalPendingCalls` for Agent Dialer.

---

## AddCall — Add a single destination

```
URI: https://api.voicenter.com/ForwardDialer/Dialer/AddCall
```

```json
{
  "Campaign": "CAMPAIGN_CODE",
  "Target": "0501234567",
  "CustomerName": "John Doe",
  "CallerID": "0722776772",
  "Priority": 42,
  "OriginateTime": 1702750000,
  "IsDateLocal": "true",
  "IgnoreDncStatus": "true",
  "CustomData": {
    "var_LeadID": 1234567,
    "var_LeadCampaign": "Facebook"
  }
}
```

| Field | Required | Description |
|---|---|---|
| `Campaign` | ✅ | Campaign code from `GetCampaignList` |
| `Target` | ✅ | Phone number (international prefix required outside Israel) |
| `CustomerName` | ❌ | Name shown to agent |
| `CallerID` | ❌ | Outbound caller ID shown to customer — must be a number in your account |
| `Priority` | ❌ | Higher = dialed first |
| `OriginateTime` | ❌ | Schedule for future dial (Epoch time). Must send with `IsDateLocal`. |
| `IsDateLocal` | ❌ | `true` = use account local timezone, `false` = GMT+0. Recommended: `true`. |
| `IgnoreDncStatus` | ❌ | `true` = bypass Do-Not-Call-Me service |
| `CustomData` | ❌ | Key-value pairs for pop-up screen and CDR logs |

---

## AddCallsBulk — Add up to 100,000 destinations

```
URI: https://api.voicenter.com/ForwardDialer/Dialer/AddCallsBulk
```

Send an array of destination objects (same fields as `AddCall`):

```json
[
  {
    "Campaign": "CAMPAIGN_CODE",
    "Target": "0501234567",
    "CustomerName": "John Doe",
    "Priority": 1,
    "CustomData": { "var_LeadID": 111 }
  },
  {
    "Campaign": "CAMPAIGN_CODE",
    "Target": "0501234568",
    "CustomerName": "Jane Doe"
  }
]
```

**Limits:** Up to 100,000 per request. Detailed per-destination results returned only for ≤ 3,000 destinations. Pass `"async": true` to force detailed response (max 3,000).

**Response:**

```json
{
  "ErrorCode": 0,
  "Description": "OK",
  "AddResult": [
    { "Target": "0501234567", "ErrorCode": 0, "Description": "OK", "CustomData": { "var_LeadID": 111 } },
    { "Target": "0501234568", "ErrorCode": 0, "Description": "OK", "CustomData": {} }
  ]
}
```

---

## RemoveCall — Remove a destination

```
URI: https://api.voicenter.com/ForwardDialer/Dialer/RemoveCall
```

```json
{ "Campaign": "CAMPAIGN_CODE", "Target": "0501234567" }
```

---

## ClearCampaignCalls — Remove ALL destinations

```
URI: https://api.voicenter.com/ForwardDialer/Dialer/ClearCampaignCalls
```

```json
{ "Campaign": "CAMPAIGN_CODE" }
```

---

## StopCampaign / StartCampaign

Pause and resume dialing:

```json
// Stop
{ "Campaign": "CAMPAIGN_CODE" }
// URI: https://api.voicenter.com/ForwardDialer/Dialer/StopCampaign

// Start
{ "Campaign": "CAMPAIGN_CODE" }
// URI: https://api.voicenter.com/ForwardDialer/Dialer/StartCampaign
```

---

## GetMembersList / AddMember / RemoveMember — Agent management

**Get agents in campaign:**
```json
// Request: { "Campaign": "CAMPAIGN_CODE" }
// Response: { "Data": [{ "Member": "SIPSIP1", "DisplayName": "John Doe" }], "ErrorCode": 0 }
```

**Add agent:**
```json
// URI: /AddMember
{ "Campaign": "CAMPAIGN_CODE", "Member": "SIPSIP1" }
// Response: { "Data": { "TotalAdded": 1 }, "ErrorCode": 0 }
```

**Remove agent:**
```json
// URI: /RemoveMember
{ "Campaign": "CAMPAIGN_CODE", "Member": "SIPSIP1" }
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

async function dialerRequest<T>(method: string, body: object): Promise<T> {
  const res = await fetch(`${DIALER_BASE}/${method}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const data = await res.json();
  if (data.ErrorCode !== 0) throw new Error(`Dialer ${method} error: ${data.Description}`);
  return data;
}

// Get all campaigns
const campaigns = await dialerRequest<any>('GetCampaignList', { Code: 'MY_CODE' });
const campaignCode = campaigns.Data[0].Code;

// Upload leads from CRM
const leads = [
  { Campaign: campaignCode, Target: '0501234567', CustomerName: 'John', Priority: 1, CustomData: { var_LeadID: 101 } },
  { Campaign: campaignCode, Target: '0501234568', CustomerName: 'Jane', Priority: 2, CustomData: { var_LeadID: 102 } },
];
await dialerRequest('AddCallsBulk', leads);

// Start the campaign
await dialerRequest('StartCampaign', { Campaign: campaignCode });

// Later — stop and clear
await dialerRequest('StopCampaign', { Campaign: campaignCode });
await dialerRequest('ClearCampaignCalls', { Campaign: campaignCode });
```

## Error Codes (common to all methods)

| ErrorCode | Description |
|---|---|
| 0 | OK |
| 1 | Invalid campaign code |
| 2 | Missing required field (Target, Member, etc.) |
| -2 | Phone number format invalid |

## Tips

- Always call `GetCampaignList` first — the `Code` in the response is your campaign identifier, not the campaign name.
- For **IVR Dialer campaigns** (predictive), use `TotalAwaitingCalls` for queue depth; for **Agent Dialer**, use `TotalPendingCalls`.
- `CustomData` values are passed through to the Pop-Up Screen and CDR Notification — use them to carry CRM lead IDs.
- `OriginateTime` + `IsDateLocal: true` lets you schedule callbacks for a specific time — great for "call back at 3 PM" CRM features.
- CDR records for dialer calls have `type: "ProductiveCall Leg1/Leg2"` — filter by `cdrTypes: [14, 15]` in the Call Log API.
