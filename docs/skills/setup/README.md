# Skill: `setup` (voicenter-mcp)

Connect Claude Code to the Voicenter MCP server using OAuth.

> Source: [`plugins/voicenter-mcp/skills/setup/SKILL.md`](../../../plugins/voicenter-mcp/skills/setup/SKILL.md)
> Plugin: [voicenter-mcp](../../plugins/voicenter-mcp.md)

---

## What it does

Walks the developer through connecting Claude Code to `https://mcp01.voicenter.co/mcp`. After this skill runs once, Claude can perform any Voicenter operation directly from a chat conversation — list extensions, fire Click2Call, query CDRs, etc.

There is no code to write, no tokens to paste, no environment variables to set. Voicenter's MCP server uses **OAuth**, and Claude Code handles the entire flow.

---

## When to invoke

- A developer just installed `voicenter-mcp` and wants to verify the connection.
- Claude reports `permission denied` from the Voicenter MCP and you need to re-authenticate.
- The team is switching Voicenter accounts.

---

## How OAuth works here

1. The plugin manifest declares the MCP server URL ([`plugins/voicenter-mcp/.claude-plugin/plugin.json`](../../../plugins/voicenter-mcp/.claude-plugin/plugin.json)).
2. The first time Claude Code calls a Voicenter MCP tool, the server returns "auth required."
3. Claude Code launches your default browser to the Voicenter authorization page.
4. You sign in to Voicenter and approve the requested scopes.
5. Claude Code receives the OAuth token, stores it securely, and refreshes it automatically.

The plugin manifest is intentionally minimal — only the server URL and `type: http`. No secrets are checked in or stored locally.

---

## Step-by-step

### 1 — Install the plugin

```text
/plugin marketplace add VoicenterTeam/claude-marketplace
/plugin install voicenter-mcp@voicenter
```

### 2 — Trigger any Voicenter action

Ask Claude in chat:

```text
List all my Voicenter extensions
```

Claude attempts the call, sees "auth required," and opens the browser.

### 3 — Approve in the browser

- Sign in to Voicenter.
- Read and approve the requested scopes.
- The browser tab confirms success — return to Claude Code.

### 4 — Verify

The same prompt now returns your real extension list. The MCP plugin is live.

---

## Things you can ask once connected

| Prompt | Underlying API (skill) |
|---|---|
| "List all my Voicenter extensions" | [extension-list](../extension-list/README.md) |
| "Initiate a click2call from extension SIPSIP to 0501234567" | [click2call](../click2call/README.md) |
| "Show me all calls from the last 7 days" | [call-log](../call-log/README.md) |
| "Add 0501234567 to the blacklist" | [blacklist](../blacklist/README.md) |
| "List all active campaigns in the dialer" | [productive-dialer](../productive-dialer/README.md) |
| "Log in agent user 123456 on extension SIPSIP" | [login-logout](../login-logout/README.md) |
| "What calls are active right now?" | [active-calls](../active-calls/README.md) |
| "Mute recording on extension SIPSIP" | [mute-recording](../mute-recording/README.md) |

---

## Re-authenticating

If your OAuth session expires or you switch Voicenter accounts, the next call automatically re-launches the browser flow. No manual cleanup required.

To force re-auth:

1. Disconnect the MCP server in Claude Code.
2. Reconnect — Claude Code launches the browser again.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| Browser flow does not start | Explicitly trigger a Voicenter tool ("list my extensions"). The connection attempt is what triggers OAuth. |
| Authorization page errors | Confirm your Voicenter account has API/MCP access enabled. Email [[email protected]](mailto:[email protected]) if not. |
| Connected but tools return "permission denied" | Disconnect and re-authenticate to obtain a token with full scopes. |
| Stale data | Tokens cache responses. Reconnect to refresh. |

---

## Configuration reference

[`plugins/voicenter-mcp/.claude-plugin/plugin.json`](../../../plugins/voicenter-mcp/.claude-plugin/plugin.json):

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

The `type: http` field is mandatory for HTTP-based MCP servers — without it Claude Code cannot register the connection.

---

## Related

- [Plugin: voicenter-mcp](../../plugins/voicenter-mcp.md)
- [Authentication overview](../../authentication.md)
- [Companion plugin: voicenter-api](../../plugins/voicenter-api.md)
