# Architecture & call flows

The Voicenter platform is best understood as **four canonical call flows**. Every skill in this marketplace participates in one or more of them, and the most powerful integrations chain skills along a flow.

This document maps each flow and shows which skill performs each step.

---

## Skill taxonomy

| Category | Skills |
|---|---|
| **Incoming call routing & enrichment** | External Layer, Pop-Up Screen, VoiceBot |
| **Outgoing call control** | Click2Call, Mute Recording |
| **Call data & analytics** | CDR Notification, Call Log, Lead Tracker |
| **Agent & extension management** | Extension List, Login/Logout, Real-Time |
| **Outbound dialer & compliance** | Productive Dialer, Blacklist |
| **Live monitoring** | Active Calls, Real-Time |
| **CRM integration scoping** | CRM Onboarding, GetCallHistory |
| **Bot authoring (build-time)** | Agent Spec Designer, Intent Detail Author, JSON Assembler |

Every skill is also classified by transport:

| Transport | Skills |
|---|---|
| REST (`code` parameter) | Click2Call, Call Log, Blacklist, Extension List, Productive Dialer, Login/Logout, Active Calls |
| REST (no `code` — IP-restricted) | Mute Recording |
| Webhook (Voicenter → your endpoint) | VoiceBot, Pop-Up Screen, CDR Notification, External Layer |
| Persistent socket.io | Real-Time |
| Browser-side JS | Lead Tracker |
| OAuth MCP | (everything via the `voicenter-mcp` plugin) |

See [authentication.md](authentication.md) for full auth details per transport.

---

## Flow 1 — Incoming call lifecycle

The end-to-end path of a call entering your Voicenter account.

```text
                  Caller dials a DID
                          │
                          ▼
              ┌───────────────────────┐
              │  Voicenter IVR layer  │
              └───────────────────────┘
                          │
            (if "Allow Mini External IVR" is on)
                          │
                          ▼
        ┌────────────────────────────────────┐
        │  EXTERNAL LAYER  ◄── your endpoint │
        │  Decide LAYER / DIAL / SAY_DIGITS  │
        │  Pass CRM context in CUSTOM_DATA   │
        └────────────────────────────────────┘
                          │
                          ▼
              Call routed to extension/queue
                          │
                          ▼
        ┌────────────────────────────────────┐
        │  POP-UP SCREEN  ◄── your endpoint  │
        │  Phase 1: Ringing → look up caller │
        │  Phase 2: Talking                  │
        │  Phase 3: Hangup                   │
        └────────────────────────────────────┘
                          │
                          ▼
              ┌────────────────────────┐
              │  Voice Agent (AI bot)  │  ── (optional)
              │  intent reached        │
              └────────────────────────┘
                          │
                          ▼
        ┌────────────────────────────────────┐
        │  VOICEBOT  ◄── your endpoint       │
        │  Fetch dynamic CRM data            │
        │  Return user[] instructions to bot │
        └────────────────────────────────────┘
                          │
                          ▼
                     Call ends
                          │
                          ▼
        ┌────────────────────────────────────┐
        │  CDR NOTIFICATION  ◄── your endpoint│
        │  Full CDR + AI analysis            │
        │  Trigger follow-up actions         │
        └────────────────────────────────────┘
```

**Correlation key:** every step shares the same call ID — `IVR_UNIQUE_ID` (External Layer / VoiceBot) ≡ `ivrid` (Pop-Up Screen) ≡ `ivruniqueid` (CDR Notification) ≡ `CallID` (Call Log).

**Custom data flow:** `CUSTOM_DATA` set by External Layer travels with the call and appears in the Pop-Up Screen `customdata` field, the VoiceBot `CUSTOM_DATA` field, and the CDR `CustomData` field.

Skills used: [External Layer](skills/external-layer/README.md), [Pop-Up Screen](skills/popup-screen/README.md), [VoiceBot](skills/voicebot/README.md), [CDR Notification](skills/cdr-notification/README.md).

### Latency budget

