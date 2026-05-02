# Glossary

Voicenter-specific terminology used across the marketplace, plugin manifests, and skill documents.

---

| Term | Meaning |
|---|---|
| **Account** | A top-level Voicenter tenant. Houses extensions, users, departments, DIDs. |
| **AccountID** | Numeric ID of a department/account (returned by Extension List). |
| **AI Data (`aiData`)** | Optional structured AI analysis attached to a CDR — transcript, emotions, summary, Q&A. |
| **CALLID** | The call's unique ID, returned by Click2Call. Same value as `ivrid` / `ivruniqueid` / `IVR_UNIQUE_ID` elsewhere. |
| **Campaign Code** | Stable identifier for a Productive Dialer campaign (the `Code` field, not the display name). |
| **CDR** | Call Detail Record — the full record of a single call (parties, timing, status, recording, etc.). |
| **CdrType** | Numeric type of a CDR (1 = Incoming, 4 = Extension Outgoing, 9/10 = Click2Call legs, 14/15 = Productive Dialer legs, etc.). |
| **Click2Call** | Voicenter's outbound 2-leg dialing primitive — Leg 1 to the agent, Leg 2 to the customer. |
| **Code (`code` / `Code`)** | The organization API token used by all REST skills. Lowercase or uppercase per endpoint — match the skill page exactly. |
| **CPanel** | The Voicenter web admin console at [cpanel.voicenter.com](https://cpanel.voicenter.com). |
| **CUSTOM_DATA / CustomData / var_\*** | A flat key-value bag carried with a call across External Layer → Pop-Up → VoiceBot → CDR. |
| **DID** | A virtual phone number — a destination an external caller can dial. Tied to IVR layers and DID-pool features (Lead Tracker). |
| **DID pool** | A group of DIDs assigned dynamically per visitor by Lead Tracker. |
| **DTMF** | Touch-tone digits collected during an IVR layer. Default `"0"` if none collected. |
| **EventsSDK** | The Voicenter socket.io client used by the Real-Time skill. |
| **Extension** | A SIP endpoint inside a Voicenter account. Identified by its **SIP code** (e.g. `SIPSIP1`). |
| **External Layer** | An IVR layer configured to call your external endpoint mid-flow to make routing decisions. |
| **`ivrid`** | The call ID, as used in Pop-Up Screen, Active Calls, and Mute Recording. |
| **`ivruniqueid`** | The call ID, as used in CDR Notification and elsewhere. |
| **`IVR_UNIQUE_ID`** | The call ID, as used in External Layer and VoiceBot request payloads. |
| **IVR layer** | A node in the Voicenter IVR tree — plays prompts, collects DTMF, routes to extensions / queues / sub-layers / external endpoints. |
| **`LAYER_ID`** | The current IVR layer ID. Used by VoiceBot/External Layer to multiplex multiple intents on a single endpoint. |
| **Login type** | Authentication mode for the Real-Time SDK — `token`, `account`, or `user`. |
| **Mini External IVR** | Voicenter's name for the External Layer feature on a layer (CPanel checkbox: "Allow mini external IVR"). |
| **Monitor server** | A per-account HTTPS endpoint (e.g. `monitor1.voicenter.co`) used by the Mute Recording API and discovered through the Real-Time SDK. |
| **Pop-Up Screen** | The screen-pop webhook Voicenter calls during the Ringing/Talking/Hangup phases of an incoming call. |
| **Productive Dialer** | Voicenter's auto-dialer — manages campaigns, agent membership, scheduled callbacks. |
| **Queue** | An IVR construct that holds incoming callers until an agent is available. |
| **`representativeStatus`** | Numeric agent state: 1=Login, 2=Logout, 3=Lunch, 5=Admin, 7=Private, 9=Other, 11=Training, 12=Team meeting, 13=Brief. |
| **SIP code** | The string identifier of an extension (e.g. `SIPSIP1`). Used as `phone` in Click2Call, `extension` in Call Log, `ExtensionUser` in Login/Logout, `Member` in Productive Dialer. |
| **SpeedDial** | A short internal number assigned to an extension. |
| **Token (Real-Time)** | A long-lived secret used by the EventsSDK `token` login mode. |
| **Token (Lead Tracker)** | A pool-scoped token embedded in browser JS. |
| **UserId** | The numeric ID of a Voicenter CPanel user (used by Login/Logout). |
| **VoiceBot / Voice Agent** | Voicenter's AI conversational agent. Calls your VoiceBot endpoint for dynamic data mid-conversation. |

---

## Date and time conventions

- All dates in **Call Log** requests must be **GMT+0** (`fromdate` / `todate` in ISO 8601).
- Israeli local time is **GMT+2** (or **GMT+3** during summer). Convert before sending.
- **CDR Notification** `time` field is **Epoch seconds** in the **account's local timezone**.
- **Productive Dialer** `OriginateTime` is **Epoch seconds**. Use `IsDateLocal: "true"` to send local time, `false` for GMT+0.

## Phone number format

Voicenter uses **E.164 without the `+`**.

| Country | Example | Wrong |
|---|---|---|
| Israel | `972501234567` | `+972501234567`, `0501234567` |
| US | `14155550123` | `+14155550123` |

Local-format numbers (e.g. `0501234567`) are accepted only on incoming-side fields like `CALLER_ID` from the Voicenter side, but always **emit** E.164-without-`+` on outbound.

## Error code conventions

Each skill defines its own error structure, but two patterns dominate:

- `ERR` / `DESC` (Active Calls, Extension List, Real-Time login)
- `ErrorCode` / `ErrorMessage` / `Description` (Blacklist, Productive Dialer, Click2Call as `ERRORCODE`)
- `ERROR_NUMBER` / `ERROR_DESCRIPTION` / `STATUS_CODE` (Call Log)
- `Err` / `Errdesc` (CDR Notification — your *response*)

Do not assume cross-skill consistency — check the matching skill page.
