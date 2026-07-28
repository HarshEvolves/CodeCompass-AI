# services package initialization
from app.services.auth_service import register_user, authenticate_user
from app.services.extractor import extract_zip_securely, ExtractionError
from app.services.parser import parse_repository_files, ParsingError
from app.services.chunker import chunk_repository_files, ChunkingError
from app.services.embedder import index_repository_chunks, EmbeddingError
from app.services.searcher import search_repository_chunks, SearchError

__all__ = [
    "register_user",
    "authenticate_user",
    "extract_zip_securely",
    "ExtractionError",
    "parse_repository_files",
    "ParsingError",
    "chunk_repository_files",
    "ChunkingError",
    "index_repository_chunks",
    "EmbeddingError",
    "search_repository_chunks",
    "SearchError"
]


