# Validation Checklist — V-Suite

Three families: **V-S** static (scriptable, run after every milestone),
**V-C** Claude Code functional, **V-A** claude.ai regression. MS6 runs the
full suite; individual milestones cite subsets in their done-criteria.

## Fixtures

- **F1 clean:** `examples/sample-spec-detailed.md` — complete, fully-detailed
  spec for a fictional business; assembles without failures.
- **F2 seeded:** F1 plus exactly three deliberate violations:
  1. blocking structural — RT=2 pairing break (CHK-05/06 class)
  2. Mustache resolvability break (CHK-07 class)
  3. one advisory field-placement violation (FP class)
- **F1-expected:** `examples/expected-output.json` — F1's exact assembly
  output under v1.17.0 (generated once from the v1.17.0 baseline, then frozen).

## 1. V-S — Static checks

| ID | Check | Pass criterion |
|---|---|---|
| V-S1 | `wc -l` on all three SKILL.md | each ≤ 500; target ≤ 400 |
| V-S2 | Duplication grep: 3 distinctive phrases sampled from CHK bodies, grepped plugin-wide | each phrase in exactly 1 file |
| V-S3 | Path grep | all shared-file pointers use `${CLAUDE_PLUGIN_ROOT}/`; no `../` escaping a skill dir except via the variable |
| V-S4 | Agent frontmatter lint | no `hooks`/`mcpServers`/`permissionMode`; `name` has no `:`; description < 1,024 chars |
| V-S5 | Depth check | no `stages/*.md` references another `stages/*.md` |
| V-S6 | Contract presence | procedure file contains the output contract; Skill 3 §6.1 and §6.2 both reference it |
| V-S7 | Description budget | all three skill descriptions ≤ 200 chars |
| V-S8 | `claude plugin validate --strict` | exit 0 |

## 2. V-C — Claude Code functional

| ID | Test | Pass criterion |
|---|---|---|
| V-C1 | Install from marketplace clone; check typeahead | `@voicenter-bot-builder:spec-verifier` appears; skills listed |
| V-C2 | Skill 3 on F1 | delegation occurs (Agent tool call visible); report matches contract; assembly proceeds; JSON **byte-comparable** to F1-expected (normalize date-in-filename only) |
| V-C3 | Skill 3 on F2 | all 3 seeded violations caught; correct severity; blocking ones block; routing names the correct skill |
| V-C4 | Force-inline (temporarily rename `agents/`), rerun V-C2 + V-C3 | **identical verdicts** to delegated runs — the single-source equivalence proof |
| V-C5 | Isolation probe | verifier report references only spec content, never conversation history |
| V-C6 | Skill 2 full run, 8–10-intent spec, pause mid-way, re-invoke | checkpoint mechanic unchanged; queue rebuilt from section 5; TodoWrite mirror (if present) never consulted for state |
| V-C7 | Skill 1 greenfield + patch smoke tests | stage files load at the right phases; no missing-instruction failures |
| V-C8 | Commands | `/bot-spec`, `/bot-detail`, `/bot-assemble` invoke the correct skills; behavior identical to description-triggered invocation |
| V-C9 | Haiku gate | V-C2 byte-comparability holds with `model: haiku` on the Assembler (else fall back to sonnet, document) |

## 3. V-A — claude.ai regression (the constraint that must not break)

Upload skills to a claude.ai test account with code execution enabled.

| ID | Test | Pass criterion |
|---|---|---|
| V-A1 | Full pipeline in one conversation: Skill 1 interview → Skill 2 detailing → Skill 3 assembly | completes end-to-end; **no subagent mention, no delegation attempt, no error or hesitation at the dispatch point** |
| V-A2 | Skill 3 on F2, inline | same violations caught as V-C3. Sensitivity differences on *advisory* checks: document, don't fail. A missed **blocking** seeded violation: FAIL |
| V-A3 | Fresh-eyes observable | inline verifier visibly re-reads the spec before checking |
| V-A4 | TodoWrite absence | Skill 2 runs without attempting TodoWrite or erroring on absence |
| V-A5 | Context measurement | tokens-to-first-question (Skill 1) and total pipeline tokens vs v1.17.0 baseline recorded; **expect 40–60% reduction on Skill 3 invocations** |
| V-A6 | Bilingual smoke | Hebrew-language run of Skill 1 Phase 1–2: AskUserQuestion values stay LTR-stable; generated identifiers ASCII |

## 4. Release acceptance criteria (MS6 gate)

1. All V-S pass.
2. V-C2 byte-comparability holds — the restructure changed zero assembly
   behavior (enforces locked decision S).
3. V-C4 equivalence holds — single source of truth proven.
4. V-A1 passes clean — zero degradation artifacts in claude.ai.
5. No blocking seeded violation missed in either runtime (V-C3, V-A2).
6. V-A5 shows measurable context reduction. If the 40–60% expectation doesn't
   materialize, the MS3 split classification was wrong — fix before shipping,
   do not waive.
7. Eval harness (golden-file + trigger evals) green in CI.

## 5. Standing regressions (every future version)

- V-C4 equivalence re-run on any change touching `verification-procedure.md`
  or Skill 3 §6.
- Golden-file eval on every push (CI) — remember directory auto-mirror makes
  every push a de-facto release; only version bumps reach installed users.
- V-S7 description budget on any frontmatter edit.
