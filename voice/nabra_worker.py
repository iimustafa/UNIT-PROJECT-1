import argparse
import sys
import wave
from pathlib import Path

import numpy as np
from huggingface_hub import snapshot_download


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--text", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    model_dir = Path(
        snapshot_download(repo_id="oddadmix/Nabra-Saudi-82M")
    ).resolve()

    sys.path.insert(0, str(model_dir))

    from load_model import load

    print("جارٍ تجهيز نموذج الصوت السعودي...", file=sys.stderr)
    model, pipeline, voice = load(device="cpu")

    result = next(pipeline(args.text, voice=voice))
    audio = result[2]

    if hasattr(audio, "detach"):
        audio = audio.detach().cpu().numpy()

    audio = np.asarray(audio, dtype=np.float32).squeeze()

    if audio.size == 0:
        raise RuntimeError("لم ينتج النموذج صوتًا.")

    audio = np.nan_to_num(audio)
    peak = float(np.max(np.abs(audio)))

    if peak > 0:
        audio = audio * min(1.0, 0.95 / peak)

    pcm = (audio * 32767).astype(np.int16)

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    with wave.open(str(output), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(24000)
        wav.writeframes(pcm.tobytes())

    print("تم إنشاء الملف الصوتي.", file=sys.stderr)


if __name__ == "__main__":
    main()
