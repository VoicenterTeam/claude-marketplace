#!/usr/bin/env python3
"""Mechanical transcription of Skill 3 (JSON Assembler) v1.17.0 §3-§4.

Why this exists
---------------
S0 must freeze the *exact* JSON that Skill 3 v1.17.0 produces for the F1 fixture.
Hand-transcribing ~1,500 lines of wire format would bake transcription errors into
a golden file that every later milestone compares against. This script implements
the same deterministic rules Skill 3 §4 specifies, so the baseline is auditable and
re-runnable instead of a one-off artifact.

Every emission rule below cites the Skill 3 section it comes from. Field ORDER is
load-bearing (§4.2.1/§4.2.2/§4.3.1 all say "matches production export"), and Python
dicts preserve insertion order, so the literal order here IS the emitted order.

Determinism
-----------
Skill 3 §4.2.1 order 6 emits CreatedDate as "ISO timestamp at assembly time". A
wall-clock value would make the golden file un-comparable on every run, so the
assembly instant is pinned by ASSEMBLY_TS. See baseline-notes.md N6.

Usage:
    python assemble.py sample-spec-detailed.md -o expected-output.json
"""

import argparse
import json
import re
import sys

# Pinned assembly instant (§4.2.1 order 6 format "YYYY-MM-DD HH:MM:SS").
ASSEMBLY_TS = "2026-08-08 09:15:00"

# §4.2.2 row 11 / Appendix D.12 — the only known shared Persona row (AccountId=0).
PERSONA_ID = 3

# Which wire-format baseline to emit. "current" = shipping output. "1.17.0" omits
# ActiveVersionInfo.PersonaID so the frozen S0 golden stays byte-reproducible.
WIRE_BASELINE = "current"

# §4.3.2 ParameterType system dictionary — copied verbatim, never re-authored.
PARAM_TYPES = {
    1:  {"Name": "STRING",  "Description": "Basic text input",                  "ValidationPattern": None,                        "IsCustomValidationAllowed": 1, "CreatedDate": "2025-01-21 11:25:25"},
    4:  {"Name": "INTEGER", "Description": "Whole number input",                "ValidationPattern": "^[0-9]+$",                  "IsCustomValidationAllowed": 1, "CreatedDate": "2025-01-21 11:25:25"},
    10: {"Name": "PHONE",   "Description": "Phone number",                      "ValidationPattern": None,                        "IsCustomValidationAllowed": 1, "CreatedDate": "2025-01-21 11:25:25"},
    16: {"Name": "BOOLEAN", "Description": "Yes/No input",                      "ValidationPattern": "^(true|false|yes|no)$",     "IsCustomValidationAllowed": 0, "CreatedDate": "2025-01-21 11:25:25"},
    19: {"Name": "ENUM",    "Description": "Selection from predefined options", "ValidationPattern": None,                        "IsCustomValidationAllowed": 0, "CreatedDate": "2025-01-21 11:25:25"},
    20: {"Name": "JSON",    "Description": "json schema",                       "ValidationPattern": None,                        "IsCustomValidationAllowed": 0, "CreatedDate": "2025-04-10 09:50:42"},
}

# model-catalog.md entries (hardcoded per locked decision F).
MODEL_CATALOG = {
    "Gemini 3.1 - LLM driven": {"AIModelConfigID": 142, "AIModelTypeId": 21, "model": "models/gemini-3.1-flash-live-preview"},
    "Gemini Live":             {"AIModelConfigID": 139, "AIModelTypeId": 18, "model": "models/gemini-3.1-flash-live-preview"},
    "Gemini Voice Driven":     {"AIModelConfigID": 136, "AIModelTypeId": 16, "model": "models/gemini-3.1-flash-live-preview"},
    "Gemini 2.5":              {"AIModelConfigID": 52,  "AIModelTypeId": 10, "model": "models/gemini-2.5-flash-native-audio-preview-12-2025"},
}

MASC_MAX_TURNS_SENTENCE = "מתנצל אבל נראה שיש לי בעיה מסויימת, אנא נסה שנית מאוחר יותר"
DEFAULT_MAX_DURATION_SENTENCE = "נראה שהגענו לזמן שיחה מקסימלי, אנא נסה שנית "
DEFAULT_DAILY_LIMIT_SENTENCE = ("Sorry, but reached daily limit of calls duration, "
                                "please try again later or contact the copany's support")


# --------------------------------------------------------------------------
# §3 Strict-template parsing
# --------------------------------------------------------------------------

