import os
import sys
from pathlib import Path
import json

# Add WinGet FFmpeg DLL directory on Windows
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

from services.context_service import extract_user_intent, build_video_context
from services.research_service import gather_real_research
from services.fact_check_service import verify_script_facts
from services.tts_service import generate_speech
from services.subtitle_service import generate_subtitles
from services.scene_service import generate_scene_breakdown
from services.visual_retrieval_service import get_authentic_scene_visual
from services.presenter_service import create_default_presenter_face, overlay_presenter_avatar
from services.scene_generation_service import generate_all_scene_videos
from services.scene_video_service import combine_scenes
from services.final_video_service import create_final_video

STORAGE_DIR = Path("storage").resolve()
STORAGE_DIR.mkdir(parents=True, exist_ok=True)


def test_telugu_pipeline():
    print("\n" + "=" * 70)
    print("1. TESTING TELUGU MULTILINGUAL PIPELINE")
    print("=" * 70)

    prompt = "Create a 30-sec Telugu video about Charminar history"
    intent = extract_user_intent(prompt)
    assert intent["language"] == "telugu", f"Expected telugu, got {intent['language']}"
    assert intent["language_code"] == "te", f"Expected te, got {intent['language_code']}"

    research = gather_real_research(prompt)
    print(f"Telugu Research Completed: {research['source_count']} sources")

    script = "హైదరాబాద్‌లోని ఛార్మినార్ 1591లో నిర్మించబడిన చారిత్రక కట్టడం. ఇది కుతుబ్ షాహీ సామ్రాజ్యం యొక్క గొప్ప శిల్పకళా నైపుణ్యాన్ని ప్రతిబింబిస్తుంది."
    script, fact_report = verify_script_facts(script, research)

    audio_path = STORAGE_DIR / "audio" / "test_telugu_audio.wav"
    speaker_sample = STORAGE_DIR / "voice" / "voice_sample.wav"
    generate_speech(text=script, output_path=str(audio_path), speaker_wav=str(speaker_sample), language="te")
    assert audio_path.exists() and audio_path.stat().st_size > 1000

    srt_path = STORAGE_DIR / "test_telugu_subtitles.srt"
    generate_subtitles(str(audio_path), str(srt_path))
    assert srt_path.exists()

    scenes = generate_scene_breakdown(script, topic=intent["exact_topic"], user_intent=intent)
    assert len(scenes) > 0

    visual = get_authentic_scene_visual(scene_number=1, scene_text=scenes[0]["text"], topic=intent["exact_topic"], user_intent=intent)
    assert visual["is_authentic"] or visual["visual_strategy"] in ("AUTHENTIC_PHOTO", "AUTHENTIC_RETRIEVAL", "STAT_CARD")

    print("[OK] TELUGU PIPELINE PASSED 100%")


def test_hindi_pipeline():
    print("\n" + "=" * 70)
    print("2. TESTING HINDI MULTILINGUAL PIPELINE")
    print("=" * 70)

    prompt = "Create a 30-sec Hindi video about Taj Mahal in Agra"
    intent = extract_user_intent(prompt)
    assert intent["language"] == "hindi", f"Expected hindi, got {intent['language']}"
    assert intent["language_code"] == "hi", f"Expected hi, got {intent['language_code']}"

    research = gather_real_research(prompt)
    print(f"Hindi Research Completed: {research['source_count']} sources")

    script = "ताज महल भारत के आगरा शहर में स्थित एक विश्व प्रसिद्ध ऐतिहासिक स्मारक है। इसे मुगल सम्राट शाहजहाँ ने बनवाया था।"
    script, fact_report = verify_script_facts(script, research)

    audio_path = STORAGE_DIR / "audio" / "test_hindi_audio.wav"
    speaker_sample = STORAGE_DIR / "voice" / "voice_sample.wav"
    generate_speech(text=script, output_path=str(audio_path), speaker_wav=str(speaker_sample), language="hi")
    assert audio_path.exists() and audio_path.stat().st_size > 1000

    srt_path = STORAGE_DIR / "test_hindi_subtitles.srt"
    generate_subtitles(str(audio_path), str(srt_path))
    assert srt_path.exists()

    scenes = generate_scene_breakdown(script, topic=intent["exact_topic"], user_intent=intent)
    assert len(scenes) > 0

    visual = get_authentic_scene_visual(scene_number=1, scene_text=scenes[0]["text"], topic=intent["exact_topic"], user_intent=intent)
    assert visual["is_authentic"] or visual["visual_strategy"] in ("AUTHENTIC_PHOTO", "AUTHENTIC_RETRIEVAL", "STAT_CARD")

    print("[OK] HINDI PIPELINE PASSED 100%")


