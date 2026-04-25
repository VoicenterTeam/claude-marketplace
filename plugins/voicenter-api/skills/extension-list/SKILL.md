---
name: extension-list
description: Retrieve the full list of active extensions and users in a Voicenter organization
---

Help the developer fetch the **Organizational Extension List** — all SIP extensions, their assigned users, speed dials, and departments.

## When to use this skill

Use this skill when the user wants to:
- Populate an agent selector dropdown in a CRM (e.g., "Which extension do you want to call from?")
- Look up a SIP code by agent name or email to use in Click2Call or Login/Logout API calls
- Enrich CDR records — map SIP extension codes to human-readable agent names
- Sync the Voicenter agent roster with an HR or identity system
- Get a list of all departments and their extensions
- Validate that a specific SIP code exists before using it in another API call

## Environment Variables

```env
VOICENTER_API_CODE=your_api_token_here
```

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
| `showAll` | ❌ | `true`/`1` = all extensions in the entire organization. `false`/`0` = only extensions in the department tied to your `code`. Default = all. |

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
| `ERR` | `0` = OK, `1` = invalid code format. An invalid code value returns an empty `EXTENSIONS` array with no error. |
| `DESC` | `"OK"` or `"Unauthorized"` |
| `SIP` | Extension's SIP user code — used as `phone` in Click2Call, `extension` in Call Log, `ExtensionUser` in Login/Logout |
| `Name` | Extension display name (as shown in CPanel) |
| `SpeedDial` | Internal speed dial number |
| `AccountID` | Department ID the extension belongs to |
| `AccountName` | Department name |
| `UserName` | Voicenter user assigned to this extension |
| `UserEmail` | Email of the assigned user |

## TypeScript Implementation

```typescript
const EXTENSIONS_URL = 'https://monitor.voicenter.co.il/Comet/api/GetExtensions';
const CODE = process.env.VOICENTER_API_CODE!;

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

async function getExtensions(showAll = true): Promise<VoicenterExtension[]> {
  const res = await fetch(EXTENSIONS_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ code: CODE, showAll: showAll ? 1 : 0 }),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const data: ExtensionsResponse = await res.json();
  if (data.ERR !== 0) throw new Error(`Extensions error: ${data.DESC}`);
  return data.EXTENSIONS;
}

// Build a SIP → extension lookup map (useful for enriching CDR records)
async function buildExtensionMap(): Promise<Map<string, VoicenterExtension>> {
  const extensions = await getExtensions();
  return new Map(extensions.map(e => [e.SIP, e]));
}

// Populate a Click2Call agent dropdown
async function getAgentDropdownOptions() {
  const extensions = await getExtensions();
  return extensions.map(e => ({
    label: `${e.Name} (${e.SpeedDial}) — ${e.UserName}`,
    value: e.SIP,
  }));
}

// Find extension by user email (e.g. from SSO or CRM login session)
async function findExtensionByEmail(email: string): Promise<VoicenterExtension | undefined> {
  const extensions = await getExtensions();
  return extensions.find(e => e.UserEmail.toLowerCase() === email.toLowerCase());
}
```

## Tips

- **Cache the result** — the extension list changes infrequently. Refresh every 15–30 minutes or on application startup, not on every request.
- `showAll: false` returns only the department tied to your `code` — useful for multi-tenant setups where each department has its own API key.
- `SIP` is the value used as `phone` in Click2Call, `extension` in Call Log filters, and `ExtensionUser` in the Login/Logout API.
- An invalid `code` value returns `ERR: 0` with an empty `EXTENSIONS` array — always check if the array is empty before assuming success.

## Related Skills

- **Click2Call** — Uses `SIP` as the `phone` parameter
- **Login/Logout** — Uses `SIP` as the `ExtensionUser` parameter
- **Active Calls** — Filter by `SIP` as the `extension` parameter to check a specific agent's call state
- **Call Log** — Filter by `SIP` as the `extensions` array parameter