| Step | Voicenter timeout | Recommended response time |
|---|---|---|
| External Layer | 5 seconds (then fallback layer) | < 1 s |
| Pop-Up Screen | 3 seconds (then no popup) | < 500 ms |
| VoiceBot | No strict limit | < 3 s (bot is mid-conversation) |
| CDR Notification | None — but ack first | Reply `200 OK` immediately, process async |

---

## Flow 2 — Outgoing call lifecycle (Click2Call)

Triggered from your CRM (a "Call" button) or any backend.

```text
       Agent clicks "Call" in CRM
                  │
                  ▼
    ┌─────────────────────────────┐
    │  EXTENSION LIST             │
    │  Resolve agent SIP code     │
    └─────────────────────────────┘
                  │
                  ▼
    ┌─────────────────────────────┐
    │  ACTIVE CALLS               │  (optional pre-check)
    │  Is the agent already busy? │
    └─────────────────────────────┘
                  │
                  ▼
    ┌─────────────────────────────┐
    │  CLICK2CALL                 │
    │  action=call                │
    │  Pass var_* CRM context     │
    │  Returns CALLID             │
    └─────────────────────────────┘
                  │
                  ▼
        Leg 1: agent extension rings
                  │
            agent answers
                  │
                  ▼
        Leg 2: customer dialed & bridged
                  │
                  ▼
    ┌─────────────────────────────┐
    │  REAL-TIME                  │  (live monitor)
    │  ExtensionEvent NEWCALL,    │
    │  ANSWER, HOLD, HANGUP       │
    └─────────────────────────────┘
                  │
                  ▼
    ┌─────────────────────────────┐
    │  MUTE RECORDING             │  (mid-call PCI compliance)
    │  ivrid = CALLID, state=1/0  │
    └─────────────────────────────┘
                  │
                  ▼
              call ends
                  │
                  ▼
    ┌─────────────────────────────┐
    │  CDR NOTIFICATION           │
    │  Two CDRs:                  │
    │   cdrType 9  = Leg1         │
    │   cdrType 10 = Leg2 (record)│
    └─────────────────────────────┘
```

Skills used: [Extension List](skills/extension-list/README.md), [Active Calls](skills/active-calls/README.md), [Click2Call](skills/click2call/README.md), [Real-Time](skills/real-time/README.md), [Mute Recording](skills/mute-recording/README.md), [CDR Notification](skills/cdr-notification/README.md).

---

## Flow 3 — Productive Dialer campaign

Outbound auto-dialing for sales / collections / surveys.

```text
       ┌─────────────────────────┐
       │ GetCampaignList         │
       │ Look up campaign Code   │
       └─────────────────────────┘
                   │
                   ▼
       ┌─────────────────────────┐
       │ EXTENSION LIST          │
       │ Resolve agent SIP codes │
       │ → AddMember             │
       └─────────────────────────┘
                   │
                   ▼
       ┌─────────────────────────┐
       │ BLACKLIST  (auto-skip)  │  ← ensure DNC numbers are blocked
       │ AddBlackList            │
       └─────────────────────────┘
                   │
                   ▼
       ┌─────────────────────────┐
       │ AddCallsBulk            │
       │ up to 100,000 leads     │
       │ + var_* CRM context     │
       └─────────────────────────┘
                   │
                   ▼
       ┌─────────────────────────┐
       │ StartCampaign           │
       └─────────────────────────┘
                   │
                   ▼
                Dialing
                   │
                   ▼
       ┌─────────────────────────┐
       │ CDR NOTIFICATION        │  cdrType 14 / 15
       │ + CALL LOG (historical) │
       └─────────────────────────┘
```

Skills used: [Productive Dialer](skills/productive-dialer/README.md), [Extension List](skills/extension-list/README.md), [Blacklist](skills/blacklist/README.md), [CDR Notification](skills/cdr-notification/README.md), [Call Log](skills/call-log/README.md).

---

## Flow 4 — Live wallboard / supervisor dashboard

