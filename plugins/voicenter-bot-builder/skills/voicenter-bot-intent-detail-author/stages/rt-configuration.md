# Skill 2 stage — Step 3: RT-specific configuration

*Load at Step 3 of each intent's authoring, after `validationPrompt` and before Step 4. The
required language fields differ per response type; section 4 declares the RT, so read it and
branch.*

*Two rules bite hardest here and are easy to get backwards: RT=1 terminals carry **no**
`announcement` (the farewell lives on the predecessor), and an `announcement` on an
auto-chaining intent must be the **empty string** (a non-empty one makes the bot wait for an
answer that never comes).*

## Table of contents

- [RT=1 (Layer Transfer)](#rt1-layer-transfer)
- [RT=2 (API Call)](#rt2-api-call)
- [RT=3 (Continue)](#rt3-continue)
- [RT=4 (Dial-Out)](#rt4-dial-out)
- [Step-3 cross-RT iron rules](#step-3-cross-rt-iron-rules-v1130)
- [RT-specific field cheat sheet](#appendix-c--rt-specific-field-cheat-sheet)

---

### 4.3 Step 3 — RT-specific configuration

The Configuration shape and required language fields differ by Response Type. Section 4 declares the RT for each intent — read it and branch.

#### RT=1 (Layer Transfer)

**v1.14.0 hard rule — RT=1 has NO `announcement`. Never author one.** The ending/farewell sentence is authored while detailing the terminal's **PREVIOUS** intent (or the dedicated pre-IVR farewell intent Skill 1 created when the predecessor splits): an FP-4 quoted line as the LAST spoken line of that predecessor's post-execution `intentInstructions`, immediately followed by the instruction to forward to this terminal (by its Description) **without waiting for a caller answer and without telling the caller the call is being transferred to a layer**. Production-verbatim shape:

```
עלייך לומר את המשפט הבא ללקוח מיד : "ההודעה נשלחה, שמחתי לעזור, שיהיה יום נהדר".
מיד לאחר מכן עלייך להעביר את השיחה מיד ל-[terminal Description] ללא המתנה לתגובה מהלקוח.
אסור לך לומר ללקוח שאתה מעביר לשכבת ניתוק.
```

Required language field (the terminal's ONLY utterance):

**Iron rule (RT=1 wording match — fires during step 3, blocking):** before picking `intentLoadingAnnouncement` wording, determine which RT=1 sub-case this terminal is, from its section-4 **Description**:

- **Hang-up terminal** (the call ends here — e.g. "ניתוק עקב שקט ממושך", "סיום השיחה במקרה של דיבור על נושא לא קשור יותר מ-N פעמים"): a short farewell/goodbye filler is correct.
- **Transfer terminal** (the call continues to a queue or human rep — e.g. "העברה לתור טכני", "העברה לנציג אנושי"): the filler MUST communicate that a transfer is happening. Farewell/goodbye phrasing here reads to the caller as the call ending, not as being connected onward — this exact mistake shipped on a production bot (a transfer intent's loading announcement carried a farewell line) and is why this rule exists.

| Field | Terminal type | Example (Hebrew) |
|---|---|---|
| `intentLoadingAnnouncement` | Hang-up | "יום טוב!" / "שיהיה המשך יום טוב!" |
| `intentLoadingAnnouncement` | Transfer | "רגע אחד, מעביר אותך." / "מעביר לנציג אנושי." |

Either way, it must NOT be the full farewell (that lives on the predecessor — FP-6 say-once, check 14; farewell placement, check 18) — it is the RT=1 intent's ONLY spoken content (v1.14.0).

Layer ID is structural (declared in section 4). Skill 1 captures the real layer number from the MCP; if the spec omits a layer, Skill 3 defaults it to `0` (root layer) — there is no `-999` sentinel for layer (v1.12.0). Do not invent a specific layer.

For a terminal carrying `**Terminal outcome:**`, step 2 already wrote the outcome-value capture mapping (check 17); step 3 confirms the loading filler only — the closing line is authored on the predecessor (check 18).

#### RT=2 (API Call)

**Iron rule (live API verification — fires during step 3, blocking; HARD BLOCK, no waiver):**

Before authoring/confirming the RT=2 `announcement`, Skill 2 must verify the API live. An RT=2 intent CANNOT be marked `[detailed]` until this passes. There is no waiver.

1. **Gather a concrete sample request.** Ask the user for real values for the body's Mustache slots and for any secret/auth header values (from section 4.5.2 env or supplied inline for the call). If the URL is still `<UNKNOWN: webhook URL>`, verification cannot run — **block** and route the user back to Skill 1 patch mode to supply the URL.
2. **Execute a live `curl`** (via the Bash tool) against the section-4 URL using the captured method/headers/body with the sample values substituted. Example shape: `curl -sS -X POST "<url>" -H "<header>: <value>" -d '<body-json>' -w "\n%{http_code}"`.
3. **Pass condition (both must hold):**
   - HTTP status is 2xx.
   - Every dotted path declared in section 4.5.4 for this intent, AND every path referenced in the `announcement`, is present in the live response JSON (path form per 4.5.4: `available_slots.0.display`, `response.order.status`).
4. **On pass:** record a verification entry in spec section 7.6 (see `spec-skeleton.md` §7.6) — ISO-8601 timestamp, intent identifier, HTTP status, the confirmed dotted paths, and a **redacted** echo of the request (method, URL, header NAMES with values masked, body with Mustache-slot values masked). Then continue to the language fields.
5. **On any failure** — non-2xx, network/DNS error, unknown URL, or any declared path absent — **block**. Surface the exact failure (HTTP code + body excerpt, or the specific missing path). The intent cannot reach `[detailed]`.

**Secrets & PII:** never write raw secrets or raw PII to the spec. Section 7.6 stores only the masked request echo, the status code, and the confirmed path list.

Required language fields:

| Field | Meaning |
|---|---|
| **Announcement (after API success)** [JSON field: `announcement` — was `apiResponseAnnouncement` pre-v1.5.0] | What the bot says when the API succeeds — **and then it yields the turn and WAITS for a caller answer (v1.17.0 turn-yield fact, FP-3)**. Author it ONLY when the intent's section-4 `**Asks next:**` is a question; it then carries the read-back + that question, almost always with Mustache references against section 4.5.4 dotted paths. When `**Asks next:**` is `[none]` (the intent auto-chains), this field MUST be the empty string — the success speech lives as FP-4 quoted lines in the post-execution `intentInstructions`, immediately before the forward. Log the intentional-empty choice to §7.3. |
| `fail_output` | What the bot says when the API fails. **Default pattern (graceful):** "I couldn't reach the system right now. Let me transfer you to a human." Skill 2 drafts this default; user confirms or rewrites. |
| `function_output` | **Fail-output fallback map** [JSON field: `function_output` — object shape `{ "default": "<fallback string>" }`, v1.5.0 shape change]. Skill 2 prompts the user for the fallback string the runtime should say when the API returns no usable response. The user supplies a single short Hebrew/English string (e.g., `"הייתה תקלה בחיפוש"` / `"Something went wrong, let me try again."`); Skill 2 wraps it as `{ "default": "<user's string>" }` in the spec. Skill 3 emits this object verbatim. If the user wants per-error-code fallbacks (e.g., `{ "default": "...", "503": "..." }`), they can extend the object via patch mode. v1 default capture is `default` key only. |
| `response_success` | **Response success instructions** [JSON field: `response_success` — object shape `{ "instructions": "<text or empty>" }`, v1.5.0 shape change]. Skill 2 prompts the user for any instructional text the runtime should use after a successful API call (e.g., next-step guidance for the LLM). Empty string is the most common production shape (`{ "instructions": "" }`). User supplies the inner string; Skill 2 wraps it as the object. |
| `intentLoadingAnnouncement` | Latency-cover utterance while the API call is in flight. (v1.5.0: capital-I `IntentLoadingAnnouncement` removed; only lowercase is emitted.) |
| `silence_sentence` | What the bot says during the API wait |
| `silence_ending_sentence` | What the bot says after silence loops are exhausted |
| `silence_instructions` | Additional LLM guidance for silence handling (often empty) |

**Iron rule (check 11 — fires during step 3, blocking):** every RT=2 intent must have a complete `api_silence_behaviour`, which is **six components** — three language fields Skill 2 authors here (`silence_sentence`, `silence_ending_sentence`, `silence_instructions`) and three structural fields owned by Skill 1 in section 4 (`silence_duration`, `silence_loops`, and the **fallback intent** — the `intent` failover that Skill 3 resolves to an `IntentId` and emits as `api_silence_behaviour.intent` + `apiSilenceRelations[].ApiSilenceIntentID`). If the structural **fallback intent is missing or unresolved** in section 4, halt and route the user back to Skill 1 patch mode — do not author around it. Per Doc 1 §14.3.6, an RT=2 intent without complete silence behavior produces dead air at runtime when the API takes 8+ seconds; an RT=2 intent **without a fallback intent has no failover** when the caller goes silent mid-API.

**Iron rule (check 10 — fires during step 3, blocking; announcement clause rewritten v1.17.0 per FP-3 turn-yield):** `fail_output`, `function_output`, and `response_success` must all be non-empty. `announcement` is conditional: **non-empty and question-carrying when `**Asks next:**` is a question; MUST be the empty string when `**Asks next:**` is `[none]`** — a non-empty announcement on an auto-chaining intent makes the bot wait for a caller answer that never comes (turn-yield stall → silence loop). The `fail_output` graceful default qualifies as non-empty. For `function_output`, the object `{ "default": "<fallback>" }` qualifies as non-empty. For `response_success`, the object `{ "instructions": "" }` (empty inner string) qualifies as non-empty. **Note:** for `function_output`, `{ "default": "" }` (empty inner string) also qualifies as non-empty for this check — only a missing `function_output` key fails. Production has RT=2 intents with empty inner strings (e.g., transport-planner `plan_customer_travel_route`); the check validates structure, not content fullness.

**Mustache references in `announcement` (RT=2 success field):** must resolve against section 4.5.4 dotted paths declared for THIS intent, OR against slots collected by THIS intent or upstream intents (per section 5 mechanics). Verify at write-time.

**Runtime fallback (voice-agent-llm v1.0.3+):** if `announcement` ships empty, the service substitutes the sentinel `[START THE CONVERSATION]` as an LLM instruction (bot opens from persona; the literal string is **not** spoken aloud). **Check 10 requires `announcement` populated on answer-awaiting intents** — the fallback is a service-side safety net, not a license to ship empty there. On auto-chaining intents (`**Asks next:**` [none]) the empty string is mandatory (v1.17.0, FP-3 turn-yield).

#### RT=3 (Continue)

Required language fields (v1.13.0 — rewritten per FP-2/FP-3/FP-7):

| Field | Meaning | Example (Hebrew) |
|---|---|---|
| `announcement` | The REAL spoken content delivered when this intent's tool completes — **after which the bot yields the turn and WAITS for a caller answer (v1.17.0 turn-yield fact, FP-3)**: the read-back with `{{CustomData}}`/slot vars plus **the section-4 `**Asks next:**` question** — the question the NEXT intent's slots will capture (FP-2 staggering). NEVER filler ("תודה.", "קיבלתי.") — acknowledgment belongs in `intentLoadingAnnouncement`. **MUST be empty whenever `**Asks next:**` is `[none]`** — an auto-chaining intent with a non-empty announcement stalls waiting for an answer that never comes (turn-yield → silence loop). The FP-3 named cases: (a) an API-response list read immediately under this intent's `intentInstructions` reading instructions; (b) this is the intent immediately before the final RT=1 terminal with no splits — its farewell is an FP-4 quoted line in its own `intentInstructions` (check 18); (c) any other auto-chaining intent (v1.17.0) — any remaining spoken line moves to an FP-4 quoted line in `intentInstructions` before the forward. A splitting predecessor never qualifies for (b) — that needs a dedicated pre-IVR farewell intent (structural → Skill 1 patch). Log to 7.3: `announcement intentionally empty on [intent] — FP-3 case (a|b|c)`. | "התוכנית: {{policies}}, חברת הביטוח: {{insurer}}, פרמיה חודשית לאחר הנחה: {{monthlypremiumafterdiscount}}. לתשומת ליבך, ייתכן שהפרמיה תתעדכן בעקבות בדיקה נוספת. האם הפרטים נכונים?" |
| `intentLoadingAnnouncement` | **MANDATORY, non-empty (FP-7 — check 12; CHK-17 backstops).** Short natural filler spoken while the tool executes, matching the persona's register and grammatical gender. An unconfigured value produces the default "." SAY directive — a verified production trigger for duplicated phrases and dead air. | "מצויין, אני רושמת" / "אין בעיה, שניה רושמת" / "אחלה, רק שומרת את התשובה" |
| `response_success` | **Response success instructions** [JSON field: `response_success` — object shape `{ "instructions": "<text or empty>" }`, v1.5.0 shape change]. Skill 2 prompts the user for any instructional text the runtime should use after RT=3 success (collect-and-continue). Empty string is the most common production shape (`{ "instructions": "" }`). User supplies the inner string; Skill 2 wraps it as the object. | `{ "instructions": "" }` |

**Filler-announcement advisory (v1.13.0, fires during step 3):** an RT=3 `announcement` that contains no `{{…}}` reference, no question mark, and is ≤ ~15 characters (e.g., "תודה.") is almost certainly misplaced acknowledgment. Surface: "Acknowledgment belongs in `intentLoadingAnnouncement`; `announcement` must carry the read-back + the `**Asks next:**` question, or be intentionally empty per FP-3 (API-list read-out / pre-terminal farewell-in-instructions / any auto-chaining intent, v1.17.0). Move it?"

**Question-less announcement rule (v1.17.0, FP-3 turn-yield — fires during step 3, blocking):** an RT=3 or RT=2 `announcement` on an intent whose `**Asks next:**` is `[none]` must be the empty string — regardless of length or content. The announcement is a wait-for-answer directive; on an auto-chaining intent it stalls the call into the silence loop. Move any content the caller must still hear into an FP-4 quoted line in the post-execution `intentInstructions` (immediately before the forward instruction), or into `intentLoadingAnnouncement` if it is pure acknowledgment. Log to 7.3.

#### RT=4 (Dial-Out)

Required language fields:

| Field | Meaning |
|---|---|
| `announcement` | Spoken before initiating the dial |
| `intentLoadingAnnouncement` | Spoken while dialing |

Other RT=4 fields (Phone destination, NEXT_VO_ID, etc.) are structural — declared in section 4 by Skill 1.

#### Step-3 cross-RT iron rules (v1.13.0)

**Max turns sentence authoring (v1.14.0 — fires once per bot, during the first step 3):** Skill 2 authors ONE default `max_turns_sentence` for the bot — a short apology-and-retry line adjusted to the persona's register and **grammatical gender**, modeled on:

- masculine: `"מתנצל אבל נראה שיש לי בעיה מסויימת, אנא נסה שנית מאוחר יותר"`
- feminine: `"מתנצלת אבל נראה שיש לי בעיה מסויימת, אנא נסה שנית מאוחר יותר"`

Show it to the user once (accept/edit), then write it into each intent's section-4 `**Max turns sentence:**` field. **Boundary note:** section 4 is Skill 1's domain; this field is a narrow, explicit Skill 2 write exception (like the §4.5.3 regeneration) because the content is language authoring, not structure. Never ask the user about `max_turns` values themselves — those are autonomous (Skill 1 §3.4.3 / Skill 3 default 5).

**Iron rule (say-once, FP-6 — fires during step 3 + gate, blocking; check 14):** no sentence may be mandated as speech in two places — within this intent's fields (`announcement` vs `intentLoadingAnnouncement` vs a quoted line in `intentInstructions`), or between this intent and a bot-level prompt (persona / opening instructions / openingAnnouncement). Compare normalized text (trim, strip punctuation/niqqud, collapse whitespace). Duplicated speak-obligations are the diagnosed root cause of the bot saying things twice in production. On detection: keep the sentence in exactly one field (announcement for content, loading for acknowledgment) and remove the other.

**Iron rule (routing anchor, FP-9 — fires during steps 3–4, blocking):** wherever an announcement or instruction references another intent, reference it by its section-4 **Description text** (e.g., "forward the call to confirming health declaration") — never by tool name, identifier, or an invented label. The Description is how the voice model identifies tools.


---

## Appendix C — RT-specific field cheat sheet

What Skill 2 must populate in step 3 per RT.

| RT | Required fields (Skill 2) | Mustache scope |
|---|---|---|
| 1 | `intentLoadingAnnouncement` only (v1.14.0 — NO `announcement`; the farewell lives on the predecessor per FP-8 / check 18) | Slots from this intent + upstream + 4.5.1 + 4.5.2 |
| 2 | `announcement` (was `apiResponseAnnouncement` pre-v1.5.0), `fail_output`, `function_output` (object `{ "default": "..." }`), `response_success` (object `{ "instructions": "..." }`), `intentLoadingAnnouncement` (v1.5.0: capital-I `IntentLoadingAnnouncement` removed), `silence_sentence`, `silence_ending_sentence`, `silence_instructions` | Above + 4.5.4 dotted paths declared for THIS intent |
| 3 | `announcement` (the read-back + `**Asks next:**` question, or intentionally empty per FP-3), `intentLoadingAnnouncement` (**mandatory, v1.13.0 FP-7**), `response_success` (object `{ "instructions": "..." }`) | Slots from this intent + upstream + 4.5.1 + 4.5.2 + 4.5.4 from upstream RT=2 intents + 4.5.5 CustomData keys |
| 4 | `announcement`, `intentLoadingAnnouncement` | Slots from this intent + upstream + 4.5.1 + 4.5.2 |

Structural fields per RT (declared in section 4 by Skill 1 — not Skill 2's domain):

- RT=1: layer ID
- RT=2: URL, method, headers, body (with Mustache), structural api_silence_behaviour pairing in section 4 + 6.3, response shape declared in 4.5.4
- RT=3: (no structural fields beyond slots)
- RT=4: phone destination, parameter holding phone, NEXT_VO_ID, max dial duration, select-dial option, record (bool)

---

*End of Skill 2 — Intent Detail Author.*
