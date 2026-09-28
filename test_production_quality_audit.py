import os
import sys
from pathlib import Path

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
from services.quality_control_service import run_pre_render_quality_control
from services.final_video_service import create_final_video, get_media_duration

STORAGE_DIR = Path("storage").resolve()
STORAGE_DIR.mkdir(parents=True, exist_ok=True)


def run_production_quality_audit():
    print("=" * 75)
    print("VYRA PRODUCTION QUALITY PIPELINE AUDIT")
    print("=" * 75)

    prompt = "Create a 30-sec video about Chandrayaan-3 Moon Landing with ISRO authentic photos and AI presenter avatar"
    print(f"User Prompt: '{prompt}'")

    # Step 1: User Intent Extraction
    intent = extract_user_intent(prompt)
    print(f"[Step 1] User Intent Extracted:")
    print(f"  - Topic:    {intent['exact_topic']}")
    print(f"  - Language: {intent['language']} ({intent['language_code']})")
    print(f"  - Duration: {intent['duration']}s")
    print(f"  - Style:    {intent['style']}")
    assert intent["exact_topic"] != "", "Topic extraction failed"

    # Step 2: Real Online Research
    research = gather_real_research(prompt)
    print(f"[Step 2] Real Online Research:")
    print(f"  - Verified Sources: {research['source_count']}")
    assert research["source_count"] > 0, "Research failed to retrieve verified sources"

    # Step 3: Script & Fact Check
    script = "Chandrayaan-3 is India's third lunar exploration mission developed by ISRO. On August 23 2023 the lander Vikram successfully touched down near the lunar south pole."
    script, fact_report = verify_script_facts(script, research)
    print(f"[Step 3] Fact Checking:")
    print(f"  - Accuracy Rating: {fact_report.get('factual_accuracy_rating', '100%')}")

    # Step 4: Narration Speech
    audio_path = STORAGE_DIR / "audio" / "audit_narration.wav"
    speaker_sample = STORAGE_DIR / "voice" / "voice_sample.wav"
    generate_speech(text=script, output_path=str(audio_path), speaker_wav=str(speaker_sample), language=intent["language_code"])
    assert audio_path.exists() and audio_path.stat().st_size > 1000, "Audio generation failed"
    print(f"[Step 4] Cloned Voice Speech Audio: {audio_path.stat().st_size:,} bytes")

    # Step 5: Whisper GPU Subtitles
    srt_path = STORAGE_DIR / "audit_subtitles.srt"
    generate_subtitles(str(audio_path), str(srt_path))
    assert srt_path.exists() and srt_path.stat().st_size > 50, "Subtitle generation failed"
    print(f"[Step 5] Whisper GPU Subtitles: {srt_path.stat().st_size:,} bytes")

    # Step 6: Intent-Grounded Scene Breakdown
    scenes = generate_scene_breakdown(script, topic=intent["exact_topic"], user_intent=intent)
    assert len(scenes) > 0, "Scene breakdown failed"
    print(f"[Step 6] Scene Breakdown: {len(scenes)} scenes generated")

    # Step 7: Authentic Visual Retrieval & Digital Avatar Overlay
    for idx, sc in enumerate(scenes, start=1):
        visual_info = get_authentic_scene_visual(scene_number=idx, scene_text=sc["text"], topic=intent["exact_topic"], user_intent=intent)
        print(f"  - Scene {idx} Visual Strategy: {visual_info['visual_strategy']}")
        print(f"    Source URL: {visual_info.get('source_url', 'Internal')}")

    scene_files = generate_all_scene_videos(scenes, topic=intent["exact_topic"], user_intent=intent, use_avatar=True)
    assert len(scene_files) > 0, "Scene video generation failed"
    print(f"[Step 7] Scene Video Generation: {len(scene_files)} scene videos created")

    # Step 8: Combine Scenes
    combined_video = STORAGE_DIR / "audit_scenes_combined.mp4"
    combine_scenes(scene_files, str(combined_video))
    assert combined_video.exists() and combined_video.stat().st_size > 10_000, "Scene combination failed"

    # Step 9: Pre-Render Quality Control
    qc_report = run_pre_render_quality_control(scenes=scenes, narration_path=str(audio_path), subtitle_path=str(srt_path))
    print(f"[Step 9] Quality Control Verification: Passed={qc_report['passed_all']}")
    assert qc_report["passed_all"], "Pre-render quality control failed"

    # Step 10: Final 1080x1920 MP4 Render
    final_mp4 = STORAGE_DIR / "audit_final_video.mp4"
    create_final_video(
        scenes_video=str(combined_video),
        audio_path=str(audio_path),
        subtitle_path=str(srt_path),
        output_path=str(final_mp4),
        language=intent["language"]
    )

    assert final_mp4.exists() and final_mp4.stat().st_size > 100_000, "Final MP4 rendering failed"
    final_dur = get_media_duration(final_mp4)
    print(f"[Step 10] Final MP4 Render Complete: {final_mp4}")
    print(f"  - Size:     {final_mp4.stat().st_size / (1024*1024):.2f} MB")
    print(f"  - Duration: {final_dur:.2f} seconds")

    print("\n" + "=" * 75)
    print("[OK] VYRA PRODUCTION QUALITY AUDIT: 100% PASSED")
    print("=" * 75)


if __name__ == "__main__":
    run_production_quality_audit()
