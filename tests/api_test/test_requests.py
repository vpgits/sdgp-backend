import pytest
import json
from celery_workers.src.api.models import DocumentSummary, QuizSummary, Mcq, KeyPoints
import celery_workers.src.api.requests as req


def test_document_summary():
    response = req.create_document_summary(["page 1", "page 2"])
    assert DocumentSummary(**json.loads(response))


def test_quiz_summary():
    response = req.create_quiz_summary(["question 1", "question 2"])
    assert QuizSummary(**json.loads(response))


def test_mcq():
    response = req.generate_mcq_fireworks("who is the president of the united states?")
    assert Mcq(**json.loads(response))


def test_key_points():
    response = req.create_key_points(
        "who is the president of the united states?", "Donald Trump", 5
    )
    assert KeyPoints(**json.loads(response))
