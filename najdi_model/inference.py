"""
Standalone inference script for FatimahEmadEldin/habibi-tts-najdi-ft.

Requirements:
    pip install git+https://github.com/SWivid/F5-TTS.git
    pip install git+https://github.com/SWivid/Habibi-TTS.git
    pip install huggingface_hub safetensors soundfile

Usage:
    python inference.py \
        --ref_audio path/to/reference.wav \
        --ref_text "exact transcript of the reference clip" \
        --text "النص المراد تحويله إلى صوت" \
        --out output.wav
"""
import argparse
import torch
import soundfile as sf
from huggingface_hub import hf_hub_download
from f5_tts.model import DiT
from f5_tts.infer.utils_infer import (
    load_model, load_vocoder, preprocess_ref_audio_text,
)
from habibi_tts.infer.utils_infer import infer_process
REPO_ID = "NAMAA-Space/NAMAA-Saudi-TTS-V2"
CKPT_FILE = "model_last.pt"
VOCAB     = "vocab.txt"

V1_BASE_CFG = dict(
    dim=1024, depth=22, heads=16,
    ff_mult=2, text_dim=512, conv_layers=4,
)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--ref_audio", required=True,
                   help="Path to 5-8s clean reference WAV")
    p.add_argument("--ref_text", required=True,
                   help="Exact transcript of the reference clip")
    p.add_argument("--text", required=True,
                   help="Arabic text to synthesize")
    p.add_argument("--out", default="output.wav",
                   help="Output WAV path")
    p.add_argument("--nfe_step", type=int, default=32,
                   help="ODE solver steps (16=fast, 32=default, 64=quality)")
    p.add_argument("--speed", type=float, default=1.0,
                   help="Speech speed multiplier")
    p.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    args = p.parse_args()

    print(f"Downloading model from {REPO_ID}...")
    ckpt_path  = hf_hub_download(repo_id=REPO_ID, filename=CKPT_FILE)
    vocab_path = hf_hub_download(repo_id=REPO_ID, filename=VOCAB)

    print(f"Loading model on {args.device}...")
    model = load_model(DiT, V1_BASE_CFG, ckpt_path,
                       vocab_file=vocab_path, device=args.device)
    model = model.to(torch.float32).eval()
    vocoder = load_vocoder()

    print(f"Preparing reference: {args.ref_audio}")
    ref_audio, ref_text = preprocess_ref_audio_text(args.ref_audio, args.ref_text)

    print(f"Generating: {args.text}")
    wave, sr, _ = infer_process(
        ref_audio, ref_text, args.text,
        model, vocoder,
        nfe_step=args.nfe_step, speed=args.speed,
    )

    sf.write(args.out, wave, sr)
    print(f"✅ Saved to {args.out}  ({len(wave)/sr:.1f}s at {sr} Hz)")


if __name__ == "__main__":
    main()
