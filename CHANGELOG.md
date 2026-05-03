# Changelog

## [1.2.1] - 2026-05-03

### Fixed (`voicenter-bot-builder` 1.0.0 → 1.0.1) — Skill 3 alignment with `ImportBotFromJSON` stored procedure

The wire-format JSON Skill 3 emits is now consumable by the platform's `ImportBotFromJSON` MySQL procedure without manual editing. Five hard-blocking and one fragile gap closed; full design at `docs/superpowers/specs/2026-05-03-skill3-import-proc-alignment-design.md`.

- **G1 — `AiModelConfig.AccountId: 0`** added to top-level `AiModelConfig`. Routes the procedure to its "reuse existing default config" branch instead of falling through to an INSERT that fails on `AIModel` and `AIModelConfig` NOT NULL columns. (Skill 3 §4.2.3.)
- **G2 — `intentCategories[].PriorityId: 2`** (Medium) emitted explicitly. Was previously absent; column is `TINYINT NOT NULL` and the proc passes the extracted value, so omission caused a NULL INSERT failure. (Skill 3 §4.3.5.)
- **G3 — `botIntents[].IntentId` / `BotIntentId`** lowercase `d` (was capital `ID`). MySQL JSON paths are case-sensitive; the proc reads `$.IntentId` and the prior emission resolved NULL, breaking the BotIntent INSERT. Capital `ID` is preserved on `intentRelations[]` (matches the proc's read there) — deliberate asymmetry. (Skill 3 §4.3.3.)
- **G4 — `botIntents[].SortOrder`** added (1-based ordinal). Required NOT NULL column previously omitted. (Skill 3 §4.3.3.)
- **G5 — `intentRelations[]` deduplication** by `(OriginIntentID, NextIntentID)`. The DB unique key forbids duplicates; previously, a spec listing the same target twice (e.g., success path AND fallback both → `transfer_to_human`) emitted two rows and broke the second INSERT. Skill 3 now keeps the lowest-`Order` survivor and notes the collapse in the banner. (Skill 3 §4.3.4.)
- **G6 — `IntentScripts: []`** (was `{}`). The proc iterates with `JSON_LENGTH` + integer indexing; the object form would index `[0]` on a populated `{}` and break. Doc 1 §16 quirk #8 amended. (Skill 3 §4.3.1, Appendix A row 8.)
- **G7 — `IntentSources` per intent**, derived from spec section 1 `Channels Active` mapped through the DB `Sources` static table (1=VOICE, 2=CHAT, 3=WEB). (Skill 3 §4.3.1.)

### Changed

- **`model-catalog.md`** populated with seven real default `AIModelConfig` rows (`AccountId=0`) drawn from `database/Tables/StaticData/AIModelConfig.Data.sql`: Gemini Live (139/18), Gemini 2.5 (52/10), Gemini Voice Driven (136/16), Gemini 3.1 LLM Driven (142/21), GPT-4 Realtime (1/1), GPT-5 Realtime (91/13), GPT Realtime Mini (132/15). Replaces the prior `<TODO>` placeholders.
- **Voice catalog expanded** from the 2-row Puck/Orus list to the full provider inventories — 10 OpenAI voices (Alloy/Ash/Ballad/Coral/Echo/Sage/Shimmer/Verse/Cedar/Marin) and 8 Gemini voices (Puck/Charon/Kore/Fenrir/Aoede/Leda/Orus/Zephyr).
- **Skill 3 Appendix D — Static reference data** added as the single source of truth for every static integer ID Skill 3 emits (BotStatusId, BotVersionStatusId, BotIntentTypeID, IntentCategoryId/PriorityId, ResponseTypeId, SourceID, ParameterTypeId, IntentRelatedTypeID, IntentScriptType, default AIModelConfig rows). Mirrors `database/Tables/StaticData/*.Data.sql`; must be re-verified when those files change.

### Plugin version bumps (lockstep per CLAUDE.md)

- `marketplace.json` metadata: `1.2.0` → `1.2.1`
- `voicenter-mcp` plugin: `1.1.1` → `1.1.2` (no content change; bumped for cache refresh)
- `voicenter-api` plugin: `1.1.1` → `1.1.2` (no content change; bumped for cache refresh)
- `voicenter-bot-builder` plugin: `1.0.0` → `1.0.1` (Skill 3 + model-catalog content changes)

## [1.2.0] - 2026-05-02

### Added
- **`voicenter-bot-builder`** — new third plugin (v1.0.0) that ships a 3-skill bot-authoring pipeline:
  - `voicenter-bot-spec-designer` (Skill 1) — interview-driven structural design; produces `agent-spec.md`
  - `voicenter-bot-intent-detail-author` (Skill 2) — per-intent language content (Conversation Routines style)
  - `voicenter-bot-json-assembler` (Skill 3) — mechanical projection to Bot JSON wire format with §15.4 cross-reference pass and fail-loud sentinels
- `docs/plugins/voicenter-bot-builder.md` and per-skill long-form references under `docs/skills/voicenter-bot-*/`
- "Bot authoring (build-time)" entry in `docs/architecture.md` taxonomy + dedicated build-time pipeline section

### Fixed (Skill suite v1 patches surfaced by Conv 6 end-to-end test)
- **Patch 1 — Identifier field.** Added `**Identifier:**` to spec section 1 so Skill 3 produces useful filenames for non-ASCII bot names. Pre-fix: Hebrew bot names produced `bot-bot-<date>.json`. Post-fix: `bot-yuval-<date>.json` / `bot-refua-<date>.json`.
- **Patch 2 — RT-specific bold sub-labels.** spec-skeleton.md formalized section 4 RT-specific sub-labels (`**URL:**`, `**Method:**`, `**Headers:**`, `**Body:**`, `**API silence behavior:**`, `**Layer:**`); Skill 3 §3.1 strict-template parser enumeration extended; Skill 3 §3.3 deviation table added.
- **RT=4 production-shape rewrite.** spec-skeleton.md, Skill 1 §3.5.1, Skill 3 §3.1, and Skill 3 §4.4 RT=4 emission table updated to match real production Configuration shape — dual modes (parameter / static), three phone slots, `selectdial_option`, `response_success.instructions`, optional announcement / loading announcement / post-execution instructions.

## [1.1.1] - 2026-04-26

### Fixed
- Bump to force plugin cache refresh — 1.1.0 update was not re-syncing SKILL.md files

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
