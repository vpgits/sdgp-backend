from typing import List
from pydantic import BaseModel, Field


class DocumentSummary(BaseModel):
    title: str = Field(..., description="Title of the user text")
    summary: str = Field(..., description="Summary of the user text")


class QuizSummary(BaseModel):
    title: str = Field(..., description="Title of the user text")
    summary: str = Field(..., description="Summary of the user text")


class Mcq(BaseModel):
    question: str = Field(description="Question of the user question")
    correctAnswer: str = Field(description="Correct answer of the user question")
    incorrectAnswers: List[str] = Field(
        description="Incorrect answers of the user question"
    )


class KeyPoints(BaseModel):
    key_points: list[str] = Field(..., description="Key points of the user text")