def field(block, name, default=None):
    m = re.search(rf'^\s*[-*]?\s*\*\*{re.escape(name)}:\*\*\s*(.*?)\s*$', block, re.M)
    return m.group(1).strip() if m else default


def fenced(block, label):
    """Extract a ```-fenced body that follows a **label:** line."""
    m = re.search(rf'\*\*{label}:\*\*\s*\n+```[a-z]*\n(.*?)```', block, re.S)
    return m.group(1) if m else None


def parse_spec(text):
    spec = {}

    sec1 = text.split('## 2. Persona Bundle')[0]
    spec['identity'] = {
        'Bot Name':            field(sec1, 'Bot Name'),
        'Identifier':          field(sec1, 'Identifier'),
        'Description':         field(sec1, 'Description'),
        'Account ID':          field(sec1, 'Account ID'),
        'Channels Active':     field(sec1, 'Channels Active'),
        'Voice Name':          field(sec1, 'Voice Name'),
        'AI Model Config':     field(sec1, 'AI Model Config'),
        'Created by':          field(sec1, 'Created by', ''),
        'Max call duration':   field(sec1, 'Max call duration', '1200'),
        'Record agent calls':  field(sec1, 'Record agent calls', 'false'),
        'Daily limit':         field(sec1, 'Daily limit', '600'),
        'Daily limit layer':   field(sec1, 'Daily limit layer', '3'),
        'Max duration layer':  field(sec1, 'Max duration layer', '0'),
        'Daily limit sentence':  field(sec1, 'Daily limit sentence'),
        'Max duration sentence': field(sec1, 'Max duration sentence'),
        'IVRLayerSelect_2':    field(sec1, 'IVRLayerSelect_2', '3'),
        'Negative instructions': field(sec1, 'Negative instructions'),
    }

    # §2 persona bundle -> prompts (§4.2.4)
    sec2 = text.split('## 2. Persona Bundle')[1].split('## 3. Caller Silence Behavior')[0]
    def sub(a, b):
        return sec2.split(a)[1].split(b)[0].strip()
    spec['prompts'] = {
        'persona':             sub('### 2.1 Persona (Global Identity)', '### 2.2'),
        'voiceInstructions':   sub('### 2.2 Voice Instructions', '### 2.3'),
        'chatInstructions':    sub('### 2.3 Chat Instructions', '### 2.4'),
        'intentInstructions':  sub('### 2.4 Bot-Level Intent Instructions (Opening Behavior)', '### 2.5'),
        'openingAnnouncement': sub('### 2.5 Opening Announcement', '---'),
    }

    # §3 caller silence
    sec3 = text.split('## 3. Caller Silence Behavior')[1].split('## 4. Intent List')[0]
    spec['silence'] = {
        'intent':                  field(sec3, 'silence failover intent'),
        'silence_duration':        field(sec3, 'silence_duration'),
        'silence_loops':           field(sec3, 'silence_loops'),
        'silence_sentence':        field(sec3, 'silence_sentence'),
        'silence_ending_sentence': field(sec3, 'silence_ending_sentence'),
    }

    # §4 intents (structural)
    sec4 = text.split('## 4. Intent List (Structural)')[1].split('## 4.5 Available Variables')[0]
    intents = []
    for blk in re.split(r'\n### Intent \d+: ', sec4)[1:]:
        ident = blk.split('\n')[0].strip()
        slots = []
        for m in re.finditer(r'^\s+(\d+)\.\s+(\w+) — `ParameterTypeId` (\d+), Required `(\w+)`, Order (\d+)(.*)$', blk, re.M):
            _, nm, pt, req, order, rest = m.groups()
            dv = re.search(r'DefaultValue\s+(.+?)\s*$', rest)
            ol = re.search(r'OptionList\s+(\[.*?\])', rest)
            slots.append({'name': nm, 'ptid': int(pt), 'required': req == 'true',
                          'order': int(order),
                          'default': dv.group(1).strip() if dv else '',
                          'optionlist': json.loads(ol.group(1)) if ol else None})
        api = {}
        m = re.search(r'\*\*API silence behavior:\*\*(.*?)(?=\n\s*-\s+\*\*[A-Z]|\Z)', blk, re.S)
        if m:
            for k in ['silence_duration', 'silence_loops', 'silence_sentence',
                      'silence_ending_sentence', 'silence_instructions']:
                mm = re.search(rf'{k}:\s*(.*?)\s*$', m.group(1), re.M)
                if mm:
                    v = mm.group(1)
                    api[k] = v[1:-1] if v.startswith('"') and v.endswith('"') else v
            mm = re.search(r'fallback intent:\s*(\S+)', m.group(1))
            if mm:
                api['intent'] = mm.group(1)
        intents.append({
            'identifier': ident,
            'Display name': field(blk, 'Display name'),
            'Description': field(blk, 'Description'),
            'Tool name': field(blk, 'Tool name'),
            'rt': int(field(blk, 'Response Type')),
            'role': field(blk, 'Bot-intent role', 'chained'),
            'asks_next': field(blk, 'Asks next'),
            'sensitive': field(blk, 'Sensitive', 'false') == 'true',
            'is_silence': field(blk, 'IsSilenceIntent', 'false') == 'true',
            'max_turns': int(field(blk, 'Max turns', '5')),
            'max_turns_sentence': field(blk, 'Max turns sentence'),
            'max_attempts': field(blk, 'Max attempts'),
            'slots': sorted(slots, key=lambda s: s['order']),
            'transitions': [t for t in re.findall(r'^\s+\d+\.\s+(\w+) \((?:success path|fallback|escalation)',
                                                  blk.split('**Transitions out:**')[1].split('- **')[0], re.M)]
                            if '**Transitions out:**' in blk else [],
            'layer': field(blk, 'Layer'),
            'url': field(blk, 'URL'), 'method': field(blk, 'Method'),
            'headers': field(blk, 'Headers'), 'body': field(blk, 'Body'),
            'api_silence': api,
            'dial_source': field(blk, 'Dial source'),
            'phones': field(blk, 'Phone1 / Phone2 / Phone3'),
            'selectdial_option': field(blk, 'selectdial_option'),
            'NEXT_VO_ID': field(blk, 'NEXT_VO_ID'),
            'MAX_DIAL_DURATION': field(blk, 'MAX_DIAL_DURATION'),
            'record': field(blk, 'Record'),
        })
    spec['intents'] = intents

    # §5 per-intent language content
    sec5 = text.split('## 5. Intent Details')[1].split('## 6. Cross-References')[0]
    details = {}
    for blk in re.split(r'\n### Intent: ', sec5)[1:]:
        ident = blk.split('\n')[0].strip()
        d = {
            'validationPrompt': fenced(blk, 'validationPrompt'),
            'announcement': fenced(blk, r'Announcement \(after API success\)'),
            'intentLoadingAnnouncement': fenced(blk, 'intentLoadingAnnouncement'),
            'intentInstructions': fenced(blk, 'Post-execution intentInstructions'),
            'fail_output': fenced(blk, 'fail_output'),
            'function_output': fenced(blk, 'function_output'),
            'response_success': fenced(blk, 'response_success'),
            'silence_sentence': fenced(blk, 'silence_sentence'),
            'silence_ending_sentence': fenced(blk, 'silence_ending_sentence'),
            'silence_instructions': fenced(blk, 'silence_instructions'),
        }
        if d['announcement'] is None:
            d['announcement'] = fenced(blk, 'Announcement')
        d['slot_desc'] = dict(re.findall(r'^- `(\w+)` — Description:\s*(.*?)\s*Type ', blk, re.M))
        details[ident] = d
    spec['details'] = details
    return spec


