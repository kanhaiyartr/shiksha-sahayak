"""Sample syllabus catalog. Five subjects per class, with short chapter lists.

This is sample text for the prototype. It is not an official SCERT syllabus.
"""

from __future__ import annotations

from typing import Any

# Chapter: topic (selection key), title, locator stem, short note.
Chapter = dict[str, str]
SubjectBlock = dict[str, Any]


def _ch(topic: str, title: str, locator: str, note: str) -> Chapter:
    return {"topic": topic, "title": title, "locator": locator, "note": note}


# Shared chapter sets used by classes 3–6 and 8 so the eval cases still resolve.
_MATH_EN = [
    _ch("Fractions", "Parts and wholes", "NCERT Class Mathematics, Chapter: Parts and Wholes", "A fraction names equal parts of one whole."),
    _ch("Decimals", "Tenths and hundredths", "NCERT Class Mathematics, Chapter: Tenths and Hundredths", "A decimal shows tenths and hundredths of one whole."),
    _ch("Perimeter", "Perimeter and area", "NCERT Class Mathematics, Chapter: Perimeter and Area", "Perimeter is the distance around a closed shape."),
]
_SCI_EN = [
    _ch("Light", "Light", "NCERT Class Science, Chapter: Light", "Light travels in a straight line until it meets an object."),
    _ch("Water cycle", "Water", "NCERT Class Science, Chapter: Water", "Water evaporates, forms clouds, and returns as rain."),
    _ch("Plants", "Plants", "NCERT Class Science, Chapter: Plants", "A plant needs water, air, and sunlight to grow."),
]
_EVS_EN = [
    _ch("Saving water", "Water we use", "NCERT Class EVS, Chapter: Water", "Close the tap while soaping your hands."),
    _ch("Neighbourhood maps", "Maps", "NCERT Class EVS, Chapter: Maps", "A map uses symbols to show places."),
]
_ENG_EN = [
    _ch("Nouns", "Naming words", "NCERT Class English, Grammar: Nouns", "A noun names a person, place, animal, or thing."),
    _ch("Verbs", "Doing words", "NCERT Class English, Grammar: Verbs", "A verb tells what someone does."),
]
_SST_EN = [
    _ch("Community helpers", "People who help us", "Sample Social Science, Chapter: Community helpers", "People in the neighbourhood help each other every day."),
    _ch("Local government", "Local bodies", "Sample Social Science, Chapter: Local government", "A local body looks after roads, water, and schools nearby."),
]

_MATH_HI = [
    _ch("भिन्न", "भिन्न", "एनसीईआरटी गणित, अध्याय: भिन्न", "भिन्न एक पूरे के बराबर भागों को बताती है।"),
    _ch("दशमलव", "दशमलव", "एनसीईआरटी गणित, अध्याय: दशमलव", "दशमलव दसवें और सौवें भाग दिखाता है।"),
    _ch("परिमाप", "परिमाप", "एनसीईआरटी गणित, अध्याय: परिमाप", "परिमाप किसी आकृति के चारों ओर की लंबाई है।"),
]
_SCI_HI = [
    _ch("प्रकाश", "प्रकाश", "एनसीईआरटी विज्ञान, अध्याय: प्रकाश", "प्रकाश सीधी रेखा में चलता है।"),
    _ch("जल चक्र", "जल", "एनसीईआरटी विज्ञान, अध्याय: जल", "जल भाप बनता है, बादल बनते हैं, और वर्षा होती है।"),
    _ch("पौधे", "पौधे", "एनसीईआरटी विज्ञान, अध्याय: पौधे", "पौधे को पानी, हवा और धूप चाहिए।"),
]
_EVS_HI = [
    _ch("पानी की बचत", "पानी", "एनसीईआरटी पर्यावरण, अध्याय: पानी", "हाथ धोते समय नल बंद रखें।"),
    _ch("नक्शा", "नक्शा", "एनसीईआरटी पर्यावरण, अध्याय: नक्शा", "नक्शा स्थानों को चिह्नों से दिखाता है।"),
]
_HIN_HI = [
    _ch("संज्ञा", "संज्ञा", "एनसीईआरटी हिन्दी, व्याकरण: संज्ञा", "संज्ञा किसी व्यक्ति, स्थान, वस्तु या प्राणी का नाम है।"),
    _ch("क्रिया", "क्रिया", "एनसीईआरटी हिन्दी, व्याकरण: क्रिया", "क्रिया बताती है कि कोई क्या करता है।"),
]
_SST_HI = [
    _ch("सामुदायिक सहायक", "हमारे सहायक", "नमूना सामाजिक विज्ञान, अध्याय: सामुदायिक सहायक", "मोहल्ले के लोग एक-दूसरे की मदद करते हैं।"),
    _ch("स्थानीय शासन", "स्थानीय निकाय", "नमूना सामाजिक विज्ञान, अध्याय: स्थानीय शासन", "स्थानीय निकाय सड़क, पानी और स्कूल का ध्यान रखते हैं।"),
]

