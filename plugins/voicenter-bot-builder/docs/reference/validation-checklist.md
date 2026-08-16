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
- **F1-expected:** `examples/expected-output.json` (frozen v1.17.0 wire baseline) and
  `examples/expected-output-shipping.json` (shipping) — F1's exact assembly
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
| V-C2 | Skill 3 on F1 | delegation occurs (Agent tool call visible); report matches contract; assembly proceeds; JSON **byte-comparable** to F1-expected (normalize the filename date plus the 24 assembly-time timestamps — 13 `CreatedDate` + 11 `ModifiedDate`; normalize **by path, never by field name**, or the 10 frozen `ParameterType.CreatedDate` values that carry CHK-21 get rewritten. See `../planning/vc-run-instructions.md` V-C2) |
| V-C3 | Skill 3 on F2 | all 3 seeded violations caught; correct severity; blocking ones block; routing names the correct skill |
| V-C4 | Force-inline (temporarily rename `agents/`), rerun V-C2 + V-C3 | **identical verdicts** to delegated runs — the single-source equivalence proof |
| V-C5 | Isolation probe | verifier report references only spec content, never conversation history |
| V-C6 | Skill 2 full run, 8–10-intent spec, pause mid-way, re-invoke | checkpoint mechanic unchanged; queue rebuilt from section 5; TodoWrite mirror (if present) never consulted for state |
| V-C7 | Skill 1 greenfield + patch smoke tests | stage files load at the right phases; no missing-instruction failures |
| V-C8 | Commands | `/voicenter-bot-builder:{bot-spec,bot-detail,bot-assemble}` invoke the correct skills; behavior identical to description-triggered invocation. Commands are namespaced — the bare form does not resolve |
| V-C9 | Haiku gate | V-C2 byte-comparability holds with `model: haiku` on the Assembler (else fall back to sonnet, document) |

### 2a. V-C results

`vc-run-instructions.md` requires pass/fail, surface, date and the **version string from
`claude plugin details`** for every run — a V-C result without the version it ran against is not
evidence. Record them here; one row per run, newest version first. Do not overwrite older rows.

| ID | Result | Version | Date | Surface | Notes |
|---|---|---|---|---|---|
| V-C1 | partial | 1.20.1 | 2026-08-16 | Claude Code (win32) | `plugin details` gate green: Skills (6), Agents (1) `spec-verifier`, always-on ~551 tok. Composer typeahead not eyeball-verified. |
| V-C2 | FAIL (1 field) | 1.20.1 | 2026-08-16 | Claude Code (win32) | Delegation engaged (real `spec-verifier` Agent call); report contract-valid; 26 checks, 0 blocking (CHK-08 banded-advisory ~1,860 tok). Assembly reproduced the golden on **1139 of 1140 lines** after path-scoped TS normalization. Sole divergence: `prompts.chatInstructions` — golden carries the leading `[default — not user-authored]` provenance marker as prompt content; hand-assembly stripped it. See the §3.1 marker-vocabulary gap below. |
| V-C3 | FAIL | 1.20.2 | 2026-08-16 | Claude Code (win32) | Run 1. Both **blocking** seeded violations caught (V1→CHK-03, V2→CHK-07), emission correctly halted. **V3 (advisory, FP-9) missed** — CHK-22 passed. Also CHK-05 fired blocking (baseline says it must not) and CHK-24's advisory half fired (not in baseline). Cause: verifier sourced `intentRelations[]` from §6.2 (derivative) instead of §4 `Transitions out`, seeing 5 edges not 6. |
| V-C3 | FAIL | 1.20.3 | 2026-08-16 | Claude Code (win32) | Run 2, after the 1.20.3 verifier fix. **CHK-05 now passes** citing the new clause verbatim — confirms plugin files are re-read per invocation. CHK-03/CHK-07 still blocking, emission halted. **V3 still missed**, new cause: the verifier now *does* read §4 (its Drift note quotes the seeded `2. transfer_to_human (fallback)` line) but excluded it from `intentRelations[]`, reasoning "routing to globals is via reachability, not explicit edges (per §6.4)". `assembly-mapping.md` §4.3.4 says the opposite — "an author may still list an explicit hand-off to a global; **that authored edge is kept**". CHK-22 needs that rule stated at the check. CHK-24 advisory fires on F1 too, so it predates the 24-check baseline rather than being a regression. |
| V-C3 | **PASS** | 1.20.4 | 2026-08-16 | Claude Code (win32) | Run 3, after the CHK-22 derivation rule. All three seeded violations caught at baseline severities: CHK-03 + CHK-07 blocking, **CHK-22 advisory on the seeded FP-9 edge**; CHK-05 quiet; CHK-02 reports **6** derived edges (was 5). No JSON emitted. Routing: CHK-03→Skill 1, CHK-22→Skill 1, CHK-07→both paths offered (Skill 1 listed first; baseline expects Skill 2 primary — cosmetic ordering delta). Two documented extras vs the frozen 24-check baseline: CHK-08 banded-advisory (baseline expects it to fire) and CHK-24 advisory half (also fires on F1, so predates the baseline). Bonus: Drift note 4 independently flagged §6.5's `-1…-10` ID scheme as diverging from `assembly-mapping.md` §4.1's `-10,-11,-12` convention — matching what the V-C2 hand assembly found. |
| V-C4 | — | | | | not yet run against 1.20.1 |
| V-C5 | — | | | | not yet run against 1.20.1 |
| V-C6 | — | | | | not yet run against 1.20.1 |
| V-C7 | — | | | | not yet run against 1.20.1 |
| V-C8 | — | | | | not yet run against 1.20.1 |
| V-C9 | — | | | | not yet run against 1.20.1 |

