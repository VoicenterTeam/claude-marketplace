# Skill: `call-log`

Pull historical call detail records (CDR) from Voicenter using the Call Log API.

> Source: [`plugins/voicenter-api/skills/call-log/SKILL.md`](../../../plugins/voicenter-api/skills/call-log/SKILL.md)
> Plugin: [voicenter-api](../../plugins/voicenter-api.md) · Direction: **In/Out** · Transport: **REST**

---

## When to use this skill

- Retrieve historical call records for reporting or analytics
- Find all calls to/from a specific phone number or extension
- Get recording URLs for past calls to display in a CRM
- Build missed-call reports (`DialStatus: ABANDONE` / `NOANSWER`)
- Correlate a call by its ID (`ivruniqueid` / `CallID`)
- Export call data to BI tools or billing systems
- Audit agent activity over a date range

---

## Endpoint

```
POST https://api.voicenter.com/hub/cdr/
GET  https://api.voicenter.com/hub/cdr/?...
```

Response is JSON.

---

## Authentication

| Field | Notes |
|---|---|
| `code` | Lowercase. In the body. |
| Server IP | Must be whitelisted in CPanel → API Settings. |

```env
VOICENTER_API_CODE=your_api_token_here
```

---

## Request structure

A request has two parts: **search criteria** (what to filter) and **fields** (what to return).

### Search criteria

| Parameter | Type | Required | Description |
|---|---|---|---|
| `code` | String | ✅ | API token |
| `fromdate` | ISO 8601 | ✅ | Start date/time in **GMT+0** |
| `todate` | ISO 8601 | ✅ | End date/time in **GMT+0** |
| `phones` | String[] | ❌ | Phone numbers to filter (with country code) |
| `extensions` | String[] | ❌ | SIP codes to filter |
| `IdentityCriteria` | String | ❌ | `Account` / `Hierarchical` / `Department` / `User` |
| `callID` | String | ❌ | Filter for one call (`ivruniqueid`) |
| `cdrTypes` | Integer[] | ❌ | Filter by call type IDs (see below) |
| `campaignID` | Number[] | ❌ | Filter by dialer campaign IDs |
| `queueID` | Number[] | ❌ | Filter by queue IDs |

### CDR type IDs

| ID | Type |
|---|---|
| 1 | Incoming Call |
| 4 | Extension Outgoing |
| 8 | Queue |
| 9 | Click2Call leg1 |
| 10 | Click2Call leg2 |
| 11 | VoiceMail |
| 13 | XferCDR (transferred) |
| 14 | ProductiveCall Leg1 |
| 15 | ProductiveCall Leg2 |
| 17 | Click 2 IVR |
| 18 | Click 2 IVR Incoming |
| 19 | Click 2 Queue Incoming |
| 21 | Attended CDR leg1 |
| 22 | Attended CDR leg2 |
| 23 | Auto forward |

### Returnable fields

`CallerNumber`, `TargetNumber`, `Date`, `DateEpoch`, `Duration`, `CallID`, `Type`, `CdrType`, `DialStatus`, `Targetextension`, `Callerextension`, `DID`, `QueueName`, `RecordURL`, `RecordExpect`, `Price`, `RingTime`, `RepresentativeName`, `RepresentativeCode`, `UserName`, `UserId`, `DTMFData`, `CustomData`, `DepartmentName`, `DepartmentId`, `TargetPrefixName`

### Sort

```json
"sort": [
  { "field": "date", "order": "desc" },
  { "field": "Duration", "order": "asc" }
]
```

---

## Full POST-JSON example

```json
{
  "code": "xxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "fields": [
    "CallerNumber", "TargetNumber", "Date", "Duration", "CallID",
    "Type", "CdrType", "DialStatus", "DID", "QueueName",
    "RecordURL", "RingTime", "RepresentativeName", "RepresentativeCode",
    "DTMFData", "CustomData", "DepartmentName"
  ],
  "search": {
    "fromdate": "2024-06-01T00:00:00",
    "todate": "2024-06-30T23:59:59",
    "cdrTypes": [1, 8, 9, 10],
    "phones": ["972501234567"],
    "extensions": ["SIPSIP1"],
    "IdentityCriteria": "Account"
  },
  "sort": [{ "field": "date", "order": "desc" }]
}
```

---

## Response

```json
{
  "ERROR_NUMBER": 0,
  "ERROR_DESCRIPTION": "OK",
  "STATUS_CODE": 200,
  "TOTAL_HITS": 2,
  "RETURN_HITS": 2,
  "CDR_LIST": [
    {
      "CallerNumber": "0722776772",
      "TargetNumber": "972501234567",
      "Date": "2024-06-10T09:04:58Z",
      "Duration": 2,
      "CallID": "202406101204550233243ghff3189e5c",
      "CustomData": {},
      "Type": "Extension Outgoing",
      "CdrType": 4,
      "DialStatus": "ANSWER",
      "CallerExtension": "SIPSIP1",
      "DID": "",
      "RecordURL": "https://cpanel.voicenter.co.il/CallsHistory/PlayRecord/2024061043950926.mp3",
      "RingTime": 10,
      "RepresentativeName": "John Doe",
      "RepresentativeCode": "87654321",
      "DTMFData": [],
      "DepartmentName": "Sales"
    }
  ]
}
```

