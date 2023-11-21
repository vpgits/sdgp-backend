from openai import OpenAI


def create_mcq_json(key_point="what is encapsulation", context=None):
    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-3.5-turbo-1106",  # gpt-4-1106-preview
        response_format={"type": "json_object"},
        messages=[
            {"role": "system",
             "content": "You are to generate a multiple choice question. Generate question and answers based on the "
                        "reference but do not depend on it. Its a guideline. Return only an JSON of fields question, "
                        "correct_answer, incorrect_answers of type array.."},
            {"role": "user", "content": f"question: {key_point}? context:{context}"}
        ]
    )
    return response.choices[0].message.content