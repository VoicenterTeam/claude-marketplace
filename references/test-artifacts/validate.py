"""
Reconstructed validation script per validation-report.md §2.1-2.4.
Asserts §15.4 cross-references, Appendix A quirks, Mustache resolvability, sentinel inventory.

Uses the JSONs emitted by build_yuval.py / build_refua.py.
"""
import json
import os
import re
import sys
from collections import OrderedDict

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "output")

YUVAL = json.load(open(os.path.join(OUT, "test-emitted-json-yuval.json"), encoding="utf-8"))
REFUA = json.load(open(os.path.join(OUT, "test-emitted-json-refua.json"), encoding="utf-8"))


def fail(msg):
    print(f"FAIL: {msg}")
    sys.exit(1)


def header(msg):
    print(f"\n=== {msg} ===")


# Mustache token extractor — works on whole-tree string scan
MUSTACHE_RE = re.compile(r"\{\{([^}]+)\}\}")

def walk_strings(node, path="$"):
    if isinstance(node, str):
        yield path, node
    elif isinstance(node, dict):
        for k, v in node.items():
            yield from walk_strings(v, f"{path}.{k}")
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from walk_strings(v, f"{path}[{i}]")


def find_mustaches(root):
    """Return list of (json_path, token) pairs for every Mustache token in the JSON tree."""
    out = []
    for p, s in walk_strings(root):
        for m in MUSTACHE_RE.finditer(s):
            out.append((p, m.group(1).strip()))
    return out


# Per-bot allowlists from spec section 4.5

def call_context_vars():
    return {"caller_phone", "TimeNow"}


def env_vars():
    return set()  # neither bot declares any


YUVAL_SLOTS = {
    "address": "validate_customer_address",
    "selected_slot_id": "confirm_appointment",
    "existing_appointment_id": "reschedule_existing",
    "reason": "reschedule_existing",
    "question": "general_inquiry",
}
YUVAL_API_RESPONSES = {
    "validate_customer_address": ["valid", "service_area"],
    "get_available_slots": [
        "available_slots",
        "available_slots.0.display", "available_slots.0.slot_id",
        "available_slots.1.display", "available_slots.1.slot_id",
        "available_slots.2.display", "available_slots.2.slot_id",
    ],
}
YUVAL_TRANSITIONS = {
    "validate_customer_address": ["get_available_slots", "transfer_to_human"],
    "get_available_slots":       ["confirm_appointment", "transfer_to_human"],
    "confirm_appointment":       ["general_inquiry", "transfer_to_human"],
    "reschedule_existing":       ["confirm_appointment", "transfer_to_human"],
    "general_inquiry":           ["transfer_to_human"],
    "transfer_to_human":         [],
}

REFUA_SLOTS = {
    "address": "validate_customer_address",
    "selected_slot_id": "confirm_pickup_point",
    "issue_description": "report_issue",
    "question": "general_inquiry",
}
REFUA_API_RESPONSES = {
    "validate_customer_address": ["valid", "service_area"],
    "get_nearest_collection_points": [
        "available_slots",
        "available_slots.0.display", "available_slots.0.slot_id", "available_slots.0.distance_km",
        "available_slots.1.display", "available_slots.1.slot_id", "available_slots.1.distance_km",
        "available_slots.2.display", "available_slots.2.slot_id", "available_slots.2.distance_km",
    ],
}
REFUA_TRANSITIONS = {
    "validate_customer_address":     ["get_nearest_collection_points", "transfer_to_human"],
    "get_nearest_collection_points": ["confirm_pickup_point", "transfer_to_human"],
    "confirm_pickup_point":          ["transfer_to_human"],
    "report_issue":                  ["transfer_to_human"],
    "general_inquiry":               ["transfer_to_human"],
    "transfer_to_human":             [],
}


def reachable_upstream_rt2(target_intent, transitions, intents_by_name):
    """All RT=2 intents from which target_intent is reachable (transitive closure)."""
    upstream = set()
    # reverse graph
    rev = {}
    for src, tgts in transitions.items():
        for t in tgts:
            rev.setdefault(t, []).append(src)
    seen = set()
    stack = [target_intent]
    while stack:
        cur = stack.pop()
        if cur in seen:
            continue
        seen.add(cur)
        for src in rev.get(cur, []):
            if intents_by_name.get(src) == 2:
                upstream.add(src)
            stack.append(src)
    return upstream


# ===== §15.4 Cross-reference checks =====

