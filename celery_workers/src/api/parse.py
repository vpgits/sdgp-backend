import logging
import re
import os
import pytesseract
from io import BytesIO
from PyPDF2 import PdfReader
from supabase import Client
from docx import Document
from pptx import Presentation


def parse_pages(path: str, supabase_client: Client, document_id: str) -> None:
    # this function will parse an entire pdf into an array of pages
    try:
        download_file(
            supabase_client, path
        )  # this function will download a file from supabase storage
        pages = file_type(
            path
            ) 
         # this function will return the type of file
        add_pages_to_supabase(
            supabase_client, pages, document_id
        )  # this function will add the pages to supabase
    except FileNotFoundError:
        logging.error("File not found")
    except Exception as e:
        logging.error(str(e))
        raise e


def file_type(path: str) -> str:
    # this function will return the type of file
    try:
        if path.endswith(".pdf"):
            return "pdf"
        elif path.endswith(".docx"):
            return "docx"
        elif path.endswith(".pptx"):
            return "pptx"
        else:
            return "unsupported"
    except Exception as e:
        logging.error("Error while getting file type: " + str(e))
        raise e



def does_pages_exist(supabase: Client, document_id: str) -> bool:
    try:
        data = (
            supabase.from_("documents").select("data").eq("id", document_id).execute()
        )
        if not data.data[0].get("data"):
            return False
        else:
            return True
    except Exception as e:
        logging.error(str(e))
        raise e


def get_pages(supabase: Client, document_id: str) -> list[str]:
    data = supabase.from_("documents").select("data").eq("id", document_id).execute()
    pages = data.data[0].get("data").get("data")
    logging.info("Pages retrieved successfully!")
    return pages


def read_pdf(path: str) -> list[str]:
    # Parse the PDF file and return a list of text from each page
    pages = []
    try:
        with open(f"./resources/{path}", "rb") as file:
            reader = PdfReader(BytesIO(file.read()))
            for page in reader.pages:
                cleaned_page = re.sub(r"\s+", " ", page.extract_text())
                pages.append(cleaned_page)
        return pages
    except FileNotFoundError as e:
        logging.error(f"File not found: {e}")
        raise
    except Exception as e:
        logging.error(f"Error parsing PDF: {str(e)}")
        raise

def read_docx(path: str) -> list[str]:
    # Parse the DOCX file and return a list of text from each page
    pages = []
    try:
        doc = Document(f"./resources/{path}")
        for para in doc.paragraphs:
            pages.append(para.text)
        return pages
    except FileNotFoundError as e:
        logging.error(f"File not found: {e}")
        raise
    except Exception as e:
        logging.error(f"Error parsing DOCX: {str(e)}")
        raise

def read_pptx(path: str) -> list[str]:
    # Parse the PPTX file and return a list of text from each page
    pages = []
    try:
        prs = Presentation(f"./resources/{path}")
        for slide in prs.slides:
            for shape in slide.shapes:
                if hasattr(shape, "text"):
                    pages.append(shape.text)
        return pages
    except FileNotFoundError as e:
        logging.error(f"File not found: {e}")
        raise
    except Exception as e:
        logging.error(f"Error parsing PPTX: {str(e)}")
        raise



def add_pages_to_supabase(
    supabase_client: Client, pages: list[str], document_id: str
) -> None:
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
        page_single_string = " ".join(pages)
        window = []
        for i in range(0, len(page_single_string), slide):
            window_chunk = page_single_string[i : i + window_size]
            window.append(window_chunk)
        return window
    except Exception as e:
        logging.error("Error while creating sliding window: " + str(e))
