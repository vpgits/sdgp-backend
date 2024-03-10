import pytest
from celery_workers.src.api.utils import sliding_window

def test_sliding_window():
    pages = ["This is a test sentence.", "This is another test sentence."]
    window_size = 10
    slide = 5

    result = sliding_window(pages, window_size, slide)

    # Check if the function returns the correct number of chunks
    assert len(result) == 11

    # Check if each chunk has the correct size
    for chunk in result:
        assert len(chunk) <= window_size

test_sliding_window()