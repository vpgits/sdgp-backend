import array
from openai import OpenAI
from pydantic import BaseModel, Field
import json
import os
from dotenv import load_dotenv
import requests

load_dotenv()

FIREWORKS_API_KEY = os.getenv("FIREWORKS_API_KEY")

# if not FIREWORKS_API_KEY:
#     raise ValueError("FIREWORKS_API_KEY not set")


class DocumentSummary(BaseModel):
    title: str = Field(..., description="Title of the user text")
    summary: str = Field(..., description="Summary of the user text")


class QuizSummary(BaseModel):
    title: str = Field(..., description="Title of the user text")
    summary: str = Field(..., description="Summary of the user text")


class Mcq(BaseModel):
    question: str = Field(..., description="Question of the user text")
    correct_answer: str = Field(..., description="Correct answer of the user text")
    incorrect_answers: list = Field(
        ..., description="Incorrect answers of the user text"
    )


class KeyPoints(BaseModel):
    key_points: list[str] = Field(..., description="Key points of the user text")


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
            "schema": QuizSummary.model_json_schema(),
        },
        max_tokens=1024,
        messages=[
            {
                "role": "system",
                "content": f"You are to analyze a JSON. Generate a summary based on the given JSON. The JSON contains an array of questions for a quiz.  Create a brief summary without spoling what's in the JSON."
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


def create_key_points(text: str, subtext: str, num_of_questions: int):
    client = OpenAI(
        base_url="https://api.fireworks.ai/inference/v1",
        api_key=FIREWORKS_API_KEY,
    )
    chat_completion = client.chat.completions.create(
        model="accounts/fireworks/models/mixtral-8x7b-instruct",
        response_format={
            "type": "json_object",
            "schema": KeyPoints.model_json_schema(),
        },
        max_tokens=1024,
        messages=[
            {
                "role": "system",
                "content": f"""You are to find key points at a user given text. 
                            The text are from lecture materials. refrain from including personal
                            information or any other information that is not related to
                            the subject as key points. key points should be simple and short.
                            {f"These are some user given specific instructions {subtext}" if subtext is not None else ""}
                            Generate only the best {num_of_questions} key points.
                            Return a JSON. The JSON should only have an 
                            array with only label called "key_points" """,
            },
            {"role": "user", "content": "".join(text)},
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


def generate_mcq_runpod(input_text: str):
    url = f"https://api.runpod.ai/v2/{os.getenv('RUNPOD_WORKER_ID')}/runsync"

    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + os.getenv("RUNPOD_API_KEY"),
        "charset": "utf-8",
    }

    payload = {
        "input": {
            "text": str(
                """[INST]### Instruction : Generate a multiple-choice question (MCQ) based on the core concept identified in a given text. This MCQ should include one correct answer and three incorrect but plausible answers, crafted to assess comprehension of the concept. Format your output as a JSON object following a specified schema, emphasizing the logical extraction and representation of the text's main idea through a question and answers format. This task requires understanding and distilling the essence of the input text, applying it to create an educational or evaluative MCQ relevant to the discussed concept.
Output Format Schema:
The output should be a JSON object with a specific structure, including fields for the question, the correct answer, and an array of incorrect answers, all requiring strings.
Task Objective:
Analyze the text to identify the core concept.
Formulate a question that encapsulates this concept.
Determine one correct answer and generate three plausible incorrect answers.
Adhere to the provided JSON schema for your output. Make sure not to generate escape characters.
.The output should be formatted as a json in the below format." + "{\"type\": \"object\", \"properties\": {\"Output\": {\"type\": \"object\", \"properties\": {\"question\": {\"type\": \"string\"}, \"correct_answer\": {\"type\": \"string\"}, \"incorrect_answers\": {\"type\": \"array\", \"items\": {\"type\": \"string\"}}}, \"required\": [\"question\", \"correct_answer\", \"incorrect_answers\"]}}, \"required\": [\"Output\"]}"""
                + f"### Input :{input_text}.[/INST]"
                + "### Output :"
            )
        }
    }
    try:
        response = requests.request(
            "POST", url, headers=headers, data=json.dumps(payload), timeout=30
        )
        return response.json()
    except requests.exceptions.RequestException as e:
        return None


def generate_mcq_fireworks(input_text: str):
    client = OpenAI(
        base_url="https://api.fireworks.ai/inference/v1",
        api_key=FIREWORKS_API_KEY,
    )
    chat_completion = client.chat.completions.create(
        model="accounts/fireworks/models/mixtral-8x7b-instruct",
        response_format={
            "type": "json_object",
            "schema": Mcq.model_json_schema(),
        },
        max_tokens=1024,
        messages=[
            {
                "role": "system",
                "content": """Generate a multiple-choice question (MCQ) based on the core concept identified in a given text. This MCQ should include one correct answer and three incorrect but plausible answers, crafted to assess comprehension of the concept. Format your output as a JSON object following a specified schema, emphasizing the logical extraction and representation of the text's main idea through a question and answers format. This task requires understanding and distilling the essence of the input text, applying it to create an educational or evaluative MCQ relevant to the discussed concept.
Output Format Schema:
The output should be a JSON object with a specific structure, including fields for the question, the correct answer, and an array of incorrect answers, all requiring strings.
Task Objective:
Analyze the text to identify the core concept.
Formulate a question that encapsulates this concept.
Determine one correct answer and generate three plausible incorrect answers.
Adhere to the provided JSON schema for your output. Make sure not to generate escape characters.
.The output should be formatted as a json in the below format." + "{\"type\": \"object\", \"properties\": {\"Output\": {\"type\": \"object\", \"properties\": {\"question\": {\"type\": \"string\"}, \"correct_answer\": {\"type\": \"string\"}, \"incorrect_answers\": {\"type\": \"array\", \"items\": {\"type\": \"string\"}}}, \"required\": [\"question\", \"correct_answer\", \"incorrect_answers\"]}}, \"required\": [\"Output\"]}"""
                + str(
                    {
                        "$schema": "http://json-schema.org/draft-07/schema#",
                        "type": "object",
                        "properties": {
                            "question": {"type": "string"},
                            "correct_answer": {"type": "string"},
                            "incorrect_answers": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                        },
                        "required": ["question", "correct_answer", "incorrect_answers"],
                    }
                ),
            },
            {"role": "user", "content": input_text},
        ],
    )
    return chat_completion.choices[0].message.content
