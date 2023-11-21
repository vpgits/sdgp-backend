import os

import aiohttp
from dotenv import load_dotenv

load_dotenv()


async def make_database_embedding(sentence, document_id=9999):
    # this function is only used to insert embedding to the database
    # remember to remove the bearer token in next deps
    headers = {
        'Authorization': f'Bearer {os.environ.get("SUPABASE_KEY")}',
        'Content-Type': 'application/json'
    }
    url = 'https://mokzgwuuykjeipsyzuwe.supabase.co/functions/v1/embed'

    data = {
        'input': sentence,
        'document_id': document_id
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data) as response:
            return await response.json()


async def generate_embedding_query(text):
    # This function will return an embedding of 384 dimensions
    headers = {
        'Authorization': f'Bearer {os.getenv("SUPABASE_KEY")}',
    }
    url = "https://mokzgwuuykjeipsyzuwe.supabase.co/functions/v1/embed_query"
    data = {'input': text}
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data) as response:
            # Ensure response is successful
            response.raise_for_status()
            return await response.json()
