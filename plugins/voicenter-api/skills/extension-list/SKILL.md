---
description: Retrieve the full list of active extensions and users in a Voicenter organization
---

Help the developer fetch the **Organizational Extension List** — all SIP extensions, their assigned users, speed dials, and departments.

## Endpoint

```
https://monitor.voicenter.co.il/Comet/api/GetExtensions
```

Accepts: `GET` or `POST-JSON`
Response: `JSON`

## Authentication

`code` field in the request body (your API token from Voicenter back office).

## Request Parameters

| Field | Required | Description |
|---|---|---|
| `code` | ✅ | API authentication token |
| `showAll` | ❌ | `true`/`1` = all extensions in the entire organization. `false`/`0` = extensions in the department the `code` belongs to. Default = all. |

### GET Request

```
https://monitor.voicenter.co.il/Comet/api/GetExtensions?code=XXXXXXXXXXXXXXX&showAll=1
```

### POST-JSON Request

```json
{
  "code": "XXXXXXXXXXXXXXX",
  "showAll": 1
}
```

## Response

```json
{
  "ERR": 0,
  "DESC": "OK",
  "EXTENSIONS": [
    {
      "SIP": "SIPSIP1",
      "Name": "Extension 1",
      "SpeedDial": "11",
      "AccountID": 12345678,
      "AccountName": "Voicenter Account",
      "UserName": "John Doe",
      "UserEmail": "[email protected]"
    },
    {
      "SIP": "SIPSIP2",
      "Name": "Extension 2",
      "SpeedDial": "12",
      "AccountID": 12345679,
      "AccountName": "Sales Department",
      "UserName": "Walter Melon",
      "UserEmail": "[email protected]"
    }
  ]
}
```

### Response Fields

| Field | Description |
|---|---|
| `ERR` | `0` = OK, `1` = invalid code format. An invalid code value returns an empty `EXTENSIONS` array. |
| `DESC` | `"OK"` or `"Unauthorized"` |
| `SIP` | Extension's SIP user code — used as `phone` in Click2Call, `extension` in Call Log, etc. |
| `Name` | Extension display name (as shown in CPanel) |
| `SpeedDial` | Internal speed dial number |
| `AccountID` | Department ID the extension belongs to |
| `AccountName` | Department name |
| `UserName` | Voicenter user assigned to this extension |
| `UserEmail` | Email of the assigned user |

## TypeScript Implementation

```typescript
const EXTENSIONS_URL = 'https://monitor.voicenter.co.il/Comet/api/GetExtensions';

interface VoicenterExtension {
  SIP: string;
  Name: string;
  SpeedDial: string;
  AccountID: number;
  AccountName: string;
  UserName: string;
  UserEmail: string;
}

interface ExtensionsResponse {
  ERR: number;
  DESC: string;
  EXTENSIONS: VoicenterExtension[];
}

async function getExtensions(code: string, showAll = true): Promise<VoicenterExtension[]> {
  const res = await fetch(EXTENSIONS_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ code, showAll: showAll ? 1 : 0 }),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const data: ExtensionsResponse = await res.json();
  if (data.ERR !== 0) throw new Error(`Extensions error: ${data.DESC}`);
  return data.EXTENSIONS;
}

// Build a SIP → user lookup map (useful for decorating CDR records)
async function buildExtensionMap(code: string): Promise<Map<string, VoicenterExtension>> {
  const extensions = await getExtensions(code);
  return new Map(extensions.map(e => [e.SIP, e]));
}

// Populate a Click2Call dropdown in your CRM
async function getExtensionDropdownOptions(code: string) {
  const extensions = await getExtensions(code);
  return extensions.map(e => ({
    label: `${e.Name} (${e.SpeedDial}) — ${e.UserName}`,
    value: e.SIP,
  }));
}

// Find extension by user email (e.g. from SSO/CRM login)
async function findExtensionByEmail(code: string, email: string): Promise<VoicenterExtension | undefined> {
  const extensions = await getExtensions(code);
  return extensions.find(e => e.UserEmail.toLowerCase() === email.toLowerCase());
}
```

## Common Use Cases

- **Click2Call dropdown** — Populate an agent selector so users can choose which extension to call from.
- **CDR enrichment** — Map `CallerExtension` / `TargetExtension` SIP codes from Call Log to human-readable names.
- **Login/Logout integration** — Pair with the Login/Logout API: list extensions so agents can choose which one to log into at shift start.
- **Agent roster sync** — Compare your HR system's employee list against Voicenter extensions to detect discrepancies.

## Tips

- Cache the extension list — it changes infrequently. Refresh every 15–30 minutes or on-demand.
- `showAll: false` returns only the department tied to your `code` — useful for multi-tenant setups where each department has its own code.
- `SIP` is the value used as `phone` in Click2Call, as `extension` in Call Log filters, and as `ExtensionUser` in Login/Logout API.
