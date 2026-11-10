#!/usr/bin/env python3
"""v1.23.0 regression — the ElevenLabs wire shape, the gendered Hebrew persona, and
the unverified-model halt.

Derives variants of the F1 fixture in memory (no new golden files) and asserts:

1. `Voicenter Voicebot - ElevenLabs` (390 / type 36) emits the production shape
   observed in BotID 37437 v0.1.149: empty top-level `AIModelConfig`, no
   version-level `created`, voice at `tts.speak.voice`, `recordAgentCalls` boolean.
2. Hebrew bots get PersonaID 261 (Male) / 296 (Female) from `**Agent Gender:**`,
   and 261 when the gender is absent.
3. A catalogued-but-unverified model (387) halts assembly instead of emitting.
5. (v1.23.1) Voicenter Voicebot (321 / type 30), the default, emits the same `tts` shape.
4. The variant passes all 26 cross-reference checks.

Usage:  python test-elevenlabs-regression.py      (exits 1 on any failure)
"""

import re
import sys

import assemble as A
import verify as V

FAILS = []


def check(cond, msg):
    if not cond:
        FAILS.append(msg)


def setf(text, key, value):
    return re.sub(rf'^\*\*{re.escape(key)}:\*\*.*$', f'**{key}:** {value}', text,
                  count=1, flags=re.M)


def main():
    base = open('sample-spec-detailed.md', encoding='utf-8').read()

    el = setf(base, 'AI Model Config', 'Voicenter Voicebot - ElevenLabs')
    el = setf(el, 'Voice Name', 's0T0DT6EAPeX57MQpn3I')
    el = setf(el, 'Agent Gender', 'Female')
    el = setf(el, 'Primary Language', 'he-IL')
    el = setf(el, 'Record agent calls', 'true')

    bot = A.assemble(A.parse_spec(el))
    top = bot['AiModelConfig']
    vac = bot['ActiveVersionInfo']['AIModelConfig']
    check(top['AIModelConfigID'] == 390, 'AIModelConfigID != 390')
    check(top['AIModel'] == 36, 'AIModel (type) != 36')
    check(top['AIModelConfig'] == {}, 'top-level AIModelConfig not empty')
    check('created' not in vac, 'version-level created present on ElevenLabs')
    check(vac.get('tts') == {'speak': {'voice': 's0T0DT6EAPeX57MQpn3I'}}, 'tts.speak.voice wrong')
    check(vac.get('recordAgentCalls') is True, 'recordAgentCalls not boolean true')
    check('max_duration' in vac and 'daily_limit' in vac, 'limit fields dropped')
    keys = list(vac)
    check(keys.index('tts') == keys.index('prompts') + 1, 'tts not right after prompts')
    check(bot['ActiveVersionInfo']['PersonaID'] == 296, 'Hebrew Female persona != 296')

    fails, _tok, _gated, _skipped = V.run(V.build_spec_context(el), bot)
    check(not fails, f'cross-reference checks failed: {fails}')

    check(A.persona_id('he-IL', 'Male') == 261, 'Hebrew Male persona != 261')
    check(A.persona_id('he', None) == 261, 'Hebrew without gender != 261')
    check(A.persona_id('en-US', 'Female') == 249, 'English persona changed')

    # v1.23.1 — Voicenter Voicebot (321 / type 30) is the default and shares the `tts`
    # shape (production export BotID 37390 v0.1.150); its voices are Voicenter's own TTS.
    vv = setf(base, 'AI Model Config', 'Voicenter Voicebot')
    vv = setf(vv, 'Voice Name', 'eitan')
    vv = setf(vv, 'Agent Gender', 'Male')
    vv = setf(vv, 'Primary Language', 'he-IL')
    vv = setf(vv, 'Record agent calls', 'true')
    vbot = A.assemble(A.parse_spec(vv))
    vtop, vvac = vbot['AiModelConfig'], vbot['ActiveVersionInfo']['AIModelConfig']
    check(vtop['Name'] == 'Voicenter Voicebot', '321: Name wrong')
    check(vtop['AIModelConfigID'] == 321 and vtop['AIModel'] == 30, '321: ids wrong')
    check(vtop['AIModelConfig'] == {}, '321: top-level AIModelConfig not empty')
    check('created' not in vvac, '321: version-level created present')
    check(vvac.get('tts') == {'speak': {'voice': 'eitan'}}, '321: tts.speak.voice wrong')
    check(vvac.get('recordAgentCalls') is True, '321: recordAgentCalls not boolean')
    check(vbot['ActiveVersionInfo']['PersonaID'] == 261, '321: Hebrew Male persona != 261')
    vfails = V.run(V.build_spec_context(vv), vbot)[0]
    check(not vfails, f'321: cross-reference checks failed: {vfails}')

    for name in ('Voicenter Voicebot - Gemini',):
        try:
            A.assemble(A.parse_spec(setf(base, 'AI Model Config', name)))
            FAILS.append(f'{name}: unverified model assembled instead of halting')
        except SystemExit as e:
            check('UNVERIFIED' in str(e), f'{name}: halted for the wrong reason: {e}')

    if FAILS:
        print('ELEVENLABS REGRESSION FAILED:')
        for f in FAILS:
            print('  -', f)
        return 1
    print('elevenlabs regression: all assertions pass')
    return 0


if __name__ == '__main__':
    sys.exit(main())
