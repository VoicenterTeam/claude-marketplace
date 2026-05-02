# 🎬 Hot Lead Sniper — Live Prospect Demo

A 10-minute live showcase that builds a "call-me-back-now" widget end-to-end in front of a prospect, ending with **their own phone ringing** and an AI voicebot briefing your rep.

Demonstrates 5 skills from the Voicenter marketplace working together: **click2call**, **voicebot**, **lead-tracker**, **blacklist**, and optionally **popup-screen** + **external-layer**.

---

## 📌 Two ways to use this script

### Mode A — Live demo (recommended for prospects)
Paste the prompts in **Beats 2–5 one at a time**. Between each prompt: open the file Claude wrote, point at it, talk to the prospect. The pacing *is* the demo. See [Live demo flow](#-live-demo-flow-10-min) below.

### Mode B — Build mode (for rehearsal)
If you want Claude to scaffold the whole project in one shot so you can rehearse running it, use the [single mega-prompt](#-mode-b-mega-prompt-rehearsal-only) at the bottom. **Do not use this in front of a prospect** — the magic is in the per-skill reveal.

---

## 🛠 Pre-demo setup (do 30 min before)

1. **Clean folder + dependencies:**
   ```bash
   mkdir hot-lead-sniper && cd hot-lead-sniper
   npm init -y && npm install express dotenv
   ```
2. **Verify plugins are enabled** — Run `/plugin` and confirm `voicenter-api` and `voicenter-mcp` show **Enabled**.
3. **MCP authenticated** — Run the `/setup` skill once so the OAuth flow is fresh.
4. **Tunnel running** for the voicebot/popup webhooks:
   ```bash
   ngrok http 3000
   ```
   Copy the `https://...ngrok-free.app` URL.
5. **`.env` prepared** in the project root:
   ```env
   VOICENTER_API_CODE=<your-org-api-token>
   VOICENTER_REP_EXTENSION=<your-own-desk-extension, e.g. 1001>
   VOICENTER_CALLER_ID=<your-DID-for-outbound>
   NGROK_URL=https://your-tunnel.ngrok-free.app
   PORT=3000
   ```
6. **Whitelist your server's public IP** in the Voicenter CPanel (required for code-based APIs).
7. **Open Claude Code** in the folder. Show the empty terminal to the prospect.

---

## 🎙 Live demo flow (10 min)

### Beat 1 — Set the stage *(30 sec, no prompt)*

> "I'm going to build a feature that calls a website visitor's phone within seconds of them clicking a button — live, no pre-written code. Watch the plugin do the work."

Run:
```
/plugin
```
Point to `voicenter-api` with 14 skills + `voicenter-mcp`. *"These are pre-built API skills Claude can use — production-grade integrations, not toy examples."*

---

### Beat 2 — Generate the widget *(prompt 1)*

**Paste this:**

```
Build a "Call me now" callback widget — a small floating card in the bottom-right
of the page with a phone input, a consent checkbox, and a button. When clicked, it
POSTs the phone number plus the visitor's page journey (URL, UTM params, time-on-
page, referrer) to /api/callback. Use vanilla JS — no framework. Keep it under 80
lines, drop-in for any HTML page. Save as public/widget.html.
```

✅ Claude writes the widget. Open the file in the editor, scroll through it.
**Talking point:** *"That's just a starting point — the real magic is what happens when you click."*

---

### Beat 3 — The Click2Call backend *(prompt 2 — invokes `click2call` + `blacklist`)*

**Paste this:**

```
Use the click2call skill to build the /api/callback Express endpoint in server.js.
It should:
- validate the phone number (E.164-ish)
- use the blacklist skill to honor opt-outs before dialing
- trigger a two-leg Voicenter call: leg 1 to my rep extension from
  VOICENTER_REP_EXTENSION, leg 2 to the visitor's number
- pass the visitor's page, UTM, and time-on-page as CustomData so it ends up
  in the CDR for attribution

Use dotenv. Return { ok: true, callId } on success, { ok: false, error } otherwise.
```

✅ Claude pulls in the **click2call** and **blacklist** SKILL.md files. Watch it write the exact API call with all required fields.

**Talking point:** *"Notice it knows the exact endpoint, response shape, and error codes — because the skill ships that knowledge. Zero docs reading."*

---

### Beat 4 — The AI voicebot brief *(prompt 3 — invokes `voicebot`)*

**Paste this:**

```
Use the voicebot skill to add a POST /webhooks/voicenter/voicebot endpoint to
server.js. When my rep picks up leg 1 first, the voicebot should greet the rep
with a whisper-coaching message like:

  "Hot lead from the pricing page — they spent {timeOnPage} seconds and came
   from {utm.source}. Connecting now."

Pull the data from CustomData passed by click2call. After the brief, the voicebot
should connect leg 2 (the visitor) to the rep automatically.
```

✅ Claude wires the voicebot endpoint pulling CustomData from the call context.

**Talking point:** *"This is whisper coaching — your rep gets briefed by AI in the 2 seconds before the visitor's phone connects."*

---

### Beat 5 — Lead tracker attribution *(prompt 4 — invokes `lead-tracker`)*

**Paste this:**

```
Use the lead-tracker skill to wire the Voicenter Lead Tracker JS SDK into
public/widget.html. Initialize it on page load to capture UTMs, GCLID, and a
persistent visitor ID via cookie. Expose getVisitorId() globally so the widget
can include it in the /api/callback payload, closing the attribution loop from
ad click to CDR.
```

✅ Claude adds the SDK and wires `window.VoicenterLeadTracker`.

**Talking point:** *"Now every call is tied back to the marketing source — Voicenter closes the loop from ad click to CDR to revenue."*

---

### Beat 6 — Run it & RING THE PROSPECT'S PHONE 📞 *(the wow)*

In the terminal:
```bash
node server.js
```

Open `http://localhost:3000/widget.html` in the browser.

**Turn to the prospect:**
> "What's your mobile number?"

Type their number into the form. Click **Call me now**.

Their phone rings within ~4 seconds. They pick up. They hear *your* voicebot say to *your* rep: *"Hot lead from the pricing page, connecting now."* — and then they're on the line with you.

🎤 **Mic drop.**

---

## 🎁 Bonus beats (if they want more)

### Bonus A — Popup-screen for the rep *(prompt 5)*

```
Use the popup-screen skill to add a POST /webhooks/voicenter/popup endpoint.
When the rep's phone rings, return the visitor's full journey as CRM data:
pages viewed, time on each, UTM source, GCLID, referrer. So the rep's screen
pops with full context the moment the call rings.
```

### Bonus B — Smart routing *(prompt 6)*

```
Use the external-layer skill to add a POST /webhooks/voicenter/external-layer
endpoint. Route logic:
- if utm_campaign=enterprise → route to extension 2001 (enterprise queue)
- otherwise → extension 2002 (SMB queue)
- outside 9-17 local time → send to voicemail (HANGUP with prompt)
```

### Bonus C — Live MCP query *(no code, just conversation)*

In Claude Code, ask:
```
Using the Voicenter MCP, show me the last 5 calls that came in today,
their outcomes, and any custom data attached.
```

✅ MCP returns live CDR data — proving the entire round trip works end to end.

---

## 🎯 Talking points to weave throughout

- *"14 APIs, zero docs reading."* The plugin teaches Claude every endpoint, request format, and gotcha.
- *"From form to ringing phone in ~10 minutes of prompts."* What used to take a sprint.
- *"Composable skills."* Click2Call → voicebot brief → CRM popup → smart routing → CDR analytics — all wired by AI.
- *"Production-shaped from minute one."* Env vars, blacklist compliance, error handling — because the skills enforce best practice.

---

## ⚠️ Common live-demo gotchas

| Symptom | Fix |
| :-- | :-- |
| `EADDRINUSE :3000` | Kill the leftover Node process: `npx kill-port 3000` |
| Click2Call returns `Err: 9` (auth) | Server's public IP isn't whitelisted in CPanel |
| Phone never rings | Check rep extension is logged in and not on DND |
| Voicebot webhook never fires | `NGROK_URL` in `.env` is stale — ngrok URLs change on each restart |
| Lead Tracker SDK 404 | The SDK URL changed — re-run prompt 4 and let Claude pull the latest |

---

## 🤖 Mode B — Mega prompt (rehearsal only)

Use this **only for rehearsal**, never in front of a prospect. It builds the whole thing in one Claude turn.

```
Build a "Hot Lead Sniper" Express app in this folder using the Voicenter
marketplace skills:

1. Use the lead-tracker skill to build public/widget.html — a floating
   bottom-right callback card with phone input, consent checkbox, and
   "Call me now" button. Initialize the Voicenter Lead Tracker JS SDK
   on page load (UTM, GCLID, visitorId via cookie). On submit, POST to
   /api/callback with phone, page, utm, visitorId, referrer, timeOnPage.

2. Use the click2call and blacklist skills to build server.js with a
   POST /api/callback endpoint that validates the phone, checks the
   blacklist, then triggers a Voicenter two-leg call (leg 1 = my rep
   extension from VOICENTER_REP_EXTENSION env var, leg 2 = visitor).
   Pass page+utm+timeOnPage as CustomData.

3. Use the voicebot skill to add POST /webhooks/voicenter/voicebot to
   server.js. When the rep picks up first, whisper a one-line brief
   built from CustomData ("Hot lead from {utm.source}, {timeOnPage}s on
   {page} — connecting now.") then connect leg 2.

4. Create .env.example with VOICENTER_API_CODE, VOICENTER_REP_EXTENSION,
   VOICENTER_CALLER_ID, NGROK_URL, PORT=3000.

5. Create README.md with setup steps: npm install, fill .env, run ngrok,
   start server, open widget.html, click Call me now.

Use dotenv. Keep all files lean and production-shaped — env vars, error
handling, no hardcoded secrets.
```

---

## 📦 What this demo proves

- The Voicenter marketplace plugin **collapses integration time** from days to minutes
- **Skills compose** — they're designed to plug into each other
- The MCP server gives **live API access** alongside the documented skills
- A non-Voicenter developer using Claude Code can ship a real Voicenter integration **without ever opening API docs**

---

*Built with the [Voicenter Claude Code marketplace](https://github.com/VoicenterTeam/claude-marketplace).*
