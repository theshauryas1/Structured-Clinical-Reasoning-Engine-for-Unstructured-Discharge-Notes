from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.agents.graph import run_reasoning_pipeline
from backend.main import app
from backend.rag.retriever import retrieve_context
from scripts.evaluate import evaluate

NOTES_DIR = Path(__file__).parent / "synthetic_notes"

NOTE_EXPECTATIONS = {
    "missing_symptom_note.txt": {"missing_symptom"},
    "new_finding_note.txt": {"new_finding"},
    "status_reversal_note.txt": {"status_reversal"},
    "resolved_no_contradiction_note.txt": set(),
    "fever_missing_note.txt": {"missing_symptom"},
    "arrhythmia_new_finding_note.txt": {"new_finding"},
    "renal_status_reversal_note.txt": {"status_reversal"},
    "respiratory_new_finding_note.txt": {"new_finding"},
    "cough_missing_note.txt": {"missing_symptom"},
    "aki_new_finding_note.txt": {"new_finding"},
}


def _assert_evidence_offsets(report) -> None:
    raw_text = report.timeline.raw_text
    for contradiction in report.contradiction_flags:
        for evidence in [contradiction.admission_evidence, contradiction.discharge_evidence]:
            if evidence is None:
                continue
            assert raw_text[evidence.start:evidence.end] == evidence.text_span


@pytest.mark.parametrize("filename,expected_types", NOTE_EXPECTATIONS.items())
def test_pipeline_execution(filename, expected_types):
    note_text = (NOTES_DIR / filename).read_text()
    report = run_reasoning_pipeline(note_text, note_id=filename)

    assert report.note_id == filename
    assert report.timeline.sections
    assert report.reasoning_trace
    assert report.orchestration_trace

    found_types = {contradiction.type.value for contradiction in report.contradiction_flags}
    if expected_types:
        assert expected_types.issubset(found_types)
    else:
        assert report.contradiction_flags == []

    _assert_evidence_offsets(report)
    if report.differentials:
        assert "base_score" in report.differentials[0].ranking_features
        assert report.differentials[0].ranking_score != 0
    if report.confidence_scores:
        assert report.confidence_scores[0].model_type == "feature_calibrated"
        assert "ranking_score" in report.confidence_scores[0].features


def test_ingest_and_report_routes():
    note_text = (NOTES_DIR / "new_finding_note.txt").read_text()

    with TestClient(app) as client:
        ingest_response = client.post(
            "/ingest",
            json={"note_text": note_text, "note_id": "api-test-note"},
        )
        assert ingest_response.status_code == 200
        ingest_payload = ingest_response.json()
        assert ingest_payload["note_id"] == "api-test-note"
        assert ingest_payload["contradiction_flags"]

        fetch_response = client.get("/report/api-test-note")
        assert fetch_response.status_code == 200
        fetch_payload = fetch_response.json()
        assert fetch_payload["note_id"] == "api-test-note"
        assert fetch_payload["contradiction_flags"] == ingest_payload["contradiction_flags"]
        assert fetch_payload["display_report"]
        assert fetch_payload["pipeline_language"] == "en"


def test_ingest_route_multilingual_edge_translation(monkeypatch):
    note_text = "Patient note in Deutsch"

    monkeypatch.setattr("backend.main.detect_input_language", lambda text, lang: ("de", []))
    monkeypatch.setattr(
        "backend.main.translate",
        lambda text, src_lang, to_english=True: (
            f"EN::{text}" if to_english else f"DE::{text}"
        ),
    )
    monkeypatch.setattr(
        "backend.main.build_display_report",
        lambda payload, language: {**payload, "note_id": f"display-{language}"},
    )

    with TestClient(app) as client:
        response = client.post(
            "/ingest",
            json={
                "note_text": note_text,
                "note_id": "multi-test-note",
                "lang": "auto",
                "display_lang": "fr",
            },
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["source_language"] == "de"
        assert payload["pipeline_language"] == "en"
        assert payload["display_language"] == "fr"
        assert payload["translated_input_text"] == "EN::Patient note in Deutsch"
        assert payload["display_report"]["note_id"] == "display-fr"


def test_report_route_can_retranslate_saved_report(monkeypatch):
    monkeypatch.setattr(
        "backend.main.get_report",
        lambda note_id: {
            "note_id": note_id,
            "warnings": [],
            "timeline": {"sections": []},
            "contradiction_flags": [],
            "differentials": [],
            "confidence_scores": [],
            "reasoning_trace": [],
            "orchestration_trace": [],
            "source_language": "de",
            "pipeline_language": "en",
            "display_language": "de",
            "display_report": {"note_id": "display-de"},
            "translated_input_text": "EN::text",
        },
    )
    monkeypatch.setattr(
        "backend.main.build_display_report",
        lambda payload, language: {"note_id": payload["note_id"], "display_language": language},
    )

    with TestClient(app) as client:
        response = client.get("/report/saved-note", params={"display_lang": "es"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["display_language"] == "es"
    assert payload["display_report"]["display_language"] == "es"


def test_rag_retriever_returns_condition_context():
    results = retrieve_context("weakness aphasia facial droop infarct", top_k=2)
    assert results
    assert results[0]["condition"] == "Acute ischemic stroke"


def test_evaluation_harness_returns_metrics():
    metrics = evaluate()
    assert metrics["summary"]["num_cases"] >= 5
    assert "top1_accuracy" in metrics["summary"]
    assert "contradiction_f1" in metrics["summary"]
    assert "mrr" in metrics["summary"]
    assert "brier_score" in metrics["summary"]
