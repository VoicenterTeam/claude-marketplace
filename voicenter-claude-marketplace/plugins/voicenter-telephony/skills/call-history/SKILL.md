---
description: Query call history and CDR records from Voicenter
---

Help the developer retrieve **call history (CDR)** from the Voicenter API and work with the data.

## What to do

1. Understand what they need: all calls, calls for a specific agent/extension, date range, or a single call by ID.
2. Build the correct request with filtering and pagination.
3. Offer to parse or display the result in a useful format.

## Voicenter Call History API

**Endpoint:** `GET https://api.voicenter.com/v2/reports/cdr`

**Authentication:** Bearer token (`Authorization: Bearer <token>`).

**Query parameters:**

| Parameter | Type | Description |
|---|---|---|
| `startDate` | string (ISO 8601) | Filter from date, e.g. `2024-01-01T00:00:00Z` |
| `endDate` | string (ISO 8601) | Filter to date |
| `extension` | string | Filter by agent extension |
| `direction` | `inbound` \| `outbound` | Call direction |
| `page` | number | Page number (default 1) |
| `pageSize` | number | Results per page (default 50, max 200) |

**Response:**
```json
{
  "total": 1234,
  "page": 1,
  "pageSize": 50,
  "records": [
    {
      "callId": "abc-123",
      "startTime": "2024-06-01T09:00:00Z",
      "endTime": "2024-06-01T09:04:30Z",
      "duration": 270,
      "src": "1001",
      "dst": "+972501234567",
      "direction": "outbound",
      "status": "answered",
      "agentName": "John Doe",
      "recordingUrl": "https://..."
    }
  ]
}
```

## Example — TypeScript

```typescript
interface CdrRecord {
  callId: string;
  startTime: string;
  duration: number;
  src: string;
  dst: string;
  direction: 'inbound' | 'outbound';
  status: string;
  agentName: string;
  recordingUrl?: string;
}

async function getCallHistory(
  token: string,
  filters: { startDate: string; endDate: string; extension?: string; page?: number }
): Promise<{ total: number; records: CdrRecord[] }> {
  const params = new URLSearchParams({
    startDate: filters.startDate,
    endDate: filters.endDate,
    page: String(filters.page ?? 1),
    pageSize: '100',
    ...(filters.extension ? { extension: filters.extension } : {}),
  });

  const res = await fetch(`https://api.voicenter.com/v2/reports/cdr?${params}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error(`CDR fetch failed: ${res.status}`);
  return res.json();
}
```

## Pagination — fetch all records

```typescript
async function getAllCalls(token: string, startDate: string, endDate: string) {
  const allRecords: CdrRecord[] = [];
  let page = 1;
  let total = Infinity;

  while (allRecords.length < total) {
    const { records, total: t } = await getCallHistory(token, { startDate, endDate, page });
    total = t;
    allRecords.push(...records);
    page++;
  }
  return allRecords;
}
```

## Tips

- Keep date ranges under 31 days per request for best performance.
- `recordingUrl` is only present when a recording exists — use the `voicenter-telephony` `/call-recordings` skill to work with recordings.
- Sort by `startTime` descending to show the most recent calls first.
