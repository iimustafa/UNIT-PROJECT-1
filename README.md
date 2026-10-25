# Taysir — تيسير

**A Python-based Quran companion with verse navigation, Tafsir, recitation playback, and an optional Arabic smart assistant.**

Taysir is a command-line application designed to make it easier to read and navigate the Holy Quran, search its text, consult Tafsir Al-Muyassar, and listen to recitation. It also includes an optional AI assistant for text-based or voice-based interaction.

> **Project status:** A learning and development project. Features that depend on external AI services, local speech models, or audio assets may require additional setup.

## Features

- Read Quranic verses and navigate between verses and surahs.
- Jump to a specific surah and verse.
- Search the Quran text.
- View Tafsir Al-Muyassar.
- Play a selected verse or the current surah.
- Repeat the current verse for a user-selected number of times.
- Use a hybrid smart assistant for natural-language commands and conversation.
- Optional Arabic speech input and Saudi Arabic speech output, depending on local model setup.

## Technology Stack

| Area | Technologies |
| --- | --- |
| Core application | Python |
| Terminal interface | Rich |
| Quran and Tafsir data | Local JSON data files |
| Audio playback | Project audio player and macOS audio playback support |
| Speech recognition | `faster-whisper`, `sounddevice` |
| Saudi Arabic speech output | Nabra-Saudi-82M, PyTorch (separate TTS environment) |
| AI assistant integration | Google Gen AI SDK and/or Ollama, depending on configuration |
| Arabic text rendering | `arabic-reshaper`, `python-bidi` |

## Project Structure

```text
Taysir/
├── commands/       # Menu, command handling, and intent parsing
├── data/           # Quran and Tafsir data files
├── interface/      # Arabic CLI display and text formatting
├── player/         # Quran recitation playback
├── quran/          # Quran data access and search
├── scripts/        # Data preparation and utility scripts
├── tafsir/         # Tafsir data access
├── voice/          # Voice input and Saudi Arabic TTS integration
├── tests/          # Project tests
├── main.py         # CLI entry point
├── gui.py          # GUI entry point / experimental interface
└── requirements.txt
```

## Requirements

- macOS is the primary development environment.
- Python 3.12 was used during development.
- Git.
- Audio output; a microphone is needed for voice input.
- Optional: internet access and credentials for a configured AI provider.
- Optional: the separate `.venv-najdi-tts` environment for local Nabra-based Saudi Arabic speech output.

## Setup

Clone the repository and enter the project folder:

```bash
git clone https://github.com/iimustafa/UNIT-PROJECT-1.git
cd UNIT-PROJECT-1
```

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Run the command-line application:

```bash
python main.py
```

If your local copy is named `Taysir`, run the commands from that folder instead.

## Optional voice setup

Voice features may require additional packages and local model downloads. The Saudi Arabic TTS implementation uses **Nabra-Saudi-82M** in a separate Python environment so that its PyTorch dependencies do not interfere with the main application environment.

The voice components are optional; the core Quran-reading and search features should be treated separately from model-dependent voice features. Follow the project’s current environment setup and model requirements before enabling voice features on a new machine.

## Data and content

The application reads Quran and Tafsir content from local JSON files under `data/`. The development copy contains 6,236 Quranic ayah records and 6,236 Tafsir records. Preserve the integrity of Quranic text and verify data-source terms and attribution when redistributing source data.

## Notes

- AI responses and voice functionality depend on local configuration and may not be available immediately after a fresh installation.
- Do not commit API keys or secrets. Keep them in a local `.env` file and ensure that file is excluded from Git.
- Large audio/model files and virtual environments should not be committed to the repository.
- This README describes the current intended functionality; setup details may vary with the exact project version.

## Author

Developed by **Mustafa Al-Ali**.

## Repository

[GitHub — UNIT-PROJECT-1](https://github.com/iimustafa/UNIT-PROJECT-1)
