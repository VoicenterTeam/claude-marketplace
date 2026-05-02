"""Skill 3 mechanical projection of test-bot-spec-refua.md.
Critical differences from Yuval:
- silence_behaviour OMITTED (section 3 = [not configured]) per Skill 3 §4.2.5
- voice channel only → chat instructions are templated default
- 6 dotted paths in get_nearest_collection_points apiResponseAnnouncement
"""
import json
from collections import OrderedDict

TS = "2026-05-01 00:00:00"
BOT_ID, BOT_VERSION_ID, INTENT_CATEGORY_ID = -1, -2, -3

IDS = {
    "validate_customer_address":     (-10, -100),
    "get_nearest_collection_points": (-11, -101),
    "confirm_pickup_point":          (-12, -102),
    "report_issue":                  (-13, -103),
    "general_inquiry":               (-14, -104),
    "transfer_to_human":             (-15, -105),
}
PARAM_IDS = {
    ("validate_customer_address", "address"):           -1000,
    ("confirm_pickup_point",      "selected_slot_id"):  -1001,
    ("report_issue",              "issue_description"): -1002,
    ("general_inquiry",           "question"):          -1003,
}
def intent_id(n): return IDS[n][0]
def bot_intent_id(n): return IDS[n][1]

PERSONA = """את הקול של חברים לרפואה. את עוזרת לחברי הקופה למצוא נקודות איסוף
קרובות, ולאשר איסוף תרופות.
את לא נותנת ייעוץ רפואי, לא משנה תרופות, לא מאשרת מרשמים —
אלה תפקידים של רוקח/ית מורשה.
ספק רפואי מצריך הפניה לנציג."""

VOICE_INSTRUCTIONS = """[default — not user-authored]

You are speaking as הקול של חברים לרפואה. Maintain the same identity and tone as defined in the global persona.

Voice-channel guidelines:

1. Speak clearly and at a measured pace. Avoid speaking too fast.
2. Pronounce names, numbers, and addresses carefully. Confirm them back to the caller when collected.
3. If the caller interrupts, stop speaking immediately and listen.
4. Avoid long pauses. If you need a moment to look something up, say so explicitly ("Give me a moment to check that...").
5. Use Hebrew only. Do not switch languages mid-call unless the caller does.

This is a generated default. If the user later activates voice as a primary channel, regenerate this section through Skill 1 patch mode (channel scope expansion)."""

CHAT_INSTRUCTIONS = """[default — not user-authored]

You are speaking as הקול של חברים לרפואה. Maintain the same identity and tone as defined in the global persona.

Chat-channel guidelines:

1. Use clear, short sentences. Avoid long paragraphs.
2. Use numbered lists when presenting options.
3. Avoid emojis unless the caller uses them first.
4. Hebrew only. Do not switch languages mid-conversation unless the caller does."""

OPENING_BEHAVIOR = """OPENING BEHAVIOR
1. ברכי קצרות.
2. הקשיבי לבקשה.
3. אם הלקוח מחפש נקודת איסוף: validate_customer_address.
4. אם בעיה עם הזמנה: report_issue.
5. אם שאלה כללית: general_inquiry.
6. אם לא ברור: transfer_to_human.

IRON RULE: לא לתת ייעוץ רפואי בשום מצב."""

OPENING_ANNOUNCEMENT = "שלום, אני כאן מטעם חברים לרפואה. איך אוכל לעזור?"

PARAM_TYPE_NAME = {1: "STRING", 10: "PHONE", 16: "BOOLEAN", 19: "ENUM"}

SLOTS = {
    "validate_customer_address": [
        ("address", 1, True, 1, [], "כתובת מלאה: רחוב, מספר בית, עיר."),
    ],
    "get_nearest_collection_points": [],
    "confirm_pickup_point": [
        ("selected_slot_id", 19, True, 1, [], "הלקוח בוחר אחת מנקודות האיסוף שהוצעו."),
    ],
    "report_issue": [
        ("issue_description", 1, True, 1, [], "תיאור הבעיה של הלקוח עם ההזמנה."),
    ],
    "general_inquiry": [
        ("question", 1, True, 1, [], "השאלה הכללית של הלקוח."),
    ],
    "transfer_to_human": [],
}

