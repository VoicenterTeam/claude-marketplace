---
description: Generate call reports and export CDR data from Voicenter
---

Help the developer **generate and export call reports** — summaries by agent, queue, date range, or call type.

## Summary report API

**Endpoint:** `GET https://api.voicenter.com/v2/reports/summary`

**Query parameters:**

| Parameter | Description |
|---|---|
| `startDate` | ISO 8601 |
| `endDate` | ISO 8601 |
| `groupBy` | `agent` \| `queue` \| `day` \| `hour` |
| `direction` | `inbound` \| `outbound` \| `all` |

**Response:**
```json
{
  "period": { "from": "2024-06-01", "to": "2024-06-30" },
  "rows": [
    {
      "label": "John Doe",
      "totalCalls": 312,
      "answeredCalls": 298,
      "missedCalls": 14,
      "avgDuration": 187,
      "totalTalkTime": 58276
    }
  ]
}
```

## Example — TypeScript

```typescript
async function getSummaryReport(
  token: string,
  startDate: string,
  endDate: string,
  groupBy: 'agent' | 'queue' | 'day' = 'agent'
) {
  const params = new URLSearchParams({ startDate, endDate, groupBy });
  const res = await fetch(`https://api.voicenter.com/v2/reports/summary?${params}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error(`Report failed: ${res.status}`);
  return res.json();
}

// Example: print top agents by answered calls this month
const report = await getSummaryReport(token, '2024-06-01T00:00:00Z', '2024-06-30T23:59:59Z', 'agent');
const sorted = report.rows.sort((a: any, b: any) => b.answeredCalls - a.answeredCalls);
sorted.slice(0, 5).forEach((row: any) => {
  console.log(`${row.label}: ${row.answeredCalls} calls, avg ${row.avgDuration}s`);
});
```

## Export to CSV — Python

```python
import requests, csv, io

def export_cdr_csv(token, start_date, end_date, output_path):
    r = requests.get(
        "https://api.voicenter.com/v2/reports/cdr/export",
        headers={"Authorization": f"Bearer {token}"},
        params={"startDate": start_date, "endDate": end_date, "format": "csv"}
    )
    r.raise_for_status()
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        f.write(r.text)
    print(f"Exported to {output_path}")
```

## Tips

- Use `groupBy=hour` to identify peak hours and staff accordingly.
- `avgDuration` is in seconds — divide by 60 for minutes in your dashboard.
- For large date ranges, use the CDR export endpoint (`/v2/reports/cdr/export`) which returns a CSV or JSON file rather than paginated records.
