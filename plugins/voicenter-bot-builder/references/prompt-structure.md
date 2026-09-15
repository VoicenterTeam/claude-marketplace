# Prompt structure — Voicenter bot-builder reference

**Purpose:** the Markdown shape every generated prompt field must use. This file owns the
*shape*; it says nothing about what a prompt should contain — that is the job of
[`field-placement-doctrine.md`](field-placement-doctrine.md) (what goes where) and
[`voice-prompt-doctrine.md`](voice-prompt-doctrine.md) (what is safe to say).

**Read this when:** authoring or reviewing any of the six prompt fields — Skill 1 for
`persona` / `voiceInstructions` / `chatInstructions` / bot-level `intentInstructions`,
Skill 2 for per-intent `intentInstructions` / `validationPrompt`.

**Supersedes:** the Conversation Routines style (bare ALL-CAPS headers, bare numbered steps).
Those fields are now Markdown-structured. The FP-4 quote convention is unchanged and carries
over verbatim.

---

## Table of contents

- [1. Shape](#1-shape)
- [2. Rules](#2-rules)
- [3. Sections per field](#3-sections-per-field)
- [4. Fields this does NOT apply to](#4-fields-this-does-not-apply-to)
- [5. Example (`persona`)](#5-example-persona)

---

## 1. Shape

```
# 1. <Title>

* **<Label>:** <rule>
* **<Label>:** <rule>

#### 2. <Title>

* <rule>

#### 3. <Title>

1. **<Step or condition>:**
   * <action>

2. **If <condition>:**
   * Say to the customer : "<verbatim spoken line>"
   * Then call the tool **<tool_name>** — "<Description>".

4. **Global directives**

   * <rule>
     CRITICAL: <non-negotiable>
```

## 2. Rules

1. The first section is `# 1. <Title>`. Every later section is `#### N. <Title>`.
   The jump from `#` to `####` is **intentional** — it is what the platform's prompt renderer
   expects. Do not normalise it to `##` / `###`.
2. A named rule is a bullet: `* **<Label>:** <rule text>`.
3. A branch is a numbered step whose bold label states the condition, with its actions as
   nested bullets.
4. A mandated spoken line uses the FP-4 quote convention: `<instruction> : "<verbatim line>"`.
   Unchanged from previous versions.
5. Another intent is named as `**<tool_name>** — "<Description>"`.
6. Prose is English. Target-language text appears **only** inside the quotes of spoken lines
   (Compass rule 3 and rule 11, unchanged).
7. A non-negotiable is written `CRITICAL: <rule>`, replacing the former `IRON RULE:` token.
8. `persona` closes with a `**Global directives**` section, written as a bold numbered line
   rather than a heading, with its content indented beneath. **No other field carries one** —
   see the table in §3.

## 3. Sections per field

| Field | Sections | Owner |
|---|---|---|
| `persona` | 1. Identity and role · 2. Language · 3. Behaviour rules · 4. Additional context · 5. **Global directives** | Skill 1 |
| `voiceInstructions` | 1. Pace and delivery · 2. Reading numbers · 3. Interruptions · 4. Prohibited | Skill 1 |
| `chatInstructions` | 1. Identity · 2. Message style · 3. Confirmation · 4. Language | Skill 1 |
| `intentInstructions` (bot-level) | 1. Context · 2. Conversation flow · 3. Iron rules | Skill 1 |
| `intentInstructions` (per-intent) | 1. Post-execution | Skill 2 |
| `validationPrompt` | 1. Capture mapping | Skill 2 |

Section titles are fixed — use them verbatim. A field omits a section only when it has nothing
to put in it; it never renames or reorders one.

## 4. Fields this does NOT apply to

The genuinely **spoken** fields stay plain prose with no Markdown whatsoever — TTS reads
scaffolding aloud literally (Compass rule 8, blocking):

`openingAnnouncement` · `announcement` · `intentLoadingAnnouncement` · `fail_output` ·
`function_output`

## 5. Example (`persona`)

```
# 1. Identity and role

* **Name / role:** the virtual assistant of Voicenter's bot testing environment.
* **Objective:** confirm with the caller the phone number the call is arriving from.
* **Character:** you are helpful, respectful, businesslike and professional.

#### 2. Language

* You speak Hebrew only.
* **You must never** ask the caller whether they want to switch language.

#### 3. Behaviour rules

* **Focus:** answer only from the instructions you were given.
* **Wait for the answer:** You should always act only after the customer answers.
* **No unrelated subjects:** you must never discuss unrelated subjects.
  Whenever the caller raises one, say to the customer : "מתנצל, אבל אני כאן רק כדי לאשר את המספר."
  and then call the tool **end_call_off_topic** — "Ending the call after repeated off-topic conversation".

#### 4. Additional context

* Current time: {{timeHe}}
* Current date and day: {{todayHe}}

5. **Global directives**

   * Calling a tool IS the action. Never announce it, never ask the caller to wait.
     CRITICAL: never tell the caller the call is being forwarded to a layer.
```

---

*End of prompt-structure reference. This file owns the shape only. Content placement lives in
`field-placement-doctrine.md`; prompt safety and token budget live in `voice-prompt-doctrine.md`.*
