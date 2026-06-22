import pytest
from fastapi.testclient import TestClient
from backend.main import app

def test_list_reports_endpoint(monkeypatch):
    class MockReasoningOutput:
        id = "test-note-123"
        generated_at = None
        timeline_json = {"sections": [{"events": [{}, {}]}]}
        differentials_json = [{}, {}]
        contradictions_json = [{}]
        report_json = {
            "source_language": "de",
            "display_language": "en"
        }

    # Mock Session context manager
    class MockSession:
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc_val, exc_tb):
            pass
        def query(self, model):
            return self
        def order_by(self, expression):
            return self
        def all(self):
            return [MockReasoningOutput()]

    monkeypatch.setattr("backend.main.SessionLocal", lambda: MockSession())

    with TestClient(app) as client:
        response = client.get("/reports")
        assert response.status_code == 200
        payload = response.json()
        assert len(payload) == 1
        assert payload[0]["note_id"] == "test-note-123"
        assert payload[0]["event_count"] == 2
        assert payload[0]["contradiction_count"] == 1
        assert payload[0]["differential_count"] == 2
        assert payload[0]["source_language"] == "de"
        assert payload[0]["display_language"] == "en"

def test_delete_report_endpoint(monkeypatch):
    deleted_records = []
    
    class MockSession:
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc_val, exc_tb):
            pass
        def get(self, model, id):
            return f"record-{model.__tablename__}-{id}"
        def delete(self, record):
            deleted_records.append(record)
        def commit(self):
            pass

    monkeypatch.setattr("backend.main.SessionLocal", lambda: MockSession())

    with TestClient(app) as client:
        response = client.delete("/report/test-note-123")
        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] == "deleted"
        assert payload["note_id"] == "test-note-123"
        # Verify both records were queried and deleted
        assert len(deleted_records) == 2
        assert any("clinical_notes" in r for r in deleted_records)
        assert any("reasoning_outputs" in r for r in deleted_records)
