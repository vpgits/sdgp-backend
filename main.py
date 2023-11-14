from io import BytesIO

from PyPDF2 import PdfReader
from fastapi import FastAPI, File

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}


@app.post("/parse")
#async function which will extract a pdf file from the post request
async def parse_pdf(file: bytes = File(...)):
    try:
        reader = PdfReader(BytesIO(file))
        metadata = reader.metadata
        return {"message": f"Hello {metadata}"}
    except Exception as e:
        return {"message": f"Hello {e}"}


