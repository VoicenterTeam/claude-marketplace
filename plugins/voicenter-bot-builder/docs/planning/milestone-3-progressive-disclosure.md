# Milestone 3 — Progressive Disclosure + Description Surgery

**Objective:** every SKILL.md ≤ 400 lines (headroom under the 500 guideline);
procedural detail moves to on-demand `stages/` files; all three frontmatter
descriptions rewritten trigger-first at ≤ 200 characters.

**Why:** the biggest cost/latency lever in the release, effective identically
in both runtimes. Also fixes a live defect: claude.ai truncates descriptions
at 200 chars, so the current ~150-word descriptions are already being cut off
on the consumer surface — trigger phrases past the cut simply don't exist
there (constraint C9).

**Baseline / target:**

| Skill | v1.17.0 lines | Target |
|---|---|---|
| voicenter-bot-spec-designer | 1,106 | ≤ 400 |
| voicenter-bot-intent-detail-author | 825 | ≤ 400 |
| voicenter-bot-json-assembler | 1,386 (pre-MS1) | ≤ 400 |

Order of work: **Skill 3 → Skill 1 → Skill 2** (Skill 3 is largest and MS1/MS2
already gutted §6).

## The classification rule (apply per section, no exceptions)

**Always-loaded (stays in SKILL.md):** decision logic, guardrails, anti-lists,
dispatch, setup/mode detection, batching/checkpoint *rules*, section-status
mechanics, the one-question-per-turn and language rules.

**Stage (moves out):** procedural walk-throughs, per-phase interview scripts,
field-by-field mapping mechanics, RT-specific authoring detail, worked
examples, banner formats.

Test for any ambiguous section: *"If Claude skipped reading this until the
moment it's needed, could anything go wrong earlier in the run?"* If yes →
always-loaded.

## Steps

### 3.1 Split Skill 3

```
skills/voicenter-bot-json-assembler/
├── SKILL.md            # parse rules, §6 dispatch (MS2), anti-list §8, blocking/advisory handling
└── stages/
    ├── assembly-mapping.md        # §4 field mapping detail (spec → wire format, RT Configuration shapes)
    └── sentinels-and-banner.md    # sentinel strategy, drift reporting, banner format + sample
```

The anti-list **must** stay in SKILL.md — it is the skill's operating
conscience and gates everything. Parse rules stay (they gate everything).
Replace each moved section with a one-line summary plus an explicit load
instruction: "At assembly step §4.2, read `stages/assembly-mapping.md`
§AIModelConfig before emitting model fields."

### 3.2 Split Skill 1

```
skills/voicenter-bot-spec-designer/
├── SKILL.md            # runtime/mode detection, phase index, iron rules, doctrine ownership pointers
└── stages/
    ├── phase-interview.md         # Phases 1–4 detail incl. per-RT capture
    ├── phase-graph-and-spec.md    # graph construction, section writing, 4.5 inventory
    └── patch-mode.md              # patch entry mode detail
```

Existing package files (`spec-skeleton.md`, `model-catalog.md`,
`trigger-detection-rules.md`, `templates/`) stay where they are — they are
already on-demand.

### 3.3 Split Skill 2

```
skills/voicenter-bot-intent-detail-author/
├── SKILL.md            # queue build §2.3, batching algorithm, checkpoint mechanic §8, iron rules
└── stages/
    ├── authoring-steps.md         # Steps 1–4 per-intent authoring detail
    └── rt-configuration.md        # RT=1/2/3/4 Configuration authoring specifics
```

The `derive_checkpoint_count` algorithm and checkpoint gate stay in SKILL.md —
they are control flow. The per-intent authoring procedure moves out.

### 3.4 Enforce structural rules on every new file

- Stage files: TOC required if > 100 lines (C6).
- **One level deep:** stage files must not chain to other stage files. They
  may point only back to shared `references/` files (via
  `${CLAUDE_PLUGIN_ROOT}`) or to files in their own skill package.
- Update each skill's required-reading table: rows that pointed at moved
  content now point at the stage file + the phase at which to load it.

### 3.5 Rewrite the three descriptions

Rules (see `../reference/skill-authoring-standards.md` §2 for the full
standard): third person; **trigger-first** ("Use when…"); name the condition,
not the workflow; include the literal phrases users type; negative scoping to
stop cross-firing between the three skills; **≤ 200 characters**; English
(runtime bilingualism stays in the body).

Drafts (tune wording, keep semantics and length budget):

- **spec-designer:** `Use when the user wants to design, scope, or patch a
  Voicenter voice/chat bot spec — "design a bot", "add an intent", "patch
  this bot". Does NOT author per-intent language or emit JSON.`
- **intent-detail-author:** `Use when an Agent Spec has intents marked
  [structural] or [detailed-revisit] and the user wants them filled —
  "detail the intents", "run Skill 2". Does NOT change structure or emit
  JSON.`
- **json-assembler:** `Use when a fully-detailed Agent Spec exists and the
  user asks to build/emit/publish the final Voicenter bot JSON — "assemble
  the JSON", "run Skill 3". Does NOT design specs or author intents.`

Critical: the description must **not summarize the workflow** — a description
that summarizes tempts the model to follow the description instead of reading
the skill body.

### 3.6 Measure

Run `claude plugin details voicenter-bot-builder` before and after; record
always-on vs on-invoke token estimates in the MS6 release notes. Run `/doctor`
to confirm no description-budget overflow.

## Done criteria

- [ ] `wc -l` on all three SKILL.md ≤ 400 (V-S1)
- [ ] All three descriptions ≤ 200 chars, trigger-first, negative-scoped
- [ ] No stage file references another stage file (V-S5)
- [ ] TOC present in every reference/stage file > 100 lines
- [ ] Skill 1 greenfield + patch smoke tests pass; stage files load at the
      right phases (V-C7)
- [ ] Skill 2 full run: checkpoint mechanic unchanged (V-C6)
- [ ] Token measurement recorded (feeds V-A5 acceptance: expect 40–60%
      reduction on Skill 3 invocations; if absent, the classification in the
      split was wrong — fix before proceeding)
