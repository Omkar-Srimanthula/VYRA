from pathlib import Path
import subprocess
import shutil


BASE_DIR = Path(__file__).resolve().parent.parent


def get_ffmpeg():
    """
    Find FFmpeg on Windows.
    """

    ffmpeg = shutil.which("ffmpeg")

    if ffmpeg:
        return ffmpeg

    possible_paths = [
        Path.home()
        / "AppData"
        / "Local"
        / "Microsoft"
        / "WinGet"
        / "Packages"
    ]

    for base_path in possible_paths:

        if base_path.exists():

            matches = list(base_path.rglob("ffmpeg.exe"))

            if matches:
                return str(matches[0])

    raise FileNotFoundError(
        "FFmpeg was not found."
    )


def create_final_video(
    scenes_video: str,
    audio_path: str,
    subtitle_path: str,
    output_path: str
):
    """
    Create the final VYRA video.

    Combines:
    - Generated scenes
    - AI narration
    - Animated subtitles
    """

    scenes_file = Path(scenes_video)
    audio_file = Path(audio_path)
    subtitle_file = Path(subtitle_path)
    output_file = Path(output_path)

    # --------------------------------------------------
    # CHECK INPUT FILES
    # --------------------------------------------------

    if not scenes_file.exists():
        raise FileNotFoundError(
            f"Scenes video not found: {scenes_file}"
        )

    if not audio_file.exists():
        raise FileNotFoundError(
            f"Audio file not found: {audio_file}"
        )

    if not subtitle_file.exists():
        raise FileNotFoundError(
            f"Subtitle file not found: {subtitle_file}"
        )

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    ffmpeg = get_ffmpeg()

    print()
    print("========================================")
    print("CREATING FINAL VYRA VIDEO")
    print("========================================")

    print(f"Scenes: {scenes_file}")
    print(f"Audio: {audio_file}")
    print(f"Subtitles: {subtitle_file}")
    print(f"Output: {output_file}")

    # --------------------------------------------------
    # FFmpeg SUBTITLE PATH
    # --------------------------------------------------

    subtitle_ffmpeg = (
        subtitle_file.resolve()
        .as_posix()
    )

    subtitle_ffmpeg = subtitle_ffmpeg.replace(
        ":",
        "\\:"
    )

    # --------------------------------------------------
    # VIDEO FILTER
    # --------------------------------------------------

    video_filter = (
        f"subtitles='{subtitle_ffmpeg}':"
        "force_style="
        "'"
        "FontName=Arial,"
        "FontSize=22,"
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

    # --------------------------------------------------
    # FFmpeg COMMAND
    # --------------------------------------------------

    command = [
        ffmpeg,

        "-y",

        "-i",
        str(scenes_file),

        "-i",
        str(audio_file),

        "-vf",
        video_filter,

        "-map",
        "0:v:0",

        "-map",
        "1:a:0",

        "-c:v",
        "libx264",

        "-preset",
        "medium",

        "-crf",
        "23",

        "-c:a",
        "aac",

        "-b:a",
        "192k",

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
        print("========================================")
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
    print("FINAL VIDEO SUCCESS")
    print("========================================")

    print(f"Final video: {output_file}")

    return str(output_file)