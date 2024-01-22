import logging
import re
from io import BytesIO
from PyPDF2 import PdfReader
import os
from supabase import Client


def parse_pdf_pages(path: str, supabase_client: Client, document_id: str) -> None:
    # this function will parse an entire pdf into an array of pages
    try:
        download_file(supabase_client, path)  # this function will download a file from supabase storage
        pages = read_pdf(path)  # Parse the PDF file and return a list of text from each page
        add_pages_to_supabase(supabase_client, pages, document_id)  # this function will add the pages to supabase
    except FileNotFoundError:
        logging.error("File not found")
    except Exception as e:
        logging.error(str(e))
        raise e


def does_pages_exist(supabase: Client, document_id: str) -> bool:
    try:
        data = supabase.from_("documents").select("data").eq("id", document_id).execute()
        logging.info(data.data[0])
        if not data.data[0]:
            return False
        else:
            return True
    except Exception as e:
        logging.error(str(e))
        raise e


def get_pages(supabase: Client, document_id: str) -> str:
    logging.info(document_id)
    data = supabase.from_("documents").select("data").eq("id", document_id).execute()
    pages = data.data[0].get("data").get("data")[0]
    logging.info("Pages retrieved successfully!")
    return pages


def read_pdf(path: str) -> list[str]:
    # Parse the PDF file and return a list of text from each page
    pages = []
    try:
        with open(f"./resources/{path}", "rb") as file:
            reader = PdfReader(BytesIO(file.read()))
            for page in reader.pages:
                cleaned_page = (re.sub(r"\s+", " ", page.extract_text()))
                pages.append(cleaned_page)
        return pages
    except FileNotFoundError as e:
        logging.error(f"File not found: {e}")
        raise
    except Exception as e:
        logging.error(f"Error parsing PDF: {str(e)}")
        raise


def add_pages_to_supabase(supabase_client: Client, pages: list[str], document_id: str) -> None:
    pages = sliding_window(pages)
    supabase_client.table("documents").update({"data": {"data": pages}}).eq(
        "id", document_id
    ).execute()
    logging.info("Pages added successfully!")


def download_file(supabase_client: Client, path: str) -> None:
    # this function will download a file from supabase storage
    file_path = f"./resources/{path}"
    res = supabase_client.storage.from_("public/pdf").download(path)
    try:
        # if the ./resources folder does not exist, create it
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "wb+") as f:
            f.write(res)
    except Exception as e:
        logging.error("Error Downloading pdf: " + str(e))
        raise e


def sliding_window(pages, window_size=512, slide=378) -> list[str]:
    # this function will take a batch of sentences and create chunks for embeddings
    try:
        window = []
        for i in range(0, len(pages), slide):
            window.append(str(pages[i: i + window_size]))
        return window
    except Exception as e:
        logging.error("Error while creating sliding window: " + str(e))
