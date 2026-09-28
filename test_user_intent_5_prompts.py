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
from services.scene_service import generate_scene_breakdown
from services.visual_retrieval_service import get_authentic_scene_visual

TEST_PROMPTS = [
    {
        "id": 1,
        "prompt": "Create a 60-sec Telugu documentary video about Chandrayaan-3 Moon landing with dramatic tone and real photos",
        "expected_topic": "Chandrayaan-3 Moon landing",
        "expected_lang": "telugu",
        "expected_code": "te",
        "expected_duration": 60,
        "expected_style": "documentary",
        "expected_tone": "dramatic"
    },
    {
        "id": 2,
        "prompt": "Explain Quantum Computing for beginners in 30 seconds with an educational tone and clear diagrams",
        "expected_topic": "Quantum Computing",
        "expected_lang": "english",
        "expected_code": "en",
        "expected_duration": 30,
        "expected_audience": "beginners",
        "expected_style": "educational"
    },
    {
        "id": 3,
        "prompt": "Un video en español sobre la historia del Imperio Inca y Machu Picchu en 45s",
        "expected_topic": "Imperio Inca y Machu Picchu",
        "expected_lang": "spanish",
        "expected_code": "es",
        "expected_duration": 45
    },
    {
        "id": 4,
        "prompt": "Un documentaire court en français sur la Révolution Française de 1789 avec des photos historiques",
        "expected_topic": "Révolution Française de 1789",
        "expected_lang": "french",
        "expected_code": "fr",
        "expected_duration": 45,
        "expected_style": "documentary"
    },
    {
        "id": 5,
        "prompt": "How to prepare authentic Hyderabadi Biryani in 45-sec with culinary storytelling style",
        "expected_topic": "Hyderabadi Biryani",
        "expected_lang": "english",
        "expected_code": "en",
        "expected_duration": 45,
        "expected_style": "storytelling"
    }
]


def run_intent_test():
    print("=" * 70)
    print("VYRA USER-INTENT TESTING — 5 DIVERSE PROMPTS")
    print("=" * 70)

    passed_count = 0

    for item in TEST_PROMPTS:
        p_id = item["id"]
        prompt = item["prompt"]
        print(f"\n--- TEST PROMPT #{p_id} ---")
        print(f"Raw Input: '{prompt}'")

        # 1. Extract Intent
        intent = extract_user_intent(prompt)
        print(f"Extracted Topic:       '{intent['exact_topic']}'")
        print(f"Extracted Language:    {intent['requested_language']} ({intent['language_code']})")
        print(f"Extracted Duration:    {intent['duration']}s")
        print(f"Extracted Tone:        {intent['tone']}")
        print(f"Extracted Style:       {intent['style']}")
        print(f"Extracted Audience:    {intent['audience']}")
        print(f"Entities Found:        {intent['entities']}")

        # Assertions
        assert intent["language"] == item["expected_lang"], f"Expected {item['expected_lang']}, got {intent['language']}"
        assert intent["language_code"] == item["expected_code"], f"Expected {item['expected_code']}, got {intent['language_code']}"
        assert intent["duration"] == item["expected_duration"], f"Expected {item['expected_duration']}, got {intent['duration']}"
        if "expected_style" in item:
            assert intent["style"] == item["expected_style"], f"Expected style {item['expected_style']}, got {intent['style']}"

        # 2. Perform Real Research
        research = gather_real_research(prompt)
        print(f"Research Sources:      {research['source_count']} verified sources")

        # 3. Scene Breakdown Grounded in Intent
        test_script = f"Exploring {intent['exact_topic']}. Key facts and historical details define this subject."
        scenes = generate_scene_breakdown(test_script, topic=intent["exact_topic"], user_intent=intent)
        print(f"Scenes Generated:      {len(scenes)} scenes")
        assert len(scenes) > 0, "Scene breakdown returned empty list"

        # 4. Authentic Visual Decision
        visual = get_authentic_scene_visual(scene_number=1, scene_text=scenes[0]["text"], topic=intent["exact_topic"], user_intent=intent)
        print(f"Visual Strategy:       {visual['visual_strategy']}")
        print(f"Visual Source:         {visual.get('source_url', 'Internal Generator')}")

        print(f"[OK] TEST #{p_id} PASSED 100%")
        passed_count += 1

    print("\n" + "=" * 70)
    print(f"VYRA USER-INTENT TEST SUITE RESULT: {passed_count}/{len(TEST_PROMPTS)} PASSED 100%")
    print("=" * 70)


if __name__ == "__main__":
    run_intent_test()