def test_english_pipeline():
    print("\n" + "=" * 70)
    print("3. TESTING ENGLISH MULTILINGUAL PIPELINE")
    print("=" * 70)

    prompt = "Explain Chandrayaan-3 Moon Landing in English"
    intent = extract_user_intent(prompt)
    assert intent["language"] == "english", f"Expected english, got {intent['language']}"

    research = gather_real_research(prompt)
    script = "Chandrayaan-3 is India's third lunar exploration mission developed by ISRO. On August 23 2023 the lander landed near the lunar south pole."
    script, fact_report = verify_script_facts(script, research)

    audio_path = STORAGE_DIR / "audio" / "test_english_audio.wav"
    speaker_sample = STORAGE_DIR / "voice" / "voice_sample.wav"
    generate_speech(text=script, output_path=str(audio_path), speaker_wav=str(speaker_sample), language="en")
    assert audio_path.exists() and audio_path.stat().st_size > 1000

    srt_path = STORAGE_DIR / "test_english_subtitles.srt"
    generate_subtitles(str(audio_path), str(srt_path))
    assert srt_path.exists()

    print("[OK] ENGLISH PIPELINE PASSED 100%")


def test_avatar_presenter_pipeline():
    print("\n" + "=" * 70)
    print("4. TESTING AVATAR PRESENTER PIPELINE (AUTHENTIC BACKGROUND constraint)")
    print("=" * 70)

    face_path = create_default_presenter_face()
    assert face_path.exists(), "Presenter face avatar was not created"

    prompt = "Chandrayaan-3 Mission by ISRO"
    intent = extract_user_intent(prompt)
    intent["use_avatar"] = True

    script = "Welcome to VYRA. India's Chandrayaan-3 made history by landing on the Moon."
    scenes = generate_scene_breakdown(script, topic=intent["exact_topic"], user_intent=intent)

    # 1. Retrieve authentic background
    visual = get_authentic_scene_visual(scene_number=1, scene_text=scenes[0]["text"], topic=intent["exact_topic"], user_intent=intent)
    assert visual["is_authentic"] or visual["visual_strategy"] in ("AUTHENTIC_PHOTO", "AUTHENTIC_RETRIEVAL", "STAT_CARD"), "Background must be authentic media"

    # 2. Overlay Digital Avatar on authentic background
    bg_img = visual.get("image_path", str(STORAGE_DIR / "ai_scenes" / "scene_1.png"))
    out_img = str(STORAGE_DIR / "ai_scenes" / "test_avatar_overlay_scene.png")
    res_img = overlay_presenter_avatar(background_image_path=bg_img, output_image_path=out_img, scene_number=1, is_speaking=True)
    assert Path(res_img).exists() and Path(res_img).stat().st_size > 5000

    # 3. Generate Scene Video & Final Video
    scene_files = generate_all_scene_videos(scenes, topic=intent["exact_topic"], user_intent=intent, use_avatar=True)
    assert len(scene_files) > 0

    combined_video = STORAGE_DIR / "test_avatar_combined.mp4"
    combine_scenes(scene_files, str(combined_video))

    audio_path = STORAGE_DIR / "audio" / "test_avatar_audio.wav"
    speaker_sample = STORAGE_DIR / "voice" / "voice_sample.wav"
    generate_speech(text=script, output_path=str(audio_path), speaker_wav=str(speaker_sample), language="en")

    srt_path = STORAGE_DIR / "test_avatar_subtitles.srt"
    generate_subtitles(str(audio_path), str(srt_path))

    final_avatar_mp4 = STORAGE_DIR / "test_final_avatar_video.mp4"
    create_final_video(
        scenes_video=str(combined_video),
        audio_path=str(audio_path),
        subtitle_path=str(srt_path),
        output_path=str(final_avatar_mp4)
    )

    assert final_avatar_mp4.exists() and final_avatar_mp4.stat().st_size > 100_000
    print(f"[OK] AVATAR PRESENTER PIPELINE PASSED 100%: {final_avatar_mp4} ({final_avatar_mp4.stat().st_size:,} bytes)")


if __name__ == "__main__":
    test_telugu_pipeline()
    test_hindi_pipeline()
    test_english_pipeline()
    test_avatar_presenter_pipeline()
    print("\n" + "=" * 70)
    print("ALL MULTILINGUAL & AVATAR PIPELINE TESTS PASSED 100%")
    print("=" * 70)
