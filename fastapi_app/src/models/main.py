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
