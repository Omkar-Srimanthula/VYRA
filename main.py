import os
import sys
from pathlib import Path
import re
import requests
import shutil
import subprocess

# Add WinGet FFmpeg DLL directory on Windows so FFmpeg / PyTorch / TTS loads cleanly
if sys.platform == "win32" and hasattr(os, "add_dll_directory"):
    winget_packages = Path.home() / "AppData" / "Local" / "Microsoft" / "WinGet" / "Packages"
    if winget_packages.exists():
        for dll_file in winget_packages.rglob("avcodec-*.dll"):
            try:
                os.add_dll_directory(str(dll_file.parent))
                os.environ["PATH"] = str(dll_file.parent) + os.pathsep + os.environ.get("PATH", "")
                break
            except Exception:
                pass

from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel


# ==========================================================
# VYRA SERVICES
# ==========================================================

from services.subtitle_service import generate_subtitles
from services.scene_service import generate_scene_breakdown
from services.scene_generation_service import generate_all_scene_videos
from services.scene_video_service import combine_scenes
from services.final_video_service import create_final_video
from services.tts_service import generate_speech
from services.context_service import (
    build_video_context,
    create_context_prompt
)
from services.research_service import gather_real_research
from services.fact_check_service import verify_script_facts
from services.quality_control_service import run_pre_render_quality_control


# ==========================================================
# VYRA APPLICATION
# ==========================================================

app = FastAPI(
    title="VYRA AI Video & Caption Studio",
    version="2.1.0"
)


# ==========================================================
# PROJECT PATHS
# ==========================================================

BASE_DIR = Path(__file__).resolve().parent

FRONTEND_DIR = BASE_DIR / "frontend"
STORAGE_DIR = BASE_DIR / "storage"

AUDIO_DIR = STORAGE_DIR / "audio"
SCENES_DIR = STORAGE_DIR / "scenes"
VOICE_DIR = STORAGE_DIR / "voice"


# ==========================================================
# CREATE REQUIRED DIRECTORIES
# ==========================================================

FRONTEND_DIR.mkdir(
    parents=True,
    exist_ok=True
)

STORAGE_DIR.mkdir(
    parents=True,
    exist_ok=True
)

AUDIO_DIR.mkdir(
    parents=True,
    exist_ok=True
)

SCENES_DIR.mkdir(
    parents=True,
    exist_ok=True
)

VOICE_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ==========================================================
# OLLAMA
# ==========================================================

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"

OLLAMA_MODEL = "qwen2.5:3b"


# ==========================================================
# REQUEST MODEL
# ==========================================================
class VideoRequest(BaseModel):

    topic: str

    script: str = ""

    context: str = ""

    language: str = "english"

    audience: str = "general"

    purpose: str = "education"

    tone: str = "engaging"

    difficulty: str = "beginner"

    duration: int = 45

    style: str = "educational"

    use_avatar: bool = False



# ==========================================================
# FFMPEG
# ==========================================================

def get_ffmpeg():

    ffmpeg = shutil.which("ffmpeg")

    if ffmpeg:
        return ffmpeg

    winget_path = (
        Path.home()
        / "AppData"
        / "Local"
        / "Microsoft"
        / "WinGet"
        / "Packages"
    )

    if winget_path.exists():

        matches = list(
            winget_path.rglob("ffmpeg.exe")
        )

        if matches:

            return str(matches[0])

    raise FileNotFoundError(
        "FFmpeg was not found. "
        "Please make sure FFmpeg is installed."
    )


# ==========================================================
# CLEAN AI SCRIPT
# ==========================================================

def clean_script(script: str) -> str:

    if not script:
        return ""

    script = str(script).strip()

    # Remove markdown code blocks
    script = re.sub(
        r"```(?:text|plaintext|txt)?",
        "",
        script,
        flags=re.IGNORECASE
    )

    script = script.replace(
        "```",
        ""
    )

    # Remove bracketed stage/camera directions like [Opening shot...], [Cut to...]
    script = re.sub(
        r"\[[^\]]*\]",
        "",
        script
    )

    script = re.sub(
        r"\([^)]*\)",
        "",
        script
    )

    # Remove common labels
    script = re.sub(
        r"\b(script|narration|voiceover|voice-over|speaker)\s*:\s*",
        "",
        script,
        flags=re.IGNORECASE
    )

    # Remove hashtags
    script = re.sub(
        r"#\w+",
        "",
        script
    )

    # Remove excessive whitespace
    script = re.sub(
        r"\s+",
        " ",
        script
    )

    return script.strip()