## 3. V-A — claude.ai regression (the constraint that must not break)

Upload skills to a claude.ai test account with code execution enabled.

| ID | Test | Pass criterion |
|---|---|---|
| V-A1 | Full pipeline in one conversation: Skill 1 interview → Skill 2 detailing → Skill 3 assembly | completes end-to-end; **no subagent mention, no delegation attempt, no error or hesitation at the dispatch point** |
| V-A2 | Skill 3 on F2, inline | same violations caught as V-C3. Sensitivity differences on *advisory* checks: document, don't fail. A missed **blocking** seeded violation: FAIL |
| V-A3 | Fresh-eyes observable | inline verifier visibly re-reads the spec before checking |
| V-A4 | TodoWrite absence | Skill 2 runs without attempting TodoWrite or erroring on absence |
| V-A5 | Context measurement | **always-loaded** context vs v1.17.0 recorded; gate is **≥ 40% reduction in always-loaded body** (measured with `claude plugin details`, not the char estimate — see `../planning/ms3-token-report.md` §1b). Per-scenario end-to-end costs are recorded as a **non-gating** metric. Re-scoped after MS3 — see `../planning/ms3-token-report.md` §3. |
| V-A6 | Bilingual smoke | Hebrew-language run of Skill 1 Phase 1–2: AskUserQuestion values stay LTR-stable; generated identifiers ASCII |

## 4. Release acceptance criteria (MS6 gate)

1. All V-S pass.
2. V-C2 byte-comparability holds — the restructure changed zero assembly
   behavior (enforces locked decision S).
3. V-C4 equivalence holds — single source of truth proven.
4. V-A1 passes clean — zero degradation artifacts in claude.ai.
5. No blocking seeded violation missed in either runtime (V-C3, V-A2).
6. V-A5 shows ≥ 40% reduction in **always-loaded** context (actual: **−68% skills-only**, −41% total plugin — `claude plugin details`, 2026-08-15; see `../planning/ms3-token-report.md` §1b).
   End-to-end happy-path cost is recorded, not gated: progressive disclosure
   cannot shrink a run that legitimately reads every rule, so a full assembly
   is flat-to-slightly-worse by construction. Content compression is scheduled
   as its own version — see `../planning/ms3-token-report.md` §3.
7. Eval harness (golden-file + trigger evals) green in CI.

## 5. Standing regressions (every future version)

- V-C4 equivalence re-run on any change touching `verification-procedure.md`
  or Skill 3 §6.
- Golden-file eval on every push (CI) — remember directory auto-mirror makes
  every push a de-facto release; only version bumps reach installed users.
- V-S7 description budget on any frontmatter edit.
