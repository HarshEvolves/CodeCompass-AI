"""
CodeCompass Semantic Search Service
"""
import uuid
import logging
from app.services.embedder import get_embedding_model, get_chroma_collection

logger = logging.getLogger(__name__)


class SearchError(Exception):
    """Custom exception raised when vector search fails."""
    pass


MIN_SIMILARITY_THRESHOLD = 0.35


async def search_repository_chunks(
    repository_id: uuid.UUID,
    query: str,
    top_k: int = 5
) -> list[dict]:
    """
    Generates query embedding and searches ChromaDB for matching code chunks in a repository.
    """
    try:
        model = get_embedding_model()
        collection = get_chroma_collection()
    except Exception as e:
        logger.error(f"Failed to load embedding model or database collection: {str(e)}")
        raise SearchError("Search database not initialized.")

    # 1. Generate query embedding
    logger.info(f"Generating query embedding for search query: '{query}'")
    try:
        query_embedding = model.encode(query, show_progress_bar=False).tolist()
    except Exception as e:
        logger.error(f"Failed to encode search query: {str(e)}")
        raise SearchError(f"Embedding generation failed: {str(e)}")

    # 2. Query collection with metadata filter
    repo_id_str = str(repository_id)
    logger.info(f"Querying ChromaDB for repository {repo_id_str} with top_k={top_k}")
    try:
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where={"repository_id": repo_id_str}
        )
    except Exception as e:
        logger.error(f"ChromaDB search query failed: {str(e)}")
        raise SearchError(f"Vector search failed: {str(e)}")

    # 3. Formulate search results
    search_results = []
    if not results or not results["ids"] or len(results["ids"][0]) == 0:
        logger.info(f"No results found for repository {repository_id} and query '{query}'")
        return []

    ids = results["ids"][0]
    distances = results["distances"][0]
    metadatas = results["metadatas"][0]
    documents = results["documents"][0]

    for i in range(len(ids)):
        # ChromaDB distance values are L2 distances (smaller is closer)
        # Cosine distance or standard L2 distance. We calculate similarity_score as:
        # score = 1.0 / (1.0 + distance)
        distance = distances[i]
        similarity_score = float(1.0 / (1.0 + distance))

        meta = metadatas[i]
        # Parse chunk ID to UUID format
        try:
            chunk_id_uuid = uuid.UUID(meta.get("chunk_id", ids[i]))
        except ValueError:
            chunk_id_uuid = uuid.uuid4()

        search_results.append({
            "chunk_id": chunk_id_uuid,
            "relative_path": meta.get("relative_path", ""),
            "language": meta.get("language", ""),
            "start_line": int(meta.get("start_line", 0)),
            "end_line": int(meta.get("end_line", 0)),
            "similarity_score": similarity_score,
            "code_content": documents[i]
        })

    # 4. Drop weak matches that would dilute the RAG context, but never
    # return nothing outright — a weak-but-only match beats no match.
    filtered_results = [r for r in search_results if r["similarity_score"] >= MIN_SIMILARITY_THRESHOLD]
    if not filtered_results and search_results:
        filtered_results = [max(search_results, key=lambda r: r["similarity_score"])]
    search_results = filtered_results

    logger.info(f"Successfully retrieved {len(search_results)} matching chunks for query '{query}'")
    return search_results
