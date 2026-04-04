---
description: Pull call detail records (CDR) from Voicenter using the Call Log API
---

Help the developer query **call history (CDR records)** from the Voicenter Call Log API — filter by date, phone, extension, call type, and choose exactly which fields to return.

## Endpoint

```
https://api.voicenter.com/hub/cdr/
```

Accepts: `POST-JSON` or `GET`
Response: `JSON`

## Authentication

Send your `code` in the request body (or as a Bearer token header).  
The requesting server's IP must be authorized in the Voicenter CPanel.

## Request Structure

The request has two parts: **search criteria** (what to filter) and **fields** (what to return).

### Search Criteria

| Parameter | Type | Required | Description |
|---|---|---|---|
| `code` | String | ✅ | API authentication token |
| `fromdate` | ISO 8601 | ✅ | Start date/time in **GMT+0** (e.g. `2024-06-01T00:00:00`) |
| `todate` | ISO 8601 | ✅ | End date/time in **GMT+0** |
| `phones` | String[] | ❌ | Phone numbers to filter (with country code, e.g. `"972501234567"`) |
| `extensions` | String[] | ❌ | SIP extension codes to filter |
| `IdentityCriteria` | String | ❌ | `Account`, `Hierarchical`, `Department`, or `User` |
| `callID` | String | ❌ | Filter for a specific call by `ivruniqueid` |
| `cdrTypes` | Integer[] | ❌ | Filter by call type IDs (see table below) |
| `campaignID` | Number[] | ❌ | Filter by dialer campaign IDs |
| `queueID` | Number[] | ❌ | Filter by queue IDs |

### CDR Type IDs

| ID | Type Name |
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

### Returnable Fields

Choose which CDR fields to receive:

`CallerNumber`, `TargetNumber`, `Date`, `DateEpoch`, `Duration`, `CallID`, `Type`, `CdrType`, `DialStatus`, `Targetextension`, `Callerextension`, `DID`, `QueueName`, `RecordURL`, `RecordExpect`, `Price`, `RingTime`, `RepresentativeName`, `RepresentativeCode`, `UserName`, `UserId`, `DTMFData`, `CustomData`, `DepartmentName`, `DepartmentId`, `TargetPrefixName`

### Sort

```json
"sort": [
  { "field": "date", "order": "desc" },
  { "field": "Duration", "order": "asc" }
]
```

## Full POST-JSON Request Example

```json
{
  "code": "xxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "fields": [
    "CallerNumber",
    "TargetNumber",
    "Date",
    "Duration",
    "CallID",
    "Type",
    "CdrType",
    "DialStatus",
    "DID",
    "QueueName",
    "RecordURL",
    "RingTime",
    "RepresentativeName",
    "RepresentativeCode",
    "DTMFData",
    "CustomData",
    "DepartmentName"
  ],
  "search": {
    "fromdate": "2024-06-01T00:00:00",
    "todate": "2024-06-30T23:59:59",
    "cdrTypes": [1, 8, 9, 10],
    "phones": ["972501234567"],
    "extensions": ["SIPSIP1"],
    "IdentityCriteria": "Account"
  },
  "sort": [
    { "field": "date", "order": "desc" }
  ]
}
```

## GET Request Example

```
https://api.voicenter.com/hub/cdr/?code=XXXX&fromdate=2024-06-01T00:00:00&todate=2024-06-30T23:59:59&phones=972501234567&fields=Date&fields=Type&fields=DID&fields=CallerNumber
```

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
      "TargetExtension": "",
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

### Error Codes

| ERROR_NUMBER | STATUS_CODE | Description |
|---|---|---|
| 0 | 200 | OK |
| 1 | 403 | Rate limit exceeded — wait 5 seconds between requests |
| 2 | 403 | Authorization failed — invalid code |
| 4 | 403 | IP not authorized |
| 5 | 404 | Date range invalid |

## TypeScript Implementation

```typescript
const CALL_LOG_URL = 'https://api.voicenter.com/hub/cdr/';

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
  code: string,
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
    code,
    fields: options?.fields ?? [
      'CallerNumber', 'TargetNumber', 'Date', 'Duration', 'CallID',
      'Type', 'CdrType', 'DialStatus', 'DID', 'QueueName',
      'RecordURL', 'RingTime', 'RepresentativeName', 'CustomData',
    ],
    search: {
      fromdate,
      todate,
      ...(options?.phones && { phones: options.phones }),
      ...(options?.extensions && { extensions: options.extensions }),
      ...(options?.cdrTypes && { cdrTypes: options.cdrTypes }),
      ...(options?.callID && { callID: options.callID }),
      IdentityCriteria: 'Account',
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
  if (data.ERROR_NUMBER !== 0) throw new Error(`Call Log error ${data.ERROR_NUMBER}: ${data.ERROR_DESCRIPTION}`);
  return data;
}

// Example: get all unanswered incoming calls today
const { CDR_LIST } = await getCallLog(
  'MY_CODE',
  '2024-06-01T00:00:00',
  '2024-06-01T23:59:59',
  {
    cdrTypes: [1, 8],              // Incoming Call + Queue
    fields: ['CallerNumber', 'Date', 'DialStatus', 'QueueName', 'DID'],
    sort: [{ field: 'date', order: 'desc' }],
  }
);

const missed = CDR_LIST.filter(r => r.DialStatus === 'ABANDONE' || r.DialStatus === 'NOANSWER');
console.log(`Missed calls: ${missed.length}`);
```

## Service Limits

- Maximum **10,000 CDR records** per request
- Maximum **30 requests per minute** — wait at least 5 seconds between requests
- CDRs appear a few minutes after a call ends
- Only authorized IP addresses can call this API (set in CPanel)

## Tips

- Use `cdrTypes: [9, 10]` to get only Click2Call records and correlate Leg1/Leg2 by `CallID`.
- `CustomData.OriginalIvrUniqueID` links a transferred call back to the original call.
- `RecordURL` is a direct MP3 link — store it in your CRM for playback.
- For large date ranges, break requests into daily chunks to stay under the 10K limit.
