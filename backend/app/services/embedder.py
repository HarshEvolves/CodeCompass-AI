"""
CodeCompass Embedding Generation Service

Generates vector embeddings for code chunks using Sentence Transformers
and stores them in ChromaDB for persistent vector storage.
"""
import asyncio
import uuid
import logging
from sentence_transformers import SentenceTransformer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.code_chunk import CodeChunk
from app.models.code_file import CodeFile

logger = logging.getLogger(__name__)


class EmbeddingError(Exception):
    """Custom exception raised when embedding generation fails."""
    pass


# ── Singleton instances (loaded once at import time) ──
_embedding_model: SentenceTransformer | None = None
_chroma_client = None
_chroma_collection = None


def get_embedding_model() -> SentenceTransformer:
    """
    Returns the singleton SentenceTransformer model instance.
    Loads the model only once on first call to avoid repeated downloads.
    """
    global _embedding_model
    if _embedding_model is None:
        from app.core.config import settings
        logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL}")
        _embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)
        logger.info("Embedding model loaded successfully.")
    return _embedding_model


def get_chroma_collection():
    """
    Returns the singleton ChromaDB collection instance.
    Creates a persistent ChromaDB client and collection on first call.
    """
    global _chroma_client, _chroma_collection
    if _chroma_collection is None:
        import chromadb
        from app.core.config import settings
        logger.info(f"Initializing ChromaDB at: {settings.CHROMA_PERSIST_DIR}")
        _chroma_client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
        # Get or create the main code embeddings collection
        _chroma_collection = _chroma_client.get_or_create_collection(
            name="code_embeddings",
            metadata={"description": "Code chunk embeddings for semantic search"}
        )
        logger.info("ChromaDB collection 'code_embeddings' ready.")
    return _chroma_collection


async def index_repository_chunks(
    db: AsyncSession,
    repository_id: uuid.UUID
) -> int:
    """
    Generates embeddings for all code chunks of a repository and stores them
    in ChromaDB. Returns the number of chunks indexed.

    Args:
        db: Async database session.
        repository_id: UUID of the repository to index.

    Returns:
        Number of chunks successfully indexed.

    Raises:
        EmbeddingError: If no chunks are found or indexing fails.
    """
    # 1. Load all code chunks with their parent CodeFile metadata
    query = (
        select(CodeChunk, CodeFile)
        .join(CodeFile, CodeChunk.code_file_id == CodeFile.id)
        .where(CodeFile.repository_id == repository_id)
        .order_by(CodeChunk.code_file_id, CodeChunk.chunk_index)
    )
    result = await db.execute(query)
    rows = result.all()

    if not rows:
        raise EmbeddingError("No code chunks found for this repository.")

    logger.info(f"Found {len(rows)} chunks to index for repository {repository_id}")

    # 2. Get singleton model and collection
    model = get_embedding_model()
    collection = get_chroma_collection()

    # 3. Remove any existing embeddings for this repository to avoid duplicates
    repo_id_str = str(repository_id)
    try:
        existing = collection.get(
            where={"repository_id": repo_id_str}
        )
        if existing and existing["ids"]:
            logger.info(
                f"Removing {len(existing['ids'])} existing embeddings for repository {repository_id}"
            )
            collection.delete(ids=existing["ids"])
    except Exception as e:
        logger.warning(f"Could not check/remove existing embeddings: {str(e)}")

    # 4. Prepare batch data for ChromaDB
    ids = []
    documents = []
    metadatas = []

    for chunk, code_file in rows:
        chunk_id_str = str(chunk.id)
        ids.append(chunk_id_str)
        documents.append(chunk.content)
        metadatas.append({
            "chunk_id": chunk_id_str,
            "repository_id": repo_id_str,
            "code_file_id": str(code_file.id),
            "relative_path": code_file.relative_path,
            "language": code_file.language,
            "start_line": chunk.start_line,
            "end_line": chunk.end_line,
        })

    # 5. Generate embeddings in a single batch call
    logger.info(f"Generating embeddings for {len(documents)} chunks...")
    try:
        loop = asyncio.get_running_loop()
        embeddings = (await loop.run_in_executor(
            None, lambda: model.encode(documents, show_progress_bar=False)
        )).tolist()
    except Exception as e:
        logger.error(f"Failed to generate embeddings: {str(e)}")
        raise EmbeddingError(f"Embedding generation failed: {str(e)}")

    # 6. Store embeddings in ChromaDB (batch upsert for safety)
    #    ChromaDB has a batch size limit, so we process in chunks of 500.
    batch_size = 500
    total_indexed = 0

    try:
        for i in range(0, len(ids), batch_size):
            batch_end = min(i + batch_size, len(ids))
            collection.upsert(
                ids=ids[i:batch_end],
                embeddings=embeddings[i:batch_end],
                documents=documents[i:batch_end],
                metadatas=metadatas[i:batch_end],
            )
            total_indexed += (batch_end - i)
            logger.info(f"Indexed batch {i}-{batch_end} ({total_indexed}/{len(ids)} total)")
    except Exception as e:
        logger.error(f"Failed to store embeddings in ChromaDB: {str(e)}")
        raise EmbeddingError(f"ChromaDB storage failed: {str(e)}")

    logger.info(
        f"Successfully indexed {total_indexed} chunks for repository {repository_id}"
    )
    return total_indexed
