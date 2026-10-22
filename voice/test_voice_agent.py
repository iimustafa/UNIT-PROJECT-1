from voice.voice_agent import VoiceAgent


def main():
    agent = VoiceAgent(
        model_size="small",
        recording_seconds=6,
    )

    text = agent.run_once()

    if text:
        print("\nنجح الاختبار: تم التعرف على الكلام.")
    else:
        print("\nلم ينجح الاختبار. راجع رسالة الخطأ أعلاه.")


if __name__ == "__main__":
    main()
