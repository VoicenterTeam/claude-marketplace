---
description: Create, update, and manage agents and users in Voicenter
---

Help the developer **create or update agents and users** via the Voicenter API — useful for CRM sync, onboarding automation, and HR integrations.

## Create an agent

**Endpoint:** `POST https://api.voicenter.com/v2/users/extensions`

```json
{
  "name": "Jane Smith",
  "email": "[email protected]",
  "extension": "1042",
  "password": "secure-password",
  "groups": ["sales"],
  "did": "+972031234999"
}
```

**Response:** the created `Extension` object with `extensionId`.

## Update an agent

**Endpoint:** `PATCH https://api.voicenter.com/v2/users/extensions/{extensionId}`

Send only the fields to change:
```json
{ "groups": ["sales", "vip-support"], "status": "active" }
```

## Deactivate an agent

**Endpoint:** `DELETE https://api.voicenter.com/v2/users/extensions/{extensionId}`

This deactivates the extension — the agent can no longer log in or receive calls.

## Example — TypeScript (CRM sync)

```typescript
interface CreateExtensionPayload {
  name: string;
  email: string;
  extension: string;
  password: string;
  groups?: string[];
}

async function createExtension(token: string, payload: CreateExtensionPayload) {
  const res = await fetch('https://api.voicenter.com/v2/users/extensions', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(`Create extension failed: ${res.status} ${await res.text()}`);
  return res.json();
}

// Sync a new employee from your HR system
async function onboardEmployee(token: string, employee: { name: string; email: string }) {
  const extension = String(Math.floor(Math.random() * 900) + 100); // assign ext 100–999
  return createExtension(token, {
    name: employee.name,
    email: employee.email,
    extension,
    password: crypto.randomUUID().slice(0, 12),
    groups: ['general'],
  });
}
```

## Tips

- Extensions must be unique within the account — check for conflicts with `GET /v2/users/extensions?search=1042` before creating.
- Use the `groups` field to control which queues and IVR options the agent belongs to.
- When deactivating, consider archiving any open tickets in your CRM first.
