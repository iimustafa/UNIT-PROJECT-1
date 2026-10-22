
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from quran.quran_reader import QuranReader
from tafsir.tafsir_reader import TafsirReader
from interface.arabic_ui import (
    show_header,
    show_menu,
    show_ayah,
    show_message,
)
from interface.arabic_text import ArabicText
from player.audio_player import AudioPlayer
from commands.intent_parser import IntentParser
from voice.voice_agent import VoiceAgent


BASE_DIR = Path(__file__).resolve().parents[1]
QURAN_FILE = BASE_DIR / "data" / "quran.json"
TAFSIR_FILE = BASE_DIR / "data" / "tafsir.json"


def normalize_digits(value):
    """تحويل الأرقام العربية والفارسية إلى أرقام إنجليزية لسهولة المعالجة."""
    translation = str.maketrans(
        "٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹",
        "01234567890123456789",
    )
    return str(value).translate(translation)


MENU_OPTIONS = [
    ("1", "قراءة القرآن"),
    ("2", "الآية التالية"),
    ("3", "الآية السابقة"),
    ("4", "الانتقال إلى آية"),
    ("5", "تكرار الآية"),
    ("6", "التفسير الميسّر"),
    ("7", "البحث في القرآن"),
    ("8", "مساعدة"),
    ("9", "استماع وتكرار الآية 3 مرات"),
    ("10", "استماع إلى السورة الحالية"),
    ("11", "إيقاف التلاوة"),
    ("12", "الوكيل الذكي — أمر باللغة العربية"),
    ("13", "الوكيل الصوتي — التحدث باللغة العربية"),
    ("0", "خروج"),
]


def show_current_ayah(console, quran, surah, ayah):
    item = quran.find(surah, ayah)

    if item is None:
        show_message(console, "لم يتم العثور على الآية.")
        return None

    show_ayah(console, item)
    return item


def show_tafsir(console, tafsir, surah, ayah):
    text = tafsir.get(surah, ayah)

    if text is None:
        show_message(
            console,
            "التفسير غير متوفر لهذه الآية.",
            "yellow",
        )
        return

    console.print(
        Panel(
            Text(ArabicText(text), justify="right"),
            title=ArabicText(f"التفسير الميسّر — {surah}:{ayah}"),
            border_style="green",
            padding=(1, 2),
        )
    )


def search_ayahs(console, quran, query=None):
    if query is None:
        query = console.input(
            f"[bold cyan]{ArabicText('اكتب كلمة أو عبارة للبحث: ')}[/]"
        ).strip()

    if not query:
        show_message(
            console,
            "اكتب كلمة أو عبارة للبحث.",
            "yellow",
        )
        return

    results = quran.search(query)

    if not results:
        show_message(console, "لم يتم العثور على نتائج.")
        return

    console.print(
        f"\n[bold green]{ArabicText('عدد النتائج')}: "
        f"{len(results)}[/]\n"
    )

    for item in results[:50]:
        console.print(
            Panel(
                Text(ArabicText(item["text"]), justify="right"),
                title=ArabicText(
                    f'{item["surah_name"]} — السورة '
                    f'{item["surah_number"]}، الآية '
                    f'{item["ayah_number"]}'
                ),
                border_style="blue",
            )
        )

    if len(results) > 50:
        show_message(
            console,
            "تم عرض أول 50 نتيجة فقط.",
            "yellow",
        )


def show_help(console):
    help_text = (
        "1. قراءة آية\n"
        "2. الانتقال إلى الآية التالية\n"
        "3. الرجوع إلى الآية السابقة\n"
        "4. الانتقال إلى سورة وآية محددتين\n"
        "5. إعادة عرض الآية الحالية\n"
        "6. عرض التفسير الميسّر\n"
        "7. البحث في نص القرآن\n"
        "8. عرض المساعدة\n"
        "9. تشغيل الآية الحالية 3 مرات\n"
        "10. تشغيل السورة الحالية\n"
        "11. إيقاف التلاوة\n"
        "12. كتابة أمر للوكيل الذكي\n"
        "13. التحدث مع الوكيل الصوتي\n"
        "0. الخروج من البرنامج"
    )

    console.print(
        Panel(
            ArabicText(help_text),
            title=ArabicText("المساعدة"),
            border_style="cyan",
        )
    )


