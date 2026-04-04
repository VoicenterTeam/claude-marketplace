---
description: List and search extensions and agents in a Voicenter account
---

Help the developer **list, search, and inspect extensions** (agents) in their Voicenter account.

## API

**Endpoint:** `GET https://api.voicenter.com/v2/users/extensions`

**Query parameters:**

| Parameter | Description |
|---|---|
| `status` | `active` \| `inactive` \| `all` (default: `all`) |
| `search` | Partial name or extension number search |
| `page` / `pageSize` | Pagination |

**Response record:**
```json
{
  "extensionId": "ext-101",
  "extension": "1001",
  "name": "John Doe",
  "email": "[email protected]",
  "status": "active",
  "presence": "available",
  "did": "+972031234567",
  "groups": ["sales", "support"]
}
```

## Example — TypeScript

```typescript
interface Extension {
  extensionId: string;
  extension: string;
  name: string;
  email: string;
  status: 'active' | 'inactive';
  presence: 'available' | 'busy' | 'away' | 'offline';
  did?: string;
  groups: string[];
}

async function listExtensions(token: string, status: 'active' | 'all' = 'active'): Promise<Extension[]> {
  const res = await fetch(`https://api.voicenter.com/v2/users/extensions?status=${status}&pageSize=200`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error(`Extensions fetch failed: ${res.status}`);
  const { records } = await res.json();
  return records;
}

// Find available agents for routing
async function getAvailableAgents(token: string): Promise<Extension[]> {
  const all = await listExtensions(token, 'active');
  return all.filter(ext => ext.presence === 'available');
}
```

## Example — Python

```python
def list_extensions(token, status="active"):
    r = requests.get(
        "https://api.voicenter.com/v2/users/extensions",
        headers={"Authorization": f"Bearer {token}"},
        params={"status": status, "pageSize": 200}
    )
    r.raise_for_status()
    return r.json()["records"]
```

## Common use cases

- **Click-to-call widget**: populate a dropdown of available agents from this list.
- **Agent status dashboard**: poll `presence` field every 30s to show real-time availability.
- **Routing logic**: pick the least-busy agent from the `available` list before calling `/call/click2call`.