# Parallel sample chapters for classes outside the eval set.
_MATH_EN_EARLY = [
    _ch("Counting", "Numbers around us", "Sample Mathematics, Chapter: Counting", "Count objects one by one."),
    _ch("Shapes", "Looking at shapes", "Sample Mathematics, Chapter: Shapes", "A circle is round. A square has four equal sides."),
]
_SCI_EN_EARLY = [
    _ch("My body", "Parts of the body", "Sample Science, Chapter: My body", "Eyes, ears, and hands help us learn about the world."),
    _ch("Animals", "Animals near us", "Sample Science, Chapter: Animals", "Some animals live at home. Some live in the wild."),
]
_EVS_EN_EARLY = [
    _ch("My family", "People at home", "Sample EVS, Chapter: My family", "Family members care for each other."),
    _ch("Clean habits", "Keeping clean", "Sample EVS, Chapter: Clean habits", "Wash hands before eating."),
]
_ENG_EN_EARLY = [
    _ch("Letters", "The alphabet", "Sample English, Chapter: Letters", "Each letter has a sound."),
    _ch("Simple sentences", "Saying a full idea", "Sample English, Chapter: Sentences", "A sentence starts with a capital letter."),
]
_SST_EN_EARLY = [
    _ch("Our school", "Places in school", "Sample Social Science, Chapter: Our school", "The classroom and the playground are parts of school."),
    _ch("Festivals", "Days we celebrate", "Sample Social Science, Chapter: Festivals", "Festivals bring people together."),
]

_MATH_EN_UPPER = [
    _ch("Algebra basics", "Letters for numbers", "Sample Mathematics, Chapter: Algebra basics", "A letter can stand for an unknown number."),
    _ch("Linear equations", "Solving for x", "Sample Mathematics, Chapter: Linear equations", "Keep both sides of an equation equal."),
    _ch("Statistics", "Reading data", "Sample Mathematics, Chapter: Statistics", "A table and a bar graph show the same facts."),
]
_SCI_EN_UPPER = [
    _ch("Atoms", "Building blocks of matter", "Sample Science, Chapter: Atoms", "Atoms join to make molecules."),
    _ch("Forces", "Push and pull", "Sample Science, Chapter: Forces", "A force can change the speed of an object."),
    _ch("Cells", "Units of life", "Sample Science, Chapter: Cells", "Living things are made of cells."),
]
_EVS_EN_UPPER = [
    _ch("Natural resources", "Things we use from nature", "Sample EVS, Chapter: Natural resources", "Use water and soil carefully."),
    _ch("Pollution", "Keeping air and water clean", "Sample EVS, Chapter: Pollution", "Smoke and plastic waste harm living things."),
]
_ENG_EN_UPPER = [
    _ch("Essay writing", "Organising ideas", "Sample English, Chapter: Essay writing", "A short essay has a beginning, middle, and end."),
    _ch("Comprehension", "Reading for meaning", "Sample English, Chapter: Comprehension", "Find the main idea in a short passage."),
]
_SST_EN_UPPER = [
    _ch("Indian Constitution", "Rules for the country", "Sample Social Science, Chapter: Constitution", "The Constitution sets the basic rules of the country."),
    _ch("Freedom struggle", "Path to independence", "Sample Social Science, Chapter: Freedom struggle", "Many people worked for India's freedom."),
]

_MATH_HI_EARLY = [
    _ch("गिनती", "संख्याएँ", "नमूना गणित, अध्याय: गिनती", "वस्तुओं को एक-एक करके गिनें।"),
    _ch("आकृतियाँ", "आकृतियाँ देखना", "नमूना गणित, अध्याय: आकृतियाँ", "वृत्त गोल होता है। वर्ग की चार भुजाएँ बराबर होती हैं।"),
]
_SCI_HI_EARLY = [
    _ch("मेरा शरीर", "शरीर के अंग", "नमूना विज्ञान, अध्याय: मेरा शरीर", "आँख, कान और हाथ हमें दुनिया जानने में मदद करते हैं।"),
    _ch("जानवर", "पास के जानवर", "नमूना विज्ञान, अध्याय: जानवर", "कुछ जानवर घर पर रहते हैं। कुछ जंगल में।"),
]
_EVS_HI_EARLY = [
    _ch("मेरा परिवार", "घर के लोग", "नमूना पर्यावरण, अध्याय: मेरा परिवार", "परिवार के सदस्य एक-दूसरे का ध्यान रखते हैं।"),
    _ch("स्वच्छ आदतें", "साफ रहना", "नमूना पर्यावरण, अध्याय: स्वच्छ आदतें", "खाने से पहले हाथ धोएँ।"),
]
_HIN_HI_EARLY = [
    _ch("अक्षर", "वर्णमाला", "नमूना हिन्दी, अध्याय: अक्षर", "हर अक्षर की एक ध्वनि होती है।"),
    _ch("छोटे वाक्य", "पूरी बात कहना", "नमूना हिन्दी, अध्याय: वाक्य", "वाक्य एक पूरी बात कहता है।"),
]
_SST_HI_EARLY = [
    _ch("हमारा स्कूल", "स्कूल के स्थान", "नमूना सामाजिक विज्ञान, अध्याय: हमारा स्कूल", "कक्षा और मैदान स्कूल के भाग हैं।"),
    _ch("त्योहार", "मिलने के दिन", "नमूना सामाजिक विज्ञान, अध्याय: त्योहार", "त्योहार लोगों को एक साथ लाते हैं।"),
]

