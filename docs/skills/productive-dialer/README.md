# Skill: `productive-dialer`

Manage auto-dialer campaigns via the Voicenter Dialer API — add/remove destinations, control campaigns, manage agents.

> Source: [`plugins/voicenter-api/skills/productive-dialer/SKILL.md`](../../../plugins/voicenter-api/skills/productive-dialer/SKILL.md)
> Plugin: [voicenter-api](../../plugins/voicenter-api.md) · Direction: **Outgoing** · Transport: **REST**

---

## When to use this skill

- Add leads to a dialer campaign from your CRM
- Bulk upload up to 100,000 numbers in one request
- Start or stop a campaign programmatically
- Schedule callbacks for specific times ("call this lead at 3 PM")
- Add or remove agents from a campaign
- Check pending-call counts
- Clear all pending calls
- Pass CRM lead data into the call for reporting

---

## Base URL

```
POST https://api.voicenter.com/ForwardDialer/Dialer/<Method>
```

All methods are POST-JSON. Authentication via `Code` (uppercase).

---

## Authentication

| Field | Notes |
|---|---|
| `Code` | **Uppercase.** Body field. |
| Server IP | Must be whitelisted in CPanel → API Settings. |

```env
VOICENTER_API_CODE=your_api_token_here
```

---

## Workflow

1. **`GetCampaignList`** → discover campaign codes.
2. Use the campaign **`Code`** (not the name) in every subsequent call.
3. Upload destinations: **`AddCall`** or **`AddCallsBulk`**.
4. Control execution: **`StartCampaign`** / **`StopCampaign`**.
5. Manage agents: **`AddMember`** / **`RemoveMember`** / **`GetMembersList`**.
6. Clean up: **`RemoveCall`** / **`ClearCampaignCalls`**.

---

## Methods

### `GetCampaignList` — list all campaigns

Request:

```json
{ "Code": "MY_API_CODE" }
```

Response:

```json
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

`StatusName`: `"Enabled"` active, `"Disabled"` stopped.
- IVR / Predictive Dialer campaigns → use `TotalAwaitingCalls`.
- Agent Dialer campaigns → use `TotalPendingCalls`.

---

### `AddCall` — add one destination

```
URI: /AddCall
```

```json
{
  "Campaign": "CAMPAIGN_CODE",
  "Code": "MY_API_CODE",
  "Target": "972501234567",
  "CustomerName": "John Doe",
  "CallerID": "0722776772",
  "Priority": 42,
  "OriginateTime": 1702750000,
  "IsDateLocal": "true",
  "IgnoreDncStatus": "true",
  "CustomData": { "var_LeadID": 1234567, "var_LeadSource": "Facebook" }
}
```

| Field | Required | Description |
|---|---|---|
| `Campaign` | ✅ | Campaign code from `GetCampaignList` |
| `Target` | ✅ | E.164 number (international prefix required for non-Israeli) |
| `Code` | ✅ | API token |
| `CustomerName` | ❌ | Customer name shown to agent |
| `CallerID` | ❌ | Outbound caller ID — must be a number on your account |
| `Priority` | ❌ | Higher = dialed first |
| `OriginateTime` | ❌ | Schedule (Epoch). Pair with `IsDateLocal`. |
| `IsDateLocal` | ❌ | `"true"` local TZ (recommended), `"false"` GMT+0 |
| `IgnoreDncStatus` | ❌ | `"true"` bypass DNC |
| `CustomData` | ❌ | Key-values forwarded to Pop-Up Screen and CDR |

---

### `AddCallsBulk` — upload up to 100,000

```
URI: /AddCallsBulk
```

Body is an **array** of destinations:

```json
[
  { "Campaign": "...", "Code": "...", "Target": "972501234567", "CustomerName": "John", "Priority": 1, "CustomData": { "var_LeadID": 111 } },
  { "Campaign": "...", "Code": "...", "Target": "972501234568", "CustomerName": "Jane" }
]
```

**Limits:**
- Up to 100,000 destinations per request
- Detailed per-destination results only for ≤ 3,000
- Add `"async": true` to force a detailed response (max 3,000)

Response:

```json
{
  "ErrorCode": 0,
  "Description": "OK",
  "AddResult": [
    { "Target": "972501234567", "ErrorCode": 0, "Description": "OK" }
  ]
}
```

---

### `RemoveCall` — remove one destination

```
URI: /RemoveCall
```

```json
{ "Campaign": "CAMPAIGN_CODE", "Code": "MY_API_CODE", "Target": "972501234567" }
```

### `ClearCampaignCalls` — wipe all pending

```
URI: /ClearCampaignCalls
```

```json
{ "Campaign": "CAMPAIGN_CODE", "Code": "MY_API_CODE" }
```

### `StartCampaign` / `StopCampaign`

```
URI: /StartCampaign
URI: /StopCampaign
```

```json
{ "Campaign": "CAMPAIGN_CODE", "Code": "MY_API_CODE" }
```

---

### Agent management

#### `GetMembersList`
```json
{ "Campaign": "CAMPAIGN_CODE", "Code": "MY_API_CODE" }
```

```json
{ "Data": [{ "Member": "SIPSIP1", "DisplayName": "John Doe" }], "ErrorCode": 0 }
```

#### `AddMember`
```
URI: /AddMember
```
```json
{ "Campaign": "CAMPAIGN_CODE", "Code": "MY_API_CODE", "Member": "SIPSIP1" }
```
```json
{ "Data": { "TotalAdded": 1 }, "ErrorCode": 0 }
```

#### `RemoveMember`
```
URI: /RemoveMember
```
```json
{ "Campaign": "CAMPAIGN_CODE", "Code": "MY_API_CODE", "Member": "SIPSIP1" }
```
```json
{ "Data": { "TotalRemoved": 1 }, "ErrorCode": 0 }
```

---

### `GetCampaignPendingCalls`

```
URI: /GetCampaignPendingCalls
```

Response (truncated):

```json
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

