import subprocess

import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel


class VoiceAgent:
    """وكيل صوتي محلي لتطبيق تيسير."""

    def __init__(
        self,
        model_size="small",
        sample_rate=16000,
        recording_seconds=6,
    ):
        self.model_size = model_size
        self.sample_rate = sample_rate
        self.recording_seconds = recording_seconds
        self.model = None

    @staticmethod
    def _print_arabic(message):
        # لا نستخدم ArabicText.shape لتجنب الخطأ السابق.
        print(str(message))

    def _load_model(self):
        """تحميل نموذج التعرف على الكلام عند الحاجة فقط."""
        if self.model is None:
            self._print_arabic(
                "جارٍ تحميل نموذج التعرف على الكلام..."
            )

            self.model = WhisperModel(
                self.model_size,
                device="cpu",
                compute_type="int8",
            )

            self._print_arabic(
                "تم تحميل النموذج بنجاح."
            )

    def record_audio(self):
        """تسجيل الصوت وإرجاعه كمصفوفة صوتية."""
        self._print_arabic(
            f"تحدث الآن باللغة العربية لمدة "
            f"{self.recording_seconds} ثوانٍ..."
        )

        audio = sd.rec(
            int(self.recording_seconds * self.sample_rate),
            samplerate=self.sample_rate,
            channels=1,
            dtype="float32",
        )

        sd.wait()

        # تحويل التسجيل إلى مصفوفة أحادية الأبعاد.
        audio = np.asarray(audio, dtype=np.float32).reshape(-1)

        # منع تمرير تسجيل فارغ إلى Whisper.
        if audio.size == 0:
            raise RuntimeError("لم يتم تسجيل أي صوت.")

        return audio

    def transcribe(self, audio):
        """تحويل المصفوفة الصوتية إلى نص عربي."""
        self._load_model()

        audio = np.asarray(audio, dtype=np.float32).reshape(-1)

        segments, _ = self.model.transcribe(
            audio,
            language="ar",
            beam_size=3,
            vad_filter=False,
        )

        return " ".join(
            segment.text.strip()
            for segment in segments
            if segment.text.strip()
        ).strip()

    def listen(self):
        """التسجيل ثم التعرف على الكلام وإرجاع النص."""
        try:
            audio = self.record_audio()

            self._print_arabic(
                "جارٍ تحويل كلامك إلى نص..."
            )

            recognized_text = self.transcribe(audio)

            if recognized_text:
                self._print_arabic(
                    "النص الذي تم التعرف عليه:"
                )
                self._print_arabic(recognized_text)
            else:
                self._print_arabic(
                    "لم أتمكن من فهم الكلام. حاول مرة أخرى."
                )

            return recognized_text

        except Exception as error:
            self._print_arabic(
                f"تعذر التسجيل أو التعرف على الكلام: {error}"
            )
            return ""

    def speak(self, text):
        """قراءة الرد بصوت macOS."""
        if not text:
            return

        try:
            subprocess.run(
                ["say", str(text)],
                check=True,
                timeout=60,
            )
        except (OSError, subprocess.SubprocessError) as error:
            self._print_arabic(
                f"تعذر تشغيل الرد الصوتي: {error}"
            )

    def run_once(self):
        """تنفيذ دورة واحدة: استماع ثم عرض النص."""
        text = self.listen()

        if text:
            self._print_arabic(
                f"أنت قلت: {text}"
            )

        return text
