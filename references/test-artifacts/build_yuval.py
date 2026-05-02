"""
Skill 3 mechanical projection of test-bot-spec-yuval.md.
Applies §4.1 ID allocation, §4.2 wrapper, §4.3 intentList, §4.4 RT-specific Configuration,
§4.5 quirk preservation, §4.6 sentinel emission.
"""
import json
from collections import OrderedDict

# Generation timestamp (deterministic for the test run)
TS = "2026-05-01 00:00:00"

# ID allocations (§4.1)
BOT_ID = -1
BOT_VERSION_ID = -2
INTENT_CATEGORY_ID = -3
IDS = {
    "validate_customer_address": (-10, -100),
    "get_available_slots":       (-11, -101),
    "confirm_appointment":       (-12, -102),
    "reschedule_existing":       (-13, -103),
    "general_inquiry":           (-14, -104),
    "transfer_to_human":         (-15, -105),
}
PARAM_IDS = {
    ("validate_customer_address", "address"):           -1000,
    ("confirm_appointment",       "selected_slot_id"):  -1001,
    ("reschedule_existing",       "existing_appointment_id"): -1002,
    ("reschedule_existing",       "reason"):            -1003,
    ("general_inquiry",           "question"):          -1004,
}

def intent_id(name): return IDS[name][0]
def bot_intent_id(name): return IDS[name][1]

# Persona bundle (verbatim from spec section 2)
PERSONA = """את יובל, נציגת שירות הלקוחות של חברת NC.
את מדברת רק בעברית, בטון מקצועי, סבלני וחם.
את עוזרת ללקוחות בנושא אחד בלבד: קביעת תורי התקנה.
לא מטפלת בחיובים, תקלות טכניות, או שינוי תוכניות —
על אלה את מעבירה לנציג אנושי.
הימנעי מסלנג, אל תשתמשי באנגלית, אל תשערי כאשר את לא בטוחה.
כשלא ברור — שאלי שוב. אם עדיין לא ברור — העבירי לנציג."""

VOICE_INSTRUCTIONS = """דברי בקצב רגוע, עצרי בין משפטים.
הקפידי על הגייה ברורה של שמות רחובות וערים.
אם הלקוח קוטע אותך — עצרי מיד והקשיבי.
הימנעי ממשפטים ארוכים מדי בנשימה אחת.
לפני קריאת מספרים, אמרי 'הקשיבי בבקשה למספר'."""

CHAT_INSTRUCTIONS = """כתבי בעברית ברורה. הימנעי מאימוג'ים.
שורות קצרות, תוכן ממוקד.
רשימות ממוספרות במקום פסקאות ארוכות."""

OPENING_BEHAVIOR = """OPENING BEHAVIOR
1. ברכי קצרות: 'שלום, איך אוכל לעזור?'
2. הקשיבי לבקשה.
3. אם הלקוח רוצה לקבוע התקנה: validate_customer_address.
4. אם רוצה לשנות התקנה קיימת: reschedule_existing.
5. אם שאלה כללית: general_inquiry.
6. אם משהו אחר (חיוב, תקלה, שינוי תוכנית): transfer_to_human.

IRON RULE: אל תנסי לטפל בנושאים מחוץ ל-scope.
אם בספק — שאלי פעם אחת ואז העבירי לנציג."""

OPENING_ANNOUNCEMENT = "שלום, אני יובל מ-NC. איך אוכל לעזור היום?"

# Bot-level silence_behaviour (section 3)
SILENCE_BEHAVIOUR = OrderedDict([
    ("silence_duration", 6),
    ("silence_loops", 3),
    ("silence_sentence", "האם את/ה עדיין שם?"),
    ("silence_ending_sentence", "נראה שיש בעיית קישור, אני סוגרת את השיחה. תוכל לחזור אלינו."),
])

