# Skill: `login-logout`

Set agent login/logout and work status via the Voicenter Login/Logout API.

> Source: [`plugins/voicenter-api/skills/login-logout/SKILL.md`](../../../plugins/voicenter-api/skills/login-logout/SKILL.md)
> Plugin: [voicenter-api](../../plugins/voicenter-api.md) · Direction: **In/Out** · Transport: **REST**

---

## When to use this skill

- Log an agent in to Voicenter when they start their shift in the CRM
- Log an agent out when their CRM session expires or they end their shift
- Set "Lunch" / "Break" status without using the Voicenter softphone
- Automate agent status from a calendar or workforce management tool
- Build a custom "Ready / Not Ready" toggle
- Sync agent state between CRM/HR and Voicenter

---

## Endpoint

```
POST https://api.voicenter.com/UserLogin/SetStatusFromAPI
GET  https://api.voicenter.com/UserLogin/SetStatusFromAPI?...
```

Response is JSON.

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

## Request fields

| Field | Required | Description |
|---|---|---|
| `Code` | ✅ | API token |
| `UserId` | ✅ | Voicenter user ID (from CPanel or Voicenter support) |
| `ExtensionUser` | ✅ | SIP code from [Extension List](../extension-list/README.md) |
| `Status` | ✅ | Status code (see table) |

### Status codes

| Code | Status | Typical use |
|---|---|---|
| 1 | Login | Start of shift |
| 2 | Logout | End of shift |
| 3 | Lunch | Lunch break |
| 5 | Administrative | Admin work, not on calls |
| 7 | Private | Personal time |
| 9 | Other | Custom unavailable state |
| 11 | Training | In training |
| 12 | Team meeting | In a team meeting |
| 13 | Brief | In a briefing |

> Status names are customizable in CPanel.

### POST-JSON

```json
{
  "Code": "XXXXXXXXXXX",
  "UserId": "123456789",
  "ExtensionUser": "SIPSIP1",
  "Status": 1
}
```

### GET

```
https://api.voicenter.com/UserLogin/SetStatusFromAPI?Code=XXXXXXXX&UserId=123456789&ExtensionUser=SIPSIP&Status=1
```

---

## Response

```json
{ "Status": 1, "StatusError": 1, "StatusErroMessage": "OK" }
```

| Field | Notes |
|---|---|
| `Status` | `1` success, `2` invalid `Code`/`UserId`, `3` invalid extension, `4` status not supported |
| `StatusError` | `0` request format error, `1` success, `4` internal error, `6` missing parameters |
| `StatusErroMessage` | `"OK"`, `"Authorization Failed"`, `"No extension found"`, `"Extension is already in use"`, `"Status not support"`, `"Error on update"` |

> The field is intentionally spelled `StatusErroMessage` (not `StatusErrorMessage`) — match exactly.

---

## TypeScript implementation

```typescript
const LOGIN_URL = 'https://api.voicenter.com/UserLogin/SetStatusFromAPI';
const CODE = process.env.VOICENTER_API_CODE!;

interface LoginResponse {
  Status: number;
  StatusError: number;
  StatusErroMessage: string;
}

const AgentStatus = {
  LOGIN: 1, LOGOUT: 2, LUNCH: 3, ADMINISTRATIVE: 5,
  PRIVATE: 7, OTHER: 9, TRAINING: 11, TEAM_MEETING: 12, BRIEF: 13,
} as const;

type AgentStatusCode = typeof AgentStatus[keyof typeof AgentStatus];

async function setAgentStatus(
  userId: string,
  extensionUser: string,
  status: AgentStatusCode
): Promise<LoginResponse> {
  const res = await fetch(LOGIN_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ Code: CODE, UserId: userId, ExtensionUser: extensionUser, Status: status }),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const data: LoginResponse = await res.json();
  if (data.Status !== 1) throw new Error(`Login API: ${data.StatusErroMessage}`);
  return data;
}
```

### CRM patterns

```typescript
async function onShiftStart(agent: { voicenterId: string; extension: string }) {
  await setAgentStatus(agent.voicenterId, agent.extension, AgentStatus.LOGIN);
}

async function onLunchBreak(agent: { voicenterId: string; extension: string }) {
  await setAgentStatus(agent.voicenterId, agent.extension, AgentStatus.LUNCH);
}

async function onSessionTimeout(agent: { voicenterId: string; extension: string }) {
  await setAgentStatus(agent.voicenterId, agent.extension, AgentStatus.LOGOUT);
}
```

---

## Tips & best practices

- Get `UserId` values from CPanel → Users or from Voicenter support.
- `ExtensionUser` is the `SIP` field from the [Extension List](../extension-list/README.md) API.
- **"Extension is already in use"** = another user is logged into that extension. Log out the current user first or pick a different extension.
- Pair with the [Real-Time API](../real-time/README.md) `userStatusUpdate` event to confirm the change propagated and to update your UI.
- Note the typo: `StatusErroMessage` (intentional in the API).

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `Status: 2` | Bad `Code` or `UserId` | Verify token and `UserId` |
| `Status: 3` | Wrong `ExtensionUser` | Resolve via Extension List |
| `"Extension is already in use"` | Someone else is on it | Log them out first or switch SIP |
| UI does not reflect change | Polling vs reality | Subscribe to Real-Time `userStatusUpdate` |

---

## Related skills

- [Extension List](../extension-list/README.md) — get valid `SIP` codes for `ExtensionUser`
- [Real-Time](../real-time/README.md) — `userStatusUpdate` confirms the change
- [Active Calls](../active-calls/README.md) — `onlineUserStatus` shows the current state without calling this API
