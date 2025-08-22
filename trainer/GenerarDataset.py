# GenerarDataset.py
# Uso:
#   ELEVENLABS_API_KEY=... ELEVENLABS_VOICE_ID=... python GenerarDataset.py \
#       --prompts prompts_es.txt \
#       --out dataset_eleven \
#       --coqui   # (opcional) genera 22.05k/mono + metadata.csv
#
# Requisitos:
#   pip install pydub python-dotenv
#   ffmpeg en PATH (para remuestrear con pydub)
#
from __future__ import annotations

import argparse
import os
import re
from pathlib import Path

# Si tu repo usa un layout distinto, ajusta este import:
from services.tts_service_elevenlabs import ElevenLabsTTSService

try:
    from pydub import AudioSegment
except Exception:
    AudioSegment = None

TAGS_PATTERN = re.compile(r"\[[^\]]+\]")
BREAK_PATTERN = re.compile(r"<\s*break\s+[^>]*\/\s*>", re.IGNORECASE)
WS = re.compile(r"\s+")

def clean_text_for_metadata(text: str) -> str:
    t = TAGS_PATTERN.sub("", text)
    t = BREAK_PATTERN.sub(" ", t)
    t = WS.sub(" ", t)
    return t.strip()

def resample_44100_to_22050_mono(src_wav: Path, dst_wav: Path):
    if AudioSegment is None:
        raise RuntimeError("pydub no está instalado. Ejecuta: pip install pydub (y asegura ffmpeg en PATH)")
    audio = AudioSegment.from_file(src_wav)
    audio = audio.set_frame_rate(22050).set_channels(1).set_sample_width(2)
    audio.export(dst_wav, format="wav")

def main():
    parser = argparse.ArgumentParser(description="Genera audios con Eleven v3 (synthesize) y dataset para Coqui (opcional).")
    parser.add_argument("--prompts", required=True, help="Archivo de prompts (una línea por frase).")
    parser.add_argument("--out", required=True, help="Carpeta de salida base.")
    parser.add_argument("--model", default="eleven_v3", help="Modelo de Eleven (por defecto: eleven_v3).")
    parser.add_argument("--stability", type=float, default=0.45)
    parser.add_argument("--similarity", type=float, default=0.90)
    parser.add_argument("--style", type=float, default=0.75)
    parser.add_argument("--speed", type=float, default=0.98)
    parser.add_argument("--speaker-boost", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--coqui", action="store_true", help="Genera wavs 22.05k/mono + metadata.csv")
    args = parser.parse_args()

    api_key = os.getenv("ELEVENLABS_API_KEY", "")
    voice_id = os.getenv("ELEVENLABS_VOICE_ID", "")
    if not api_key:
        raise EnvironmentError("Falta ELEVENLABS_API_KEY")
    if not voice_id:
        raise EnvironmentError("Falta ELEVENLABS_VOICE_ID")

    prompts_path = Path(args.prompts)
    if not prompts_path.exists():
        raise FileNotFoundError(f"No existe {prompts_path}")

    out_base = Path(args.out)
    out_44 = out_base / "wav_44100"
    out_22 = out_base / "wavs"       # estándar Coqui = 'wavs'
    out_base.mkdir(parents=True, exist_ok=True)
    out_44.mkdir(parents=True, exist_ok=True)
    if args.coqui:
        out_22.mkdir(parents=True, exist_ok=True)

    # Inicializa tu servicio
    tts = ElevenLabsTTSService(api_key=api_key, voice_id=voice_id)

    # Lee prompts
    prompts = [line.strip() for line in prompts_path.read_text(encoding="utf-8").splitlines() if line.strip()]

    # Genera audios
    meta_lines = []
    for i, text in enumerate(prompts, start=1):
        fn44 = out_44 / f"sample_{i:03d}.wav"
        print(f"[{i}/{len(prompts)}] Generando: {fn44.name}")

        # Preferimos 'synthesize' (sin timestamps). Si tu servicio no lo tuviera, hacemos fallback a synthesize_with_timestamps.
        ok = False
        if hasattr(tts, "synthesize"):
            try:
                tts.synthesize(
                    text=text,
                    output_path=str(fn44),
                    model_id=args.model,
                    stability=args.stability,
                    similarity_boost=args.similarity,
                    style=args.style if hasattr(tts, "synthesize") else None,  # por si tu signature no acepta 'style'
                    speed=args.speed if hasattr(tts, "synthesize") else None,
                    output_format="wav_44100_16bit_mono",
                    seed=args.seed,
                    force_regenerate=False,
                )
                ok = True
            except TypeError:
                # Si la firma de tu synthesize no soporta algunos kwargs
                tts.synthesize(
                    text=text,
                    output_path=str(fn44),
                    model_id=args.model,
                    stability=args.stability,
                    similarity_boost=args.similarity,
                    output_format="wav_44100_16bit_mono",
                    seed=args.seed,
                    force_regenerate=False,
                )
                ok = True

        if not ok and hasattr(tts, "synthesize_with_timestamps"):
            # Fallback: usa el método con timestamps y extrae el path
            result = tts.synthesize_with_timestamps(
                text=text,
                output_path=str(fn44),
                model_id=args.model,
                stability=args.stability,
                similarity_boost=args.similarity,
                output_format="wav_44100_16bit_mono",
                seed=args.seed,
            )
            if isinstance(result, dict) and result.get("audio_path"):
                ok = True

        if not ok:
            print(f"⚠️  No se pudo generar {fn44.name}")
            continue

        if args.coqui:
            fn22 = out_22 / f"sample_{i:03d}.wav"
            resample_44100_to_22050_mono(fn44, fn22)
            clean = clean_text_for_metadata(text)
            meta_lines.append(f"{fn22.name}|{clean}")

    # Crea metadata.csv (solo si --coqui)
    if args.coqui and meta_lines:
        (out_base / "metadata.csv").write_text("\n".join(meta_lines), encoding="utf-8")
        print(f"✅ metadata.csv creado en: {out_base / 'metadata.csv'}")

    print(f"✅ Audios 44.1k en: {out_44}")
    if args.coqui:
        print(f"✅ Audios 22.05k/mono en: {out_22}")

if __name__ == "__main__":
    main()
