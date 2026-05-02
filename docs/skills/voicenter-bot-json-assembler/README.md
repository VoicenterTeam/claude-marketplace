# Skill: `voicenter-bot-json-assembler`

Assemble a fully-detailed Agent Spec into deployable Voicenter Bot JSON. Skill 3 in the three-skill pipeline.

> Source: [`plugins/voicenter-bot-builder/skills/voicenter-bot-json-assembler/SKILL.md`](../../../plugins/voicenter-bot-builder/skills/voicenter-bot-json-assembler/SKILL.md)
> Plugin: [voicenter-bot-builder](../../plugins/voicenter-bot-builder.md) · Pipeline phase: **3 / 3**

---

## What it does

Mechanically projects a `[detailed]` Agent Spec into Bot JSON wire format. Produces:

- `bot-<identifier>-<YYYY-MM-DD>.json` — the deployable JSON
- `bot-<identifier>-<YYYY-MM-DD>.banner.md` — a sidecar listing every fail-loud sentinel, drift note, and applied default

**Operating principle: pure parser, not interpreter.** Skill 3 makes no creative decisions. If the spec deviates from the strict template, Skill 3 emits a structured parse error and refuses to assemble. If the §15.4 cross-reference pass fails any of seven checks, Skill 3 emits a structured failure report with routing recommendations and refuses to emit JSON. The discipline is the design — if Skill 3 interpreted, "what JSON does this spec produce?" would depend on Skill 3's mood, and the source-of-truth contract dies.

The risk vector is **doing too much**: filling in plausible-looking values for unknowns, smoothing over template deviations, auto-fixing cross-reference violations. The skill's longest section (anti-list §8) is the explicit "do not" list.

---

## When to invoke

- Every intent in section 5 is `[detailed]` — Skill 2 is done.
- The user asked to *"assemble the JSON"*, *"emit the bot JSON"*, *"publish the bot"*, *"build the wire-format"*, or *"run Skill 3"*.
- Skill 2 emitted a handoff hint pointing to Skill 3.

Skill 3 refuses to run if any intent is still `[structural]` or `[detailed-revisit]` — it cites the pending list and recommends Skill 2.

---

## Pre-flight gates

Two gates run before any assembly. Both blocking. Refusal at either gate emits a clear message and halts; no JSON is produced.

| Gate | Check | Refusal route |
|---|---|---|
| **A — Completeness** | Section 5 has zero `[structural]` or `[detailed-revisit]` intents | Skill 2 (Intent Detail Author) |
| **B — Parseability** | Strict-template parser succeeds against the spec | Skill 1 patch mode (structural deviation) or manual fix |

In a malformed spec where section headers are missing entirely, Gate B fires first; in a structurally clean spec with pending intents, Gate A fires first.

---

## Strict-template parser

Skill 3 reads the Agent Spec as a fixed grammar — no synonyms, no flexibility, no creative tolerance. The parser expects:

- **Section headers exact:** `## 1. Bot Identity`, `## 2. Persona Bundle`, `## 3. Caller Silence Behavior`, `## 4. Intent List (Structural)`, `## 4.5 Available Variables`, `## 5. Intent Details`, `## 6. Cross-References`, `## 7. Generation Metadata`.
- **Field labels exact:** `**Bot Name:**`, `**Identifier:**`, `**Description:**`, `**Account ID:**`, `**Primary Language:**`, `**Channels Active:**`, `**Voice Name:**`, `**AI Model Config:**`.
- **Status markers exact:** `[structural]`, `[detailed]`, `[detailed-revisit]`. No synonyms.
- **Unknown markers exact:** `<UNKNOWN: <description>>`, `<INCOMPLETE: <description>>`, `[not configured]`. Angle brackets, literal token.
- **Intent header in section 4:** `### Intent N: <identifier>` where N is the 1-based ordinal.
- **Intent header in section 5:** `### Intent: <identifier>`.
- **Slot lines** in section 4: numbered, format `[slot_name] — \`ParameterTypeId\` [N], Required [\`true\`|\`false\`], Order [N], OptionList [if ENUM]`.
- **Transition lines** in section 4: numbered list under `**Transitions out:**`, target identifier optionally followed by a parenthetical role label.
- **RT-specific sub-labels in section 4:**
  - RT=1: `**Layer:**` followed by an integer.
  - RT=2: `**URL:**`, `**Method:**`, `**Headers:**`, `**Body:**`, `**API silence behavior:**` (six sub-bullets exact: `silence_duration:`, `silence_loops:`, `silence_sentence:`, `silence_ending_sentence:`, `silence_instructions:`, `fallback intent:`).
  - RT=3: empty.
  - RT=4: `**Dial source:**` (`parameter` | `static`), then `**Parameter phone:**` OR `**Phone1:**`/`**Phone2:**`/`**Phone3:**`, plus `**selectdial_option:**`, `**NEXT_VO_ID:**`, `**MAX_DIAL_DURATION:**`, `**Record:**`, optional `**Announcement:**` / `**Loading announcement:**` / `**Post-execution intent instructions:**`, and `**Response success:**`.

