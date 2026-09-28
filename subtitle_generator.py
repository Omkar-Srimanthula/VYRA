from pathlib import Path
from faster_whisper import WhisperModel
import torch


# ==========================================================
# VYRA - GPU SUBTITLE GENERATOR
# ==========================================================

BASE_DIR = Path(__file__).resolve().parent

AUDIO_FILE = BASE_DIR / "storage" / "audio" / "narration.wav"
OUTPUT_FILE = BASE_DIR / "storage" / "subtitles.srt"


# ==========================================================
# GPU / DEVICE CONFIGURATION
# ==========================================================

if torch.cuda.is_available():
    DEVICE = "cuda"
    COMPUTE_TYPE = "float16"

    print("========================================")
    print("VYRA WHISPER GPU MODE")
    print("========================================")
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"CUDA: {torch.version.cuda}")
    print(f"Compute Type: {COMPUTE_TYPE}")
    print("========================================")

else:
    DEVICE = "cpu"
    COMPUTE_TYPE = "int8"

    print("========================================")
    print("VYRA WHISPER CPU FALLBACK")
    print("========================================")
    print("CUDA is not available.")
    print("Using CPU transcription.")
    print("========================================")


# ==========================================================
# CHECK AUDIO FILE
# ==========================================================

if not AUDIO_FILE.exists():

    print()
    print("ERROR: Audio file not found.")
    print(f"Expected: {AUDIO_FILE}")
    print()

    raise FileNotFoundError(
        f"Audio file not found: {AUDIO_FILE}"
    )


# ==========================================================
# LOAD WHISPER
# ==========================================================

print()
print("Loading Whisper model...")
print("Model: tiny")
print(f"Device: {DEVICE}")
print(f"Compute type: {COMPUTE_TYPE}")
print()

model = WhisperModel(
    "tiny",
    device=DEVICE,
    compute_type=COMPUTE_TYPE
)


print("Whisper model loaded successfully.")


# ==========================================================
# TRANSCRIBE
# ==========================================================

print()
print("Transcribing audio...")
print(f"Audio: {AUDIO_FILE}")
print()

segments, info = model.transcribe(
    str(AUDIO_FILE),
    beam_size=5,
    vad_filter=True
)

segments = list(segments)


# ==========================================================
# TIME FORMATTER
# ==========================================================

def format_time(seconds):
    """
    Convert seconds into SRT timestamp format.

    Example:
    12.345 seconds
    ->
    00:00:12,345
    """

    milliseconds = int(seconds * 1000)

    hours = milliseconds // 3_600_000
    milliseconds %= 3_600_000

    minutes = milliseconds // 60_000
    milliseconds %= 60_000

    secs = milliseconds // 1000
    milliseconds %= 1000

    return (
        f"{hours:02d}:"
        f"{minutes:02d}:"
        f"{secs:02d},"
        f"{milliseconds:03d}"
    )


# ==========================================================
# CREATE OUTPUT DIRECTORY
# ==========================================================

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True
)


# ==========================================================
# WRITE SRT
# ==========================================================

with open(
    OUTPUT_FILE,
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

        file.write(
            f"{index}\n"
        )

        file.write(
            f"{start} --> {end}\n"
        )

        file.write(
            f"{text}\n\n"
        )


# ==========================================================
# SUCCESS
# ==========================================================

print()
print("========================================")
print("SUBTITLE GENERATION SUCCESS")
print("========================================")
print(f"Audio     : {AUDIO_FILE}")
print(f"Subtitles : {OUTPUT_FILE}")
print(f"Segments  : {len(segments)}")
print(f"Device    : {DEVICE}")
print(f"Compute   : {COMPUTE_TYPE}")
print("========================================")