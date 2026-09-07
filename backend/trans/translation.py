import json
import re
import httpx
from config import config

CATEGORIES = {
    "education": """
Schools, colleges, teachers, students, exams, scholarships,
classrooms, educational facilities, textbooks, or access to education.
""",
    "agriculture": """
Farming, crops, farm irrigation, seeds, fertilizers, pesticides,
livestock, agricultural equipment, agricultural markets, or crop damage.
""",
    "healthcare": """
Hospitals, clinics, doctors, nurses, medicines, diagnosis,
treatment, ambulances, medical services, or healthcare access.
""",
    "water_resources": """
Drinking water supply, public water supply, water pipelines,
groundwater, reservoirs, water availability, water quality,
water leakage, or public water infrastructure.
""",
    "environment": """
Pollution, waste, air quality, water pollution, deforestation,
wildlife, environmental damage, or environmental protection.
""",
    "energy": """
Electricity, power supply, power outages, electrical infrastructure,
renewable energy, fuel, or other energy-related services.
""",
    "urban_development": """
Urban infrastructure and municipal services such as city roads,
streets, drainage, sewage, garbage collection, public spaces,
traffic, or urban planning.
""",
    "accessibility": """
Accessibility barriers for persons with disabilities, including
inaccessible buildings, transport, websites, public services,
ramps, elevators, or other physical/digital access barriers.
""",
    "public_administration": """
Government offices, government procedures, documents, certificates,
licenses, public-service delivery, bureaucratic delays,
or administrative processes.
""",
    "rural_livelihoods": """
Rural employment, income generation, self-employment,
village livelihoods, rural jobs, skill development,
or economic opportunities for rural communities.
""",
}

CATEGORY_NAMES = list(CATEGORIES.keys())

SYSTEM_PROMPT = f"""
You are a strict government complaint classification engine.

Classify the complaint into EXACTLY ONE administrative domain.

You understand:
- Hindi in Devanagari
- Roman Hindi
- Hinglish
- English
- mixed Hindi and English
- informal language
- common spelling mistakes

Do NOT translate the complaint before classifying it.
Understand its meaning directly.

ALLOWED CATEGORIES:
{json.dumps(CATEGORY_NAMES)}

CATEGORY DEFINITIONS:
{
    chr(10).join(
        f"{name}: {description.strip()}"
        for name, description in CATEGORIES.items()
    )
}

RULES:
1. Choose exactly ONE category.
2. Use one of the exact allowed category names.
3. Never invent a category.
4. Classify the PRIMARY problem.
5. Return ONLY valid JSON: {{"category": "category_name"}}
"""

KEYWORD_RULES = {
    "water_resources": [
        "water", "drinking", "pipeline", "pipe", "tap", "well", "borewell", "groundwater",
        "paani", "pani", "peene", "jal", "tanker", "nal", "leakage"
    ],
    "agriculture": [
        "crop", "crops", "farm", "farming", "farmer", "fertilizer", "pesticide", "seed",
        "irrigation", "fasal", "kisan", "kheti", "khet", "anaaj", "beej"
    ],
    "healthcare": [
        "hospital", "clinic", "doctor", "nurse", "medicine", "health", "ambulance", "patient",
        "bimari", "dawa", "ilaj", "aspatal", "swasthya"
    ],
    "energy": [
        "electricity", "power", "outage", "transformer", "grid", "voltage", "solar",
        "bijli", "light", "current", "batti", "tar"
    ],
    "environment": [
        "pollution", "garbage", "waste", "chemical", "river", "air", "deforestation", "smoke",
        "pradushan", "kachra", "dhuwa", "nadi", "gandagi"
    ],
    "urban_development": [
        "road", "street", "pothole", "traffic", "sewage", "drain", "drainage", "city",
        "sadak", "gaddha", "gali", "naali", "sewer"
    ],
    "accessibility": [
        "wheelchair", "ramp", "disability", "disabled", "handicap", "blind", "elevator", "lift",
        "divyang", "baishakhi"
    ],
    "public_administration": [
        "bribe", "corruption", "certificate", "license", "ration", "officer", "delay", "bureaucracy",
        "praman patra", "daftaron", "adhikari", "document", "aadhaar"
    ],
    "education": [
        "school", "college", "teacher", "student", "classroom", "textbook", "exam", "scholarship",
        "vidyalaya", "shiksha", "adhyapak", "chhatra", "kitab"
    ],
    "rural_livelihoods": [
        "livelihood", "employment", "job", "wage", "mgnrega", "village craft", "self-help",
        "naukri", "rozgar", "majdoori", "gaon", "gramin"
    ]
}


def _rule_based_fallback(text: str) -> str:
    lower_text = text.lower()
    scores = {cat: 0 for cat in CATEGORY_NAMES}

    for cat, keywords in KEYWORD_RULES.items():
        for kw in keywords:
            if kw in lower_text:
                scores[cat] += 1

    best_cat, best_score = max(scores.items(), key=lambda item: item[1])
    if best_score > 0:
        return best_cat
    return "public_administration"


def _parse_category(output: str) -> str:
    try:
        data = json.loads(output)
        category = data.get("category")
        if category in CATEGORY_NAMES:
            return category
    except json.JSONDecodeError:
        pass

    match = re.search(r'"category"\s*:\s*"([^"]+)"', output, re.IGNORECASE)
    if match:
        category = match.group(1)
        if category in CATEGORY_NAMES:
            return category

    raise ValueError(f"Invalid model output: {output}")


def _classify_with_gemini(text: str) -> str:
    models_to_try = [config.GEMINI_MODEL, "gemini-flash-latest"] if config.GEMINI_MODEL != "gemini-flash-latest" else ["gemini-flash-latest"]

    for model in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={config.GEMINI_API_KEY}"
        payload = {
            "contents": [{
                "parts": [{
                    "text": f"{SYSTEM_PROMPT}\n\nComplaint to classify:\n{text}"
                }]
            }]
        }
        try:
            with httpx.Client(timeout=12.0) as client:
                resp = client.post(url, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
                    for part in reversed(parts):
                        if "text" in part:
                            try:
                                return _parse_category(part["text"])
                            except ValueError:
                                continue
        except Exception:
            continue

    raise RuntimeError("Gemini API call failed")


def classify_issue(text: str) -> str:
    text = text.strip()
    if not text:
        raise ValueError("Complaint cannot be empty.")

    if getattr(config, "GEMINI_API_KEY", None):
        try:
            return _classify_with_gemini(text)
        except Exception:
            pass

    return _rule_based_fallback(text)