# Skill: `voicebot`

Build a VoiceBot data endpoint that the Voicenter Voice Agent calls mid-conversation to fetch dynamic CRM data.

> Source: [`plugins/voicenter-api/skills/voicebot/SKILL.md`](../../../plugins/voicenter-api/skills/voicebot/SKILL.md)
> Plugin: [voicenter-api](../../plugins/voicenter-api.md) · Direction: **In/Out** · Transport: **Webhook (push)**

---

> **Language.** Reply in the user's language: detect what they write — Hebrew→Hebrew, English→English — and mirror it, switching if they switch mid-conversation. This shapes your prose, your questions, and your `AskUserQuestion` option labels only. It does **not** change the artifacts you produce — identifiers, JSON keys, BCP-47 language codes, API field names, and other data stay exactly as specified.

## When to use this skill

- Feed real-time CRM data to an AI voice agent mid-conversation
- Look up customers by caller ID or by DTMF the bot collected
- Return structured data the bot will read back to the caller
- Adapt the agent's behavior based on the caller's CRM profile
- Return appointment slots, product info, or personalized offers
- Multiplex multiple intents on a single endpoint via `LAYER_ID`

---

## How it works

1. A call is handled by a Voicenter Voice Agent (AI bot).
2. The agent reaches an intent that needs external data.
3. Voicenter POSTs call info + collected intent parameters to your endpoint.
4. Your server fetches data from CRM/DB and responds.
5. The Voice Agent reads the response and continues the conversation.

> Pair with [External Layer](../external-layer/README.md) for the full pattern: External Layer passes CRM context into `CUSTOM_DATA` at call start; VoiceBot fetches dynamic data per intent.

Configure the URL in: **Voice Agent intent settings → "URL" field under "תגובה" (Response)**.

---

## Request Voicenter sends you

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

| Field | Description |
|---|---|
| `CALL_INFO.DID` | The DID dialed |
| `CALL_INFO.CALLER_ID` | Caller's phone |
| `CALL_INFO.IVR_UNIQUE_ID` | Universal call ID |
| `CALL_INFO.DTMF` | Digits the caller pressed (default `"0"`) |
| `CALL_INFO.LAYER_ID` | IVR layer ID — use to multiplex intents on one endpoint |
| `CALL_INFO.PREVIOUS_LAYER_ID` | Previous layer |
| `IntentParameters` | Fields the agent has collected so far this conversation |
| `CUSTOM_DATA` | Flat key-value data from External Layer. **No nested objects.** |

---

## Your response

All fields are optional. Return `{}` to let the agent continue with its existing instructions.

| Field | Type | Description |
|---|---|---|
| `function_output` | Object | Structured data for the agent. Any valid JSON. |
| `user` | String[] | Instructions for the agent. **Most commonly used.** Markdown supported. |
| `assistant` | Object | Additional behavior overrides. Rarely needed. |
| `system` | Object | System-prompt additions. Markdown supported. |

### Instruction-only

```json
{
  "user": [
    "Tell the caller their order #123456 shipped this morning. Delivery is expected today between 2 PM and 4 PM. Ask if there is anything else they need."
  ]
}
```

### With structured data

```json
{
  "function_output": {
    "account_balance": 180,
    "plan": "Pro",
    "renewal_date": "2024-08-01",
    "open_tickets": 2
  },
  "user": [
    "Read the caller their account balance and plan. Let them know they have 2 open support tickets and offer to transfer them."
  ]
}
```

### With a list

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

---

## TypeScript implementation (Express)

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

    if (layerId === '10') {
      const order = await crm.getLatestOrder(crmClientId);
      const response: VoiceBotResponse = {
        function_output: { order_id: order.id, status: order.status, eta: order.estimatedDelivery },
        user: [
          `Tell the caller their latest order (${order.id}) is currently ${order.status}. ` +
          `Estimated delivery: ${order.estimatedDelivery}. Ask if they need anything else.`,
        ],
      };
      return res.json(response);
    }

    if (layerId === '11') {
      const account = await crm.getAccount(crmClientId);
      return res.json({
        function_output: { balance: account.balance, currency: 'ILS', plan: account.plan },
        user: ['Read the caller their account balance and current plan.'],
      });
    }

    if (layerId === '12') {
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

    return res.json({});
  } catch (err) {
    console.error('VoiceBot endpoint error:', err);
    return res.json({}); // never 5xx
  }
});

app.listen(3000);
```

---

## Tips & best practices

- **Always respond** — even on error, return `{}`. Never let the request hang or 5xx — the bot is mid-conversation.
- **`LAYER_ID` is your routing key** when multiple intents share an endpoint.
- **`CUSTOM_DATA` is flat** — no nested objects. Put complex data in `function_output` of your **response**.
- **`user` supports Markdown** — use it for tables, bullet lists, headers when guiding the bot through structured data.
- **`IntentParameters`** = whatever the agent has already collected (order numbers, dates, names) — use it to look up records.
- Works for both **inbound and outbound** calls.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Bot freezes | Endpoint hung or > 10 s | Always reply, even with `{}` |
| Bot ignores your data | `function_output` shape mismatch with prompt | Make sure `user` instructs the bot what to read |
| Wrong intent handled | All layers hit the same branch | Switch on `CALL_INFO.LAYER_ID` |
| `CUSTOM_DATA` empty | External Layer didn't run or set it | Verify External Layer config and CPanel |

---

## Related skills

- [External Layer](../external-layer/README.md) — runs at call start; sets `CUSTOM_DATA` for VoiceBot
- [CDR Notification](../cdr-notification/README.md) — receives the full call record after the conversation ends
- [Click2Call](../click2call/README.md) — `IVR_UNIQUE_ID` correlates outbound bot calls