def strip_block(s):
    """A fenced body is verbatim content; trailing newline is fence formatting."""
    return '' if s is None else s[:-1] if s.endswith('\n') else s


# --------------------------------------------------------------------------
# §4 Assembly
# --------------------------------------------------------------------------

def assemble(spec):
    ident = spec['identity']
    ints = spec['intents']
    det = spec['details']
    acct = int(ident['Account ID'])
    voice_active = 'voice' in ident['Channels Active']
    created_by = ident['Created by'] or ''

    # ---- §4.1 placeholder allocation ----
    iid, bid, pid, srcid = {}, {}, {}, {}
    for n, it in enumerate(ints):
        iid[it['identifier']] = -10 - n
    for n, it in enumerate([i for i in ints if i['role'] in ('entry', 'global')]):
        bid[it['identifier']] = -100 - n
    n = 0
    for it in ints:
        for s in it['slots']:
            pid[(it['identifier'], s['name'])] = -1000 - n
            n += 1
    for n, it in enumerate(ints):
        srcid[it['identifier']] = -4000 - n

    relations = []              # (origin, next)
    for it in ints:
        for t in it['transitions']:
            if (it['identifier'], t) not in relations:
                relations.append((it['identifier'], t))

    cond = -3000                # §4.1 shared -3000 range
    cond_bot, cond_rel = {}, {}
    for it in ints:
        if it['role'] in ('entry', 'global'):
            cond_bot[it['identifier']] = cond
            cond -= 1
    for r in relations:
        cond_rel[r] = cond
        cond -= 1

    mc = MODEL_CATALOG[ident['AI Model Config']]

    # ---- §4.4 Configuration per RT ----
    def configuration(it):
        d = det[it['identifier']]
        rt = it['rt']
        if rt == 1:                                             # §4.4 RT=1
            return {"layer": int(it['layer'] or 0),
                    "intentLoadingAnnouncement": strip_block(d['intentLoadingAnnouncement'])}
        if rt == 2:                                             # §4.4 RT=2
            a = it['api_silence']
            return {
                "url": it['url'],
                "method": it['method'],
                "headers": json.loads(it['headers']) if it['headers'] else {},
                "body": json.loads(it['body']) if it['body'] else {},
                "fail_output": strip_block(d['fail_output']),
                "announcement": strip_block(d['announcement']),
                "function_output": json.loads(strip_block(d['function_output'])),
                "response_success": json.loads(strip_block(d['response_success'])),
                "intentInstructions": strip_block(d['intentInstructions']),
                "api_silence_behaviour": {                      # §4.4.1 six keys
                    # §4.4.1: -999 sentinel when the fallback intent is unresolvable.
                    "intent": iid.get(a.get('intent'), -999),
                    "silence_loops": int(a['silence_loops']),
                    "silence_duration": int(a['silence_duration']),
                    "silence_sentence": a['silence_sentence'],
                    "silence_instructions": strip_block(d['silence_instructions']),
                    "silence_ending_sentence": a['silence_ending_sentence'],
                },
                "intentLoadingAnnouncement": strip_block(d['intentLoadingAnnouncement']),
            }
        if rt == 3:                                             # §4.4 RT=3 (golden key order)
            return {
                "announcement": strip_block(d['announcement']),
                "response_success": json.loads(strip_block(d['response_success'])),
                "intentInstructions": strip_block(d['intentInstructions']),
                "intentLoadingAnnouncement": strip_block(d['intentLoadingAnnouncement']),
            }
        if rt == 4:                                             # §4.4 RT=4
            p = [x.strip().strip('"') for x in (it['phones'] or '"" / "" / ""').split('/')]
            c = {"phone1": p[0], "phone2": p[1], "phone3": p[2]}
            if it['dial_source'] == 'parameter':
                c = {"phone1": "", "phone2": "", "phone3": "",
                     "parameter_phone": field_or(it, 'Parameter phone'),
                     "selectdial_option": "Parameter"}
            elif it['selectdial_option']:
                c["selectdial_option"] = it['selectdial_option']
            c["NEXT_VO_ID"] = int(it['NEXT_VO_ID'])
            c["MAX_DIAL_DURATION"] = int(it['MAX_DIAL_DURATION'])
            c["record"] = it['record'] == 'true'
            if d['announcement'] is not None:
                c["announcement"] = strip_block(d['announcement'])
            if d['intentLoadingAnnouncement'] is not None:
                c["intentLoadingAnnouncement"] = strip_block(d['intentLoadingAnnouncement'])
            c["intentInstructions"] = strip_block(d['intentInstructions'])
            c["response_success"] = json.loads(strip_block(d['response_success'])) if d['response_success'] else {}
            return c
        raise ValueError(f"unknown RT {rt}")

    def field_or(it, name):
        return it.get(name.lower().replace(' ', '_'), '')

    # ---- §4.3.2 IntentParameters ----
    def parameters(it):
        out = []
        for s in it['slots']:
            pt = PARAM_TYPES[s['ptid']]
            out.append({
                "Name": s['name'],
                "Schema": None,
                "IntentId": iid[it['identifier']],
                "IsActive": 1,
                "CreatedBy": created_by,
                "IsRequired": 1 if s['required'] else 0,
                "ModifiedBy": " ",
                "OptionList": s['optionlist'] if s['ptid'] == 19 else None,
                "CreatedDate": ASSEMBLY_TS,
                "Description": det[it['identifier']]['slot_desc'].get(s['name'], ''),
                "ParameterId": pid[(it['identifier'], s['name'])],
                "DefaultValue": s['default'],
                "ModifiedDate": ASSEMBLY_TS,
                "ParameterType": {
                    "Name": pt['Name'],
                    "IsActive": 1,
                    "CreatedBy": "SYSTEM",
                    "ModifiedBy": None,
                    "CreatedDate": pt['CreatedDate'],
                    "Description": pt['Description'],
                    "ModifiedDate": None,
                    "ParameterTypeId": s['ptid'],
                    "ValidationPattern": pt['ValidationPattern'],
                    "IsCustomValidationAllowed": pt['IsCustomValidationAllowed'],
                },
                "CollectionOrder": s['order'],
                "ParameterTypeId": s['ptid'],
                "ValidationRules": {},
            })
        return out

    # ---- §4.3.1 intents[] ----
    intents_out = []
    for it in ints:
        d = det[it['identifier']]
        intents_out.append({
            "Name": it['Display name'],
            "IntentId": iid[it['identifier']],
            "IsActive": 1,
            "Priority": 1,
            "AccountId": acct,
            "Description": it['Description'],
            "MaxAttempts": int(it['max_attempts']) if it['max_attempts'] else 3,
            "IntentConfig": {
                "prompts": {"llmDescription": "",
                            "validationPrompt": strip_block(d['validationPrompt'])},
                "additional": {
                    "max_turns": it['max_turns'],
                    "sensitive": it['sensitive'],
                    "max_turns_sentence": it['max_turns_sentence'] or MASC_MAX_TURNS_SENTENCE,
                },
            },
            "IntentScripts": [],
            "IntentSources": ([{"SourceID": 1, "SourceName": "VOICE",
                                "IntentSourceID": srcid[it['identifier']]}] if voice_active else []),
            "IntentToolName": it['Tool name'],
            "IntentResponces": {                                 # §4.4 four-key outer shape
                "IsActive": 1,
                "Configuration": configuration(it),
                "ResponseTypeId": it['rt'],
                "SuccessCondition": "",
            },
            "IsSilenceIntent": 1 if it['is_silence'] else 0,
            "IntentCategoryId": -3,
            "IntentParameters": parameters(it),
            "ValidationTimeout": 30,
            "HandlingInstructions": None,
        })

    # ---- §4.3.3 botIntents[] ----
    bot_intents = []
    for order, it in enumerate([i for i in ints if i['role'] in ('entry', 'global')]):
        b = bid[it['identifier']]
        bot_intents.append({
            "BotId": -1,
            "DTMFList": [],
            "IntentId": iid[it['identifier']],
            "IsActive": 1,
            "SortOrder": order,
            "BotIntentId": b,
            "BotVersionId": -2,
            "BotIntentTypeID": 1 if it['role'] == 'entry' else 2,
            "ConditionGroupList": [{
                "Order": 1,
                "IntentConditionList": [],
                "IntentConditionName": "",
                "IntentConditionGroupID": cond_bot[it['identifier']],
                "IntentConditionGroupType": 1,
                "IntentConditionRelationID": b,
                "IntentConditionRelationType": 1,
                "IntentConditionGroupTypeName": "tool",
                "IntentConditionRelationTypeName": "BotIntentID",
            }],
        })

    # ---- §4.3.4 intentRelations[] ----
    rel_out, per_origin = [], {}
    for n, (o, nx) in enumerate(relations):
        rid = -2000 - n
        order = per_origin.get(o, 0)
        per_origin[o] = order + 1
        rel_out.append({
            "Order": order,
            "DTMFList": [],
            "NextIntentID": iid[nx],
            "OriginIntentID": iid[o],
            "IntentRelatedID": rid,
            "ConditionGroupList": [{
                "Order": 0,
                "IntentConditionList": [],
                "IntentConditionName": "",
                "IntentConditionGroupID": cond_rel[(o, nx)],
                "IntentConditionGroupType": 1,
                "IntentConditionRelationID": rid,
                "IntentConditionRelationType": 2,
                "IntentConditionGroupTypeName": "tool",
                "IntentConditionRelationTypeName": "RelatedIntentID",
            }],
        })

    # ---- §4.3.7 apiSilenceRelations[] (deep copy of parent Configuration) ----
    api_rel = []
    for it in ints:
        if it['rt'] == 2:
            api_rel.append({
                "Configuration": json.loads(json.dumps(configuration(it))),
                "OriginIntentID": iid[it['identifier']],
                "ApiSilenceIntentID": iid.get(it['api_silence'].get('intent'), -999),
            })

    # ---- §4.2.5 silence_behaviour ----
    silence = {
        "intent": iid[spec['silence']['intent']],
        "silence_duration": int(spec['silence']['silence_duration']),
        "silence_loops": int(spec['silence']['silence_loops']),
        "silence_sentence": spec['silence']['silence_sentence'],
        "silence_ending_sentence": spec['silence']['silence_ending_sentence'],
    }

    # ---- §4.2.4 created payload (lean) ----
    created = {"realtimeInputConfig": {"automaticActivityDetection": {"disabled": "true"}}}
    if voice_active:
        created["generationConfig"] = {"speechConfig": {"voiceConfig": {
            "prebuiltVoiceConfig": {"voiceName": ident['Voice Name']}}}}

    # ---- §4.2.1 root ----
    out = {
        "Name": ident['Bot Name'],
        "BotID": -1,
        "AccountID": acct,
        "intentList": {                                          # §4.3 six parallel collections
            "intents": intents_out,
            "botIntents": bot_intents,
            "intentRelations": rel_out,
            "intentCategories": [{                               # §4.3.5
                "Name": ident['Bot Name'],
                "IsActive": 1,
                "AccountId": acct,
                "PriorityId": 1,
                "Description": ident['Bot Name'],
                "IntentCategoryId": -3,
            }],
            "silenceRelations": [],                              # §4.3.6
            "apiSilenceRelations": api_rel,
        },
        "BotStatusId": 1,
        "CreatedDate": ASSEMBLY_TS,
        "Description": ident['Description'],
        "BotLanguages": [],
        "ModifiedDate": None,
        "AiModelConfig": {                                       # §4.2.3 top-level
            "Name": ident['AI Model Config'],
            "ApiKey": {},
            "AIModel": mc['AIModelTypeId'],
            "IsActive": 1,
            "AccountId": 0,
            "ModifiedBy": None,
            "CreatedDate": ASSEMBLY_TS,
            "ModifiedDate": ASSEMBLY_TS,
            "AIModelConfig": {"created": {"model": mc['model']}},
            "AIModelConfigID": mc['AIModelConfigID'],
        },
        "ActiveVersionInfo": {                                   # §4.2.2
            "IsActive": 1,
            "CreatedDate": ASSEMBLY_TS,
            "Description": "",
            "BotVersionId": -2,
            "ModifiedDate": None,
            "SystemPrompt": "",
            "AIModelConfig": {                                   # §4.2.3 version-level
                "max_duration": int(ident['Max call duration']),
                "daily_limit": int(ident['Daily limit']),
                "dailyLimitLayerId": int(ident['Daily limit layer']),
                "maxDurationLayerId": int(ident['Max duration layer']),
                "daily_limit_sentence": ident['Daily limit sentence'] or DEFAULT_DAILY_LIMIT_SENTENCE,
                "max_duration_sentence": ident['Max duration sentence'] or DEFAULT_MAX_DURATION_SENTENCE,
                "IVRLayerSelect_2": int(ident['IVRLayerSelect_2']),
                "prompts": spec['prompts'],
                "recordAgentCalls": ident['Record agent calls'],
                "silence_behaviour": silence,
                "created": created,
            },
            "VersionNumber": "0.0.1",
            "AIModelConfigId": mc['AIModelConfigID'],
            "BotVersionStatusId": 3,
        },
    }

    # §4.2.2 row 11 — PersonaID, added by the functional v1.18.0 per
    # voicebot-json-contract.md R7. Appended last (position unverified against a
    # golden export). Omitted under --wire-baseline 1.17.0 so the frozen S0 golden
    # stays byte-reproducible: that fixture's job is proving the *restructure* was
    # inert, and it predates this field.
    if WIRE_BASELINE != "1.17.0":
        out["ActiveVersionInfo"]["PersonaID"] = PERSONA_ID

    return out


def main():
    global WIRE_BASELINE
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--wire-baseline", choices=["current", "1.17.0"], default="current",
                    help="'current' emits shipping output; '1.17.0' omits "
                         "ActiveVersionInfo.PersonaID to reproduce the frozen S0 golden")
    a = ap.parse_args()
    WIRE_BASELINE = a.wire_baseline
    spec = parse_spec(open(a.spec, encoding="utf-8").read())
    out = assemble(spec)
    with open(a.out, "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"wrote {a.out}: {len(spec['intents'])} intents, "
          f"{len(out['intentList']['botIntents'])} botIntents, "
          f"{len(out['intentList']['intentRelations'])} relations, "
          f"{len(out['intentList']['apiSilenceRelations'])} apiSilenceRelations")


if __name__ == "__main__":
    sys.exit(main())
