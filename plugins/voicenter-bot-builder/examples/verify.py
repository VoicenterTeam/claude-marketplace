#!/usr/bin/env python3
"""Mechanical transcription of Skill 3 §6 — the 39-check cross-reference pass.

Implements the detections in Skill 3 SKILL.md §6.2, run against the assembled
wire structure (plus the spec, which checks 16-24 additionally consult).

Used twice in S0: to confirm F1 assembles clean, and to record which checks fire
on the F2 seeded fixture (the v1.17.0 detection baseline that V-C3/V-C4/V-A2
compare against).

Run order per §6.1: 1-7, 11-13, 15, 16-21, 22-24, 26-39, then 8, 9, 10, 14, 25.
Blocking per §6: 1-7, 11-13, 15, 16-21, 24(announcement half), 26-39. 8 is banded.
9, 14, 22, 23 advisory; 10 blocking on mismatch; 25 blocking since v1.22.0.

CHK-25 (PersonaID) postdates the frozen v1.17.0 golden, so --wire-baseline=1.17.0
reports it as `skipped` rather than failing it.

Usage:
    python verify.py sample-spec-detailed.md expected-output-shipping.json
    python verify.py sample-spec-detailed.md expected-output.json --wire-baseline=1.17.0
"""

import json
import re
import sys
import unicodedata

import assemble as A

BLOCKING = {1, 2, 3, 4, 5, 6, 7, 11, 12, 13, 15, 16, 17, 18, 19, 20, 21, 24, 25, 26, 27, 28,
            29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39}
NAMES = {
    1: "botIntents[].IntentID resolves", 2: "intentRelations[] resolves",
    3: "apiSilenceRelations[] resolves", 4: "intents[].IntentCategoryId resolves",
    5: "RT=2 apiSilenceRelations pairing + inline failover",
    6: "Configuration == apiSilenceRelations[].Configuration",
    7: "Mustache resolvability", 8: "Assembled-prompt token budget (Compass rule 1)",
    9: "Session-resumption ceiling (Compass rule 2)",
    10: "Model-config doctrine (Compass rule 12)",
    11: "Global registered as type-2", 12: "No chained intent in botIntents",
    13: "Start point exists", 14: "Section-4.6 catalog intents resolve",
    15: "No duplicate global intents by tool name",
    16: "validationPrompt speech-free (FP-5)",
    17: "RT=3 intentLoadingAnnouncement present (FP-7)",
    18: "Own-parameter references (FP-8)", 19: "No duplicate speak-obligation (FP-6)",
    20: "Terminal shape (FP-8)", 21: "ParameterType dictionary byte-match",
    22: "No authored edges into type-2 globals (FP-9)",
    23: "Off-topic global present (FP-6)",
    24: "Turn-yield announcement gating (FP-3)",
    25: "Persona derivation from Primary Language (contract R7/R11)",
    26: "Layer fields are integers (contract §2 Types)",
    27: "Import placeholder IDs present and unique (contract R3/§7)",
    28: "Bot status in range (contract R8/R11/§7)",
    29: "Helper and tool labels present and unique (contract §8)",
    30: "Tool assignments resolve (contract §8)",
    31: "Helper intents are the file's intent labels (contract §8)",
    32: "Helper fields (contract §8)",
    33: "Tool fields (contract §8)",
    34: "Tool parameter lists (contract §8)",
    35: "Assignment conditions complete (contract §8)",
    36: "No credential-only tool type in the file (contract §8)",
    37: "No stray null in helpers and tools (contract §8)",
    38: "No credential in the file (contract §8)",
    39: "Helper instruction names its tools (contract §8)",
}

# Appendix D.12 — known shared Persona rows (AccountId=0) that are never emitted.
# 3 (TTSScriptReader) was the flat default through v1.21.0 and is the likeliest
# regression value; 244 (multilingual Hebrew speaker) was the Hebrew row through
# v1.22.0, replaced in v1.23.0 by the gendered 261 / 296 pair.
PERSONA_NEVER_EMITTED = {3: "TTSScriptReader", 244: "multilingual Hebrew speaker (pre-v1.23.0)"}

# A line that is wholly wrapped in parentheses is context, not a speech obligation.
PAREN_LINE = re.compile(r"^\(.*\)$", re.S)


def fp4_quotes(text):
    """FP-4 quoted lines (`: "<line>"`) that are genuine speech obligations.

    Fully-parenthesised lines are skipped (finding N1). FP-4's convention is
    semantic — `<instruction verb> : "<verbatim line>"` — but the extraction is
    syntactic, so it cannot tell "say this" from "this was already said". A
    parenthetical restating the opening announcement is the latter, and treating
    it as an obligation made CHK-19 block a bot authored exactly as Skill 1
    documented. Parentheses already mean "context" by convention throughout these
    specs, so honouring that is narrower than allow-listing instruction verbs,
    which would risk false negatives on real double-speech.

    Splitting on newlines means a quoted line that itself spans a newline is not
    matched. That is not an authoring shape these specs use, and line granularity
    is what makes "fully parenthesised" decidable.
    """
    out = []
    for line in str(text or "").split("\n"):
        if PAREN_LINE.match(line.strip()):
            continue
        out.extend(re.findall(r':\s*"([^"]+)"', line))
    return out


