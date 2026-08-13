#!/usr/bin/env python3
"""Mechanical transcription of Skill 3 §6 — the 25-check cross-reference pass.

Implements the detections in Skill 3 SKILL.md §6.2, run against the assembled
wire structure (plus the spec, which checks 16-24 additionally consult).

Used twice in S0: to confirm F1 assembles clean, and to record which checks fire
on the F2 seeded fixture (the v1.17.0 detection baseline that V-C3/V-C4/V-A2
compare against).

Run order per §6.1: 1-7, 11-13, 15, 16-21, 22-24, then 8, 9, 10, 14, 25.
Blocking per §6: 1-7, 11-13, 15, 16-21, 24(announcement half). 8 is banded.
9, 14, 22, 23, 25 advisory; 10 blocking on mismatch.

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

BLOCKING = {1, 2, 3, 4, 5, 6, 7, 11, 12, 13, 15, 16, 17, 18, 19, 20, 21, 24}
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
    25: "Persona FK sanity (contract R7/R11)",
}

# Appendix D.12 — the only known shared Persona row (AccountId=0).
PERSONA_WHITELIST = {3}

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

    # 8/9 token estimate (§6.2 check 8 specifics)
    gated = bot["AiModelConfig"]["AIModelConfig"]["created"]["model"] == "models/gemini-3.1-flash-live-preview"
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

    # 25 persona FK sanity (advisory) — runs last, per the procedure file's run order.
    # Skipped against the frozen v1.17.0 baseline, which predates the field; a skipped
    # model/baseline-gated check is still reported as a row.
    if A.WIRE_BASELINE == "1.17.0":
        skipped.append((25, "pre-dates ActiveVersionInfo.PersonaID (frozen v1.17.0 baseline)"))
    else:
        pid = bot["ActiveVersionInfo"].get("PersonaID")
        if pid is None:
            fail(25, "ActiveVersionInfo.PersonaID absent or null — the proc would fall back "
                     "to the first AccountId=0 Persona row (contract R7)")
        elif pid not in PERSONA_WHITELIST:
            fail(25, f"PersonaID {pid} outside known shared whitelist "
                     f"{sorted(PERSONA_WHITELIST)} — confirm the row exists on the target account")

    return fails, tok, gated, skipped


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
    ran = 25 - len(skipped)
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
