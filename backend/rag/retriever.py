import json
import logging
import math
import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Dict, List
from sqlalchemy import create_engine, text

logger = logging.getLogger(__name__)

KB_PATH = Path(__file__).resolve().parent / "knowledge_base.jsonl"
TOKEN_PATTERN = re.compile(r"[a-z0-9]+")

_pg_engine = None


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


def _get_pg_engine():
    global _pg_engine
    if _pg_engine is None:
        db_url = os.getenv("DATABASE_URL")
        if db_url:
            if db_url.startswith("postgres://"):
                db_url = db_url.replace("postgres://", "postgresql+psycopg://", 1)
            elif db_url.startswith("postgresql://"):
                db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)
            _pg_engine = create_engine(db_url, pool_pre_ping=True, future=True)
    return _pg_engine


def retrieve_context(query_text: str, top_k: int = 3) -> List[Dict[str, object]]:
    # Check if we should use PostgreSQL semantic search
    db_url = os.getenv("DATABASE_URL")
    has_nim_key = bool(os.getenv("NVIDIA_NIM_API_KEY"))

    if db_url and (db_url.startswith("postgres") or db_url.startswith("postgresql")) and has_nim_key:
        try:
            logger.info("Attempting pgvector semantic retrieval from PostgreSQL...")
            from backend.rag.embeddings import get_embedding

            # Fetch query embedding from NVIDIA NIM
            query_embedding = get_embedding(query_text, is_query=True)

            engine = _get_pg_engine()
            if engine:
                with engine.connect() as conn:
                    # Query guidelines using pgvector cosine similarity
                    query = text(
                        """
                        SELECT condition, summary, follow_up, 
                               1 - (embedding <=> CAST(:emb AS vector)) AS similarity
                        FROM clinical_guidelines
                        ORDER BY embedding <=> CAST(:emb AS vector)
                        LIMIT :top_k;
                    """
                    )
                    result = conn.execute(
                        query, {"emb": str(query_embedding), "top_k": top_k}
                    )

                    scored_entries = []
                    for row in result:
                        scored_entries.append(
                            {
                                "condition": row.condition,
                                "summary": row.summary,
                                "follow_up": row.follow_up,
                                "score": round(float(row.similarity), 4),
                            }
                        )

                    if scored_entries:
                        logger.info(
                            f"Successfully retrieved {len(scored_entries)} guideline matches via pgvector."
                        )
                        return scored_entries
        except Exception as exc:
            logger.warning(
                f"pgvector semantic retrieval failed, falling back to lexical search: {exc}"
            )

    logger.info("Running local TF-IDF lexical retrieval fallback...")
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
