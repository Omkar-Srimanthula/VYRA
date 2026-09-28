from pathlib import Path
import subprocess
import shutil


# ==========================================================
# PROJECT PATHS
# ==========================================================

BASE_DIR = Path(__file__).resolve().parent.parent
STORAGE_DIR = BASE_DIR / "storage"


# ==========================================================
# FIND FFMPEG
# ==========================================================

def get_ffmpeg():

    ffmpeg = shutil.which("ffmpeg")

    if ffmpeg:
        return ffmpeg

    base_path = (
        Path.home()
        / "AppData"
        / "Local"
        / "Microsoft"
        / "WinGet"
        / "Packages"
    )

    if base_path.exists():

        matches = list(
            base_path.rglob("ffmpeg.exe")
        )

        shared_matches = [
            path
            for path in matches
            if "Shared" in str(path)
        ]

        if shared_matches:
            return str(shared_matches[0])

        if matches:
            return str(matches[0])

    raise FileNotFoundError(
        "FFmpeg was not found."
    )


# ==========================================================
# FIND FFPROBE
# ==========================================================

def get_ffprobe():

    ffprobe = shutil.which("ffprobe")

    if ffprobe:
        return ffprobe

    base_path = (
        Path.home()
        / "AppData"
        / "Local"
        / "Microsoft"
        / "WinGet"
        / "Packages"
    )

    if base_path.exists():

        matches = list(
            base_path.rglob("ffprobe.exe")
        )

        if matches:
            return str(matches[0])

    raise FileNotFoundError(
        "FFprobe was not found."
    )


# ==========================================================
# GET MEDIA DURATION
# ==========================================================

def get_media_duration(file_path):

    file_path = Path(
        file_path
    ).resolve()

    ffprobe = get_ffprobe()

    command = [

        ffprobe,

        "-v",
        "error",

        "-show_entries",
        "format=duration",

        "-of",
        "default=noprint_wrappers=1:nokey=1",

        str(file_path),
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )

    if result.returncode != 0:

        raise RuntimeError(
            "Could not determine media duration.\n"
            + result.stderr
        )

    try:

        duration = float(
            result.stdout.strip()
        )

    except ValueError:

        raise RuntimeError(
            "Invalid media duration returned "
            f"by FFprobe: {result.stdout}"
        )

    if duration <= 0:

        raise RuntimeError(
            f"Invalid media duration: {duration}"
        )

    return duration


# ==========================================================
# ESCAPE SUBTITLE PATH FOR FFMPEG
# ==========================================================

def escape_subtitle_path(
    subtitle_file
):

    path = str(
        Path(subtitle_file)
        .resolve()
    )

    # FFmpeg subtitles filter on Windows
    # requires escaping the drive colon.

    path = path.replace(
        "\\",
        "/"
    )

    path = path.replace(
        ":",
        "\\:"
    )

    path = path.replace(
        "'",
        "\\'"
    )

    return path


# ==========================================================
# CREATE SUBTITLE FILTER
# ==========================================================

def build_subtitle_filter(
    subtitle_file,
    language="english"
):

    subtitle_path = escape_subtitle_path(
        subtitle_file
    )

    lang = str(language or "").lower()
    font_name = "Nirmala UI" if lang in ("te", "telugu", "hi", "hindi", "ta", "kn", "ml", "mr", "bn", "gu", "pa") else "Segoe UI"

    return (
        f"subtitles='{subtitle_path}':"
        "force_style="
        "'"
        f"FontName={font_name},"
        "FontSize=22,"
        "Bold=1,"
        "PrimaryColour=&H0000FFFF,"
        "SecondaryColour=&H00FFFFFF,"
        "OutlineColour=&H00000000,"
        "BackColour=&H80000000,"
        "BorderStyle=3,"
        "Outline=2,"
        "Shadow=1,"
        "Alignment=2,"
        "MarginL=70,"
        "MarginR=70,"
        "MarginV=180"
        "'"
    )


# ==========================================================
# CREATE FINAL VIDEO
# ==========================================================