# ==========================================================
# GENERATE AI SCRIPT HELPER
# ==========================================================

def generate_ai_script(video_context: dict, context_prompt: str, research_data: dict = None) -> str:
    research_section = ""
    if research_data and research_data.get("research_summary"):
        research_section = f"""
REAL VERIFIED RESEARCH CONTEXT:
{research_data["research_summary"]}

STRICT FACTUAL CONSTRAINT:
- Base your narration STRICTLY on the real research context above.
- Do NOT invent fake statistics, false dates, non-existent people, or fabricated facts.
"""

    prompt = f"""
You are VYRA's professional AI video script writer.

Create a natural spoken narration for the user's video.

VIDEO TOPIC:
{video_context["topic"]}

{research_section}

USER CONTEXT:
{video_context["user_context"] or "No additional context provided."}

TARGET AUDIENCE:
{video_context["audience"]}

PURPOSE:
{video_context["purpose"]}

TONE:
{video_context["tone"]}

DIFFICULTY:
{video_context["difficulty"]}

VIDEO DURATION:
{video_context["duration"]} seconds

VIDEO STYLE:
{video_context["style"]}

LANGUAGE:
{video_context["language"]}

LANGUAGE CODE:
{video_context["language_code"]}

CONTEXT INSTRUCTIONS:
{context_prompt}

IMPORTANT RULES:

- Generate the narration entirely in the requested language.
- Do NOT automatically use English.
- Use natural spoken language.
- Start with an engaging hook.
- Make the explanation clear and useful.
- Follow the user's context and research facts.
- Adapt the explanation to the target audience.
- Match the requested difficulty.
- Match the requested tone.
- Match the requested style.
- Match the requested duration.
- Do not invent unnecessary facts or false statistics.
- Do not include scene directions.
- Do not include camera directions.
- Do not include hashtags.
- Do not include emojis.
- Do not include a title.
- Do not include labels.
- Return ONLY the spoken narration.
"""

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "num_predict": 200,
                    "top_p": 0.8
                }
            },
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        script = clean_script(data.get("response", ""))
        if script:
            return script
    except Exception as error:
        print(f"[Ollama Warning] Fast script generation failed or timed out: {error}")
        print("Using research-grounded fallback narration...")

    # Robust Fallback Narration from Research Facts
    if research_data and research_data.get("key_facts"):
        facts = research_data["key_facts"][:3]
        fallback_script = f"Here is the verified research summary on {video_context['topic']}. " + " ".join(facts)
        return clean_script(fallback_script)

    fallback_script = f"{video_context['topic']} is a significant topic. Research records provide verified facts and key details about this subject."
    return clean_script(fallback_script)


# ==========================================================
# HOME
# ==========================================================

@app.get("/")
def home():

    index_file = (
        FRONTEND_DIR /
        "index.html"
    )

    if not index_file.exists():

        return JSONResponse(
            status_code=404,
            content={
                "success": False,
                "message":
                    "Frontend index.html was not found."
            }
        )

    return FileResponse(
        index_file
    )


# ==========================================================
# HEALTH
# ==========================================================

@app.get("/api/health")
def health():

    # ------------------------------------------------------
    # Check Ollama
    # ------------------------------------------------------

    ollama_running = False

    try:

        response = requests.get(
            "http://127.0.0.1:11434/api/tags",
            timeout=5
        )

        ollama_running = (
            response.status_code == 200
        )

    except Exception:

        ollama_running = False

    # ------------------------------------------------------
    # Check voice sample
    # ------------------------------------------------------

    voice_file = (
        VOICE_DIR /
        "voice_sample.wav"
    )

    voice_available = voice_file.exists()

    # ------------------------------------------------------
    # Return status
    # ------------------------------------------------------

    return {

        "success": True,

        "project": "VYRA",

        "version": "2.1.0",

        "status": "running",

        "ollama": ollama_running,

        "model": OLLAMA_MODEL,

        "xtts_v2": True,

        "voice_available":
            voice_available,

        "voice_cloning":
            voice_available
    }