---

## Error codes

| ERROR_NUMBER | STATUS_CODE | Meaning |
|---|---|---|
| 0 | 200 | OK |
| 1 | 403 | Rate limit exceeded — wait 5 s between requests |
| 2 | 403 | Authorization failed — invalid code |
| 4 | 403 | IP not authorized |
| 5 | 404 | Date range invalid |

---

## Service limits

- Max **10,000 CDR records** per response — break large date ranges into daily chunks.
- Max **30 requests / minute** — add a 2-second delay between sequential requests.
- CDRs appear a few minutes after a call ends — not for real-time use.
- Only authorized server IPs can call the endpoint.

---

## TypeScript implementation

```typescript
const CALL_LOG_URL = 'https://api.voicenter.com/hub/cdr/';
const CODE = process.env.VOICENTER_API_CODE!;

interface CdrRecord {
  CallerNumber: string;
  TargetNumber: string;
  Date: string;
  Duration: number;
  CallID: string;
  Type: string;
  CdrType: number;
  DialStatus: string;
  DID: string;
  QueueName?: string;
  RecordURL: string;
  RingTime: number;
  RepresentativeName: string;
  RepresentativeCode: string;
  DTMFData: Array<{ LayerName: string; DTMF: number; LayerNumber: string }>;
  CustomData: Record<string, unknown>;
}

interface CallLogResponse {
  ERROR_NUMBER: number;
  ERROR_DESCRIPTION: string;
  TOTAL_HITS: number;
  RETURN_HITS: number;
  CDR_LIST: CdrRecord[];
}

async function getCallLog(
  fromdate: string,
  todate: string,
  options?: {
    phones?: string[];
    extensions?: string[];
    cdrTypes?: number[];
    callID?: string;
    fields?: string[];
    sort?: Array<{ field: string; order: 'asc' | 'desc' }>;
  }
): Promise<CallLogResponse> {
  const body = {
    code: CODE,
    fields: options?.fields ?? [
      'CallerNumber', 'TargetNumber', 'Date', 'Duration', 'CallID',
      'Type', 'CdrType', 'DialStatus', 'DID', 'QueueName',
      'RecordURL', 'RingTime', 'RepresentativeName', 'CustomData',
    ],
    search: {
      fromdate,
      todate,
      IdentityCriteria: 'Account',
      ...(options?.phones && { phones: options.phones }),
      ...(options?.extensions && { extensions: options.extensions }),
      ...(options?.cdrTypes && { cdrTypes: options.cdrTypes }),
      ...(options?.callID && { callID: options.callID }),
    },
    sort: options?.sort ?? [{ field: 'date', order: 'desc' }],
  };

  const res = await fetch(CALL_LOG_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const data: CallLogResponse = await res.json();
  if (data.ERROR_NUMBER !== 0) {
    throw new Error(`Call Log error ${data.ERROR_NUMBER}: ${data.ERROR_DESCRIPTION}`);
  }
  return data;
}
```

### Example: missed calls today

```typescript
const { CDR_LIST } = await getCallLog(
  '2024-06-01T00:00:00',
  '2024-06-01T23:59:59',
  { cdrTypes: [1, 8], fields: ['CallerNumber', 'Date', 'DialStatus', 'QueueName', 'DID'] }
);
const missed = CDR_LIST.filter(r => ['ABANDONE', 'NOANSWER'].includes(r.DialStatus));
```

### Example: chunk a long date range

```typescript
async function* paginateByDay(start: Date, end: Date) {
  for (let d = new Date(start); d < end; d.setDate(d.getDate() + 1)) {
    const from = d.toISOString().slice(0, 19);
    const to = new Date(d.getTime() + 86_400_000 - 1_000).toISOString().slice(0, 19);
    yield await getCallLog(from, to);
    await new Promise(r => setTimeout(r, 2_000)); // respect rate limits
  }
}
```

---

## Tips & best practices

- Use `cdrTypes: [9, 10]` to fetch only Click2Call records and join Leg1/Leg2 by `CallID`.
- `CustomData.OriginalIvrUniqueID` links a transferred call back to the original.
- `RecordURL` is a direct MP3 link — store it in your CRM for playback.
- All dates are **GMT+0** in the request. Israeli time is GMT+2 (or GMT+3 in summer).
- `DialStatus` values: `ANSWER`, `NOANSWER`, `BUSY`, `CANCEL`, `ABANDONE`, `TIMEOUT`, `VOICEMAIL`.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `ERROR_NUMBER 1` | Rate limit | Add ≥ 2-second delay between requests |
| `ERROR_NUMBER 4` | IP not authorized | Whitelist in CPanel |
| Empty `CDR_LIST` | Date range in wrong TZ | Convert to GMT+0 (subtract 2 or 3 hours from Israeli time) |
| `RECORD_HITS == 10000` | Hit the per-response cap | Split into smaller date windows |

---

## Related skills

- [CDR Notification](../cdr-notification/README.md) — receive CDRs live via webhook (use both — CDR for live, Call Log for backfill)
- [Click2Call](../click2call/README.md) — `CALLID` returned matches `CallID` here
- [Productive Dialer](../productive-dialer/README.md) — filter dialer records with `cdrTypes: [14, 15]`
- [Active Calls](../active-calls/README.md) — for live call state (Call Log is historical)