def create_final_video(
    scenes_video: str,
    audio_path: str,
    subtitle_path: str,
    output_path: str,
    language: str = "english"
):

    """
    Create the final VYRA vertical video.

    Pipeline:

        AI SCENES
            +
        NARRATION
            +
        SUBTITLES
            =
        FINAL VIDEO

    The visual video is automatically looped
    when it is shorter than the narration.
    """

    scenes_file = Path(
        scenes_video
    ).resolve()

    audio_file = Path(
        audio_path
    ).resolve()

    subtitle_file = Path(
        subtitle_path
    ).resolve()

    output_file = Path(
        output_path
    ).resolve()

    # ======================================================
    # CHECK INPUTS
    # ======================================================

    print()
    print("=" * 60)
    print("VYRA FINAL VIDEO PIPELINE")
    print("=" * 60)

    print()
    print("Checking input files...")

    if not scenes_file.exists():

        raise FileNotFoundError(
            f"Scenes video not found:\n"
            f"{scenes_file}"
        )

    if not audio_file.exists():

        raise FileNotFoundError(
            f"Audio file not found:\n"
            f"{audio_file}"
        )

    if not subtitle_file.exists():

        raise FileNotFoundError(
            f"Subtitle file not found:\n"
            f"{subtitle_file}"
        )

    if scenes_file.stat().st_size == 0:

        raise ValueError(
            "Scenes video is empty."
        )

    if audio_file.stat().st_size == 0:

        raise ValueError(
            "Narration audio is empty."
        )

    if subtitle_file.stat().st_size == 0:

        raise ValueError(
            "Subtitle file is empty."
        )

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    # ======================================================
    # FFMPEG
    # ======================================================

    ffmpeg = get_ffmpeg()

    print()
    print("FFmpeg:")
    print(ffmpeg)

    # ======================================================
    # DURATIONS
    # ======================================================

    print()
    print("=" * 60)
    print("ANALYZING MEDIA")
    print("=" * 60)

    scene_duration = get_media_duration(
        scenes_file
    )

    narration_duration = get_media_duration(
        audio_file
    )

    print(
        f"Visual duration: "
        f"{scene_duration:.2f} seconds"
    )

    print(
        f"Narration duration: "
        f"{narration_duration:.2f} seconds"
    )

    # ======================================================
    # LOOP INFORMATION
    # ======================================================

    if scene_duration < narration_duration:

        print()
        print(
            "Visual video is shorter than narration."
        )

        print(
            "FFmpeg will loop the visual automatically."
        )

    else:

        print()
        print(
            "Visual video is long enough."
        )

    # ======================================================
    # SUBTITLE FILTER
    # ======================================================

    subtitle_filter = build_subtitle_filter(
        subtitle_file,
        language=language
    )

    # ======================================================
    # VIDEO FILTER
    # ======================================================

    video_filter = (
        "scale=1080:1920:"
        "force_original_aspect_ratio=decrease,"
        "pad=1080:1920:"
        "(ow-iw)/2:"
        "(oh-ih)/2,"
        "setsar=1,"
        f"{subtitle_filter}"
    )

    # ======================================================
    # FFMPEG COMMAND
    # ======================================================

    command = [

        ffmpeg,

        "-y",

        "-hide_banner",

        "-loglevel",
        "error",

        # --------------------------------------------------
        # VISUAL INPUT
        # --------------------------------------------------

        "-stream_loop",
        "-1",

        "-i",
        str(scenes_file),

        # --------------------------------------------------
        # AUDIO INPUT
        # --------------------------------------------------

        "-i",
        str(audio_file),

        # --------------------------------------------------
        # VIDEO FILTER
        # --------------------------------------------------

        "-vf",
        video_filter,

        # --------------------------------------------------
        # VIDEO MAP
        # --------------------------------------------------

        "-map",
        "0:v:0",

        # --------------------------------------------------
        # AUDIO MAP
        # --------------------------------------------------

        "-map",
        "1:a:0",

        # --------------------------------------------------
        # VIDEO CODEC
        # --------------------------------------------------

        "-c:v",
        "libx264",

        "-preset",
        "medium",

        "-crf",
        "21",

        "-pix_fmt",
        "yuv420p",

        # --------------------------------------------------
        # AUDIO CODEC
        # --------------------------------------------------

        "-c:a",
        "aac",

        "-b:a",
        "192k",

        # --------------------------------------------------
        # FINAL LENGTH
        # --------------------------------------------------

        "-t",
        str(narration_duration),

        # --------------------------------------------------
        # FAST START
        # --------------------------------------------------

        "-movflags",
        "+faststart",

        # --------------------------------------------------
        # OUTPUT
        # --------------------------------------------------

        str(output_file),
    ]

    # ======================================================
    # PRINT COMMAND INFORMATION
    # ======================================================

    print()
    print("=" * 60)
    print("CREATING FINAL VYRA VIDEO")
    print("=" * 60)

    print()
    print("Scenes:")
    print(scenes_file)

    print()
    print("Narration:")
    print(audio_file)

    print()
    print("Subtitles:")
    print(subtitle_file)

    print()
    print("Output:")
    print(output_file)

    print()
    print("Final duration:")
    print(
        f"{narration_duration:.2f} seconds"
    )

    print()
    print("Rendering final video...")
    print()

    # ======================================================
    # RUN FFMPEG
    # ======================================================

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )

    # ======================================================
    # ERROR
    # ======================================================

    if result.returncode != 0:

        print()
        print("=" * 60)
        print("FFMPEG FINAL VIDEO ERROR")
        print("=" * 60)

        print(
            result.stderr
        )

        raise RuntimeError(
            "Final VYRA video generation failed."
        )

    # ======================================================
    # VERIFY OUTPUT
    # ======================================================

    if not output_file.exists():

        raise RuntimeError(
            "FFmpeg completed but final video "
            "was not created."
        )

    file_size = (
        output_file.stat().st_size
    )

    if file_size == 0:

        raise RuntimeError(
            "Final video was created but "
            "the file is empty."
        )

    # ======================================================
    # VERIFY DURATION
    # ======================================================

    final_duration = get_media_duration(
        output_file
    )

    # ======================================================
    # SUCCESS
    # ======================================================

    print()
    print("=" * 60)
    print("FINAL VYRA VIDEO SUCCESS")
    print("=" * 60)

    print()
    print(
        "Final video:"
    )

    print(
        output_file
    )

    print()
    print(
        f"Final duration: "
        f"{final_duration:.2f} seconds"
    )

    print(
        f"Expected duration: "
        f"{narration_duration:.2f} seconds"
    )

    print()
    print(
        f"File size: "
        f"{file_size / (1024 * 1024):.2f} MB"
    )

    print()
    print("=" * 60)

    return str(
        output_file
    )


# ==========================================================
# CONVENIENCE FUNCTION
# ==========================================================

def create_vyra_final_video():

    scenes = (
        STORAGE_DIR
        / "combined_scenes.mp4"
    )

    narration = (
        STORAGE_DIR
        / "audio"
        / "narration.wav"
    )

    subtitles = (
        STORAGE_DIR
        / "subtitles.srt"
    )

    output = (
        STORAGE_DIR
        / "final_vyra_video.mp4"
    )

    return create_final_video(
        scenes_video=scenes,
        audio_path=narration,
        subtitle_path=subtitles,
        output_path=output
    )