import subprocess
import threading


class TTSEngine:
    """تحويل النص إلى كلام باستخدام صوت Majed العربي في macOS."""

    def __init__(self, voice="Majed", rate=175):
        self.voice = voice
        self.rate = rate
        self._lock = threading.Lock()

    def speak(self, text):
        if not isinstance(text, str) or not text.strip():
            return False

        command = [
            "say",
            "-v", self.voice,
            "-r", str(self.rate),
            text.strip(),
        ]

        try:
            with self._lock:
                subprocess.run(command, check=True)
            return True

        except (OSError, subprocess.SubprocessError) as error:
            print(f"تعذر تشغيل الصوت: {error}")
            return False