_MATH_HI_UPPER = [
    _ch("बीजगणित आधार", "संख्या के लिए अक्षर", "नमूना गणित, अध्याय: बीजगणित", "अक्षर अज्ञात संख्या बता सकता है।"),
    _ch("रैखिक समीकरण", "x ज्ञात करना", "नमूना गणित, अध्याय: रैखिक समीकरण", "समीकरण के दोनों पक्ष बराबर रखें।"),
    _ch("सांख्यिकी", "आँकड़े पढ़ना", "नमूना गणित, अध्याय: सांख्यिकी", "तालिका और दंड आलेख एक ही बात दिखाते हैं।"),
]
_SCI_HI_UPPER = [
    _ch("परमाणु", "पदार्थ की इकाई", "नमूना विज्ञान, अध्याय: परमाणु", "परमाणु मिलकर अणु बनाते हैं।"),
    _ch("बल", "धक्का और खिंचाव", "नमूना विज्ञान, अध्याय: बल", "बल वस्तु की गति बदल सकता है।"),
    _ch("कोशिका", "जीवन की इकाई", "नमूना विज्ञान, अध्याय: कोशिका", "जीव कोशिका से बने होते हैं।"),
]
_EVS_HI_UPPER = [
    _ch("प्राकृतिक संसाधन", "प्रकृति से मिलने वाली वस्तुएँ", "नमूना पर्यावरण, अध्याय: प्राकृतिक संसाधन", "पानी और मिट्टी का सही उपयोग करें।"),
    _ch("प्रदूषण", "वायु और जल साफ रखना", "नमूना पर्यावरण, अध्याय: प्रदूषण", "धुआँ और प्लास्टिक जीवों को हानि पहुँचाते हैं।"),
]
_HIN_HI_UPPER = [
    _ch("निबंध लेखन", "विचार जोड़ना", "नमूना हिन्दी, अध्याय: निबंध", "छोटे निबंध में शुरुआत, बीच और अंत होता है।"),
    _ch("गद्यांश बोध", "अर्थ समझना", "नमूना हिन्दी, अध्याय: गद्यांश", "गद्यांश का मुख्य विचार खोजें।"),
]
_SST_HI_UPPER = [
    _ch("भारतीय संविधान", "देश के नियम", "नमूना सामाजिक विज्ञान, अध्याय: संविधान", "संविधान देश के मूल नियम तय करता है।"),
    _ch("स्वतंत्रता संग्राम", "आजादी का मार्ग", "नमूना सामाजिक विज्ञान, अध्याय: स्वतंत्रता संग्राम", "कई लोगों ने भारत की आजादी के लिए काम किया।"),
]


def _subjects_en(math: list, sci: list, evs: list, eng: list, sst: list) -> list[SubjectBlock]:
    return [
        {"name": "Mathematics", "chapters": math},
        {"name": "Science", "chapters": sci},
        {"name": "EVS", "chapters": evs},
        {"name": "English", "chapters": eng},
        {"name": "Social Science", "chapters": sst},
    ]


def _subjects_hi(math: list, sci: list, evs: list, hin: list, sst: list) -> list[SubjectBlock]:
    return [
        {"name": "गणित", "chapters": math},
        {"name": "विज्ञान", "chapters": sci},
        {"name": "पर्यावरण", "chapters": evs},
        {"name": "हिन्दी", "chapters": hin},
        {"name": "सामाजिक विज्ञान", "chapters": sst},
    ]


def _eval_en() -> list[SubjectBlock]:
    return _subjects_en(_MATH_EN, _SCI_EN, _EVS_EN, _ENG_EN, _SST_EN)