Common deviations the parser surfaces:

| Deviation | Example error |
|---|---|
| Missing section header | `Expected: '## 4. Intent List (Structural)'. Found: '## Intent List'. Fix: restore the section number and exact heading.` |
| Bold field label punctuation off | `Expected: '**Bot Name:** <value>'. Found: 'Bot Name: <value>'. Fix: wrap the label in bold markdown.` |
| Unknown marker shape wrong | `Expected: '<UNKNOWN: <description>>'. Found: '(UNKNOWN: ...)'. Fix: use angle brackets and the literal token UNKNOWN.` |
| RT-specific sub-label punctuation off | `Expected: '**URL:** <value>'. Found: 'URL: <value>'. Fix: wrap the sub-label in bold markdown.` |
| Status marker synonym | `Expected: one of '[structural]', '[detailed]', '[detailed-revisit]'. Found: '[done]'. Fix: re-run Skill 2 to set the canonical marker.` |
| Section 4 transition target missing | `Intent 'validate_customer_address' transitions to 'get_slots', but no intent 'get_slots' exists in section 4 (closest match: 'get_available_slots'). Fix: re-run Skill 1 patch mode.` |

Skill 3 halts on the first deviation, emits a structured error, and does not attempt to interpret around it. One deviation, one error, one halt.

---

## Spec-to-wire-format assembly

Runs only if both pre-flight gates pass.

### ID placeholder allocation

Sequential negative integers, range-coded so the kind of ID is identifiable at a glance:

| ID kind | Placeholder range | Rule |
|---|---|---|
| `BotID` | `-1` | Single value |
| `BotVersionId` | `-2` | Single value |
| `IntentCategoryId` | `-3` | Single default category |
| `IntentId` | `-10, -11, -12, ...` | One per intent in section 4 ordering |
| `BotIntentID` | `-100, -101, -102, ...` | One per intent, same ordering |
| `ParameterId` | `-1000, -1001, ...` | One per slot, intent-by-intent then slot-by-slot |

Real platform-assigned IDs after import are positive integers, so there's no collision risk on re-export.

### Top-level wrapper and version envelope

Section 1 fields map to top-level root keys. The two `AIModelConfig` objects (top-level `AiModelConfig` + version-level `AIModelConfig` per Doc 1 §6) are emitted with byte-identical `created` payload — this duplication is a §16 schema quirk preserved deliberately.

### Per-RT Configuration assembly

Skill 3 emits the Configuration shape per Response Type, populating language fields verbatim from section 5:

| RT | Configuration keys |
|---|---|
| 1 | `layer`, `announcement`, `intentLoadingAnnouncement` |
| 2 | `url`, `method`, `headers`, `body`, `apiResponseAnnouncement`, `fail_output`, `function_output`, `intentLoadingAnnouncement`, `IntentLoadingAnnouncement` (case-bug pair preserved), `intentInstructions`, `api_silence_behaviour`, `response_success: ""` |
| 3 | `announcement`, `intentInstructions`, `response_success: ""` |
| 4 | `phone1`, `phone2`, `phone3`, `parameter_phone` (when slot-driven), `selectdial_option`, `NEXT_VO_ID`, `MAX_DIAL_DURATION`, `record`, `announcement`, `intentLoadingAnnouncement`, `intentInstructions`, `response_success` (object with `instructions` key) |

### Quirk preservation

Skill 3 walks Appendix A (the §16 schema-quirks list) after assembly and verifies every quirk is correctly emitted: `IntentResponces` typo, RT=2 case-bug pair, `HandlingInstructions: null` per intent, `SystemPrompt: ""`, dual `AiModelConfig` / `AIModelConfig`, `tools: []`, `instructions: ""`, `IntentScripts: {}`, `ValidationRules: {}` and `ValidationPattern: null` per param, `silenceRelations: []`, `BotLanguages: []`, `llmDescription: ""`, `response_success: ""` on RT=2/RT=3, `Priority: 1` / `MaxAttempts: 3` / `ValidationTimeout: 30` per intent, `silence_behaviour` key omission when section 3 is `[not configured]`. Mis-emission is a Skill 3 internal bug — halt and report.

