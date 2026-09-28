from pathlib import Path
import subprocess


# --------------------------------------------------
# PROJECT PATHS
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
STORAGE_DIR = BASE_DIR / "storage"


# --------------------------------------------------
# FIND FFMPEG
# --------------------------------------------------

FFMPEG_PATH = (
    Path.home()
    / "AppData"
    / "Local"
    / "Microsoft"
    / "WinGet"
    / "Packages"
    / "Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe"
    / "ffmpeg-9.0-full_build"
    / "bin"
    / "ffmpeg.exe"
)


# --------------------------------------------------
# GENERATE FINAL VIDEO
# --------------------------------------------------

def generate_video(
    audio_path: str,
    subtitle_path: str,
    output_path: str,
    visual_path: str
):

    audio_file = Path(audio_path)
    subtitle_file = Path(subtitle_path)
    visual_file = Path(visual_path)
    output_file = Path(output_path)

    # --------------------------------------------------
    # CHECK FILES
    # --------------------------------------------------

    if not audio_file.exists():
        raise FileNotFoundError(
            f"Audio file not found: {audio_file}"
        )

    if not subtitle_file.exists():
        raise FileNotFoundError(
            f"Subtitle file not found: {subtitle_file}"
        )

    if not visual_file.exists():
        raise FileNotFoundError(
            f"Visual file not found: {visual_file}"
        )

    if not FFMPEG_PATH.exists():
        raise FileNotFoundError(
            f"FFmpeg not found: {FFMPEG_PATH}"
        )

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    # --------------------------------------------------
    # PREPARE SUBTITLE PATH
    # --------------------------------------------------

    subtitle_path_ffmpeg = (
        subtitle_file.resolve()
        .as_posix()
        .replace(":", "\\:")
    )

    # --------------------------------------------------
    # BUILD FFMPEG COMMAND
    # --------------------------------------------------

    print()
    print("========================================")
    print("CREATING FINAL VIDEO")
    print("========================================")

    print(f"Visual: {visual_file}")
    print(f"Audio: {audio_file}")
    print(f"Subtitles: {subtitle_file}")
    print(f"Output: {output_file}")

    command = [
        str(FFMPEG_PATH),

        "-y",

        # Visual input
        "-i",
        str(visual_file),

        # Audio input
        "-i",
        str(audio_file),

        # Subtitle filter
        "-vf",
        (
            f"subtitles='{subtitle_path_ffmpeg}':"
            "force_style="
            "'FontName=Arial,"
            "FontSize=18,"
            "Bold=1,"
            "PrimaryColour=&HFFFFFF&,"
            "OutlineColour=&H000000&,"
            "BorderStyle=1,"
            "Outline=3,"
            "Shadow=1,"
            "Alignment=2,"
            "MarginV=150'"
        ),

        # Video
        "-c:v",
        "libx264",

        "-preset",
        "medium",

        "-crf",
        "23",

        # Audio
        "-c:a",
        "aac",

        # Match narration duration
        "-shortest",

        str(output_file)
    ]

    # --------------------------------------------------
    # RUN FFMPEG
    # --------------------------------------------------

    result = subprocess.run(
        command,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:

        print()
        print("FFMPEG ERROR")
        print("========================================")
        print(result.stderr)

        raise RuntimeError(
            "Final video generation failed."
        )

    # --------------------------------------------------
    # SUCCESS
    # --------------------------------------------------

    print()
    print("========================================")
    print("FINAL VIDEO GENERATION SUCCESS")
    print("========================================")

    print(f"Video: {output_file}")

    return str(output_file)