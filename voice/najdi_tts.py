import subprocess
import tempfile
import threading
from pathlib import Path

from voice.arabic_pronunciation import prepare_arabic_for_tts


PROJECT_DIR = Path(__file__).resolve().parents[1]
WORKER_FILE = PROJECT_DIR / "voice" / "nabra_worker.py"
TTS_PYTHON = PROJECT_DIR / ".venv-najdi-tts" / "bin" / "python"


class NajdiTTS:
    """توليد صوت سعودي محلي باستخدام نموذج Nabra-Saudi-82M."""

    def __init__(self, volume=1.0):
        self.volume = max(0.1, min(float(volume), 1.0))
        self._speak_lock = threading.Lock()

    def speak(self, text):
        text = prepare_arabic_for_tts(str(text)).strip()

        if not text:
            return False

        if not TTS_PYTHON.is_file():
            print(
                "تعذر توليد الصوت: لم يتم العثور على بيئة "
                ".venv-najdi-tts."
            )
            return False

        if not WORKER_FILE.is_file():
            print("تعذر توليد الصوت: ملف nabra_worker.py غير موجود.")
            return False

        output_path = None

        try:
            with self._speak_lock:
                with tempfile.NamedTemporaryFile(
                    suffix=".wav",
                    prefix="taysir_saudi_",
                    delete=False,
                ) as temporary_file:
                    output_path = Path(temporary_file.name)

                subprocess.run(
                    [
                        str(TTS_PYTHON),
                        str(WORKER_FILE),
                        "--text",
                        text,
                        "--output",
                        str(output_path),
                    ],
                    cwd=str(PROJECT_DIR),
                    check=True,
                    timeout=300,
                    capture_output=True,
                    text=True,
                )

                if not output_path.exists() or output_path.stat().st_size <= 44:
                    raise RuntimeError("لم يتم إنشاء ملف صوتي صالح.")

                subprocess.run(
                    ["afplay", "-v", str(self.volume), str(output_path)],
                    check=True,
                    timeout=300,
                    capture_output=True,
                    text=True,
                )

                return True

        except subprocess.TimeoutExpired:
            print("استغرق توليد الصوت وقتًا أطول من المتوقع.")
            return False

        except subprocess.CalledProcessError as error:
            details = (error.stderr or error.stdout or "").strip()
            if details:
                print(f"تعذر توليد الصوت السعودي:\n{details[-2500:]}")
            else:
                print("تعذر توليد الصوت السعودي.")
            return False

        except Exception as error:
            print(f"تعذر توليد الصوت السعودي: {error}")
            return False

        finally:
            if output_path and output_path.exists():
                output_path.unlink()