### Sentinel emission for unknowns

| Spec marker | Wire-format emission |
|---|---|
| `<UNKNOWN: webhook_url>` (string) | `"<USER_TO_FILL: webhook_url>"` |
| `<UNKNOWN: layer ID>` (integer ID) | `-999` |
| `<UNKNOWN: NEXT_VO_ID>` (integer) | `-999` |
| `<UNKNOWN: phone destination>` (string) | `"<USER_TO_FILL: phone3>"` |
| `<UNKNOWN: Account ID>` (integer ID) | `-999` |
| `<UNKNOWN: AI Model Config>` (cascade) | `<USER_TO_FILL: ...>` for strings, `-999` for IDs across the whole `AiModelConfig` block |
| `<UNKNOWN: <object field>>` (object) | `{}` plus a banner note |
| `<INCOMPLETE: ...>` (section partial) | Section emitted with available content; banner notes incompleteness |
| `[not configured]` (whole section) | Section omitted from JSON entirely |

The sentinel value carries the field role inside the placeholder text, so the banner's path-plus-value listing is self-documenting.

---

## §15.4 cross-reference pass — seven blocking checks

After assembly + section 6 sanity check, run all seven §15.4 checks against the in-memory wire structure. **All blocking.** All seven run unconditionally so the user gets a complete failure report rather than fixing one issue at a time.

| # | Check | Validates |
|---|---|---|
| 1 | `botIntents[].IntentID` resolves | Every `botIntents[].IntentID` matches an `intents[].IntentId` |
| 2 | `intentRelations[]` resolves (both endpoints) | Every `OriginIntentID` and `NextIntentID` matches an `intents[].IntentId` |
| 3 | `apiSilenceRelations[]` resolves (both endpoints) | Every `OriginIntentID` and `ApiSilenceIntentID` matches an `intents[].IntentId` |
| 4 | `intents[].IntentCategoryId` resolves | Every `IntentCategoryId` matches an `intentCategories[].IntentCategoryId` |
| 5 | RT=2 has `apiSilenceRelations[]` pairing | Every RT=2 intent has a corresponding `apiSilenceRelations[]` entry |
| 6 | `api_silence_behaviour` matches `apiSilenceRelations[].Configuration` | Field-by-field deep equality on the 6 silence fields |
| 7 | Mustache resolvability | Every Mustache token resolves via 4.5.1 / 4.5.2 / 4.5.3 / 4.5.4 with directional ordering |

Failure routing:

| Failure | Route |
|---|---|
| Check 1, 2, 3 — dangling ID | Skill 1 patch mode (structural error — intent deleted but reference not cleaned up) |
| Check 4 — IntentCategoryId mismatch | Skill 1 patch mode (should never happen in v1; if it does, hand-edit error or Skill 1 bug) |
| Check 5 — RT=2 missing pairing | Skill 1 patch mode (RT=2 structural authoring incomplete) |
| Check 6 — `api_silence_behaviour` mismatch | Skill 3 internal bug (Skill 3 emits both from the same source; mismatch means emission bug) |
| Check 7 — Mustache unresolvable | Skill 1 patch mode (variable should exist — add to 4.5.1 / 4.5.4) OR Skill 2 reactivation (reference is wrong — typo) |

Skill 3 does not invoke Skill 1 or Skill 2 itself. It reports the routing recommendation; the user invokes the appropriate skill.

---

## Filename convention

`bot-<bot-snake-name>-<YYYY-MM-DD>.json`

`<bot-snake-name>` is the spec section 1 `**Identifier:**` value (a snake_case ASCII identifier captured by Skill 1 at interview time). If the field is missing (legacy spec from before v1.0), Skill 3 falls back to ASCII-folding `**Bot Name:**`, then to `bot`. For Hebrew bot names, this fallback fails — which is why Skill 1 asks for an explicit identifier.

Companion banner file (Claude Code only): `bot-<bot-snake-name>-<YYYY-MM-DD>.banner.md`.

If the file already exists in the workspace, Skill 3 appends `-<counter>` before `.json`.

---

## Banner format

The banner is rendered **above** the JSON (single-conversation runtime) or as a sidecar file (Claude Code runtime). Plain text — never embedded in the JSON itself, so the user can copy the JSON code block directly.

