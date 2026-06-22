import os
import pytest
from unittest.mock import MagicMock, patch
from backend.rag.embeddings import get_embedding
from backend.rag.retriever import retrieve_context


@pytest.fixture
def mock_env(monkeypatch):
    monkeypatch.setenv("NVIDIA_NIM_API_KEY", "mock-key")
    monkeypatch.setenv("NVIDIA_NIM_BASE_URL", "https://mock.nvidia.com/v1")
    monkeypatch.setenv("NVIDIA_NIM_EMBEDDING_MODEL", "nvidia/nv-embedqa-e5-v5")
    # Reset cached engine
    monkeypatch.setattr("backend.rag.retriever._pg_engine", None)


def test_get_embedding_payload(mock_env):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": [{"embedding": [0.1, 0.2, 0.3]}]}

    with patch("requests.post", return_value=mock_response) as mock_post:
        embedding = get_embedding("test query", is_query=True)
        assert embedding == [0.1, 0.2, 0.3]
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert args[0] == "https://mock.nvidia.com/v1/embeddings"
        payload = kwargs["json"]
        assert payload["model"] == "nvidia/nv-embedqa-e5-v5"
        assert payload["input"] == ["test query"]
        assert payload["input_type"] == "query"


def test_lexical_fallback_on_sqlite(monkeypatch):
    # Force SQLite
    monkeypatch.setenv("DATABASE_URL", "sqlite:///test.db")
    monkeypatch.setenv("NVIDIA_NIM_API_KEY", "")

    # Run retrieval
    results = retrieve_context("pneumonia cough fever", top_k=2)
    assert len(results) > 0
    # The condition "Community-acquired pneumonia" contains these words
    assert any("pneumonia" in r["condition"].lower() for r in results)
    assert all("score" in r for r in results)


def test_postgres_semantic_search_flow(mock_env, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://mockuser:mockpass@mockhost/mockdb")

    mock_embedding = [0.0] * 1024

    # Mock embeddings client
    mock_get_embedding = MagicMock(return_value=mock_embedding)
    monkeypatch.setattr("backend.rag.embeddings.get_embedding", mock_get_embedding)

    # Mock db connection execution
    mock_row = MagicMock()
    mock_row.condition = "Acute ischemic stroke"
    mock_row.summary = "Stroke summary"
    mock_row.follow_up = "Follow up"
    mock_row.similarity = 0.85

    mock_conn = MagicMock()
    mock_conn.execute.return_value = [mock_row]

    mock_engine = MagicMock()
    mock_engine.connect.return_value.__enter__.return_value = mock_conn

    # Inject mock engine
    monkeypatch.setattr("backend.rag.retriever._pg_engine", mock_engine)

    results = retrieve_context("unilateral weakness", top_k=1)

    assert len(results) == 1
    assert results[0]["condition"] == "Acute ischemic stroke"
    assert results[0]["score"] == 0.85

    # Check that pgvector SQL query was executed
    mock_conn.execute.assert_called_once()
    called_sql = str(mock_conn.execute.call_args[0][0])
    assert "<=>" in called_sql
    assert "clinical_guidelines" in called_sql
