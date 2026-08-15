# Verification Procedure (25-check cross-reference pass)

**Single source of truth** for the Voicenter Bot cross-reference verification pass. Every
consumer executes this file and nothing else: the `spec-verifier` subagent, Skill 3's
inline path, and any future CI harness. No check text lives anywhere else in the plugin.

Origin: Doc 1 §15.4 (checks 1–8), Compass doctrine (9, 10, 14 via
`voice-prompt-doctrine.md`), botIntents-role integrity (11–13), duplicate-global (15),
field-placement doctrine (16–24 via `field-placement-doctrine.md`), and the
`ImportBotFromJSON` stored-procedure contract (25 via `voicebot-json-contract.md`).

Check IDs `CHK-01`…`CHK-25` map 1:1 to the legacy numbering. **Never renumber.**
Retire an ID if a check is removed; append new IDs at the end.

> **CHK-25 was appended, not renumbered.** It arrived with the functional v1.18.0
> (`ActiveVersionInfo.PersonaID` emission) after this file became canonical. Adding a check
> means: one entry below, one TOC line, one severity-table cell, one run-order position —
> and nothing else anywhere in the plugin. That is the property this file exists to provide.

---

## Table of contents

- [How to execute this file](#how-to-execute-this-file)
- [Checks](#checks)
  - [CHK-01 — botIntents[].IntentID resolves](#chk-01--botintentsintentid-resolves)
  - [CHK-02 — intentRelations[] resolves (both endpoints)](#chk-02--intentrelations-resolves-both-endpoints)
  - [CHK-03 — apiSilenceRelations[] resolves (both endpoints)](#chk-03--apisilencerelations-resolves-both-endpoints)
  - [CHK-04 — intents[].IntentCategoryId resolves](#chk-04--intentsintentcategoryid-resolves)
  - [CHK-05 — RT=2 pairing and inline failover](#chk-05--rt2-pairing-and-inline-failover)
  - [CHK-06 — Configuration deep equality](#chk-06--configuration-deep-equality)
  - [CHK-07 — Mustache resolvability](#chk-07--mustache-resolvability)
  - [CHK-08 — Assembled-prompt token budget](#chk-08--assembled-prompt-token-budget)
  - [CHK-09 — Session-resumption ceiling](#chk-09--session-resumption-ceiling)
  - [CHK-10 — Model-config doctrine](#chk-10--model-config-doctrine)
  - [CHK-11 — Global registered as type-2](#chk-11--global-registered-as-type-2)
  - [CHK-12 — No chained intent in botIntents](#chk-12--no-chained-intent-in-botintents)
  - [CHK-13 — Start point exists](#chk-13--start-point-exists)
  - [CHK-14 — Section-4.6 catalog intents resolve](#chk-14--section-46-catalog-intents-resolve)
  - [CHK-15 — No duplicate global intents by tool name](#chk-15--no-duplicate-global-intents-by-tool-name)
  - [CHK-16 — validationPrompt speech-free](#chk-16--validationprompt-speech-free)
  - [CHK-17 — RT=3 intentLoadingAnnouncement present](#chk-17--rt3-intentloadingannouncement-present)
  - [CHK-18 — Own-parameter references](#chk-18--own-parameter-references)
  - [CHK-19 — No duplicate speak-obligation](#chk-19--no-duplicate-speak-obligation)
  - [CHK-20 — Terminal shape](#chk-20--terminal-shape)
  - [CHK-21 — ParameterType dictionary byte-match](#chk-21--parametertype-dictionary-byte-match)
  - [CHK-22 — No authored edges into type-2 globals](#chk-22--no-authored-edges-into-type-2-globals)
  - [CHK-23 — Off-topic global present](#chk-23--off-topic-global-present)
  - [CHK-24 — Turn-yield announcement gating](#chk-24--turn-yield-announcement-gating)
  - [CHK-25 — Persona FK sanity](#chk-25--persona-fk-sanity)
- [Output contract](#output-contract)

---

## How to execute this file

### What the pass operates on

The **assembled in-memory wire structure**, not the spec. CHK-16…CHK-24 additionally
consult the spec's section-4 staggering/terminal/role fields (CHK-24 reads
`**Asks next:**`), the 4.5 variable inventory, and — for CHK-23 — the persona text.

Sentinel values (`-999`, `<USER_TO_FILL: ...>`) are present at this point and are **not**
treated as missing references for the ID-resolution checks (CHK-01…CHK-04). Those operate
on placeholder integers (the negative-integer cache), which are internally consistent by
construction; sentinel `-999` only appears in user-supplied ID fields (`AccountID`,
`layer`, `NEXT_VO_ID`), which are not the subject of any check.

When executing standalone (subagent or CI) against a spec that has not been assembled,
derive the wire structure per Skill 3 §4 first, then run the checks against it.

### Run order

```
1 → 2 → 3 → 4 → 5 → 6 → 7 → 11 → 12 → 13 → 15 → 16 → 17 → 18 → 19 → 20
  → 21 → 22 → 23 → 24 → 8 → 9 → 10 → 14 → 25
```

**All checks run unconditionally — no short-circuit on first failure.** The caller gets a
complete failure report rather than fixing one issue at a time.

### Model gating

CHK-08, CHK-09 and CHK-10 fire only when `AiModelConfig.AIModelConfig.created.model` is
`models/gemini-3.1-flash-live-preview`. On any other model they **skip silently**, with a
one-time per-spec log entry to spec section 7.3. CHK-11…CHK-13, CHK-15, CHK-16…CHK-24 and
CHK-25 are model-agnostic.

### Severity

| Severity | Checks |
|---|---|
| **blocking** | CHK-01…CHK-07, CHK-11, CHK-12, CHK-13, CHK-15, CHK-16…CHK-21, CHK-24 (announcement half) |
| **banded** | CHK-08 — advisory 1,500–4,999 tok; blocking ≥ 5,000; forced decomposition ≥ 6,000 |
| **blocking on mismatch** | CHK-10 |
| **advisory** | CHK-09, CHK-14, CHK-22, CHK-23, CHK-24 (wait-rule half), CHK-25 |

**Failure of any blocking check halts emission.** Advisory failures are reported and do
not halt.

### Verdict vocabulary

`pass` | `FAIL` | `error`. Use `error` when the check could not be executed, with the
reason in the detail column; `error` on a blocking check is treated as blocking.

Severity is fixed by this file. A consumer **never re-decides** severity — it restates
what is written here.

---

## Checks

### CHK-01 — botIntents[].IntentID resolves

- **Verifies:** every `botIntents[]` entry points at an intent that exists.
- **Source:** Doc 1 §15.4 item 1
- **Severity:** `blocking`
- **On failure route to:** **Skill 1 patch mode** — likely a structural error (intent deleted but reference not cleaned up).
- **Procedure:** Build the set of `intents[].IntentId` values; for each `botIntents[i].IntentID`, verify membership.

### CHK-02 — intentRelations[] resolves (both endpoints)

- **Verifies:** every transition's origin and target intent exist.
- **Source:** Doc 1 §15.4 item 2
- **Severity:** `blocking`
- **On failure route to:** **Skill 1 patch mode** — likely a structural error (intent deleted but reference not cleaned up).
- **Procedure:** Same set as CHK-01; verify membership for both `OriginIntentID` and `NextIntentID`. `IntentRelatedID` is not checked separately (it's a unique row PK from the `-2000` placeholder range per §4.1; verified by the placeholder allocator).

### CHK-03 — apiSilenceRelations[] resolves (both endpoints)

- **Verifies:** every RT=2 API-silence registry row points at intents that exist.
- **Source:** Doc 1 §15.4 item 3
- **Severity:** `blocking`
- **On failure route to:** **Skill 1 patch mode** — likely a structural error (intent deleted but reference not cleaned up).
- **Procedure:** Same set as CHK-01; verify membership for `OriginIntentID` and `ApiSilenceIntentID`.

> **Coverage note.** A `fallback intent:` naming an intent that does not exist in section 4
> surfaces here, not at CHK-05: Skill 3 resolves the inline `intent` and
> `ApiSilenceIntentID` from the same spec field, so they are equal by construction even
> when both carry the `-999` sentinel. CHK-05 detects emission drift; CHK-03 detects a bad
> identifier.

### CHK-04 — intents[].IntentCategoryId resolves

- **Verifies:** every intent's category exists in `intentCategories[]`.
- **Source:** Doc 1 §15.4 item 4
- **Severity:** `blocking`
- **On failure route to:** **Skill 1 patch mode** — should never happen in v1 (single hardcoded category); if it does, either Skill 1 has a bug or the spec was hand-edited inconsistently.
- **Procedure:** Every `intents[].IntentCategoryId` matches an `intentCategories[].IntentCategoryId`. v1 has a single category (`-3`); check is trivial but explicit.

### CHK-05 — RT=2 pairing and inline failover

- **Verifies:** every RT=2 intent has a registry pairing row and a usable inline failover target.
- **Source:** Doc 1 §15.4 item 5 / Doc 1 §11.2
- **Severity:** `blocking`
- **On failure route to:** **Skill 1 patch mode** — RT=2 structural authoring incomplete.
- **Procedure:** Every intent with `IntentResponces.ResponseTypeId = 2` has (a) a corresponding `apiSilenceRelations[]` entry where `OriginIntentID` matches the intent's `IntentId`, and (b) a `Configuration.api_silence_behaviour.intent` that is a present, non-null integer equal to that entry's `ApiSilenceIntentID`. Walk RT=2 intents; for each, verify the row exists AND the inline `intent` failover key is present and matches `ApiSilenceIntentID`. A missing/null/string `intent` is a blocking failure — the intent has no failover.

### CHK-06 — Configuration deep equality

- **Verifies:** the RT=2 registry copy of `Configuration` has not drifted from the intent's own.
- **Source:** Doc 1 §15.4 item 6
- **Severity:** `blocking`
- **On failure route to:** **Skill 3 internal bug** — Skill 3 emits both from the same source; a mismatch means an emission bug. Report and halt; user files a skill-level issue.
- **Procedure:** For each RT=2 intent, the **full content** of `IntentResponces.Configuration` equals the corresponding `apiSilenceRelations[].Configuration` content. Deep equality across every key in the parent intent's Configuration: `url`, `method`, `headers`, `body` (if any), `fail_output`, `announcement`, `function_output`, `response_success`, `intentInstructions`, `intentLoadingAnnouncement`, AND the nested `api_silence_behaviour` sub-object (all six keys: the failover `intent` plus `silence_loops`, `silence_duration`, `silence_sentence`, `silence_instructions`, `silence_ending_sentence`).

### CHK-07 — Mustache resolvability

- **Verifies:** every `{{...}}` reference resolves against a declared inventory and is not read before it is written.
- **Source:** Doc 1 §15.4 item 7 / §14.3.5 / FP-11
- **Severity:** `blocking`
- **On failure route to:** **Skill 1 patch mode** if the missing variable should exist (e.g., add to 4.5.1 or 4.5.4), OR **Skill 2 reactivation** if the reference is wrong (e.g., typo in `validationPrompt`). The error message identifies the field and suggests both paths.
- **Procedure:** Every Mustache reference (in any text field across the assembled structure) resolves: (a) collected by the same intent that uses it, OR (b) in 4.5.1+4.5.2 whitelist (call-context or env), OR (c) in 4.5.3 collected by an intent that is upstream of the using intent in the transition graph, OR (d) in 4.5.4 declared for the same RT=2 intent or an upstream RT=2 intent, OR (e) in the 4.5.5 CustomData key list. Walk every text field; extract Mustache tokens; for each, classify against (a)-(e). Failure message appends: `CustomData keys are never invented — if {{<name>}} is a real per-call key, add it to spec 4.5.5 via Skill 1 patch mode.`

**Dotted-path validation depth:**

| Mustache shape | How resolution works |
|---|---|
| `{{slot_name}}` | Match against 4.5.1, 4.5.2, or 4.5.3. For 4.5.3 (slot variables), the slot must be collected by the same intent OR by an intent upstream in the transition graph. Cousin intents (no path either way) are violations. |
| `{{response.foo.bar}}` or `{{available_slots.N.field}}` | Match against 4.5.4 dotted-path declarations. The owning RT=2 intent must be the using intent itself OR an upstream RT=2 intent in the transition graph. Downstream or cousin = violation. |
| `{{ENV.SOMETHING}}` | Match against 4.5.2. |

**Upstream determination (v1 simplification per Conv 4 decision):** intent A is upstream of
intent B if there is a path A → ... → B in the transition graph (`intentRelations[]`).
Cousins (no path either direction) and downstream intents (path B → ... → A) are not
upstream. This check uses simple reachability, not full dataflow analysis. False negatives
are possible (a runtime path may exist that the static graph doesn't capture); false
positives are unlikely.

### CHK-08 — Assembled-prompt token budget

- **Verifies:** the assembled systemInstruction-equivalent text stays inside the doctrine's size bands.
- **Source:** Compass rule 1 (`voice-prompt-doctrine.md`)
- **Severity:** **banded** — advisory 1,500–4,999; blocking ≥ 5,000; forced decomposition ≥ 6,000
- **Model gating:** fires only on `models/gemini-3.1-flash-live-preview`
- **On failure route to:** **Skill 1 patch mode** to trim bot-level prompts, OR **Skill 2 reactivation** to trim per-intent `validationPrompt` and post-exec `intentInstructions`. Above 4,000 tok, also recommend splitting into orchestrator + specialist bots.
- **Procedure:** Estimated token count of the assembled systemInstruction-equivalent text (bot-level prompts + per-intent validationPrompt + per-intent post-exec intentInstructions, excluding openingAnnouncement) is below the doctrine thresholds. Banner-report the count and band. Halt on ≥ 5,000.

**Token estimate method** — apply the char-based estimate from
`voice-prompt-doctrine.md` §2:

1. Concatenate, in this order, the text content of: `prompts.persona` + `prompts.voiceInstructions` (only if section 1's voice channel is active) + `prompts.chatInstructions` (only if chat channel is active) + `prompts.intentInstructions` (bot-level) + for each intent in section 4 order: that intent's `validationPrompt` + that intent's post-execution `intentInstructions`. **Exclude** `prompts.openingAnnouncement` (platform-rendered per Compass §6).
2. Count characters per class: Latin/ASCII/digit/punctuation at 1/4 token; Hebrew/Arabic/CJK at 1/1.5 token; whitespace at 1/4 token.
3. Sum and round up. The result has ±15% accuracy.

**Thresholds** (enforcement policy — deliberately above the Compass §4 degradation point;
see `voice-prompt-doctrine.md` rule 1 enforcement note and §4):

- < 1,500 tok: no banner entry.
- 1,500 – 4,999 tok: advisory — emit banner line `# - Token estimate: <N> tok (advisory threshold 1,500-4,999; expect noticeable barge-in lag and instruction-drop risk above ~2,500 per Compass §4). See references/voice-prompt-doctrine.md rule 1.`
- 5,000 – 5,999 tok: blocking — halt assembly. The structured error includes:
  ```
  CHK-08: Assembled-prompt token budget (Compass rule 1)
    Violation: estimated <N> tok exceeds the 5,000 enforcement ceiling
    Route to: Skill 1 patch mode — trim prompts.persona / voiceInstructions / intentInstructions, OR split this bot into orchestrator + specialist bots.
    Suggested fix: review per-intent validationPrompt for redundant guidance duplicated across persona and voiceInstructions; remove duplicates from the per-intent fields.
  ```
- ≥ 6,000 tok: blocking — same halt, but the error additionally **mandates decomposition**:
  ```
  CHK-08: Assembled-prompt token budget (Compass rule 1)
    Violation: estimated <N> tok exceeds the 6,000 decomposition ceiling — trimming alone will not reach budget.
    Route to: Skill 1 patch mode — split this bot into an orchestrator + specialist bots (Compass §4). Trimming prompt text will not be sufficient at this size.
  ```

### CHK-09 — Session-resumption ceiling

- **Verifies:** a bot declaring cross-session continuity stays under the resumption handle's known ceiling.
- **Source:** Compass rule 2
- **Severity:** `advisory`
- **Model gating:** same as CHK-08
- **On failure route to:** Informational — no route. The user either drops the cross-session continuity requirement or accepts the known limitation per Compass §1 cookbook #1197 Issue 11.
- **Procedure:** Fires only when spec section 1 (or an extension subsection) declares `**Cross-session continuity:** required`. If the field is absent or `**Cross-session continuity:** not required` (default for v1 specs): silently skip. When it fires: reuse the same char-based estimate as CHK-08 and compare against 200 tok.
  - < 200 tok: no banner entry.
  - ≥ 200 tok: advisory — banner line `# - Session-resumption ceiling (Compass rule 2): assembled prompt is <N> tok; sessionResumption.handle is known to silently break above 200 tok on Gemini Live 3.1 native-audio. Mitigation: stateless prompt + per-session summary injection (out of scope for v1 bot-builder).`

### CHK-10 — Model-config doctrine

- **Verifies:** no dropped generation-config field has been re-added to the lean payload.
- **Source:** Compass rule 12 (v1.5.0 inversion)
- **Severity:** **blocking on mismatch**
- **Model gating:** same as CHK-08
- **On failure route to:** **Skill 1 patch mode** — model config is set in spec section 1. Skill 1 needs to update the AI Model Config selection or apply per-field corrections (the typical fix: drop `affectiveDialog`/`proactiveAudio` overrides; reset `thinkingLevel` to minimal).
- **Procedure:** Validate that the version-level `AIModelConfig.created` does **NOT** contain any of the dropped fields (`temperature`, `topP`, `topK`, `responseModalities`, `proactivity`, `thinkingConfig`, `systemInstruction`, `tools`, `affectiveDialog`, `proactiveAudio`, `thinkingConfig.thinkingLevel != "minimal"`). The lean payload from §4.2.4 has none of these by construction; this check catches future regressions. Inspect the assembled in-memory `ActiveVersionInfo.AIModelConfig.created`. The expected keys are exactly `realtimeInputConfig` and (when voice active) `generationConfig.speechConfig.voiceConfig.prebuiltVoiceConfig.voiceName`. Any other key under `generationConfig` is a failure.

| Failure | Expected | Failure message |
|---|---|---|
| `temperature` present in `generationConfig` | absent | `generationConfig.temperature is present (value: <actual>); per Compass §1 + v1.5.0 lean payload rule, this should be absent (platform server-side default). Route to: code fix in Skill 3 emission logic — production export of Gemini 3.1 Voice driven does not carry this field.` |
| `topP` / `topK` present in `generationConfig` | absent | `generationConfig.<field> is present; v1.5.0 lean payload omits.` |
| `responseModalities` present in `generationConfig` | absent | `generationConfig.responseModalities is present; v1.5.0 lean payload omits (platform infers from channel).` |
| `proactivity` / `proactiveAudio` present in `generationConfig` | absent | `generationConfig.<field> is present; per Compass §1, this is unsupported in 3.1 and a regression risk. Route to Skill 1 patch mode or fix the spec.` |
| `thinkingConfig` present with any keys | absent or `{}` | `generationConfig.thinkingConfig has content; v1.5.0 lean payload uses platform default (minimal).` |
| `affectiveDialog` present in `generationConfig` | absent | `generationConfig.affectiveDialog is present; per Compass §1, unsupported in 3.1.` |
| `systemInstruction` present | absent | `created.systemInstruction is present; v1.5.0 emits the systemInstruction-equivalent content via `prompts` bundle only.` |
| `tools: [...]` present in `created` | absent | `created.tools is present; v1.5.0 emits tools via `IntentToolName` per intent, not here.` |

The blocking error report aggregates all CHK-10 sub-failures into a single entry.

### CHK-11 — Global registered as type-2

- **Verifies:** every intent whose role is `global` is actually reachable from anywhere.
- **Source:** botIntents-role integrity C-a
- **Severity:** `blocking`
- **On failure route to:** **Skill 1 patch mode** — role/registry inconsistency; re-run role classification (§3.6).
- **Procedure:** Build the set of `global` identifiers from section 4; for each, verify a `botIntents[]` entry exists with that `IntentId` and `BotIntentTypeID = 2`.

### CHK-12 — No chained intent in botIntents

- **Verifies:** chained intents are not registered as top-level triggers.
- **Source:** botIntents-role integrity C-c
- **Severity:** `blocking`
- **On failure route to:** **Skill 1 patch mode** — an intent marked `chained` was registered; fix the role or the membership.
- **Procedure:** For each `botIntents[]` entry, verify its source intent's role is `entry` or `global`.

### CHK-13 — Start point exists

- **Verifies:** the bot has at least one top-level trigger.
- **Source:** botIntents-role integrity C-d
- **Severity:** `blocking`
- **On failure route to:** **Skill 1 patch mode** — designate at least one `entry` intent (or a `global`).
- **Procedure:** Assert `botIntents[]` is non-empty and contains ≥1 type-1 or type-2 entry.

### CHK-14 — Section-4.6 catalog intents resolve

- **Verifies:** referenced platform catalog intents were actually injected.
- **Source:** Doc 1 §15.4 (catalog extension)
- **Severity:** `advisory`
- **On failure route to:** **Skill 1 patch mode** or **manual fix** — verify the catalog `IntentId` in section 4.6 is correct; if referencing a non-existent catalog intent, either remove the reference or add the catalog definition.
- **Procedure:** Every catalog intent referenced by section 3 (`silence_behaviour.intent`) or any structural failover field is present in the emitted `intents[]` by real `IntentId`, AND its `IntentCategoryId` is present in `intentCategories[]`. Walk every failover `intent` field that resolves to a catalog IntentId; verify presence in `intents[]` and `intentCategories[]` by real ID.

### CHK-15 — No duplicate global intents by tool name

- **Verifies:** a tool name is registered as a global at most once, so the UI shows no duplicates.
- **Source:** botIntents-role integrity C-e
- **Severity:** `blocking`
- **On failure route to:** **Skill 1 patch mode** — review section 4 roles. Mark the legacy intent as role=`chained` (keep it in `intents[]`, unregister from `botIntents[]`), leaving only the current intent as role=`global`. Alternatively, delete the old intent from section 4 if it's no longer referenced.
- **Procedure:** For each unique `IntentToolName` value across section 4, at most **one** intent with that tool name may have role `global` (registered in `botIntents[]` with `BotIntentTypeID = 2`). Build a map `{ IntentToolName → [intent1, intent2, ...] }` for all intents with role `global`. For each tool name with count > 1, it's a blocking failure listing the duplicate intent identifiers.

**Background.** When a bot is rebuilt or updated, new intents are sometimes created while
old ones remain in the `intents[]` array (orphaned but not registered in `botIntents[]`).
The UI displays only intents registered in `botIntents[]`. If two intents with the same
`IntentToolName` are both registered as type-2, the UI shows both as separate entries,
creating a perceived duplicate and routing ambiguity.

**Structured error format:**

```
CHK-15: No duplicate global intents by tool name (C-e)
  Violation: tool name 'transfer_to_human' registered as global (type-2) in 2 intents:
    - Intent identifier: transfer_to_human (IntentId -10)
    - Intent identifier: transfer_to_human_legacy (IntentId -11)

  At most one intent per tool name may have role=global (type-2 in botIntents).

  Root cause: when a bot is rebuilt, new intents are created but old ones remain orphaned
  in intents[]. If BOTH the new and old are marked global, they both register and appear
  as duplicates in the UI.

  Solution: Only the NEW transfer intent should have role=global. The old one should be
  marked role=chained (or role=entry if it's a starting point), leaving it in intents[]
  but unregistered in botIntents[].

  Route to: Skill 1 patch mode — review intent roles. Mark the legacy/old transfer intent
  as role=chained, keeping only the current transfer intent as global. Or remove the old
  intent from section 4 entirely if it's no longer used.
```

### CHK-16 — validationPrompt speech-free

- **Verifies:** no `validationPrompt` contains content written to be spoken.
- **Source:** FP-5
- **Severity:** `blocking`
- **On failure route to:** **Skill 2 reactivation** — the intent's validationPrompt must be rewritten as a capture mapping (FP-5, style-guide patterns C1–C5); the script/question moves to `announcement` or an FP-4 quoted instruction line; a turn-taking guard moves to persona (Skill 1 patch).
- **Procedure:** No `IntentConfig.prompts.validationPrompt` contains imperative speech content — scripts, questions to the caller, greetings, or turn-taking guards. The Intent Agent is the only consumer; anything written to be spoken there is never spoken. Per validationPrompt, per line: (i) imperative-speech regex `(?im)^\s*\W*(say|ask|tell|greet|announce|read (back|aloud)|repeat back)\b` and Hebrew imperatives `(אמרי|אמור|שאלי|שאל|חזרי|הקריאי|קראי|ברכי)`; (ii) a question mark inside a quoted string or ending a non-quoted line; (iii) guard/gate headers (`(?im)^(TURN.?TAKING|GATE\b)`) or IRON-RULE blocks containing wait/turn phrasing; (iv) greeting tokens (`שלום`, `hello`, `hi there`) outside a saved-value context. **Whitelist:** quoted strings on lines that also contain save/set/store/"exactly" language plus a parameter name owned by THIS intent (protects pinned outcome values and `"true"`/`"false"` literals).

### CHK-17 — RT=3 intentLoadingAnnouncement present

- **Verifies:** every RT=3 intent has a real latency filler, not the default SAY-directive bug.
- **Source:** FP-7
- **Severity:** `blocking`
- **On failure route to:** **Skill 2 reactivation** — author the FP-7 filler for the flagged intent(s).
- **Procedure:** Every RT=3 intent's `Configuration.intentLoadingAnnouncement` is present, non-empty, not whitespace-only, and not the literal `"."`. Walk RT=3 intents; test the field.

### CHK-18 — Own-parameter references

- **Verifies:** no intent references a slot it does not own.
- **Source:** FP-8
- **Severity:** `blocking`
- **On failure route to:** **Skill 1 patch mode** if the parameter should move to the flagged intent, OR **Skill 2 reactivation** to remove the reference (the outcome slot lives on its owning terminal per FP-8). The error offers both paths.
- **Procedure:** No intent's `validationPrompt`, `Configuration.announcement`, or `Configuration.intentInstructions` references a parameter name that belongs to a DIFFERENT intent — an intent can only set its own `IntentParameters`; foreign references (e.g., a gate "setting" a terminal's status slot) are un-executable. Build the bot-wide set of all `IntentParameters[].Name` values with their owning IntentIds. For each intent, scan the three fields for word-boundary matches of any slot name; any match whose owner is a different intent fails, reporting intent, field, matched name, and the owning intent.

### CHK-19 — No duplicate speak-obligation

- **Verifies:** no sentence is mandated as speech in two places.
- **Source:** FP-6
- **Severity:** `blocking`
- **On failure route to:** **Skill 2 reactivation** for intent-field duplicates; **Skill 1 patch mode** when one site is persona / opening instructions / openingAnnouncement. Keep the sentence in exactly one field.
- **Procedure:** No normalized speech obligation appears in two or more obligation sites — the diagnosed mechanism of double-speech bugs (e.g., a farewell in both a terminal's announcement and another field). Extract mandated-speech strings: sentences of every `announcement`, every `intentLoadingAnnouncement`, sentences of `prompts.openingAnnouncement`, and FP-4 quoted lines (`: "<...>"`) inside per-intent `Configuration.intentInstructions`, `prompts.intentInstructions`, and `prompts.persona`. **Skip any line that is wholly wrapped in parentheses** — a parenthetical is context by convention, not a speech obligation (see the note below). Normalize each remaining string (trim; strip punctuation and niqqud; collapse whitespace). Any normalized string ≥ 12 characters appearing in 2+ sites fails, reporting both JSON paths.

> **Why parentheticals are excluded.** FP-4's convention is semantic —
> `<instruction verb> : "<verbatim line>"` — but this extraction is syntactic, so it cannot
> distinguish "say this" from "this was already said". A parenthetical restating the opening
> announcement is the second kind, and counting it as an obligation made this check block a
> bot authored exactly as Skill 1's canonical template documented (finding N1).
>
> The narrower fix was chosen deliberately. Allow-listing instruction verbs before the colon
> would match FP-4's semantics more closely, but it needs a bilingual verb list and trades a
> known false positive for unknown **false negatives** — and double-speech is precisely what
> FP-6 exists to catch. Honouring the existing parentheses-mean-context convention costs no
> sensitivity on instruction lines.
>
> Regression-tested by `examples/test-chk19-regression.py`, whose third case asserts a real
> duplicate still fails. If that case ever goes quiet, this exclusion has gone too far.

### CHK-20 — Terminal shape

- **Verifies:** RT=1 terminals are one-hop, own their outcome slot, and carry no farewell.
- **Source:** FP-8 (announcement clause added v1.14.0)
- **Severity:** `blocking`
- **On failure route to:** **Skill 1 patch mode** — per-outcome terminal restructure (add the outcome slot / remove the terminal-origin relation / merge the finalize→end_call chain); **Skill 2 reactivation** when only the validationPrompt's value-mode implementation is off.
- **Procedure:** Every RT=1 terminal: has `Configuration.layer` (0 allowed — banner-noted); carries **NO `Configuration.announcement` key** (the farewell lives in the predecessor's `intentInstructions`; a spec-supplied RT=1 announcement is a failure, not an emission choice); when the spec declares `**Terminal outcome:**`, the named slot exists in that intent's `IntentParameters` AND the validationPrompt implements the declared value mode (fixed mode ⇒ the exact pinned string appears verbatim; captured/dynamic ⇒ a save/compose instruction naming the slot exists); and NO `intentRelations[]` row has an RT=1 intent as `OriginIntentID` (no terminal→anything chains, incl. finalize→end_call). Walk RT=1 intents against the spec section-4/5 fields and the relations array; assert the `announcement` key is absent from every RT=1 `Configuration`.

### CHK-21 — ParameterType dictionary byte-match

- **Verifies:** emitted `ParameterType` blocks match the system dictionary exactly.
- **Source:** Doc 1 §12 / Skill 3 §4.3.2
- **Severity:** `blocking`
- **On failure route to:** **Skill 3 internal bug** — Skill 3 emits these from its own §4.3.2 dictionary; a mismatch means emission drift. Report and halt; user files a skill-level issue.
- **Procedure:** Every emitted `ParameterType` object on bot-own intents matches the §4.3.2 system-dictionary table field-for-field (Name, Description, ParameterTypeId, ValidationPattern, IsCustomValidationAllowed, IsActive, CreatedBy, CreatedDate, ModifiedBy, ModifiedDate). System dictionary rows are copied verbatim, never re-authored. Carve-outs: §4.6 catalog-intent blocks are verbatim pass-through (excluded); unverified PHONE downgrades to a banner note.

### CHK-22 — No authored edges into type-2 globals

- **Verifies:** the graph carries no redundant edges into globals.
- **Source:** FP-9
- **Severity:** `advisory`
- **On failure route to:** Informational — recommend **Skill 1 patch mode** to drop the redundant relation; the global is reachable from anywhere by construction.
- **Procedure:** `intentRelations[]` rows whose `NextIntentID` is a type-2 global are legal but usually redundant — globals are reachable from anywhere by construction, and extra edges enlarge the tool-routing surface. List any relation targeting a botIntents type-2 IntentId; banner line recommending removal via Skill 1 patch mode.

### CHK-23 — Off-topic global present

- **Verifies:** the bot has an off-topic escape hatch and a persona rule that routes to it.
- **Source:** FP-6 (v1.14.0)
- **Severity:** `advisory`
- **On failure route to:** Recommend **Skill 1 patch mode** — run the §3.2.5 off-topic elicitation (outcome / loops / wording) to add the dedicated off-topic global and/or inject the persona rule.
- **Procedure:** Every bot should carry the mandatory off-topic handling pair: (a) at least one RT=1 intent registered type-2 in `botIntents[]` whose Description/Name marks it as the off-topic/unrelated-topic terminal, AND (b) a `prompts.persona` off-topic section (forbid + deflect + N-loop ending) that references that intent's Description. Missing either half means the bot has no escape hatch when a caller won't return to the flow. Scan `botIntents[]` type-2 entries' source intents (RT=1) for off-topic semantics in Description/Name (e.g., "unrelated", "לא קשור"); scan `prompts.persona` for an off-topic rule and match its routing target against that Description. On miss: banner line routing to Skill 1 patch mode (§3.2.5 elicitation).

### CHK-24 — Turn-yield announcement gating

- **Verifies:** an intent that asks nothing does not stall the call waiting for an answer.
- **Source:** FP-3 (v1.17.0 turn-yield)
- **Severity:** `blocking` (announcement half) · `advisory` (wait-rule half)
- **On failure route to:** **Skill 2 reactivation** — empty the flagged `announcement`; move any line the caller must still hear to an FP-4 quoted line in the intent's `intentInstructions` immediately before the forward instruction, and replace any wait rule with the immediate-forward instruction.
- **Procedure:** A non-empty `announcement` makes the bot yield the turn and WAIT for a caller answer (confirmed live). Every RT=2/RT=3 intent whose spec section-4 `**Asks next:**` is `[none]` must have `Configuration.announcement` equal to the empty string — a non-empty value there stalls the call into the silence loop. RT=1 is covered by CHK-20 (no announcement key at all); RT=4 is exempt (pre-dial speech, platform dials immediately after). Walk RT=2/RT=3 intents; read section-4 `**Asks next:**`; when `[none]`, assert `announcement === ""` (blocking on failure, reporting intent + the offending text). **Advisory scan** on the same intents: regex `(?i)(stop and wait|wait for (the customer|their|a) (explicit )?(answer|response))` or Hebrew `המתן לתשוב` inside `Configuration.intentInstructions` → banner line routing to Skill 2 reactivation.

### CHK-25 — Persona FK sanity

- **Verifies:** `ActiveVersionInfo.PersonaID` is present and names a `Persona` row that will exist on the target account.
- **Source:** `voicebot-json-contract.md` R7/R11 (functional v1.18.0)
- **Severity:** `advisory`
- **On failure route to:** Informational — banner note asking the operator to confirm the `Persona` row exists on the target account before import (FK). **Not user-actionable during authoring in v1** (Skill 1 has no persona-selection field yet); relevant once that feature ships. Do not route to a skill.
- **Procedure:** Assert `ActiveVersionInfo.PersonaID` is present and non-null, and that its value is in the known shared whitelist `{3}` (`TTSScriptReader`, `AccountId=0`). v1 always emits `3` by construction, so this check is **trivial today** — the same "trivial but explicit" rationale as CHK-04. It exists so that a later spec-level persona-selection feature cannot introduce an unverified FK silently. If the value is absent or null: report `FAIL` (advisory) — the stored procedure would fall back to the first `Persona` row with `AccountId=0`, and if that row is missing on the target server, step 3 fails and produces exactly the "Bot with intents but no BotVersion" symptom the contract exists to prevent. If the value is present but outside the whitelist: report `FAIL` (advisory) with a banner line asking the operator to confirm that row exists on the target account.

---

## Output contract

**Both** execution paths — the `spec-verifier` subagent and Skill 3's inline path — emit
exactly this format. This is what makes the two paths mechanically comparable.

### Report structure (exactly these blocks, in order)

```markdown
## Verification Report
Spec: <absolute path or "in-conversation">
Procedure version: <plugin version from plugin.json>
Executed: <delegated | inline>

### Verdicts
| CHK | Severity | Verdict | Detail |
|-----|----------|---------|--------|
| CHK-01 | blocking | pass | — |
| CHK-02 | blocking | FAIL | <one-line: what, where in the spec (section/intent id)> |
| …all 25 rows, in order, no omissions… |

### Blocking failures
<numbered list of every blocking FAIL: CHK id, spec location, one-line description.
 If none: "None.">

### Routing recommendations
<one line per FAIL: "CHK-NN → Skill 1|Skill 2 — <what the responsible skill
 must change>". Advisory failures included, marked "(advisory)".
 If none: "None.">

### Drift notes
<discrepancies between spec section 6 and regenerated views, per the
 v1.17.0 drift semantics. If none: "None.">
```

### Rules

- **All 25 rows, always, in CHK order.** A skipped check is itself a malformed report.
  A model- or baseline-gated check that did not fire is still a row, with its verdict
  recorded as `error` (unrunnable) or noted as skipped in the detail column.
- Verdict vocabulary: `pass` | `FAIL` | `error` (check could not be executed — detail says why). `error` on a blocking check is treated as blocking.
- Severity column restates this file's assignment — the consumer never re-decides severity.
- Detail lines are one line each. The report is a verdict artifact, not an essay; explanation depth belongs in the routing recommendation.
- No content outside the four blocks. No preamble, no summary paragraph, no advice beyond routing lines.
- A model-gated check that skipped (CHK-08/09/10 on a non-Gemini-3.1 model) reports verdict `pass` with detail `skipped — model gating`.

### Structured-error form (unrunnable verification)

If the spec path is missing/unreadable, or this procedure file cannot be loaded, emit
instead:

```markdown
## Verification Report — ERROR
Spec: <path as given>
Executed: <delegated | inline>
Error: <one line: what could not be done>
Action: <one line: what the caller should fix>
```

The subagent never hunts for alternative files; the inline path may ask the user (it is in
the main conversation) but must not guess.

### Consumer-side validity check

A delegated report is valid iff: the `## Verification Report` header is present, the
Verdicts table contains exactly CHK-01…CHK-25 in order, and every verdict is in the
allowed vocabulary. Anything else → discard, log one line to the user (`verifier report
malformed — running checks inline`), and fall back to the inline path.