# created payload (§4.2.4) — defaults per Skill 3
def build_created():
    return OrderedDict([
        ("model", "models/gemini-2.5-flash-preview-native-audio-dialog"),
        ("generationConfig", OrderedDict([
            ("temperature", 1.5),
            ("topP", 0.95),
            ("topK", 64),
            ("responseModalities", ["AUDIO"]),
            ("speechConfig", OrderedDict([
                ("languageCode", "he-IL"),
                ("voiceConfig", OrderedDict([
                    ("prebuiltVoiceConfig", OrderedDict([
                        ("voiceName", "Puck"),
                    ])),
                ])),
            ])),
            ("proactivity", {}),
            ("thinkingConfig", {}),
        ])),
        ("systemInstruction", OrderedDict([
            ("parts", [OrderedDict([("text", "")])]),
        ])),
        ("tools", []),
    ])

# Param type denormalization (§4.3.2)
PARAM_TYPE_NAME = {1: "STRING", 10: "PHONE", 16: "BOOLEAN", 19: "ENUM"}

# Slot definitions per intent (slot_name, ParameterTypeId, IsRequired, Order, OptionList, Description)
SLOTS = {
    "validate_customer_address": [
        ("address", 1, True, 1, [], "כתובת מלאה: רחוב, מספר בית, עיר. למשל: רחוב הרצל 14 רמת גן."),
    ],
    "get_available_slots": [],
    "confirm_appointment": [
        ("selected_slot_id", 19, True, 1, [], "הלקוח בוחר אחד מהתורים שהוצעו: {{available_slots}}"),
    ],
    "reschedule_existing": [
        ("existing_appointment_id", 1, True, 1, [], "מזהה התור הקיים שהלקוח רוצה לשנות."),
        ("reason", 1, False, 2, [], "סיבת השינוי (אופציונלי)."),
    ],
    "general_inquiry": [
        ("question", 1, True, 1, [], "השאלה הכללית של הלקוח."),
    ],
    "transfer_to_human": [],
}

# validationPrompt per intent
VALIDATION_PROMPTS = {
    "validate_customer_address": """ADDRESS COLLECTION
1. בקשי מהלקוח כתובת מלאה.
2. ודאי: רחוב, מספר בית, עיר.
3. חזרי על הכתובת לאישור.
4. שמרי ב-{{address}} רק אם הלקוח אישר.

IRON RULE: לא ממשיכה ללא רחוב + מספר + עיר.
אם חסר אחד — שאלי שוב פעם אחת.
אם עדיין חסר — תני fail_output ועברי ל-transfer_to_human.""",
    "get_available_slots": """PRE-EXECUTION
1. ודאי שהכתובת ב-{{address}} זמינה ואומתה ב-validate_customer_address.
2. אם לא — אל תפעילי, חזרי ל-transfer_to_human.

IRON RULE: אסור להפעיל את ה-API בלי כתובת מאומתת.""",
    "confirm_appointment": """SLOT SELECTION
1. הצעי את שלושת התורים שהתקבלו מ-get_available_slots.
2. הקשיבי לבחירה.
3. אם הבחירה ברורה — שמרי {{selected_slot_id}}.
4. אם לא ברור — חזרי על שלושת האפשרויות.

IRON RULE: לא לשמור slot_id לפני אישור הלקוח.""",
    "reschedule_existing": """RESCHEDULE FLOW
1. בקשי מזהה התור הקיים מהלקוח.
2. אם רוצה — בקשי סיבה (אופציונלי).
3. הודיעי שתעבירי לנציג להמשך טיפול.

IRON RULE: ב-v1 הזרימה לא מיושמת בצורה מלאה — תמיד מובילה ל-transfer_to_human.""",
    "general_inquiry": """GENERAL INQUIRY
1. הקשיבי לשאלה.
2. אם השאלה ברורה — שמרי {{question}}.
3. אם לא ברור — שאלי שוב פעם אחת.

IRON RULE: ב-95% מהמקרים זה לא נושא שאני יכולה לטפל בו — אעבירך לנציג.""",
    "transfer_to_human": "",
}

