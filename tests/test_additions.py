import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.ingestion.file_extractor import extract_content


def test_file_extractor_txt():
    content = b"ADMISSION SUMMARY:\nPatient admitted with fever."
    text, warnings = extract_content(content, "note.txt", "text/plain")
    assert "ADMISSION SUMMARY:" in text
    assert warnings == ""


def test_file_extractor_unsupported():
    content = b"random binary bytes"
    with pytest.raises(ValueError, match="Unsupported file format"):
        extract_content(content, "doc.pdf.exe", "application/octet-stream")


def test_ingest_file_endpoint(monkeypatch):
    # Mock out the pipeline reasoning graph execution to run fast
    from backend.agents.models import NoteReport, ClinicalTimeline
    
    # Simple mock return report
    class MockTimeline:
        warnings = []
        sections = []
        raw_text = "ADMISSION SUMMARY: Fever."
        extractor_backend = "rules"

    mock_report = NoteReport(
        note_id="uploaded-note",
        timeline=ClinicalTimeline(raw_text="ADMISSION SUMMARY: Fever.", extractor_backend="rules"),
        differentials=[],
        contradiction_flags=[],
        confidence_scores=[]
    )
    
    monkeypatch.setattr(
        "backend.main.run_reasoning_pipeline",
        lambda text, note_id: mock_report
    )
    
    # Mock translation edge to bypass
    monkeypatch.setattr("backend.main.detect_input_language", lambda text, lang: ("en", []))
    monkeypatch.setattr("backend.main.translate", lambda text, src_lang, to_english: text)
    monkeypatch.setattr("backend.main.build_display_report", lambda payload, lang: payload)

    with TestClient(app) as client:
        # Mock a text file upload
        files = {"file": ("note.txt", b"ADMISSION SUMMARY: Patient with fever.", "text/plain")}
        data = {"lang": "en", "display_lang": "en"}
        
        response = client.post("/ingest-file", files=files, data=data)
        assert response.status_code == 200
        payload = response.json()
        assert payload["note_id"] == "uploaded-note"
        assert "timeline" in payload


def test_chat_endpoint(monkeypatch):
    # Mock database report retrieval
    monkeypatch.setattr(
        "backend.main.get_report",
        lambda note_id: {
            "note_id": note_id,
            "timeline": {"sections": []},
            "contradiction_flags": [],
            "differentials": [{"name": "Atrial fibrillation", "rank": 1, "score": 0.85, "rationale": "palpitations"}],
            "confidence_scores": []
        }
    )
    
    # Mock LLM completions response
    def mock_call_llm(messages):
        system_content = messages[0]["content"]
        if "expert clinical reasoning assistant" in system_content:
            return "[Disclaimer: This assistant is for educational and auditing purposes only. It is not a substitute for professional clinical advice or judgment.]\n\nClinical response content."
        else:
            return "[Disclaimer: This assistant is for educational purposes only. It is not a substitute for professional medical advice, diagnosis, or treatment. Always consult your doctor for medical concerns.]\n\nLayperson response content."
            
    monkeypatch.setattr("backend.agents.chat_agent.call_llm", mock_call_llm)
    
    with TestClient(app) as client:
        # Test 1: Clinical Mode
        response = client.post(
            "/chat",
            json={
                "note_id": "test-note-1",
                "messages": [{"role": "user", "content": "What is the diagnosis?"}],
                "mode": "clinical"
            }
        )
        assert response.status_code == 200
        payload = response.json()
        assert "Clinical response content." in payload["response"]
        assert "Disclaimer" in payload["response"]

        # Test 2: Layperson Mode
        response = client.post(
            "/chat",
            json={
                "note_id": "test-note-1",
                "messages": [{"role": "user", "content": "Explain in simple terms."}],
                "mode": "layperson"
            }
        )
        assert response.status_code == 200
        payload = response.json()
        assert "Layperson response content." in payload["response"]
        assert "Disclaimer" in payload["response"]


def test_explain_endpoint(monkeypatch):
    monkeypatch.setattr(
        "backend.main.get_report",
        lambda note_id: {
            "note_id": note_id,
            "timeline": {"sections": []},
            "contradiction_flags": [],
            "differentials": [],
            "confidence_scores": []
        }
    )
    
    # Mock LLM completions response for explainer
    monkeypatch.setattr(
        "backend.agents.plain_lang_translator.call_llm",
        lambda messages: "[Disclaimer: This assistant is for educational purposes only. It is not a substitute for professional medical advice, diagnosis, or treatment. Always consult your doctor for medical concerns.]\n\nExplanation text."
    )
    
    with TestClient(app) as client:
        response = client.post("/explain/test-note-1")
        assert response.status_code == 200
        payload = response.json()
        assert "Explanation text." in payload["explanation"]
        assert "Disclaimer" in payload["explanation"]
