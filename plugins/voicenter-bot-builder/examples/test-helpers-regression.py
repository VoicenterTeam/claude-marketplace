#!/usr/bin/env python3
"""v1.25.0 regression — a bot's helpers (sub-agents) and their tools.

Asserts, in memory (the only new golden is expected-output-helpers.json, diffed in CI):

1. F1 (no spec section 4.8) emits neither `subAgents` nor `subAgentTools`.
2. F3 (`sample-spec-helpers.md`) assembles to its golden and passes every check.
3. The wire shape: labels -5000… / -6000…, intents by the file's labels, the Email tool
   left out, the knowledge base carried for the import to report, the credential setting a
   marker, `source_filed` spelled as the import reads it, null only on an AI argument's
   `ToolTypeConfigID`.
4. Spec section 4.8 parse errors.
5. CHK-29…CHK-39 each fire on a seeded fault — every failure the import answers with a bare
   500 (or drops silently) — and are blocking.

Usage:  python test-helpers-regression.py      (exits 1 on any failure)
"""

import copy
import json
import re
import sys

import assemble as A
import verify as V

FAILS = []
NEW = range(29, 40)


def check(cond, msg):
    if not cond:
        FAILS.append(msg)


def fails_of(spec_text, bot):
    return V.run(V.build_spec_context(spec_text), bot)[0]


