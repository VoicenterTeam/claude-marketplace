#!/usr/bin/env python3
"""CHK-19 regression tests — finding N1 and its fix.

N1: Skill 1's canonical opening-behaviour template restated the opening
announcement as a *quoted* parenthetical:

    (Opening announcement already played: "<the opening line>")

That matches CHK-19's FP-4 `: "<...>"` extraction, so the opening line counted as
a mandated speech obligation in two sites and CHK-19 failed BLOCKING — meaning a
bot authored exactly as Skill 1 documented could not be assembled.

Two fixes were applied:
  A. Skill 1's template now paraphrases instead of quoting.
  B. CHK-19 no longer extracts quotes from fully-parenthesised lines, since a
     parenthetical is context by convention, not a speech obligation.

Fix B is the risky half: loosening a blocking check can trade a known false
positive for unknown false negatives, and double-speech is exactly what FP-6
exists to catch. So case 3 below is the real point of this file — it asserts the
check still fires on a genuine duplicate. If case 3 ever goes quiet, fix B has
gone too far and must be reverted.

Usage:  python test-chk19-regression.py
Exit 0 = all cases behave as specified.
"""

import io
import json
import sys

import assemble as A
import verify as V

GOLDEN = "expected-output-1.19.0.json"
SPEC = "sample-spec-detailed.md"


def load():
    raw = io.open(SPEC, encoding="utf-8").read()
    spec = V.build_spec_context(raw)
    bot = json.loads(io.open(GOLDEN, encoding="utf-8").read())
    return spec, bot


def chk19(spec, bot):
    fails, _tok, _gated, _skipped = V.run(spec, bot)
    return fails.get(19, [])


CASES = []


def case(name, expect_fires, mutate, why):
    CASES.append((name, expect_fires, mutate, why))


# ---- 1. baseline: the shipped fixture is clean ----
case("baseline F1 (paraphrased parenthetical)", False,
     lambda pr: None,
     "fix A's phrasing must not trip the check")


# ---- 2. the N1 shape itself ----
def n1_shape(pr):
    opening = pr["openingAnnouncement"]
    pr["intentInstructions"] = (
        f'OPENING BEHAVIOR\n(Opening announcement already played: "{opening}")\n'
        + pr["intentInstructions"].split("\n", 2)[-1]
    )


case("N1: quoted parenthetical restating openingAnnouncement", False, n1_shape,
     "the exact shape Skill 1 used to document — must NOT fire after fix B")


# ---- 3. sensitivity: a genuine duplicate must still fail ----
def real_duplicate(pr):
    opening = pr["openingAnnouncement"]
    pr["intentInstructions"] = (
        f'OPENING BEHAVIOR\n1. Greet the caller : "{opening}"\n'
        + pr["intentInstructions"].split("\n", 2)[-1]
    )


case("real duplicate: instruction line re-speaks openingAnnouncement", True, real_duplicate,
     "THE GUARD — fix B must not have blinded the check to actual double-speech")


# ---- 4. a parenthetical wrapping a real instruction is still context ----
def paren_with_instruction(pr):
    opening = pr["openingAnnouncement"]
    pr["intentInstructions"] = (
        f'OPENING BEHAVIOR\n(Note - earlier the bot said : "{opening}")\n'
        + pr["intentInstructions"].split("\n", 2)[-1]
    )


case("parenthetical containing a colon-quote", False, paren_with_instruction,
     "parentheses mean context by convention, wherever the colon sits inside them")


def main():
    fails = 0
    for name, expect_fires, mutate, why in CASES:
        spec, bot = load()
        mutate(bot["ActiveVersionInfo"]["AIModelConfig"]["prompts"])
        msgs = chk19(spec, bot)
        fired = bool(msgs)
        ok = fired == expect_fires
        print(f"[{'PASS' if ok else 'FAIL'}] {name}")
        print(f"         expected CHK-19 {'to fire' if expect_fires else 'silent'}, "
              f"got {'fired' if fired else 'silent'}  — {why}")
        for m in msgs:
            print(f"         > {m}")
        if not ok:
            fails += 1
    print(f"\n{len(CASES) - fails}/{len(CASES)} cases behaved as specified")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
