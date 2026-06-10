# Changelog

## [Unreleased]

### Skills

- **Skill 1 (Spec Designer):** the Phase 1 **Identifier** is no longer prompted. It is now silently auto-derived from the Bot Name — ASCII names are snake_cased, non-ASCII (e.g. Hebrew) names are transliterated to Latin then snake_cased (`יובל` → `yuval`). Removes one `AskUserQuestion` from the interview. The separate Phase 3 intent-name reject-and-suggest prompt is unaffected.

## [1.9.0] — 2026-06-02

### Skills

- **All 18 skills:** added a **language-mirroring** directive — each skill now replies in the user's language (Hebrew→Hebrew, English→English) and follows mid-conversation switches. Affects conversational prose, questions, and `AskUserQuestion` labels only; emitted artifacts (identifiers, JSON keys, BCP-47 codes, API field names) are unchanged. The generated bot's runtime language behavior and the code-switch guardrail are **not** affected.
- **4 interactive skills** (voicenter-mcp `setup`, Skill 1 Spec Designer, Skill 2 Intent Detail Author, Skill 3 JSON Assembler): added a **bilingual opening** (Hebrew + English greeting on first contact). Skills 2, 3 and `setup` also gained a **one-question-per-turn** interview directive (single `AskUserQuestion` per message, never batch). Skill 1's existing §2.4 iron rule was **upgraded** with the same one-question-per-turn teeth rather than duplicated.

### Versioning

- voicenter-mcp 1.1.6 → 1.1.7, voicenter-api 1.1.6 → 1.1.7, voicenter-bot-builder 1.8.0 → 1.9.0, marketplace metadata 1.8.0 → 1.9.0.

## [1.8.0] — 2026-06-01

### Skills

- **Skill 1 (Spec Designer):** new section-4 `**Bot-intent role:**` field (`entry`/`global`/`chained`, default `chained`). Approach-B role classification in close-out (propose from §2.4 opening targets + always-available intents, confirm in one batch, write explicit field). Section 6.2/6.4 now include auto global fan-out edges. **Caller-silence (section 3) gains a structural `silence failover intent`** (Skill 3 emits it as `silence_behaviour.intent`), defaulting to the transfer-to-human global; `silence_ending_sentence` then defaults to a transfer-to-representative line. Check 7 noted as auto-satisfied by fan-out when a global exists.
- **Skill 3 (JSON Assembler):** parses the role field (§3.1). `botIntents[]` is now a **selective** registry — only `entry` (`BotIntentTypeID 1`) and `global` (`2`) intents; chained intents omitted (§4.3.3). 0-based `SortOrder` over the subset. Global **fan-out** (§4.3.4): an edge from every non-global intent to each global, deduped. §5 6.2 regeneration is fan-out-aware. Four new blocking cross-reference checks 11–14 (global-is-type-2, fan-out completeness, no-chained-in-botIntents, start-point-exists); the pass is now fourteen checks.
- **Silence-failover structural `intent` (design D8 revised).** A production export (operator/משרד-התחבורה bot) showed the bot-level `silence_behaviour` carries a structural `intent` failover field (mirroring `api_silence_behaviour.intent`) — the initial "authored sentence, no structural field" decision was wrong. Skill 3 §4.2.5 now emits `silence_behaviour.intent` (resolved `IntentId`, first key, default transfer-to-human global, `-999` sentinel if unknown), Doc 1 §6.B.3 documents it, and the invariant guard asserts both `silence_behaviour.intent` and the RT=2 `api_silence_behaviour.intent`/`apiSilenceRelations` pairing.

### Documentation

- Doc 1 (`voicenter-bot-json-schema-audit-v1.md`): §8.2 + G-10 rewritten — `BotIntentTypeID` is a discriminator (1=entry, 2=global); `botIntents[]` is a selective subset.
- Doc 2 (`voicenter-bot-skills-architecture-v1.md`): botIntents emission note corrected.
- `validation-report.md` §3.3 marked RESOLVED with the Brimag/Noa production evidence.
- `docs/skills/voicenter-bot-{spec-designer,json-assembler}/README.md` mirrors updated.

### Test artifacts

- Golden outputs `bot-ananit-2026-06-01.json` and `bot-noa-2026-06-01.json` (hand-applied v1.8.0; Noa Hebrew re-authored from a lossy source — see banners).
- `validate-botintent-roles-v18.py` invariant guard.

### Plugin version bumps

- `marketplace.json` `metadata.version`: `1.7.0` → `1.8.0`
- `voicenter-bot-builder` plugin: `1.7.0` → `1.8.0`
- `voicenter-mcp` and `voicenter-api` plugins: unchanged at `1.1.6`

