from pydantic import BaseModel


class PreprocessBody(BaseModel):
    path: str
    document_id: str


class GenerateMCQBody(BaseModel):
    key_point_id: int
