---
name: setup
description: Connect Claude Code to the Voicenter MCP server using OAuth authentication
---

Help the developer connect Claude Code to the **Voicenter MCP server** at `mcp01.voicenter.co/mcp`.

## How authentication works

The Voicenter MCP server uses **OAuth** — not a static API token or environment variable. You do not need to configure any credentials manually. Claude Code handles the entire OAuth flow for you automatically when you first connect.

There is nothing to set in `.env` files, shell profiles, or environment variables. The `voicenter-mcp` plugin only needs the server URL, which is already configured in `plugin.json`.

## Step 1 — Install the plugin

In Claude Code:

```
/plugin install voicenter-mcp@voicenter
```

## Step 2 — Connect and authenticate

The first time Claude Code tries to use the Voicenter MCP server, it will detect that authentication is required and launch the OAuth flow automatically. You will be prompted to:

1. Open a browser window (or have it opened for you automatically).
2. Log in to your Voicenter account at the authorization page.
3. Grant Claude Code permission to access the Voicenter API on your behalf.
4. Return to Claude Code — the connection is established.

Claude Code stores the OAuth token securely and refreshes it automatically. You will only need to go through this flow once per device (or when your session expires).

## Step 3 — Verify the connection

Once authenticated, ask Claude:

```
List all my Voicenter extensions
```

Claude will call the MCP server live. If it responds with your extension list, you are connected.

## What you can do once connected

| Prompt | What happens |
|---|---|
| "Initiate a click2call from extension SIPSIP to 0501234567" | Calls the Click2Call API |
| "Show me all calls from the last 7 days" | Queries the Call Log API |
| "Add 0501234567 to the blacklist" | Calls the Blacklist API |
| "List all active campaigns in the dialer" | Calls the Dialer GetCampaignList API |
| "Log in agent user 123456 on extension SIPSIP" | Calls the Login/Logout API |
| "What calls are active right now?" | Calls the Active Calls API |

## Re-authenticating

If your OAuth session expires or you switch Voicenter accounts, Claude Code will prompt you to authenticate again the next time it tries to use the MCP server. This is handled automatically — you do not need to clear any tokens manually.

## Troubleshooting

**Claude does not launch the OAuth flow** — Try explicitly asking Claude to use a Voicenter tool (e.g. "list my extensions"). This triggers the connection attempt and the OAuth prompt.

**Authorization page shows an error** — Make sure your Voicenter account has API / MCP access enabled. Contact [api@voicenter.com](mailto:api@voicenter.com) if it does not.

**Connection works but Claude cannot perform an action** — The OAuth scope granted may not include the required permission. Disconnect and re-authenticate to get a fresh token with the correct scopes.