def norm(s):
    s = unicodedata.normalize("NFKC", s).strip().lower()
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", "", s))


def walk_strings(o, path=""):
    if isinstance(o, dict):
        for k, v in o.items():
            yield from walk_strings(v, f"{path}.{k}")
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from walk_strings(v, f"{path}[{i}]")
    elif isinstance(o, str):
        yield path, o


def run(spec, bot):
    il = bot["intentList"]
    ints = il["intents"]
    by_id = {i["IntentId"]: i for i in ints}
    ids = set(by_id)
    s4 = {i["identifier"]: i for i in spec["intents"]}
    ident_of = {}
    for i in ints:
        ident_of[i["IntentId"]] = i["IntentToolName"]
    fails = {}
    skipped = []

    def fail(n, msg):
        fails.setdefault(n, []).append(msg)

    # 1-4 ID resolution
    for b in il["botIntents"]:
        if b["IntentId"] not in ids:
            fail(1, f"botIntents IntentId {b['IntentId']} unresolved")
    for r in il["intentRelations"]:
        for k in ("OriginIntentID", "NextIntentID"):
            if r[k] not in ids:
                fail(2, f"intentRelations {k} {r[k]} unresolved")
    for r in il["apiSilenceRelations"]:
        for k in ("OriginIntentID", "ApiSilenceIntentID"):
            if r[k] not in ids:
                fail(3, f"apiSilenceRelations {k} {r[k]} unresolved")
    cats = {c["IntentCategoryId"] for c in il["intentCategories"]}
    for i in ints:
        if i["IntentCategoryId"] not in cats:
            fail(4, f"{i['IntentToolName']}: IntentCategoryId {i['IntentCategoryId']} unresolved")

    # 5-6 RT=2 pairing + deep equality
    for i in ints:
        if i["IntentResponces"]["ResponseTypeId"] != 2:
            continue
        cfg = i["IntentResponces"]["Configuration"]
        row = next((r for r in il["apiSilenceRelations"] if r["OriginIntentID"] == i["IntentId"]), None)
        if row is None:
            fail(5, f"{i['IntentToolName']}: no apiSilenceRelations row")
            continue
        inline = cfg.get("api_silence_behaviour", {}).get("intent")
        if not isinstance(inline, int):
            fail(5, f"{i['IntentToolName']}: api_silence_behaviour.intent missing/non-int")
        elif inline != row["ApiSilenceIntentID"]:
            fail(5, f"{i['IntentToolName']}: inline intent {inline} != ApiSilenceIntentID {row['ApiSilenceIntentID']}")
        if json.dumps(cfg, sort_keys=True, ensure_ascii=False) != json.dumps(row["Configuration"], sort_keys=True, ensure_ascii=False):
            fail(6, f"{i['IntentToolName']}: Configuration deep-inequality with registry copy")

    # 7 Mustache resolvability
    ctx = set(re.findall(r"`\{\{(\w+)\}\}`", spec["_45_1"]))
    env = set(re.findall(r"`\{\{(ENV\.\w+)\}\}`", spec["_45_2"]))
    cd = set(re.findall(r"`\{\{(\w+)\}\}`", spec["_45_5"]))
    slot_owner = {s["name"]: it["identifier"] for it in spec["intents"] for s in it["slots"]}
    api_paths = {}
    for m in re.finditer(r"`(\w+)` returns:\n((?:- `[^`]+`\n)+)", spec["_45_4"]):
        api_paths[m.group(1)] = set(re.findall(r"- `([^`]+)`", m.group(2)))
    # reachability over authored relations
    adj = {}
    for r in il["intentRelations"]:
        adj.setdefault(ident_of[r["OriginIntentID"]], set()).add(ident_of[r["NextIntentID"]])

    def upstream(a, b):                       # is a upstream of b
        seen, stack = set(), [a]
        while stack:
            n = stack.pop()
            if n == b and n != a:
                return True
            for x in adj.get(n, ()):
                if x not in seen:
                    seen.add(x)
                    stack.append(x)
        return False

    for i in ints:
        who = i["IntentToolName"]
        for path, txt in walk_strings(i):
            for tok in re.findall(r"\{\{([^}]+)\}\}", txt):
                if tok in ctx or tok in env or tok in cd:
                    continue
                if tok in slot_owner:
                    o = slot_owner[tok]
                    if o == who or upstream(o, who):
                        continue
                    fail(7, f"{who}{path}: {{{{{tok}}}}} owned by {o}, not upstream")
                    continue
                hit = any(tok in p for src, p in
                          [(k, v) for k, vs in api_paths.items() for v in vs]
                          if src == who or upstream(src, who))
                if not hit:
                    fail(7, f"{who}{path}: {{{{{tok}}}}} unresolvable")

    # 11-13, 15 role integrity
    bt = {b["IntentId"]: b for b in il["botIntents"]}
    for ident, it in s4.items():
        i = next(x for x in ints if x["IntentToolName"] == ident)
        if it["role"] == "global" and bt.get(i["IntentId"], {}).get("BotIntentTypeID") != 2:
            fail(11, f"{ident}: role global but not registered type-2")
        if it["role"] == "chained" and i["IntentId"] in bt:
            fail(12, f"{ident}: role chained but present in botIntents")
    if not il["botIntents"]:
        fail(13, "no botIntents entries — bot has no start point")
    seen = {}
    for ident, it in s4.items():
        if it["role"] == "global":
            seen.setdefault(it["Tool name"], []).append(ident)
    for tn, lst in seen.items():
        if len(lst) > 1:
            fail(15, f"tool name {tn!r} global in {len(lst)} intents: {lst}")

    # 16 validationPrompt speech-free
    SPEECH = re.compile(r"(?im)^\s*\W*(say|ask|tell|greet|announce|read (back|aloud)|repeat back)\b")
    for i in ints:
        vp = i["IntentConfig"]["prompts"]["validationPrompt"]
        for ln in vp.splitlines():
            if SPEECH.search(ln) and not re.search(r"(?i)(save|set|store|exactly)", ln):
                fail(16, f"{i['IntentToolName']}: speech in validationPrompt: {ln.strip()[:60]!r}")

    # 17 RT=3 loading announcement
    for i in ints:
        if i["IntentResponces"]["ResponseTypeId"] == 3:
            la = i["IntentResponces"]["Configuration"].get("intentLoadingAnnouncement", "")
            if not la.strip() or la.strip() == ".":
                fail(17, f"{i['IntentToolName']}: RT=3 intentLoadingAnnouncement empty/'.'")

    # 18 own-parameters only
    owner = {p["Name"]: i["IntentToolName"] for i in ints for p in i["IntentParameters"]}
    for i in ints:
        cfg = i["IntentResponces"]["Configuration"]
        body = " ".join([i["IntentConfig"]["prompts"]["validationPrompt"],
                         str(cfg.get("announcement", "")), str(cfg.get("intentInstructions", ""))])
        for nm, o in owner.items():
            if o != i["IntentToolName"] and re.search(rf"\b{re.escape(nm)}\b", body):
                fail(18, f"{i['IntentToolName']}: foreign param {nm!r} (owned by {o})")

    # 19 duplicate speak-obligation
    sites = {}

    def add(t, where):
        for s in re.split(r"(?<=[.!?])\s+", (t or "").strip()):
            n = norm(s)
            if len(n) >= 12:
                sites.setdefault(n, set()).add(where)

    for i in ints:
        cfg = i["IntentResponces"]["Configuration"]
        add(cfg.get("announcement", ""), f"{i['IntentToolName']}.announcement")
        add(cfg.get("intentLoadingAnnouncement", ""), f"{i['IntentToolName']}.loading")
        for q in fp4_quotes(cfg.get("intentInstructions", "")):
            add(q, f"{i['IntentToolName']}.instr-quote")
    pr = bot["ActiveVersionInfo"]["AIModelConfig"]["prompts"]
    add(pr["openingAnnouncement"], "prompts.openingAnnouncement")
    for f in ("persona", "intentInstructions"):
        for q in fp4_quotes(pr[f]):
            add(q, f"prompts.{f}-quote")
    for n, w in sites.items():
        if len(w) > 1:
            fail(19, f"{sorted(w)}: {n[:55]!r}")

    # 20 terminal shape
    origins = {r["OriginIntentID"] for r in il["intentRelations"]}
    for i in ints:
        if i["IntentResponces"]["ResponseTypeId"] != 1:
            continue
        cfg = i["IntentResponces"]["Configuration"]
        ident = i["IntentToolName"]
        if "announcement" in cfg:
            fail(20, f"{ident}: RT=1 carries an announcement key")
        if "layer" not in cfg:
            fail(20, f"{ident}: RT=1 missing layer")
        if i["IntentId"] in origins:
            fail(20, f"{ident}: RT=1 terminal is an OriginIntentID (terminal->x chain)")
        to = spec["_terminal_outcome"].get(ident)
        if to:
            slot = to.split("=")[0].strip()
            if slot not in {p["Name"] for p in i["IntentParameters"]}:
                fail(20, f"{ident}: terminal outcome slot {slot!r} not in IntentParameters")
            val = to.split("=", 1)[1].strip()
            if val.startswith('"'):
                if val.strip('"') not in i["IntentConfig"]["prompts"]["validationPrompt"]:
                    fail(20, f"{ident}: fixed outcome value not pinned verbatim in validationPrompt")

    # 21 ParameterType dictionary byte-match
    for i in ints:
        for p in i["IntentParameters"]:
            t, ptid = p["ParameterType"], p["ParameterTypeId"]
            d = A.PARAM_TYPES[ptid]
            exp = {"Name": d["Name"], "IsActive": 1, "CreatedBy": "SYSTEM", "ModifiedBy": None,
                   "CreatedDate": d["CreatedDate"], "Description": d["Description"],
                   "ModifiedDate": None, "ParameterTypeId": ptid,
                   "ValidationPattern": d["ValidationPattern"],
                   "IsCustomValidationAllowed": d["IsCustomValidationAllowed"]}
            if t != exp:
                fail(21, f"{i['IntentToolName']}.{p['Name']}: ParameterType mismatch")

    # 22 authored edges into type-2 globals (advisory)
    g2 = {b["IntentId"] for b in il["botIntents"] if b["BotIntentTypeID"] == 2}
    for r in il["intentRelations"]:
        if r["NextIntentID"] in g2:
            fail(22, f"relation into type-2 global {ident_of[r['NextIntentID']]}")

    # 23 off-topic global present (advisory)
    ot = [i for i in ints if i["IntentId"] in g2 and i["IntentResponces"]["ResponseTypeId"] == 1
          and re.search(r"(?i)unrelated|off.topic|לא קשור", i["Description"] + i["Name"])]
    if not ot:
        fail(23, "no off-topic type-2 RT=1 terminal found")
    elif not re.search(r"(?i)unrelated|off.topic", pr["persona"]):
        fail(23, "persona carries no off-topic rule")

    # 24 turn-yield gating
    for i in ints:
        rt = i["IntentResponces"]["ResponseTypeId"]
        if rt not in (2, 3):
            continue
        an = s4[i["IntentToolName"]].get("asks_next")
        if an and an.startswith("[none"):
            if i["IntentResponces"]["Configuration"].get("announcement", "") != "":
                fail(24, f"{i['IntentToolName']}: auto-chaining but announcement non-empty")
            if re.search(r"(?i)(stop and wait|wait for (the customer|their|a) (explicit )?(answer|response))",
                         str(i["IntentResponces"]["Configuration"].get("intentInstructions", ""))):
                fail(24, f"{i['IntentToolName']}: ADVISORY wait rule on auto-chaining intent")

    # 26 layer fields are integers — bool is a subclass of int, so reject it first.
    def _int(v):
        return isinstance(v, int) and not isinstance(v, bool)

    avm = bot["ActiveVersionInfo"]["AIModelConfig"]
    for k in ("dailyLimitLayerId", "maxDurationLayerId", "IVRLayerSelect_2"):
        if k in avm and not _int(avm[k]):
            fail(26, f"ActiveVersionInfo.AIModelConfig.{k} = {avm[k]!r} "
                     f"({type(avm[k]).__name__}) — must be a JSON integer")
    for i in ints:
        r = i["IntentResponces"]
        cfg, rt, tn = r["Configuration"], r["ResponseTypeId"], i["IntentToolName"]
        if rt == 1 and not _int(cfg.get("layer")):
            fail(26, f"{tn}: Configuration.layer = {cfg.get('layer')!r} "
                     f"({type(cfg.get('layer')).__name__}) — must be a JSON integer")
        if rt == 4 and "NEXT_VO_ID" in cfg and not _int(cfg["NEXT_VO_ID"]):
            fail(26, f"{tn}: Configuration.NEXT_VO_ID = {cfg['NEXT_VO_ID']!r} "
                     f"({type(cfg['NEXT_VO_ID']).__name__}) — must be a JSON integer")

    # 27 placeholder IDs present and unique — the five lists the importer keys by ID.
    # The import refuses the whole file (import_placeholder_clash) on either problem.
    id_lists = [
        ("intentCategories", "IntentCategoryId", il["intentCategories"]),
        ("intents", "IntentId", ints),
        ("intents[].IntentParameters", "ParameterId",
         [p for i in ints for p in i["IntentParameters"]]),
        ("botIntents", "BotIntentId", il["botIntents"]),
        ("intentRelations", "IntentRelatedID", il["intentRelations"]),
    ]
    for lst, fld, items in id_lists:
        seen_ids = set()
        for idx, item in enumerate(items):
            v = item.get(fld)
            if not _int(v):
                fail(27, f"{lst}[{idx}].{fld} = {v!r} — missing")
            elif v in seen_ids:
                fail(27, f"{lst}[{idx}].{fld} {v} — repeated")
            else:
                seen_ids.add(v)

    # 28 bot status in range and equal to the spec's choice (default 1).
    st = bot.get("BotStatusId")
    want = int(spec["identity"].get("Bot status") or 1)
    if not _int(st) or st not in (1, 2, 3):
        fail(28, f"BotStatusId = {st!r} — must be 1, 2 or 3")
    elif st != want:
        fail(28, f"BotStatusId {st} != spec Bot status {want}")

    run_helper_checks(il, ids, fail, _int)

    # 8/9 token estimate (§6.2 check 8 specifics)
    top_created = bot["AiModelConfig"]["AIModelConfig"].get("created", {})
    gated = top_created.get("model") == "models/gemini-3.1-flash-live-preview"
    vac = bot["ActiveVersionInfo"]["AIModelConfig"]
    txt = pr["persona"] + pr["voiceInstructions"] + pr["intentInstructions"]
    for i in ints:
        txt += i["IntentConfig"]["prompts"]["validationPrompt"]
        txt += str(i["IntentResponces"]["Configuration"].get("intentInstructions", ""))
    tok = 0
    for ch in txt:
        tok += 1 / 1.5 if unicodedata.category(ch)[0] == "L" and ord(ch) > 0x400 else 0.25
    tok = int(tok + 0.999)
    if gated and tok >= 5000:
        fail(8, f"token estimate {tok} >= 5000 enforcement ceiling")

    # 10 model-config doctrine, ElevenLabs family (v1.23.0) — not [GL3.1]-gated.
    # Shape from production export BotID 37437 v0.1.149.
    mname = bot["AiModelConfig"].get("Name")
    mc = A.MODEL_CATALOG.get(mname, {})
    if mc.get("family") == "tts":
        if bot["AiModelConfig"]["AIModelConfig"] != {}:
            fail(10, "ElevenLabs: AiModelConfig.AIModelConfig must be an empty object")
        if "created" in vac:
            fail(10, "ElevenLabs: version-level `created` present — ElevenLabs carries `tts` instead")
        if "voice" in spec["identity"].get("Channels Active", ""):
            voice = vac.get("tts", {}).get("speak", {}).get("voice")
            if not voice:
                fail(10, "ElevenLabs: tts.speak.voice missing on a voice bot")
            elif voice != spec["identity"].get("Voice Name"):
                fail(10, f"ElevenLabs: tts.speak.voice {voice!r} != spec Voice Name")
        if not isinstance(vac.get("recordAgentCalls"), bool):
            fail(10, "ElevenLabs: recordAgentCalls must be a JSON boolean")

    # 10 model-config doctrine, Voicenter Voicebot - Gemini (387, v1.23.2) — not
    # [GL3.1]-gated. Shape from production export BotID 37428 v0.1.151.
    if mc.get("family") == "voicenter-gemini":
        if bot["AiModelConfig"]["AIModelConfig"] != {}:
            fail(10, "Voicenter Gemini: AiModelConfig.AIModelConfig must be an empty object")
        if "tts" in vac:
            fail(10, "Voicenter Gemini: `tts` present — the voice goes in created.generationConfig")
        created = vac.get("created", {})
        extra = sorted(set(created) - {"generationConfig"})
        if extra:
            fail(10, f"Voicenter Gemini: created carries {extra} — only generationConfig is allowed")
        if "voice" in spec["identity"].get("Channels Active", ""):
            voice = (created.get("generationConfig", {}).get("speechConfig", {})
                     .get("voiceConfig", {}).get("prebuiltVoiceConfig", {}).get("voiceName"))
            if not voice:
                fail(10, "Voicenter Gemini: prebuiltVoiceConfig.voiceName missing on a voice bot")
            elif voice != spec["identity"].get("Voice Name"):
                fail(10, f"Voicenter Gemini: voiceName {voice!r} != spec Voice Name")
        if not isinstance(vac.get("recordAgentCalls"), bool):
            fail(10, "Voicenter Gemini: recordAgentCalls must be a JSON boolean")

    # 10 model-config doctrine (inverted — dropped fields must be absent)
    if gated:
        gc = bot["ActiveVersionInfo"]["AIModelConfig"]["created"].get("generationConfig", {})
        for k in ("temperature", "topP", "topK", "responseModalities", "proactivity",
                  "proactiveAudio", "thinkingConfig", "affectiveDialog"):
            if k in gc:
                fail(10, f"generationConfig.{k} present — v1.5.0 lean payload omits")
        for k in ("systemInstruction", "tools"):
            if k in bot["ActiveVersionInfo"]["AIModelConfig"]["created"]:
                fail(10, f"created.{k} present — v1.5.0 lean payload omits")

    # 25 persona derivation (blocking) — runs last, per the procedure file's run order.
    # Skipped against the frozen v1.17.0 baseline, which predates the field; a skipped
    # model/baseline-gated check is still reported as a row.
    if A.WIRE_BASELINE == "1.17.0":
        skipped.append((25, "pre-dates ActiveVersionInfo.PersonaID (frozen v1.17.0 baseline)"))
    else:
        lang = spec["identity"].get("Primary Language") or ""
        subtag = lang.split("-")[0].strip().lower()
        expected = (A.persona_id(lang, spec["identity"].get("Agent Gender"))
                    if subtag in A.PERSONA_BY_LANG else None)
        pid = bot["ActiveVersionInfo"].get("PersonaID")
        if expected is None:
            fail(25, f"primary language {lang!r} (subtag {subtag!r}) has no Persona row in "
                     f"assembly-mapping.md D.12 — Skill 3 should have halted at assembly")
        elif pid is None:
            fail(25, "ActiveVersionInfo.PersonaID absent or null — the proc would fall back "
                     "to the first AccountId=0 Persona row (contract R7)")
        elif pid != expected:
            why = PERSONA_NEVER_EMITTED.get(pid)
            note = f" — {why}, a known row v1 never emits" if why else ""
            fail(25, f"PersonaID {pid} does not match the row derived from Primary Language "
                     f"{lang!r}: expected {expected}{note}. A wrong-but-valid FK imports "
                     f"cleanly and ships a bot speaking in the wrong voice.")

    return fails, tok, gated, skipped


