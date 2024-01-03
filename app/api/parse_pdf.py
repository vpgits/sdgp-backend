import re
from io import BytesIO
from PyPDF2 import PdfReader
from app.api.database import download_file


def parse_pdf_pages(path):
    # this function will parse an entire pdf into an array of pages
    try:
        download_file(path)
        with open(f'./resources/{path}', 'rb') as f:
            response = f.read()
        reader = PdfReader(BytesIO(response))
        pages = []
        for page in reader.pages:
            cleaned_page = re.sub(r"\s+", " ", page.extract_text())
            pages.append(cleaned_page)
        return {"pages": pages}
    except FileNotFoundError:
        # File not found error
        print("File not found")
    except Exception as e:
        # Other exceptions
        print(str(e))


def parse_pdf_sentences(pages):
    try:
        sentences = []
        for page in pages:
            sentences.extend(re.split(r'(?<=[^A-Z].[.?]) +(?=[A-Z])', page))
        return sentences
    except Exception as e:
        print(str(e))


def sliding_window(pages, window_size=512, slide=378):
    # this function will take a batch of sentences and create embeddings
    try:
        text = " ".join(pages)
        window = []
        for i in range(0, len(text), slide):
            window.append(text[i:i + window_size])
        return window
    except Exception as e:
        print(str(e))
