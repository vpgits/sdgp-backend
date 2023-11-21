from pydantic import BaseModel


class Document(BaseModel):
    path: str


class Query(BaseModel):
    query: str


class Embeddings(BaseModel):
    document_id: int
    pages: list
