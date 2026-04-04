---
description: Add or remove phone numbers from the Voicenter organization blacklist
---

Help the developer manage the **Voicenter Blacklist** — block numbers from being dialed by agents or dialers, and remove them when needed.

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
    { "Phone": "0501234567", "Name": "John Doe" },
    { "Phone": "031234567",  "Name": "Walter Melon" }
  ]
}
```

| Field | Required | Description |
|---|---|---|
| `Code` | ✅ | API authentication token |
| `Phones` | ✅ | Array of phone objects to block |
| `Phone` | ✅ | Phone number in E.164 format (international, without `+`) |
| `Name` | ❌ | Label for this blocked number (POST-only) |

### GET Request

```
https://api.voicenter.com/Blacklist/AddBlackList?code=XXXX&phones=0501234567&phones=031234567
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
    { "Phone": "0501234567" },
    { "Phone": "031234567" }
  ]
}
```

### GET Request

```
https://api.voicenter.com/Blacklist/RemoveBulkFromBlacklist?code=XXXX&phones=0501234567&phones=031234567
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
| 1 | Phone number format invalid — use E.164 (e.g. `972501234567`) |
| 2 | Internal error — contact Voicenter support |

---

## TypeScript Implementation

```typescript
const BL_BASE = 'https://api.voicenter.com/Blacklist';

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

async function addToBlacklist(
  code: string,
  phones: BlacklistPhone[]
): Promise<BlacklistResponse> {
  const res = await fetch(`${BL_BASE}/AddBlackList`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ Code: code, Phones: phones }),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const data: BlacklistResponse = await res.json();
  if (data.ErrorCode !== 0) throw new Error(`Blacklist error: ${data.ErrorMessage}`);
  return data;
}

async function removeFromBlacklist(
  code: string,
  phones: string[]
): Promise<BlacklistResponse> {
  const res = await fetch(`${BL_BASE}/RemoveBulkFromBlacklist`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ Code: code, Phones: phones.map(p => ({ Phone: p })) }),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

// Add numbers
await addToBlacklist('MY_CODE', [
  { Phone: '972501234567', Name: 'Do Not Call' },
  { Phone: '972031234567' },
]);

// Remove numbers
await removeFromBlacklist('MY_CODE', ['972501234567', '972031234567']);

// Bulk add from CRM opt-out list
async function syncOptOuts(code: string, optOutList: string[]) {
  const CHUNK = 100;
  for (let i = 0; i < optOutList.length; i += CHUNK) {
    const chunk = optOutList.slice(i, i + CHUNK).map(p => ({ Phone: p }));
    const result = await addToBlacklist(code, chunk);
    const failed = result.Phones.filter(p => p.ErrorCode !== 0);
    if (failed.length) console.warn('Failed to blacklist:', failed);
  }
}
```

## Tips

- Phone numbers must be in **E.164 format without `+`** — e.g. `972501234567` not `+972501234567` or `0501234567`.
- Check per-phone `ErrorCode` in the response — a top-level `ErrorCode: 0` does not guarantee every number was added successfully.
- Use this in combination with the CDR Notification API: when a customer's SMS/call status is `OPT_OUT`, automatically add them to the blacklist.
- The blacklist blocks outbound dialing. Inbound calls from blacklisted numbers are handled separately via IVR configuration in CPanel.
