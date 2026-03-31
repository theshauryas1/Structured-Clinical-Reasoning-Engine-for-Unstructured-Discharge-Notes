import json
import math
import re
from functools import lru_cache
from pathlib import Path
from typing import Dict, List

KB_PATH = Path(__file__).resolve().parent / "knowledge_base.jsonl"
TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


def _tokenize(text: str) -> List[str]:
    return TOKEN_PATTERN.findall(text.lower())


@lru_cache(maxsize=1)
def load_knowledge_base() -> List[Dict[str, object]]:
    knowledge_base: List[Dict[str, object]] = []
    with KB_PATH.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                knowledge_base.append(json.loads(line))
    return knowledge_base


def _document_text(entry: Dict[str, object]) -> str:
    keywords = " ".join(entry.get("keywords", []))
    complications = " ".join(entry.get("complications", []))
    return f"{entry.get('condition', '')} {entry.get('summary', '')} {keywords} {complications} {entry.get('follow_up', '')}"


def _idf(knowledge_base: List[Dict[str, object]], token: str) -> float:
    docs_with_token = 0
    for entry in knowledge_base:
        if token in set(_tokenize(_document_text(entry))):
            docs_with_token += 1
    if docs_with_token == 0:
        return 0.0
    return math.log((1 + len(knowledge_base)) / (1 + docs_with_token)) + 1


def retrieve_context(query_text: str, top_k: int = 3) -> List[Dict[str, object]]:
    knowledge_base = load_knowledge_base()
    query_tokens = _tokenize(query_text)
    if not query_tokens:
        return []

    scored_entries: List[Dict[str, object]] = []
    query_token_set = set(query_tokens)

    for entry in knowledge_base:
        entry_tokens = _tokenize(_document_text(entry))
        entry_token_set = set(entry_tokens)
        overlap = query_token_set & entry_token_set
        if not overlap:
            continue

        lexical_score = sum(_idf(knowledge_base, token) for token in overlap)
        keyword_bonus = 0.0
        for keyword in entry.get("keywords", []):
            if keyword.lower() in query_text.lower():
                keyword_bonus += 0.3

        total_score = lexical_score + keyword_bonus
        scored_entries.append(
            {
                "condition": entry["condition"],
                "summary": entry["summary"],
                "follow_up": entry["follow_up"],
                "score": round(total_score, 4),
            }
        )

    scored_entries.sort(key=lambda item: item["score"], reverse=True)
    return scored_entries[:top_k]
