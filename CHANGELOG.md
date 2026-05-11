# Changelog

## [1.4.2] - 2026-05-11

### Changed

Cache-refresh bump across all three plugins to force `/reload-plugins` to resync SKILL.md content on existing installs. No behavior or surface-area change since 1.4.1.

### Plugin version bumps (lockstep per CLAUDE.md)

- `marketplace.json` metadata: `1.4.1` → `1.4.2`
- `voicenter-mcp` plugin: `1.1.5` → `1.1.6` (no content change; bumped for cache refresh)
- `voicenter-api` plugin: `1.1.5` → `1.1.6` (no content change; bumped for cache refresh)
- `voicenter-bot-builder` plugin: `1.2.1` → `1.2.2` (no content change; bumped for cache refresh)

## [1.4.1] - 2026-05-11

### Fixed (`voicenter-bot-builder` 1.2.0 → 1.2.1) — Skill 3 `IntentResponces.IsActive` structural correction

Skill 3 (`voicenter-bot-json-assembler`) now emits the per-intent active flag **inside** `IntentResponces` (as the middle key between `ResponseTypeId` and `Configuration`) and no longer emits `IsActive` or `IsDeleted` at the intent root. The corrected shape matches the platform-validated bot JSON (`docs/json-bag/good.json` intent -10). The `ImportBotFromJSON` procedure reads `IntentResponces.IsActive` for the per-intent active flag; the prior intent-root location was silently ignored, so the bot's runtime active state was unchanged by the fix — this is a wire-format correctness fix, not a behavior change.