```
# Voicenter Bot JSON — generation banner
# Skill suite: v1
# Generated: <ISO-8601 timestamp>
# Source spec: <spec source reference>
# Source spec version: <from section 7.1>
#
# UNKNOWN VALUES — user must replace before import:
#   - <wire-format JSON path>: <sentinel value> (<role description>)
#   [...]
#
# DRIFT NOTES (section 6 sanity check):
#   - 6.1: <one-line drift summary> [if any]
#   [or:]
#   - No drift detected.
#
# RECONCILIATION (section 7.4 vs emitted sentinels):
#   - <one-line note per discrepancy> [if any]
#   [or:]
#   - 7.4 and emitted sentinels in agreement.
#
# DEFAULTS APPLIED:
#   - generationConfig.temperature = 1.5 (v1 default)
#   - generationConfig.topP = 0.95 (v1 default)
#   - generationConfig.topK = 64 (v1 default)
#   - [...]
```

Each section is always emitted, even if its content is "(none)" — consistent banner shape regardless of whether the spec was tidy. The "DEFAULTS APPLIED" section lists every value Skill 3 emitted that wasn't authored in the spec; this makes Skill 3's contributions auditable.

---

## Section 6 drift handling

After §4 assembly and before §6 cross-reference pass, Skill 3 regenerates spec sections 6.1–6.5 from sections 4-5 and compares to the spec's existing section 6. Subsection-by-subsection diff, normalized for whitespace and ordering.

**Drift handling: soft warning, not blocking.** Section 6 is derivative; sections 4-5 are authoritative. If the regenerated 6 differs, Skill 3 records the drift in the banner ("DRIFT NOTES") and the section 7.3 generation log, but does not auto-fix and does not block emission. If the user cares enough about the drift to fix it, they invoke Skill 1 patch mode (which regenerates section 6 cleanly).

---

## Output contract

**On success:**

- A single JSON object per Doc 1 §4 — pretty-printed with 2-space indent, UTF-8, keys in Doc 1 documentation order
- Valid JSON only — no comments, no trailing commas
- Banner emitted as plain text (single-conversation) or a sidecar file (Claude Code)
- Spec section 7.3 updated with: timestamp, sentinel count, drift count, cross-reference pass result

**On failure:**

- No JSON emitted
- Spec section 7.3 updated with the failure log
- Closing message points to the appropriate skill or fix path

### Runtime-specific delivery

| Runtime | Output |
|---|---|
| **Single-conversation** | Banner rendered as plain text in the chat message; JSON in a fenced code block; closing message instructs how to copy and import |
| **Claude Code** | JSON written to `bot-<id>-<date>.json`; banner written to `bot-<id>-<date>.banner.md`; closing message references both files |

---

## Anti-list — what Skill 3 does NOT do

- Author any text content (Skills 1 and 2 only)
- Make creative decisions about RT-specific defaults the spec didn't specify
- Fill in plausible-looking values for unknowns (fail loud with sentinels instead)
- Smooth over template deviations (parse error and halt instead)
- Auto-fix cross-reference violations (route to Skill 1 / Skill 2 instead)
- Invoke other skills (recommends routing; the user invokes)
- Emit a partial JSON when assembly fails midway
- Modify the spec beyond the section 7.3 generation log entry

---

## Common pitfalls

- **Spec has `[detailed-revisit]` intents.** Skill 3 refuses at Gate A. Run Skill 2 to redetail them.
- **Hand-edited spec breaks the strict template.** Skill 3 refuses at Gate B with a one-line fix hint. Either fix manually or run Skill 1 patch mode.
- **Filename produces `bot-bot-<date>.json`.** The spec is missing `**Identifier:**` (legacy spec from before v1.0). Run Skill 1 patch mode to add the field.
- **Cross-reference Check 7 fails on a typo.** Re-run Skill 2 for the affected intent, fix the Mustache reference, re-invoke Skill 3.
- **Cross-reference Check 1/2/3 fails on a deleted intent.** Spec was edited inconsistently — run Skill 1 patch mode to clean up the references.
- **Banner says `<USER_TO_FILL: bot description>` and similar.** Expected — the spec marked these as `<UNKNOWN: ...>`. Replace before importing to the platform.

---

## Related skills

- [voicenter-bot-spec-designer](../voicenter-bot-spec-designer/README.md) — Skill 1; produces the structural skeleton Skill 3 reads.
- [voicenter-bot-intent-detail-author](../voicenter-bot-intent-detail-author/README.md) — Skill 2; fills the language Skill 3 emits verbatim.
