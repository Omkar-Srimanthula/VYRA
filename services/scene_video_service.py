from pathlib import Path
import subprocess
import shutil
import math

from .visual_service import generate_all_scene_videos


# ==========================================================
# PROJECT PATHS
# ==========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

STORAGE_DIR = BASE_DIR / "storage"
SCENES_DIR = STORAGE_DIR / "scenes"


STORAGE_DIR.mkdir(
    parents=True,
    exist_ok=True
)

SCENES_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ==========================================================
# FIND FFMPEG
# ==========================================================

def get_ffmpeg():
    """
    Find FFmpeg from PATH or WinGet installation.
    """

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
            return str(
                shared_matches[0]
            )

        if matches:
            return str(
                matches[0]
            )

    raise FileNotFoundError(
        "FFmpeg was not found. "
        "Please make sure FFmpeg is installed."
    )


# ==========================================================
# GET MEDIA DURATION
# ==========================================================

def get_media_duration(file_path):
    """
    Get media duration using FFprobe.
    """

    ffmpeg = get_ffmpeg()

    ffprobe = Path(ffmpeg).with_name(
        "ffprobe.exe"
    )

    if not ffprobe.exists():

        ffprobe_path = shutil.which(
            "ffprobe"
        )

        if ffprobe_path:
            ffprobe = Path(
                ffprobe_path
            )

    if not ffprobe.exists():

        raise FileNotFoundError(
            "FFprobe was not found."
        )

    command = [

        str(ffprobe),

        "-v",
        "error",

        "-show_entries",
        "format=duration",

        "-of",
        "default=noprint_wrappers=1:nokey=1",

        str(file_path)
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
            f"Invalid duration returned by FFprobe: "
            f"{result.stdout}"
        )

    if duration <= 0:

        raise RuntimeError(
            f"Invalid media duration: {duration}"
        )

    return duration


# ==========================================================
# CALCULATE AUTOMATIC SCENE DURATIONS
# ==========================================================

def calculate_scene_durations(
    scenes,
    total_duration,
    minimum_duration=4.0,
    maximum_duration=8.0
):
    """
    Automatically distribute the narration duration
    across the supplied scenes.

    Example:

        total duration = 78 seconds
        scenes = 10

    The function creates approximately 7-8 second
    scenes instead of using a fixed 5 second duration.
    """

    if not scenes:

        raise ValueError(
            "No scenes were provided."
        )

    try:

        total_duration = float(
            total_duration
        )

    except (
        TypeError,
        ValueError
    ):

        raise ValueError(
            "Invalid total duration."
        )

    if total_duration <= 0:

        raise ValueError(
            "Total duration must be greater than zero."
        )

    scene_count = len(
        scenes
    )

    # ------------------------------------------------------
    # IDEAL DURATION
    # ------------------------------------------------------

    ideal_duration = (
        total_duration
        / scene_count
    )

    # ------------------------------------------------------
    # CLAMP TO CINEMATIC RANGE
    # ------------------------------------------------------

    target_duration = max(
        minimum_duration,
        min(
            maximum_duration,
            ideal_duration
        )
    )

    # ------------------------------------------------------
    # INITIAL DURATIONS
    # ------------------------------------------------------

    durations = [
        target_duration
        for _ in range(scene_count)
    ]

    # ------------------------------------------------------
    # SCALE TO EXACT TOTAL
    # ------------------------------------------------------

    current_total = sum(
        durations
    )

    scale = (
        total_duration
        / current_total
    )

    durations = [
        duration * scale
        for duration in durations
    ]

    # ------------------------------------------------------
    # ROUND
    # ------------------------------------------------------

    durations = [
        round(
            duration,
            3
        )
        for duration in durations
    ]

    # ------------------------------------------------------
    # CORRECT ROUNDING ERROR
    # ------------------------------------------------------

    difference = round(
        total_duration
        - sum(durations),
        3
    )

    if durations:

        durations[-1] = round(
            durations[-1]
            + difference,
            3
        )

    return durations


# ==========================================================
# PREPARE SCENES WITH AUTOMATIC TIMING
# ==========================================================

def prepare_scenes_for_duration(
    scenes,
    total_duration
):
    """
    Add automatically calculated durations to scene data.

    Existing durations are replaced intentionally so that
    the entire visual sequence matches the narration.
    """

    if not scenes:

        raise ValueError(
            "No scenes were provided."
        )

    durations = calculate_scene_durations(
        scenes,
        total_duration
    )

    prepared_scenes = []

    for index, scene in enumerate(
        scenes
    ):

        duration = durations[index]

        if isinstance(
            scene,
            dict
        ):

            new_scene = dict(
                scene
            )

            new_scene["duration"] = (
                duration
            )

        else:

            new_scene = {
                "duration": duration,
                "visual_description": str(
                    scene
                )
            }

        prepared_scenes.append(
            new_scene
        )

    return prepared_scenes