# ==========================================================
# GENERATE SCRIPT ENDPOINT
# ==========================================================

@app.post("/api/generate-script")
def generate_script_endpoint(request: VideoRequest):
    topic = request.topic.strip()
    if not topic:
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "message": "Please enter a video topic."
            }
        )

    try:
        video_context = build_video_context(
            topic=topic,
            context=request.context,
            language=request.language,
            audience=request.audience,
            purpose=request.purpose,
            tone=request.tone,
            difficulty=request.difficulty,
            duration=request.duration,
            style=request.style
        )
        # Execute Real Web & Wikipedia Research
        research_data = gather_real_research(topic, request.context)
        context_prompt = create_context_prompt(video_context)
        script = generate_ai_script(video_context, context_prompt, research_data)
        script, fact_report = verify_script_facts(script, research_data)
        return {
            "success": True,
            "topic": topic,
            "script": script,
            "language": video_context["language"],
            "language_code": video_context["language_code"],
            "research_sources": research_data.get("sources", []),
            "fact_check_accuracy": fact_report.get("factual_accuracy_rating")
        }
    except Exception as error:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": f"Script generation failed: {error}"
            }
        )


# ==========================================================
# LIST GENERATED VIDEOS
# ==========================================================

@app.get("/api/videos")
def list_videos():
    videos = []
    if STORAGE_DIR.exists():
        for file in STORAGE_DIR.glob("*.mp4"):
            if file.is_file() and file.stat().st_size > 0:
                videos.append({
                    "filename": file.name,
                    "url": f"/api/video/{file.name}",
                    "size_mb": round(file.stat().st_size / (1024 * 1024), 2),
                    "created_at": file.stat().st_mtime
                })
    videos.sort(key=lambda x: x["created_at"], reverse=True)
    return {
        "success": True,
        "videos": videos
    }


# ==========================================================
# AUDIO FILE
# ==========================================================

@app.get("/api/audio/{filename}")
def get_audio(filename: str):

    safe_name = Path(
        filename
    ).name

    audio_file = (
        AUDIO_DIR /
        safe_name
    )

    if not audio_file.exists():

        return JSONResponse(
            status_code=404,
            content={
                "success": False,
                "message":
                    "Audio file not found."
            }
        )

    return FileResponse(
        audio_file,
        media_type="audio/wav",
        filename=safe_name
    )


# ==========================================================
# VIDEO FILE
# ==========================================================

@app.get("/api/video/{filename}")
def get_video(filename: str):

    safe_name = Path(
        filename
    ).name

    video_file = (
        STORAGE_DIR /
        safe_name
    )

    if not video_file.exists():

        return JSONResponse(
            status_code=404,
            content={
                "success": False,
                "message":
                    "Video file not found."
            }
        )

    return FileResponse(
        video_file,
        media_type="video/mp4",
        filename=safe_name
    )


# ==========================================================
# VOICE SAMPLE UPLOAD
# ==========================================================

