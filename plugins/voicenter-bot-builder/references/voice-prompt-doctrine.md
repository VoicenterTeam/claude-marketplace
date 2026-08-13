# Voice prompt doctrine — Voicenter bot-builder reference

**Source:** *Voice agent prompts on Gemini Live 3.1: an engineering guideline* (the Compass doc; available in the user's working materials, not embedded here). This file distills the Compass into 13 enforceable rules tied to the `voicenter-bot-builder` pipeline.

**Read this when:** loaded by Skill 1, Skill 2, and Skill 3 at invocation per their §1 required-reading tables.

**Operating principle:** the prompt is conversational policy and nothing else. Each rule below has a single enforcement skill, a severity, and a model gating clause. Rules that the platform can't realistically enforce in v1 (PII redaction, prompt-injection classifier, rate limiting) are out of scope — see §3 boundary table.

---

## Table of contents

- [1. Rule catalog](#1-rule-catalog)
  - [Rule 1 — Assembled-prompt token budget](#rule-1-assembled-prompt-token-budget)
  - [Rule 2 — Session-resumption ceiling](#rule-2-session-resumption-ceiling)
  - [Rule 3 — English operational, target-language utterances](#rule-3-english-operational-target-language-utterances)
  - [Rule 4 — Intent description in English](#rule-4-intent-description-in-english)
  - [Rule 5 — Recency-slot language-lock guardrail](#rule-5-recency-slot-language-lock-guardrail)
  - [Rule 6 — Contradictory pacing/length](#rule-6-contradictory-pacinglength)
  - [Rule 7 — Generic-policy boilerplate](#rule-7-generic-policy-boilerplate)
  - [Rule 8 — TTS-safe formatting in voice output](#rule-8-tts-safe-formatting-in-voice-output)
  - [Rule 9 — Date math in prompt](#rule-9-date-math-in-prompt)
  - [Rule 10 — Few-shot transcript example cap](#rule-10-few-shot-transcript-example-cap)
  - [Rule 11 — Hebrew-utterance isolation](#rule-11-hebrew-utterance-isolation)
  - [Rule 12 — Model-config doctrine (Gemini Live 3.1)](#rule-12-model-config-doctrine-gemini-live-31)
  - [Rule 13 — Doctrine banner sentinels](#rule-13-doctrine-banner-sentinels)
- [2. Token-counting method (v1 — char-based, ±15% accuracy)](#2-token-counting-method-v1-char-based-15-accuracy)
- [3. In-prompt vs platform boundary table](#3-in-prompt-vs-platform-boundary-table)
- [4. Token budget table](#4-token-budget-table)
- [5. The 10 operating rules (Compass §8) — closing checklist](#5-the-10-operating-rules-compass-8-closing-checklist)

---

## 1. Rule catalog

Severity legend: **blocking** = skill refuses to proceed until resolved; **advisory** = skill warns, records resolution in spec section 7.3, continues; **structural** = auto-applied (no user prompt).

Gating legend: `[GL3.1]` = applies only when spec section 1 declares `AIModelConfigID=139` (Gemini Live 3.1, voice driven) or `AIModelConfigID=142` (Gemini 3.1 - LLM driven — same `models/gemini-3.1-flash-live-preview` runtime, so the same limits apply); `[voice]` = applies when section 1 declares an active voice channel; `[any voice]` = applies to any platform but most impactful when a voice channel is active (the rule is universal but framed against voice-bot workflows); `[any]` = universal.

### Rule 1 — Assembled-prompt token budget

**Source:** Compass §4 budget table, §8 operating rule 2.
**Applies to:** assembled `systemInstruction` content (= `prompts.persona` + `prompts.voiceInstructions` + `prompts.intentInstructions` + sum of every intent's `validationPrompt` + sum of every intent's post-execution `intentInstructions`).
**Owning skill:** Skill 3 — enforced at assembly time by CHK-08; see [`verification-procedure.md`](verification-procedure.md).
**Severity:** advisory at 1,500–4,999 tok; **blocking** at ≥ 5,000 tok (forced decomposition at ≥ 6,000 tok).
**Gating:** `[GL3.1]`.
**Why:** Gemini Live 3.1 Flash does not support context caching — the assembled prompt is paid in full on every session start, and every subsequent turn re-attends over it. Above 2,500 tok, first-turn TTFA materially degrades and instruction-drop risk rises (Compass §1, §4). **Enforcement note:** the pipeline gate is deliberately set *higher* than the Compass degradation point — advisory through 4,999, blocking only at ≥ 5,000 — an operator decision that accepts the documented 2,500–4,999 degradation as advisory-only to give authors working room. The Compass measurement (degradation begins ~2,500) is unchanged; only the pipeline's block threshold is relaxed. See §4.
**Fix recipe (advisory):** offer to (a) split bot-level `prompts.intentInstructions` across orchestrator + specialist bots, (b) trim duplicate guidance across `persona` / `voiceInstructions` / per-intent `validationPrompt`, (c) move policy that's not call-wide into the relevant intent.
**Fix recipe (blocking):** halt assembly with the same advice plus a routing recommendation to Skill 1 patch mode.

### Rule 2 — Session-resumption ceiling

**Source:** Compass §1 (cookbook #1197 Issue 11), §4.
**Applies to:** same assembled systemInstruction as rule 1, but the threshold is 200 tok.
**Owning skill:** Skill 3 — enforced at assembly time by CHK-09; see [`verification-procedure.md`](verification-procedure.md). Fires only when the spec declares cross-session continuity is required.
**Severity:** advisory.
**Gating:** `[GL3.1]`.
**Why:** above ~200 tok, `sessionResumption.handle` silently breaks on Gemini Live 3.1 native-audio sessions. The only mitigation is a stateless prompt + injected per-session summary.
**Fix recipe:** drop the cross-session continuity requirement, OR use a stateless prompt design with per-session summary injection (out of scope for the bot-builder; warn only).

### Rule 3 — English operational, target-language utterances

**Source:** Compass §4 (Hebrew tokenizes catastrophically, ~3× tax; "Token Tax" arXiv 2509.05486).
**Applies to:** `prompts.persona`, `prompts.voiceInstructions`, `prompts.intentInstructions` (bot-level) text body.
**Owning skill:** Skill 1 (§5 self-val check 11).
**Severity:** advisory; the skill offers an English rewrite as a user-confirmed action — never silently rewrites.
**Gating:** `[any voice]`; the rule is most impactful for non-English bots but the principle (English operational, target lang in quoted utterances) holds universally.
**Detection heuristic:** for each prompt field, count characters in non-Latin scripts (Hebrew U+0590-U+05FF, Arabic U+0600-U+06FF, CJK ranges). If ≥30% of the field's character count is non-Latin AND the bot's primary language is non-English: fire advisory.
**Fix recipe:** offer to rewrite operational prose in English while preserving Hebrew/target-language quoted utterances in their own lines or inside quote marks. User opts in; rewrite is shown for confirmation before applied. After the user confirms the English rewrite, run the rule 11 (Hebrew-utterance isolation) check on the rewritten field as a mirror — the rewrite may have left inline RTL content mixed with new English prose.

### Rule 4 — Intent description in English

**Source:** Compass §4 ("tool descriptions stay in English — function-calling layer is English-trained and Hebrew tool descriptions degrade selection accuracy").
**Applies to:** every section 4 intent's `Description` field.
**Owning skill:** Skill 1 (§5 self-val check 12).
**Severity:** advisory.
**Gating:** `[any voice]`.
**Detection heuristic:** same character-class scan as rule 3, applied to `Description` text only. Threshold ≥30% non-Latin chars.
**Fix recipe:** offer an English rewrite of the Description. Display name (Hebrew) stays as authored.

### Rule 5 — Recency-slot language-lock guardrail

**Source:** Compass §1 (cookbook #1197 false language switching on Hispanic-sounding names), §4 (recency slot per "Lost in the Middle" + "Found in the Middle").
**Applies to:** `prompts.intentInstructions` (bot-level — the field that anchors the recency slot when assembled).
**Owning skill:** Skill 1 (§5 self-val check 13).
**Severity:** advisory; user opt-in injection or relocation.
**Gating:** `[any voice; especially recommended for non-English]`.
**Detection method:** regex over `prompts.intentInstructions` text:
- Pattern A (positive match — rule satisfied): `(?i)(infer|switch|change).*(language|לשון|לעבור)` OR `(?i)(name|accent|tone).*(language|לשון)`.
- If Pattern A matches in the final third of the text (≥66% character offset): rule satisfied, no warning.
- If Pattern A matches earlier in text: warning — "the language-lock guardrail is present but not in the recency slot; move to end?"
- If Pattern A does not match at all: warning — "no language-lock guardrail detected; recommended to append a line equivalent to 'NEVER infer language from caller's name, accent, or tone.'"
**Fix recipe:** offer the standard line (or its Hebrew equivalent for Hebrew bots), with user confirmation before injection or move.

### Rule 6 — Contradictory pacing/length

**Source:** Compass §5 anti-pattern "Contradictory pacing/tone"; ConInstruct benchmark arXiv 2511.14342.
**Applies to:** combined text of `prompts.persona` + `prompts.voiceInstructions`.
**Owning skill:** Skill 1 (§5 self-val check 14).
**Severity:** advisory.
**Gating:** `[any voice]`.
**Detection method:** pattern-pair detection — if the combined text contains a tone descriptor matching `(?i)\b(warm|conversational|friendly|relaxed|easygoing|easy-going|patient)\b` AND a length constraint matching `(?i)\b(\d+|one|two)\s*(sentence|sentences|words|line|lines)\s*(max|maximum|or less|or fewer|at most)\b`: warn.
**Fix recipe:** advise picking one tone descriptor and explicit length bounds; do not auto-resolve.

### Rule 7 — Generic-policy boilerplate

**Source:** Compass §2 anti-list ("generic content-policy lists"), §5.
**Applies to:** `prompts.persona`, `prompts.voiceInstructions`, `prompts.intentInstructions` (bot-level), per-intent `validationPrompt` (Skill 2 also re-checks via rule 7 mirror; primary enforcement is Skill 1).
**Owning skill:** Skill 1 (§5 self-val check 15).
**Severity:** advisory; do not auto-remove.
**Gating:** `[any]`.
**Detection method:** case-insensitive substring match against the v1 stem list:
- `gdpr`, `hipaa`, `pii`, `personally identifiable`, `medical advice`, `legal advice`, `financial advice`, `we do not store`, `we do not retain`, `data retention`, `do not provide professional`.
**Fix recipe:** if the bot is a medical/legal/financial domain, the stems are domain-appropriate and the user confirms "keep it." If the bot is unrelated (e.g., pizza delivery), the stems are content-policy bloat — recommend removal. User decides.

### Rule 8 — TTS-safe formatting in voice output

**Source:** Compass §5 anti-pattern "Chat-agent boilerplate copied to voice"; §6 "Output rules" canonical pattern.
**Applies to (v1.13.0):** the SPOKEN fields — per-intent `announcement` (any RT), `intentLoadingAnnouncement`, `fail_output`, `function_output`, and the quoted spoken lines of post-execution `intentInstructions`. Per-intent `validationPrompt` is EXEMPT — it is consumed only by the Intent Agent and never vocalized (field-placement doctrine FP-5), and its capture-mapping form legitimately uses `*` bullets.
**Owning skill:** Skill 2 (iron rule wired into §4.3, §4.4 step phases).
**Severity:** **blocking** on markdown bullets/headers/URLs in voice-active intent fields; advisory on raw long digit runs (≥6 consecutive digits without a spell-out instruction nearby).
**Gating:** `[voice]`.
**Detection method:**
- Markdown: regex `(?m)^\s*[-*+]\s` (bullet), `(?m)^\s*#+\s` (header), `\[.*\]\(.*\)` (markdown link).
- URLs: regex `https?://\S+`.
- Raw long digit runs: regex `\d{6,}` AND no `digit by digit` / `ספרה ספרה` instruction within 100 characters.
**Fix recipe (markdown/URLs blocking):** require rewrite to natural-language prose before proceeding.
**Fix recipe (digit-run advisory):** suggest adding "spell digit-by-digit" or local-language equivalent ("ספרה ספרה" for Hebrew, etc.) instruction.

### Rule 9 — Date math in prompt

**Source:** Compass §2 anti-list "Date and time math"; §8 operating rule 8.
**Applies to:** per-intent `validationPrompt`.
**Owning skill:** Skill 2 (new iron rule wired into §4.2 step 2).
**Severity:** advisory.
**Gating:** `[any]`.
**Detection method:** pattern match against:
- `(?i)\bnot\s+(in\s+)?(the\s+)?future\b`
- `(?i)\b(year|שנה)\s*[≥>=]+\s*\d{4}\b`
- `(?i)\b(today|tomorrow|yesterday)\b` AND no surrounding `{{TimeNow}}` or equivalent variable reference.
**Fix recipe:** recommend pre-rendered `{{TimeNow}}`-derived variable injection. The advisory message points to spec section 4.5.1 (call-context variables) where the user can declare an additional pre-rendered date variable.

### Rule 10 — Few-shot transcript example cap

**Source:** Compass §4 "Examples vs rules" (English 80–200 tok per example; Hebrew 250–500 tok).
**Applies to:** per-intent `validationPrompt`.
**Owning skill:** Skill 2 (new iron rule wired into §4.2 step 2).
**Severity:** advisory; harsher language for non-English bots.
**Gating:** `[any voice]`.
**Detection method:** count occurrences of `(?im)^\s*(user|caller|פונה|לקוח)\s*:` followed by a line matching `(?im)^\s*(agent|bot|נציג|בוט)\s*:` inside any single `validationPrompt`. Threshold: more than 2 transcript pairs.
**Fix recipe:** recommend keeping the most calibration-relevant pair only, or moving examples to a per-intent reference doc out of the prompt.

### Rule 11 — Hebrew-utterance isolation

**Source:** Compass §4 "Sanity rule: never inject RTL Hebrew strings into the middle of an LTR English instruction line."
**Applies to:** per-intent `validationPrompt`, per-intent `announcement`, per-intent post-execution `intentInstructions`. Mirror runs on Skill 1 bot-level fields when the user accepted a rule-3 English rewrite.
**Owning skill:** Skill 2 (primary; new iron rule wired into §4.2/§4.3/§4.4). Skill 1 (mirror runs only on fields the user accepted an English rewrite for, in §5 check 11).
**Severity:** **blocking**.
**Gating:** `[any; bites Hebrew especially]`.
**Detection method:** regex `[֐-׿؀-ۿ一-鿿぀-ゟ゠-ヿ]+` inside a line whose remaining non-whitespace content is ≥50% ASCII alphanumerics. Detection per line; the line is the unit.
**Fix recipe:** require the user to either (a) move the Hebrew/target-language content onto its own line, (b) wrap it in quotes (`"שלום"` or `'שלום'`), or (c) rewrite the line. Block until resolved.

### Rule 12 — Model-config doctrine (Gemini Live 3.1)

**Source:** Compass §1 (3.1 regression list — synchronous tool calls only, no `affective_dialog`, no `proactive_audio`, default `thinkingLevel=minimal`); §7 reference Python config.
**Applies to:** assembled `AiModelConfig.created.generationConfig` and pinned model string.
**Owning skill:** Skill 3 — enforced at assembly time by CHK-10; see [`verification-procedure.md`](verification-procedure.md).
**Severity:** **blocking** on any mismatch.
**Gating:** `[GL3.1]`.
**Detection method:**
- `AiModelConfig.created.model` must equal `"models/gemini-3.1-flash-live-preview"`.
- `AiModelConfig.created.generationConfig.thinkingConfig.thinkingLevel` must equal `"minimal"` OR the key must be absent (defaults to minimal).
- `AiModelConfig.created.generationConfig.affectiveDialog` must be absent OR `false`.
- `AiModelConfig.created.generationConfig.proactiveAudio` must be absent OR `{}`. (The `proactivity` key may be present as an empty object `{}` — that is the v1 default; rule fires only on populated content.)
- `AiModelConfig.created.generationConfig.responseModalities` must contain `"AUDIO"` if section 1 declares an active voice channel.
**Fix recipe:** if any check fails, halt assembly with a routing recommendation to Skill 1 patch mode (model selection is a section 1 field).

### Rule 13 — Doctrine banner sentinels

**Source:** pipeline mechanic; extension of Skill 3 fail-loud sentinel pattern.
**Applies to:** advisory rules above (1, 2, 3, 4, 5, 6, 7, 9, 10) and rule 8's advisory digit-run sub-severity that fired and were not resolved by user opt-in.
**Owning skill:** Skill 3 (§7.2 banner emission).
**Severity:** structural (auto-applied; no user prompt).
**Gating:** `[any]`.
**Implementation:** the banner template adds a new section `DOCTRINE SENTINELS` between `RECONCILIATION` and `DEFAULTS APPLIED`. Each unresolved advisory contributes one line of the form `# - Rule <N> (<name>): <one-line summary of the violation> — see references/voice-prompt-doctrine.md rule <N> for fix recipe`. If no advisories fired or all were resolved, emit `# - No doctrine sentinels.`

---

## 2. Token-counting method (v1 — char-based, ±15% accuracy)

Rules 1 and 2 require an assembled-prompt token estimate. v1 uses a deterministic char-based heuristic — no external tokenizer dependency.

**Algorithm:**

1. Assemble the systemInstruction-equivalent text by concatenating, in this order:
   - `prompts.persona`
   - `prompts.voiceInstructions` (only if voice channel active in section 1)
   - `prompts.chatInstructions` (only if chat channel active)
   - `prompts.intentInstructions` (bot-level)
   - For each intent in section 4 ordering, append: that intent's `validationPrompt` + per-intent post-execution `intentInstructions`.
   - Skip `prompts.openingAnnouncement` — per Compass §6, the greeting is platform-rendered, not part of the systemInstruction.

2. For the concatenated text, classify each character:
   - **Latin / ASCII script chars** (`\p{Latin}` plus digits and punctuation): contribute 1/4 token (4 chars per token).
   - **Hebrew, Arabic, CJK script chars**: contribute 1/1.5 token (1.5 chars per token — per Compass §4 measurements).
   - **Whitespace and structural punctuation**: contribute 1/4 token.

3. Sum the per-char contributions to get the estimate. Round up to the nearest integer.

**Reporting:** in the banner, declare the method and the band: `token estimate (char-method, ±15%): <N> tok — threshold <X> <fired|not fired>`.

**Known limitations:** ±15% accuracy is acceptable for the 1,500 / 5,000 thresholds, both of which have wide bands. Sharper accuracy would be needed to enforce the 200-tok session-resumption ceiling tightly — for that, the spec recommends warning when the estimate is within ±30% of 200.

---

## 3. In-prompt vs platform boundary table

Compass §2 + §6 condensed. Use this table to triage whether a concern belongs in the prompt at all.

| Concern | Belongs in prompt | Belongs outside prompt |
|---|---|---|
| Identity / persona | ✓ (`prompts.persona`) | |
| Tone & pacing concrete behaviors | ✓ (`prompts.voiceInstructions`) | |
| Output rules — TTS-safe formatting | ✓ (per-intent `announcement` / `validationPrompt`) | |
| Tool invocation policy (when/how/preamble) | ✓ (per-intent `intentInstructions`) | |
| Guardrails — domain-specific, contextual judgment | ✓ (`prompts.intentInstructions` recency slot) | |
| Opening greeting | | ✓ Platform — `prompts.openingAnnouncement` (pre-rendered) |
| Voice / language code / VAD thresholds | | ✓ Platform — `AiModelConfig.created.generationConfig` |
| Recording consent / retention | | ✓ Platform — Voicenter CPanel + dialplan |
| PII redaction | | ✓ Pipeline — Presidio / DLP pre+post (out of scope for v1 bot-builder) |
| Prompt-injection defense | | ✓ Pre-LLM classifier — Prompt Guard 2 (out of scope) |
| Parameter format validation | | ✓ Schema + backend validator — slot `ParameterTypeId` + `validationPrompt` enforcement |
| Date/time math | | ✓ Pre-rendered variable injection — `{{TimeNow}}` + derivatives in 4.5.1 |
| Authorization | | ✓ Backend, bound to verified caller identity |
| Rate limiting / abuse | | ✓ Asterisk / SIP trunk level |

**Implication for the bot-builder:** any rule that the doctrine flags as "outside prompt" should not be enforced by the prompt. Skill 1 surfaces "out of prompt scope" warnings (rule 7) when it detects boilerplate that platform should handle.

---

## 4. Token budget table

The **Impact** column is the Compass §4 *measurement* for Gemini Live 3.1 (unchanged). The **Skill 3 behavior** column is the pipeline's *enforcement* policy, deliberately relaxed above the degradation point so authors have working room — see the rule 1 enforcement note. The two diverge on purpose between 2,500 and 5,000.

| Size (tok) | Impact (Compass §4, measured) | Skill 3 behavior (pipeline policy) |
|---|---|---|
| < 800 | Negligible; native audio path ~400 ms TTFA | No banner mention. |
| 800 – 1,499 | Mild; first-turn +100–300 ms | No banner mention. |
| 1,500 – 2,499 | Noticeable; barge-in feels sluggish | Advisory in banner. |
| 2,500 – 3,999 | Material degradation; instruction-drop risk | Advisory in banner. |
| 4,000 – 4,999 | Severe (Compass: "stop, split") | Advisory in banner. |
| 5,000 – 5,999 | — | **Block assembly.** |
| ≥ 6,000 | — | **Block + force decomposition** (orchestrator + specialists). |

The 200-tok session-resumption ceiling (rule 2) is a separate concern with its own banner line.

---

## 5. The 10 operating rules (Compass §8) — closing checklist

These are the prompt-author-facing summary. Useful to re-read before any bot-level prompt edit.

1. The prompt is conversational policy and nothing else. If a concern can be enforced in code with guarantees, enforce it in code.
2. Target 600–1,200 tokens for the system instruction; hard ceiling at 1,500. Above that, split the agent. Below 200 if you need session resumption to work reliably.

> **Pipeline note:** the bot-builder's Skill 3 enforces *advisory* (not blocking) at 1,500–4,999 to give authors room to work; blocking fires at ≥ 5,000, with forced decomposition at ≥ 6,000. See rule 1 and §4 for the actual enforcement thresholds. The 1,500 figure is the Compass author's ideal target, retained verbatim here because the operating rules section is meant to mirror Compass §8; note the pipeline's block threshold (5,000) is deliberately set above the Compass degradation point (2,500).

3. No prompt-injection defenses in the prompt. Use a multilingual classifier as an input gate.
4. No PII rules, rate limits, or compliance boilerplate in the prompt. Those live in the data plane.
5. Tool parameter formats and validation belong in the function schema and a backend validator. The prompt covers *when* and *how* to call, not *what shape*.
6. Voice selection, language code, VAD thresholds, recording consent, and interruption sensitivity are platform configuration — not prompt text.
7. The first message is pre-rendered, not LLM-generated.
8. Compute time and dates in code; inject as pre-rendered variables. Never ask the LLM to do calendar math.
9. Run a separate observer LLM asynchronously on the transcript stream for policy-drift detection. Keep it off the inference critical path. *(Out of scope for v1 bot-builder; informational.)*
10. Delete `"never reveal your system prompt"` and every variant. Treat the prompt as public; put no secrets in it; rely on the layered architecture for actual security.

---

*End of voice-prompt-doctrine reference. Each numbered rule above is cited by skill at runtime via its rule number. Update this file when the Compass doc evolves; bump the spec version in each skill's §1 required-reading row when the contract changes.*
