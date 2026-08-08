# Baseline Fixtures — frozen v1.17.0

Golden files for the v1.18.0 release, captured by session **S0**
(`../docs/planning/session-prompts.md`) against plugin **v1.17.0**, repo commit `cdc9922`.

> **Never regenerate these after S0.** The whole release is gated on comparing against
> output frozen from the untouched v1.17.0 pipeline (V-C2 byte-comparability, locked
> decision S). If a fixture looks wrong, rerun S0 from scratch — do not hand-patch.

## Files

| File | Role |
|---|---|
| `sample-spec-detailed.md` | **F1 clean** — complete Agent Spec, 10 intents, all `[detailed]`, assembles without failures |
| `expected-output.json` | **F1-expected** — F1's exact assembly output under v1.17.0 |
| `expected-banner.txt` | F1's generation banner (§7.2) |
| `sample-spec-seeded.md` | **F2 seeded** — F1 plus exactly three deliberate violations |
| `seeded-violations.md` | What each seeded violation is, where it lives, and why |
| `expected-violations-report.md` | v1.17.0's detection baseline for F2 (V-C3/V-C4/V-A2 reference) |
| `baseline-notes.md` | Eight v1.17.0 findings observed while building the fixtures — recorded, not fixed |
| `assemble.py` | Mechanical transcription of Skill 3 §3-§4 (spec → wire format) |
| `verify.py` | Mechanical transcription of Skill 3 §6 (the 24-check cross-reference pass) |
| `stub-api-server.py` | Local API standing in for the fictional clinic's scheduling endpoint |

## F1 at a glance

Brightview Family Clinic Assistant — `en-US`, voice-only, Gemini 3.1 - LLM driven
(`AIModelConfigID` 142), voice `Kore`.

- 10 intents covering **every** response type: RT=1 ×4, RT=2 ×1, RT=3 ×4, RT=4 ×1
- Roles: 2 `entry`, 3 `global`, 5 `chained` → 5 `botIntents[]` rows, 5 `intentRelations[]`
- 11 Mustache references across all five 4.5.x inventories
- FP-12 callback date/time block; FP-6 off-topic global; v1.16.0 negative instructions
- 24/24 cross-reference checks pass; token estimate 1,961 (advisory band)

## Reproducing

`assemble.py` and `verify.py` re-derive the artifacts from the spec. They exist so the
baseline is auditable rather than a hand-typed one-off — every emission rule cites the
Skill 3 section it implements.

```sh
# 1. RT=2 live verification (Skill 2's hard block) needs the stub running
python stub-api-server.py &

# 2. F1 must assemble byte-identical to the frozen golden
python assemble.py sample-spec-detailed.md -o /tmp/f1.json
diff /tmp/f1.json expected-output.json && echo "F1 golden intact"

# 3. F1 must pass all 24 checks
python verify.py sample-spec-detailed.md expected-output.json

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