## [1.7.0] — 2026-05-31

### Changed (voicenter-bot-builder)

- **Skill 1 — Phase 1 interview: AI model config is no longer prompted.** The interview previously asked the user to pick an AI model config via `AskUserQuestion`. It now silently defaults to the canonical model — **Gemini Live (Voice driven 3.1)** (`AIModelConfigID=139`, `AIModelTypeId=18`) — and writes it to spec section 1 without asking. A different model is used only if the user volunteers one (by catalog name or raw `AIModelConfigID` + `AIModelTypeId`). The `<UNKNOWN: AI Model Config>` deferral path is unchanged.
- **Skill 1 — Phase 1 interview: explicit agent-gender question added, with gender-filtered voice suggestions.** Phase 1 now asks whether the agent should sound **Female** or **Male** (header "Agent voice") before the voice-name prompt, and offers **only voices matching the chosen gender** for the active model family. The skill is instructed to **never infer gender from the bot name** (unisex names previously caused male-only suggestions like `Puck`/`Orus`). Written to spec section 1 as `**Agent Gender:**` — selection-aid metadata only; not emitted to the JSON.
  - `model-catalog.md`: added a `Gender` column to both the Gemini and OpenAI voice tables (Gemini Female → Kore/Aoede/Leda/Zephyr, Male → Puck/Charon/Fenrir/Orus; OpenAI labelled per voice, `alloy` = Neutral).
  - `spec-skeleton.md` §1: added the `Agent Gender` field after `Voice Name`.
- **Skill 2 — Check 11 (RT=2 `api_silence_behaviour` completeness) now enforces the fallback intent.** Check 11 previously claimed "six fields" but enumerated only the five `silence_*` fields, never the failover. It now requires all six components (3 language fields authored by Skill 2 + 3 structural fields owned by Skill 1: `silence_duration`, `silence_loops`, and the **fallback intent**) and **halts/routes to Skill 1 patch mode if the fallback intent is missing or unresolved** in section 4.
- **Skill 3 — RT=2 `api_silence_behaviour.intent` failover now explicitly specified and enforced.** The inline failover pointer (`Configuration.api_silence_behaviour.intent` = resolved fallback `IntentId`) was never spelled out — Skill 3 only said "the six fields embedded inline," so the failover could be dropped or emitted as a string. Fixes:
  - New §4.4.1 documents the exact six-key `api_silence_behaviour` object; `intent` (resolved fallback `IntentId`, equal to `apiSilenceRelations[].ApiSilenceIntentID`) is marked **mandatory — never omit, never emit as a string**; `-999` sentinel if the fallback intent is `<UNKNOWN>`.
  - Cross-reference **Check 5** is now blocking on the inline `intent` being a present, non-null integer equal to `ApiSilenceIntentID`.
  - Cross-reference **Check 6** deep-equality description now names all six `api_silence_behaviour` keys (including `intent`).

### Documentation (voicenter-bot-builder)

- All four SKILL.md changes above mirrored into the paired `docs/skills/voicenter-bot-*/README.md`.
- **voice-agent-llm v1.0.3 runtime behavior documented in all three bot-builder skills.** No schema, validation rule, or plugin-version change — Skill 2's Check 10 still requires authored `announcement` for RT=2.
  - Empty `announcement` (or legacy `apiResponseAnnouncement`) at runtime is now substituted by the service with the sentinel `[START THE CONVERSATION]` as an LLM instruction — bot opens from persona; the literal string is **not** spoken aloud. Documented as a production safety net, not an authoring relaxation.
  - Voice-active text fields (`validationPrompt`, `announcement`, `fail_output`, `function_output`, post-execution `intentInstructions`) are now sanitized server-side before TTS. The existing Compass rule 8 authoring rule (write plain conversational prose; no Markdown/URLs in these fields) still applies.
  - Spec Designer SKILL.md: three remaining references to `apiResponseAnnouncement` updated to `announcement` (was `apiResponseAnnouncement` pre-v1.5.0).
- **Internal voice-agent service traceability (informational only, no skill change):** Mastra library bumped 1.04 → 1.36.0; `mastra-voicenter` bumped 2.0.3 → 2.1.0.

### Plugin version bumps

- `marketplace.json` `metadata.version`: `1.6.0` → `1.7.0`
- `voicenter-bot-builder` plugin: `1.6.0` → `1.7.0`
- `voicenter-mcp` and `voicenter-api` plugins: unchanged at `1.1.6`

## [1.6.0] — 2026-05-24

