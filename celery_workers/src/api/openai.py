from openai import OpenAI
from pydantic import BaseModel, Field
import json
import os
from dotenv import load_dotenv

load_dotenv()

FIREWORKS_API_KEY = os.getenv("FIREWORKS_API_KEY")

if not FIREWORKS_API_KEY:
    raise ValueError("FIREWORKS_API_KEY not set")


class DocumentSummary(BaseModel):
    title: str = Field(..., description="Title of the user text")
    summary: str = Field(..., description="Summary of the user text")


class QuizSummary(BaseModel):
    title: str = Field(..., description="Title of the user text")
    summary: str = Field(..., description="Summary of the user text")


def create_mcq_json(key_point="what is encapsulation", context=None):
    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-3.5-turbo-1106",  # gpt-4-1106-preview
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": "You are to generate a multiple choice question. Generate question based on the question "
                "field and answers based on thecontext field. Make sure to create appropirate question and "
                "answers which are suitable for "
                "multiple choice questions. Its a guideline. Return only an JSON of fields question,"
                "correct_answer, incorrect_answers of type array..",
            },
            {"role": "user", "content": f"question: {key_point}? context:{context}"},
        ],
    )
    return response.choices[0].message.content


def create_quiz_summary(quiz: list):
    client = OpenAI(
        base_url="https://api.fireworks.ai/inference/v1",
        api_key=FIREWORKS_API_KEY,
    )
    chat_completion = client.chat.completions.create(
        model="accounts/fireworks/models/mixtral-8x7b-instruct",
        response_format={
            "type": "json_object",
            "schema": DocumentSummary.model_json_schema(),
        },
        max_tokens=1024,
        messages=[
            {
                "role": "system",
                "content": "You are to analyze a JSON. Generate a summary based on the given JSON. The JSON contains an array of questions for a quiz.  Create a brief summary without spoling what's in the JSON."
                "Make sure to create an appropriate summary and please refrain from disclosing personal or sensitive information. Create an appropriate title for the quiz. Return only a JSON of "
                "field summary and keywords which contains the title and the summary . Reply just in one JSON. JSON schema is "
                + str(
                    {
                        "$schema": "http://json-schema.org/draft-07/schema#",
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "summary": {"type": "string"},
                        },
                        "required": ["title", "summary"],
                    },
                ),
            },
            {"role": "user", "content": "".join([json.dumps(q) for q in quiz])},
        ],
    )
    return chat_completion.choices[0].message.content


def create_document_summary(pages: list):
    client = OpenAI(
        base_url="https://api.fireworks.ai/inference/v1",
        api_key=FIREWORKS_API_KEY,
    )
    chat_completion = client.chat.completions.create(
        model="accounts/fireworks/models/mixtral-8x7b-instruct",
        response_format={
            "type": "json_object",
            "schema": DocumentSummary.model_json_schema(),
        },
        max_tokens=1024,
        messages=[
            {
                "role": "system",
                "content": "You are to analyze a document.Identify key areas where the document context is related to.Key areas have to be generic key areas and not to be extracted directly from the document. Generate a summary based on the document "
                "Make sure to create an appropriate summary and please refrain from disclosing personal or sensitive information. Return only a JSON of "
                "field summary and keywords which contains the summary and key areas respectively. Reply just in one JSON. JSON schema is "
                + str(
                    {
                        "$schema": "http://json-schema.org/draft-07/schema#",
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "summary": {"type": "string"},
                        },
                        "required": ["title", "summary"],
                    },
                ),
            },
            {"role": "user", "content": "".join(pages)},
        ],
    )
    return chat_completion.choices[0].message.content
