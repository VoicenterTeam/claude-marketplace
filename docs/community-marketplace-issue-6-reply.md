# Reply to claude-plugins-community issue #6

> *"`voicenter` entry resolves to the repo root, not a plugin"* — @bryan-anthropic, 2026-07-04.
>
> Paste the block below as the issue reply. Kept here so the repo records what was
> requested and what we answered.

---

Hi Bryan — thanks for the clear diagnosis, and you're right about the cause.

`voicenter` is the name of the **marketplace**, not a plugin. It's the `name` field in our root
`.claude-plugin/marketplace.json`, and it appears as the `@marketplace` suffix in an install
command (`/plugin install voicenter-mcp@voicenter`). There is no plugin manifest named
`voicenter` and there deliberately never will be — a plugin sharing the marketplace's name is
exactly the ambiguity that produced this entry, so we've added a CI check that fails the build
if anyone ever introduces one.

**Please list one plugin: `voicenter-mcp`.**

| Field | Value |
|---|---|
| Plugin name | `voicenter-mcp` |
| Path in repo | `plugins/voicenter-mcp` |
| Manifest | `plugins/voicenter-mcp/.claude-plugin/plugin.json` |
| Repository | https://github.com/VoicenterTeam/claude-marketplace |

That's the front door: it connects Claude directly to our OAuth-protected MCP server and gives
live access to the whole Voicenter telephony API surface, so it's the single entry that's useful
on its own with no configuration beyond the browser OAuth flow.

The other two plugins you found are real and correctly manifested — `voicenter-api` (integration
skills) and `voicenter-bot-builder` (voice-bot authoring). We're holding them back from the
community listing for now; `voicenter-mcp`'s description points to them, and both remain
installable from our own marketplace. We may come back and ask you to add them later.

So the `voicenter` entry can be replaced with a single `voicenter-mcp` entry pointing at
`plugins/voicenter-mcp`.

One note in case it helps your indexer with other monorepos: the bare token `voicenter` appears in
our repo in three places that are all *not* plugin names — the marketplace `name`, the
`mcpServers` key inside `voicenter-mcp/plugin.json`, and the `@voicenter` install suffix. Reading
`plugins/*/.claude-plugin/plugin.json` (as you did) is the reliable source; we've also added a
plugin table to the top of our README that spells out the name-to-directory mapping explicitly.

Thanks for catching this.

---

## What we changed on our side

Nothing needed fixing to resolve the issue — the repo was already correct — but we hardened
against recurrence:

1. **README** now opens with a "Plugins in this repository" table (real name, directory, install
   command) and an explicit note that `voicenter` is the marketplace, not a plugin.
2. **CI** (`.github/workflows/plugin-validate.yml`) asserts, for every marketplace entry:
   entry name == `plugin.json` name == directory basename, the `source` directory exists, versions
   agree, and **no plugin is named the same as the marketplace**. Verified that the last check
   fires on a simulated `voicenter-mcp` → `voicenter` rename.
3. **`voicenter-mcp`'s manifest was enriched** — `displayName`, `author`, `homepage`,
   `repository`, `license`, `keywords`, and a description that names the companion plugins. It had
   only `name`/`description`/`version`/`mcpServers`, which is what a directory listing would have
   rendered.

### Considered and rejected: renaming `voicenter-mcp` to `voicenter`

The obvious-looking fix, but wrong:

- It breaks existing installs — the plugin registry keys on `voicenter-mcp@voicenter`.
- It produces `voicenter@voicenter`, i.e. the plugin name and marketplace name become identical:
  the very collision that made this entry unresolvable.
- It doesn't answer the actual request, which is per-plugin entries under real names.
- ~111 references across ~21 files.

### Lesson for our own directory submission (MS6 §6.4)

Never submit a bare monorepo root and expect the indexer to infer the plugin. Name the plugin(s)
and their subdirectories explicitly in the submission.