def _eval_hi() -> list[SubjectBlock]:
    return _subjects_hi(_MATH_HI, _SCI_HI, _EVS_HI, _HIN_HI, _SST_HI)


def _early_en() -> list[SubjectBlock]:
    return _subjects_en(_MATH_EN_EARLY, _SCI_EN_EARLY, _EVS_EN_EARLY, _ENG_EN_EARLY, _SST_EN_EARLY)


def _early_hi() -> list[SubjectBlock]:
    return _subjects_hi(_MATH_HI_EARLY, _SCI_HI_EARLY, _EVS_HI_EARLY, _HIN_HI_EARLY, _SST_HI_EARLY)


def _upper_en() -> list[SubjectBlock]:
    return _subjects_en(_MATH_EN_UPPER, _SCI_EN_UPPER, _EVS_EN_UPPER, _ENG_EN_UPPER, _SST_EN_UPPER)


def _upper_hi() -> list[SubjectBlock]:
    return _subjects_hi(_MATH_HI_UPPER, _SCI_HI_UPPER, _EVS_HI_UPPER, _HIN_HI_UPPER, _SST_HI_UPPER)


CATALOG: dict[str, dict[str, list[SubjectBlock]]] = {}
for level in ("1", "2"):
    CATALOG[level] = {"en": _early_en(), "hi": _early_hi()}
for level in ("3", "4", "5", "6", "8"):
    CATALOG[level] = {"en": _eval_en(), "hi": _eval_hi()}
for level in ("7", "9", "10", "11", "12"):
    CATALOG[level] = {"en": _upper_en(), "hi": _upper_hi()}


def list_catalog(class_level: str, language: str, query: str = "") -> dict[str, Any]:
    """Return up to five subjects and their chapters for one class and language."""

    language_key = language.strip().lower()
    if class_level not in CATALOG or language_key not in ("en", "hi"):
        return {
            "class_level": class_level,
            "language": language_key,
            "sample": True,
            "subjects": [],
            "note": "Choose a class from 1 to 12 and language en or hi.",
        }
    subjects = CATALOG[class_level][language_key]
    needle = query.casefold().strip()
    if needle:
        filtered: list[SubjectBlock] = []
        for subject in subjects:
            chapters = [
                chapter for chapter in subject["chapters"]
                if needle in subject["name"].casefold()
                or needle in chapter["topic"].casefold()
                or needle in chapter["title"].casefold()
            ]
            if chapters or needle in subject["name"].casefold():
                filtered.append({
                    "name": subject["name"],
                    "chapters": chapters if chapters else list(subject["chapters"]),
                })
        subjects = filtered[:5]
    return {
        "class_level": class_level,
        "language": language_key,
        "sample": True,
        "subjects": [
            {
                "name": subject["name"],
                "chapters": [
                    {"topic": chapter["topic"], "title": chapter["title"]}
                    for chapter in subject["chapters"]
                ],
            }
            for subject in subjects
        ],
        "note": "Sample syllabus for this prototype. Check the textbook before class.",
    }


def _hint_from_chapter(class_level: str, chapter: dict[str, str], language: str, topic: str) -> dict[str, str]:
    from app.chapter_content import pack_for_hint

    hint = {
        "title": chapter["title"],
        "locator": f"{chapter['locator']} | class {class_level}",
        "note": chapter["note"],
        "untrusted": "false",
        "kind": "syllabus_hint",
    }
    hint.update(pack_for_hint(language, topic))
    return hint


def lookup_syllabus_hint(class_level: str, subject: str, topic: str, language: str) -> dict[str, str]:
    """Return reference text for a topic. Arguments from the model are ignored by the caller."""

    topic_key = topic.casefold().strip()
    subject_key = subject.casefold().strip()
    language_key = language.strip().lower()
    subjects = CATALOG.get(class_level, {}).get(language_key, [])
    for block in subjects:
        if block["name"].casefold() != subject_key:
            continue
        for chapter in block["chapters"]:
            if chapter["topic"].casefold() == topic_key:
                return _hint_from_chapter(class_level, chapter, language_key, chapter["topic"])
    for block in subjects:
        for chapter in block["chapters"]:
            if chapter["topic"].casefold() == topic_key:
                return _hint_from_chapter(class_level, chapter, language_key, chapter["topic"])
    if language_key == "hi":
        note = "इस विषय का संग्रहित संकेत नहीं मिला। कक्षा से पहले पाठ्यपुस्तक देखें।"
        title = "पाठ्यपुस्तक जाँच"
    else:
        note = "No stored hint for this topic. Check the textbook before the class."
        title = "Textbook check"
    return {
        "title": title,
        "locator": f"textbook:not-found | class {class_level} | {subject}",
        "note": note,
        "untrusted": "false",
        "kind": "syllabus_hint",
    }