**Note:** this release was developed under the working version name "v1.5.0" (visible in inline references throughout the changelog entry below and in the SKILL.md / docs README v1.5.0 correction notes). The release was renumbered to 1.6.0 to avoid collision with the prior 1.5.0 Compass doctrine release (May 14). Skill 3 SKILL.md and docs may continue to use "v1.5.0" as the working label for these changes; the platform-facing release version is 1.6.0.

### Changed (voicenter-bot-builder)

- **BREAKING (wire format):** Skill 3 emission restructured to match the production Voicenter export shape for Gemini 3.1 Voice driven bots. Bots emitted by pre-1.5.0 Skill 3 will import successfully but won't round-trip cleanly through the platform's export UI. Re-emit any in-progress bots after upgrading.
- **Skill 1 — Phase 1 interview:** added three new bot-identity questions: `Created by`, `Max call duration`, `Record agent calls`.
- **Skill 1 — spec-skeleton.md §4:** added optional `Max turns` / `Max turns sentence` per-intent fields.
- **Skill 2 — per-intent authoring:** field renamed and shape changes for `apiResponseAnnouncement` (→ `announcement`), `function_output` (→ object `{ "default": ... }`), `response_success` (→ object `{ "instructions": ... }`).
- **Skill 3 — emission shape (largest change set):**
  - Top-level wrapper field order: `intentList` moves to position #4.
  - `AiModelConfig` (top-level catalog reference) restructured: new fields (`ApiKey`, `AIModel`, `IsActive`, `AccountId`, `ModifiedBy`, `CreatedDate`, `ModifiedDate`, nested `AIModelConfig` carrying only the model string). Removed: `Description`, `BaseUrl`, `Type`, `AIModelTypeId`, full `created` payload (lives in the version-level only).
  - `ActiveVersionInfo.AIModelConfig` (version-level runtime config): added `max_duration`, `recordAgentCalls`. Removed: `tools: []`, `instructions: ""`.
  - `created` payload reduced to lean shape: `realtimeInputConfig.automaticActivityDetection.disabled: "true"` + voice config only (version-level); model string only (top-level catalog reference). Dropped: `temperature`, `topP`, `topK`, `responseModalities`, `proactivity`, `thinkingConfig`, `systemInstruction`, `tools`.
  - `intents[]` entry: 17-field skeleton (intent-root `IsActive` and `AccountId` restored from production observation, removed incorrectly in the v1.4.1 schema correction). `IsSilenceIntent` now integer 0/1. `IntentSources` shape includes `SourceName` and `IntentSourceID` (was `[{ SourceID: 1 }]`). Optional `IntentConfig.max_turns` / `max_turns_sentence` per-intent.
  - `IntentParameters[]` entry: audit fields added (`Schema: null`, `CreatedBy`, `ModifiedBy: " "`, `CreatedDate`, `ModifiedDate`). Type fields now integers (`IsRequired: 0/1`). `OptionList: null` for non-ENUM (was `[]`). `DefaultValue: ""` for unset strings (was `null`). `ParameterType` fully nested with frozen type-catalog metadata.
  - `botIntents[]`: `BotId`/`IntentId` lowercase-d casing. `DTMFList: []` always. `BotVersionId` added. `SortOrder` 0-based. `ConditionGroupList` populated by default.
  - `intentRelations[]`: `Order` 0-based. `IntentRelatedID` is a unique row PK (placeholder range `-2000+`), no longer a `NextIntentID` mirror. `ConditionGroupList` populated by default.
  - `intentCategories[]`: no `BotID`. Added `IsActive`, `AccountId`, `Description`. `PriorityId: 1` (was `2`).
  - `apiSilenceRelations[].Configuration`: full mirror of parent `IntentResponces.Configuration` (was just the six `silence_*` fields).
  - RT=2 `Configuration`: `announcement` (was `apiResponseAnnouncement`). `function_output` → object `{ "default": ... }`. `response_success` → object `{ "instructions": ... }`. `IntentLoadingAnnouncement` (capital I) dropped.
  - RT=3 `Configuration`: `response_success` → object.
- **Skill 3 — §6.2 cross-reference checks:** Check 6 now validates full Configuration deep equality between RT=2 intents and their `apiSilenceRelations[]` Configuration (was just `silence_*` six-field). Check 10 (Compass rule 12 model-config doctrine) inverted: instead of positively asserting present fields, now catches regressions to dropped fields under `generationConfig`.
- **Skill 3 — Appendix A:** Quirk row 2 (the `intentLoadingAnnouncement` / `IntentLoadingAnnouncement` casing-bug pair) marked REMOVED in v1.5.0. Quirks 16–19 added (nested `AIModelConfig`, `recordAgentCalls` as string, `realtimeInputConfig.automaticActivityDetection.disabled` as string, `IntentParameters[].ModifiedBy` single-space literal).
- **Skill 3 — new ID placeholder ranges:** `IntentRelatedID` (`-2000+`), `IntentConditionGroupID` (`-3000+`), `IntentSourceID` (`-4000+`).

