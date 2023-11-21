from openai import OpenAI
import fireworks.client


async def create_summary_json(text, subtext=None):
    # this openai function takes in a string and outputs a summary
    client = OpenAI()
    response = client.chat.completions.create(model="gpt-3.5-turbo-1106",
                                              response_format={"type": "json_object"},
                                              messages=[{"role": "system",
                                                         "content": """You are to find key points at a user given text.
                                                          Return a JSON. The JSON should only have an 
                                                         array with only label called "key_points" """},
                                                        {"role": "user",
                                                         "content": f"{text}. {subtext}"""}])
    return response.choices[0].message.content

# async def create_summary_json_fireworks(text): fireworks.client.api_key = "" completion =
# fireworks.client.ChatCompletion.create( model="accounts/fireworks/models/llama-v2-70b-chat", messages=[ {"role":
# "system", "content": """You are to find key points at a user given text. Return only a JSON. The JSON should only
# have an array with only label called "key_points" Here is the schema.{ "$schema":
# "http://json-schema.org/draft-07/schema#", "type": "array", "items": { "type": "object", "properties": { "id": {
# "type": "string" }, "description": { "type": "string" } }, "required": ["id", "description"] } } """},
# {"role": "user", "content": f"{text}. Return only a JSON. I am parsing the output so no greet text"""} ],
# stream=False, n=1, max_tokens=4096, temperature=0.1, top_p=0.9, ) return completion.choices[0].message.content