def check_cross_references(label, root, transitions, slots, api_responses, intents_by_name):
    header(f"{label}: §15.4 cross-reference (7 checks)")
    intent_list = root["intentList"]
    intents = intent_list["intents"]
    bot_intents = intent_list["botIntents"]
    intent_relations = intent_list["intentRelations"]
    api_silence_relations = intent_list["apiSilenceRelations"]
    intent_categories = intent_list["intentCategories"]

    intent_id_to_name = {i["IntentId"]: i["IntentToolName"] for i in intents}
    intent_name_to_id = {v: k for k, v in intent_id_to_name.items()}
    valid_intent_ids = set(intent_id_to_name)
    valid_category_ids = {c["IntentCategoryId"] for c in intent_categories}

    passes = 0

    # 1. botIntents[].IntentID resolves to intents[].IntentId
    for bi in bot_intents:
        if bi["IntentID"] not in valid_intent_ids:
            fail(f"botIntents IntentID {bi['IntentID']} doesn't resolve in intents[]")
    passes += 1
    print(f"  1/7 botIntents IntentID resolves: PASS ({len(bot_intents)} entries)")

    # 2. intentRelations[] both endpoints resolve
    for ir in intent_relations:
        if ir["OriginIntentID"] not in valid_intent_ids:
            fail(f"intentRelations OriginIntentID {ir['OriginIntentID']} doesn't resolve")
        if ir["NextIntentID"] not in valid_intent_ids:
            fail(f"intentRelations NextIntentID {ir['NextIntentID']} doesn't resolve")
        if ir["IntentRelatedID"] not in valid_intent_ids:
            fail(f"intentRelations IntentRelatedID {ir['IntentRelatedID']} doesn't resolve")
    passes += 1
    print(f"  2/7 intentRelations both endpoints resolve: PASS ({len(intent_relations)} edges)")

    # 3. apiSilenceRelations[] both endpoints resolve
    for asr in api_silence_relations:
        if asr["OriginIntentID"] not in valid_intent_ids:
            fail(f"apiSilenceRelations OriginIntentID {asr['OriginIntentID']} doesn't resolve")
        if asr["ApiSilenceIntentID"] not in valid_intent_ids:
            fail(f"apiSilenceRelations ApiSilenceIntentID {asr['ApiSilenceIntentID']} doesn't resolve")
    passes += 1
    print(f"  3/7 apiSilenceRelations both endpoints resolve: PASS ({len(api_silence_relations)} entries)")

    # 4. IntentCategoryId resolves to intentCategories[]
    for i in intents:
        if i["IntentCategoryId"] not in valid_category_ids:
            fail(f"intent {i['IntentToolName']} IntentCategoryId {i['IntentCategoryId']} doesn't resolve")
    passes += 1
    print(f"  4/7 intent.IntentCategoryId resolves: PASS ({len(intents)} intents)")

    # 5. Every RT=2 intent has paired apiSilenceRelations entry
    rt2_origin_ids = {intent_name_to_id[name] for name, rt in intents_by_name.items() if rt == 2}
    asr_origin_ids = {asr["OriginIntentID"] for asr in api_silence_relations}
    if rt2_origin_ids != asr_origin_ids:
        fail(f"RT=2 intents {rt2_origin_ids} != apiSilenceRelations origins {asr_origin_ids}")
    passes += 1
    print(f"  5/7 every RT=2 has paired apiSilenceRelations: PASS ({len(rt2_origin_ids)} pairs)")

    # 6. api_silence_behaviour content is byte-identical to apiSilenceRelations[].Configuration
    asr_by_origin = {asr["OriginIntentID"]: asr for asr in api_silence_relations}
    for i in intents:
        if intents_by_name.get(i["IntentToolName"]) != 2:
            continue
        cfg = i["IntentResponces"]["Configuration"]
        embedded = cfg["api_silence_behaviour"]
        relation = asr_by_origin[i["IntentId"]]["Configuration"]
        if json.dumps(embedded, ensure_ascii=False) != json.dumps(relation, ensure_ascii=False):
            fail(f"intent {i['IntentToolName']} api_silence_behaviour != apiSilenceRelations.Configuration")
    passes += 1
    print(f"  6/7 embedded api_silence_behaviour == apiSilenceRelations.Configuration: PASS")

    # 7. Every Mustache token resolves via 4.5.1 / 4.5.3 / 4.5.4
    mustaches = find_mustaches(root)
    cc = call_context_vars()
    env = env_vars()
    unresolved = []
    for path, tok in mustaches:
        if "." in tok:
            head, *rest = tok.split(".")
            full_path = tok
            # 4.5.4 — only resolves inside the same RT=2 intent's apiResponseAnnouncement
            # OR for any field downstream of an RT=2 intent that declared the path
            # Determine which intent this path belongs to from JSON path.
            m = re.search(r"intents\[(\d+)\]", path)
            owner_intent = None
            if m:
                idx = int(m.group(1))
                owner_intent = intents[idx]["IntentToolName"]
            resolved = False
            # Same-intent declaration in 4.5.4
            if owner_intent in api_responses:
                if full_path in api_responses[owner_intent] or head in api_responses[owner_intent]:
                    resolved = True
            # Upstream RT=2 declaration
            if not resolved and owner_intent:
                for upstream in reachable_upstream_rt2(owner_intent, transitions, intents_by_name):
                    if upstream in api_responses and (full_path in api_responses[upstream] or head in api_responses[upstream]):
                        resolved = True
                        break
            # Slot dotted path? (rare)
            if not resolved and head in slots:
                resolved = True
            if not resolved:
                unresolved.append((path, tok))
        else:
            if tok in cc:
                continue
            if tok in env:
                continue
            if tok in slots:
                continue
            # API response root: same-intent or upstream-RT=2 declaration
            m = re.search(r"intents\[(\d+)\]", path)
            owner_intent = intents[int(m.group(1))]["IntentToolName"] if m else None
            resolved = False
            if owner_intent in api_responses and tok in api_responses[owner_intent]:
                resolved = True
            if not resolved and owner_intent:
                for upstream in reachable_upstream_rt2(owner_intent, transitions, intents_by_name):
                    if upstream in api_responses and tok in api_responses[upstream]:
                        resolved = True
                        break
            if not resolved:
                unresolved.append((path, tok))
    if unresolved:
        for u in unresolved:
            print(f"    UNRESOLVED: {u}")
        fail(f"{label}: {len(unresolved)} unresolved Mustache tokens")
    passes += 1
    print(f"  7/7 every Mustache token resolves: PASS ({len(mustaches)} tokens)")

    print(f"  ->{passes}/7 cross-reference checks PASSED")
    return passes


