# Skill: `crm-onboarding`

CRM integration scoping & onboarding playbook — discovery, feasibility, and implementation-decision guidance for a new CRM integration.

> Source: [`plugins/voicenter-api/skills/crm-onboarding/SKILL.md`](../../../plugins/voicenter-api/skills/crm-onboarding/SKILL.md)
> Plugin: [voicenter-api](../../plugins/voicenter-api.md) · Direction: **Guided** · Transport: **Conversational**

---

> **Language.** Reply in the user's language: detect what they write — Hebrew→Hebrew, English→English — and mirror it, switching if they switch mid-conversation. This shapes the prose, questions, and `AskUserQuestion` option labels only. It does **not** change the artifacts produced — identifiers, JSON keys, BCP-47 language codes, API field names, and other data stay exactly as specified.

Guide the team through **scoping and specifying a new CRM integration** — the full discovery/feasibility process, implementation decisions, and responsibility boundaries for all three core services: Click2Call, Screen Pop, and Call History.

## When to use this skill

Use this skill when the team needs to:

- Scope a new CRM integration from scratch
- Run a discovery or feasibility meeting with a customer
- Choose the right implementation path (API / Chrome extension / BAT file)
- Decide who owns the screen pop (CRM vs Voicenter)
- Decide Push vs Pull for call history
- Create a spec or integration requirements document

---

## STEP 0 — CRM type: the first question

**Always ask this first.** Is the CRM:

- **On-premise** — installed software on the customer's machines or server
- **Web-based** — users work through a browser

**Why it matters:** this single answer determines which components are available:

| Component | On-Premise | Web-Based |
|-----------|-----------|-----------|
| Chrome extension (Click2Call button, screen pop) | ❌ | ✅ |
| Local BAT file component | ✅ | ❌ |
| API-based integration | ✅ | ✅ |

Everything else branches from this answer.

---

## STEP 1 — Entity & field mapping

Before any API decisions, map the CRM's data structure. Every later decision (who gets identified, where a call is logged, where the dial button lives) depends on this.

- **Which entities hold phone numbers?** Contact, Lead, Account, Opportunity, Ticket, custom?
- **Phone format in the CRM:** local `05XXXXXXXX`, international `+9725XXXXXXXX` / `9725XXXXXXXX`, mixed? Normalize early — Voicenter passes numbers in a specific format, so if the CRM stores a different format, screen-pop lookups will fail. Decide who normalizes: the CRM side or the integration layer.
- **CRM API capabilities** to verify before committing to any approach:
  - Search a record by phone number → required for screen pop
  - Create / update a record via API → required for auto-creation on answer
  - Accept inbound webhook requests → required for CDR Notification / Real-Time triggers
  - Build a direct deep-link URL to a record card

---

## SERVICE 1 — Click2Call

How it works: the CRM fires an HTTP request to Voicenter with three required parameters:

- `phone` — the agent's **station code** (SIP extension). Different per user — must be set when the agent logs into the CRM.
- `target` — the customer's phone number. Changes per call.
- `code` — the account code. Same for all users, provided by Voicenter during onboarding.

**Station code is a prerequisite.** The CRM user record must have a dedicated field for the station code. Confirm it exists — or that it can be added — before committing to this integration path.

**Scope boundary.** Voicenter provides the API and integration guidance. Placing the "Call" button inside the CRM UI is the CRM developers' responsibility, not Voicenter's.

**Fallback — no API capability:** if the CRM cannot fire an outbound HTTP request, use the Voicenter **Chrome extension**: users select any phone number in the browser and right-click to dial. This is a browser-only option and is not an API integration.

### Discovery questions

1. Does a station code field exist on the CRM user, or can one be added?
2. How will the station code be populated automatically when the agent logs in?
3. Can the CRM fire an outbound HTTP request on a button click?
4. Has the CRM integrated with telephony systems before? If yes — how was the PBX user ↔ CRM user mapping handled?

---

## SERVICE 2 — Screen Pop

### Key decision: who owns the pop?

**Does the CRM open the customer card, or does Voicenter?**

#### Option A — CRM owns the pop

The CRM receives a trigger from Voicenter and handles opening the card itself. Three delivery methods:

1. **CRM's own API** — Voicenter calls the CRM's documented endpoint per event
2. **Real-Time webhook** — Voicenter POSTs to a URL the CRM exposes on each event
3. **Socket.IO** — the CRM connects to Voicenter's real-time event stream and listens

**Requires a mapping field:** the CRM user must have a field that holds their PBX extension/user ID, so incoming events can be routed to the right agent. Locate this field early.

#### Option B — Voicenter owns the pop

- **B.1 Chrome extension (web CRM):** each agent installs the extension. The CRM builds a URL endpoint that receives phone + call params and returns JSON with customer details + a URL to the card. The extension opens that URL.
- **B.2 Local component (on-premise CRM):** a locally installed component runs a **BAT file** to open the record in the local system when the CRM cannot accept an inbound trigger.

### Trigger stage rules

There are three stages where Voicenter can send a trigger: **ringing, answer, hangup.**

