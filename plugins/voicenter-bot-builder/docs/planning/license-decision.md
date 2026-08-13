# License decision — open items for legal / lead sign-off

**Status: NOT signed off. Do not submit to the Anthropic plugin directory until §2 is
cleared.** MS4 step 4.2 is the blocking gate.

---

## 1. What is already decided (recorded in the repo)

The license *choice* was not invented by this milestone — it is pre-existing:

| Where | Value |
|---|---|
| Repo-root `LICENSE` | MIT, "Copyright (c) 2025 Voicenter" |
| Repo-root `.claude-plugin/marketplace.json` → bot-builder entry | `"license": "MIT"` |
| `plugins/voicenter-bot-builder/.claude-plugin/plugin.json` (added in MS4) | `"license": "MIT"` |
| `plugins/voicenter-bot-builder/LICENSE` (added in MS4) | copy of the repo-root MIT text |

The plugin-level `LICENSE` copy exists because a marketplace install copies **only the plugin
directory** into `~/.claude/plugins/cache`. Without it, the installed plugin would carry no
license text at all.

MIT is a permissive OSI license and satisfies the directory's licensing expectation for the
plugin *wrapper*. Nothing below disputes that.

---

## 2. What legal must confirm before submission

The plugin does not just ship code and prompts — it bundles reference material that
**describes Voicenter's proprietary bot wire format in field-level detail**. Publishing it
under MIT grants anyone the right to use, modify and redistribute that description
commercially. That is a business decision, not an engineering one.

### 2.1 Distribution rights on the bundled reference material

| File | What it discloses |
|---|---|
| `references/verification-procedure.md` | The 24 validation invariants of the wire format, including exact field names, the `api_silence_behaviour` contract, and the ID placeholder scheme |
| `references/field-placement-doctrine.md` | FP-1…FP-13 — which prompt field carries which content, derived from production root-cause analysis of Voicenter bots |
| `references/voice-prompt-doctrine.md` | The Compass distillation, including token budgets and model-config specifics for the deployed Gemini Live configuration |
| `skills/voicenter-bot-spec-designer/model-catalog.md` | Real platform `AIModelConfigID` / `AIModelTypeId` values and provider model strings, sourced from `AIModelConfig.Data.sql` |
| `skills/voicenter-bot-json-assembler/stages/assembly-mapping.md` | The complete spec→wire field mapping, the §16 schema quirks, and Appendix D static reference data (status IDs, type IDs, system-dictionary rows) |
| `skills/voicenter-bot-json-assembler/stages/parse-errors.md` | Strict-template grammar |

**Confirm:** is Voicenter content to publish all of the above under MIT?

Three possible outcomes, each with a different action:

1. **Yes, all MIT.** No further action; strike this section and record the approval date.
2. **Wrapper MIT, reference material proprietary.** The reference files need proprietary
   headers and the README needs a licensing note distinguishing the two. Note that a
   dual-license arrangement inside a single published plugin is unusual and may draw
   directory-review questions — worth confirming it is acceptable before building it.
3. **Some content must not ship at all.** Then the affected material has to be reduced to
   non-disclosing form (rule statements without field-level specifics), which is a content
   rewrite with real behavioural risk — the skills depend on those specifics to emit correct
   JSON. Treat as a scope change, not a tidy-up.

### 2.2 Model-catalog IDs

`model-catalog.md` carries live platform row IDs from `AIModelConfig.Data.sql`. Confirm these
are not considered sensitive configuration. They are not credentials, but they are internal
database identifiers.

### 2.3 Branding

MS4 §4.6 requires that Voicenter branding in the plugin is authorized and that nothing
implies Anthropic endorsement. The README written in MS4 makes no endorsement claim. Confirm
the Voicenter name/marks usage is approved for a public Anthropic-directory listing.

### 2.4 Copyright year

Repo-root `LICENSE` reads "Copyright (c) 2025 Voicenter". If the first public release lands in
2026, confirm whether the notice should read `2025-2026` or be left as-is. Cosmetic, but it is
the kind of thing a reviewer notices.

---

## 3. Not legal questions, but submission-checklist items

### 3.1 The planning tree ships inside the plugin

`plugins/voicenter-bot-builder/docs/` currently ships **inside** the plugin, so it is copied to
every install. It carries no instructions Claude will load — the plugin runtime reads only
`skills/`, `agents/`, `commands/` and files those reference — so there is no behavioural risk.
But it adds install weight and exposes internal milestone planning to anyone who installs.

Decide before submission: leave it, or relocate the planning tree to the repo root (which means
updating every path reference in `session-prompts.md`).

### 3.2 Sibling manifests are not strict-clean

`claude plugin validate --strict` passes on `voicenter-bot-builder` as of v1.20.0, but **fails
on the marketplace root and on `voicenter-mcp` / `voicenter-api`**, all for the same reason:
those `plugin.json` files carry no `author` block.

This predates v1.20.0 and belongs to those plugins' own versioning — CLAUDE.md requires a
version bump in lockstep with any manifest change, so adding `author` to three sibling
manifests is their release, not this one. The CI job (`.github/workflows/plugin-validate.yml`)
therefore gates bot-builder strictly and validates the siblings non-strict, reporting the
strict failures as informational output so the gap stays visible without blocking every build.

Decide before submission: whether the *marketplace root* failing strict validation matters for
the directory listing. If it does, the sibling `author` blocks need adding and those plugins
bumping — a small change, but a deliberate one.

---

## 4. Sign-off

| Item | Owner | Status | Date |
|---|---|---|---|
| 2.1 Distribution rights on bundled reference material | | **pending** | |
| 2.2 Model-catalog IDs not sensitive | | **pending** | |
| 2.3 Branding authorized, no Anthropic endorsement implied | | **pending** | |
| 2.4 Copyright year | | **pending** | |
| 3. `docs/` ships-or-relocates decision | | **pending** | |
