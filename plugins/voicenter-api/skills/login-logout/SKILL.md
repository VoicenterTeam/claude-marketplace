---
description: Set agent login/logout and status via the Voicenter Login/Logout API
---

Help the developer integrate **agent status management** — log agents in/out and set their work status (Login, Logout, Lunch, etc.) directly from a CRM, HR system, or workforce management tool.

## When to use this skill

Use this skill when the user wants to:
- Log an agent in to Voicenter automatically when they start their shift in the CRM
- Log an agent out when their CRM session expires or they click "End Shift"
- Set an agent to "Lunch" or "Break" status from the CRM without using the Voicenter softphone
- Automate agent status based on calendar, schedule, or workforce management rules
- Build a "Ready/Not Ready" toggle in a custom agent dashboard
- Sync agent states between their CRM/HR system and Voicenter

## Environment Variables

```env
VOICENTER_API_CODE=your_api_token_here
```

## Endpoint

```
https://api.voicenter.com/UserLogin/SetStatusFromAPI
```

Accepts: `GET` or `POST-JSON`
Response: `JSON`

## Authentication

`Code` field in the request body (your API token from Voicenter back office).

## Request Parameters

| Field | Required | Description |
|---|---|---|
| `Code` | ✅ | API authentication token |
| `UserId` | ✅ | Voicenter user ID (from CPanel or provided by Voicenter support) |
| `ExtensionUser` | ✅ | SIP code of the extension to log into — use `SIP` field from Extension List API |
| `Status` | ✅ | Status code (see table below) |

### Status Codes

| Code | Status | Typical use |
|---|---|---|
| 1 | Login | Start of shift — agent is ready to take calls |
| 2 | Logout | End of shift — agent goes offline |
| 3 | Lunch | Agent on lunch break |
| 5 | Administrative | Agent doing admin work, not taking calls |
| 7 | Private | Personal time |
| 9 | Other | Custom unavailable state |
| 11 | Training | Agent in training |
| 12 | Team meeting | Agent in a team meeting |
| 13 | Brief | Agent in a briefing |

*Status names can be customized in the Voicenter CPanel.*

## GET Request

```
https://api.voicenter.com/UserLogin/SetStatusFromAPI?Code=XXXXXXXX&UserId=123456789&ExtensionUser=SIPSIP&Status=1
```

## POST-JSON Request

```json
{
  "Code": "XXXXXXXXXXX",
  "UserId": "123456789",
  "ExtensionUser": "SIPSIP1",
  "Status": 1
}
```

## Response

```json
{
  "Status": 1,
  "StatusError": 1,
  "StatusErroMessage": "OK"
}
```

| Field | Description |
|---|---|
| `Status` | `1` = success, `2` = invalid Code or UserId, `3` = invalid Extension, `4` = status not supported |
| `StatusError` | `0` = request format error, `1` = success, `4` = internal error, `6` = missing parameters |
| `StatusErroMessage` | `"OK"`, `"Authorization Failed"`, `"No extension found"`, `"Extension is already in use"`, `"Status not support"`, `"Error on update"` |

## TypeScript Implementation

```typescript
const LOGIN_URL = 'https://api.voicenter.com/UserLogin/SetStatusFromAPI';
const CODE = process.env.VOICENTER_API_CODE!;

interface LoginResponse {
  Status: number;
  StatusError: number;
  StatusErroMessage: string;
}

const AgentStatus = {
  LOGIN: 1,
  LOGOUT: 2,
  LUNCH: 3,
  ADMINISTRATIVE: 5,
  PRIVATE: 7,
  OTHER: 9,
  TRAINING: 11,
  TEAM_MEETING: 12,
  BRIEF: 13,
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

## CRM Integration Pattern

```typescript
// Agent clicks "Start Shift" in CRM
async function onShiftStart(agent: { voicenterId: string; extension: string }) {
  await setAgentStatus(agent.voicenterId, agent.extension, AgentStatus.LOGIN);
  await crm.shiftLog.create({ userId: agent.voicenterId, type: 'login', time: new Date() });
}

// Agent clicks "Take Lunch"
async function onLunchBreak(agent: { voicenterId: string; extension: string }) {
  await setAgentStatus(agent.voicenterId, agent.extension, AgentStatus.LUNCH);
}

// CRM session expires → auto logout
async function onSessionTimeout(agent: { voicenterId: string; extension: string }) {
  await setAgentStatus(agent.voicenterId, agent.extension, AgentStatus.LOGOUT);
}
```

## Tips

- Get `UserId` values from Voicenter support or from CPanel → Users. `ExtensionUser` (SIP code) comes from the **Extension List API**.
- **`"Extension is already in use"`** means another user is already logged into that extension. Log out the current user first, or choose a different extension.
- Pair with the **Real-Time API** `userStatusUpdate` event to confirm the status change propagated and update your UI.
- Note the typo in the API response field name: `StatusErroMessage` (not `StatusErrorMessage`) — this is intentional in the API.

## Related Skills

- **Extension List** — Get valid `SIP` codes to use as `ExtensionUser`
- **Real-Time API** — Listen to `userStatusUpdate` events to confirm and reflect status changes in your UI
- **Active Calls** — Check `onlineUserStatus` field to see the current agent status without calling this API
