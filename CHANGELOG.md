# Changelog

## [1.1.0] - 2026-04-26

### Fixed
- Skills now register correctly on `/reload-plugins` (was reporting 0 skills loaded)
  - Added explicit `name:` field to all 15 SKILL.md frontmatter entries
  - Removed redundant `"skills": "./skills/"` from plugin.json (default discovery handles it)
- `voicenter-mcp` MCP server config now includes required `"type": "http"` field
- Optimized all 14 SKILL.md files for clearer Claude Code invocation

### Changed
- Conformed `plugin.json` files to the official Claude Code plugin manifest schema
- Removed unsupported `icon` field from plugin and marketplace configs
- Removed nested V2 marketplace duplicate

### Added
- `LICENSE` file (MIT)
- `CHANGELOG.md`
- `.gitignore` for local Claude settings

## [1.0.0] - 2025-04-04

### Added
- Initial marketplace release with 2 plugins
- **voicenter-mcp** — Live API access via OAuth MCP server at mcp01.voicenter.co
- **voicenter-api** — 14 API integration skills:
  - Push APIs: VoiceBot, Pop-Up Screen, CDR Notification, External Layer
  - Outgoing APIs: Click2Call, Call Log, Blacklist, Mute Recording, Extension List, Real-Time, Productive Dialer, Login/Logout, Lead Tracker, Active Calls