VALIDATION_PROMPTS = {
    "validate_customer_address": """ADDRESS COLLECTION
1. בקשי כתובת מלאה (רחוב, מספר, עיר).
2. חזרי על הכתובת לאישור.
3. שמרי {{address}} רק אחרי אישור.

IRON RULE: לא ממשיכה ללא רחוב + מספר + עיר.""",
    "get_nearest_collection_points": """PRE-EXECUTION
1. ודאי שהכתובת ב-{{address}} זמינה ואומתה.
2. אם לא — אל תפעילי, חזרי ל-transfer_to_human.

IRON RULE: אסור להפעיל את ה-API בלי כתובת מאומתת.""",
    "confirm_pickup_point": """PICKUP SELECTION
1. הקשיבי לבחירה של הלקוח.
2. אם הבחירה ברורה — שמרי {{selected_slot_id}}.
3. אם לא ברור — חזרי על שלוש האפשרויות.

IRON RULE: לא לשמור slot_id לפני אישור הלקוח.""",
    "report_issue": """ISSUE COLLECTION
1. בקשי מהלקוח לתאר את הבעיה.
2. הקשיבי בלי להפריע.
3. שמרי את התיאור ב-{{issue_description}}.

IRON RULE: אל תנסי לפתור את הבעיה בעצמך — תעבירי לנציג עם הקשר.""",
    "general_inquiry": """GENERAL INQUIRY
1. הקשיבי לשאלה.
2. שמרי {{question}}.

IRON RULE: אל תיתני ייעוץ רפואי. רובן של השאלות → transfer_to_human.""",
    "transfer_to_human": "",
}

POST_EXEC = {
    "validate_customer_address": """POST-EXECUTION (address validated)
1. הזיזי את השיחה ל-get_nearest_collection_points.
2. אם valid=false: אמרי שהכתובת לא באזור שירות והעבירי לנציג.""",
    "get_nearest_collection_points": """POST-EXECUTION (pickup points returned)
1. הציגי את שלוש הנקודות עם המרחק.
2. עברי ל-confirm_pickup_point.""",
    "confirm_pickup_point": """POST-EXECUTION (pickup confirmed)
1. אם הלקוח שואל על משהו אחר — transfer_to_human.
2. אחרת — סיימי בנימוס.""",
    "report_issue": """POST-EXECUTION
1. תמיד עברי ל-transfer_to_human.""",
    "general_inquiry": """POST-EXECUTION
1. תמיד עברי ל-transfer_to_human.""",
}

RT2_CONFIGS = {
    "validate_customer_address": {
        "url": "https://connector.center/refua/validate-address",
        "method": "POST",
        "headers": {},
        "body": {"address": "{{address}}"},
        "apiResponseAnnouncement": "הכתובת אומתה. מחפשת נקודות איסוף קרובות...",
        "fail_output": "אני לא מצליחה לאמת את הכתובת. אעבירך לנציג.",
        "function_output": "Returns { valid: bool, service_area: string }. If valid=true proceed to get_nearest_collection_points; if valid=false transfer.",
        "loading_announcement": "רגע, בודקת...",
        "silence_duration": 8, "silence_loops": 5,
        "silence_sentence": "אני עדיין בודקת...",
        "silence_ending_sentence": "השרת לא מגיב. אעבירך לנציג.",
        "silence_instructions": "",
        "fallback_intent": "transfer_to_human",
    },
    "get_nearest_collection_points": {
        "url": "https://connector.center/refua/find-pickup-points",
        "method": "POST",
        "headers": {},
        "body": {"address": "{{address}}", "max_results": 3},
        # Six dotted paths — the stress test
        "apiResponseAnnouncement": ('מצאתי שלוש נקודות איסוף קרובות:\n'
                                    '1. {{available_slots.0.display}} ({{available_slots.0.distance_km}} ק"מ)\n'
                                    '2. {{available_slots.1.display}} ({{available_slots.1.distance_km}} ק"מ)\n'
                                    '3. {{available_slots.2.display}} ({{available_slots.2.distance_km}} ק"מ)\n'
                                    'איזו מהן מתאימה לך?'),
        "fail_output": "אני לא מצליחה למצוא נקודות איסוף כרגע. אעבירך לנציג.",
        "function_output": "Response shape: { available_slots: [{display, slot_id, distance_km}, ...] }. Caller will pick one in confirm_pickup_point intent.",
        "loading_announcement": "רגע, מחפשת נקודות איסוף...",
        "silence_duration": 8, "silence_loops": 5,
        "silence_sentence": "אני עדיין מחפשת...",
        "silence_ending_sentence": "השרת לא מגיב. אעבירך לנציג.",
        "silence_instructions": "",
        "fallback_intent": "transfer_to_human",
    },
}

