import pytest

import numpy as np

from celery_workers.src.api.embeddings import generate_embedding_query


def test_generate_embedding_query():
    """
    Tests the generate_embedding_query function from embeddings.py The parent function is a wrapper around the ML pipeline that outputs an embedding list of shape n, 384
    """
    result: np.array = np.array(generate_embedding_query("test"))
    print(f"Source text: test\nEmbedding: {result}")
    assert result.shape == (1, 384)  # asserts the embedding dimensions are accurate