def build_surah_names(quran):
    """إنشاء قاموس بأسماء السور من بيانات القرآن الموجودة."""
    names = {}

    for item in quran.ayahs:
        names.setdefault(
            item["surah_number"],
            item["surah_name"],
        )

    return names


def handle_smart_command(
    console,
    parser,
    quran,
    tafsir,
    player,
    current_surah,
    current_ayah,
    command=None,
    voice_agent=None,
):
    # إذا لم يصل أمر جاهز، نطلبه من المستخدم كتابةً.
    if command is None:
        command = console.input(
            f"\n[bold cyan]{ArabicText('اكتب أمرك لتيسير: ')}[/]"
        ).strip()

    if not command:
        show_message(
            console,
            "لم يتم إدخال أي أمر.",
            "yellow",
        )
        return current_surah, current_ayah

    # نرسل النص كما هو إلى محلل الأوامر.
    command = normalize_digits(command)
    intent = parser.parse(command)
    response = ""

    if intent.action == "unknown":
        response = (
            "لم أفهم الأمر. جرّب الآية التالية، أو اعرض التفسير، "
            "أو انتقل إلى سورة الملك الآية 5، أو ابحث عن الحمد لله."
        )
        show_message(console, response, "yellow")
        if voice_agent is not None:
            try:
                voice_agent.speak(response)
            except Exception as error:
                show_message(console, f"تعذرت الاستجابة الصوتية: {error}", "yellow")
        return current_surah, current_ayah

    if intent.action == "read":
        item = show_current_ayah(
            console, quran, current_surah, current_ayah
        )
        if item:
            response = item.get("text", "")

    elif intent.action == "next":
        if quran.find(current_surah, current_ayah + 1):
            current_ayah += 1
        else:
            next_surah = current_surah + 1

            while (
                next_surah <= 114
                and not quran.find(next_surah, 1)
            ):
                next_surah += 1

            if next_surah <= 114:
                current_surah = next_surah
                current_ayah = 1
            else:
                show_message(
                    console,
                    "وصلت إلى نهاية القرآن الكريم.",
                )
                return current_surah, current_ayah

        item = show_current_ayah(
            console, quran, current_surah, current_ayah
        )
        if item:
            response = item.get("text", "")

    elif intent.action == "previous":
        if current_ayah > 1:
            current_ayah -= 1

        elif current_surah > 1:
            previous_surah = current_surah - 1

            while (
                previous_surah > 1
                and not quran.get_surah(previous_surah)
            ):
                previous_surah -= 1

            ayahs = quran.get_surah(previous_surah)

            if ayahs:
                current_surah = previous_surah
                current_ayah = ayahs[-1]["ayah_number"]

        else:
            show_message(
                console,
                "أنت في بداية القرآن الكريم.",
                "yellow",
            )
            return current_surah, current_ayah

        item = show_current_ayah(
            console, quran, current_surah, current_ayah
        )
        if item:
            response = item.get("text", "")

    elif intent.action == "goto":
        if intent.surah is None or intent.ayah is None:
            show_message(
                console,
                "حدّد السورة والآية، مثل: "
                "انتقل إلى سورة الملك الآية 5.",
                "yellow",
            )
            return current_surah, current_ayah

        item = quran.find(intent.surah, intent.ayah)

        if item is None:
            show_message(
                console,
                "السورة أو الآية غير موجودة.",
                "yellow",
            )
            return current_surah, current_ayah

        current_surah = intent.surah
        current_ayah = intent.ayah

        show_ayah(console, item)
        response = item.get("text", "")

    elif intent.action == "tafsir":
        show_tafsir(console, tafsir, current_surah, current_ayah)
        tafsir_text = tafsir.get(current_surah, current_ayah)
        if isinstance(tafsir_text, str):
            response = tafsir_text
        elif isinstance(tafsir_text, dict):
            response = (
                tafsir_text.get("text")
                or tafsir_text.get("tafsir")
                or "تم عرض التفسير على الشاشة."
            )
        else:
            response = "تم عرض التفسير على الشاشة."

    elif intent.action == "repeat":
        item = show_current_ayah(
            console, quran, current_surah, current_ayah
        )
        if item:
            response = item.get("text", "")

    elif intent.action == "search":
        search_ayahs(console, quran, intent.query)
        response = "تم تنفيذ البحث في القرآن الكريم."

    elif intent.action == "play_ayah":
        player.play_ayah(current_surah, current_ayah, repeats=1)
        response = "تم طلب تشغيل الآية الحالية."

    elif intent.action == "play_surah":
        player.play_surah(quran.get_surah(current_surah))
        response = "تم طلب تشغيل السورة الحالية."

    elif intent.action == "stop":
        player.stop()
        response = "تم طلب إيقاف التلاوة."
        show_message(console, response)

    elif intent.action == "help":
        show_help(console)
        response = (
            "يمكنك طلب قراءة الآية، أو الانتقال للآية التالية، "
            "أو عرض التفسير، أو البحث في القرآن الكريم."
        )

    elif intent.action == "exit":
        response = "للخروج من البرنامج، اختر صفر من القائمة الرئيسية."
        show_message(console, response, "yellow")

    if voice_agent is not None and response:
        try:
            voice_agent.speak(str(response))
        except Exception as error:
            show_message(
                console,
                f"تعذرت الاستجابة الصوتية: {error}",
                "yellow",
            )

    return current_surah, current_ayah