# Post-execution intentInstructions (RT=2 and RT=3 only)
POST_EXEC = {
    "validate_customer_address": """POST-EXECUTION (address validated)
1. הזיזי את השיחה ל-get_available_slots.
2. אם valid=false: אמרי "הכתובת לא באזור שירות שלנו",
   והציעי transfer_to_human.""",
    "get_available_slots": """POST-EXECUTION (slots returned)
1. הציגי את שלושת התורים ועברי ל-confirm_appointment.
2. אם המערך ריק או חסר — אעבירך לנציג.""",
    "confirm_appointment": """POST-EXECUTION (booking confirmed)
1. אם הלקוח שואל על משהו אחר — general_inquiry.
2. אם רוצה לשנות — transfer_to_human (לא חוזרים ל-reschedule).
3. אחרת — סיימי בנימוס.""",
    "reschedule_existing": """POST-EXECUTION
1. תמיד עברי ל-transfer_to_human (v1).
2. confirm_appointment קיים בגרף לצורך גמישות עתידית בלבד.""",
    "general_inquiry": """POST-EXECUTION
1. תמיד עברי ל-transfer_to_human (95% מהמקרים).
2. אל תנסי לענות בעצמך על שאלות שאינן בתחום קביעת תורים.""",
}

# RT=2 Configurations
RT2_CONFIGS = {
    "validate_customer_address": {
        "url": "https://connector.center/nc/validate-address",
        "method": "POST",
        "headers": {},
        "body": {"address": "{{address}}"},
        "apiResponseAnnouncement": "הכתובת אומתה. בודקת זמינות תורים...",
        "fail_output": "אני לא מצליחה לאמת את הכתובת כרגע. אעבירך לנציג.",
        "function_output": "The API returns { valid: bool, service_area: string }. If valid=true, proceed to get_available_slots. If valid=false, the address is outside service area — announce that politely and transfer.",
        "loading_announcement": "רגע, בודקת...",
        "silence_duration": 8,
        "silence_loops": 5,
        "silence_sentence": "אני עדיין בודקת...",
        "silence_ending_sentence": "השרת לא מגיב. אעבירך לנציג.",
        "silence_instructions": "",
        "fallback_intent": "transfer_to_human",
    },
    "get_available_slots": {
        "url": "https://connector.center/nc/get-slots",
        "method": "POST",
        "headers": {},
        "body": {"address": "{{address}}"},
        "apiResponseAnnouncement": "מצאתי שלושה תורים: 1) {{available_slots.0.display}}, 2) {{available_slots.1.display}}, 3) {{available_slots.2.display}}",
        "fail_output": "אני לא מצליחה למצוא תורים זמינים כרגע. אעבירך לנציג.",
        "function_output": "Response shape: { available_slots: [{display, slot_id}, ...] }. The caller will pick one in confirm_appointment intent.",
        "loading_announcement": "רגע, מחפשת תורים...",
        "silence_duration": 8,
        "silence_loops": 5,
        "silence_sentence": "אני עדיין בודקת...",
        "silence_ending_sentence": "השרת לא מגיב. אעבירך לנציג.",
        "silence_instructions": "",
        "fallback_intent": "transfer_to_human",
    },
}

# RT=3 announcements
RT3_ANNOUNCEMENTS = {
    "confirm_appointment": "מעולה. רשמתי לך תור ב-{{available_slots.0.display}} בכתובת {{address}}. נשלח לך SMS עם פרטים.",
    "reschedule_existing": "הבנתי, יש לך תור קיים שאת/ה רוצה לשנות. אעבירך לנציג.",
    "general_inquiry": "אם השאלה לא קשורה לתור התקנה, אעבירך לנציג.",
}

# RT=1 transfer config (transfer_to_human)
RT1_CONFIG = {
    "transfer_to_human": {
        "layer": 43,
        "announcement": "אעבירך לנציג, רגע.",
        "intentLoadingAnnouncement": "מעבירה...",
    },
}