## TypeScript implementation

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
  if (data.ErrorCode !== 0) throw new Error(`Dialer ${method}: ${data.Description}`);
  return data;
}

// Full workflow: list → upload → start
const { Data: campaigns } = await dialerRequest<any>('GetCampaignList', {});
const campaignCode = campaigns[0].Code;

const leads = [
  { Campaign: campaignCode, Target: '972501234567', CustomerName: 'John', Priority: 1, CustomData: { var_LeadID: '101' } },
  { Campaign: campaignCode, Target: '972501234568', CustomerName: 'Jane', Priority: 2, CustomData: { var_LeadID: '102' } },
];
await dialerRequest('AddCallsBulk', leads);
await dialerRequest('StartCampaign', { Campaign: campaignCode });

// Later
await dialerRequest('StopCampaign', { Campaign: campaignCode });
await dialerRequest('ClearCampaignCalls', { Campaign: campaignCode });
```

---

## Error codes

| ErrorCode | Description |
|---|---|
| 0 | OK |
| 1 | Invalid campaign code |
| 2 | Missing required field |
| -2 | Phone number format invalid |

---

## Tips & best practices

- **Always call `GetCampaignList` first.** The `Code` field is the campaign identifier — never use the human-readable `Name`.
- `OriginateTime` + `IsDateLocal: "true"` schedules a future callback in the account's local timezone — perfect for "call me at 3 PM" CRM features.
- **`CustomData`** flows to [Pop-Up Screen](../popup-screen/README.md) and [CDR Notification](../cdr-notification/README.md) — use it to carry lead IDs and source attribution.
- Dialer CDRs have `type: "ProductiveCall Leg1/Leg2"` — filter [Call Log](../call-log/README.md) with `cdrTypes: [14, 15]`.
- The [Blacklist](../blacklist/README.md) auto-skips matching numbers — keep it in sync with your CRM opt-out list.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `ErrorCode: 1` | Wrong campaign `Code` | Re-fetch via `GetCampaignList` |
| `ErrorCode: -2` | Bad phone number | Convert to E.164 without `+` |
| Bulk upload returns no `AddResult` | Over 3,000 destinations | Add `"async": true` or chunk |
| Campaign won't start | Missing members or pending calls | Add at least one agent and one destination |
| Numbers not dialed | Currently blacklisted | Inspect Blacklist; remove if needed |

---

## Related skills

- [Extension List](../extension-list/README.md) — get valid `SIP` codes for `Member`
- [Call Log](../call-log/README.md) — retrieve dialer call results with `cdrTypes: [14, 15]`
- [CDR Notification](../cdr-notification/README.md) — receive dialer CDRs live
- [Blacklist](../blacklist/README.md) — blacklisted numbers are auto-skipped