def run_cli():
    console = Console()

    try:
        quran = QuranReader(QURAN_FILE)
        tafsir = TafsirReader(TAFSIR_FILE)

    except (OSError, ValueError) as error:
        show_message(
            console,
            f"تعذّر تحميل البيانات: {error}",
            "red",
        )
        return

    if not quran.ayahs:
        show_message(
            console,
            "ملف القرآن لا يحتوي على آيات.",
            "red",
        )
        return

    try:
        player = AudioPlayer()

    except Exception as error:
        show_message(
            console,
            f"تعذّر تهيئة مشغل الصوت: {error}",
            "red",
        )
        return

    parser = IntentParser(build_surah_names(quran))

    current_surah = 1
    current_ayah = 1

    # يُحمّل نموذج Whisper عند استخدام الخيار الصوتي،
    # وليس عند بدء البرنامج.
    voice_agent = None

    try:
        show_header(console)

        console.print(
            f"[green]{ArabicText('تم تحميل')} "
            f"{quran.get_ayah_count()} "
            f"{ArabicText('آية.')}[/]"
        )

        console.print(
            f"[green]{ArabicText('عدد التفسيرات المحمّلة:')} "
            f"{tafsir.get_count()}[/]"
        )

        show_current_ayah(
            console,
            quran,
            current_surah,
            current_ayah,
        )

        while True:
            show_menu(console, MENU_OPTIONS)

            choice = console.input(
                f"\n[bold cyan]{ArabicText('اختر رقم العملية: ')}[/]"
            ).strip()
            choice = normalize_digits(choice)

            if choice == "0":
                show_message(
                    console,
                    "شكرًا لاستخدام تيسير.",
                )
                break

            elif choice == "1":
                show_current_ayah(
                    console,
                    quran,
                    current_surah,
                    current_ayah,
                )

            elif choice == "2":
                if quran.find(
                    current_surah,
                    current_ayah + 1,
                ):
                    current_ayah += 1

                else:
                    next_surah = current_surah + 1

                    while (
                        next_surah <= 114
                        and not quran.find(next_surah, 1)
                    ):
                        next_surah += 1

                    if next_surah <= 114:
                        current_surah = next_surah
                        current_ayah = 1

                    else:
                        show_message(
                            console,
                            "وصلت إلى نهاية القرآن الكريم.",
                        )
                        continue

                show_current_ayah(
                    console,
                    quran,
                    current_surah,
                    current_ayah,
                )

            elif choice == "3":
                if current_ayah > 1:
                    current_ayah -= 1

                elif current_surah > 1:
                    previous_surah = current_surah - 1

                    while (
                        previous_surah > 1
                        and not quran.get_surah(previous_surah)
                    ):
                        previous_surah -= 1

                    previous_ayahs = quran.get_surah(
                        previous_surah
                    )

                    if previous_ayahs:
                        current_surah = previous_surah
                        current_ayah = previous_ayahs[-1][
                            "ayah_number"
                        ]

                else:
                    show_message(
                        console,
                        "أنت في بداية القرآن الكريم.",
                        "yellow",
                    )
                    continue

                show_current_ayah(
                    console,
                    quran,
                    current_surah,
                    current_ayah,
                )

            elif choice == "4":
                try:
                    surah_text = console.input(
                        ArabicText("أدخل رقم السورة: ")
                    ).strip()
                    ayah_text = console.input(
                        ArabicText("أدخل رقم الآية: ")
                    ).strip()

                    surah = int(normalize_digits(surah_text))
                    ayah = int(normalize_digits(ayah_text))

                except ValueError:
                    show_message(
                        console,
                        "أدخل أرقامًا صحيحة.",
                        "red",
                    )
                    continue

                item = quran.find(surah, ayah)

                if item is None:
                    show_message(
                        console,
                        "السورة أو الآية غير موجودة.",
                        "yellow",
                    )
                    continue

                current_surah, current_ayah = surah, ayah
                show_ayah(console, item)

            elif choice == "5":
                show_current_ayah(
                    console,
                    quran,
                    current_surah,
                    current_ayah,
                )

            elif choice == "6":
                show_tafsir(
                    console,
                    tafsir,
                    current_surah,
                    current_ayah,
                )

            elif choice == "7":
                search_ayahs(console, quran)

            elif choice == "8":
                show_help(console)

            elif choice == "9":
                player.play_ayah(
                    current_surah,
                    current_ayah,
                    repeats=3,
                )

            elif choice == "10":
                player.play_surah(
                    quran.get_surah(current_surah)
                )

            elif choice == "11":
                player.stop()

            elif choice == "12":
                current_surah, current_ayah = handle_smart_command(
                    console,
                    parser,
                    quran,
                    tafsir,
                    player,
                    current_surah,
                    current_ayah,
                )

            elif choice == "13":
                try:
                    if voice_agent is None:
                        voice_agent = VoiceAgent()

                    recognized_text = voice_agent.listen()

                    if recognized_text:
                        console.print(
                            f"\n[bold green]"
                            f"{ArabicText('الأمر الذي تم التعرف عليه:')}"
                            f"[/]"
                        )
                        console.print(
                            Text(
                                ArabicText(recognized_text),
                                justify="right",
                            )
                        )

                        current_surah, current_ayah = (
                            handle_smart_command(
                                console,
                                parser,
                                quran,
                                tafsir,
                                player,
                                current_surah,
                                current_ayah,
                                command=recognized_text,
                                voice_agent=voice_agent,
                            )
                        )

                    else:
                        show_message(
                            console,
                            "لم يتم التعرف على الأمر. حاول مرة أخرى.",
                            "yellow",
                        )

                except Exception as error:
                    show_message(
                        console,
                        f"تعذّر تشغيل الوكيل الصوتي: {error}",
                        "red",
                    )

            else:
                show_message(
                    console,
                    "اختيار غير صحيح. حاول مرة أخرى.",
                    "yellow",
                )

    except KeyboardInterrupt:
        show_message(
            console,
            "تم إيقاف البرنامج.",
        )

    finally:
        player.close()


if __name__ == "__main__":
    run_cli()
