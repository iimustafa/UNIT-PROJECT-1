import re

CONTEXT_RULES = [
    # تحسين نطق كلمة السور في السياق القرآني
    (r"(?<!\S)السور(?=\s|$|[،.!؟])", "السُّوَر"),
    (r"(?<!\S)سور(?=\s|$|[،.!؟])", "سُوَر"),

    # تحسين نطق كلمة التالية
    (r"(?<!\S)التالية(?=\s|$|[،.!؟])", "التَّالِيَة"),

    # تحسين نطق إلى في عبارة التحدث
    (r"(?<!\S)التحدث\s+إلى(?=\s|$|[،.!؟])", "التحدث إِلَيْ"),
    (r"(?<!\S)التحدث\s+الي(?=\s|$|[،.!؟])", "التحدث إِلَيْ"),

    # تحسين نطق الانتقال
    (r"(?<!\S)والانتقال(?=\s|$|[،.!؟])", "والإنْتِقَال"),
    (r"(?<!\S)الانتقال(?=\s|$|[،.!؟])", "الإنْتِقَال"),
]


def prepare_arabic_for_tts(text: str) -> str:
    """تهيئة النص لمحرك الصوت دون تغيير النص الأصلي المعروض."""
    if not isinstance(text, str):
        text = str(text)

    spoken_text = text.strip()

    for pattern, replacement in CONTEXT_RULES:
        spoken_text = re.sub(pattern, replacement, spoken_text)

    spoken_text = re.sub(r"[ \t]+", " ", spoken_text)
    return spoken_text