# Section 4 ordering (drives intents[], botIntents[], intentRelations[] order)
INTENT_ORDER = [
    "validate_customer_address",
    "get_available_slots",
    "confirm_appointment",
    "reschedule_existing",
    "general_inquiry",
    "transfer_to_human",
]

# Section 4 transitions out (drives intentRelations[])
TRANSITIONS = {
    "validate_customer_address": ["get_available_slots", "transfer_to_human"],
    "get_available_slots":       ["confirm_appointment", "transfer_to_human"],
    "confirm_appointment":       ["general_inquiry", "transfer_to_human"],
    "reschedule_existing":       ["confirm_appointment", "transfer_to_human"],
    "general_inquiry":           ["transfer_to_human"],
    "transfer_to_human":         [],
}

# Response types
RT = {
    "validate_customer_address": 2,
    "get_available_slots":       2,
    "confirm_appointment":       3,
    "reschedule_existing":       3,
    "general_inquiry":           3,
    "transfer_to_human":         1,
}

# Display name + description per intent
DISPLAY = {
    "validate_customer_address": ("אימות כתובת לקוח", "וידוא שהכתובת של הלקוח נמצאת באזור השירות שלנו."),
    "get_available_slots":       ("קבלת תורים זמינים", "השגת שלושה תורים זמינים הקרובים ביותר עבור הכתובת."),
    "confirm_appointment":       ("אישור תור", "אישור בחירת התור על ידי הלקוח."),
    "reschedule_existing":       ("שינוי תור קיים", "טיפול בבקשה לשנות תור התקנה קיים."),
    "general_inquiry":           ("שאלה כללית", "טיפול בשאלות כלליות שאינן קשורות לקביעת תור התקנה."),
    "transfer_to_human":         ("העברה לנציג", "העברת השיחה לנציג שירות אנושי."),
}


def build_intent_parameters(intent_name):
    out = []
    for slot_name, pt_id, required, order, opt_list, desc in SLOTS[intent_name]:
        param_id = PARAM_IDS[(intent_name, slot_name)]
        out.append(OrderedDict([
            ("ParameterId", param_id),
            ("IntentId", intent_id(intent_name)),
            ("Name", slot_name),
            ("Description", desc),
            ("IsRequired", required),
            ("DefaultValue", None),
            ("CollectionOrder", order),
            ("ParameterTypeId", pt_id),
            ("ParameterType", OrderedDict([
                ("ParameterTypeId", pt_id),
                ("Name", PARAM_TYPE_NAME[pt_id]),
            ])),
            ("OptionList", opt_list),
            ("ValidationRules", {}),       # quirk
            ("ValidationPattern", None),    # quirk
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
                ("url", cfg["url"]),
                ("method", cfg["method"]),
                ("headers", cfg["headers"]),
                ("body", cfg["body"]),
                ("apiResponseAnnouncement", cfg["apiResponseAnnouncement"]),
                ("fail_output", cfg["fail_output"]),
                ("function_output", cfg["function_output"]),
                ("intentLoadingAnnouncement", cfg["loading_announcement"]),
                ("IntentLoadingAnnouncement", cfg["loading_announcement"]),  # quirk: casing-bug pair
                ("intentInstructions", POST_EXEC[intent_name]),
                ("api_silence_behaviour", build_api_silence_behaviour(intent_name)),
                ("response_success", ""),  # quirk
            ])),
        ])
    if rt == 3:
        return OrderedDict([
            ("ResponseTypeId", 3),
            ("Configuration", OrderedDict([
                ("announcement", RT3_ANNOUNCEMENTS[intent_name]),
                ("intentInstructions", POST_EXEC[intent_name]),
                ("response_success", ""),  # quirk
            ])),
        ])
    raise ValueError(f"Unhandled RT for {intent_name}")