### Added (voicenter-bot-builder)

- `references/test-artifacts/test-prod-bot-transport-planner.json`: production export of the user-supplied "סוכן תכנון מסלול - לקוח" v0.0.38 Gemini 3.1 Voice driven bot, serving as the third reference fixture and the ground-truth round-trip target for v1.5.0+ emission.

### Documentation

- `references/docs/voicenter-bot-json-schema-audit-v1.md`: ~12 subsections rewritten (§4, §5, §6.A, §6.B, §6.B.2, §8.2, §8.3, §8.4, §8.6, §9.0, §9.1, §10, §11.2, §11.3, §11.5, §16). The doc remains the canonical wire-format contract; this update aligns it to the production Gemini 3.1 Voice driven export.
- `docs/skills/voicenter-bot-*/README.md`: all three plugin docs READMEs mirror the corresponding SKILL.md changes.

### Internal

- `references/test-artifacts/test-emitted-json-yuval.json` and `test-emitted-json-refua.json` regenerated to v1.5.0 shape. Placeholder IDs preserved.

### Plugin version bumps

- `marketplace.json` `metadata.version`: `1.5.0` → `1.6.0` (renumbered to avoid collision with the May 14 1.5.0 Compass doctrine release)
- `voicenter-bot-builder` plugin: `1.3.0` → `1.6.0` (production wire-format alignment)
- `voicenter-mcp` and `voicenter-api` plugins: unchanged at `1.1.6`

## [1.5.0] - 2026-05-14

### Added
- **Compass doctrine integration in `voicenter-bot-builder`.** New shared reference `plugins/voicenter-bot-builder/references/voice-prompt-doctrine.md` distilled from the Gemini Live 3.1 voice agent engineering guideline. The reference catalogs 13 enforceable rules and is loaded by all three skills.
  - **Skill 1 (Agent Spec Designer)** gains 5 new self-validation checks (11–15) covering rules 3 (English operational), 4 (intent description in English), 5 (recency-slot language-lock guardrail), 6 (contradictory pacing/length), 7 (generic-policy boilerplate), plus a rule-11 mirror on rewritten fields. New Appendix D documents the mapping.
  - **Skill 2 (Intent Detail Author)** gains 4 new per-intent iron rules covering rules 8 (TTS-safe formatting; blocking on markdown/URLs), 9 (date math in prompt), 10 (few-shot example cap), 11 (Hebrew-utterance isolation; blocking). The `conversation-routines-style-guide.md` gets a TTS-safety addendum.
  - **Skill 3 (JSON Assembler)** gains 3 new cross-reference checks (8, 9, 10) plus a DOCTRINE SENTINELS banner section (rule 13). Check 8 (token budget) is advisory at 1,500–2,499 tok and blocking at ≥ 2,500. Check 10 (model-config doctrine) is blocking on any mismatch. All three are gated on `AiModelConfig.created.model = "models/gemini-3.1-flash-live-preview"`.
  - Token-counting uses a char-based estimate (Latin 1/4 tok, Hebrew/Arabic/CJK 1/1.5 tok) — ±15% accuracy, sufficient for the doctrine thresholds.

### Notes
- Rules 1, 2, 12 apply only when `AIModelConfigID=139` (Gemini Live 3.1). Rules 3, 4, 5, 6, 8, 10, 11 apply to any active voice channel. Rules 7, 9, 13 apply universally.
- Non-goal: this release does not retroactively fix existing bot artifacts (e.g., `bot-noa-2026-05-12.json`). To apply the doctrine to an existing bot, re-run Skill 1 → 2 → 3 on its spec.
- Non-goal: platform-side concerns the Compass flags as out-of-prompt (PII redaction, prompt-injection classifier, rate limiting, recording consent) are not enforced by the bot-builder. The doctrine reference §3 notes which concerns belong to which plane.

### Plugin version bumps
- `marketplace.json` metadata: `1.4.2` → `1.5.0`
- `voicenter-bot-builder` plugin: `1.2.2` → `1.3.0` (Compass doctrine integration across all three skills)
- `voicenter-mcp` plugin: `1.1.6` (unchanged)
- `voicenter-api` plugin: `1.1.6` (unchanged)

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