RT3_ANNOUNCEMENTS = {
    "confirm_pickup_point": "מעולה. בחרת את {{available_slots.0.display}}. נשלח לך SMS עם פרטים.",
    "report_issue": "הבנתי. אעביר אותך לנציג עם פרטי הבעיה.",
    "general_inquiry": "אעביר אותך לנציג שיוכל לעזור עם השאלה.",
}

RT1_CONFIG = {
    "transfer_to_human": {
        "layer": 41,
        "announcement": "אעבירך לרוקח/ית, רגע אחד.",
        "intentLoadingAnnouncement": "מעבירה...",
    },
}

INTENT_ORDER = [
    "validate_customer_address",
    "get_nearest_collection_points",
    "confirm_pickup_point",
    "report_issue",
    "general_inquiry",
    "transfer_to_human",
]

TRANSITIONS = {
    "validate_customer_address":     ["get_nearest_collection_points", "transfer_to_human"],
    "get_nearest_collection_points": ["confirm_pickup_point", "transfer_to_human"],
    "confirm_pickup_point":          ["transfer_to_human"],
    "report_issue":                  ["transfer_to_human"],
    "general_inquiry":               ["transfer_to_human"],
    "transfer_to_human":             [],
}

RT = {
    "validate_customer_address":     2,
    "get_nearest_collection_points": 2,
    "confirm_pickup_point":          3,
    "report_issue":                  3,
    "general_inquiry":               3,
    "transfer_to_human":             1,
}

DISPLAY = {
    "validate_customer_address":     ("אימות כתובת לקוח", "וידוא שהכתובת של הלקוח נמצאת באזור השירות."),
    "get_nearest_collection_points": ("מציאת נקודות איסוף", "איתור שלוש נקודות האיסוף הקרובות ביותר לכתובת הלקוח."),
    "confirm_pickup_point":          ("אישור נקודת איסוף", "הלקוח בוחר אחת מנקודות האיסוף שהוצעו."),
    "report_issue":                  ("דיווח על בעיה", "קבלת תיאור הבעיה בהזמנה והעברה לנציג."),
    "general_inquiry":               ("שאלה כללית", "טיפול בשאלות שאינן קשורות לאיסוף תרופות."),
    "transfer_to_human":             ("העברה לנציג", "העברת השיחה לרוקח/ית או נציג שירות."),
}


def build_created():
    return OrderedDict([
        ("model", "models/gemini-2.5-flash-preview-native-audio-dialog"),
        ("generationConfig", OrderedDict([
            ("temperature", 1.5), ("topP", 0.95), ("topK", 64),
            ("responseModalities", ["AUDIO"]),
            ("speechConfig", OrderedDict([
                ("languageCode", "he-IL"),
                ("voiceConfig", OrderedDict([
                    ("prebuiltVoiceConfig", OrderedDict([("voiceName", "Orus")])),
                ])),
            ])),
            ("proactivity", {}), ("thinkingConfig", {}),
        ])),
        ("systemInstruction", OrderedDict([("parts", [OrderedDict([("text", "")])])])),
        ("tools", []),
    ])


