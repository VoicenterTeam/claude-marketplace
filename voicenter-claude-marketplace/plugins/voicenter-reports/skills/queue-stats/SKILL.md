---
description: Get real-time and historical queue statistics from Voicenter
---

Help the developer retrieve **queue statistics** — wait times, abandonment rates, service levels, and real-time agent availability.

## Real-time queue stats

**Endpoint:** `GET https://api.voicenter.com/v2/queues/stats/realtime`

**Response:**
```json
{
  "queues": [
    {
      "queueId": "q-sales",
      "name": "Sales",
      "waitingCalls": 3,
      "longestWait": 45,
      "availableAgents": 5,
      "busyAgents": 2,
      "avgWaitTime": 22
    }
  ]
}
```

## Historical queue stats

**Endpoint:** `GET https://api.voicenter.com/v2/queues/stats/history`

**Query parameters:** `startDate`, `endDate`, `queueId` (optional), `groupBy` (`day` | `hour`)

**Response row:**
```json
{
  "queueId": "q-sales",
  "period": "2024-06-01",
  "totalCalls": 87,
  "answeredCalls": 79,
  "abandonedCalls": 8,
  "avgWaitTime": 18,
  "serviceLevel": 91.4
}
```

`serviceLevel` = percentage of calls answered within the SLA threshold (configured in your Voicenter account).

## Example — TypeScript live dashboard

```typescript
interface QueueStat {
  queueId: string;
  name: string;
  waitingCalls: number;
  longestWait: number;
  availableAgents: number;
  avgWaitTime: number;
}

async function getRealTimeQueues(token: string): Promise<QueueStat[]> {
  const res = await fetch('https://api.voicenter.com/v2/queues/stats/realtime', {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error(`Queue stats failed: ${res.status}`);
  const { queues } = await res.json();
  return queues;
}

// Poll every 10 seconds for a live wallboard
setInterval(async () => {
  const queues = await getRealTimeQueues(token);
  queues.forEach(q => {
    console.log(`[${q.name}] Waiting: ${q.waitingCalls} | Available agents: ${q.availableAgents} | Longest wait: ${q.longestWait}s`);
  });
}, 10_000);
```

## SLA compliance report — Python

```python
def get_sla_report(token, queue_id, start_date, end_date):
    r = requests.get(
        "https://api.voicenter.com/v2/queues/stats/history",
        headers={"Authorization": f"Bearer {token}"},
        params={"queueId": queue_id, "startDate": start_date, "endDate": end_date, "groupBy": "day"}
    )
    r.raise_for_status()
    rows = r.json()["rows"]
    for row in rows:
        flag = "✅" if row["serviceLevel"] >= 80 else "❌"
        print(f"{row['period']} {flag} SLA: {row['serviceLevel']}% | Abandoned: {row['abandonedCalls']}")
```

## Tips

- Use the `voicenter-webhooks` plugin's `queue.call_waiting` event to trigger alerts when `waitingCalls` exceeds a threshold.
- Real-time stats are eventually consistent — a slight delay (1–2 seconds) is normal.
- `serviceLevel` threshold is account-configured — contact Voicenter support to change the SLA target.
