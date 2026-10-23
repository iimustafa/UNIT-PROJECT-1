"""OpenAI-powered command understanding for the Taysir CLI."""

import json
import os
import tempfile

import sounddevice as sd
from scipy.io.wavfile import write as write_wav

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


ACTIONS = [
    "read", "next", "previous", "goto", "tafsir", "repeat", "search",
    "play_ayah", "play_surah", "stop", "help", "exit", "chat",
]

SCHEMA = {
    "type": "object",
    "properties": {
        "action": {"type": "string", "enum": ACTIONS},
        "surah": {"type": ["integer", "null"]},
        "ayah": {"type": ["integer", "null"]},
        "query": {"type": "string"},
        "reply": {"type": "string"},
    },
    "required": ["action", "surah", "ayah", "query", "reply"],
    "additionalProperties": False,
}

INSTRUCTIONS = """
أنت وكيل الأوامر والمحادثة لتطبيق تيسير، وهو قارئ قرآن يعمل محليًا.
افهم العربية الفصحى واللهجات العربية والأوامر القصيرة والأخطاء الإملائية البسيطة.
مهمتك إما تحديد أمر من القائمة أو الرد بمحادثة قصيرة.
الأفعال المسموحة:
read=عرض الآية الحالية، next=الآية التالية، previous=الآية السابقة،
goto=الانتقال إلى سورة وآية محددتين، tafsir=عرض التفسير الميسر للآية الحالية،
repeat=إعادة عرض الآية الحالية، search=البحث عن عبارة في نص القرآن،
play_ayah=تشغيل الآية الحالية، play_surah=تشغيل السورة الحالية،
stop=إيقاف التلاوة، help=شرح الاستخدام، exit=طلب الخروج من المحادثة،
chat=محادثة عادية أو طلب توضيح.

أمثلة:
"ودي أروح لسورة الملك عند الآية خمسة" => goto، surah=67، ayah=5.
"رجعني آية" => previous.
"اقرأ اللي بعدها" => next.
"وش تفسيرها؟" => tafsir.
"دور على الحمد لله" => search مع query="الحمد لله".
"شغلها" => play_ayah.

استخدم أسماء السور الواردة في سياق المستخدم لتحديد رقم السورة بدقة.
إذا كان الأمر ناقصًا أو غامضًا، لا تخمّن رقم السورة أو الآية؛ اختر chat واسأل سؤال توضيح قصيرًا بالعربية.
إذا كان السؤال الديني يحتاج تفسيرًا أو معلومة غير موجودة في بيانات التطبيق، لا تخترع آية أو تفسيرًا؛ قل بلطف إنك تستطيع عرض الآية أو التفسير الميسر من داخل التطبيق.
لا تدّع أنك نفذت أي أمر بنفسك؛ البرنامج المحلي هو الذي ينفذ الأمر بعد تصنيفك.
أعد JSON مطابقًا للمخطط فقط. اترك surah و ayah بقيمة null إذا لم يكونا مطلوبين، و query فارغًا إذا لم يكن هناك بحث.
""".strip()


class TaysirAIAgent:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "لم يتم العثور على OPENAI_API_KEY. أضف مفتاح OpenAI API إلى ملف .env."
            )
        self.client = OpenAI(api_key=api_key)
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    def listen(self, seconds=6, sample_rate=16000):
        """تسجيل الصوت من الميكروفون وتحويله إلى نص عبر OpenAI، دون Whisper/PyAV المحلي."""
        audio = sd.rec(
            int(seconds * sample_rate),
            samplerate=sample_rate,
            channels=1,
            dtype="int16",
        )
        sd.wait()

        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_path = temp_file.name
            write_wav(temp_path, sample_rate, audio)
            with open(temp_path, "rb") as audio_file:
                transcription = self.client.audio.transcriptions.create(
                    model=os.getenv("OPENAI_TRANSCRIPTION_MODEL", "gpt-4o-mini-transcribe"),
                    file=audio_file,
                    language="ar",
                )
            return (getattr(transcription, "text", "") or "").strip()
        finally:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)

    def understand(self, user_text, current_surah, current_ayah, surah_names):
        context = {
            "user_message": user_text,
            "current_location": {
                "surah_number": current_surah,
                "ayah_number": current_ayah,
            },
            "surah_names_number_to_name": {
                str(number): name for number, name in surah_names.items()
            },
        }

        response = self.client.responses.create(
            model=self.model,
            instructions=INSTRUCTIONS,
            input=json.dumps(context, ensure_ascii=False),
            text={
                "format": {
                    "type": "json_schema",
                    "name": "taysir_command",
                    "strict": True,
                    "schema": SCHEMA,
                }
            },
        )

        result = json.loads(response.output_text)
        if result.get("action") not in ACTIONS:
            raise ValueError("أعاد النموذج أمرًا غير مدعوم.")
        return result
