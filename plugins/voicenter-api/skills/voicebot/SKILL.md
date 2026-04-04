---
description: Build a VoiceBot data endpoint that the Voicenter Voice Agent calls mid-conversation to fetch dynamic CRM data
---

Help the developer implement a **VoiceBot API endpoint** — a URL that the Voicenter Voice Agent calls during a live conversation when it needs to retrieve or update data from the CRM before continuing.

## How it works

1. An inbound or outbound call is handled by a Voicenter Voice Agent (AI bot).
2. During the conversation, the agent reaches a point where it needs external data (account balance, order status, open tickets, available slots, etc.).
3. The Voice Agent POSTs a request to your configured URL containing call info, any DTMF input, and data collected so far.
4. Your server fetches the relevant data from your CRM/DB and responds.
5. The Voice Agent reads the response and continues the conversation with the new data.

Configure the endpoint URL in the Voice Agent's intent settings, in the field called **URL**, under the "תגובה" (Response) options.

**Note:** The VoiceBot API is typically combined with the [External Layer API](https://www.voicenter.com/API/External-Layer) — the External Layer passes initial caller context (from CRM) via `CUSTOM_DATA` before the Voice Agent starts, and the VoiceBot API is called later mid-conversation as needed.

## Request Voicenter sends you

**Method:** `POST`  
**Format:** `JSON`

```json
{
  "CALL_INFO": {
    "DID": "0722776772",
    "CALLER_ID": "0501234567",
    "IVR_UNIQUE_ID": "ssss1bcd7954224861f85a2d70612f2",
    "DTMF": "1234",
    "LAYER_ID": "5",
    "PREVIOUS_LAYER_ID": "5"
  },
  "IntentParameters": {
    "city": "Tel Aviv",
    "product_interest": "Pro Plan"
  },
  "CUSTOM_DATA": {
    "CRM_client_ID": "12345",
    "Last_ticket_ID": "222",
    "Last_representative": "John Doe"
  }
}
```

### Request Fields

| Field | Type | Description |
|---|---|---|
| `CALL_INFO.DID` | String | The phone number the caller dialed |
| `CALL_INFO.CALLER_ID` | String | Caller's phone number |
| `CALL_INFO.IVR_UNIQUE_ID` | String | Unique call ID — use to correlate with CDR and other APIs |
| `CALL_INFO.DTMF` | String | Digits the caller pressed. Default `"0"` if none pressed. |
| `CALL_INFO.LAYER_ID` | String (int) | IVR layer ID the request is sent from — useful for routing logic when multiple intents call the same endpoint |
| `CALL_INFO.PREVIOUS_LAYER_ID` | String (int) | Previous IVR layer ID |
| `IntentParameters` | Object | Fields collected by the Voice Agent during this conversation so far (defined in the agent's intent configuration) |
| `CUSTOM_DATA` | Object | Key-Value data passed in from an earlier stage (e.g. from External Layer API). Only supports flat Key + Value — no nested objects. |

## Your Response

None of the response fields are mandatory. You can return an empty object `{}` and the Voice Agent will continue with its existing instructions.

### Response Fields

| Field | Type | Required | Description |
|---|---|---|---|
| `function_output` | Object | No | Structured data for the agent to use. Any valid JSON object — the agent will use the field names and values to answer the caller. |
| `user` | Array of strings | No | Instructions for the agent on what to do with the data. Supports Markdown (headers, bold, tables) for long prompts. Most commonly used field. |
| `assistant` | Object | No | Additional influence on agent behavior. Rarely needed when the other fields are used. |
| `system` | Object | No | General system-level instructions merged into the agent's base prompt. Use to restrict or refine behavior. Supports Markdown. |

### Simple Response — instruction only

```json
{
  "user": [
    "הסבר ללקוח שהזמנה מספר 123456 יצאה אליו הבוקר, וכי השליח צפוי להגיע היום בין 14:00 ל16:00 אחר הצהריים."
  ]
}
```

Or in English:
```json
{
  "user": [
    "Tell the caller their order #123456 shipped this morning. Delivery is expected today between 2 PM and 4 PM. Ask if there is anything else they need."
  ]
}
```

### Response with structured data (`function_output`)

```json
{
  "function_output": {
    "account_balance": 180,
    "plan": "Pro",
    "renewal_date": "2024-08-01",
    "open_tickets": 2
  },
  "user": [
    "Read the caller their account balance and plan. Let them know they have open tickets and offer to transfer them to support."
  ]
}
```

### Response with a list (e.g. open orders)

```json
{
  "function_output": {
    "orders": [
      { "id": "ORD-001", "status": "Shipped", "eta": "Today" },
      { "id": "ORD-002", "status": "Processing", "eta": "2-3 days" }
    ]
  },
  "user": [
    "Read the caller their open orders from the list above. For each order, state the order ID and its status."
  ]
}
```

### Weather API example (from official docs)

```json
{
  "function_output": {
    "weather": [{ "main": "Clear", "description": "clear sky" }],
    "main": { "temp": 27.89, "feels_like": 28.78, "humidity": 55 },
    "name": "Ramat Gan"
  },
  "user": [
    "Read the maximum temperature in the caller's city and ask if they want any other weather details."
  ]
}
```

## TypeScript Implementation (Express)

```typescript
import express, { Request, Response } from 'express';

const app = express();
app.use(express.json());

interface VoiceBotRequest {
  CALL_INFO: {
    DID: string;
    CALLER_ID: string;
    IVR_UNIQUE_ID: string;
    DTMF: string;
    LAYER_ID: string;
    PREVIOUS_LAYER_ID: string;
  };
  IntentParameters: Record<string, string>;
  CUSTOM_DATA: Record<string, string>;
}

interface VoiceBotResponse {
  function_output?: Record<string, unknown>;
  user?: string[];
  assistant?: Record<string, unknown>;
  system?: Record<string, unknown>;
}

app.post('/webhooks/voicenter/voicebot', async (req: Request, res: Response) => {
  const payload = req.body as VoiceBotRequest;
  const { CALL_INFO, IntentParameters, CUSTOM_DATA } = payload;

  try {
    const crmClientId = CUSTOM_DATA.CRM_client_ID;
    const layerId = CALL_INFO.LAYER_ID;

    // Route logic based on which intent/layer triggered the call
    if (layerId === '10') {
      // Order status intent
      const order = await crm.getLatestOrder(crmClientId);
      const response: VoiceBotResponse = {
        function_output: {
          order_id: order.id,
          status: order.status,
          eta: order.estimatedDelivery,
        },
        user: [
          `Tell the caller their latest order (${order.id}) is currently ${order.status}. ` +
          `Estimated delivery: ${order.estimatedDelivery}. Ask if they need anything else.`,
        ],
      };
      return res.json(response);
    }

    if (layerId === '11') {
      // Account balance intent
      const account = await crm.getAccount(crmClientId);
      return res.json({
        function_output: { balance: account.balance, currency: 'ILS', plan: account.plan },
        user: ['Read the caller their account balance and current plan.'],
      });
    }

    if (layerId === '12') {
      // Appointment scheduling intent
      const city = IntentParameters.city ?? '';
      const slots = await crm.getAvailableSlots(city);
      return res.json({
        function_output: { available_slots: slots },
        user: [
          'Read the caller the available appointment slots in their city. ' +
          'Ask which time works best and confirm the booking.',
        ],
      });
    }

    // Default — let the agent continue with existing instructions
    return res.json({});

  } catch (err) {
    console.error('VoiceBot endpoint error:', err);
    // Return empty so agent continues gracefully
    return res.json({});
  }
});

app.listen(3000);
```

## Tips

- **Always respond** — even on error, return `{}` so the Voice Agent continues. Never let the endpoint hang or return a 5xx.
- **`LAYER_ID`** is your routing key when multiple intents call the same endpoint — use it to run different CRM queries per intent.
- **`CUSTOM_DATA`** only supports flat Key + Value (no nested objects). If you need to pass complex data into the conversation, use the `function_output` in the response to return it dynamically instead.
- **`user` field** supports Markdown — use it for complex multi-step instructions, tables, or lists when guiding the agent through structured data.
- **`IntentParameters`** contains what the agent has already collected in this conversation — use it to look up records (e.g. an order number the caller just said).
- The VoiceBot API works for both inbound and outbound calls.
- Pair with **External Layer API** for the full flow: External Layer runs at call start (passes caller context), VoiceBot runs mid-conversation (fetches dynamic data on demand).
