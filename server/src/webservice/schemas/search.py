from pydantic import BaseModel

# Search-related Pydantic models

class TitleRequest(BaseModel):
    content: str
    user_query: str | None = None

class TitleResponse(BaseModel):
    title: str

class FTSResponse(BaseModel):
    chunks: list[dict]  # List of FTS chunks
    total: int  # Total number of chunks

class ConciseRequest(BaseModel):
    content: str

class ConciseResponse(BaseModel):
    concise: str

class ChunkContentResponse(BaseModel):
    content: str

class ExcerptResponse(BaseModel):
    excerpt: list[dict]  # List of excerpt chunks

class CategoriesResponse(BaseModel):
    categories: list[str]  # List of suggested categories 