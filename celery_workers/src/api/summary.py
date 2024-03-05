# Depricated



# import json
# import logging
# from re import sub
# from openai import OpenAI
# from supabase import Client
# from celery_workers.src.config.supabase_client import get_supabase_client

# # user_id: str,
# # supabase_client: Client,


# def create_key_points_json(
#     text: list[str],
#     subtext=None,
#     num_of_questions=10,
# ):
#     # this openai function takes in a string and outputs a summary gpt-4-1106-preview
#     try:
#         # summary = (
#         #     supabase_client.table("documents")
#         #     .select("summary")
#         #     .eq("id", document_id)
#         #     .execute()
#         # )
#         # if summary.data[0].get("summary") is not None:
#         #     logging.info("Summary already exists!")
#         # else:
#         logging.info("Attempting to generate key points on context " + subtext)
#         client = OpenAI()
#         response = client.chat.completions.create(
#             model="gpt-3.5-turbo-1106",
#             response_format={"type": "json_object"},
#             messages=[
#                 {
#                     "role": "system",
#                     "content": f"""You are to find key points at a user given text. 
#                             The text are from lecture materials. refrain from including personal
#                             information or any other information that is not related to
#                             the subject as key points. key points should be simple and short.
#                             {f"These are some user given specific instructions {subtext}" if subtext is not None else ""}
#                             Generate only the best {num_of_questions} key points.
#                             Return a JSON. The JSON should only have an 
#                             array with only label called "key_points" """,
#                 },
#                 {"role": "user", "content": f"{text}. " ""},
#             ],
#         )
#         # supabase_client.table("documents").upsert(
#         #         {
#         #             "summary": json.loads(response.choices[0].message.content),
#         #             "id": document_id,
#         #             "user_id": user_id,
#         #         }
#         #     ).execute()
#         logging.info(f"Key points generated successfully!")
#         return response.choices[0].message.content
#     except Exception as e:
#         logging.error(str(e))


# def create_context_summary(key_point_id: str, access_token: str, refresh_token: str):
#     try:
#         supabase: Client = get_supabase_client(access_token, refresh_token)
#         response = (
#             supabase.table("key_points")
#             .select("context", "key_point", "summary")
#             .eq("id", key_point_id)
#             .execute()
#         )
#         summary = response.data[0].get("summary")
#         context = response.data[0].get("context")
#         logging.info("Context extracted successfully!")
#         key_point = response.data[0].get("key_point")
#         if summary is None:
#             client = OpenAI()
#             response = client.chat.completions.create(
#                 model="gpt-3.5-turbo-1106",
#                 response_format={"type": "json_object"},
#                 messages=[
#                     {
#                         "role": "system",
#                         "content": f"""Create a concise, educational short note 
#                                                                      on the following topic: {key_point} The note
#                                                                       should be standalone, focusing solely on key
#                                                                        educational content relevant to the topic. It 
#                                                                        should be structured to clearly present the 
#                                                                        essential concepts, definitions, or principles 
#                                                                        related to the topic in a manner that is easy to
#                                                                         understand. The note should be brief yet 
#                                                                         informative, ideally fitting into a single 
#                                                                         paragraph, and should avoid any contextual or 
#                                                                         unrelated information. Return a JSON. The JSON 
#                                                                         should only have a label called "summary" """,
#                     },
#                     {"role": "user", "content": f"{context}. "},
#                 ],
#             )
#             summary = json.loads(response.choices[0].message.content).get("summary")
#             supabase.table("key_points").update(
#                 {
#                     "summary": summary,
#                 }
#             ).eq("id", key_point_id).execute()
#             logging.info("Summary added successfully!")
#             logging.info("Summary generated successfully!")
#         else:
#             logging.info("Summary already exists!")
#     except Exception as e:
#         logging.error(str(e))
