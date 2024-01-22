from pydantic import BaseModel


class Document(BaseModel):
    path: str
    user_id: str
    document_id: int


class Query(BaseModel):
    query: str


class Embeddings(BaseModel):
    document_id: int
    pages: list


class Mcq(BaseModel):
    document_id: int
    key_point_id: int
