# Skill: `extension-list`

Retrieve the full list of active extensions and users in a Voicenter organization.

> Source: [`plugins/voicenter-api/skills/extension-list/SKILL.md`](../../../plugins/voicenter-api/skills/extension-list/SKILL.md)
> Plugin: [voicenter-api](../../plugins/voicenter-api.md) · Direction: **In/Out** · Transport: **REST**

---

> **Language.** Reply in the user's language: detect what they write — Hebrew→Hebrew, English→English — and mirror it, switching if they switch mid-conversation. This shapes your prose, your questions, and your `AskUserQuestion` option labels only. It does **not** change the artifacts you produce — identifiers, JSON keys, BCP-47 language codes, API field names, and other data stay exactly as specified.

## When to use this skill

- Populate an agent selector dropdown ("Which extension do you want to call from?")
- Look up a SIP code by agent name or email for [Click2Call](../click2call/README.md) / [Login/Logout](../login-logout/README.md)
- Enrich CDR records — map SIP codes to human-readable agent names
- Sync the Voicenter agent roster with HR / IDP
- Get all departments and their extensions
- Validate that a specific SIP code exists before using it elsewhere

---

## Endpoint

```
POST https://monitor.voicenter.co.il/Comet/api/GetExtensions
GET  https://monitor.voicenter.co.il/Comet/api/GetExtensions?...
```

Response is JSON.

---

## Authentication

| Field | Notes |
|---|---|
| `code` | Lowercase. Body or query. |
| Server IP | Must be whitelisted in CPanel → API Settings. |

```env
VOICENTER_API_CODE=your_api_token_here
```

---

## Request

| Field | Required | Description |
|---|---|---|
| `code` | ✅ | API token |
| `showAll` | ❌ | `1` = entire organization (default). `0` = only the department tied to your `code`. |

### POST-JSON

```json
{ "code": "XXXXXXXXXXXXXXX", "showAll": 1 }
```

### GET

```
https://monitor.voicenter.co.il/Comet/api/GetExtensions?code=XXXXXXXXXXXXXXX&showAll=1
```

---

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
    }
  ]
}
```

### Fields

| Field | Description |
|---|---|
| `ERR` | `0` OK, `1` invalid code format. **Invalid code value returns `ERR: 0` with empty `EXTENSIONS`.** |
| `DESC` | `"OK"` or `"Unauthorized"` |
| `SIP` | SIP code — used as `phone` in Click2Call, `extension` in Call Log, `ExtensionUser` in Login/Logout, `Member` in Productive Dialer |
| `Name` | Display name |
| `SpeedDial` | Internal short number |
| `AccountID` / `AccountName` | Department owning this extension |
| `UserName` / `UserEmail` | Voicenter user assigned |

---

## TypeScript implementation

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

// Build a SIP → extension lookup map
async function buildExtensionMap(): Promise<Map<string, VoicenterExtension>> {
  const list = await getExtensions();
  return new Map(list.map(e => [e.SIP, e]));
}

// Populate a Click2Call agent dropdown
async function getAgentDropdownOptions() {
  const list = await getExtensions();
  return list.map(e => ({
    label: `${e.Name} (${e.SpeedDial}) — ${e.UserName}`,
    value: e.SIP,
  }));
}

// Find by user email (e.g. SSO email)
async function findExtensionByEmail(email: string) {
  const list = await getExtensions();
  return list.find(e => e.UserEmail.toLowerCase() === email.toLowerCase());
}
```

---

## Tips & best practices

- **Cache the result** for 15–30 minutes. The roster changes infrequently.
- `showAll: 0` returns only the department tied to your `code` — useful for multi-tenant integrations where each department has its own token.
- An invalid `code` value returns `ERR: 0` with an **empty** `EXTENSIONS` array — always check for empty results before assuming success.
- The `SIP` field is the lingua franca across the marketplace — every other skill uses it under different parameter names.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Empty `EXTENSIONS` with `ERR: 0` | Wrong `code` value | Verify the org token |
| `403` | IP not whitelisted | Add IP in CPanel |
| `ERR: 1` | Malformed `code` | Check casing and length |

---

## Related skills

- [Click2Call](../click2call/README.md) — uses `SIP` as `phone`
- [Login/Logout](../login-logout/README.md) — uses `SIP` as `ExtensionUser`
- [Active Calls](../active-calls/README.md) — filters by `SIP` as `extension`
- [Call Log](../call-log/README.md) — `extensions` filter takes an array of `SIP` codes
- [Productive Dialer](../productive-dialer/README.md) — `Member` adds an agent by `SIP`
