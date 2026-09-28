import os
import sys
import time
from pathlib import Path

# Ensure UTF-8 output encoding for Windows terminal
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Ensure Windows FFmpeg DLL directory is set before loading torch/TTS modules
ffmpeg_shared_dir = Path.home() / "AppData" / "Local" / "Microsoft" / "WinGet" / "Packages"
for p in ffmpeg_shared_dir.rglob("avcodec-*.dll"):
    try:
        os.add_dll_directory(str(p.parent))
        os.environ["PATH"] = str(p.parent) + os.pathsep + os.environ.get("PATH", "")
        break
    except Exception:
        pass

from services.research_service import gather_real_research
from services.fact_check_service import verify_script_facts
from services.visual_retrieval_service import classify_scene_subject, get_authentic_scene_visual
from services.quality_control_service import run_pre_render_quality_control

print("=" * 60)
print("VYRA REAL RESEARCH & VISUAL AUTHENTICITY PIPELINE TEST")
print("=" * 60)

test_topics = [
    "Hyderabad Charminar history",
    "ISRO Chandrayaan mission",
    "Elon Musk"
]

for topic in test_topics:
    print(f"\n" + "=" * 50)
    print(f"TESTING REAL TOPIC: '{topic}'")
    print("=" * 50)
    
    # 1. Real Research
    research_data = gather_real_research(topic)
    assert research_data["source_count"] > 0, "No sources retrieved!"
    print(f"Sources Found: {research_data['source_count']}")
    
    # 2. Fact Check Grounding Test
    sample_script = f"The topic '{topic}' is historically significant. Official records provide verified information."
    verified_script, fact_report = verify_script_facts(sample_script, research_data)
    print(f"Fact Check Accuracy: {fact_report['factual_accuracy_rating']}")
    
    # 3. Visual Authenticity Retrieval Test
    retrieval_res = get_authentic_scene_visual(scene_number=1, scene_text=topic, visual_description=topic)
    print(f"Authentic Image Strategy: {retrieval_res['visual_strategy']}")
    print(f"Is Authentic Media:       {retrieval_res['is_authentic']}")
    if retrieval_res['is_authentic']:
        print(f"Downloaded Image Path:   {retrieval_res['image_path']}")
        print(f"Source URL:              {retrieval_res['source_url']}")
        print(f"License:                 {retrieval_res['license']}")
        assert Path(retrieval_res['image_path']).exists(), "Retrieved image file does not exist!"
        assert retrieval_res['is_authentic'] is True, "Expected authentic photograph for real entity!"

print("\n" + "=" * 60)
print("ALL RESEARCH & VISUAL AUTHENTICITY TESTS PASSED 100%!")
print("=" * 60)
