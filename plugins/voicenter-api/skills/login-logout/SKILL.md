---
description: Set agent login/logout and status via the Voicenter Login/Logout API
---

Help the developer integrate **agent status management** — log agents in/out and set their work status (Login, Logout, Lunch, etc.) directly from their CRM or HR system.

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
| `UserId` | ✅ | Voicenter user ID (from CPanel or Extension List API) |
| `ExtensionUser` | ✅ | SIP code of the extension to log into (from Extension List API) |
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
  "ExtensionUser": "sipsip",
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
| `Status` | `1` = success, `2` = invalid Code or UserId, `3` = invalid Extension, `4` = status not supported or extension invalid |
| `StatusError` | `0` = request format error, `1` = success, `4` = internal error, `6` = missing parameters |
| `StatusErroMessage` | Human-readable: `"OK"`, `"Authorization Failed"`, `"No extension found"`, `"Extension is already in use"`, `"Status not support"`, `"Error on update"` |

## TypeScript Implementation

```typescript
const LOGIN_URL = 'https://api.voicenter.com/UserLogin/SetStatusFromAPI';

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
  code: string,
  userId: string,
  extensionUser: string,
  status: AgentStatusCode
): Promise<LoginResponse> {
  const res = await fetch(LOGIN_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ Code: code, UserId: userId, ExtensionUser: extensionUser, Status: status }),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const data: LoginResponse = await res.json();
  if (data.Status !== 1) throw new Error(`Login API: ${data.StatusErroMessage}`);
  return data;
}

// Login agent at shift start
await setAgentStatus('MY_CODE', '123456789', 'SIPSIP1', AgentStatus.LOGIN);

// Set lunch break
await setAgentStatus('MY_CODE', '123456789', 'SIPSIP1', AgentStatus.LUNCH);

// Logout at shift end
await setAgentStatus('MY_CODE', '123456789', 'SIPSIP1', AgentStatus.LOGOUT);
```

## CRM Integration Pattern

```typescript
// Shift start: agent clicks "Start Shift" in CRM
async function onShiftStart(crmUser: { voicenterId: string; extension: string }) {
  await setAgentStatus(API_CODE, crmUser.voicenterId, crmUser.extension, AgentStatus.LOGIN);
  // Record shift start in CRM
  await crm.shiftLog.create({ userId: crmUser.voicenterId, type: 'login', time: new Date() });
}

// Break: agent clicks "Take Break"
async function onBreak(crmUser: { voicenterId: string; extension: string }, breakType: 'lunch' | 'other') {
  const status = breakType === 'lunch' ? AgentStatus.LUNCH : AgentStatus.OTHER;
  await setAgentStatus(API_CODE, crmUser.voicenterId, crmUser.extension, status);
}

// Auto-logout when CRM session expires
async function onSessionTimeout(crmUser: { voicenterId: string; extension: string }) {
  await setAgentStatus(API_CODE, crmUser.voicenterId, crmUser.extension, AgentStatus.LOGOUT);
}
```

## Tips

- Get `UserId` and valid `ExtensionUser` (SIP) values from the **Organizational Extension List API** — `ExtensionUser` = `SIP` field, `UserId` is provided by Voicenter support or visible in CPanel.
- `"Extension is already in use"` means another user is already logged into that extension. Logout the current user first or choose a different extension.
- Pair with the **Real-Time API** `userStatusUpdate` event to confirm the status change propagated.
- This API is designed for CRM-driven workforce management — replaces manual agent login in the Voicenter softphone.
