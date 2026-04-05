---
description: Add or remove phone numbers from the Voicenter organization blacklist
---

Help the developer manage the **Voicenter Blacklist** — block numbers from being dialed by agents or dialers, and remove them when needed.

## When to use this skill

Use this skill when the user wants to:
- Block a customer who requested to not be called (opt-out / Do Not Call)
- Sync a CRM opt-out list with the Voicenter dialer blacklist
- Remove a number from the blacklist after a customer withdraws their opt-out
- Prevent specific numbers from being dialed in a campaign
- Automate blacklist updates triggered by CDR events (e.g. a customer pressed "opt out" DTMF)

## Environment Variables

```env
VOICENTER_API_CODE=your_api_token_here
```

## Endpoints

| Action | URI |
|---|---|
| Add numbers | `https://api.voicenter.com/Blacklist/AddBlackList` |
| Remove numbers | `https://api.voicenter.com/Blacklist/RemoveBulkFromBlacklist` |

Both accept: `GET` or `POST-JSON`
Response: `JSON`

## Authentication

`Code` field in the request body (your API token from Voicenter back office).

---

## AddBlackList

### POST-JSON Request

```json
{
  "Code": "XXXXXXXXXXXXXXXXXXXX",
  "Phones": [
    { "Phone": "972501234567", "Name": "John Doe" },
    { "Phone": "97231234567",  "Name": "Walter Melon" }
  ]
}
```

| Field | Required | Description |
|---|---|---|
| `Code` | ✅ | API authentication token |
| `Phones` | ✅ | Array of phone objects to block |
| `Phone` | ✅ | Phone number in E.164 format without `+` (e.g. `972501234567`) |
| `Name` | ❌ | Label for this blocked number (POST-only) |

### GET Request

```
https://api.voicenter.com/Blacklist/AddBlackList?code=XXXX&phones=972501234567&phones=97231234567
```

### Response

```json
{
  "ErrorCode": 0,
  "ErrorMessage": "OK",
  "Phones": [
    { "ErrorCode": 0, "ErrorMessage": "OK", "Phone": "972501234567" },
    { "ErrorCode": 0, "ErrorMessage": "OK", "Phone": "97231234567" }
  ]
}
```

---

## RemoveBulkFromBlacklist

### POST-JSON Request

```json
{
  "Code": "XXXXXXXXXXXXXXXXXXXX",
  "Phones": [
    { "Phone": "972501234567" },
    { "Phone": "97231234567" }
  ]
}
```

### GET Request

```
https://api.voicenter.com/Blacklist/RemoveBulkFromBlacklist?code=XXXX&phones=972501234567&phones=97231234567
```

### Response

```json
{
  "ErrorCode": 0,
  "ErrorMessage": "OK",
  "Phones": [
    { "ErrorCode": 0, "ErrorMessage": "OK", "Phone": "972501234567" },
    { "ErrorCode": 0, "ErrorMessage": "OK", "Phone": "97231234567" }
  ]
}
```

---

## Error Codes

| ErrorCode (top-level) | Meaning |
|---|---|
| 0 | OK |
| 1 | Invalid or missing `Code` |
| 2 | `Phone` field missing or invalid |

| ErrorCode (per phone) | Meaning |
|---|---|
| 0 | OK |
| 1 | Phone number format invalid — use E.164 without `+` (e.g. `972501234567`) |
| 2 | Internal error — contact Voicenter support |

---

## TypeScript Implementation

```typescript
const BL_BASE = 'https://api.voicenter.com/Blacklist';
const CODE = process.env.VOICENTER_API_CODE!;

interface BlacklistPhone {
  Phone: string;
  Name?: string;
}

interface BlacklistPhoneResult {
  ErrorCode: number;
  ErrorMessage: string;
  Phone: string;
}

interface BlacklistResponse {
  ErrorCode: number;
  ErrorMessage: string;
  Phones: BlacklistPhoneResult[];
}

async function addToBlacklist(phones: BlacklistPhone[]): Promise<BlacklistResponse> {
  const res = await fetch(`${BL_BASE}/AddBlackList`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ Code: CODE, Phones: phones }),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const data: BlacklistResponse = await res.json();
  if (data.ErrorCode !== 0) throw new Error(`Blacklist error: ${data.ErrorMessage}`);
  return data;
}

async function removeFromBlacklist(phones: string[]): Promise<BlacklistResponse> {
  const res = await fetch(`${BL_BASE}/RemoveBulkFromBlacklist`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ Code: CODE, Phones: phones.map(p => ({ Phone: p })) }),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

// Add a single opt-out
await addToBlacklist([{ Phone: '972501234567', Name: 'Opted out via website' }]);

// Remove after customer withdraws opt-out
await removeFromBlacklist(['972501234567']);

// Sync a large CRM opt-out list in chunks
async function syncOptOuts(optOutList: string[]) {
  const CHUNK = 100;
  for (let i = 0; i < optOutList.length; i += CHUNK) {
    const chunk = optOutList.slice(i, i + CHUNK).map(p => ({ Phone: p }));
    const result = await addToBlacklist(chunk);
    const failed = result.Phones.filter(p => p.ErrorCode !== 0);
    if (failed.length) console.warn('Failed to blacklist:', failed);
  }
}
```

## Tips

- Phone numbers must be in **E.164 format without `+`** — e.g. `972501234567` not `+972501234567` or `0501234567`.
- **Always check per-phone `ErrorCode`** in the response — a top-level `ErrorCode: 0` does not guarantee every number was added successfully.
- The blacklist blocks **outbound dialing**. Inbound call blocking from blacklisted numbers is configured separately in CPanel IVR settings.
- Use chunking (100 numbers per request) for large bulk operations to avoid timeouts.

## Related Skills

- **CDR Notification** — Trigger blacklist add when a caller's status is `OPT_OUT` or presses a specific DTMF
- **Productive Dialer** — Blacklisted numbers are automatically skipped in dialer campaigns
- **Call Log** — Audit which blacklisted numbers were attempted before the block took effect
