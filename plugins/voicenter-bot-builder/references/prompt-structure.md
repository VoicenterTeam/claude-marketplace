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
6. **Prose is in the bot's primary language (v1.23.0).** A Hebrew bot is written in Hebrew
   throughout — prose, section titles, rule labels and routing Descriptions — as the production
   Voicenter bots are. Only tool names and `{{variables}}` stay ASCII. (Through v1.22.0 prose was
   English with target-language text only inside quotes — Compass rule 3, now retired.)
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
| `intentInstructions` (bot-level) | 1. Context · 2. Conversation flow — **no Iron rules section (v1.23.0)** | Skill 1 |
| `intentInstructions` (per-intent) | 1. Post-execution | Skill 2 |
| `validationPrompt` | 1. Capture mapping | Skill 2 |

Section titles are fixed — use them verbatim, in the bot's primary language. A field omits a
section only when it has nothing to put in it; it never renames or reorders one.

**Hebrew titles** (Hebrew bots — the `persona` titles are verbatim from production export
BotID 37437):

| Field | Hebrew sections |
|---|---|
| `persona` | 1. זהות ותפקיד · 2. שפה · 3. חוקי התנהגות · 4. הוראות נוספות · 5. **הנחיות גלובליות** |
| `voiceInstructions` | 1. קצב והגשה · 2. הקראת מספרים · 3. התפרצויות · 4. איסורים |
| `chatInstructions` | 1. זהות · 2. סגנון הודעות · 3. אישור · 4. שפה |
| `intentInstructions` (bot-level) | 1. הקשר · 2. מהלך השיחה |
| `intentInstructions` (per-intent) | 1. לאחר הביצוע |
| `validationPrompt` | 1. מיפוי שמירה |

**Where the former Iron rules go (v1.23.0).** The bot-level `intentInstructions` no longer has a
third section. A non-negotiable that belongs to one flow step is a `CRITICAL:` line under that
step; a call-wide rule belongs in `persona` → Global directives; the language-lock guardrail
(Compass rule 5) is the last bullet of the flow section.

## 4. Fields this does NOT apply to

The genuinely **spoken** fields stay plain prose with no Markdown whatsoever — TTS reads
scaffolding aloud literally (Compass rule 8, blocking):

`openingAnnouncement` · `announcement` · `intentLoadingAnnouncement` · `fail_output` ·
`function_output`

## 5. Example (`persona`, Hebrew bot)

```
# 1. זהות ותפקיד

* **שם/תפקיד:** הנציג הווירטואלי של סביבת בדיקות הבוטים של Voicenter.
* **מטרת על:** לאשר מול המתקשר את מספר הטלפון שממנו מגיעה השיחה.
* **אופי:** אתה שירותי, מכבד, ענייני ומקצועי.

#### 2. שפה

* אתה מדבר רק עברית.
* **אסור לך** לשאול את המתקשר אם הוא רוצה להחליף שפה.

#### 3. חוקי התנהגות

* **מיקוד:** ענה רק על סמך ההוראות שקיבלת.
* **המתנה לתשובה:** פעל תמיד רק אחרי שהלקוח ענה.
* **איסור דיבור על נושאים אחרים:** אסור לך לדבר על נושאים שאינם קשורים.
  בכל פעם שהמתקשר מעלה נושא כזה, אמור ללקוח : "מתנצל, אבל אני כאן רק כדי לאשר את המספר."
  ומיד לאחר מכן קרא לכלי **end_call_off_topic** — "סיום השיחה לאחר דיבור חוזר על נושא לא קשור".

#### 4. הוראות נוספות

* השעה עכשיו: {{timeHe}}
* התאריך והיום: {{todayHe}}

5. **הנחיות גלובליות**

   * הקריאה לכלי היא הפעולה עצמה. לעולם אל תודיע עליה ואל תבקש מהמתקשר להמתין.
     CRITICAL: לעולם אל תגיד למתקשר שהשיחה מועברת לשכבה.
```

---

*End of prompt-structure reference. This file owns the shape only. Content placement lives in
`field-placement-doctrine.md`; prompt safety and token budget live in `voice-prompt-doctrine.md`.*