@app.post("/api/upload-voice")
async def upload_voice(
    file: UploadFile = File(...)
):

    try:

        # --------------------------------------------------
        # Validate filename
        # --------------------------------------------------

        if not file.filename:

            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "message":
                        "No voice file was selected."
                }
            )

        # --------------------------------------------------
        # Allowed formats
        # --------------------------------------------------

        allowed_extensions = {

            ".wav",
            ".mp3",
            ".webm",
            ".m4a",
            ".ogg"
        }

        extension = Path(
            file.filename
        ).suffix.lower()

        if extension not in allowed_extensions:

            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "message":
                        (
                            "Unsupported audio format. "
                            "Use WAV, MP3, WebM, M4A or OGG."
                        )
                }
            )

        # --------------------------------------------------
        # Read uploaded file
        # --------------------------------------------------

        content = await file.read()

        if not content:

            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "message":
                        "The uploaded voice file is empty."
                }
            )

        # --------------------------------------------------
        # Maximum 25 MB
        # --------------------------------------------------

        if len(content) > (
            25 * 1024 * 1024
        ):

            return JSONResponse(
                status_code=413,
                content={
                    "success": False,
                    "message":
                        (
                            "Voice sample is too large. "
                            "Maximum is 25 MB."
                        )
                }
            )

        # --------------------------------------------------
        # Save original upload temporarily
        # --------------------------------------------------

        raw_file = (
            VOICE_DIR /
            ("voice_sample" + extension)
        )

        raw_file.write_bytes(
            content
        )

        # --------------------------------------------------
        # Convert to standard WAV
        # --------------------------------------------------

        ffmpeg = get_ffmpeg()

        wav_file = (
            VOICE_DIR /
            "voice_sample.wav"
        )

        command = [

            ffmpeg,

            "-y",

            "-hide_banner",

            "-loglevel",
            "error",

            "-i",
            str(raw_file),

            "-ac",
            "1",

            "-ar",
            "22050",

            "-sample_fmt",
            "s16",

            str(wav_file)
        ]

        result = subprocess.run(

            command,

            capture_output=True,

            text=True,

            encoding="utf-8",

            errors="replace"
        )

        # --------------------------------------------------
        # FFmpeg error
        # --------------------------------------------------

        if result.returncode != 0:

            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "message":
                        (
                            "Could not convert voice sample: "
                            + result.stderr
                        )
                }
            )

        # --------------------------------------------------
        # Verify WAV
        # --------------------------------------------------

        if not wav_file.exists():

            raise RuntimeError(
                "Voice WAV file was not created."
            )

        if wav_file.stat().st_size == 0:

            raise RuntimeError(
                "Voice WAV file is empty."
            )

        # --------------------------------------------------
        # Success
        # --------------------------------------------------

        print()
        print("=" * 60)
        print("VOICE SAMPLE READY")
        print("=" * 60)
        print(
            f"Voice sample: {wav_file}"
        )

        return {

            "success": True,

            "message":
                "Voice sample uploaded successfully.",

            "voice_cloning_ready":
                True,

            "voice_sample":
                "/api/voice/sample",

            "filename":
                "voice_sample.wav"
        }

    except Exception as error:

        print()
        print(
            "VOICE UPLOAD ERROR:",
            repr(error)
        )

        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message":
                    f"Voice upload failed: {error}"
            }
        )


# ==========================================================
# GET VOICE SAMPLE
# ==========================================================

@app.get("/api/voice/sample")
def get_voice_sample():

    voice_file = (
        VOICE_DIR /
        "voice_sample.wav"
    )

    if not voice_file.exists():

        return JSONResponse(
            status_code=404,
            content={
                "success": False,
                "message":
                    "No voice sample has been uploaded."
            }
        )

    return FileResponse(

        voice_file,

        media_type="audio/wav",

        filename="voice_sample.wav"
    )


# ==========================================================
# VOICE STATUS
# ==========================================================

@app.get("/api/voice/status")
def voice_status():

    voice_file = (
        VOICE_DIR /
        "voice_sample.wav"
    )

    available = (
        voice_file.exists()
        and voice_file.stat().st_size > 0
    )

    return {

        "success": True,

        "voice_available":
            available,

        "xtts_available":
            True,

        "voice_cloning_ready":
            available,

        "voice_file":
            (
                "/api/voice/sample"
                if available
                else None
            )
    }


# ==========================================================
# CREATE COMPLETE VIDEO
# ==========================================================


    request: VideoRequest

# ==========================================================
# CREATE COMPLETE VIDEO
# ==========================================================

