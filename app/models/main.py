from pydantic import BaseModel
from typing import List


class PreprocessBody(BaseModel):
    path: str
    document_id: str


class GenerateMCQBody(BaseModel):
    key_point_id: int
    question_id: str


class QuizBody(BaseModel):
    quiz_id: str


class OutputModel(BaseModel):
    question: str
    correct_answer: str
    incorrect_answers: List[str]


class MCQ(BaseModel):
    Output: OutputModel
