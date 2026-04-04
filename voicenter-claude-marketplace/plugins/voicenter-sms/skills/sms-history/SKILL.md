---
description: Query sent and received SMS history from Voicenter
---

Help the developer retrieve **SMS message history** — sent messages, received replies, delivery statuses, and opt-outs.

## API

**Endpoint:** `GET https://api.voicenter.com/v2/sms/history`

**Query parameters:**

| Parameter | Description |
|---|---|
| `startDate` | ISO 8601 start date |
| `endDate` | ISO 8601 end date |
| `direction` | `outbound` \| `inbound` |
| `status` | `delivered` \| `failed` \| `pending` |
| `from` | Filter by sender ID |
| `to` | Filter by recipient number |
| `page` / `pageSize` | Pagination (max 200 per page) |

**Response record:**
```json
{
  "messageId": "sms-uuid",
  "from": "MyApp",
  "to": "+972501234567",
  "text": "Your order is ready",
  "direction": "outbound",
  "status": "delivered",
  "sentAt": "2024-06-01T10:00:00Z",
  "deliveredAt": "2024-06-01T10:00:03Z",
  "segments": 1
}
```

## Example — TypeScript

```typescript
async function getSmsHistory(
  token: string,
  filters: { startDate: string; endDate: string; direction?: 'inbound' | 'outbound' }
) {
  const params = new URLSearchParams({
    startDate: filters.startDate,
    endDate: filters.endDate,
    ...(filters.direction ? { direction: filters.direction } : {}),
  });
  const res = await fetch(`https://api.voicenter.com/v2/sms/history?${params}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error(`SMS history failed: ${res.status}`);
  return res.json();
}

// Get inbound messages (replies / opt-outs)
const replies = await getSmsHistory(token, {
  startDate: '2024-06-01T00:00:00Z',
  endDate: '2024-06-30T23:59:59Z',
  direction: 'inbound',
});
```

## Checking delivery rates

```typescript
async function getDeliveryStats(token: string, startDate: string, endDate: string) {
  const { records } = await getSmsHistory(token, { startDate, endDate, direction: 'outbound' });
  const total = records.length;
  const delivered = records.filter((r: any) => r.status === 'delivered').length;
  return { total, delivered, rate: total ? `${((delivered / total) * 100).toFixed(1)}%` : 'N/A' };
}
```