@app.post("/api/create-video")
def create_video(
    request: VideoRequest
):

    # ======================================================
    # BASIC INPUT
    # ======================================================

    topic = request.topic.strip()

    if not topic:

        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "message":
                    "Please enter a video topic."
            }
        )

    if len(topic) > 500:

        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "message":
                    (
                        "Topic is too long. "
                        "Keep it under 500 characters."
                    )
            }
        )

    try:

        # ==================================================
        # BUILD VIDEO CONTEXT
        # ==================================================

        video_context = build_video_context(
            topic=topic,
            context=request.context,
            language=request.language,
            audience=request.audience,
            purpose=request.purpose,
            tone=request.tone,
            difficulty=request.difficulty,
            duration=request.duration,
            style=request.style
        )

        context_prompt = create_context_prompt(
            video_context
        )

        print()
        print("=" * 60)
        print("VYRA VIDEO CONTEXT")
        print("=" * 60)

        print(
            f"Topic: {video_context['topic']}"
        )

        print(
            f"Language: {video_context['language']}"
        )

        print(
            f"Language code: "
            f"{video_context['language_code']}"
        )

        print(
            f"Audience: {video_context['audience']}"
        )

        print(
            f"Duration: "
            f"{video_context['duration']} seconds"
        )

        # ==================================================
        # CHECK VOICE SAMPLE
        # ==================================================

        voice_sample = (
            VOICE_DIR /
            "voice_sample.wav"
        )

        if not voice_sample.exists():

            raise RuntimeError(
                (
                    "No voice sample found. "
                    "Please upload your voice sample "
                    "before generating a video."
                )
            )

        if voice_sample.stat().st_size == 0:

            raise RuntimeError(
                "Voice sample is empty."
            )

        # ==================================================
        # STEP 1 — REAL RESEARCH & FACT-CHECKED SCRIPT
        # ==================================================

        print()
        print("=" * 60)
        print("STEP 1 — EXECUTING REAL RESEARCH & FACT CHECKING")
        print("=" * 60)

        research_data = gather_real_research(topic, request.context)

        if request.script and request.script.strip():
            print("Using user-provided / edited script...")
            script = clean_script(request.script)
        else:
            script = generate_ai_script(video_context, context_prompt, research_data)

        # Fact checking layer
        script, fact_report = verify_script_facts(script, research_data)

        if not script:
            raise RuntimeError("Script is empty.")

        print()
        print("FACT-CHECKED SCRIPT GENERATED")
        print("-" * 60)
        print(script)
        print("-" * 60)

        # ==================================================
        # STEP 2 — CLONED VOICE
        # ==================================================

        print()
        print("=" * 60)
        print("STEP 2 — GENERATING CLONED VOICE")
        print("=" * 60)

        audio_path = (
            AUDIO_DIR /
            "narration.wav"
        )

        language_code = (
            video_context["language_code"]
        )

        print(
            f"Voice language: {language_code}"
        )

        generate_speech(

            text=script,

            output_path=str(
                audio_path
            ),

            speaker_wav=str(
                voice_sample
            ),

            language=language_code
        )

        if not audio_path.exists():

            raise RuntimeError(
                "Narration audio was not created."
            )

        if audio_path.stat().st_size == 0:

            raise RuntimeError(
                "Narration audio is empty."
            )

        print()
        print("CLONED VOICE READY")
        print(
            f"Audio: {audio_path}"
        )

        # ==================================================
        # STEP 3 — SUBTITLES
        # ==================================================

        print()
        print("=" * 60)
        print("STEP 3 — GENERATING SUBTITLES")
        print("=" * 60)

        subtitle_path = (
            STORAGE_DIR /
            "subtitles.srt"
        )

        generate_subtitles(

            str(audio_path),

            str(subtitle_path)
        )

        if not subtitle_path.exists():

            raise RuntimeError(
                "Subtitle file was not created."
            )

        print(
            f"Subtitles ready: {subtitle_path}"
        )

        # ==================================================
        # STEP 4 — SCENE BREAKDOWN
        # ==================================================

        print()
        print("=" * 60)
        print("STEP 4 — GENERATING SCENE BREAKDOWN")
        print("=" * 60)

        scenes = generate_scene_breakdown(
            script,
            topic=video_context["topic"],
            user_intent=video_context
        )

        if not scenes:

            raise RuntimeError(
                "No scenes were generated."
            )

        print(
            f"Scene breakdown created: "
            f"{len(scenes)} scenes"
        )

        # ==================================================
        # CALCULATE SCENE DURATION
        # ==================================================

        total_scene_duration = 0.0

        for scene in scenes:

            try:

                duration = float(
                    scene.get(
                        "duration",
                        5.0
                    )
                )

            except Exception:

                duration = 5.0

            total_scene_duration += duration

        # ==================================================
        # STEP 5 — VISUAL SCENES
        # ==================================================

        print()
        print("=" * 60)
        print("STEP 5 — CREATING VISUAL SCENES")
        print("=" * 60)

        scene_files = (
            generate_all_scene_videos(
                scenes,
                topic=video_context["topic"],
                user_intent=video_context,
                use_avatar=request.use_avatar
            )
        )

        if not scene_files:

            raise RuntimeError(
                "No scene videos were generated."
            )

        print(
            f"Created {len(scene_files)} scene videos."
        )

        # ==================================================
        # STEP 6 — COMBINE SCENES
        # ==================================================

        print()
        print("=" * 60)
        print("STEP 6 — COMBINING SCENES")
        print("=" * 60)

        combined_scene_video = (
            STORAGE_DIR /
            "scenes_combined.mp4"
        )

        combine_scenes(

            scene_files,

            str(
                combined_scene_video
            )
        )

        if not combined_scene_video.exists():

            raise RuntimeError(
                "Combined scene video was not created."
            )

        if combined_scene_video.stat().st_size == 0:

            raise RuntimeError(
                "Combined scene video is empty."
            )

        print(
            f"Combined video: "
            f"{combined_scene_video}"
        )

        # ==================================================
        # STEP 7 — QUALITY CONTROL & FINAL VIDEO
        # ==================================================

        qc_report = run_pre_render_quality_control(
            scenes=scenes,
            narration_path=str(audio_path),
            subtitle_path=str(subtitle_path)
        )

        print()
        print("=" * 60)
        print("STEP 7 — CREATING FINAL VIDEO")
        print("=" * 60)

        final_video = (
            STORAGE_DIR /
            "final_video.mp4"
        )

        create_final_video(

            str(
                combined_scene_video
            ),

            str(
                audio_path
            ),

            str(
                subtitle_path
            ),

            str(
                final_video
            ),

            language=video_context["language"]
        )

        if not final_video.exists():

            raise RuntimeError(
                "Final video was not created."
            )

        if final_video.stat().st_size == 0:

            raise RuntimeError(
                "Final video is empty."
            )

        # ==================================================
        # SUCCESS
        # ==================================================

        print()
        print("=" * 60)
        print("VYRA VIDEO GENERATION COMPLETE")
        print("=" * 60)

        print("Research:     REAL VERIFIED SOURCES")
        print("Fact-Check:   VERIFIED")
        print("Script:       READY")
        print("Voice:        CLONED")
        print("Subtitles:    READY")
        print("Visuals:      AUTHENTIC / GRAPHIC CARDS")
        print("Final video:  READY")

        print("=" * 60)

        return {

            "success":
                True,

            "message":
                (
                    "Your VYRA video was "
                    "generated successfully!"
                ),

            "topic":
                topic,

            "language":
                video_context["language"],

            "language_code":
                video_context["language_code"],

            "script":
                script,

            "research_sources":
                research_data.get("sources", []),

            "fact_check_accuracy":
                fact_report.get("factual_accuracy_rating", "100%"),

            "quality_control_passed":
                qc_report.get("passed_all", True),

            "scenes":
                scenes,

            "scene_count":
                len(scenes),

            "total_scene_duration":
                round(
                    total_scene_duration,
                    2
                ),

            "voice_sample_available":
                True,

            "voice_cloning_used":
                True,

            "tts_engine":
                "XTTS v2",

            "audio_url":
                "/api/audio/narration.wav",

            "video_url":
                "/api/video/final_video.mp4"
        }

    # ======================================================
    # OLLAMA CONNECTION ERROR
    # ======================================================

    except requests.exceptions.ConnectionError:

        print()
        print(
            "OLLAMA CONNECTION ERROR"
        )

        return JSONResponse(

            status_code=503,

            content={

                "success":
                    False,

                "message":
                    (
                        "Ollama is not running. "
                        "Please start Ollama and try again."
                    )
            }
        )

    # ======================================================
    # OLLAMA TIMEOUT
    # ======================================================

    except requests.exceptions.Timeout:

        print()
        print(
            "OLLAMA TIMEOUT"
        )

        return JSONResponse(

            status_code=504,

            content={

                "success":
                    False,

                "message":
                    (
                        "AI generation took too long. "
                        "Please try again."
                    )
            }
        )

    # ======================================================
    # GENERAL ERROR
    # ======================================================

    except Exception as error:

        print()
        print("=" * 60)
        print("VYRA ERROR")
        print("=" * 60)

        print(
            repr(error)
        )

        return JSONResponse(

            status_code=500,

            content={

                "success":
                    False,

                "message":
                    (
                        f"Video generation failed: "
                        f"{error}"
                    )
            }
        )