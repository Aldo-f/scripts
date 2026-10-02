"""
Whisper Audio CAPTCHA Solver
Uses tiny Whisper model for speech-to-text CAPTCHA solving
"""
import time
import logging
import subprocess
import os
from pathlib import Path

logger = logging.getLogger("form_automation.whisper_solver")


def install_whisper_if_needed():
    """Ensure whisper.cpp is built and tiny model is downloaded."""
    whisper_dir = Path.home() / ".cache" / "hermes" / "whisper.cpp"
    models_dir = Path.home() / ".cache" / "hermes" / "models"

    if not whisper_dir.exists():
        logger.info("Setting up whisper.cpp runtime...")
        subprocess.run(["git", "clone", "https://github.com/ggerganis/whisper.cpp.git", str(whisper_dir)], check=True)
        os.chdir(str(whisper_dir))
        subprocess.run(["cmake", "-B", "build", "-D", "WHISPER_CUBLAS=1"], check=True)
        subprocess.run(["cmake", "--build", "build", "--config", "Release"], check=True)
    else:
        os.chdir(str(whisper_dir))

    tiny_model = models_dir / "ggml-tiny.bin"
    if not tiny_model.exists():
        logger.info("Downloading Whisper tiny model...")
        subprocess.run([str(whisper_dir / "models" / "download-ggml.sh"), "tiny"], check=True)

    return str(whisper_dir / "build" / "main"), str(tiny_model)


def solve_audio_captcha(wav_file: str, lang="en") -> str:
    """Transcribe CAPTCHA audio file using local Whisper tiny model."""
    whisper_bin, model_bin = install_whisper_if_needed()

    temp_dir = Path.home() / "scripts" / "form-automation-v2" / "logs" / "audio_buffer"
    temp_dir.mkdir(parents=True, exist_ok=True)

    wav_out = str(temp_dir / "captcha_audio.wav")

    try:
        subprocess.run(
            ["ffmpeg", "-i", wav_file, "-ar", "16k", "-ac", "1", wav_out],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except Exception as e:
        logger.warning(f"Audio conversion failed: {e}")
        return ""

    cmd = [
        whisper_bin,
        "-m", model_bin,
        "-f", wav_out,
        "-l", lang,
        "--no-speech-thresh", "0.5",
        "--output_txt"
    ]

    try:
        start = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        elapsed = time.time() - start

        # Whisper outputs txt file with same base name
        txt_file = temp_dir / Path(wav_file).stem
        if txt_file.exists():
            transcription = txt_file.read_text().strip()
            logger.info(f"Whisper solved CAPTCHA in {elapsed:.2f}s: {transcription}")
            return transcription

        # Fallback parse output
        if result.stdout:
            lines = [l for l in result.stdout.splitlines() if l.strip()]
            if lines:
                return lines[0].strip()

    except Exception as e:
        logger.error(f"Whisper solve failed: {e}")

    return ""


def solve_with_human_fallback():
    """Fallback to manual solving with prompt."""
    print("\n" + "=" * 60)
    print("CAPTCHA DETECTED - Manual solve required")
    print("Solve CAPTCHA manually, paste the solution here:")
    print("=" * 60 + "\n")
    answer = input("Enter CAPTCHA text: ").strip()
    logger.info(f"Human solved CAPTCHA: {answer}")
    return answer