# ===== Quirk preservation =====

def check_quirks(label, root, expect_silence_omission=False):
    header(f"{label}: Appendix A quirk preservation")
    quirks_passed = 0
    quirks_total = 16 if expect_silence_omission else 15

    intents = root["intentList"]["intents"]

    # #1 IntentResponces typo present
    for i in intents:
        if "IntentResponces" not in i:
            fail(f"#1 IntentResponces typo missing on intent {i['IntentToolName']}")
    quirks_passed += 1
    print(f"  #1 IntentResponces typo: PASS")

    # #2 intentLoadingAnnouncement+IntentLoadingAnnouncement casing pair on RT=2
    for i in intents:
        if i["IntentResponces"]["ResponseTypeId"] == 2:
            cfg = i["IntentResponces"]["Configuration"]
            if "intentLoadingAnnouncement" not in cfg or "IntentLoadingAnnouncement" not in cfg:
                fail(f"#2 casing pair missing on RT=2 intent {i['IntentToolName']}")
    quirks_passed += 1
    print(f"  #2 RT=2 casing-pair (intentLoadingAnnouncement + IntentLoadingAnnouncement): PASS")

    # #3 HandlingInstructions: null on every intent
    for i in intents:
        if i.get("HandlingInstructions", "missing") is not None:
            fail(f"#3 HandlingInstructions not null on {i['IntentToolName']}")
    quirks_passed += 1
    print(f"  #3 HandlingInstructions: null on every intent: PASS")

    # #4 SystemPrompt: ""
    if root["ActiveVersionInfo"].get("SystemPrompt", "missing") != "":
        fail("#4 SystemPrompt is not empty string")
    quirks_passed += 1
    print(f"  #4 SystemPrompt: \"\": PASS")

    # #5 top-level AiModelConfig + version-level AIModelConfig present, both with byte-identical created
    top_created = root["AiModelConfig"]["created"]
    ver_created = root["ActiveVersionInfo"]["AIModelConfig"]["created"]
    if json.dumps(top_created, ensure_ascii=False) != json.dumps(ver_created, ensure_ascii=False):
        fail("#5 created payload differs between top-level and version-level")
    quirks_passed += 1
    print(f"  #5 top-level AiModelConfig + version-level AIModelConfig with byte-identical created: PASS")

    # #6 AIModelConfig.tools: []
    if root["ActiveVersionInfo"]["AIModelConfig"].get("tools", "missing") != []:
        fail("#6 AIModelConfig.tools != []")
    quirks_passed += 1
    print(f"  #6 AIModelConfig.tools: []: PASS")

    # #7 AIModelConfig.instructions: ""
    if root["ActiveVersionInfo"]["AIModelConfig"].get("instructions", "missing") != "":
        fail("#7 AIModelConfig.instructions != \"\"")
    quirks_passed += 1
    print(f"  #7 AIModelConfig.instructions: \"\": PASS")

    # #8 IntentScripts: {}
    for i in intents:
        if i.get("IntentScripts", "missing") != {}:
            fail(f"#8 IntentScripts != {{}} on {i['IntentToolName']}")
    quirks_passed += 1
    print(f"  #8 IntentScripts: {{}}: PASS")

    # #9 ValidationRules: {} per param
    # #10 ValidationPattern: null per param
    for i in intents:
        for p in i.get("IntentParameters", []):
            if p.get("ValidationRules", "missing") != {}:
                fail(f"#9 ValidationRules != {{}} on {i['IntentToolName']}.{p.get('Name')}")
            if p.get("ValidationPattern", "missing") is not None:
                fail(f"#10 ValidationPattern != null on {i['IntentToolName']}.{p.get('Name')}")
    quirks_passed += 2
    print(f"  #9 ValidationRules: {{}} per param: PASS")
    print(f"  #10 ValidationPattern: null per param: PASS")

    # #11 silenceRelations: []
    if root["intentList"].get("silenceRelations", "missing") != []:
        fail("#11 silenceRelations != []")
    quirks_passed += 1
    print(f"  #11 silenceRelations: []: PASS")

    # #12 BotLanguages: []
    if root.get("BotLanguages", "missing") != []:
        fail("#12 BotLanguages != []")
    quirks_passed += 1
    print(f"  #12 BotLanguages: []: PASS")

    # #13 llmDescription: ""
    for i in intents:
        prompts = i.get("IntentConfig", {}).get("prompts", {})
        if prompts.get("llmDescription", "missing") != "":
            fail(f"#13 llmDescription != \"\" on {i['IntentToolName']}")
    quirks_passed += 1
    print(f"  #13 llmDescription: \"\": PASS")

    # #14 response_success: "" on RT=2 and RT=3
    for i in intents:
        rt = i["IntentResponces"]["ResponseTypeId"]
        if rt in (2, 3):
            cfg = i["IntentResponces"]["Configuration"]
            if cfg.get("response_success", "missing") != "":
                fail(f"#14 response_success != \"\" on {i['IntentToolName']} (RT={rt})")
    quirks_passed += 1
    print(f"  #14 response_success: \"\" on RT=2/RT=3: PASS")

    # #15 §16 constants on every intent: Priority=1, MaxAttempts=3, ValidationTimeout=30
    for i in intents:
        if i.get("Priority") != 1:
            fail(f"#15 Priority != 1 on {i['IntentToolName']}")
        if i.get("MaxAttempts") != 3:
            fail(f"#15 MaxAttempts != 3 on {i['IntentToolName']}")
        if i.get("ValidationTimeout") != 30:
            fail(f"#15 ValidationTimeout != 30 on {i['IntentToolName']}")
    quirks_passed += 1
    print(f"  #15 Priority=1 / MaxAttempts=3 / ValidationTimeout=30 (section 16 constants) per intent: PASS")

    # #16 silence_behaviour key behavior — only applies when section 3 configured-ness differs
    # Refua has section 3 [not configured], expects key OMITTED. Yuval has section 3 configured;
    # the "configured" presence is structurally implied (and asserted by quirk #5 created-payload alone is not
    # the silence_behaviour assertion). #16 is Refua-only.
    ver = root["ActiveVersionInfo"]["AIModelConfig"]
    if expect_silence_omission:
        if "silence_behaviour" in ver:
            fail("#16 silence_behaviour key present on Refua but should be omitted")
        quirks_passed += 1
        print(f"  #16 silence_behaviour key OMITTED (section 3 [not configured]): PASS")
    else:
        # Yuval: #16 doesn't apply (section 3 IS configured); confirm the key is present, but don't count it.
        if "silence_behaviour" not in ver:
            fail("Yuval section 3 is configured but silence_behaviour key absent in JSON")
        print(f"  #16 N/A (Yuval has section 3 configured; omission test runs only on Refua)")

    print(f"  ->{quirks_passed}/{quirks_total} quirks PASS")
    return quirks_passed, quirks_total