Real-time situational awareness.

```text
   ┌──────────────────────┐         ┌────────────────────────┐
   │ EXTENSION LIST       │         │ REAL-TIME (socket.io)  │
   │ Static roster        │ ──────▶ │ AllExtensionsStatus    │  ◄── initial state
   │                      │         │ loginStatus            │
   └──────────────────────┘         └────────────────────────┘
                                              │
                                              ▼
                                  Incremental events
                                              │
                ┌───────────────┬──────────────┴──────────────┐
                ▼               ▼                              ▼
       ┌────────────────┐ ┌──────────────┐         ┌──────────────────┐
       │ ExtensionEvent │ │ QueueEvent   │         │ userStatusUpdate │
       │ NEWCALL/ANSWER │ │ JOIN/EXIT/   │         │ Login/Logout/    │
       │ HOLD/HANGUP    │ │ ABANDONED    │         │ Lunch / Other    │
       └────────────────┘ └──────────────┘         └──────────────────┘

   ┌──────────────────────┐
   │ ACTIVE CALLS         │  ◄── on-demand polling alternative when no socket
   │ GetExtensionsCalls   │
   │ GetQueuesCallers     │
   └──────────────────────┘
```

Skills used: [Real-Time](skills/real-time/README.md), [Active Calls](skills/active-calls/README.md), [Extension List](skills/extension-list/README.md), [Login/Logout](skills/login-logout/README.md).

The Real-Time SDK connection URL also yields the **monitor server hostname** that the [Mute Recording](skills/mute-recording/README.md) skill needs.

---

## Universal correlation key: the call ID

Every Voicenter API surfaces the same call identifier under different names. Treat them as one:

| Surface | Field name |
|---|---|
| Click2Call response | `CALLID` |
| External Layer request | `IVR_UNIQUE_ID` |
| VoiceBot request | `IVR_UNIQUE_ID` |
| Pop-Up Screen request | `ivrid` |
| Real-Time `ExtensionEvent` | `currentCall.ivrid` / `data.ivruniqueid` |
| Active Calls | `ivrid` |
| Mute Recording request | `ivrid` |
| CDR Notification | `ivruniqueid` |
| Call Log | `CallID` |

> Use this ID as the unique key in your database. Voicenter may retransmit webhook payloads — store it on a uniqueness constraint to deduplicate.

---

## Universal context channel: `CUSTOM_DATA` / `var_*` / `CustomData`

You can attach a flat key-value bag to a call once and read it everywhere downstream. Channels:

| Where you set it | Field |
|---|---|
| Click2Call request | `var_*` parameters |
| External Layer response | `CUSTOM_DATA` object |
| Productive Dialer `AddCall` | `CustomData` object |
| Lead Tracker `init()` | `visitorInfo` object |

| Where you read it back | Field |
|---|---|
| Pop-Up Screen request | `currentCall.customdata` |
| VoiceBot request | `CUSTOM_DATA` |
| CDR Notification | `CustomData` |
| Call Log | `CustomData` (request `fields: ["CustomData"]`) |
| Real-Time `ExtensionEvent` | `currentCall.customdata` |

This is how you carry CRM identifiers, lead source, ticket IDs, and campaign tags through an entire call without re-querying your CRM at every step.

> The data is **flat** — no nested objects. Keep keys simple (`var_clientID`, `Ticket_ID`).

---

## Choosing between Real-Time and Active Calls

| You need… | Use |
|---|---|
| A persistent live event stream | [Real-Time](skills/real-time/README.md) (socket.io) |
| A one-shot "what's happening right now" snapshot | [Active Calls](skills/active-calls/README.md) (REST) |
| Confirmation that a Login/Logout API call took effect | Real-Time `userStatusUpdate` |
| The dynamic monitor server hostname (for Mute Recording) | Real-Time connection URL |
| To check before initiating Click2Call ("is the agent free?") | Active Calls |

Real-Time is push, Active Calls is pull. They expose overlapping data — pick the one that fits your latency / infrastructure profile.

