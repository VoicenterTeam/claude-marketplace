# CLAUDE.md — agent guide for the Voicenter Claude Code marketplace

This repository ships **three Claude Code plugins** that integrate with the Voicenter telephony platform:

- `voicenter-mcp` — live API access through the OAuth-protected MCP server at `mcp01.voicenter.co`.
- `voicenter-api` — 14 integration skills (one folder per Voicenter API).
- `voicenter-bot-builder` — 3 build-time authoring skills that produce deployable Voicenter bot JSON via a Spec Designer → Intent Detail Author → JSON Assembler pipeline.

The repo is **pure documentation and configuration** — no build, no tests, no runtime. Your job as an agent is to keep the marketplace, plugin manifests, source `SKILL.md` files, and the deep [`docs/`](docs/README.md) tree consistent with each other.

> Read the full reference under [`docs/`](docs/README.md). The most important pages: [docs/architecture.md](docs/architecture.md), [docs/authentication.md](docs/authentication.md), [docs/glossary.md](docs/glossary.md). Per-skill deep dives live under [docs/skills/](docs/skills/).

---

## Repo layout

```
.claude-plugin/marketplace.json     ← the marketplace package
plugins/
  voicenter-mcp/
    .claude-plugin/plugin.json      ← HTTP MCP server config
    skills/setup/SKILL.md           ← OAuth setup skill
  voicenter-api/
    .claude-plugin/plugin.json      ← skills plugin manifest
    skills/<skill-name>/SKILL.md    ← one folder per API (14 total)
  voicenter-bot-builder/
    .claude-plugin/plugin.json      ← bot-authoring plugin manifest
    skills/<skill-name>/SKILL.md    ← one folder per pipeline stage (3 total)
docs/
  README.md, getting-started.md, architecture.md,
  authentication.md, glossary.md
  plugins/<plugin>.md               ← one page per plugin
  skills/<skill-name>/README.md     ← deep reference per skill (18 total)
README.md   CHANGELOG.md   DEMO.md   LICENSE
```

The 18 skills (1 in `voicenter-mcp`, 14 in `voicenter-api`, 3 in `voicenter-bot-builder`):

> **API + MCP (15):** `setup` · `voicebot` · `click2call` · `popup-screen` · `cdr-notification` · `external-layer` · `call-log` · `blacklist` · `mute-recording` · `extension-list` · `real-time` · `productive-dialer` · `login-logout` · `lead-tracker` · `active-calls`
>
> **Bot-builder (3):** `voicenter-bot-spec-designer` · `voicenter-bot-intent-detail-author` · `voicenter-bot-json-assembler`

---

## SKILL.md ↔ docs/ contract

The two trees are **paired** and must stay in sync:

| Source of truth (loaded by Claude Code at runtime) | Long-form reference (for humans + retrieval) |
|---|---|
| `plugins/voicenter-api/skills/<skill>/SKILL.md` | `docs/skills/<skill>/README.md` |
| `plugins/voicenter-mcp/skills/setup/SKILL.md` | `docs/skills/setup/README.md` |
| `plugins/voicenter-bot-builder/skills/<skill>/SKILL.md` | `docs/skills/<skill>/README.md` |

**When you change a SKILL.md, also update the matching `docs/skills/<skill>/README.md`** — same fields, same examples, same error codes. The docs page may add troubleshooting and patterns the SKILL.md does not need.

`SKILL.md` files must:

- Start with YAML frontmatter `--- name: <skill> description: ... ---`.
- Stay short (Claude loads them at runtime — terseness is a feature).
- For **API/MCP skills** (`voicenter-api`, `voicenter-mcp`), follow the section order: *When to use → Environment Variables → Endpoint → Authentication → Request → Response → Error codes → TypeScript → Tips → Related Skills*.
- **Bot-builder skills** (`voicenter-bot-builder`) are authoring skills, not API call wrappers, and intentionally use an authoring section order (e.g. *What it does → When to invoke → Pre-flight gates → Output contract → Anti-list*). Do not retrofit them to the API-skill order.

