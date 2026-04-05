---
description: Build a VoiceBot data endpoint that the Voicenter Voice Agent calls mid-conversation to fetch dynamic CRM data
---

Help the developer implement a **VoiceBot API endpoint** — a URL that the Voicenter Voice Agent (AI bot) calls during a live conversation to retrieve dynamic CRM data before continuing.

## When to use this skill

Use this skill when the user wants to:
- Feed real-time CRM data to an AI voice agent mid-conversation (account balance, order status, open tickets)
- Let a voice bot look up customer information by the caller ID or DTMF input collected during the call
- Return structured data that the voice agent will read back to the caller
- Route the voice agent's behavior dynamically based on the caller's CRM profile
- Return appointment slots, product info, or personalized offers from an external system
- Handle multiple intents from a single endpoint using `LAYER_ID` to route logic

## Environment Variables

```env
# No outbound API token needed — Voicenter sends requests TO your server.
# Configure your endpoint URL in: Voice Agent intent settings → "URL" field under "תגובה" (Response)
```

## How it works

1. An inbound or outbound call is handled by a Voicenter Voice Agent (AI bot).
2. The agent reaches an intent that needs external data.
3. The Voice Agent POSTs call info + collected intent parameters to your endpoint.
4. Your server fetches the data from your CRM/DB and responds.
5. The Voice Agent reads the response and continues the conversation.

**Note:** Pair with the **External Layer API** for the full pattern — External Layer passes CRM context (caller ID, tier, ticket) into `CUSTOM_DATA` at call start, and VoiceBot fetches dynamic data mid-conversation.

## Request Voicenter sends you

**Method:** `POST`
**Content-Type:** `application/json`

```json
{
  "CALL_INFO": {
    "DID": "0722776772",
    "CALLER_ID": "0501234567",
    "IVR_UNIQUE_ID": "ssss1bcd7954224861f85a2d70612f2",
    "DTMF": "1234",
    "LAYER_ID": "10",
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
| `CALL_INFO.CALLER_ID` | String | Caller's phone number — use to look them up in CRM |
| `CALL_INFO.IVR_UNIQUE_ID` | String | Unique call ID — correlates with CDR and other APIs |
| `CALL_INFO.DTMF` | String | Digits the caller pressed. Default `"0"` if none. |
| `CALL_INFO.LAYER_ID` | String | IVR layer ID — use to route different intents when multiple share the same endpoint |
| `CALL_INFO.PREVIOUS_LAYER_ID` | String | Previous IVR layer ID |
| `IntentParameters` | Object | Fields collected by the Voice Agent in this conversation so far |
| `CUSTOM_DATA` | Object | Flat key-value data passed from External Layer API. **No nested objects.** |

## Your Response

All fields are optional. Return `{}` to let the agent continue with existing instructions.

### Response Fields

| Field | Type | Description |
|---|---|---|
| `function_output` | Object | Structured data for the agent to use. Any valid JSON — the agent reads field names and values. |
| `user` | String[] | Instructions for the agent. **Most commonly used field.** Supports Markdown. |
| `assistant` | Object | Additional influence on agent behavior. Rarely needed. |
| `system` | Object | System-level instructions merged into the agent's base prompt. Supports Markdown. |

### Simple response — instruction only

```json
{
  "user": [
    "Tell the caller their order #123456 shipped this morning. Delivery is expected today between 2 PM and 4 PM. Ask if there is anything else they need."
  ]
}
```

### Response with structured data

```json
{
  "function_output": {
    "account_balance": 180,
    "plan": "Pro",
    "renewal_date": "2024-08-01",
    "open_tickets": 2
  },
  "user": [
    "Read the caller their account balance and plan. Let them know they have 2 open support tickets and offer to transfer them to support."
  ]
}
```

### Response with a list (e.g., open orders)

```json
{
  "function_output": {
    "orders": [
      { "id": "ORD-001", "status": "Shipped", "eta": "Today" },
      { "id": "ORD-002", "status": "Processing", "eta": "2-3 days" }
    ]
  },
  "user": [
    "Read the caller their open orders. For each order, state the order ID and current status."
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
  const { CALL_INFO, IntentParameters, CUSTOM_DATA } = req.body as VoiceBotRequest;

  try {
    const crmClientId = CUSTOM_DATA.CRM_client_ID;
    const layerId = CALL_INFO.LAYER_ID;

    // Route logic by intent/layer ID
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

    // Default — agent continues with existing instructions
    return res.json({});

  } catch (err) {
    console.error('VoiceBot endpoint error:', err);
    // Always return a valid response — never let it hang or return 5xx
    return res.json({});
  }
});

app.listen(3000);
```

## Tips

- **Always respond** — even on error, return `{}` so the Voice Agent continues gracefully. Never return a 5xx or let the request hang.
- **`LAYER_ID` is your routing key** when multiple intents call the same endpoint — use it to run different CRM queries per intent.
- **`CUSTOM_DATA` is flat** — only supports simple key-value pairs (no nested objects). Use `function_output` in your response to return complex structured data.
- **`user` field supports Markdown** — use headers, bold, tables, and lists when guiding the agent through structured data like order lists or slot tables.
- **`IntentParameters`** contains what the agent has already collected — use it to look up records (e.g., an order number or ID the caller said aloud).
- Works for both **inbound and outbound** calls.

## Related Skills

- **External Layer** — Run at call start to pass CRM context into `CUSTOM_DATA` before the VoiceBot is called
- **CDR Notification** — Receives the full call record after the voice agent conversation ends
- **Click2Call** — Use `IVR_UNIQUE_ID` to correlate voicebot calls with outbound Click2Call initiations