---

## Choosing between CDR Notification and Call Log

| You need… | Use |
|---|---|
| A record the moment a call ends | [CDR Notification](skills/cdr-notification/README.md) (webhook) |
| Historical analytics, reports, BI exports | [Call Log](skills/call-log/README.md) (REST query) |
| AI analysis (`aiData`: transcript, emotions, summary) | CDR Notification (only delivered via webhook) |
| To rebuild data for a date range you missed | Call Log with `fromdate`/`todate` |

The two are complementary: the recommended pattern is to subscribe to CDR Notification for live processing **and** keep Call Log as a backfill / audit tool.

---

## Idempotency, retries, and backpressure

- **Webhooks** (CDR, Pop-Up, External Layer, VoiceBot) — Voicenter may retry on network failures. Always deduplicate by `ivruniqueid` / `IVR_UNIQUE_ID`.
- **Reply fast** — for CDR especially, return `{"Err": 0, "Errdesc": "OK"}` immediately and process asynchronously.
- **REST APIs** — rate-limited (Call Log: 30 req/min, others vary). Add a small delay between successive calls.
- **Socket.io** — the SDK auto-reconnects. On reconnect, expect a fresh `AllExtensionsStatus` / `loginStatus` snapshot — re-initialize state.

---

## Where each skill fits

| Concern | Skill |
|---|---|
| "Where is the call coming from?" | Lead Tracker (campaign), External Layer (route), DID metadata |
| "Who is calling?" | Pop-Up Screen, External Layer (CRM lookup) |
| "What is the AI bot doing?" | VoiceBot |
| "What just happened to the call?" | Real-Time, CDR Notification |
| "What happened on this call yesterday?" | Call Log |
| "Make a call now" | Click2Call |
| "Make a thousand calls now" | Productive Dialer |
| "Don't call this number" | Blacklist |
| "Pause recording for the next 30 seconds" | Mute Recording |
| "Who is on shift?" | Real-Time, Active Calls, Extension List |
| "Set this agent's status" | Login/Logout |
| "Design and emit a new bot" | Agent Spec Designer → Intent Detail Author → JSON Assembler |

---

## Build-time pipeline — Bot authoring

The four flows above are **runtime** flows: they describe how skills compose during a live call. The `voicenter-bot-builder` plugin operates at a different layer — **build-time**. You use it once per bot, before any call happens, to generate the deployable JSON.

```text
        ┌──────────────────────────┐
        │  Agent Spec Designer     │      writes
        │  (Skill 1)               │ ──────────────▶ agent-spec.md
        │  Interview-driven        │   sections 1-4, 4.5,
        │                          │   5 stubs, 6 init, 7 init
        └────────────┬─────────────┘
                     │
                     ▼
        ┌──────────────────────────┐
        │  Intent Detail Author    │      updates
        │  (Skill 2)               │ ──────────────▶ agent-spec.md
        │  Per-intent language     │   section 5 detail per intent
        │  in batches              │
        └────────────┬─────────────┘
                     │
                     ▼
        ┌──────────────────────────┐
        │  JSON Assembler          │      emits
        │  (Skill 3)               │ ──────────────▶ bot-<id>-<date>.json
        │  Mechanical projection   │ ──────────────▶ bot-<id>-<date>.banner.md
        │  + §15.4 cross-ref       │
        └──────────────────────────┘
                     │
                     ▼
        Deploy via Voicenter platform UI
                     │
                     ▼
        At runtime, the deployed bot consumes the four runtime flows above:
        VoiceBot for CRM data, External Layer for routing, CDR Notification
        for post-call analytics, etc.
```

The pipeline's three skills hand off through one shared file (`agent-spec.md`); status markers per intent (`[structural]` → `[detailed]` → `[detailed-revisit]`) drive which skill is allowed to run when.

See [plugins/voicenter-bot-builder.md](plugins/voicenter-bot-builder.md) for the plugin overview and the per-skill docs for deep references.
