#!/usr/bin/env python3
"""v1.24.0 regression — the bot status choice (CHK-28) and the import's placeholder-ID
rule (CHK-27).

Derives variants of the F1 fixture in memory (no new golden files) and asserts:

1. A spec without `**Bot status:**` still emits `BotStatusId` 1 (the goldens are unchanged).
2. `**Bot status:** 2` / `3` emit 2 / 3 and pass every cross-reference check.
3. Any other spec value — `4` (Deleted), `0`, a name — is a parse error, never a default.
4. CHK-28 fails an emitted status that is out of range, not an integer, or not the spec's.
5. CHK-27 fails a repeated or missing ID in each of the five lists the import keys by ID —
   including a repeated `intentRelations[].IntentRelatedID`, the shape v1.2.0 emitted —
   and stays quiet on the shipping golden.

Usage:  python test-import-contract-regression.py      (exits 1 on any failure)
"""

import copy
import json
import re
import sys

import assemble as A
import verify as V

FAILS = []


def check(cond, msg):
    if not cond:
        FAILS.append(msg)


def with_status(text, value):
    return re.sub(r'^(\*\*Primary Language:\*\*.*)$', rf'\1\n**Bot status:** {value}',
                  text, count=1, flags=re.M)


def fails_of(spec_text, bot):
    return V.run(V.build_spec_context(spec_text), bot)[0]


def main():
    base = open('sample-spec-detailed.md', encoding='utf-8').read()
    golden = json.load(open('expected-output-shipping.json', encoding='utf-8'))

    # 1. default unchanged
    bot = A.assemble(A.parse_spec(base))
    check(bot['BotStatusId'] == 1, 'default BotStatusId != 1')
    check(not fails_of(base, golden), f'shipping golden fails: {fails_of(base, golden)}')

    # 2. the choice is emitted and verifies clean
    for v in (1, 2, 3):
        s = with_status(base, v)
        b = A.assemble(A.parse_spec(s))
        check(b['BotStatusId'] == v, f'Bot status {v}: emitted {b["BotStatusId"]!r}')
        check(list(b).index('BotStatusId') == list(bot).index('BotStatusId'),
              f'Bot status {v}: BotStatusId moved')
        f = fails_of(s, b)
        check(not f, f'Bot status {v}: checks failed: {f}')

    # 3. anything else is a parse error
    for bad in ('4', '0', 'Inactive'):
        try:
            A.parse_spec(with_status(base, bad))
            FAILS.append(f'Bot status {bad!r} parsed instead of failing')
        except SystemExit as e:
            check('PARSE ERROR' in str(e), f'Bot status {bad!r}: wrong halt: {e}')

    # 4. CHK-28 catches emission drift
    s2 = with_status(base, 2)
    b2 = A.assemble(A.parse_spec(s2))
    for wrong in (4, 0, '2', True, 3):
        b = copy.deepcopy(b2)
        b['BotStatusId'] = wrong
        check(28 in fails_of(s2, b), f'CHK-28 silent on BotStatusId {wrong!r}')
        check(28 in V.BLOCKING, 'CHK-28 not blocking')

    # 5. CHK-27 — repeated or missing IDs in each list
    def mutated(fn):
        b = copy.deepcopy(golden)
        fn(b['intentList'])
        return fails_of(base, b).get(27, [])

    def dup_rel(il):  # v1.2.0's shape: a second relation reusing the first one's id
        il['intentRelations'][1]['IntentRelatedID'] = il['intentRelations'][0]['IntentRelatedID']

    def dup_param_across_intents(il):
        ps = [p for i in il['intents'] for p in i['IntentParameters']]
        owner = {id(p): i['IntentId'] for i in il['intents'] for p in i['IntentParameters']}
        a = ps[0]
        b = next(p for p in ps if owner[id(p)] != owner[id(a)])
        b['ParameterId'] = a['ParameterId']

    cases = {
        'repeated IntentRelatedID': (dup_rel, 'intentRelations[1].IntentRelatedID', 'repeated'),
        'missing IntentRelatedID': (lambda il: il['intentRelations'][2].pop('IntentRelatedID'),
                                    'intentRelations[2].IntentRelatedID', 'missing'),
        'repeated ParameterId across intents': (dup_param_across_intents, 'ParameterId', 'repeated'),
        'missing ParameterId': (lambda il: il['intents'][0]['IntentParameters'][0].update(ParameterId=None),
                                'ParameterId', 'missing'),
        'null BotIntentId': (lambda il: il['botIntents'][0].update(BotIntentId=None),
                             'botIntents[0].BotIntentId', 'missing'),
        'repeated BotIntentId': (lambda il: il['botIntents'][1].update(BotIntentId=il['botIntents'][0]['BotIntentId']),
                                 'botIntents[1].BotIntentId', 'repeated'),
        'repeated IntentCategoryId': (lambda il: il['intentCategories'].append(dict(il['intentCategories'][0])),
                                      'intentCategories[1].IntentCategoryId', 'repeated'),
    }
    # An IntentId is referenced elsewhere, so it is changed together with its references
    # (otherwise the other checks lose them before CHK-27 runs).
    REF_KEYS = {'IntentId', 'OriginIntentID', 'NextIntentID', 'ApiSilenceIntentID', 'intent'}

    def retarget(o, old, new):
        if isinstance(o, dict):
            for k, v in o.items():
                if k in REF_KEYS and v == old and not isinstance(v, bool):
                    o[k] = new
                else:
                    retarget(v, old, new)
        elif isinstance(o, list):
            for v in o:
                retarget(v, old, new)

    ids0 = [i['IntentId'] for i in golden['intentList']['intents']]
    cases['repeated IntentId'] = (lambda il: retarget(il, ids0[3], ids0[2]),
                                  'intents[3].IntentId', 'repeated')
    cases['string IntentId'] = (lambda il: retarget(il, ids0[3], str(ids0[3])),
                                'intents[3].IntentId', 'missing')
    for name, (fn, where, problem) in cases.items():
        msgs = mutated(fn)
        check(any(where in m and problem in m for m in msgs),
              f'CHK-27 missed {name}: {msgs}')
    check(27 in V.BLOCKING, 'CHK-27 not blocking')

    # Every relation in the shipping golden has its own id (the guard holds on real output).
    rel_ids = [r['IntentRelatedID'] for r in golden['intentList']['intentRelations']]
    check(len(rel_ids) == len(set(rel_ids)), 'golden repeats an IntentRelatedID')

    if FAILS:
        print('IMPORT CONTRACT REGRESSION FAILED:')
        for f in FAILS:
            print('  -', f)
        return 1
    print('import contract regression: all assertions pass')
    return 0


if __name__ == '__main__':
    sys.exit(main())
