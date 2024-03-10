import logging


def sliding_window(pages, window_size=512, slide=378) -> list[str]:
    # this function will take a batch of sentences and create chunks for embeddings
    try:
        page_single_string = " ".join(pages)
        window = []
        for i in range(0, len(page_single_string), slide):
            window_chunk = page_single_string[i : i + window_size]
            window.append(window_chunk)
        return window
    except Exception as e:
        logging.error("Error while creating sliding window: " + str(e))