# ===== Sentinel inventory =====

EXPECTED_SENTINELS = [
    ("AccountID", "$.AccountID", -999),
    ("Description (top-level)", "$.Description", "<USER_TO_FILL: bot description>"),
    ("AiModelConfig.AIModelConfigID", "$.AiModelConfig.AIModelConfigID", -999),
    ("AiModelConfig.AIModelTypeId", "$.AiModelConfig.AIModelTypeId", -999),
    ("AiModelConfig.Type.AIModelTypeId", "$.AiModelConfig.Type.AIModelTypeId", -999),
    ("ActiveVersionInfo.AIModelConfigId", "$.ActiveVersionInfo.AIModelConfigId", -999),
]


def get_path(root, path):
    cur = root
    parts = path.lstrip("$.").split(".")
    for p in parts:
        cur = cur[p]
    return cur


def check_sentinels(label, root):
    header(f"{label}: sentinel inventory (expect 6)")
    found = 0
    for name, path, expected in EXPECTED_SENTINELS:
        actual = get_path(root, path)
        if actual != expected:
            fail(f"sentinel mismatch at {path}: expected {expected!r}, got {actual!r}")
        found += 1
        print(f"  [OK]{name} = {expected!r}")

    # Surplus sentinel scan: any other -999 or <USER_TO_FILL: ...> in tree?
    sentinel_paths = {p for _, p, _ in EXPECTED_SENTINELS}
    surplus = []
    for jp, val in walk_strings(root):
        if isinstance(val, str) and val.startswith("<USER_TO_FILL:"):
            if jp not in sentinel_paths:
                surplus.append((jp, val))
    # Walk again for -999 ints
    def walk_all(node, path="$"):
        if isinstance(node, dict):
            for k, v in node.items():
                yield from walk_all(v, f"{path}.{k}")
        elif isinstance(node, list):
            for i, v in enumerate(node):
                yield from walk_all(v, f"{path}[{i}]")
        else:
            yield path, node
    for jp, val in walk_all(root):
        if val == -999 and jp not in sentinel_paths:
            surplus.append((jp, val))
    if surplus:
        for s in surplus:
            print(f"  SURPLUS sentinel: {s}")
        fail(f"{label}: surplus sentinels found")
    print(f"  ->exactly {found} sentinels (no surplus): PASS")
    return found


