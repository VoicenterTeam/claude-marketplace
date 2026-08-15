# Baseline Fixtures — frozen v1.17.0

Golden files for the v1.20.0 release, captured by session **S0**
(`../docs/planning/session-prompts.md`) against plugin **v1.17.0**, repo commit `cdc9922`.

> **Never regenerate these after S0.** The whole release is gated on comparing against
> output frozen from the untouched v1.17.0 pipeline (V-C2 byte-comparability, locked
> decision S). If a fixture looks wrong, rerun S0 from scratch — do not hand-patch.

## Why there are two goldens

A **functional v1.18.0** landed on `main` mid-release, adding one emitted field
(`ActiveVersionInfo.PersonaID`, per `references/voicebot-json-contract.md` R7). That put two
rules in direct conflict: "never regenerate the S0 fixtures" and "the golden must match
shipping output." Resolution — keep both, because they prove different things:

| Golden | Baseline | Proves |
|---|---|---|
| `expected-output.json` | v1.17.0, **frozen** | the progressive-disclosure restructure changed **zero bytes** (decision S) |
| `expected-output-shipping.json` | shipping | current emission is correct, PersonaID included |

`assemble.py --wire-baseline 1.17.0` reproduces the frozen one; the default reproduces the
shipping one. CI asserts both **and** that the delta between them is exactly the one key —
which is what bounds the blast radius of the upstream functional change.

`verify.py --wire-baseline=1.17.0` reports CHK-25 as `skipped` against the frozen golden
(the field postdates it) rather than failing it. A skipped check is still a reported row.

## Files

| File | Role |
|---|---|
| `sample-spec-detailed.md` | **F1 clean** — complete Agent Spec, 10 intents, all `[detailed]`, assembles without failures |
| `expected-output.json` | **F1-expected (frozen)** — F1's exact output under the v1.17.0 wire baseline |
| `expected-output-shipping.json` | **F1-shipping** — F1's exact output under current emission rules |
| `expected-banner.txt` | F1's generation banner (§7.2), v1.17.0 vintage — the shipping banner adds exactly one DEFAULTS APPLIED line (`ActiveVersionInfo.PersonaID = 3`) |
| `sample-spec-seeded.md` | **F2 seeded** — F1 plus exactly three deliberate violations |
| `seeded-violations.md` | What each seeded violation is, where it lives, and why |
| `expected-violations-report.md` | v1.17.0's detection baseline for F2 (V-C3/V-C4/V-A2 reference) |
| `baseline-notes.md` | Eight v1.17.0 findings observed while building the fixtures — recorded, not fixed |
| `assemble.py` | Mechanical transcription of Skill 3 §3-§4 (spec → wire format) |
| `verify.py` | Mechanical transcription of Skill 3 §6 (the 26-check cross-reference pass) |
| `stub-api-server.py` | Local API standing in for the fictional clinic's scheduling endpoint |
| `check-static.py` | The V-S static check suite (MS6 §6.1) — runs in CI on every push |
| `trigger-evals.json` | Description trigger evals: positive sets + the cross-fire matrix (needs a live run) |

## F1 at a glance

Brightview Family Clinic Assistant — `en-US`, voice-only, Gemini 3.1 - LLM driven
(`AIModelConfigID` 142), voice `Kore`.

- 10 intents covering **every** response type: RT=1 ×4, RT=2 ×1, RT=3 ×4, RT=4 ×1
- Roles: 2 `entry`, 3 `global`, 5 `chained` → 5 `botIntents[]` rows, 5 `intentRelations[]`
- 11 Mustache references across all five 4.5.x inventories
- FP-12 callback date/time block; FP-6 off-topic global; v1.16.0 negative instructions
- 26/26 cross-reference checks pass on the shipping baseline (25/25 + CHK-25 skipped on the frozen one); token estimate 1,961 (advisory band)

## Reproducing

`assemble.py` and `verify.py` re-derive the artifacts from the spec. They exist so the
baseline is auditable rather than a hand-typed one-off — every emission rule cites the
Skill 3 section it implements.

```sh
# 1. RT=2 live verification (Skill 2's hard block) needs the stub running
python stub-api-server.py &

# 2. F1 must assemble byte-identical to BOTH goldens
python assemble.py sample-spec-detailed.md --wire-baseline 1.17.0 -o /tmp/f1-frozen.json
diff /tmp/f1-frozen.json expected-output.json && echo "frozen golden intact"
python assemble.py sample-spec-detailed.md -o /tmp/f1.json
diff /tmp/f1.json expected-output-shipping.json && echo "shipping golden intact"

# 3. F1 must pass the checks on both baselines (25 + 1 skipped / 26)
python verify.py sample-spec-detailed.md expected-output.json --wire-baseline=1.17.0
python verify.py sample-spec-detailed.md expected-output-shipping.json

# 4. F2 must fire exactly checks 3, 7 (blocking) and 22 (advisory)
python assemble.py sample-spec-seeded.md -o /tmp/f2.json
python verify.py sample-spec-seeded.md /tmp/f2.json    # exits 1 — expected
```

`assemble.py` pins the assembly timestamp (`ASSEMBLY_TS`) because Skill 3 emits
`CreatedDate` "at assembly time" in 26 places, which would otherwise make byte-comparison
impossible. See `baseline-notes.md` N6 — this needs settling in MS6 before the eval
harness is built.

There is deliberately **no** `seeded-output.json`: §6.4 halts emission on any blocking
failure, so a JSON artifact for F2 would itself be a regression.
