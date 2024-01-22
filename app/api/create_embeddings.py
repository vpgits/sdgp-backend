import asyncio
import logging
import os
import aiohttp
from dotenv import load_dotenv
import torch.nn.functional as F
from torch import Tensor
from transformers import AutoTokenizer, AutoModel
from supabase import Client
from pinecone import Pinecone
from pinecone.exceptions import NotFoundException

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_embedding_query(sentence: str):
    return generate_embeddings([sentence])[0]


def create_vector_index(chunks: list[str], document_id: str):
    if do_embeddings_exist(document_id):
        logger.info("Embeddings already exist!")
        return
    try:
        embeddings = generate_embeddings(chunks)
        logger.info("Adding embeddings to Pinecone")
        for index, embedding in enumerate(embeddings):
            add_embeddings_to_pinecone(embedding, f"{document_id}:{index}", document_id)
    except Exception as e:
        logger.error(f"Anc exception has occurred: {str(e)}")
        raise e


def do_embeddings_exist(document_id: str):
    try:
        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        index = pc.Index(name=os.getenv("PINECONE_INDEX_NAME"))
        return True
    except NotFoundException:
        return False
    except Exception as e:
        logger.error(f"An exception has occurred: {str(e)}")
        raise e


def generate_embeddings(input_texts: list[str]):
    try:
        logging.info("Generating embeddings")
        tokenizer = AutoTokenizer.from_pretrained("./app/api/gte-small/")
        model = AutoModel.from_pretrained("./app/api/gte-small/")
        batch_dict = tokenizer(input_texts, max_length=512, padding=True, truncation=True, return_tensors="pt")
        outputs = model(**batch_dict)
        embeddings = average_pool(outputs.last_hidden_state, batch_dict["attention_mask"])
        embeddings = F.normalize(embeddings, p=2, dim=1)
        logging.info("Embeddings generated successfully!")
        return embeddings.tolist()
    except Exception as e:
        logger.error(f"An exception has occurred: {str(e)}")
        raise e


def average_pool(last_hidden_states: Tensor,
                 attention_mask: Tensor) -> Tensor:
    last_hidden = last_hidden_states.masked_fill(~attention_mask[..., None].bool(), 0.0)
    return last_hidden.sum(dim=1) / attention_mask.sum(dim=1)[..., None]


def add_embeddings_to_pinecone(embedding, embedding_id: str, document_id: str):
    try:
        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        index = pc.Index(name=os.getenv("PINECONE_INDEX_NAME"))
        index.upsert(vectors=[{"id": embedding_id, "values": embedding}], namespace=document_id)
    except Exception as e:
        logger.error(f"An exception has occurred: {str(e)}")
        raise e
