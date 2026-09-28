from pathlib import Path

from faster_whisper import WhisperModel


# --------------------------------------------------
# PROJECT PATH
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent


# --------------------------------------------------
# WHISPER MODEL
import torch

MODEL = None


def get_model():
    global MODEL

    if MODEL is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        compute_type = "float16" if device == "cuda" else "int8"
        print(f"Loading Whisper Tiny model on {device} ({compute_type})...")

        MODEL = WhisperModel(
            "tiny",
            device=device,
            compute_type=compute_type
        )

        print(f"Whisper Tiny model loaded on {device}.")

    return MODEL


# --------------------------------------------------
# SRT TIME FORMAT
# --------------------------------------------------

def format_time(seconds):
    milliseconds = int(seconds * 1000)

    hours = milliseconds // 3_600_000
    milliseconds %= 3_600_000

    minutes = milliseconds // 60_000
    milliseconds %= 60_000

    secs = milliseconds // 1000
    milliseconds %= 1000

    return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"


# --------------------------------------------------
# GENERATE SUBTITLES
# --------------------------------------------------

def generate_subtitles(audio_path: str, output_path: str):

    audio_file = Path(audio_path)
    subtitle_file = Path(output_path)

    # Check audio file
    if not audio_file.exists():
        raise FileNotFoundError(
            f"Audio file not found: {audio_file}"
        )

    # Load Whisper only when needed
    model = get_model()

    # Make sure output directory exists
    subtitle_file.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    print("Transcribing audio...")

    # Transcribe audio
    segments, info = model.transcribe(
        str(audio_file),
        beam_size=5
    )

    segments = list(segments)

    # Create SRT file
    with open(
        subtitle_file,
        "w",
        encoding="utf-8"
    ) as file:

        for index, segment in enumerate(
            segments,
            start=1
        ):

            start = format_time(segment.start)
            end = format_time(segment.end)

            text = segment.text.strip()

            if not text:
                continue

            file.write(f"{index}\n")
            file.write(f"{start} --> {end}\n")
            file.write(f"{text}\n\n")

    print("SUBTITLE GENERATION SUCCESS")
    print(f"Audio: {audio_file}")
    print(f"Subtitles: {subtitle_file}")
    print(f"Segments: {len(segments)}")

    return str(subtitle_file)