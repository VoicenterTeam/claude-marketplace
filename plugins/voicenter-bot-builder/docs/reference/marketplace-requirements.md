# Marketplace / Directory Requirements

Verified as of **2026-08-08**. Governs MS4 and MS6.4.

## 1. Which surface we are targeting

Three Anthropic-run plugin surfaces exist; they are frequently conflated:

| Surface | What it is | Path in |
|---|---|---|
| `anthropics/claude-plugins-official` | Anthropic-curated directory, auto-added to Claude Code | **Curation-only** — "inclusion is at Anthropic's discretion." No open PR/application path. |
| `anthropics/claude-plugins-community` | Community-driven directory; read-only mirror of Anthropic's internal review pipeline | **In-app submission form** — this is our target. PRs against the repo are auto-closed. |
| Demo marketplace (`anthropics/claude-code/plugins`) | Examples only | N/A |

The directory is surfaced across **Cowork (claude.ai) and Claude Code**
(browsable at claude.com/plugins). A subset of accepted plugins later earns an
**"Anthropic Verified"** badge after additional human review — criteria not
public; treat as aspirational, not plannable.

Separate tracks, not ours: the Enterprise/Software Directory
(partnership-gated) and the MCP Connectors Directory (MCP-specific — relevant
to the separate `mcp01.voicenter.co/mcp` effort, not this plugin).

## 2. Submission mechanics

- **What you submit:** a GitHub link. The repo **must be public** —
  "closed-source plugins are not accepted."
- **Where:** in-app form — claude.ai admin settings (requires Team/Enterprise
  org, directory-management access; Owners have it) **or** Console at
  platform.claude.com (any account, Developer/Admin/Owner role). Canonical
  link: clau.de/plugin-directory-submission.
- **Pre-check:** run `claude plugin validate` (we run `--strict`) — the review
  pipeline runs the same check plus automated safety screening (pass/warn/fail).
- **Review time:** "varies with queue volume" — no SLA.
- **Updates after acceptance:** pushes to the GitHub repo auto-mirror to the
  public marketplace with re-screening. **No re-submission needed.** With an
  explicit `version` in plugin.json, installed users receive updates **only on
  version bump**.
- **Vendor-specific plugins are in-scope.** The directory carries
  company-branded plugins for the companies' own platforms (MongoDB, Miro,
  monday, Shippo, Mercado Pago). A Voicenter-branded plugin generating
  Voicenter config is squarely acceptable.

## 3. Manifest requirements

`plugin.json`: only `name` is required (kebab-case, immutable slug once
published). For a directory listing, populate: `displayName`, `version`
(semver), `description`, `author` (object: name/email/url), `homepage`,
`repository`, `license` (SPDX id), `keywords`. There is **no `category` field
in plugin.json** — `category` and `tags` live in the **marketplace.json
entry** (repo root `.claude-plugin/marketplace.json`; entry requires `name` +
`source`; `description` required by Anthropic's marketplace CI; names unique).

## 4. Directory Policy requirements (the ones that bind us)

- **§1D data minimization:** "Software must only collect data from the user's
  context that is necessary to perform their function… must not collect
  extraneous conversation data, even for logging purposes." Must not extract
  from Claude's memory/chat history/uploaded files.
- **§2 descriptions:** must precisely match functionality; no undelivered
  promises; "must not contain hidden, obfuscated, or encoded instructions.
  All behavioral guidance must be human-readable."
- **§3A privacy:** if the software collects user data or connects to a remote
  service → clear privacy policy link required. (We do neither — state so
  explicitly in README; becomes mandatory if any endpoint is ever contacted.)
- **§3B support contact** required.
- **§3C documentation:** how it works, intended purpose, troubleshooting.
- **§3D reviewability:** provide means to exercise functionality → our
  in-repo sample spec + expected JSON.
- **§3E:** "at least three working examples of prompts or use cases."

## 5. Trademark / branding

- Submitting grants Anthropic a license to display Voicenter's name/marks in
  the listing. You must own/control the branding used.
- The only trademark restriction is on **Anthropic's** marks: no implied
  partnership/sponsorship/endorsement; comply with Anthropic's Trademark
  Guidelines.
- Skill-level rule (separate from directory policy): skill `name` frontmatter
  must not contain "claude" or "anthropic".

## 6. Security posture (what screening looks at)

Plugins are "highly trusted components" executing with user privileges;
screening and optional org-level scanning review for malicious behavior.
Skills instructing external URL fetches or broad file writes get extra
scrutiny. **Our profile — skills-only, no hooks, no MCP, no network calls,
deterministic local JSON output — is near the lowest-risk class. State this
explicitly in the README and submission notes; make it legible to reviewers.**

## 7. Known doc inconsistency

Anthropic's submit page and discover-plugins page describe the
official/community relationship differently. Reconciled reading: one
community-driven directory fed by the form; Anthropic curates/promotes a
subset and applies "Verified." Re-verify exact surfacing at submission time;
set stakeholder expectations to "community directory listing," not
"claude-plugins-official inclusion."
