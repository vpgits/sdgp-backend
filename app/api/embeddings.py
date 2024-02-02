import logging
import os
from dotenv import load_dotenv
import torch.nn.functional as F
from torch import Tensor
from transformers import AutoTokenizer, AutoModel
from pinecone import Pinecone
from pinecone.exceptions import NotFoundException
from app.api.parse import sliding_window

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_embedding_query(sentence: str):
    return generate_embeddings([sentence])[0]


def create_vector_index(pages: list[str], document_id: str):
    if do_embeddings_exist(document_id):
        logger.info("Embeddings already exist!")
        delete_embeddings_index(document_id)
    try:
        chunks = sliding_window(pages)
        logger.info("Generating embeddings")
        embeddings = generate_embeddings(chunks)
        logger.info(f"{len(chunks)} Embeddings generated")
        logger.info("Adding embeddings to Pinecone")
        embeddings_list = [{f"{document_id}:{id}", embedding} for id, embedding in enumerate(embeddings)]
        add_embeddings_to_pinecone(embeddings_list, document_id)
        for index, embedding in enumerate(embeddings):
            add_embeddings_to_pinecone(embedding, f"{document_id}:{index}", document_id)
    except Exception as e:
        logger.error(f"Anc exception has occurred in create vector index: {str(e)}")
        raise e


def do_embeddings_exist(document_id: str):
    try:
        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        index = pc.Index(name=os.getenv("PINECONE_INDEX_NAME"))
        return document_id in index.describe_index_stats()["namespaces"]
    except Exception as e:
        logger.error(f"An exception has occurred in do embeddings exist: {str(e)}")
        raise e


def delete_embeddings_index(document_id: str):
    try:
        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        index = pc.Index(name=os.getenv("PINECONE_INDEX_NAME"))
        index.delete(delete_all=True, namespace=document_id)
    except Exception as e:
        logger.error(f"An exception has occurred in delete embeddings index: {str(e)}")
        raise e


def generate_embeddings(input_texts: list[str]) -> [list[float]]:
    try:
        logging.info("Generating embeddings on geneerate_embeddings")
        tokenizer = AutoTokenizer.from_pretrained("./app/api/gte-small/")
        model = AutoModel.from_pretrained("./app/api/gte-small/")
        batch_dict = tokenizer(
            input_texts,
            max_length=512,
            padding=True,
            truncation=True,
            return_tensors="pt",
        )
        outputs = model(**batch_dict)
        embeddings = average_pool(
            outputs.last_hidden_state, batch_dict["attention_mask"]
        )
        embeddings = F.normalize(embeddings, p=2, dim=1)
        return embeddings.tolist()
    except Exception as e:
        logger.error(f"An exception has occurred while generating embeddings: {str(e)}")
        raise e


def average_pool(last_hidden_states: Tensor, attention_mask: Tensor) -> Tensor:
    last_hidden = last_hidden_states.masked_fill(~attention_mask[..., None].bool(), 0.0)
    return last_hidden.sum(dim=1) / attention_mask.sum(dim=1)[..., None]


def add_embeddings_to_pinecone(embeddings: list[dict], document_id: str):
    try:
        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        index = pc.Index(name=os.getenv("PINECONE_INDEX_NAME"))
        index.upsert(
            vectors=embeddings, namespace=document_id
        )
    except Exception as e:
        logger.error(
            f"An exception has occurred when adding embeddings to pinecone: {str(e)}"
        )
        raise e