---

## Plugin manifest contract

Each `plugin.json` must conform to the official Claude Code plugin manifest schema:

- `voicenter-mcp/.claude-plugin/plugin.json` — must include `"mcpServers"` with `"type": "http"` and the URL `https://mcp01.voicenter.co/mcp`.
- `voicenter-api/.claude-plugin/plugin.json` — declares only metadata; skills auto-discover from `skills/`. Do **not** add `"skills": "./skills/"` — default discovery handles it (see [CHANGELOG.md](CHANGELOG.md)).
- `voicenter-bot-builder/.claude-plugin/plugin.json` — declares only metadata; skills auto-discover from `skills/`. Same default-discovery rule as `voicenter-api`.

Forbidden fields (removed in v1.1.0): `icon`, nested V2 marketplace duplicates.

When bumping a version, update **all four** in lockstep:

1. `.claude-plugin/marketplace.json` (`metadata.version` and each plugin's `version`)
2. `plugins/voicenter-mcp/.claude-plugin/plugin.json` (`version`)
3. `plugins/voicenter-api/.claude-plugin/plugin.json` (`version`)
4. `plugins/voicenter-bot-builder/.claude-plugin/plugin.json` (`version`)

Add a corresponding entry to [CHANGELOG.md](CHANGELOG.md).

---

## Voicenter API conventions to enforce in any code you generate

These are repeated in every skill page; treat them as house rules:

- **Phone numbers**: E.164 **without `+`** — `972501234567`, never `+972501234567` or `0501234567`.
- **JSON, not XML**: always include `format=json` for Click2Call (its default is XML).
- **Universal call ID**: `CALLID` ≡ `IVR_UNIQUE_ID` ≡ `ivrid` ≡ `ivruniqueid` ≡ `CallID`. Use it as the unique key in any database; deduplicate webhook deliveries on it.
- **Custom-data channel**: `var_*` (Click2Call) → `CUSTOM_DATA` (External Layer / VoiceBot) → `CustomData` (CDR / Call Log / Productive Dialer). Flat key-values only — no nested objects.
- **Webhook latency budget**: External Layer **5 s**, Pop-Up Screen **3 s**, CDR Notification — reply `200 OK` immediately and process async.
- **CORS for Pop-Up Screen**: `Access-Control-Allow-Origin: chrome-extension://ifiaikfdhcagbagdeflffjdammidpbio` is mandatory.
- **`code` vs `Code`**: case matters and is not interchangeable per endpoint. Match the SKILL.md exactly.
- **Server IP whitelisting**: every REST skill (`code`-based) requires the calling IP to be whitelisted in CPanel → API Settings.
- **Dates**: Call Log uses **GMT+0**; CDR Notification `time` is account-local Epoch; Productive Dialer `OriginateTime` defaults to GMT+0 unless `IsDateLocal: "true"` is sent.

The full reference is in [docs/glossary.md](docs/glossary.md) and [docs/authentication.md](docs/authentication.md).

---

## Authentication models (which skill uses which)

See [docs/authentication.md](docs/authentication.md) for the full matrix. Quick view:

| Auth model | Skills |
|---|---|
| OAuth (browser) | `voicenter-mcp` plugin (all access) |
| `code` / `Code` parameter (REST) + IP whitelist | `click2call`, `call-log`, `blacklist`, `extension-list`, `productive-dialer`, `login-logout`, `active-calls` |
| Webhook (no inbound auth — URL is the secret, HTTPS only) | `voicebot`, `popup-screen`, `cdr-notification`, `external-layer` |
| Socket.io (`token` / `account` / `user`) | `real-time` |
| Browser JS token | `lead-tracker` |
| Implicit (dynamic monitor server) | `mute-recording` |
| None — build-time authoring (no Voicenter API calls at runtime) | `voicenter-bot-spec-designer`, `voicenter-bot-intent-detail-author`, `voicenter-bot-json-assembler` |

Never put `VOICENTER_API_CODE` in client-side JavaScript — it is a server-only secret.

---

## How the four canonical call flows compose

Most integrations chain skills along one of these flows. See [docs/architecture.md](docs/architecture.md) for diagrams.

| Flow | Skill chain |
|---|---|
| **Incoming call lifecycle** | External Layer → Pop-Up Screen → VoiceBot → CDR Notification |
| **Outgoing call (Click2Call)** | Extension List → Active Calls (pre-check) → Click2Call → Real-Time → Mute Recording → CDR Notification |
| **Productive Dialer campaign** | GetCampaignList → Extension List → Blacklist → AddCallsBulk → StartCampaign → CDR / Call Log |
| **Live wallboard** | Real-Time + Active Calls + Extension List + Login/Logout |

The Real-Time SDK connection URL also yields the **monitor server hostname** required by Mute Recording.

---

## Common tasks

### Add a new skill

1. Create `plugins/<plugin>/skills/<skill>/SKILL.md` with the required frontmatter and the section order matching the plugin (API-skill order for `voicenter-api`/`voicenter-mcp`, authoring order for `voicenter-bot-builder`).
2. Create the matching `docs/skills/<skill>/README.md` (deep reference).
3. Add the row to the skill index in [docs/README.md](docs/README.md), [docs/architecture.md](docs/architecture.md), and the relevant `docs/plugins/<plugin>.md` page.
4. Cross-link from related skill pages (`Related skills` section).
5. Update the `description` in the plugin's `.claude-plugin/plugin.json` to reflect the new total.
6. Update the marketplace `keywords` if a new search term is warranted.

### Update an existing skill

1. Edit `plugins/voicenter-api/skills/<skill>/SKILL.md`.
2. Mirror the same edits in `docs/skills/<skill>/README.md` (it usually has more detail; preserve that).
3. Add a CHANGELOG entry only when behavior or surface area changes.

### Bump version

1. Update all four `version` fields (marketplace metadata + each plugin entry inside marketplace.json + each plugin's own plugin.json).
2. Add a CHANGELOG entry.
3. Confirm `/plugin` after install still reports all three plugins as **Enabled** with the right skill counts (1 + 14 + 3 = 18).

### Validate locally

There is no test runner. Manual validation:

- `/plugin marketplace add VoicenterTeam/claude-marketplace`
- `/plugin install voicenter-mcp@voicenter`, `voicenter-api@voicenter`, and `voicenter-bot-builder@voicenter`
- `/plugin` should show all three **Enabled**.
- For MCP, trigger any tool ("list my extensions") to verify OAuth + scopes.

---

## Pitfalls (real ones from the changelog)

- **Skills not registered** if SKILL.md frontmatter is missing the explicit `name:` field — this regressed in v1.1.0 and was fixed by adding `name:` everywhere.
- **MCP server fails to register** if `"type": "http"` is missing from `mcpServers.voicenter`.
- **Plugin cache** is sticky — bumping version is sometimes the only way to force `/reload-plugins` to re-sync.
- Don't add `"skills": "./skills/"` — default discovery handles it; an explicit value caused 0-skill loads previously.

---

## Resources

- **Full docs index** → [docs/README.md](docs/README.md)
- **Getting started** → [docs/getting-started.md](docs/getting-started.md)
- **Architecture** → [docs/architecture.md](docs/architecture.md)
- **Authentication** → [docs/authentication.md](docs/authentication.md)
- **Glossary** → [docs/glossary.md](docs/glossary.md)
- Live demo script → [DEMO.md](DEMO.md)
- Release history → [CHANGELOG.md](CHANGELOG.md)
- Voicenter API portal → https://www.voicenter.com/API
- CPanel → https://cpanel.voicenter.com
- Real-Time SDK → https://github.com/VoicenterTeam/VoicenterEventsSDK
- Developer support → [[email protected]](mailto:[email protected])
