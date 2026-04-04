---
description: Initiate a click-to-call via the Voicenter API
---

Help the developer implement a **click-to-call** feature using the Voicenter API.

## What to do

1. Ask which language/framework they are working in if not clear from context.
2. Show the correct API call using their environment.
3. Cover authentication, required parameters, and error handling.
4. Offer to integrate it into their existing code.

## Voicenter Click-to-Call API

**Endpoint:** `POST https://api.voicenter.com/v2/call/click2call`

**Authentication:** Bearer token in the `Authorization` header.  
The token is obtained from `POST /v2/auth/token` using `{ "username": "...", "password": "...", "accountId": "..." }`.

**Request body:**
```json
{
  "src": "CALLER_EXTENSION_OR_DID",
  "dst": "DESTINATION_NUMBER",
  "callerId": "OPTIONAL_CALLER_ID_TO_PRESENT",
  "accountId": "ACCOUNT_ID"
}
```

**Response (200):**
```json
{
  "callId": "unique-call-id",
  "status": "initiated"
}
```

**Common errors:**
- `401` — invalid or expired token → re-authenticate
- `400` — missing `src` or `dst`
- `403` — the extension is not permitted to call that destination

## Example — Node.js / TypeScript

```typescript
const VOICENTER_API = 'https://api.voicenter.com/v2';

async function getToken(username: string, password: string, accountId: string): Promise<string> {
  const res = await fetch(`${VOICENTER_API}/auth/token`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password, accountId }),
  });
  const data = await res.json();
  return data.token;
}

async function clickToCall(token: string, src: string, dst: string, accountId: string) {
  const res = await fetch(`${VOICENTER_API}/call/click2call`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify({ src, dst, accountId }),
  });
  if (!res.ok) throw new Error(`Call failed: ${res.status} ${await res.text()}`);
  return res.json(); // { callId, status }
}
```

## Example — Python

```python
import requests

VOICENTER_API = "https://api.voicenter.com/v2"

def get_token(username, password, account_id):
    r = requests.post(f"{VOICENTER_API}/auth/token", json={
        "username": username, "password": password, "accountId": account_id
    })
    r.raise_for_status()
    return r.json()["token"]

def click_to_call(token, src, dst, account_id):
    r = requests.post(f"{VOICENTER_API}/call/click2call",
        headers={"Authorization": f"Bearer {token}"},
        json={"src": src, "dst": dst, "accountId": account_id}
    )
    r.raise_for_status()
    return r.json()  # {"callId": ..., "status": "initiated"}
```

## Best practices

- Store credentials in environment variables, never in source code.
- Cache the token and refresh it when you receive a `401`.
- Log the returned `callId` so you can correlate call events from webhooks later.
- Use the `voicenter-webhooks` plugin to listen for `call.answered` and `call.ended` events tied to the same `callId`.