# ==========================================================
# GENERATE AI VIDEO SCENES
# ==========================================================

def generate_scene_videos(
    scenes,
    output_directory=None
):
    """
    Generate AI-powered MP4 videos for all scenes.
    """

    if not scenes:

        raise ValueError(
            "No scenes were provided."
        )

    if output_directory is None:

        output_directory = SCENES_DIR

    output_directory = Path(
        output_directory
    ).resolve()

    output_directory.mkdir(
        parents=True,
        exist_ok=True
    )

    print()
    print("=" * 60)
    print("VYRA AI SCENE VIDEO GENERATION")
    print("=" * 60)

    print(
        "Output directory:",
        output_directory
    )

    print(
        "Total scenes:",
        len(scenes)
    )

    # ------------------------------------------------------
    # GENERATE
    # ------------------------------------------------------

    scene_files = generate_all_scene_videos(
        scenes=scenes,
        output_directory=output_directory
    )

    # ------------------------------------------------------
    # VERIFY
    # ------------------------------------------------------

    if not scene_files:

        raise RuntimeError(
            "AI scene generation returned "
            "no video files."
        )

    for scene_file in scene_files:

        scene_path = Path(
            scene_file
        ).resolve()

        if not scene_path.exists():

            raise FileNotFoundError(
                f"Generated scene does not exist: "
                f"{scene_path}"
            )

        if scene_path.stat().st_size == 0:

            raise RuntimeError(
                f"Generated scene is empty: "
                f"{scene_path}"
            )

    print()
    print("=" * 60)
    print("AI SCENE VIDEOS GENERATED")
    print("=" * 60)

    for index, scene_file in enumerate(
        scene_files,
        start=1
    ):

        print(
            f"Scene {index}: {scene_file}"
        )

    return scene_files


# ==========================================================
# COMBINE VIDEO SCENES
# ==========================================================

def combine_scenes(
    scene_files,
    output_path
):
    """
    Combine multiple MP4 scene files into one MP4.
    """

    if not scene_files:

        raise ValueError(
            "No scene files were provided."
        )

    output_file = Path(
        output_path
    ).resolve()

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    ffmpeg = get_ffmpeg()

    print()
    print("=" * 60)
    print("COMBINING VIDEO SCENES")
    print("=" * 60)

    print(
        f"Number of scenes: "
        f"{len(scene_files)}"
    )

    print(
        f"Output: "
        f"{output_file}"
    )

    # ======================================================
    # VALIDATE SCENES
    # ======================================================

    valid_scene_files = []

    for index, scene in enumerate(
        scene_files,
        start=1
    ):

        scene_path = Path(
            scene
        ).resolve()

        print(
            f"Checking scene {index}: "
            f"{scene_path}"
        )

        if not scene_path.exists():

            raise FileNotFoundError(
                f"Scene file not found: "
                f"{scene_path}"
            )

        if scene_path.stat().st_size == 0:

            raise ValueError(
                f"Scene file is empty: "
                f"{scene_path}"
            )

        valid_scene_files.append(
            scene_path
        )

    # ======================================================
    # REMOVE OLD OUTPUT
    # ======================================================

    if output_file.exists():

        try:

            output_file.unlink()

        except PermissionError as error:

            raise RuntimeError(
                f"Cannot replace output video "
                f"because it is being used by "
                f"another program:\n"
                f"{output_file}"
            ) from error

    # ======================================================
    # CONCAT FILE
    # ======================================================

    concat_file = (
        output_file.parent
        / "scene_concat.txt"
    )

    with open(
        concat_file,
        "w",
        encoding="utf-8"
    ) as file:

        for scene_path in valid_scene_files:

            safe_path = str(
                scene_path
            ).replace(
                "\\",
                "/"
            )

            safe_path = safe_path.replace(
                "'",
                "'\\''"
            )

            file.write(
                f"file '{safe_path}'\n"
            )

    print(
        "Concat file:",
        concat_file
    )

    # ======================================================
    # FFMPEG
    # ======================================================

    command = [

        ffmpeg,

        "-y",

        "-hide_banner",

        "-loglevel",
        "error",

        "-f",
        "concat",

        "-safe",
        "0",

        "-i",
        str(concat_file),

        "-c",
        "copy",

        "-movflags",
        "+faststart",

        str(output_file)
    ]

    print()
    print(
        "Running FFmpeg scene combination..."
    )

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
        print("FFMPEG SCENE COMBINATION ERROR")
        print("=" * 60)

        if result.stderr:
            print(
                result.stderr
            )

        raise RuntimeError(
            "Scene combination failed."
        )

    # ======================================================
    # VERIFY
    # ======================================================

    if not output_file.exists():

        raise RuntimeError(
            "FFmpeg finished without "
            "creating the combined video."
        )

    if output_file.stat().st_size == 0:

        raise RuntimeError(
            "Combined video was created "
            "but the file is empty."
        )

    # ======================================================
    # SUCCESS
    # ======================================================

    print()
    print("=" * 60)
    print("SCENES COMBINED SUCCESSFULLY")
    print("=" * 60)

    print(
        "Output:",
        output_file
    )

    print(
        "Size:",
        f"{output_file.stat().st_size / (1024 * 1024):.2f} MB"
    )

    return str(
        output_file
    )


