# Skill 3 stage — Sentinels, drift reporting and the banner

*Load this after the cross-reference pass passes and before emitting (Skill 3 §7). It
carries the sentinel bookkeeping for unknowns, the section-6 regeneration sanity check and
its drift semantics, the banner format, and a worked banner example.*

*The banner is plain text rendered above the JSON (single-conversation) or written as a
sidecar file (Claude Code) — never embedded in the JSON, so the user can copy the JSON
straight into the importer.*

## Table of contents

- [4.6 Sentinel emission for unknowns](#46-sentinel-emission-for-unknowns)
- [5. Section 6 regeneration sanity check](#5-section-6-regeneration-sanity-check)
- [7.2 Banner format](#72-banner-format)
- [Appendix C — Banner worked example](#appendix-c--banner-worked-example)
- [6.4 Cross-reference failure report format](#64-cross-reference-failure-report-format)
- [7.5 / 7.6 Spec section 7.3 log entries](#75--76-spec-section-73-log-entries)

---

### 4.6 Sentinel emission for unknowns

Walk spec section 7.4. For each unknown marker, the corresponding wire-format field has already received a sentinel during §4.2-4.4. §4.6 is the bookkeeping pass:

1. Build the **sentinel inventory**: for each `<UNKNOWN: ...>` marker in section 7.4, identify the wire-format JSON path that received the sentinel and the sentinel value emitted.
2. Build the **disagreement list**: any `<UNKNOWN: ...>` in section 7.4 that did not produce a sentinel (Skill 1/2 staged the unknown but Skill 3 didn't find a wire-format slot for it), or any sentinel emitted at §4.2-4.4 that is not in section 7.4 (Skill 3 found an unknown the spec didn't track).
3. Both lists feed the banner (§7.2). The sentinel inventory is the user's pre-import checklist; the disagreement list is a soft warning about spec/skill drift.

**Sentinel format reference:**

| Spec marker shape | Wire-format emission |
|---|---|
| `<UNKNOWN: webhook_url>` (string field) | `"<USER_TO_FILL: webhook_url>"` |
| `<UNKNOWN: NEXT_VO_ID>` (integer field) | `-999` |
| `<UNKNOWN: phone destination>` (string) | `"<USER_TO_FILL: phone3>"` |
| `<UNKNOWN: Account ID>` (integer ID) | `-999` |
| `<UNKNOWN: AIModelConfigID>` (integer ID) | `-999` |
| `<UNKNOWN: AIModelTypeId>` (integer ID) | `-999` |
| `<UNKNOWN: AI Model Config>` (string name → triggers all model fields unknown) | `<USER_TO_FILL: ...>` for strings, `-999` for IDs across the whole `AiModelConfig` block |
| `<UNKNOWN: <some object field>>` (object) | `{}` plus a banner note |
| `<INCOMPLETE: ...>` (section partial) | Section emitted with available content; banner notes incompleteness |
| `[not configured]` (whole-section omission) | Section omitted from JSON entirely |

The sentinel value carries the field role (`webhook_url`, `phone3`, `model_config_name`) inside the placeholder text, so the banner's path-plus-value listing is self-documenting.

---

## 5. Section 6 regeneration sanity check

After §4 assembly completes and before §6 cross-reference pass: regenerate spec section 6 (subsections 6.1–6.5) from sections 4-5 fully. Compare to the spec's existing section 6.

| Subsection | Regeneration source |
|---|---|
| 6.1 Mustache variable usage | Walk every text field across sections 2 and 5 + section 4 RT=2 body; for each Mustache reference, record `(reference, location, resolution source)`. |
| 6.2 Intent transition graph | Flatten section 4 transitions out → list of `(origin → next)` pairs, deduped. **Authored transitions only (v1.12.0 — no global fan-out);** this matches the emitted `intentRelations[]` and Skill 1's section 6.2, so no spurious drift is reported. |
| 6.3 RT=2 API silence pairings | For each RT=2 intent, the `apiSilenceRelations[]` registry entry that pairs with its embedded `api_silence_behaviour`. |
| 6.4 Escalation paths | For each non-terminal intent, the transition row that points to escalation. |
| 6.5 ID assignments | The `<identifier> → IntentId` mapping built in §4.1. |

**Comparison logic:** subsection-by-subsection diff. Differences are normalized for whitespace and ordering before comparison — section 6 in spec is allowed to list entries in any order, since it's derivative.

**Drift handling: soft warning, not blocking.** Section 6 is derivative; sections 4-5 are authoritative. If the regenerated 6 differs from the spec's 6, that's a signal that either (a) sections 4-5 were edited inconsistently after section 6 was generated (e.g., manual edits between Skill 1/2 invocations), or (b) Skill 1/2's section 6 update logic has a bug. Skill 3 doesn't auto-fix and doesn't block emission. It records the drift in the banner and section 7.3 generation log.

The banner section "DRIFT NOTES" lists each subsection that drifted, with a one-line summary (e.g., `6.1: regenerated had 3 references the spec missed; 6.2: spec had 1 transition that no longer exists in section 4`).

If the user cares enough about the drift to fix it, they invoke Skill 1 patch mode (which regenerates section 6 cleanly). Otherwise the JSON is still emitted from the authoritative sections 4-5.

---

### 7.2 Banner format

The banner is rendered **above** the JSON (single-conv runtime) or as a sidecar file (Claude Code runtime). It is plain text — never embedded in the JSON itself — so the user can copy the JSON code block directly without stripping anything before importing.

**Banner sections, in order:**

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
#   - 6.2: <one-line drift summary> [if any]
#   - [...]
#   [or:]
#   - No drift detected.
#
# RECONCILIATION (section 7.4 vs emitted sentinels):
#   - <one-line note per discrepancy> [if any]
#   [or:]
#   - 7.4 and emitted sentinels in agreement.
#
# DOCTRINE SENTINELS (Compass advisories not resolved during authoring):
#   - Rule <N> (<name>): <one-line summary> — see references/voice-prompt-doctrine.md rule <N> for fix recipe
#   [...]
#   [or:]
#   - No doctrine sentinels.
#
# DEFAULTS APPLIED:
#   - ActiveVersionInfo.AIModelConfig.created.realtimeInputConfig.automaticActivityDetection.disabled = "true" (v1.5.0 lean payload constant)
#   - ActiveVersionInfo.AIModelConfig.max_duration = 1200 (v1.5.0 default — see spec section 1)
#   - ActiveVersionInfo.AIModelConfig.daily_limit = 600, dailyLimitLayerId = 3, maxDurationLayerId = 0, IVRLayerSelect_2 = 3 (v1.14.0 defaults — layer targets are account-specific; verify after import)
#   - IntentConfig.additional defaults applied (max_turns = 5 / sensitive = false / max_turns_sentence masculine fallback) on intents without spec overrides (v1.14.0)
#   - ActiveVersionInfo.AIModelConfig.recordAgentCalls = "false" (v1.5.0 default — see spec section 1)
#   - [...]
#
# MANDATORY POST-IMPORT STEP (v1.14.0 — emitted whenever silence_behaviour.intent is a placeholder):
#   - silence_behaviour.intent = <placeholder> is a pre-import placeholder the import procedure does NOT
#     remap — after import, set the silence forward to "<display name>" in the UI
#     (the target intent is identifiable by IsSilenceIntent: 1).
#
# MANDATORY POST-IMPORT STEP (v1.16.0 — emitted whenever spec section 1 carries **Negative instructions:**):
#   - Negative instructions are NOT emitted to the JSON (wire field unverified) — after import, paste the
#     spec's Negative instructions text into the UI's AI Security Settings → Negative Instructions field:
#     "<spec section 1 Negative instructions text>"
```

Each section is always emitted, even if its content is "(none)" or "(in agreement)" — the user gets a consistent banner shape regardless of whether the spec was tidy. Appendix C has a worked example.

The "DEFAULTS APPLIED" section lists every value Skill 3 emitted that was not authored in the spec — generation params, the constants per Doc 1 §16 (e.g., `Priority: 1`, `MaxAttempts: 3`), and the catalog-derived `created` payload defaults. This makes Skill 3's contributions auditable: anything not in the banner came from the spec.

**DOCTRINE SENTINELS population (Compass rule 13).** Walk section 7.3 of the spec. For each log entry of the form `Compass rule <N> advisory fired on [<context>] — user kept original` (or any variant where the user opted not to fix), emit one banner line under DOCTRINE SENTINELS. The line format is:

```
# - Rule <N> (<rule name>): <human-readable summary of the violation in context> — see references/voice-prompt-doctrine.md rule <N> for fix recipe
```

Rule names are sourced from the reference catalog (`references/voice-prompt-doctrine.md` §1 headings). Example lines:

```
# - Rule 3 (English operational, target-language utterances): prompts.persona is 87% Hebrew on a he-IL bot; user kept original — see references/voice-prompt-doctrine.md rule 3 for fix recipe
# - Rule 7 (Generic-policy boilerplate): "GDPR" appears in prompts.persona; user kept (declared domain-appropriate) — see references/voice-prompt-doctrine.md rule 7 for fix recipe
# - Rule 10 (Few-shot example cap): collect_inquiry_details.validationPrompt has 3 transcript pairs (Hebrew bot — ~750 tok cost); user kept — see references/voice-prompt-doctrine.md rule 10 for fix recipe
```

If no Compass advisories fired or all were resolved, emit `# - No doctrine sentinels.` (matching the established pattern of the other banner sections).

The DOCTRINE SENTINELS section is **structural** per the doctrine catalog (rule 13) — auto-applied based on the spec's section 7.3 trail; no user prompt and no opt-out at emission time. If a user wants a clean banner, they fix the advisories during Skill 1 / Skill 2 authoring.

## Appendix C — Banner worked example

Sample banner for a hypothetical bot with: 1 unknown webhook URL, no model config IDs (Gemini Live with TODO), section 6 drift on subsection 6.1 (a Mustache reference Skill 2 forgot to log), and section 7.4 in agreement with emitted sentinels. (Note: RT=1 layer no longer produces a sentinel as of v1.12.0 — it defaults to `0`.)

```
# Voicenter Bot JSON — generation banner
# Skill suite: v1
# Generated: 2026-05-01T14:32:18Z
# Source spec: agent-spec.md
# Source spec version: 1.0.0
#
# UNKNOWN VALUES — user must replace before import:
#   - intents[1].IntentResponces.Configuration.url: "<USER_TO_FILL: webhook_url>" (RT=2 webhook for validate_customer_address)
#   - AccountID: -999 (customer account ID; user knows this)
#   - AiModelConfig.AIModelConfigID: -999 (Gemini Live; catalog has TODO)
#   - AiModelConfig.AIModelTypeId: -999 (Gemini Live; catalog has TODO)
#   - ActiveVersionInfo.AIModelConfigId: -999 (mirror of above)
#
# DRIFT NOTES (section 6 sanity check):
#   - 6.1: regenerated had 1 reference the spec did not log — {{caller_phone}} used in confirm_appointment.intentInstructions
#   - 6.2: in agreement
#   - 6.3: in agreement
#   - 6.4: in agreement
#   - 6.5: in agreement
#
# RECONCILIATION (section 7.4 vs emitted sentinels):
#   - 7.4 and emitted sentinels in agreement.
#
# DOCTRINE SENTINELS (Compass advisories not resolved during authoring):
#   - No doctrine sentinels.
#
# DEFAULTS APPLIED:
#   - ActiveVersionInfo.AIModelConfig.created.realtimeInputConfig.automaticActivityDetection.disabled = "true" (v1.5.0 lean payload constant)
#   - ActiveVersionInfo.AIModelConfig.max_duration = 1200 (v1.5.0 default — see spec section 1)
#   - ActiveVersionInfo.AIModelConfig.daily_limit = 600, dailyLimitLayerId = 3, maxDurationLayerId = 0, IVRLayerSelect_2 = 3 (v1.14.0 defaults — layer targets are account-specific; verify after import)
#   - IntentConfig.additional defaults applied (max_turns = 5 / sensitive = false / max_turns_sentence masculine fallback) on intents without spec overrides (v1.14.0)
#   - ActiveVersionInfo.AIModelConfig.recordAgentCalls = "false" (v1.5.0 default — see spec section 1)
#   - All intents: Priority = 1, MaxAttempts = 3, ValidationTimeout = 30 (per Doc 1 §9.0)
#   - intentCategories: single default category, IntentCategoryId = -3
#   - All §16 quirks emitted per Appendix A checklist
```

The banner stays terse — one line per item, prefixed with `#` so the user can paste it as a comment block in their notes if useful. The JSON code block follows the banner directly with no decorative separator beyond a blank line.

---

---

## 6.4 Cross-reference failure report format

**On any check failing:** emit a structured error report:

```
Skill 3 cross-reference pass failed.

Checks failed: <count> of <total checks run>
Checks passed: <count>

[For each failure:]
CHK-NN: <check name>
  Violation: <one-line description>
  Field path: <wire-format path or spec source>
  Route to: <Skill 1 patch mode | Skill 2 reactivation | Skill 3 internal bug>
  Suggested fix: <one-line hint>

No JSON emitted. Section 7.3 has been updated with this failure log.

Next step: <route guidance based on highest-frequency failure type>.
```

Skill 3 does not invoke Skill 1 or Skill 2 itself. The user reads the routing
recommendation and invokes the appropriate skill, then re-invokes Skill 3.

---

## 7.5 / 7.6 Spec section 7.3 log entries

### 7.5 Spec section 7.3 update — success path

Append one entry to spec section 7.3:

```
[ISO-8601 timestamp]  Skill 3  assembling  Emitted bot.json. <N> sentinels listed in banner. <D> drift notes. Section 7.4: <unknowns count>. Cross-reference pass: <passed>/<total> passed.
```

In single-conv: this entry appears in the regenerated spec, which is part of Skill 3's chat output below the JSON code block.

In Claude Code: write the updated spec back to `agent-spec.md`.

### 7.6 Spec section 7.3 update — failure path

If parse fails, completeness gate fails, or cross-reference pass fails: append one entry to spec section 7.3:

```
[ISO-8601 timestamp]  Skill 3  assembling  Failed at <stage>: <one-line summary>. No JSON emitted. Route: <skill recommendation>.
```

`<stage>` is one of `parse`, `gate-completeness`, `cross-reference-pass-N` (where N is the failing check), or `internal`.

In Claude Code, write the updated spec back. In single-conv, the regenerated spec with the failure log is part of the error output.

---
