---
description: Set up and authenticate the Voicenter MCP server in Claude Code
---

Help the developer **connect Claude Code to the live Voicenter API** via the MCP server at `mcp.voicenter.co`.

Once connected, Claude can make real API calls on your behalf — initiate calls, send SMS, pull reports, manage IVR flows, and more — without writing any code first.

## Step 1 — Get your API token

Log in to your Voicenter account and navigate to **Settings → API Access → Generate Token**.
Copy the token — you'll need it in the next step.

If you don't have API access, contact [support@voicenter.com](mailto:support@voicenter.com).

## Step 2 — Set the environment variable

Add your token to your shell profile so Claude Code picks it up on startup:

**macOS / Linux (bash or zsh)**
```bash
# Add to ~/.zshrc or ~/.bashrc
export VOICENTER_API_TOKEN="your-token-here"
```
Then reload: `source ~/.zshrc`

**Windows (PowerShell)**
```powershell
[System.Environment]::SetEnvironmentVariable("VOICENTER_API_TOKEN","your-token-here","User")
```

**Verify it's set:**
```bash
echo $VOICENTER_API_TOKEN
```

## Step 3 — Verify the connection

In Claude Code, ask:
```
Can you list my Voicenter extensions?
```

Claude will use the `voicenter` MCP server tool to fetch your extensions live. If it works, you're connected.

## Step 4 — What you can do now

With the MCP server connected, Claude Code can:

| Action | Example prompt |
|---|---|
| Make a call | "Call extension 1001 from DID +972031234567" |
| Send SMS | "Send an SMS to +972501234567 saying 'Your order is ready'" |
| Get call history | "Show me all calls from today" |
| Check queue stats | "What's the current wait time in the Sales queue?" |
| Pull a report | "How many calls did John Doe answer this week?" |
| List extensions | "Which agents are currently available?" |
| Create IVR | "Build me an IVR that routes sales calls to queue q-sales" |

## Troubleshooting

**"Unauthorized" error** — Your token may have expired or be incorrect. Regenerate it in the Voicenter portal and update the env variable.

**"Connection refused"** — Make sure `mcp.voicenter.co` is reachable from your network. Corporate firewalls may block outbound SSE connections on port 443.

**Claude doesn't use the MCP tools** — Restart Claude Code after setting the env variable. The MCP server is only registered at startup.

## Token security

- Never commit `VOICENTER_API_TOKEN` to source control.
- Use a CI/CD secret (e.g. GitHub Actions secret) in automated environments.
- Tokens are scoped to your account — use read-only tokens when write access isn't needed.
