from pathlib import Path
import json
import requests
import re

BASE_DIR = Path(__file__).resolve().parent.parent
STORAGE_DIR = BASE_DIR / "storage"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)


# ==========================================================
# TOPIC SANITIZER HELPER
# ==========================================================

def extract_core_topic(raw_topic: str) -> str:
    """
    Extracts the core subject/entity from prompt instructions if user pastes a long prompt.
    E.g.: 'Create a 60-sec Telugu video about Chandrayaan-3. Research facts...' -> 'Chandrayaan-3'
    """
    text = str(raw_topic or "").strip()
    if not text:
        return ""
        
    # Match patterns like "about X", "topic X", "history of X", "on X"
    match = re.search(r'\b(?:about|on|regarding|topic|history of)\s+([^.\n,!?]+)', text, re.IGNORECASE)
    if match:
        extracted = match.group(1).strip()
        # Clean extra instructions
        extracted = re.sub(r'\b(?:research|verify|use|make|create|video|script|facts|authentic|real|photos|footage|subtitles|make it|cinematic|professional)\b.*', '', extracted, flags=re.IGNORECASE).strip()
        if len(extracted) > 2:
            return extracted
            
    # Take first sentence and strip prompt commands
    first_sentence = re.split(r'[.\n!?]', text)[0].strip()
    cleaned = re.sub(r'^(?:create|make|generate|produce|write|explain)\s+(?:a\s+)?(?:\d+[- ](?:sec|second|min|minute)\s+)?(?:telugu|english|hindi\s+)?(?:video|script)\s+(?:about|on)?\s*', '', first_sentence, flags=re.IGNORECASE).strip()
    
    if len(cleaned) > 2:
        return cleaned
        
    return text[:60]


# ==========================================================
# RESEARCH SERVICE
# ==========================================================

def search_wikipedia_api(query: str, limit: int = 5) -> list:
    """
    Search Wikipedia API for canonical factual information on a topic.
    """
    url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "list": "search",
        "srsearch": query,
        "format": "json",
        "srlimit": limit
    }
    headers = {"User-Agent": "VYRA-ResearchEngine/2.5 (https://vyra.ai)"}

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json().get("query", {}).get("search", [])
    except Exception as e:
        print(f"[Research Error] Wikipedia search failed for '{query}': {e}")
    return []


def get_wikipedia_summary(title: str) -> dict:
    """
    Get official REST summary and metadata for a specific Wikipedia page.
    """
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{requests.utils.quote(title)}"
    headers = {"User-Agent": "VYRA-ResearchEngine/2.5 (https://vyra.ai)"}

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return {
                "title": data.get("title", title),
                "extract": data.get("extract", ""),
                "description": data.get("description", ""),
                "url": data.get("content_urls", {}).get("desktop", {}).get("page", f"https://en.wikipedia.org/wiki/{title}"),
                "thumbnail": data.get("thumbnail", {}).get("source"),
                "original_image": data.get("originalimage", {}).get("source"),
                "source_type": "Authoritative Encyclopedia"
            }
    except Exception as e:
        print(f"[Research Error] Wikipedia summary failed for '{title}': {e}")
    return {}


def gather_real_research(topic: str, user_context: str = "") -> dict:
    """
    Executes real multi-source research for a topic.
    Gathers canonical facts, official summaries, and source URLs.
    """
    raw_topic = str(topic or "").strip()
    search_query = extract_core_topic(raw_topic)
    
    print()
    print("=" * 60)
    print("VYRA RESEARCH ENGINE — GATHERING REAL FACTS")
    print("=" * 60)
    print(f"Raw Input:    {raw_topic[:80]}...")
    print(f"Search Term:  {search_query}")

    sources = []
    combined_extracts = []
    key_facts = []

    # 1. Primary Wikipedia Search with cleaned search query
    wiki_results = search_wikipedia_api(search_query, limit=4)
    for result in wiki_results:
        page_title = result.get("title")
        if not page_title:
            continue
        
        summary = get_wikipedia_summary(page_title)
        if summary and summary.get("extract"):
            sources.append({
                "title": summary["title"],
                "url": summary["url"],
                "description": summary.get("description", ""),
                "type": summary["source_type"],
                "original_image": summary.get("original_image"),
                "thumbnail": summary.get("thumbnail")
            })
            combined_extracts.append(f"[{summary['title']}]: {summary['extract']}")
            
            # Extract key sentences as bullet points
            sentences = re.split(r'\. |\.\n', summary['extract'])
            for s in sentences:
                s_clean = s.strip()
                if len(s_clean) > 20 and s_clean not in key_facts:
                    key_facts.append(s_clean)

    # 2. Add user context if present
    if user_context and user_context.strip():
        combined_extracts.append(f"[User Context]: {user_context.strip()}")

    full_summary = "\n\n".join(combined_extracts) if combined_extracts else f"Factual reference for: {search_query}"
    
    # Trim summary to top 800 characters for fast Ollama script generation
    trimmed_summary = full_summary[:800]

    research_payload = {
        "topic": search_query,
        "raw_topic": raw_topic,
        "research_summary": trimmed_summary,
        "key_facts": key_facts[:8],
        "sources": sources,
        "source_count": len(sources)
    }

    # Save research data to disk
    research_file = STORAGE_DIR / "research_data.json"
    with open(research_file, "w", encoding="utf-8") as f:
        json.dump(research_payload, f, indent=2, ensure_ascii=False)

    print(f"Research completed with {len(sources)} verified sources.")
    for src in sources:
        print(f"  - {src['title']}: {src['url']}")

    return research_payload