# CHK-29…CHK-39 (v1.25.0) — helpers and tools, voicebot-json-contract.md §8. Every
# failure below is one the import answers with a bare 500 and stores nothing, or drops
# silently; none is refused with a reason.
TOOL_TYPES_IN_FILE = {1: "MCP", 10: "WebAPI", 13: "Database"}
TOOL_TYPES_DEFERRED = {4: "Email", 7: "SMS", 16: "FileStorage"}
OPERATORS = {1, 4, 7, 10, 13, 16, 19, 22, 48}
CRED_MARKER = re.compile(r"^<USER_TO_FILL: credential\b[^>]*>$")
CRED_LIKE = re.compile(
    r"(?i)(\bauthorization\b|\bbearer\s+\S|\bbasic\s+[A-Za-z0-9+/=]{8,}|x-api-key|api[-_ ]?key"
    r"|access[-_ ]?token|\btoken[\"']?\s*[:=]|secret|passw(?:or)?d|\bpwd\s*=|cookie"
    r"|://[^/\s:@]+:[^/\s@]+@)")
CRED_CONFIGS = {33: "AuthToken", 39: "ConnectionString"}


def run_helper_checks(il, intent_ids, fail, _int):
    subs = il.get("subAgents", [])
    tls = il.get("subAgentTools", [])
    if "subAgents" not in il and "subAgentTools" not in il:
        return

    def s(v):
        return isinstance(v, str)

    # 29 labels present and unique
    for lst, fld, items in (("subAgents", "SubAgentID", subs), ("subAgentTools", "ToolId", tls)):
        seen = set()
        for i, item in enumerate(items):
            v = item.get(fld)
            if not _int(v):
                fail(29, f"{lst}[{i}].{fld} = {v!r} — missing")
            elif v in seen:
                fail(29, f"{lst}[{i}].{fld} {v} — repeated")
            else:
                seen.add(v)
    tool_ids = {t.get("ToolId") for t in tls}
    tool_name = {t.get("ToolId"): t.get("ToolName") for t in tls}

    for h, sub in enumerate(subs):
        where = f"subAgents[{h}]"
        # 30 assignments point at a tool of this file, once per helper
        seen = set()
        for a, asg in enumerate(sub.get("ToolAssignments", [])):
            v = asg.get("ToolId")
            if not _int(v) or v not in tool_ids:
                fail(30, f"{where}.ToolAssignments[{a}].ToolId {v!r} is not a subAgentTools label")
            elif v in seen:
                fail(30, f"{where}.ToolAssignments[{a}].ToolId {v} — assigned twice")
            else:
                seen.add(v)
        # 31 intents: the file's own intent labels, at least one, none repeated
        iids = sub.get("IntentIds")
        if not isinstance(iids, list) or not iids:
            fail(31, f"{where}.IntentIds empty or missing — the helper would serve no intent")
        else:
            seen = set()
            for v in iids:
                if not _int(v) or v not in intent_ids or v >= 0:
                    fail(31, f"{where}.IntentIds {v!r} is not a label of the file's intents")
                elif v in seen:
                    fail(31, f"{where}.IntentIds {v} — repeated")
                else:
                    seen.add(v)
        # 32 helper fields
        nm = sub.get("SubAgentName")
        if not s(nm) or not nm.strip():
            fail(32, f"{where}.SubAgentName missing")
        elif len(nm) > 100:
            fail(32, f"{where}.SubAgentName is {len(nm)} characters — at most 100")
        if not s(sub.get("SubAgentTitle", "")) or len(sub.get("SubAgentTitle", "")) > 255:
            fail(32, f"{where}.SubAgentTitle not a string of at most 255 characters")
        for k in ("SubAgentDescription", "Instruction"):
            if not s(sub.get(k, "")):
                fail(32, f"{where}.{k} not a string")
        m = sub.get("AiModelId")
        if not _int(m) or (m <= 0 and m != -999):
            fail(32, f"{where}.AiModelId = {m!r} — must be an AI model ID (or the -999 sentinel)")
        if sub.get("SubAgentStatusID", 1) not in (1, 2) or isinstance(sub.get("SubAgentStatusID"), bool):
            fail(32, f"{where}.SubAgentStatusID = {sub.get('SubAgentStatusID')!r} — must be 1 or 2")
        # 35 conditions complete
        for a, asg in enumerate(sub.get("ToolAssignments", [])):
            for c, cond in enumerate(asg.get("ConditionList", []) or []):
                p = f"{where}.ToolAssignments[{a}].ConditionList[{c}]"
                if not _int(cond.get("Parameter")):
                    fail(35, f"{p}.Parameter = {cond.get('Parameter')!r} — must be a source parameter ID")
                if cond.get("OperatorID") not in OPERATORS or isinstance(cond.get("OperatorID"), bool):
                    fail(35, f"{p}.OperatorID = {cond.get('OperatorID')!r} — not an operator")
                if not s(cond.get("Value")):
                    fail(35, f"{p}.Value = {cond.get('Value')!r} — must be present")
        # 39 the instruction names every assigned tool exactly
        ins = sub.get("Instruction") or ""
        for asg in sub.get("ToolAssignments", []):
            tn = tool_name.get(asg.get("ToolId"))
            if s(tn) and not re.search(rf"(?<![\w-]){re.escape(tn)}(?![\w-])", ins):
                fail(39, f"{where} ({nm}): Instruction does not name its tool {tn!r}")

    names = {}
    for t, tool in enumerate(tls):
        where = f"subAgentTools[{t}]"
        # 33 tool fields
        tn = tool.get("ToolName")
        if not s(tn) or not tn.strip():
            fail(33, f"{where}.ToolName missing")
        elif len(tn) > 100:
            fail(33, f"{where}.ToolName is {len(tn)} characters — at most 100")
        elif tn.lower() in names:
            fail(33, f"{where}.ToolName {tn!r} repeats {names[tn.lower()]}")
        else:
            names[tn.lower()] = where
        if not s(tool.get("ToolDisplayName", "")) or len(tool.get("ToolDisplayName", "")) > 200:
            fail(33, f"{where}.ToolDisplayName not a string of at most 200 characters")
        ty = tool.get("ToolTypeId")
        if ty not in TOOL_TYPES_IN_FILE and ty not in TOOL_TYPES_DEFERRED or isinstance(ty, bool):
            fail(33, f"{where}.ToolTypeId = {ty!r} — not a tool type")
        for k, ok in (("ToolExecutionTypeID", (1, 2)), ("ToolStatusID", (1, 2, 3)),
                      ("ToolRiskTypeID", (1, 2, 3, 4))):
            if k in tool and (tool[k] not in ok or isinstance(tool[k], bool)):
                fail(33, f"{where}.{k} = {tool[k]!r} — must be one of {ok}")
        if "ParameterSchemaJson" in tool and tool.get("ToolExecutionTypeID", 1) != 2:
            fail(33, f"{where}: ParameterSchemaJson on a tool whose ToolExecutionTypeID is not 2 (AI)")
        if "TemplateId" in tool:
            fail(33, f"{where}.TemplateId present — the import keeps only global templates; omit it")
        vn = (tool.get("ToolVersion") or {}).get("VersionNumber", "1.0.0")
        if not s(vn) or len(vn) > 20:
            fail(33, f"{where}.ToolVersion.VersionNumber {vn!r} — a string of at most 20 characters")
        # 36 credential-only tool types are never in the file
        if ty in TOOL_TYPES_DEFERRED:
            fail(36, f"{where} {tn!r}: type {ty} ({TOOL_TYPES_DEFERRED[ty]}) needs a credential — "
                     f"the import drops it; it is added after the import")

    # 34 parameter lists, 38 credentials — tool level and assignment level
    lists = [(f"subAgentTools[{t}]", tool.get("Parameters", []), tool) for t, tool in enumerate(tls)]
    lists += [(f"subAgents[{h}].ToolAssignments[{a}]", asg.get("Parameters", []), None)
              for h, sub in enumerate(subs) for a, asg in enumerate(sub.get("ToolAssignments", []))]
    for where, params, tool in lists:
        if not isinstance(params, list):
            fail(34, f"{where}.Parameters is not a list")
            continue
        props = set(((tool or {}).get("ParameterSchemaJson") or {}).get("properties", {}))
        seen, filled = set(), set()
        for p, prm in enumerate(params):
            pw = f"{where}.Parameters[{p}]"
            pn = prm.get("ParameterName")
            if not s(pn) or not pn.strip() or len(pn) > 255:
                fail(34, f"{pw}.ParameterName {pn!r} — a name of at most 255 characters")
            elif pn in seen:
                fail(34, f"{pw}.ParameterName {pn!r} — twice in one list")
            else:
                seen.add(pn)
            src, cfg_id = prm.get("ToolParameterSourceID"), prm.get("ToolTypeConfigID")
            cfg = prm.get("Config") if isinstance(prm.get("Config"), dict) else {}
            if src not in (1, 2, 3, 4, 5) or isinstance(src, bool):
                fail(34, f"{pw}.ToolParameterSourceID = {src!r} — not a parameter source")
            if src == 1:
                if cfg_id is not None:
                    fail(34, f"{pw}: an AI argument carries ToolTypeConfigID {cfg_id!r} — must be null")
                sf = cfg.get("source_filed")
                if tool is not None and sf not in props:
                    fail(34, f"{pw}.Config.source_filed {sf!r} is not an argument of ParameterSchemaJson")
                filled.add(sf)
            elif not _int(cfg_id):
                fail(34, f"{pw}.ToolTypeConfigID = {cfg_id!r} — a setting needs its config ID")
            if src == 5 and not s(cfg.get("value")):
                fail(34, f"{pw}.Config.value must be a string")
            # 38 nothing that looks like a credential
            for k, v in cfg.items():
                if not s(v) or CRED_MARKER.match(v):
                    continue
                if v.strip() == "****":
                    fail(38, f"{pw}.Config.{k} is a masked export secret '****' — record the setting "
                             f"as to set after the import")
                elif cfg_id in CRED_CONFIGS:
                    fail(38, f"{pw} ({CRED_CONFIGS[cfg_id]}) holds a value — a credential is never "
                             f"written into the file")
                elif CRED_LIKE.search(v):
                    fail(38, f"{pw}.Config.{k} looks like a credential: "
                             f"{CRED_LIKE.search(v).group(0)!r}")
        for missing in sorted(props - filled):
            fail(34, f"{where}: argument {missing!r} of ParameterSchemaJson has no AI parameter")

    # 37 no stray null — only an AI argument's ToolTypeConfigID may be null
    def nulls(o, path):
        if isinstance(o, dict):
            for k, v in o.items():
                if v is None:
                    if not (k == "ToolTypeConfigID" and o.get("ToolParameterSourceID") == 1):
                        fail(37, f"{path}.{k} is null")
                else:
                    nulls(v, f"{path}.{k}")
        elif isinstance(o, list):
            for i, v in enumerate(o):
                if v is None:
                    fail(37, f"{path}[{i}] is null")
                nulls(v, f"{path}[{i}]")
    nulls(subs, "subAgents")
    nulls(tls, "subAgentTools")