def build_intent_parameters(intent_name):
    out = []
    for slot_name, pt_id, required, order, opt_list, desc in SLOTS[intent_name]:
        out.append(OrderedDict([
            ("ParameterId", PARAM_IDS[(intent_name, slot_name)]),
            ("IntentId", intent_id(intent_name)),
            ("Name", slot_name),
            ("Description", desc),
            ("IsRequired", required),
            ("DefaultValue", None),
            ("CollectionOrder", order),
            ("ParameterTypeId", pt_id),
            ("ParameterType", OrderedDict([("ParameterTypeId", pt_id), ("Name", PARAM_TYPE_NAME[pt_id])])),
            ("OptionList", opt_list),
            ("ValidationRules", {}),
            ("ValidationPattern", None),
            ("IsActive", 1),
            ("IsDeleted", 0),
        ]))
    return out


def build_api_silence_behaviour(intent_name):
    cfg = RT2_CONFIGS[intent_name]
    return OrderedDict([
        ("silence_duration", cfg["silence_duration"]),
        ("silence_loops", cfg["silence_loops"]),
        ("silence_sentence", cfg["silence_sentence"]),
        ("silence_ending_sentence", cfg["silence_ending_sentence"]),
        ("silence_instructions", cfg["silence_instructions"]),
        ("intent", intent_id(cfg["fallback_intent"])),
    ])


def build_intent_responces(intent_name):
    rt = RT[intent_name]
    if rt == 1:
        cfg = RT1_CONFIG[intent_name]
        return OrderedDict([
            ("ResponseTypeId", 1),
            ("Configuration", OrderedDict([
                ("layer", cfg["layer"]),
                ("announcement", cfg["announcement"]),
                ("intentLoadingAnnouncement", cfg["intentLoadingAnnouncement"]),
            ])),
        ])
    if rt == 2:
        cfg = RT2_CONFIGS[intent_name]
        return OrderedDict([
            ("ResponseTypeId", 2),
            ("Configuration", OrderedDict([
                ("url", cfg["url"]), ("method", cfg["method"]),
                ("headers", cfg["headers"]), ("body", cfg["body"]),
                ("apiResponseAnnouncement", cfg["apiResponseAnnouncement"]),
                ("fail_output", cfg["fail_output"]),
                ("function_output", cfg["function_output"]),
                ("intentLoadingAnnouncement", cfg["loading_announcement"]),
                ("IntentLoadingAnnouncement", cfg["loading_announcement"]),  # quirk
                ("intentInstructions", POST_EXEC[intent_name]),
                ("api_silence_behaviour", build_api_silence_behaviour(intent_name)),
                ("response_success", ""),
            ])),
        ])
    if rt == 3:
        return OrderedDict([
            ("ResponseTypeId", 3),
            ("Configuration", OrderedDict([
                ("announcement", RT3_ANNOUNCEMENTS[intent_name]),
                ("intentInstructions", POST_EXEC[intent_name]),
                ("response_success", ""),
            ])),
        ])
    raise ValueError(intent_name)


def build_intent(intent_name):
    name, desc = DISPLAY[intent_name]
    return OrderedDict([
        ("IntentId", intent_id(intent_name)),
        ("Name", name), ("Description", desc),
        ("IntentToolName", intent_name),
        ("HandlingInstructions", None),
        ("IsSilenceIntent", False),
        ("IntentCategoryId", INTENT_CATEGORY_ID),
        ("Priority", 1), ("MaxAttempts", 3), ("ValidationTimeout", 30),
        ("IntentParameters", build_intent_parameters(intent_name)),
        ("IntentConfig", OrderedDict([
            ("prompts", OrderedDict([
                ("llmDescription", ""),
                ("validationPrompt", VALIDATION_PROMPTS[intent_name]),
            ])),
        ])),
        ("IntentScripts", {}),
        ("IntentResponces", build_intent_responces(intent_name)),
        ("IsActive", 1), ("IsDeleted", 0),
    ])


