import json
import re

import torch
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
)
from transformers.utils import logging


MODEL_NAME = "nvidia/Nemotron-4-Mini-Hindi-4B-Instruct"

# Keep Transformers output quiet.
logging.set_verbosity_error()


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
5. Do not classify from keywords alone.
6. Consider the complete meaning of the complaint.
7. If multiple domains are mentioned, choose the domain containing
   the main problem that needs to be solved.
8. Do not answer the complaint.
9. Do not provide an explanation.
10. Return ONLY JSON:

{{"category": "category_name"}}

DISAMBIGUATION:

Drinking/public water supply -> water_resources
Water specifically needed for farming/crops -> agriculture

Pollution/environmental damage -> environment
Lack of access to water -> water_resources

Farming/crops -> agriculture
Rural employment/income/livelihood -> rural_livelihoods

Physical city/municipal infrastructure -> urban_development
Government paperwork/procedures/delays -> public_administration

Actual school/college/teacher/student problem -> education
Administrative paperwork related to education -> public_administration

Actual medical problem/service -> healthcare
Administrative government procedure related to healthcare -> public_administration

Disability-related access barrier -> accessibility

EXAMPLES:

"mere gaon mein peene ka paani nahi aa raha"
{{"category": "water_resources"}}

"kheton ke liye paani nahi mil raha"
{{"category": "agriculture"}}

"school mein teachers nahi hain"
{{"category": "education"}}

"hospital mein doctor nahi hai"
{{"category": "healthcare"}}

"hamare area mein roz bijli jaati hai"
{{"category": "energy"}}

"nadi mein factory ka chemical waste ja raha hai"
{{"category": "environment"}}

"sadak par bahut bade gaddhe hain"
{{"category": "urban_development"}}

"wheelchair ke liye government office mein ramp nahi hai"
{{"category": "accessibility"}}

"mera birth certificate banwane mein delay ho raha hai"
{{"category": "public_administration"}}

"gaon mein naukri ke koi mauke nahi hain"
{{"category": "rural_livelihoods"}}
"""


tokenizer = AutoTokenizer.from_pretrained(
    MODEL_NAME,
    local_files_only=True,
)

model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    dtype=torch.float16,
    device_map="auto",
    local_files_only=True,
)

model.eval()


def _generate(text: str) -> str:
    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": text,
        },
    ]

    inputs = tokenizer.apply_chat_template(
        messages,
        tokenize=True,
        add_generation_prompt=True,
        return_dict=True,
        return_tensors="pt",
    )

    inputs = {
        key: value.to(model.device)
        for key, value in inputs.items()
    }

    with torch.inference_mode():
        outputs = model.generate(
            **inputs,
            max_new_tokens=32,
            do_sample=False,
            use_cache=True,
            pad_token_id=tokenizer.eos_token_id,
        )

    generated = outputs[0][inputs["input_ids"].shape[-1]:]

    return tokenizer.decode(
        generated,
        skip_special_tokens=True,
        clean_up_tokenization_spaces=False,
    ).strip()


def _parse_category(output: str) -> str:
    try:
        data = json.loads(output)

        category = data.get("category")

        if category in CATEGORY_NAMES:
            return category

    except json.JSONDecodeError:
        pass

    match = re.search(
        r'"category"\s*:\s*"([^"]+)"',
        output,
        re.IGNORECASE,
    )

    if match:
        category = match.group(1)

        if category in CATEGORY_NAMES:
            return category

    raise ValueError(
        f"Invalid model output: {output}"
    )


def classify_issue(text: str) -> str:
    text = text.strip()

    if not text:
        raise ValueError("Complaint cannot be empty.")

    output = _generate(text)

    return _parse_category(output)