def build_intent(intent_name):
    name, desc = DISPLAY[intent_name]
    return OrderedDict([
        ("IntentId", intent_id(intent_name)),
        ("Name", name),
        ("Description", desc),
        ("IntentToolName", intent_name),
        ("HandlingInstructions", None),  # quirk
        ("IsSilenceIntent", False),
        ("IntentCategoryId", INTENT_CATEGORY_ID),
        ("Priority", 1),
        ("MaxAttempts", 3),
        ("ValidationTimeout", 30),
        ("IntentParameters", build_intent_parameters(intent_name)),
        ("IntentConfig", OrderedDict([
            ("prompts", OrderedDict([
                ("llmDescription", ""),  # quirk
                ("validationPrompt", VALIDATION_PROMPTS[intent_name]),
            ])),
        ])),
        ("IntentScripts", {}),  # quirk
        ("IntentResponces", build_intent_responces(intent_name)),  # quirk: typo preserved
        ("IsActive", 1),
        ("IsDeleted", 0),
    ])


def build_bot_intents():
    return [
        OrderedDict([
            ("BotIntentID", bot_intent_id(name)),
            ("BotID", BOT_ID),
            ("IntentID", intent_id(name)),
            ("BotIntentTypeID", 1),  # all 1 per Doc 1 §8.2
            ("ConditionGroupList", []),
        ])
        for name in INTENT_ORDER
    ]


def build_intent_relations():
    rows = []
    for origin in INTENT_ORDER:
        for order_idx, target in enumerate(TRANSITIONS[origin], start=1):
            rows.append(OrderedDict([
                ("OriginIntentID", intent_id(origin)),
                ("NextIntentID", intent_id(target)),
                ("IntentRelatedID", intent_id(target)),  # duplicates NextIntentID per Doc 1 §8.3
                ("Order", order_idx),
                ("ConditionGroupList", []),
            ]))
    return rows


def build_intent_categories():
    return [
        OrderedDict([
            ("IntentCategoryId", INTENT_CATEGORY_ID),
            ("BotID", BOT_ID),
            ("Name", "Default Category"),
        ]),
    ]


def build_api_silence_relations():
    out = []
    for name in INTENT_ORDER:
        if RT[name] == 2:
            out.append(OrderedDict([
                ("OriginIntentID", intent_id(name)),
                ("ApiSilenceIntentID", intent_id(RT2_CONFIGS[name]["fallback_intent"])),
                ("Configuration", build_api_silence_behaviour(name)),
            ]))
    return out


def build_intent_list():
    return OrderedDict([
        ("intents",            [build_intent(n) for n in INTENT_ORDER]),
        ("botIntents",         build_bot_intents()),
        ("intentRelations",    build_intent_relations()),
        ("intentCategories",   build_intent_categories()),
        ("silenceRelations",   []),  # quirk
        ("apiSilenceRelations", build_api_silence_relations()),
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
    return OrderedDict([
        ("prompts", OrderedDict([
            ("persona", PERSONA),
            ("voiceInstructions", VOICE_INSTRUCTIONS),
            ("chatInstructions", CHAT_INSTRUCTIONS),
            ("intentInstructions", OPENING_BEHAVIOR),
            ("openingAnnouncement", OPENING_ANNOUNCEMENT),
        ])),
        ("created", build_created()),  # identical to top-level (quirk)
        ("silence_behaviour", SILENCE_BEHAVIOUR),
        ("tools", []),         # quirk
        ("instructions", ""),  # quirk
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
        ("SystemPrompt", ""),  # quirk
        ("AIModelConfigId", -999),  # mirror of top-level (sentinel here)
        ("AIModelConfig", build_ai_model_config_version()),
    ])


def build_root():
    return OrderedDict([
        ("Name", "יובל"),
        ("BotID", BOT_ID),
        ("AccountID", -999),  # sentinel
        ("Description", "<USER_TO_FILL: bot description>"),  # sentinel
        ("BotStatusId", 1),
        ("BotLanguages", []),  # quirk
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
    with open(os.path.join(out_dir, "test-emitted-json-yuval.json"), "w", encoding="utf-8") as f:
        f.write(out)
    print(f"Wrote {len(out)} chars, {out.count(chr(10))+1} lines")
