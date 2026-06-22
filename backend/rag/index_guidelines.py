import json
import logging
from pathlib import Path
from sqlalchemy import text
from backend.rag.embeddings import get_embedding

logger = logging.getLogger(__name__)

KB_PATH = Path(__file__).resolve().parent / "knowledge_base.jsonl"


def index_guidelines_to_postgres(engine) -> None:
    """
    Enables pgvector, creates clinical_guidelines table, and indexes
    guidelines with semantic embeddings in PostgreSQL.
    """
    try:
        with engine.connect() as conn:
            # 1. Enable pgvector extension
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            conn.commit()

            # 2. Create the guidelines table
            conn.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS clinical_guidelines (
                    id SERIAL PRIMARY KEY,
                    condition TEXT NOT NULL UNIQUE,
                    summary TEXT NOT NULL,
                    follow_up TEXT NOT NULL,
                    embedding vector(1024) NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
            """
                )
            )
            conn.commit()

            # 3. Read guidelines from JSONL
            if not KB_PATH.exists():
                logger.error(f"Knowledge base file not found at {KB_PATH}")
                return

            guidelines = []
            with KB_PATH.open("r", encoding="utf-8") as handle:
                for line in handle:
                    if line.strip():
                        guidelines.append(json.loads(line))

            # 4. Check if guidelines are already loaded
            result = conn.execute(text("SELECT COUNT(*) FROM clinical_guidelines;"))
            count = result.scalar()
            if count >= len(guidelines):
                logger.info("Clinical guidelines are already indexed in PostgreSQL.")
                return

            logger.info(
                f"Indexing {len(guidelines)} guidelines into PostgreSQL using NIM embeddings..."
            )

            # 5. Index missing guidelines
            for entry in guidelines:
                condition = entry.get("condition", "")
                summary = entry.get("summary", "")
                follow_up = entry.get("follow_up", "")

                # Check if this specific condition exists
                res = conn.execute(
                    text("SELECT 1 FROM clinical_guidelines WHERE condition = :cond LIMIT 1;"),
                    {"cond": condition},
                )
                if res.first():
                    continue

                # Formulate rich text representation for passage embedding
                passage_text = (
                    f"Condition: {condition}. Summary: {summary} Follow-up: {follow_up}"
                )

                # Retrieve embedding using NIM embeddings client
                embedding_vector = get_embedding(passage_text, is_query=False)

                # Insert record with vector cast
                conn.execute(
                    text(
                        """
                        INSERT INTO clinical_guidelines (condition, summary, follow_up, embedding)
                        VALUES (:cond, :sum, :fol, CAST(:emb AS vector));
                    """
                    ),
                    {
                        "cond": condition,
                        "sum": summary,
                        "fol": follow_up,
                        "emb": str(embedding_vector),
                    },
                )
                conn.commit()
                logger.info(f"Successfully indexed guideline for: {condition}")

    except Exception as exc:
        logger.error(f"Failed to execute pgvector database migrations or indexing: {exc}")
        # Log error but let the application start up (graceful resilience)
