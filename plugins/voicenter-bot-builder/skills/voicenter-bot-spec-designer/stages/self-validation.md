# Skill 1 stage — Self-validation checklist (24 checks)

*Load at greenfield close-out and after every patch, before declaring the spec ready. These
are Skill 1's own checks on its own output — distinct from Skill 3's CHK-01…CHK-26
cross-reference pass, which validates the assembled JSON. The two numbering schemes are
unrelated; do not cross-reference them by number.*

24 checks total: 16 blocking, 7 advisory (Checks 8 + 11–15 + 24, of which 11–15 are Compass
doctrine), 1 structural-correctness. Checks 16–17 are house rules covering the opening
announcement/behaviour pair; 18–21 are field-placement doctrine; 22–24 are v1.14.0 rules.

**Execute in the order below.** Blocking failures are surfaced one at a time, in order, with
the exact failure message given.

## Table of contents

- [Checks 1–10 — persona, naming, transitions, channels](#check-1--persona-articulates-identity-role-tone-language-1431--blocking)
- [Checks 11–15 — Compass doctrine (advisory)](#check-11--prompt-prose-in-the-bots-primary-language-v1230-replaces-compass-rule-3--advisory)
- [Checks 16–17 — opening announcement / behaviour house rules](#check-16--opening-announcement-ends-with-a-question-house-rule-v1121--blocking)
- [Checks 18–24 — field-placement and v1.14.0 rules](#check-18--opening-gate-merge-v1130-fp-2--blocking)
- [Severity-handling rules](#severity-handling-rules)

---

### Check 1 — Persona articulates identity, role, tone, language (§14.3.1) — blocking

**Trigger:** `prompts.persona` is empty, generic ("helpful assistant"), or missing one or more of: identity, role, tone, language.

**Failure message:**
> The persona doesn't articulate `[missing element(s)]`. A bot persona must include identity, role, tone, and language at minimum. Empty or generic personas default to generic chatbot behavior at runtime, and code-switch languages mid-call. (Doc 1 §14.3.1.)

**Remediation:** revise persona; re-check.

### Check 2 — No channel-specific content in persona (§14.3.9) — blocking

**Trigger:** `prompts.persona` contains references to pacing, pronunciation, interruption, audio cues (voice-isms), OR formatting, message length, emojis (chat-isms).

**Failure message:**
> The persona contains channel-specific content: "[quoted snippet]". This belongs in `voiceInstructions` (or `chatInstructions`), not `persona` — `persona` is in position 1 of the assembled prompt and runs on every channel. Move it?

**Remediation:** offer to move; on confirmation, edit both fields.

### Check 3 — No per-intent procedural logic in persona (§14.3.10) — blocking

**Trigger:** `prompts.persona` references specific intents or per-intent procedural steps ("when validating address...", "after getting available slots...").

**Failure message:**
> The persona contains per-intent procedural logic: "[quoted snippet]". `persona` runs on every assembled prompt; per-intent logic belongs in the intent's post-execution `intentInstructions` (Skill 2 will author that text). Move it?

**Remediation:** offer to extract; on confirmation, remove from persona and stage a note for Skill 2 about which intent should carry the logic.

### Check 4 — No persistent policy embedded in single intents (§14.3.13) — blocking

**Trigger:** an intent's Skill-1-captured fields (e.g., RT=2 body, RT=4 announcement) contain policy that should apply call-wide (privacy, GDPR, retention, escalation policy, scope-out rules).

**Failure message:**
> Intent `[name]` contains policy that applies to the whole call: "[quoted snippet]". Persistent policy belongs in `persona`, not a single intent — otherwise it's only in scope when that intent is active. Move it?

**Remediation:** offer to move to persona; remove from intent.

### Check 5 — Persona's claimed capabilities ⊆ intent set (§14.3.7) — blocking

**Trigger:** `persona` claims capability X, but no intent handles X.

**Failure message:**
> Persona claims to "[capability]", but no intent is defined to handle that. Either add an intent or trim the persona claim. (Doc 1 §14.3.7 — overpromising leads to hallucinations at runtime.)

**Remediation:** user picks one; act on choice.

### Check 6 — snake_case verb_object naming on all intents (§14.3.8) — blocking

**Trigger:** any `IntentToolName` not in snake_case verb_object form (e.g., camelCase, kebab-case, spaces, Title Case).

**Failure message:**
> Intent identifier "[bad name]" doesn't follow snake_case verb_object. Suggested: "[snake_case suggestion]". Confirm or propose alternative?

**Remediation:** rename; update all transition refs and Mustache refs.

### Check 7 — Every non-terminal intent has escalation transition (§14.3.4) — blocking

**Trigger:** a non-terminal intent (RT ≠ 1, OR RT=1 but not an explicit transfer) lacks at least one transition pointing to an escalation intent.

**Failure message:**
> Intent `[name]` has no escalation path. Per Doc 1 §14.3.4, every non-terminal intent must have a fallback (typically `transfer_to_human`). Add one?

**Remediation:** user supplies escalation target; transition is added.

**Global interaction:** when the bot has a `global` intent, it is reachable from anywhere via its `botIntents[]` type-2 registration, so every intent has an escalation path by construction and Check 7 is satisfied automatically (v1.12.0 — this implicit reachability replaces the v1.8.0 fan-out edges). Check 7 still fires for bots with **no** global intent — those must author explicit escalation transitions, or the user should designate a `global` transfer-to-human.

### Check 8 — Mustache references resolve against section 4.5 + section 5 slots (§14.3.5) — **advisory**

**Trigger:** a Mustache `{{...}}` reference doesn't resolve against:
- 4.5.1 (call-context)
- 4.5.2 (environment)
- 4.5.3 (slots)
- 4.5.4 (API response paths, scoped to the same RT=2 intent's `announcement` — was `apiResponseAnnouncement` pre-v1.5.0)
- 4.5.5 (CustomData keys, v1.13.0)

**Warning message:**
> Reference `{{[name]}}` in `[intent.field]` doesn't resolve against section 4.5. Possibilities: (a) it's collected upstream and I missed it, (b) it's a typo for an existing variable, (c) it's a real CustomData key missing from 4.5.5 — CustomData keys are never invented; if it's real, add it to 4.5.5. Which?

**Action:** record the user's resolution to section 7.3. Continue. Skill 3's check is blocking — this is the early-warning version.

### Check 9 — Active-channel `prompts` fields populated (§14.3.1) — blocking

**Trigger:** a channel marked active in section 1 has empty `prompts.{voice,chat}Instructions`.

**Failure message:**
> Channel `[voice|chat]` is marked active but `prompts.[name]` is empty. Author content for that channel.

**Remediation:** revisit Phase 2.2 for the missing channel.

### Check 10 — Inactive-channel `prompts` have templated defaults, recorded in §7.7 (decision D) — structural-correctness (auto-fix)

**Trigger:** a channel marked inactive in section 1 has `prompts.[name]` empty (no template emitted) OR has template content with no matching line in §7.7 Prompt provenance. **Also fires** when the section-2 body still carries a literal `[default — not user-authored]` marker — that is the pre-v1.20.2 inline form, and it ships into the deployed prompt.

**Action:** auto-fix — emit the template if missing, add the §7.7 line if missing, and strip any inline `[default — not user-authored]` marker (plus the legacy trailing "regenerate this section through Skill 1 patch mode" sentence) from the section-2 body. Log to 7.3: "Auto-applied templated default for inactive channel `[name]`." and, when a legacy marker was stripped, "Migrated inline prompt-provenance marker to §7.7 (v1.20.2)."

No user prompt required.

### Check 11 — Prompt prose in the bot's primary language (v1.23.0; replaces Compass rule 3) — advisory

**Trigger:** Skill 1 inspects each of `prompts.persona`, `prompts.voiceInstructions` (if voice active), `prompts.chatInstructions` (if chat active), `prompts.intentInstructions`. When section 1's `Primary Language` is Hebrew (`he*`), fire if a field's prose — excluding tool names, Mustache variables and quoted lines — is ≥50% Latin letters, i.e. written in English.

**Failure message:**
> The `[field name]` is written mostly in English, but this is a Hebrew bot. Since v1.23.0 every prompt field is written in the bot's primary language — prose, section headings and intent Descriptions — the way the production Voicenter bots are written. Would you like to:
>   (a) Rewrite the field in Hebrew, keeping tool names and `{{variables}}` as they are? *(Recommended)*
>   (b) Keep as-is and continue.

**Remediation:** if (a): draft the Hebrew rewrite, show it, replace on confirmation. If (b): log to 7.3 — `Prompt-language advisory fired on [field]; user kept English.`

**Retired (v1.23.0):** the former check 11 recommended the *opposite* — rewriting ≥30%-non-Latin prose into English (Compass rule 3) — and its rule-11 mirror. Neither fires any more.

### Check 12 — Intent Description in the bot's primary language (v1.23.0; replaces Compass rule 4) — advisory

**Trigger:** for each intent in section 4 of a Hebrew bot, inspect the `Description`. Fire if it is ≥50% Latin letters.

**Failure message:**
> Intent `[identifier]`'s Description is in English, but this is a Hebrew bot. Since v1.23.0 Descriptions are written in the bot's primary language. Would you like to:
>   (a) Rewrite the Description in Hebrew? *(Recommended)*
>   (b) Keep as-is and continue.

**Remediation:** if (a): draft and replace on confirmation. If (b): log to 7.3.

**Gating:** `[any voice]`.

### Check 13 — Recency-slot language-lock guardrail (Compass rule 5) — advisory

**Trigger:** apply only when section 1's `Primary Language` is not English. Inspect `prompts.intentInstructions` text. Apply the regex pattern `(?i)(infer|switch|change).*(language|לשון|לעבור)` OR `(?i)(name|accent|tone).*(language|לשון)` OR (Hebrew, v1.23.0) `(תסיק|תחליף|להחליף|לשנות).*(שפה|השפה)` OR `(שם|מבטא|טון).*(שפה|השפה)` OR `(שפה|השפה).*(שם|מבטא|טון)`.

- If a match exists and is located in the final third (≥66% of total character offset) of the text: pass; no warning.
- If a match exists earlier in the text: warn — "the guardrail is present but not in the recency slot."
- If no match: warn — "no language-lock guardrail detected."

**Failure message (no match case):**
> The bot-level `prompts.intentInstructions` has no language-lock guardrail. Per Compass rule 5 and the cookbook #1197 production bug, Gemini Live can code-switch based on caller name/accent even with English-only instructions elsewhere in the prompt. The mitigation is a recency-slot constraint such as:
>
>   `* לעולם אל תסיק את השפה מהשם, המבטא או הטון של המתקשר. דבר רק עברית.`
>
> (Written in the bot's primary language — the Hebrew line above for a Hebrew bot.) Would you like to:
>   (a) Append the standard guardrail as the last bullet of the `#### 2.` flow section of `prompts.intentInstructions`? *(Recommended)*
>   (b) Skip and continue.

**Failure message (match-but-not-in-recency case):**
> The language-lock guardrail in `prompts.intentInstructions` is present but located at character offset `[N]` of `[total]` ([percent]%). Per Compass §4 "Found in the Middle" + Gemini prompting guidance, negative constraints belong at the end of the instruction. Would you like to move it to the recency slot? *(Recommended yes)*

**Remediation:** on user opt-in: inject the standard line or move the existing match to the end. Log resolution to 7.3.

**Gating:** `[any voice; especially recommended for non-English bots]`.

### Check 14 — Contradictory pacing/length (Compass rule 6) — advisory

**Trigger:** concatenate `prompts.persona` and `prompts.voiceInstructions`. Apply both patterns: tone descriptor regex `(?i)\b(warm|conversational|friendly|relaxed|easygoing|easy-going|patient)\b` AND length-constraint regex `(?i)\b(\d+|one|two)\s*(sentence|sentences|words|line|lines)\s*(max|maximum|or less|or fewer|at most)\b`. Fire if both match within the same field or across fields.

**Failure message:**
> The persona/voice instructions combine a tone descriptor ("[matched tone]") with a strict length constraint ("[matched length]"). Per Compass §5 anti-pattern "Contradictory pacing/tone" and the ConInstruct benchmark (arXiv 2511.14342), this produces friendly preambles that consume the length budget before answering, and response length variance balloons across turns. Pick one primary tone and define an explicit, non-conflicting length bound — e.g., "Default: 1–2 sentences. Use brief affirmations like 'יהי' for soft acknowledgment within longer turns."

**Remediation:** advise rewrite; do not auto-resolve. User confirms with revised text or accepts the warning and continues. Log resolution to 7.3.

**Gating:** `[any voice]`.

### Check 15 — Generic-policy boilerplate (Compass rule 7) — advisory

**Trigger:** case-insensitive substring search across `prompts.persona`, `prompts.voiceInstructions`, `prompts.intentInstructions`, and all per-intent `validationPrompt` fields. v1 stem list: `gdpr`, `hipaa`, `pii`, `personally identifiable`, `medical advice`, `legal advice`, `financial advice`, `we do not store`, `we do not retain`, `data retention`, `do not provide professional`. Fire if any stem matches.

**Failure message:**
> Detected generic-policy boilerplate `"[matched stem]"` in `[field]`. Per Compass §2 anti-list ("generic content-policy lists"), the prompt cannot enforce GDPR/HIPAA/PII compliance — these belong in the data plane (Presidio redaction, dialplan recording-consent gating, SIEM audit). Putting them in the prompt is "a liability waiting to surface in your next HIPAA audit" (Prediction Guard analysis cited in Compass). Three paths:
>   (a) Relocate the content to the spec's §1 `**Negative instructions:**` field — the product's dedicated AI Security Settings destination for "what the agent must never say or commit to." *(Recommended for must-never-say / must-never-commit content, v1.16.0)*
>   (b) Confirm the boilerplate is appropriate to this bot's domain (e.g., medical-domain bot rightly mentions HIPAA) and keep it in place.
>   (c) Remove the boilerplate and rely on platform-side controls (or accept that prompt-side enforcement is probabilistic).

**Remediation:** record user's decision per match in 7.3 — `Compass rule 7 advisory: stem "[X]" in [field] — user relocated to §1 Negative instructions|kept|removed`. On relocate: move the matched content out of the prompt field and append it to §1 `**Negative instructions:**` (creating the field if absent). Do not auto-remove or auto-relocate without the user's choice.

**Gating:** `[any]`.

### Check 16 — Opening announcement ends with a question (house rule, v1.12.1) — blocking

**Trigger:** spec section 2.5 (`prompts.openingAnnouncement`) does not end with a question mark (`?`, or `؟` for Arabic bots), ignoring trailing quotes and whitespace.

**Failure message:**
> The opening announcement "[current text]" does not end with a question. The first audible message must close with an engaging question — preferably asking for the first detail the bot collects (the entry intent's first slot, e.g., "Who am I speaking with?" / "Is it a good time to talk?"). A statement opening leaves the caller without a conversational hook. Suggested rewrite: "[current text reworked to end with a question derived from the entry intent's first slot, or an engaging question if no slot fits]".

**Remediation:** prompt via `AskUserQuestion` per Section 2.4.B (header: "Opening line", 2 options: "Use suggested rewrite *(Recommended)*" / "Write my own question" — free-text capture). Re-check until the announcement ends with a question. There is no pass-without-question path.

### Check 17 — Opening behavior consumes the announcement's answer (house rule, v1.12.1) — blocking

**Trigger:** spec section 2.4's (`prompts.intentInstructions`) first numbered step does not handle the caller's answer to the section 2.5 opening question, OR section 2.4 greets again, OR it re-asks the same question the announcement already asked.

**Failure message:**
> The opening behavior does not consume the opening announcement's question ("[the §2.5 question]"). [It re-greets / re-asks the question / ignores the caller's answer: "[quoted snippet]".] The announcement already greeted and asked; step 1 of OPENING BEHAVIOR must handle the caller's answer (capture the name, branch on yes/no, confirm identity) and never repeat the greeting or the question. Suggested aligned rewrite of the opening steps: "[rewrite]".

**Remediation:** prompt via `AskUserQuestion` per Section 2.4.B (header: "Opening behavior", 2 options: "Apply aligned rewrite *(Recommended)*" / "Edit myself" — free-text capture). Re-check until aligned.

### Check 18 — Opening-gate merge (v1.13.0, FP-2) — blocking

**Trigger:** an `entry` intent whose slot list reduces to a single BOOLEAN whose meaning matches the §2.5 opening question's semantics (canonical case: a dedicated "is now a convenient time?" gate), or any intent whose sole purpose is asking the question the opening announcement already ends with.

**Failure message:**
> Intent `[name]` exists only to ask the opening question ("[the §2.5 question]"). That wastes a full tool round-trip before the first real question. Per FP-2, the question is the LAST sentence of the opening announcement (§2.5) and the yes/no branch lives in the opening behavior (§2.4); the FIRST flow intent's slots capture the answer (`**Captures answer to:**`). Proposed restructure: delete `[name]`, move its branch logic into §2.4, and set `[next intent]`'s `**Captures answer to:**` to the opening question.

**Remediation:** prompt via `AskUserQuestion` per Section 2.4.B (header: "Opening gate", 2 options: "Apply restructure *(Recommended)*" / "Keep the intent"). "Keep" is an escape hatch only when the user affirms the gate does more than the yes/no (extra slots, side effects) — record the justification in 7.3.

### Check 19 — Terminal shape (v1.13.0, FP-8) — blocking

**Trigger (any of):**
- a distinct call outcome named in the interview has no owning RT=1 terminal;
- an RT=1 terminal lacks `**Terminal outcome:**`, or its named slot is missing from the intent's slot list;
- a transition's origin is an RT=1 terminal (terminal→anything chains, incl. finalize→end_call);
- a non-terminal intent's captured fields or staged notes reference an outcome/status slot it doesn't own;
- an intent's purpose is centralized outcome computation (IF/ELSE-IF prose choosing between outcome values);
- (v1.14.0) an RT=1 terminal's predecessor has multiple outbound transitions AND no dedicated pre-IVR farewell intent exists between them — the ending sentence has no valid home (the FP-3 corollary).

**Failure message:**
> Terminal-shape violation: [specifics]. Per FP-8, every outcome gets its OWN one-hop RT=1 terminal that owns its outcome slot (value mode: fixed / captured / dynamic); gates never mention the outcome slot; no intent computes the outcome by recalling the call; the farewell is spoken by the terminal's PREDECESSOR's `intentInstructions` (v1.14.0), so a splitting predecessor needs a dedicated pre-IVR farewell intent. Proposed restructure: [per-terminal decomposition / remove the gate's status reference / merge the finalize→end_call chain into per-outcome terminals / insert a dedicated pre-IVR farewell intent].

**Remediation:** route to the Phase 3 restructure; re-check until clean.

### Check 20 — Persona call-wide rules stated once (v1.13.0, FP-6) — blocking

**Trigger (any of):** persona lacks the turn-taking rule; persona lacks the human-rep handling rule while a human-rep `global` exists; persona lacks the disapproval/decline handling rule while a decline terminal exists; **(v1.14.0) persona lacks the FP-6(d) off-topic handling section (deflect + redirect on first occurrence; ending line + forward to the off-topic global after N loops)**; OR any of these rules' text is ALSO staged into per-intent notes / section 4 fields (duplication).

**Failure message:**
> Persona call-wide rules issue: [missing rule X / rule X duplicated into intent `[name]`]. Per FP-6, the turn-taking rule, human-rep handling, disapproval handling, and off-topic handling (v1.14.0) are each stated exactly once, in persona — the layer the voice model always sees. Canonical turn-taking wording: "You should always act only after the customer answers and only by the instructions you got. You should never act without the customer's specific answer." [If the off-topic section is missing: propose the §3.2.5 injection — run the §3.2.5 elicitation if its answers were never collected.]

**Remediation:** inject the missing rule (AskUserQuestion accept/edit) or remove the duplicate; re-check.

### Check 21 — Callback date/time machinery (v1.13.0, FP-12) — blocking when a callback/scheduling-time slot exists

**Trigger:** any intent collects a callback/scheduling time (slot semantics), AND §2.4 lacks the FP-12 interpretation block (the `{{todayHe}}`/`{{timeHe}}` anchor + relative-time rules), OR 4.5.1 lacks `todayHe`/`timeHe`.

**Failure message:**
> The flow collects a callback time (`[slot]` on `[intent]`) but the opening behavior has no date/time interpretation machinery. Without the `{{todayHe}}`/`{{timeHe}}` anchor and relative-expression rules, downstream automation cannot reliably convert the answer to a dial time, and the bot re-asks what the caller already said. Proposed injection into §2.4: [the FP-12 canonical block].

**Remediation:** prompt via `AskUserQuestion` per Section 2.4.B (header: "Callback block", 2 options: "Inject canonical block *(Recommended)*" / "Edit"); add `todayHe`/`timeHe` to 4.5.1; re-check.

### Check 22 — Off-topic global exists (v1.14.0, FP-6) — blocking

**Trigger:** no section-4 intent is the dedicated off-topic terminal (an RT=1 intent with `**Bot-intent role:** global` whose purpose is ending/forwarding the call after repeated off-topic talk), OR the persona's FP-6(d) off-topic rule does not route to it by its Description, OR more than one such intent exists.

**Failure message:**
> Every bot must carry exactly one dedicated off-topic global intent (v1.14.0): role `global`, RT=1 with the layer matching the user-chosen outcome, short loading announcement only (e.g., "יום טוב !"), and the persona's off-topic rule must forward to it by Description. Currently: [missing / persona routes to "[X]" which doesn't match / duplicates: [list]].

**Remediation:** prompt via `AskUserQuestion` per Section 2.4.B (header: "Off-topic global", 2 options: "Add the off-topic global *(Recommended)*" / "Edit"). Adding runs the §3.2.5 elicitation for any answers not yet collected (outcome / loops / wording); re-check.

### Check 23 — Dedicated forwarding targets (v1.14.0) — blocking

**Trigger (any of):**
- section 3's `silence failover intent` does not resolve to either (i) the dedicated silence-forwarding intent (`**IsSilenceIntent:** true`, RT=1) or (ii) an existing flow intent the user explicitly chose (7.3-logged);
- `**IsSilenceIntent:** true` appears on zero intents while (i) was chosen, or on more than one intent;
- any RT=2 intent's API-silence fallback is missing, or does not resolve to the dedicated API-timeout forwarding intent / a user-chosen existing intent / a 7.3-logged per-intent override.

**Failure message:**
> Silence / API-timeout forwarding issue: [specifics]. Per v1.14.0, the bot always carries a dedicated silence-forwarding intent and a dedicated API-timeout forwarding intent (one each, usually RT=1 Hang-up or Human-rep terminals), unless the user explicitly chose an existing flow intent (e.g., main menu) for that role.

**Remediation:** prompt via `AskUserQuestion` per Section 2.4.B (header: "Forwarding target", 2 options: "Create the dedicated forwarding intent *(Recommended)*" / "Pick an existing intent"). Re-run the §3.1 step 9 / §3.5.1 outcome question if never asked; re-check.

### Check 24 — Sensitive placement (v1.14.0) — advisory

**Trigger (either):**
- `**Sensitive:** true` appears on an intent that does not collect truly sensitive data (ID number, credit card / CVV / expiry / cardholder ID, medical info), or on the ASKING intent of an FP-2 stagger instead of the collecting intent;
- an intent's slots collect sensitive-looking data (slot semantics: national ID, credit card, CVV, medical details) but the intent lacks `**Sensitive:** true`.

**Warning message:**
> Sensitive-flag placement: [intent `[name]` collects [what] but is not flagged / intent `[name]` is flagged but collects nothing sensitive / the flag sits on the asking intent — it belongs on the collecting intent `[N+1 name]`]. When flagged, the details remain usable in API calls configured on that intent but are NOT saved in LOGS/TRACES (Information Security).

**Remediation:** prompt via `AskUserQuestion` per Section 2.4.B (header: "Sensitive flag", 2 options: "Set Sensitive: true *(Recommended)*" / "Keep false"). On setting the flag, ALWAYS deliver the §3.4.3 disclosure message. Record the resolution in 7.3; continue either way.

---

### Severity-handling rules

- **Blocking failures:** do not declare the spec ready until the user resolves them. Each failure is surfaced one at a time, in order, with the exact failure message above.
- **Advisory failures:** record the user's resolution in 7.3, continue. Do not block.
- **Structural-correctness:** auto-fix; log to 7.3; continue.

---
