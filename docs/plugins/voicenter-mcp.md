# Plugin: `voicenter-mcp`

Live access to the Voicenter platform from inside any Claude Code conversation.

The plugin registers an HTTP MCP server pointing at `https://mcp01.voicenter.co/mcp`. Claude can then invoke any Voicenter operation as a tool call — list extensions, initiate Click2Call, query CDRs, manage the dialer — without you writing any wrapper code.

---

## Manifest

[`plugins/voicenter-mcp/.claude-plugin/plugin.json`](../../plugins/voicenter-mcp/.claude-plugin/plugin.json):

```json
{
  "name": "voicenter-mcp",
  "description": "Live Voicenter API access via MCP server at mcp01.voicenter.co",
  "version": "1.1.1",
  "mcpServers": {
    "voicenter": {
      "type": "http",
      "url": "https://mcp01.voicenter.co/mcp"
    }
  }
}
```

| Field | Value | Notes |
|---|---|---|
| Name | `voicenter-mcp` | |
| Version | `1.1.1` | Tracks the marketplace version |
| Server type | `http` | Required for HTTP-based MCP servers |
| URL | `https://mcp01.voicenter.co/mcp` | Voicenter-hosted, OAuth-protected |

The plugin ships a single skill, [setup](../skills/setup/README.md), which guides a developer through the OAuth connection.

---

## Authentication

OAuth, fully automatic. Claude Code launches the browser flow on first use; tokens are stored and refreshed automatically. There are **no environment variables**, **no shared secrets**, and **no IP whitelisting** required.

If you switch Voicenter accounts or your session expires, the next call re-launches the OAuth flow.

See [authentication.md](../authentication.md#1-oauth-voicenter-mcp) and [skills/setup/README.md](../skills/setup/README.md) for details.

---

## Capabilities

The MCP server proxies the same Voicenter functionality the [`voicenter-api`](voicenter-api.md) skills document — but you do not have to write the calls yourself. Examples of prompts that work out of the box:

| Prompt | Underlying API |
|---|---|
| "List all my Voicenter extensions" | Extension List |
| "Initiate a click2call from extension SIPSIP to 0501234567" | Click2Call |
| "Show me all calls from the last 7 days" | Call Log |
| "Add 0501234567 to the blacklist with name 'Opted out'" | Blacklist |
| "List all active campaigns in the dialer" | Productive Dialer (GetCampaignList) |
| "Log in agent user 123456 on extension SIPSIP" | Login/Logout |
| "What calls are active right now?" | Active Calls |
| "Mute recording on extension SIPSIP" | Mute Recording |

The full surface depends on the OAuth scopes your Voicenter account has been granted. If a tool returns "permission denied," disconnect and re-authenticate to obtain a fresh token.

---

## Installation

```text
/plugin marketplace add VoicenterTeam/claude-marketplace
/plugin install voicenter-mcp@voicenter
```

Then trigger any Voicenter action; the OAuth browser flow runs automatically.

Verify with:

```text
/plugin
```

`voicenter-mcp` should be **Enabled**.

---

## When to use this plugin

Use the MCP plugin when you want Claude to **operate** the Voicenter platform — exploration, ad-hoc operations, and live debugging of an integration you are building.

Use the [`voicenter-api`](voicenter-api.md) plugin (skills) when you want Claude to **write code** for your application that talks to Voicenter directly. Most teams install both.

---

## Troubleshooting

| Symptom | Resolution |
|---|---|
| OAuth flow does not launch | Trigger any Voicenter tool ("list my extensions") to force connection |
| Authorization page errors | Confirm your Voicenter account has API/MCP access — email [[email protected]](mailto:[email protected]) |
| Tool call returns "permission denied" | Disconnect and re-authenticate with full scopes |
| Stale data | Tokens cache; reconnect to refresh |

---

## Related documentation

- [Skills · setup](../skills/setup/README.md)
- [Authentication](../authentication.md)
- [Architecture & call flows](../architecture.md)
- [Companion plugin: voicenter-api](voicenter-api.md)