# ==========================================================
# COMPLETE SCENE PIPELINE
# ==========================================================

def create_scene_video(
    scenes,
    output_path=None
):
    """
    Complete scene pipeline.

        Scene data
             ↓
        Stable Diffusion
             ↓
        AI scene MP4 files
             ↓
        FFmpeg concatenation
             ↓
        Combined scene video
    """

    if not scenes:

        raise ValueError(
            "No scenes were provided."
        )

    if output_path is None:

        output_path = (
            STORAGE_DIR
            / "combined_scenes.mp4"
        )

    output_path = Path(
        output_path
    ).resolve()

    scene_files = generate_scene_videos(
        scenes=scenes,
        output_directory=SCENES_DIR
    )

    combined_video = combine_scenes(
        scene_files=scene_files,
        output_path=output_path
    )

    print()
    print("=" * 60)
    print("VYRA COMPLETE SCENE PIPELINE SUCCESS")
    print("=" * 60)

    print(
        "Combined video:",
        combined_video
    )

    return combined_video


# ==========================================================
# AUTOMATIC NARRATION-SYNCHRONIZED SCENE PIPELINE
# ==========================================================

def create_scenes_for_narration(
    scenes,
    narration_path,
    output_path=None
):
    """
    Create AI scenes whose total duration matches
    the narration duration.

    This is the new VYRA automatic timing engine.
    """

    if not scenes:

        raise ValueError(
            "No scenes were provided."
        )

    narration_file = Path(
        narration_path
    ).resolve()

    if not narration_file.exists():

        raise FileNotFoundError(
            f"Narration file not found: "
            f"{narration_file}"
        )

    if output_path is None:

        output_path = (
            STORAGE_DIR
            / "combined_scenes.mp4"
        )

    output_path = Path(
        output_path
    ).resolve()

    # ======================================================
    # NARRATION DURATION
    # ======================================================

    narration_duration = get_media_duration(
        narration_file
    )

    print()
    print("=" * 60)
    print("VYRA AUTOMATIC SCENE TIMING")
    print("=" * 60)

    print(
        f"Narration duration: "
        f"{narration_duration:.2f} seconds"
    )

    print(
        f"Input scenes: "
        f"{len(scenes)}"
    )

    # ======================================================
    # PREPARE SCENES
    # ======================================================

    prepared_scenes = prepare_scenes_for_duration(
        scenes,
        narration_duration
    )

    print()
    print("Calculated scene durations:")

    for index, scene in enumerate(
        prepared_scenes,
        start=1
    ):

        print(
            f"Scene {index}: "
            f"{scene['duration']:.3f} sec"
        )

    print(
        f"Total: "
        f"{sum(scene['duration'] for scene in prepared_scenes):.3f} sec"
    )

    # ======================================================
    # GENERATE
    # ======================================================

    scene_files = generate_scene_videos(
        scenes=prepared_scenes,
        output_directory=SCENES_DIR
    )

    # ======================================================
    # COMBINE
    # ======================================================

    combined_video = combine_scenes(
        scene_files=scene_files,
        output_path=output_path
    )

    # ======================================================
    # VERIFY DURATION
    # ======================================================

    final_visual_duration = get_media_duration(
        combined_video
    )

    print()
    print("=" * 60)
    print("AUTOMATIC SCENE PIPELINE COMPLETE")
    print("=" * 60)

    print(
        f"Visual duration: "
        f"{final_visual_duration:.2f} sec"
    )

    print(
        f"Narration duration: "
        f"{narration_duration:.2f} sec"
    )

    return combined_video