"""Gemini-powered AI agent with Ollama fallback for Taysir."""

import json
import os
from pathlib import Path

import ollama
from dotenv import load_dotenv
from google import genai
from google.genai import types

from voice.voice_agent import VoiceAgent


# Load project settings from Taysir/.env.
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(dotenv_path=BASE_DIR / ".env")


ACTIONS = [
    "read",
    "next",
    "previous",
    "goto",
    "tafsir",
    "repeat",
    "search",
    "play_ayah",
    "play_surah",
    "stop",
    "help",
    "exit",
    "chat",
]


INSTRUCTIONS = """
أنت وكيل الأوامر والمحادثة لتطبيق تيسير، قارئ قرآن.

افهم العربية الفصحى واللهجات العربية والأوامر القصيرة.

الأفعال المسموحة:
read = عرض الآية الحالية
next = الانتقال للآية التالية
previous = الانتقال للآية السابقة
goto = الانتقال إلى سورة وآية محددتين
tafsir = عرض التفسير الميسر للآية الحالية
repeat = إعادة عرض الآية الحالية
search = البحث في نص القرآن
play_ayah = تشغيل الآية الحالية
play_surah = تشغيل السورة الحالية
stop = إيقاف التلاوة
help = عرض المساعدة
exit = إنهاء المحادثة
chat = محادثة عادية أو طلب توضيح

أمثلة:
"اقرأ اللي بعدها" => next
"رجعني آية" => previous
"وش تفسيرها؟" => tafsir
"دور على الحمد لله" => search
"شغلها" => play_ayah
"شغل سورة البقرة" => play_surah
"انتقل لسورة الملك آية خمسة" => goto، surah=67، ayah=5

استخدم أرقام السور الواردة في السياق.
إذا كان الطلب غامضًا، اختر chat واطلب توضيحًا.
لا تخترع آيات أو تفاسير.
لا تدّعِ تنفيذ أي أمر؛ التطبيق هو الذي ينفذه.

أعد JSON فقط بالمفاتيح:
action, surah, ayah, query, reply

surah و ayah أرقام صحيحة أو null.
query و reply نصان.
"""


def _extract_json(text):
    """Extract a JSON object from the model response."""

    if not text:
        raise ValueError("لم يُرجع النموذج أي نص.")

    text = text.strip()

    if text.startswith("```"):
        lines = text.splitlines()

        if lines and lines[0].startswith("```"):
            lines = lines[1:]

        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]

        text = "\n".join(lines).strip()

    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end <= start:
        raise ValueError("لم يُرجع النموذج JSON صالحًا.")

    return json.loads(text[start:end + 1])


def _validate_result(result):
    """Validate the model output before the app uses it."""

    if not isinstance(result, dict):
        raise ValueError("صيغة استجابة الوكيل غير صحيحة.")

    if result.get("action") not in ACTIONS:
        raise ValueError("أعاد النموذج أمرًا غير مدعوم.")

    for field in ("surah", "ayah"):
        value = result.get(field)

        if value is not None:
            if isinstance(value, bool) or not isinstance(value, int):
                raise ValueError(f"قيمة {field} يجب أن تكون رقمًا صحيحًا.")

    result.setdefault("surah", None)
    result.setdefault("ayah", None)
    result.setdefault("query", "")
    result.setdefault("reply", "")

    if not isinstance(result["query"], str):
        result["query"] = str(result["query"])

    if not isinstance(result["reply"], str):
        result["reply"] = str(result["reply"])

    return result


class TaysirAIAgent:
    """Gemini primary agent with Ollama fallback and local voice input."""

    def __init__(self):
        self.provider = os.getenv("TAYSIR_AI_PROVIDER", "gemini").lower()

        self.gemini_model = os.getenv(
            "GEMINI_TEXT_MODEL",
            "gemini-flash-latest",
        )

        self.ollama_model = os.getenv(
            "OLLAMA_MODEL",
            "qwen3:14b",
        )

        self.gemini_client = None

        api_key = os.getenv("GEMINI_API_KEY")

        if api_key:
            self.gemini_client = genai.Client(api_key=api_key)

        self.ollama_client = ollama.Client(
            host=os.getenv(
                "OLLAMA_HOST",
                "http://127.0.0.1:11434",
            )
        )

        # Voice recognition remains local.
        self.voice_agent = VoiceAgent(
            model_size="small",
            sample_rate=16000,
            recording_seconds=6,
        )

    def listen(self, seconds=6, sample_rate=16000):
        """Record and transcribe Arabic speech locally."""

        self.voice_agent.recording_seconds = seconds
        self.voice_agent.sample_rate = sample_rate

        return self.voice_agent.listen()

    def _build_context(
        self,
        user_text,
        current_surah,
        current_ayah,
        surah_names,
    ):
        return {
            "user_message": user_text.strip(),
            "current_location": {
                "surah_number": current_surah,
                "ayah_number": current_ayah,
            },
            "surah_names_number_to_name": {
                str(number): name
                for number, name in surah_names.items()
            },
        }

    def _understand_with_gemini(self, context):
        if self.gemini_client is None:
            raise RuntimeError(
                "لم يتم العثور على GEMINI_API_KEY في ملف .env."
            )

        response = self.gemini_client.models.generate_content(
            model=self.gemini_model,
            contents=json.dumps(context, ensure_ascii=False),
            config=types.GenerateContentConfig(
                system_instruction=INSTRUCTIONS,
                response_mime_type="application/json",
                temperature=0,
            ),
        )

        return _validate_result(_extract_json(response.text))

    def _understand_with_ollama(self, context):
        response = self.ollama_client.chat(
            model=self.ollama_model,
            messages=[
                {
                    "role": "system",
                    "content": INSTRUCTIONS,
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        context,
                        ensure_ascii=False,
                    ),
                },
            ],
            format="json",
            options={"temperature": 0},
        )

        return _validate_result(
            _extract_json(response["message"]["content"])
        )

    def understand(
        self,
        user_text,
        current_surah,
        current_ayah,
        surah_names,
    ):
        """Classify an Arabic request using Gemini or local Ollama."""

        if not user_text or not user_text.strip():
            return {
                "action": "chat",
                "surah": None,
                "ayah": None,
                "query": "",
                "reply": "لم أتمكن من فهم الأمر. حاول كتابته بوضوح.",
            }

        context = self._build_context(
            user_text,
            current_surah,
            current_ayah,
            surah_names,
        )

        if self.provider == "ollama":
            return self._understand_with_ollama(context)

        try:
            return self._understand_with_gemini(context)

        except Exception as gemini_error:
            # If Gemini fails, try the existing local Ollama model.
            try:
                return self._understand_with_ollama(context)

            except Exception as ollama_error:
                raise RuntimeError(
                    "تعذر استخدام Gemini وOllama.\n"
                    f"Gemini: {gemini_error}\n"
                    f"Ollama: {ollama_error}"
                ) from ollama_error