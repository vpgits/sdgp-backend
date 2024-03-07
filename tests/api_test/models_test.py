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

def test_mcq():
    data = {
        "question": "Test Question",
        "correct_answer": "Test Correct Answer",
        "incorrect_answers": ["Test Incorrect Answer 1", "Test Incorrect Answer 2"]
    }
    mcq = Mcq(**data)
    assert mcq.question == data["question"]
    assert mcq.correct_answer == data["correct_answer"]
    assert mcq.incorrect_answers == data["incorrect_answers"]

def test_key_points():
    data = {"key_points": ["Test Key Point 1", "Test Key Point 2"]}
    key_points = KeyPoints(**data)
    assert key_points.key_points == data["key_points"]

def test_document_summary_missing_field():
    data = {"title": "Test Title"}
    with pytest.raises(ValueError):
        DocumentSummary(**data)