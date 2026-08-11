# Milestone 4 — Marketplace / Directory Readiness

**Objective:** close every submission blocker for the Anthropic plugin
directory. Parallelizable with MS1–3 (touches metadata and docs, not skill
logic).

**Why:** submission requires a public repo, a validating manifest, and
compliance with the Software Directory Policy (README with example prompts,
support contact, data-handling clarity, no hidden instructions). Full policy
detail and citations: `../reference/marketplace-requirements.md`.

**Files touched (all in `plugins/voicenter-bot-builder/` unless noted):**
`.claude-plugin/plugin.json`, `LICENSE`, `README.md`, `CHANGELOG.md`,
repo-root `.claude-plugin/marketplace.json`, CI workflow.

## Steps

### 4.1 Complete `plugin.json`

Current manifest has `name`, `description`, `version`, `keywords` only. Add:

```json
{
  "name": "voicenter-bot-builder",
  "displayName": "Voicenter Bot Builder",
  "version": "1.19.0",
  "description": "<one crisp line — reuse the README tagline>",
  "author": { "name": "Voicenter", "email": "<support email>", "url": "https://www.voicenter.com" },
  "homepage": "<docs or product page URL>",
  "repository": "https://github.com/VoicenterTeam/claude-marketplace",
  "license": "<SPDX id — see 4.2>",
  "keywords": ["voicenter", "voicebot", "voice-ai", "ivr", "conversational-ai", "intent-design", "json-generator"]
}
```

Rules: `name` is an **immutable slug** once published — never change it; use
`displayName` for label changes. Explicit semver `version` means updates
propagate **only on version bump** — this is what we want for a published
plugin (see MS6 release step).

### 4.2 LICENSE decision + file

Decision needed from Voicenter legal/lead: permissive OSI license
(MIT or Apache-2.0) for the plugin wrapper. Flag separately: the bundled
reference material (`verification-procedure.md`, doctrine files, model
catalog) describes Voicenter's proprietary wire format — confirm distribution
rights and mark proprietary content headers if the license differs from the
wrapper. **Do not submit until this is signed off.**

### 4.3 README.md (plugin-level)

Required content (Directory Policy §3):
- What the plugin does, intended purpose, how the three-skill pipeline works
- **≥ 3 working example prompts** exercising core functionality (§3E), e.g.
  greenfield design, patch mode, full detail→assemble run
- Troubleshooting section (§3C)
- **Support contact** (§3B)
- **Data-handling statement** (§1D/§3A): explicitly state the plugin makes no
  network calls, transmits nothing, logs nothing; all interview data stays in
  the local session; the only artifacts written are the spec markdown and the
  generated bot JSON. (If any Voicenter endpoint is ever contacted in a future
  version, a privacy-policy link becomes mandatory — record this as a tripwire.)
- **Known limitations:** RTL/bidi rendering in terminal surfaces (see MS5 §5.4);
  subagent verification is a Claude Code / Cowork enhancement, claude.ai runs
  the identical checks inline
- No implied Anthropic endorsement anywhere; Voicenter branding confirmed
  authorized

### 4.4 CHANGELOG.md

Backfill from the version history you have (1.12.0 → 1.17.0 highlights are
recoverable from in-file version annotations), then the full v1.19.0 entry.
Keep-a-Changelog format. Git tags must match `plugin.json` versions from
v1.19.0 onward.

### 4.5 Reviewer test kit

Directory Policy §3D expects reviewers to be able to exercise functionality.
The plugin is self-contained (no login), so ship in-repo:
`examples/sample-spec-detailed.md` (a complete, fully-detailed fictional-business
spec) + `examples/expected-output.json` (its exact assembly output). This doubles
as the MS6 golden file.

### 4.6 Compliance sweep

- Skill `name` fields: ≤ 64 chars, lowercase/numbers/hyphens, **no reserved
  words "claude"/"anthropic"** (all three current names comply — verify after
  any rename).
- Descriptions: human-readable only, no hidden/encoded instructions, promise
  nothing undelivered.
- Marketplace entry (repo root `.claude-plugin/marketplace.json`): `name`,
  `source`, `description` present; add `category` + `tags` (free-form; use
  something like category "productivity"/"integration", tags mirroring
  keywords).

### 4.7 CI validation

Add a GitHub Actions job: `claude plugin validate ./plugins/voicenter-bot-builder --strict`
on every PR + push to main. Strict mode: warnings (misspelled/unrecognized
fields) fail the build.

## Done criteria

- [ ] `claude plugin validate --strict` exits clean, wired into CI
- [ ] plugin.json complete per 4.1; marketplace.json entry has category/tags
- [ ] LICENSE present, legal sign-off recorded (incl. bundled reference docs)
- [ ] README with ≥3 example prompts, support contact, data-handling statement,
      known-limitations section
- [ ] CHANGELOG.md present and consistent with plugin.json version + git tag plan
- [ ] examples/ test kit in repo and assembly-verified
- [ ] Reserved-word / hidden-instruction sweep documented as done