def main():
    f1 = open('sample-spec-detailed.md', encoding='utf-8').read()
    f3 = open('sample-spec-helpers.md', encoding='utf-8').read()
    golden = json.load(open('expected-output-helpers.json', encoding='utf-8'))

    # 1. no section 4.8, no new keys
    b1 = A.assemble(A.parse_spec(f1))
    check('subAgents' not in b1['intentList'] and 'subAgentTools' not in b1['intentList'],
          'F1 emits helper keys')

    # 2. F3 reproduces its golden and verifies clean
    b3 = A.assemble(A.parse_spec(f3))
    check(b3 == golden, 'F3 does not reproduce expected-output-helpers.json')
    check(not fails_of(f3, golden), f'F3 golden fails: {fails_of(f3, golden)}')

    # 3. wire shape
    il = golden['intentList']
    check(list(il)[-2:] == ['subAgents', 'subAgentTools'], 'helper lists not last in intentList')
    iid = {i['IntentToolName']: i['IntentId'] for i in il['intents']}
    subs, tls = il['subAgents'], il['subAgentTools']
    check([s['SubAgentID'] for s in subs] == [-5000, -5001], 'helper labels')
    check([t['ToolId'] for t in tls] == [-6000], 'tool labels (the Email tool must be left out)')
    check(subs[0]['IntentIds'] == [iid['collect_appointment_preferences'], iid['confirm_slot_booking']],
          'booking helper intents')
    check(subs[1]['IntentIds'] == [iid['confirm_slot_booking']], 'two helpers do not share an intent')
    check(subs[0]['ToolAssignments'] == [{'ToolId': -6000, 'IsEnabled': 1, 'Parameters': [],
                                          'ConditionList': []}], 'booking helper assignment')
    check(subs[1]['KnowledgeBases'] == [{'KnowledgeBaseID': 30008,
                                         'KnowledgeBaseName': 'Clinic visitor guide'}], 'knowledge base')
    check(all(t['ToolTypeId'] not in (4, 7, 16) for t in tls), 'deferred type in the file')
    prm = {p['ParameterName']: p for p in tls[0]['Parameters']}
    check(V.CRED_MARKER.match(prm['RequestHeaders']['Config']['value']) is not None,
          'credential setting is not a credential marker')
    check(prm['requested_date'] == {'ToolTypeConfigID': None, 'ParameterName': 'requested_date',
                                    'ToolParameterSourceID': 1,
                                    'Config': {'source_filed': 'requested_date'}}, 'AI argument shape')
    check('TemplateId' not in tls[0], 'TemplateId emitted')

    # 4. parse errors
    bad = {
        'served intent unknown': f3.replace('**Serves intents:** confirm_slot_booking',
                                            '**Serves intents:** confirm_booking', 1),
        'Email without add-after': f3.replace('- **Add after the import:**', '- **Note:**', 1),
        'Used by unknown helper': f3.replace('- **Used by:** booking_helper', '- **Used by:** nobody', 1),
        'no section 5 entry': f3.replace('### Helper: clinic_info_helper\n**Status:**',
                                         '### Helper: info_helper\n**Status:**', 1),
        'risk off-grammar': f3.replace('- **Risk:** 1 — Read', '- **Risk:** low', 1),
        'AI model off-grammar': f3.replace('- **AI model:** 31', '- **AI model:** Gemini', 1),
        'entry without its block': f3.replace('\n---\n\n## 6. Cross-References',
                                              '\n---\n\n### Tool: ghost_tool\n**Status:** [detailed]\n'
                                              '\n---\n\n## 6. Cross-References', 1),
        'section 5 entries without 4.8': f3.replace('## 4.8 Helpers and Tools', '## 4.9 Notes', 1),
    }
    for name, text in bad.items():
        check(text != f3, f'parse case {name!r} did not change the spec')
        try:
            A.parse_spec(text)
            FAILS.append(f'parse case {name!r} parsed instead of failing')
        except SystemExit as e:
            check('PARSE ERROR' in str(e), f'parse case {name!r}: wrong halt: {e}')

    # 5. every new check fires on a seeded fault
    def mutate(fn):
        b = copy.deepcopy(golden)
        fn(b['intentList'])
        return fails_of(f3, b)

    def two_tools(il):
        t = copy.deepcopy(il['subAgentTools'][0])
        t['ToolName'] = 'clinic_slot_lookup_two'
        il['subAgentTools'].append(t)

    def tool0(il):
        return il['subAgentTools'][0]

    def sub(il, n=0):
        return il['subAgents'][n]

    cases = [
        (29, 'repeated ToolId', two_tools),
        (29, 'missing ToolId', lambda il: tool0(il).pop('ToolId')),
        (29, 'repeated SubAgentID', lambda il: sub(il, 1).update(SubAgentID=-5000)),
        (30, 'assignment to an absent tool', lambda il: sub(il)['ToolAssignments'][0].update(ToolId=-6999)),
        (30, 'assignment to a real tool id', lambda il: sub(il)['ToolAssignments'][0].update(ToolId=7624)),
        (30, 'same tool twice on one helper',
         lambda il: sub(il)['ToolAssignments'].append(dict(sub(il)['ToolAssignments'][0]))),
        (31, 'IntentIds repeats a label', lambda il: sub(il)['IntentIds'].append(sub(il)['IntentIds'][0])),
        (31, 'IntentIds holds a real intent id', lambda il: sub(il, 1).update(IntentIds=[64732])),
        (31, 'IntentIds holds an unknown label', lambda il: sub(il, 1).update(IntentIds=[-99])),
        (31, 'IntentIds empty', lambda il: sub(il, 1).update(IntentIds=[])),
        (32, 'SubAgentName missing', lambda il: sub(il).pop('SubAgentName')),
        (32, 'SubAgentName over 100', lambda il: sub(il).update(SubAgentName='x' * 101)),
        (32, 'AiModelId missing', lambda il: sub(il).pop('AiModelId')),
        (32, 'AiModelId not a number', lambda il: sub(il).update(AiModelId='31')),
        (32, 'SubAgentStatusID 3', lambda il: sub(il).update(SubAgentStatusID=3)),
        (33, 'ToolName missing', lambda il: tool0(il).pop('ToolName')),
        (33, 'ToolName over 100', lambda il: tool0(il).update(ToolName='t' * 101)),
        (33, 'ToolName repeated', lambda il: (two_tools(il), il['subAgentTools'][1].update(
            ToolId=-6001, ToolName='clinic_slot_lookup'))),
        (33, 'unknown ToolTypeId', lambda il: tool0(il).update(ToolTypeId=99)),
        (33, 'unknown ToolRiskTypeID', lambda il: tool0(il).update(ToolRiskTypeID=9)),
        (33, 'VersionNumber over 20', lambda il: tool0(il)['ToolVersion'].update(VersionNumber='1' * 21)),
        (33, 'TemplateId present', lambda il: tool0(il).update(TemplateId=4)),
        (33, 'schema on a non-AI tool', lambda il: tool0(il).update(ToolExecutionTypeID=1)),
        (34, 'ParameterName twice in a tool',
         lambda il: tool0(il)['Parameters'].append(dict(tool0(il)['Parameters'][0]))),
        (34, 'ParameterName twice in an assignment',
         lambda il: sub(il)['ToolAssignments'][0].update(Parameters=[
             {'ToolTypeConfigID': 18, 'ParameterName': 'ApiEndpoint', 'ToolParameterSourceID': 5,
              'Config': {'value': 'a'}},
             {'ToolTypeConfigID': 18, 'ParameterName': 'ApiEndpoint', 'ToolParameterSourceID': 5,
              'Config': {'value': 'b'}}])),
        (34, 'unknown ToolParameterSourceID', lambda il: tool0(il)['Parameters'][0].update(ToolParameterSourceID=9)),
        (34, 'source_filed not an argument',
         lambda il: tool0(il)['Parameters'][-1]['Config'].update(source_filed='orderId')),
        (35, 'condition without Value', lambda il: sub(il)['ToolAssignments'][0].update(
            ConditionList=[{'Parameter': 3, 'OperatorID': 1}])),
        (35, 'condition with an unknown operator', lambda il: sub(il)['ToolAssignments'][0].update(
            ConditionList=[{'Parameter': 3, 'OperatorID': 2, 'Value': 'x'}])),
        (35, 'condition without Parameter', lambda il: sub(il)['ToolAssignments'][0].update(
            ConditionList=[{'OperatorID': 1, 'Value': 'x'}])),
        (36, 'an Email tool in the file', lambda il: tool0(il).update(ToolTypeId=4)),
        (36, 'a FileStorage tool in the file', lambda il: tool0(il).update(ToolTypeId=16)),
        (37, 'null SubAgentTitle', lambda il: sub(il).update(SubAgentTitle=None)),
        (37, 'null setting config id', lambda il: tool0(il)['Parameters'][0].update(ToolTypeConfigID=None)),
        (37, 'null in IntentIds', lambda il: sub(il)['IntentIds'].append(None)),
        (38, 'a bearer token in a header', lambda il: tool0(il)['Parameters'][2]['Config'].update(
            value='{"Authorization": "Bearer abc123"}')),
        (38, 'a masked export secret', lambda il: tool0(il)['Parameters'][2]['Config'].update(value='****')),
        (38, 'an MCP AuthToken value', lambda il: tool0(il)['Parameters'][0].update(
            ToolTypeConfigID=33, ParameterName='AuthToken', Config={'value': 'abc'})),
        (38, 'credentials in a URL', lambda il: tool0(il)['Parameters'][0]['Config'].update(
            value='https://user:pw@example.invalid/x')),
        (39, 'instruction does not name its tool', lambda il: sub(il).update(
            Instruction=sub(il)['Instruction'].replace('clinic_slot_lookup', 'the lookup tool'))),
    ]
    fired = {}
    for n, name, fn in cases:
        f = mutate(fn)
        fired.setdefault(n, []).append(name)
        check(n in f, f'CHK-{n} silent on {name!r} (fired: {sorted(f)})')
    for n in NEW:
        check(n in V.BLOCKING, f'CHK-{n} not blocking')
        check(n in fired, f'CHK-{n} has no seeded fault')

    if FAILS:
        print('HELPERS REGRESSION FAILED:')
        for f in FAILS:
            print('  -', f)
        return 1
    for n in NEW:
        print(f'CHK-{n} fires on: ' + '; '.join(fired[n]))
    print('helpers regression: all assertions pass')
    return 0


if __name__ == '__main__':
    sys.exit(main())
