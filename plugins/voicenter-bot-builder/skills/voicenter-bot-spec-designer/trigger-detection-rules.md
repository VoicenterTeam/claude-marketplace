# Deep Research Nudge — Trigger Detection Rules

This file is consulted by Skill 1 at the **end of greenfield Phase 2** (before Phase 3) to decide whether to activate the Deep Research nudge per locked decisions H, I, J.

Skill 1 scans the transcript of phases 1-2 for any of the four trigger cues below.

- **No cue fires:** silent. The user never sees the nudge. Proceed directly to Phase 3.
- **Any cue fires:** activate the nudge. Construct the parameterized query and offer the user pause-and-research or skip.

The four triggers are extension-friendly: v2 may add new triggers by appending a new rule with the same shape (cue list + query-section impact).

---

## Trigger 1 — Regulated industry

**Detection cues** (any one fires):

- User mentions: medical, healthcare, hospital, clinic, doctor, patient, pharmacy, pharmaceutical, drug, prescription, telemedicine
- User mentions: financial, banking, bank, lending, loan, credit, investment, brokerage, securities, trading, asset management
- User mentions: legal, lawyer, attorney, court, lawsuit, litigation, contract review, paralegal
- User mentions: insurance, claims, policy underwriting, risk assessment
- User mentions specific regulators or compliance frameworks: HIPAA, GDPR, PCI-DSS, SOX, FINRA, SEC, FDA, MiFID, CCPA, PIPEDA, LGPD

**Query-section impact:** populates the conditional `Regulatory/competitive context` section of the research query with regulated-industry-specific framing — what compliance constraints apply to outbound voice/chat agents in this domain, what disclosures are required, what data-handling rules govern the bot's behavior.

---

## Trigger 2 — Expressed uncertainty

**Detection cues** (any one fires):

- User asks: "What's standard?", "What do most people do?", "What's the typical approach?"
- User says: "I don't know", "I'm not sure", "we haven't decided yet", "we're not sure how to handle this"
- User says: "What would you recommend?" — and the context doesn't suggest they want Skill 1 to invent (i.e., they're explicitly asking for external knowledge, not a creative leap)
- User asks for examples of similar bots or reference architectures

**Query-section impact:** flags the `Domain context` and `Intent-derived focus` sections to ask explicitly for "common patterns", "reference architectures", and "what gaps stand out vs. typical bots in this domain".

---

## Trigger 3 — Competitor question

**Detection cues** (any one fires):

- User asks: "How does `[competitor name]` do this?", "How do other `[industry]` companies handle X?"
- User mentions a competitor by name as a reference point ("we want to be like X", "we're competing with Y")
- User asks: "What does the market look like for this?"

**Query-section impact:** populates the conditional `Regulatory/competitive context` section with competitor-research framing — list named competitors, focus on their bot strategies, identify differentiators.

---

## Trigger 4 — Unrecognized niche domain

**Detection cues** (Skill 1's self-assessment):

- The user's domain is highly specific and Skill 1 has no clear priors (e.g., very narrow industry vertical: marine logistics for refrigerated cargo; specialty agricultural equipment leasing; rare medical device repair; bespoke industrial process consulting)
- Skill 1 cannot, with confidence, sketch the typical intent set for this domain from training data alone

**Query-section impact:** the `Domain context` section explicitly requests *domain education* — what the bot's industry actually does day-to-day, who the typical caller is, what success looks like for this kind of bot — not just bot-pattern advice.

This trigger is the most subjective. **When in doubt, fire** — research is offered, not forced. The user can always skip.

---

## Query template

When any trigger fires, Skill 1 constructs a query with these four sections:

```
Research query for [bot name] design

DOMAIN CONTEXT (always populated):
[Industry, use case, target caller demographic, primary purpose of the bot.
 If Trigger 4 fired: also request domain education — what does this industry
 actually do day-to-day?]

REGIONAL/LANGUAGE CONTEXT (always populated):
[Country/region of deployment, primary language, any regional regulatory or
 cultural factors relevant to bot interactions.]

INTENT-DERIVED FOCUS (always populated):
[Rough intent set sketched in phases 1-2, framed as a question:
 "Given this rough intent set, what additional intents or flow patterns are
 common for bots of this type? What gaps stand out compared to reference
 architectures? Any patterns we should adopt or avoid?"]

REGULATORY/COMPETITIVE CONTEXT (conditional — populated only if Trigger 1 or Trigger 3 fired):
[For Trigger 1: specific compliance frameworks the bot must respect; what
 disclosures are typically required; what data-handling rules govern this domain.
 For Trigger 3: named competitors mentioned, what to study about their approach,
 differentiation goals.]
```

---

## Pause-or-skip handling

After presenting the query, Skill 1 asks:

> You can pause here, run this query in a Deep Research conversation, and return with findings — or skip and proceed without research. Which?

### If the user pauses

**Single-conversation runtime:**
- Emit the partial spec (sections 1, 2 filled; sections 3-7 empty/init) as a message.
- Emit the query as a separate message-block.
- Instruct: "Copy both. Run the query in a separate Deep Research conversation. Return here, paste the findings, and I'll continue from Phase 3."

**Claude Code runtime:**
- Write the partial spec to `agent-spec.md`.
- Write the query to `research-query.md`.
- Instruct: "Run the query in a Deep Research conversation. When you have findings, paste them here or save to `research-findings.md`, and I'll continue."

Append to spec section 7.3:
```
[ISO-8601]  Skill 1  greenfield  Deep Research nudge offered (triggers: [list which fired]); user paused for research.
```

### If the user skips

Append to spec section 7.3:
```
[ISO-8601]  Skill 1  greenfield  Deep Research nudge offered (triggers: [list which fired]); user skipped.
```

Proceed to Phase 3.

### Returning from research

User pastes findings (single-conversation) or saves them (Claude Code).

Incorporate into Phase 3 elicitation: "Given these findings, let's revisit the intent set. What changes or additions do they suggest?"

Append to spec section 7.3:
```
[ISO-8601]  Skill 1  greenfield  Deep Research findings incorporated; phase 3 informed by external research.
```

---

## v2 extension pattern

To add a new trigger:

1. Append a section "## Trigger N — `[name]`" below Trigger 4.
2. List detection cues (specific keywords or self-assessment criteria).
3. Specify which query section is impacted (one of the four, or a new conditional section).
4. If a new conditional section is introduced, add it to the query template above.

No SKILL.md edit required as long as the trigger uses the existing four-section query template. New conditional sections require both this file and SKILL.md update.
