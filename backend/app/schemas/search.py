"""
CodeCompass Search Schema Validations
"""
import uuid
from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    """
    Validation schema for search queries.
    """
    query: str = Field(..., description="The query string to search for in code chunks.")
    top_k: int = Field(5, ge=1, le=50, description="The maximum number of chunks to return.")


class SearchResultResponse(BaseModel):
    """
    Response schema representing one matched code chunk with its metadata and similarity.
    """
    chunk_id: uuid.UUID
    relative_path: str
    language: str
    start_line: int
    end_line: int
    similarity_score: float
    code_content: str

    model_config = {
        "from_attributes": True
    }