| Stage | What fires | Rule |
|-------|------------|------|
| Ringing | Fires **per ringing station** (multiple in parallel) | **Notification only** — never create entities (duplicates risk) |
| Answer | Fires **once** for the answering station only | Screen pop + entity creation + call association |
| Hangup | Fires per station | **Use CDR instead** — single, comprehensive post-call record |

**Key rules:**

- Create records on **answer**, not ring — ring fires per parallel station and causes duplicates.
- At hangup, prefer the **CDR Notification** (arrives once, comprehensive) over a real-time hangup event.

### No-match behavior (unidentified caller)

Decide what happens when the phone number isn't found:

- Show "unknown caller" bubble — agent handles manually
- **Auto-create a record on answer** (recommended if auto-create): define entity, name format (`"Unknown customer"`), phone field, owner, source, initial status, and de-duplication logic (check by phone before re-creating)
- Show a "Create record" button pre-filled with the number

### Multiple-match resolution

If a phone number appears on more than one record, decide: first created / last updated / all results (list view) / priority by entity type (e.g., Account before Lead).

### Discovery questions

1. Who owns the pop — CRM or Voicenter?
2. Trigger delivery method (CRM API / webhook / Socket.IO / extension / BAT)?
3. Which stages should trigger (ring = notify only / answer = create+pop / hangup = CDR)?
4. PBX-user ↔ CRM-user mapping field?
5. Which entities and fields to search on incoming call?
6. What to display in the pop (entity name, status, owner, last interaction)?
7. Multiple-match resolution?
8. No-match behavior — and auto-create fields if applicable?

---

## SERVICE 3 — Call History logging

|  | CDR Notification (Push) | Call Log API (Pull) |
|--|--------------------------|----------------------|
| Full Transcription | ✅ **(only here)** | ❌ |
| AI Analysis | ✅ automatic per call | Via GetCallHistory (extra step per CallID; no transcription) |
| Storage | Stored in the CRM | Not stored in the CRM |
| Best for | Reports, internal triggers, transcription | Display-only, no storage needed |
| Disadvantage | Consumes CRM storage | No transcription; AI requires an extra fetch |

**Decision rule:** if the customer needs transcription, or wants to run reports / fire internal triggers from call data → **CDR Notification (Push)**. Display-only without storage needs → **Call Log (Pull)** may suffice.

### Discovery questions

1. CDR Notification (Push) or Call Log API (Pull)?
2. Is transcription needed?
3. Is AI analysis needed (summary, emotions, insights)?
4. Which entity logs the call (Activity / Task / Call Log / Ticket / custom)?
5. Which fields to save (recording link, summary, duration, status, agent, queue, DID, custom vars)?
6. Who is the call associated to — in what order? (Recommend same entity priority as screen pop search.)
7. Should Voicenter update any status or field on the record after logging?

---

## Decision Checklist

1. CRM type: on-premise / web
2. Entities + phone format + normalization owner
3. CRM API capabilities: search / create / update / webhook endpoint / deep-link
4. Click2Call: API vs Chrome extension
5. Click2Call: station code field exists + auto-populate at login
6. Screen Pop: who owns it (CRM / Voicenter)
7. Trigger delivery method (CRM API / webhook / Socket.IO / extension / BAT)
8. Trigger stages: ring = notify only / answer = create+pop / hangup = CDR
9. PBX ↔ CRM user mapping field
10. Multiple-match resolution
11. No-match behavior + auto-create fields if applicable
12. Call history: CDR Push vs Call Log Pull
13. Transcription / AI analysis needed?
14. Logging entity + association order + fields to save + status updates

---

## Tips

- **Start with CRM type (Step 0)** — local vs web decides which components are possible before any other discussion.
- **Station code is a prerequisite for Click2Call** — if the CRM user has no station code field and can't add one, the API path is blocked.
- **"Who owns the pop"** is the architectural fork in screen pop — answer it before designing anything else.
- **Create on answer, not ring** — ring is multiplied across parallel stations; answer is a single event.
- **CDR over real-time hangup** — CDR is a single, complete post-call record; real-time hangup has the same multiplicity problem as ring.
- Ask for the customer's existing telephony docs if they've integrated before — saves significant scoping time.
- Never include credentials or passwords in spec documents — use a separate secure channel.
- Voicenter supplies the extension list and account code during onboarding — they are not the integration team's responsibility to generate.

---

## Related skills

- [Click2Call](../click2call/README.md) — full API reference for outbound call initiation
- [Pop-Up Screen](../popup-screen/README.md) — Chrome extension screen pop endpoint reference (Option B.1)
- [CDR Notification](../cdr-notification/README.md) — push webhook with call data + AI + transcription after each call ends
- [Call Log](../call-log/README.md) — pull API for historical call records (no AI)
- [GetCallHistory](../get-call-history/README.md) — pull AI analysis per CallID (no transcription)
- [Real-Time](../real-time/README.md) — Socket.IO / webhook triggers for ring, answer, hangup events
- [Extension List](../extension-list/README.md) — retrieve valid SIP codes / station codes for Click2Call setup