def build_intent_list():
    bot_intents = [
        OrderedDict([
            ("BotIntentID", bot_intent_id(n)),
            ("BotID", BOT_ID),
            ("IntentID", intent_id(n)),
            ("BotIntentTypeID", 1),
            ("ConditionGroupList", []),
        ])
        for n in INTENT_ORDER
    ]
    intent_relations = []
    for origin in INTENT_ORDER:
        for order_idx, target in enumerate(TRANSITIONS[origin], start=1):
            intent_relations.append(OrderedDict([
                ("OriginIntentID", intent_id(origin)),
                ("NextIntentID", intent_id(target)),
                ("IntentRelatedID", intent_id(target)),
                ("Order", order_idx),
                ("ConditionGroupList", []),
            ]))
    api_silence_relations = [
        OrderedDict([
            ("OriginIntentID", intent_id(n)),
            ("ApiSilenceIntentID", intent_id(RT2_CONFIGS[n]["fallback_intent"])),
            ("Configuration", build_api_silence_behaviour(n)),
        ])
        for n in INTENT_ORDER if RT[n] == 2
    ]
    return OrderedDict([
        ("intents", [build_intent(n) for n in INTENT_ORDER]),
        ("botIntents", bot_intents),
        ("intentRelations", intent_relations),
        ("intentCategories", [OrderedDict([
            ("IntentCategoryId", INTENT_CATEGORY_ID),
            ("BotID", BOT_ID),
            ("Name", "Default Category"),
        ])]),
        ("silenceRelations", []),
        ("apiSilenceRelations", api_silence_relations),
    ])


def build_ai_model_config_top():
    return OrderedDict([
        ("AIModelConfigID", -999),
        ("Name", "Gemini Live"),
        ("Description", "Production reference. Used by Yuval and Refua bots in Doc 1 samples."),
        ("BaseUrl", None),
        ("AIModelTypeId", -999),
        ("Type", OrderedDict([
            ("AIModelTypeId", -999),
            ("Name", "Gemini Live"),
            ("Description", None),
        ])),
        ("created", build_created()),
    ])


def build_ai_model_config_version():
    # KEY DIFFERENCE FROM YUVAL: silence_behaviour is OMITTED entirely
    return OrderedDict([
        ("prompts", OrderedDict([
            ("persona", PERSONA),
            ("voiceInstructions", VOICE_INSTRUCTIONS),
            ("chatInstructions", CHAT_INSTRUCTIONS),
            ("intentInstructions", OPENING_BEHAVIOR),
            ("openingAnnouncement", OPENING_ANNOUNCEMENT),
        ])),
        ("created", build_created()),
        # NO silence_behaviour key — section 3 was [not configured]
        ("tools", []),
        ("instructions", ""),
    ])


def build_active_version_info():
    return OrderedDict([
        ("BotVersionId", BOT_VERSION_ID),
        ("VersionNumber", "0.0.1"),
        ("BotVersionStatusId", 3),
        ("IsActive", 1),
        ("Description", ""),
        ("CreatedDate", TS),
        ("ModifiedDate", None),
        ("SystemPrompt", ""),
        ("AIModelConfigId", -999),
        ("AIModelConfig", build_ai_model_config_version()),
    ])


def build_root():
    return OrderedDict([
        ("Name", "חברים לרפואה"),
        ("BotID", BOT_ID),
        ("AccountID", -999),
        ("Description", "<USER_TO_FILL: bot description>"),
        ("BotStatusId", 1),
        ("BotLanguages", []),
        ("CreatedDate", TS),
        ("ModifiedDate", None),
        ("AiModelConfig", build_ai_model_config_top()),
        ("ActiveVersionInfo", build_active_version_info()),
        ("intentList", build_intent_list()),
    ])


if __name__ == "__main__":
    root = build_root()
    out = json.dumps(root, ensure_ascii=False, indent=2)
    import os
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "test-emitted-json-refua.json"), "w", encoding="utf-8") as f:
        f.write(out)
    print(f"Wrote {len(out)} chars, {out.count(chr(10))+1} lines")
    print(f"silence_behaviour key in version-level AIModelConfig: {'silence_behaviour' in root['ActiveVersionInfo']['AIModelConfig']}")