# ===== Run =====

YUVAL_INTENTS_BY_NAME = {
    "validate_customer_address": 2,
    "get_available_slots": 2,
    "confirm_appointment": 3,
    "reschedule_existing": 3,
    "general_inquiry": 3,
    "transfer_to_human": 1,
}
REFUA_INTENTS_BY_NAME = {
    "validate_customer_address": 2,
    "get_nearest_collection_points": 2,
    "confirm_pickup_point": 3,
    "report_issue": 3,
    "general_inquiry": 3,
    "transfer_to_human": 1,
}


def main():
    print("\n########## YUVAL ##########")
    yp = check_cross_references("Yuval", YUVAL, YUVAL_TRANSITIONS, YUVAL_SLOTS, YUVAL_API_RESPONSES, YUVAL_INTENTS_BY_NAME)
    yq, yqt = check_quirks("Yuval", YUVAL, expect_silence_omission=False)
    ys = check_sentinels("Yuval", YUVAL)

    print("\n########## REFUA ##########")
    rp = check_cross_references("Refua", REFUA, REFUA_TRANSITIONS, REFUA_SLOTS, REFUA_API_RESPONSES, REFUA_INTENTS_BY_NAME)
    rq, rqt = check_quirks("Refua", REFUA, expect_silence_omission=True)
    rs = check_sentinels("Refua", REFUA)

    print("\n########## SUMMARY ##########")
    print(f"Yuval:  {yp}/7 cross-ref, {yq}/{yqt} quirks, {ys} sentinels")
    print(f"Refua:  {rp}/7 cross-ref, {rq}/{rqt} quirks, {rs} sentinels")
    if yp == 7 and rp == 7 and yq == yqt and rq == rqt and ys == 6 and rs == 6:
        print("\nALL CHECKS PASS")
        sys.exit(0)
    fail("not all checks passed")


if __name__ == "__main__":
    main()
