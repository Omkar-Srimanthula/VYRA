from pathlib import Path
import subprocess
import shutil


BASE_DIR = Path(__file__).resolve().parent.parent


def get_ffmpeg():
    """
    Find FFmpeg installed on Windows.
    """

    ffmpeg = shutil.which("ffmpeg")

    if ffmpeg:
        return ffmpeg

    possible_paths = [
        Path(
            r"C:\Users\omkar\AppData\Local\Microsoft\WinGet\Packages"
        )
    ]

    for base_path in possible_paths:

        if base_path.exists():

            matches = list(
                base_path.rglob("ffmpeg.exe")
            )

            if matches:
                return str(matches[0])

    raise FileNotFoundError(
        "FFmpeg was not found. Please make sure FFmpeg is installed."
    )


def create_animated_captions(
    input_video: str,
    subtitle_file: str,
    output_video: str
):

    input_path = Path(input_video)
    subtitle_path = Path(subtitle_file)
    output_path = Path(output_video)

    if not input_path.exists():
        raise FileNotFoundError(
            f"Input video not found: {input_path}"
        )

    if not subtitle_path.exists():
        raise FileNotFoundError(
            f"Subtitle file not found: {subtitle_path}"
        )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    ffmpeg = get_ffmpeg()

    print()
    print("========================================")
    print("CREATING ANIMATED CAPTIONS")
    print("========================================")

    print(f"Input video: {input_path}")
    print(f"Subtitles: {subtitle_path}")
    print(f"Output: {output_path}")

    # Convert Windows path to FFmpeg-friendly path
    subtitle_for_ffmpeg = str(
        subtitle_path.resolve()
    ).replace("\\", "/")

    # Escape colon for FFmpeg filter syntax
    subtitle_for_ffmpeg = subtitle_for_ffmpeg.replace(
        ":",
        "\\:"
    )

    filter_text = (
        f"subtitles='{subtitle_for_ffmpeg}'"
        ":force_style="
        "'"
        "FontName=Nirmala UI,"
        "FontSize=20,"
        "Bold=1,"
        "PrimaryColour=&H00FFFFFF,"
        "OutlineColour=&H00000000,"
        "BorderStyle=1,"
        "Outline=3,"
        "Shadow=1,"
        "Alignment=2,"
        "MarginV=180"
        "'"
    )

    command = [
        ffmpeg,

        "-y",

        "-i",
        str(input_path),

        "-vf",
        filter_text,

        "-c:v",
        "libx264",

        "-preset",
        "medium",

        "-crf",
        "23",

        "-c:a",
        "copy",

        str(output_path)
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:

        print()
        print("FFmpeg ERROR:")
        print(result.stderr)

        raise RuntimeError(
            "Animated caption generation failed."
        )

    print()
    print("========================================")
    print("ANIMATED CAPTIONS SUCCESS")
    print("========================================")

    print(f"Video: {output_path}")

    return str(output_path)