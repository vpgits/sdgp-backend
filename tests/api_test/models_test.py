import pytest
from celery_workers.src.api.models import DocumentSummary, QuizSummary, Mcq, KeyPoints

def test_document_summary():
    data = {"title": "Test Title", "summary": "Test Summary"}
    document = DocumentSummary(**data)
    assert document.title == data["title"]
    assert document.summary == data["summary"]

def test_quiz_summary():
    data = {"title": "Test Title", "summary": "Test Summary"}
    quiz = QuizSummary(**data)
    assert quiz.title == data["title"]
    assert quiz.summary == data["summary"]

def test_key_points():
    data = {"key_points": ["Test Key Point 1", "Test Key Point 2"]}
    key_points = KeyPoints(**data)
    assert key_points.key_points == data["key_points"]

def test_document_summary_missing_field():
    data = {"title": "Test Title"}
    with pytest.raises(ValueError):
        DocumentSummary(**data)