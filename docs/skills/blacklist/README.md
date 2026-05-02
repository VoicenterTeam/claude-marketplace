# Skill: `blacklist`

Add or remove phone numbers from the Voicenter organization blacklist (Do-Not-Call list for outbound dialing).

> Source: [`plugins/voicenter-api/skills/blacklist/SKILL.md`](../../../plugins/voicenter-api/skills/blacklist/SKILL.md)
> Plugin: [voicenter-api](../../plugins/voicenter-api.md) · Direction: **Outgoing** · Transport: **REST**

---

## When to use this skill

- Block a customer who requested no further calls (DNC / opt-out)
- Sync a CRM opt-out list with the Voicenter dialer blacklist
- Remove a number after a customer withdraws their opt-out
- Prevent specific numbers from being dialed in a campaign
- Automate blacklist updates triggered by CDR events (e.g. opt-out DTMF)

---

## Endpoints

| Action | URL |
|---|---|
| Add numbers | `https://api.voicenter.com/Blacklist/AddBlackList` |
| Remove numbers | `https://api.voicenter.com/Blacklist/RemoveBulkFromBlacklist` |

Both accept `GET` or `POST-JSON`. Response is JSON.

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

## AddBlackList

### POST-JSON

```json
{
  "Code": "XXXXXXXXXXXXXXXXXXXX",
  "Phones": [
    { "Phone": "972501234567", "Name": "John Doe" },
    { "Phone": "97231234567",  "Name": "Walter Melon" }
  ]
}
```

### GET

```
https://api.voicenter.com/Blacklist/AddBlackList?code=XXXX&phones=972501234567&phones=97231234567
```

### Fields

| Field | Required | Description |
|---|---|---|
| `Code` | ✅ | API token |
| `Phones` | ✅ | Array of objects |
| `Phone` | ✅ | E.164 without `+` |
| `Name` | ❌ | Optional label (POST only) |

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

### POST-JSON

```json
{
  "Code": "XXXXXXXXXXXXXXXXXXXX",
  "Phones": [{ "Phone": "972501234567" }, { "Phone": "97231234567" }]
}
```

### GET

```
https://api.voicenter.com/Blacklist/RemoveBulkFromBlacklist?code=XXXX&phones=972501234567&phones=97231234567
```

Response shape mirrors `AddBlackList`.

---

## Error codes

### Top-level

| ErrorCode | Meaning |
|---|---|
| 0 | OK |
| 1 | Invalid or missing `Code` |
| 2 | `Phone` field missing or invalid |

### Per phone

| ErrorCode | Meaning |
|---|---|
| 0 | OK |
| 1 | Phone format invalid — must be E.164 without `+` |
| 2 | Internal error — contact Voicenter support |

> A top-level `ErrorCode: 0` does **not** mean every number was added. Always inspect the per-phone array.

---

## TypeScript implementation

```typescript
const BL_BASE = 'https://api.voicenter.com/Blacklist';
const CODE = process.env.VOICENTER_API_CODE!;

interface BlacklistPhone { Phone: string; Name?: string; }
interface BlacklistPhoneResult { ErrorCode: number; ErrorMessage: string; Phone: string; }
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

---

## Patterns

### Auto-blacklist on opt-out DTMF

In your [CDR Notification](../cdr-notification/README.md) handler, inspect `IVR[].Dtmf` for the opt-out digit and call `addToBlacklist`:

```typescript
const optedOut = cdr.IVR?.some(layer => layer.Dtmf === 9);
if (optedOut) {
  await addToBlacklist([{ Phone: cdr.caller, Name: 'Opted out via DTMF' }]);
}
```

---

## Tips & best practices

- Always send phone numbers in **E.164 without `+`** — `972501234567`.
- **Always inspect per-phone `ErrorCode`** — a top-level `0` does not guarantee every entry succeeded.
- The blacklist blocks **outbound dialing** only. To block inbound calls from blacklisted numbers, configure CPanel IVR settings.
- Chunk large bulk operations to ≤ 100 numbers per request to avoid timeouts.
- Store an audit trail of who added what, when, and why — Voicenter does not.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `ErrorCode: 1` top-level | Wrong/missing `Code` | Verify token, check casing (`Code` not `code`) |
| All phones return per-phone `ErrorCode: 1` | Wrong number format | Convert to E.164 without `+` |
| `403` | IP not whitelisted | Add IP in CPanel |

---

## Related skills

- [CDR Notification](../cdr-notification/README.md) — trigger blacklist add on opt-out DTMF
- [Productive Dialer](../productive-dialer/README.md) — blacklisted numbers are skipped automatically
- [Call Log](../call-log/README.md) — audit which blacklisted numbers were attempted before the block