- **SKILL.md §4.3.1** — removed the two intent-root rows (`IsActive: 1`, `IsDeleted: 0`); added an inline note pointing readers to §4.4 for the corrected location.
- **SKILL.md §4.4** — added `IsActive: 1` row to all four RT-specific tables (RT=1, RT=2, RT=3, RT=4) immediately below the `ResponseTypeId` row. Added an invariant-shape header note documenting that every `IntentResponces` has the same three-key outer shape regardless of RT.
- **SKILL.md Appendix A** — added quirk #15 (`IntentResponces.IsActive: 1` emission rule + anti-quirk note explicitly forbidding intent-root `IsActive`/`IsDeleted`). Preamble updated from "14 quirks" to "15 quirks". Skill 3's §4.5 quirk-preservation verification pass now covers the new quirk.
- **Companion docs (`docs/skills/voicenter-bot-json-assembler/README.md`)** — per-RT keys preamble and the quirk-preservation walk paragraph mirror the SKILL.md changes. (Drive-by fix: `IntentScripts: {}` corrected to `IntentScripts: []` to match the v1.2.1 SKILL.md Appendix A quirk #8 amendment.)
- **Schema audit (`references/docs/voicenter-bot-json-schema-audit-v1.md`)** — §9.0 renamed "16-Field Skeleton" → "14-Field Skeleton" (intent-root `IsActive`/`IsDeleted` rows removed); §9.2 `IntentResponces` tree updated from two fields to three with `IsActive` between `ResponseTypeId` and `Configuration`. Inline "Schema correction (2026-05-11)" addenda explain the rationale.

### Test artifacts

`references/test-artifacts/test-emitted-json-{yuval,refua}.json` predate this fix and may show the pre-v1.4.1 shape. Regeneration is deferred — these files are reference samples, not consumed by any runtime. The next genuine Skill 3 invocation against either spec will produce the corrected shape.

### Plugin version bumps (lockstep per CLAUDE.md)

- `marketplace.json` metadata: `1.4.0` → `1.4.1`
- `voicenter-mcp` plugin: `1.1.4` → `1.1.5` (no content change; bumped for cache refresh)
- `voicenter-api` plugin: `1.1.4` → `1.1.5` (no content change; bumped for cache refresh)
- `voicenter-bot-builder` plugin: `1.2.0` → `1.2.1` (Skill 3 wire-format correction)

## [1.4.0] - 2026-05-03

### Added (`voicenter-bot-builder` 1.1.0 → 1.2.0) — Skill 1 intent flow diagram + refinement loop

Skill 1 now generates a **Mermaid `flowchart TD`** of the bot's intent graph as the final structural artifact, embedded in the spec under new section 6.6, and offers a **refinement loop** before final emission. Same diagram regenerates after every patch, so the user can see the structural impact visually before finalizing.

- **Mermaid diagram (spec section 6.6)** — Skill 1 §3.6.1. One node per intent in section 4 (label: `<identifier><br/>RT=<n> · slots: <count>`, plus ` ⚑` if hard-intent). Node shapes encode response type: stadium for RT=1 transfer, rounded rectangle for RT=2 API, default rectangle for RT=3 conversational, subroutine shape for RT=4 outbound dial. One labeled edge per transition (`success` / `fallback` / `escalation`). If section 4.7 (advanced overrides) declares `dtmf_list:` for a transition, digits append to the edge label. Skill 3 ignores section 6.6 — it's for human comprehension only, not the import contract.
- **Refinement loop at greenfield close-out** — Skill 1 §3.6 step 5. After section 6 + 6.6 are generated and soft-cap warnings surface, Skill 1 renders the diagram and prompts via `AskUserQuestion` (header: "Diagram review", 4 options: "Looks good — finalize *(Recommended)*" / "Adjust an intent" / "Adjust a transition" / "Adjust persona / opening behavior"). Any "Adjust" pick routes back to the relevant phase, applies the change, regenerates section 6 (including 6.6), re-runs the self-validation checklist, and re-prompts. Capped at 5 iterations to prevent endless cycles — beyond 5, Skill 1 logs the iteration count to section 7.3 and proceeds.
- **Patch-mode regeneration** — Skill 1 §4.6 + §4.7. Section 6.6 regenerates after every applied patch, alongside the cascade summary, and the same refinement loop is offered before final emission.

### Changed

- **Skill 1 output contract** updated to list section 6.6 as a greenfield/patch artifact (and to clarify it's not consumed by Skill 3 or the import proc).
- **Docs lockstep:** `docs/skills/voicenter-bot-spec-designer/README.md` mirrors the diagram + refinement-loop additions, with a new "Intent flow diagram + refinement loop" section under Output contract.

### Plugin version bumps (lockstep per CLAUDE.md)

- `marketplace.json` metadata: `1.3.0` → `1.4.0`
- `voicenter-mcp` plugin: `1.1.3` → `1.1.4` (no content change; bumped for cache refresh)
- `voicenter-api` plugin: `1.1.3` → `1.1.4` (no content change; bumped for cache refresh)
- `voicenter-bot-builder` plugin: `1.1.0` → `1.2.0` (Skill 1 diagram + refinement loop)

## [1.3.0] - 2026-05-03

### Added (`voicenter-bot-builder` 1.0.1 → 1.1.0) — Skill 1 interactive UX + optional advanced features

Skill 1 (`voicenter-bot-spec-designer`) now uses live MCP lookup for Voicenter platform resources and `AskUserQuestion` (interactive menu inputs) for every closed-set choice in the interview, instead of free-text capture. Skill 1 also gains an opt-in path for the two runtime-supported features (`ConditionGroupList`, `DTMFList`) that were previously inaccessible from the build pipeline.

- **Live resource lookup via `voicenter-mcp.list_resources` (recommended default).** Customer Account ID (Phase 1) and RT=1 Layer ID (Phase 4) are now fetched live with `entityFilter: ["Accounts"]` / `["Layers"]` and presented as id+name tables, then prompted via `AskUserQuestion`. New SKILL.md §2.4.A documents a 3-tier fallback that is **never silently skipped**: (1) plugin not installed → offer install + auth via `AskUserQuestion`; (2) plugin installed but unauthenticated → offer authenticate via `AskUserQuestion`; (3) user declines or retry fails → fall back to text-only mode and `<UNKNOWN: …>` markers, logged once to spec section 7.3 with the reason; the user is not re-prompted in the same session.
- **`AskUserQuestion` for every closed-set choice** (SKILL.md §2.4.B). New iron rule: if the user can answer with one of a fixed set of strings, route through interactive inputs. Covers runtime/mode detection, channel scope, voice/model catalog picks, caller-silence yes/no, identifier ASCII confirmation, every Phase 2 "Accept draft / Edit" prompt, Deep Research pause/skip, Response Type (RT=1/2/3/4), per-slot `ParameterTypeId` + `IsRequired`, RT=2 Method (POST/GET) + fallback intent reference (from existing intent set), RT=4 dial source + `record` + rarity-warning confirmation, account / layer selection from live MCP lists, patch-mode cascade confirm, every self-validation iron-rule re-prompt, and the new MCP install/auth/skip prompts. Free-text capture is reserved for genuinely open-ended fields (names, descriptions, free-form text content, integer/numeric values).
- **Optional advanced features (default: skip — *not required*)** — new SKILL.md §3.5.5 adds an opt-in capture path for `ConditionGroupList` (conditional branching on `BotIntent` / `IntentRelated`) and `DTMFList` (DTMF keypad routing). After Phase 4 captures the structural intent set, Skill 1 prompts once via `AskUserQuestion` with **"Skip — accept defaults *(Recommended)*"** as the default. Skip path writes nothing; Skill 3 falls back to existing safe defaults (`ConditionGroupList: []`, `DTMFList` omitted), and the `ImportBotFromJSON` proc skips both arrays cleanly via NULL-guards in `CreateConditionGroups` and the `IntentRelatedDTMF` insert. Opt-in path captures into a new freeform spec **section 4.7 Advanced overrides**; Skill 3 (§4.3.3 / §4.3.4) lifts `condition_groups:` and `dtmf_list:` blocks verbatim into the corresponding `botIntents[]` / `intentRelations[]` entries. Skill 1 does not validate §4.7 contents — pass-through to Skill 3.
- **RT=3 schema cross-reference clarification** — Skill 1 §3.4.3 RT prompt now includes a parenthetical noting the DB seed name for `ResponseTypeId=3` is "Message" / "Update Bot Configuration" but the operational use is conversational data-collection. Cosmetic only; no behavior change.

### Changed

- **Skill 1 anti-list** updated: live MCP lookup is now in scope (was previously listed as out-of-scope with the model catalog); `ConditionGroupList` / `DTMFList` are documented as opt-in only via §4.7.
- **Skill 3** §4.3.3 + §4.3.4 (`botIntents[]` and `intentRelations[]`): `ConditionGroupList` and `DTMFList` rows now read from spec §4.7 if present, fall back to the existing default-skip behavior if absent.
- **Docs lockstep:** `docs/skills/voicenter-bot-spec-designer/README.md` and `docs/skills/voicenter-bot-json-assembler/README.md` updated with the new tool conventions, the §3.5.5 opt-in summary, and the §4.7 pass-through behavior.

### Plugin version bumps (lockstep per CLAUDE.md)

- `marketplace.json` metadata: `1.2.1` → `1.3.0`
- `voicenter-mcp` plugin: `1.1.2` → `1.1.3` (no content change; bumped for cache refresh)
- `voicenter-api` plugin: `1.1.2` → `1.1.3` (no content change; bumped for cache refresh)
- `voicenter-bot-builder` plugin: `1.0.1` → `1.1.0` (Skill 1 interactive UX + optional §3.5.5; Skill 3 §4.7 pass-through)

## [1.2.1] - 2026-05-03

### Fixed (`voicenter-bot-builder` 1.0.0 → 1.0.1) — Skill 3 alignment with `ImportBotFromJSON` stored procedure

The wire-format JSON Skill 3 emits is now consumable by the platform's `ImportBotFromJSON` MySQL procedure without manual editing. Five hard-blocking and one fragile gap closed.

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
