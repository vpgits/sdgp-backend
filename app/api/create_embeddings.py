import asyncio
import logging
import os

import aiohttp
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def sentence_embedding(sentence, document_id=9999):
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


async def sentence_embeddings(sentences, document_id=9999):
    logger.info(f"Attempting to add {len(sentences)}, on document id {document_id} sentences to the database")
    # this function will take a batch of sentences and create embeddings
    try:
        responses = await asyncio.gather(
            *(sentence_embedding(sentence, document_id) for sentence in sentences[:1]))
        if all(response.get("message") == "Embedding added successfully!" for response in responses):
            logger.info("All embeddings added successfully!")
            return True
        else:
            logger.warning("Some Embeddings are not added successfully!")
            for response in responses:
                if response.get("message") != "Embedding added successfully!":
                    logger.info(f"{response.get('message')})")
            return False
    except Exception as e:
        print(str(e))
        logger.error(f"Anc exception has occurred: {str(e)}")
        return False
