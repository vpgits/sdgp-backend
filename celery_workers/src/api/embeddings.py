import logging
import os
from dotenv import load_dotenv
from supabase import Client
import torch.nn.functional as F
from torch import Tensor
from transformers import AutoTokenizer, AutoModel
from pinecone import Pinecone
from celery_workers.src.api.utils import sliding_window
import vecs
from vecs import IndexMethod, IndexMeasure, IndexArgsHNSW


load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_embedding_query(sentence: str):
    return generate_embeddings([sentence])


def create_vector_index(pages: list[str], document_id: str, supabase: Client):
    try:
        chunks = sliding_window(pages)
        logger.info("Generating embeddings")
        embeddings = []
        chunk_size = 10
        for i in range(0, len(chunks), chunk_size):
            chunk_subset = chunks[i : i + chunk_size]
            embeddings.extend(generate_embeddings(chunk_subset))
        logger.info(f"{len(chunks)} Embeddings generated")
        logger.info("Adding embeddings to Supabase")
        vectors = list(
            (f"{document_id}:{index}", embedding)
            for index, embedding in enumerate(embeddings)
        )
        add_embeddings_to_pinecone(vectors, document_id)
        # add_embeddings_to_supabase(embeddings, document_id)
    except Exception as e:
        logger.error(f"Anc exception has occurred in create vector index: {str(e)}")
        raise e


def generate_embeddings(input_texts: list[str]) -> list[float]:
    try:
        logging.info("Generating embeddings on generate_embeddings")
        tokenizer = AutoTokenizer.from_pretrained("./celery_workers/src/api/gte-small/")
        model = AutoModel.from_pretrained("./celery_workers/src/api/gte-small/")
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
        index = pc.Index(name=os.getenv("PINECONE_INDEX_NAME"), pool_threads=30)
        async_results = [
            index.upsert(vectors=embeddings, namespace=document_id, async_req=True)
        ]
        [async_result.get() for async_result in async_results]
    except Exception as e:
        logger.error(
            f"An exception has occurred when adding embeddings to pinecone: {str(e)}"
        )
        raise e


def get_similar_embeddings(sentence: str, document_id: str, pages: list[str]):
    try:
        sentence_embedding = generate_embedding_query(sentence)[0]
        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        index = pc.Index(name=os.getenv("PINECONE_INDEX_NAME"))
        results = index.query(
            vector=sentence_embedding,
            namespace=document_id,
            top_k=3,
        )
        matches = results.get("matches")
        return extract_context(matches, pages)
    except Exception as e:
        logger.error(
            f"An exception has occurred when getting similar embeddings: {str(e)}"
        )
        raise e


def get_similar_embeddings_supabase(sentence: str, document_id: str, pages: list[str]):
    try:
        sentence_embedding = generate_embedding_query(sentence)[0]
        DB_CONNECTION = os.getenv("DB_CONNECTION")
        vx = vecs.create_client(DB_CONNECTION)
        doc = vx.get_or_create_collection(name=document_id, dimension=384)
        matches = doc.query(
            data=sentence_embedding,
            limit=3,
            measure=IndexMeasure.cosine_distance,
            include_value=False,
            include_metadata=False,
        )
        return extract_context_supabase(matches, pages)
    except Exception as e:
        logger.error(
            f"An exception has occurred when getting similar embeddings: {str(e)}"
        )
        raise e


def extract_context(matches: list[any], pages: list[str]):
    try:
        context_ids = [match.get("id").split(":")[1] for match in matches]
        chunks = sliding_window(pages)
        context = [chunks[int(context_id)] for context_id in context_ids]
        context = "".join(context)
        return context
    except Exception as e:
        logger.error(f"An exception has occurred when extracting context: {str(e)}")
        raise e


def extract_context_supabase(matches: list[any], pages: list[str]):
    try:
        context_ids = [match.split(":")[1] for match in matches]
        chunks = sliding_window(pages)
        context = [chunks[int(context_id)] for context_id in context_ids]
        context = "".join(context)
        return context
    except Exception as e:
        logger.error(f"An exception has occurred when extracting context: {str(e)}")
        raise e


def add_embeddings_to_supabase(embeddings: list[dict], document_id: str):
    try:
        DB_CONNECTION = os.getenv("DB_CONNECTION")
        vx = vecs.create_client(DB_CONNECTION)
        doc = vx.get_or_create_collection(name=document_id, dimension=384)
        data = [
            (f"{document_id}:{index}", embedding, "")
            for index, embedding in enumerate(embeddings)
        ]
        doc.upsert(records=data)
        doc.create_index(
            method=IndexMethod.hnsw,
            measure=IndexMeasure.cosine_distance,
            index_arguments=IndexArgsHNSW(m=8),
        )
    # supabase.from_("embeddings").upsert(data).execute()
    except Exception as e:
        logger.error(
            f"An exception has occurred when adding embeddings to supabase: {str(e)}"
        )
        raise e