def build_spec_context(raw):
    """Parse a spec and attach the section-4/4.5 context the checks consult."""
    spec = A.parse_spec(raw)
    v = raw.split("## 4.5 Available Variables")[1].split("## 4.6")[0]
    spec["_45_1"] = v.split("### 4.5.1")[1].split("###")[0]
    spec["_45_2"] = v.split("### 4.5.2")[1].split("###")[0]
    spec["_45_4"] = v.split("### 4.5.4")[1].split("###")[0]
    spec["_45_5"] = v.split("### 4.5.5")[1].split("###")[0] if "### 4.5.5" in v else ""
    sec4 = raw.split("## 4. Intent List (Structural)")[1].split("## 4.5")[0]
    spec["_terminal_outcome"] = {}
    for blk in re.split(r"\n### Intent \d+: ", sec4)[1:]:
        t = A.field(blk, "Terminal outcome")
        if t:
            spec["_terminal_outcome"][blk.split("\n")[0].strip()] = t
    return spec


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "--wire-baseline=1.17.0" in sys.argv:
        A.WIRE_BASELINE = "1.17.0"
    spec_path, json_path = args[0], args[1]
    spec = build_spec_context(open(spec_path, encoding="utf-8").read())
    bot = json.load(open(json_path, encoding="utf-8"))

    fails, tok, gated, skipped = run(spec, bot)
    blocking = sorted(n for n in fails if n in BLOCKING
                      and not all("ADVISORY" in m for m in fails[n]))
    ran = len(NAMES) - len(skipped)
    print(f"Token estimate: {tok} tok (checks 8/9/10 {'FIRE' if gated else 'skip'})")
    print(f"Checks run: {ran} | failed: {len(fails)} | blocking: {len(blocking)}\n")
    for n in sorted(fails):
        sev = "BLOCKING" if n in blocking else "advisory"
        print(f"Check {n} [{sev}] — {NAMES[n]}")
        for m in fails[n]:
            print(f"    - {m}")
    for n, why in skipped:
        print(f"Check {n} [skipped]  — {NAMES[n]}: {why}")
    if not fails:
        print(f"ALL {ran} CHECKS PASS — assembly may proceed to §7 emission.")
    return 1 if blocking else 0


if __name__ == "__main__":
    sys.exit(main())
