"""
CodeCompass RAG AI Service
"""
import logging
import uuid
import httpx
from typing import List, Dict, Any
from app.services.searcher import search_repository_chunks
from app.services.embedder import get_chroma_collection
from app.core.config import settings

logger = logging.getLogger(__name__)


class RAGError(Exception):
    """Custom exception raised when RAG generation fails."""
    pass


MAX_CHUNK_CHARS = 2000
MAX_CONTEXT_CHARS = 12000


def build_rag_prompt(query: str, chunks: List[Dict[str, Any]]) -> str:
    """
    Constructs the prompt containing only the retrieved code snippets
    and instructions to strictly restrict answers to the context.

    Each chunk is truncated to MAX_CHUNK_CHARS so one large file can't
    dominate the token budget, and the combined context stops growing
    past MAX_CONTEXT_CHARS, so requests stay under LLM provider token
    limits even on repos with many large chunks.
    """
    context_str = ""
    for chunk in chunks:
        content = chunk["code_content"]
        if len(content) > MAX_CHUNK_CHARS:
            content = content[:MAX_CHUNK_CHARS] + "... (truncated)"

        entry = f"--- FILE: {chunk['relative_path']} (Lines: {chunk['start_line']}-{chunk['end_line']}) ---\n{content}\n\n"
        if len(context_str) + len(entry) > MAX_CONTEXT_CHARS:
            break
        context_str += entry

    prompt = f"""You are an expert AI code assistant helping a developer understand a repository. Answer the user's question using the provided repository context below.

Guidelines:
1. Base your answer on the provided code context. You may summarize, explain, and connect information across the provided snippets — you don't need the answer to appear verbatim, just clearly supported by what's shown.
2. Only say you don't have enough information if the context is genuinely unrelated to the question — not merely because the answer requires you to read and interpret the code rather than finding a literal match.
3. Do not invent function names, behavior, or details that aren't shown in the context. If you're inferring something (e.g. likely intent from a partial snippet), say so.
4. Keep your answer technical, concise, and grounded in the provided code.

Retrieved Repository Context:
{context_str}

User Question: {query}

Answer:"""
    return prompt


BROAD_QUERY_PHRASES = [
    "what does", "explain", "overview", "how does this work",
    "core classes", "core functions",
]

HIGH_SIGNAL_FILENAMES = {
    "readme.md", "readme.rst", "main.py", "app/main.py", "index.js", "src/index.ts",
}

MAX_TOTAL_CHUNKS = 8


def _is_broad_query(query: str) -> bool:
    """
    Heuristic for vague/whole-repo questions ("what does this do", "explain
    the core classes") that raw vector similarity tends to answer poorly,
    since there's no specific concept for the embedding to match against.
    """
    q = query.strip().lower()
    if len(q.split()) < 6:
        return True
    return any(phrase in q for phrase in BROAD_QUERY_PHRASES)


def _is_high_signal_path(relative_path: str) -> bool:
    """
    Matches a chunk's relative_path against the known high-signal filenames,
    exact or as the tail of a nested path — indexed repos are stored with
    their extracted root folder prefixed (e.g. "some-repo-main/app/main.py"),
    so a bare equality check against "app/main.py" would never match.
    """
    path = relative_path.lower()
    return any(path == name or path.endswith("/" + name) for name in HIGH_SIGNAL_FILENAMES)


def _get_high_signal_chunks(repository_id: Any) -> List[Dict[str, Any]]:
    """
    Fetches chunks belonging to well-known high-signal files (README, main
    entrypoints) for a repository directly from ChromaDB by metadata filter,
    bypassing vector similarity entirely. Used to ground broad questions
    that semantic search alone tends to miss.
    """
    try:
        collection = get_chroma_collection()
        results = collection.get(where={"repository_id": str(repository_id)})
    except Exception as e:
        logger.warning(f"High-signal file lookup failed, continuing without it: {str(e)}")
        return []

    if not results or not results.get("ids"):
        return []

    high_signal_chunks = []
    for i, raw_id in enumerate(results["ids"]):
        meta = results["metadatas"][i]
        relative_path = meta.get("relative_path", "")
        if not _is_high_signal_path(relative_path):
            continue
        try:
            chunk_id = uuid.UUID(meta.get("chunk_id", raw_id))
        except ValueError:
            chunk_id = uuid.uuid4()
        high_signal_chunks.append({
            "chunk_id": chunk_id,
            "relative_path": relative_path,
            "language": meta.get("language", ""),
            "start_line": int(meta.get("start_line", 0)),
            "end_line": int(meta.get("end_line", 0)),
            "similarity_score": 1.0,
            "code_content": results["documents"][i]
        })
    return high_signal_chunks


async def generate_rag_answer(
    repository_id: Any,
    query: str,
    top_k: int = 5
) -> Dict[str, Any]:
    """
    Executes the full RAG pipeline:
    1. Retrieves top-K code chunks for the query from ChromaDB.
    2. Constructs a context-isolated prompt.
    3. Calls the configured LLM API (Groq, Gemini, or OpenAI — tried in that order).
    4. Formulates response containing the answer, retrieved files, code snippets, and citations.
    """
    # Check for API Keys
    groq_key = getattr(settings, "GROQ_API_KEY", None)
    gemini_key = getattr(settings, "GEMINI_API_KEY", None)
    openai_key = getattr(settings, "OPENAI_API_KEY", None)

    if not groq_key and not gemini_key and not openai_key:
        raise RAGError("API key configuration missing. Please set GROQ_API_KEY, GEMINI_API_KEY, or OPENAI_API_KEY in your environment.")

    # 1. Retrieve relevant code chunks
    try:
        chunks = await search_repository_chunks(repository_id, query, top_k=top_k)
    except Exception as e:
        logger.error(f"Search retrieval step in RAG failed: {str(e)}")
        raise RAGError(f"Retrieval failed: {str(e)}")

    # Broad/vague questions often miss the most useful files under pure
    # vector similarity, so ground them with known high-signal files
    # (README, main entrypoints) if the repository has any indexed.
    if _is_broad_query(query):
        high_signal_chunks = _get_high_signal_chunks(repository_id)
        if high_signal_chunks:
            existing_ids = {c["chunk_id"] for c in chunks}
            new_high_signal = [c for c in high_signal_chunks if c["chunk_id"] not in existing_ids]
            chunks = (new_high_signal + chunks)[:MAX_TOTAL_CHUNKS]

    if not chunks:
        # If no relevant chunks are found, we return the default "insufficient" answer directly
        return {
            "answer": "I couldn't find that information in the uploaded repository.",
            "retrieved_files": [],
            "retrieved_code_snippets": [],
            "citations": []
        }

    # 2. Build files, snippets list, and citations
    retrieved_files = list(set(chunk["relative_path"] for chunk in chunks))
    retrieved_code_snippets = [chunk["code_content"] for chunk in chunks]
    citations = [
        {
            "file_path": chunk["relative_path"],
            "start_line": chunk["start_line"],
            "end_line": chunk["end_line"]
        }
        for chunk in chunks
    ]

    # 3. Construct LLM prompt
    prompt = build_rag_prompt(query, chunks)

    # 4. Invoke LLM API
    answer = ""
    async with httpx.AsyncClient() as client:
        try:
            if groq_key:
                # Call Groq API (OpenAI-compatible request/response shape)
                model_name = getattr(settings, "GROQ_MODEL", "llama-3.3-70b-versatile")
                url = "https://api.groq.com/openai/v1/chat/completions"
                headers = {
                    "Authorization": f"Bearer {groq_key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": model_name,
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.0,
                    "max_tokens": 1024
                }
                logger.info(f"Calling Groq API ({model_name}) for RAG...")
                res = await client.post(url, json=payload, headers=headers, timeout=60.0)
                if res.status_code == 429:
                    logger.error(f"Groq API rate limit hit: {res.text}")
                    raise RAGError("Groq's rate limit was hit. Please wait a few seconds and try your question again.")
                if res.status_code != 200:
                    if "reduce the length of the messages or completion" in res.text:
                        logger.error(f"Groq API context-length error despite truncation: {res.text}")
                        raise RAGError("The retrieved context was too large for this query. Try asking a more specific question.")
                    logger.error(f"Groq API returned error code {res.status_code}: {res.text}")
                    raise RAGError(f"Groq API error: {res.text}")

                res_data = res.json()
                answer = res_data["choices"][0]["message"]["content"].strip()
                logger.info(f"RAG answer generated successfully via provider=groq model={model_name}")

            elif gemini_key:
                # Call Gemini API
                model_name = getattr(settings, "GEMINI_MODEL", "gemini-1.5-flash")
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={gemini_key}"
                payload = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"temperature": 0.0}
                }
                logger.info(f"Calling Gemini API ({model_name}) for RAG...")
                res = await client.post(url, json=payload, timeout=60.0)
                if res.status_code == 429:
                    logger.error(f"Gemini API rate limit hit: {res.text}")
                    raise RAGError("Gemini's free-tier rate limit was hit. Please wait a few seconds and try your question again.")
                if res.status_code != 200:
                    logger.error(f"Gemini API returned error code {res.status_code}: {res.text}")
                    raise RAGError(f"Gemini API error: {res.text}")

                res_data = res.json()
                answer = res_data["candidates"][0]["content"]["parts"][0]["text"].strip()
                logger.info(f"RAG answer generated successfully via provider=gemini model={model_name}")

            elif openai_key:
                # Call OpenAI API
                model_name = getattr(settings, "OPENAI_MODEL", "gpt-4o-mini")
                url = "https://api.openai.com/v1/chat/completions"
                headers = {
                    "Authorization": f"Bearer {openai_key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": model_name,
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.0,
                    "max_tokens": 1024
                }
                logger.info(f"Calling OpenAI API ({model_name}) for RAG...")
                res = await client.post(url, json=payload, headers=headers, timeout=60.0)
                if res.status_code == 429:
                    logger.error(f"OpenAI API rate limit hit: {res.text}")
                    raise RAGError("OpenAI's rate limit was hit. Please wait a few seconds and try your question again.")
                if res.status_code != 200:
                    logger.error(f"OpenAI API returned error code {res.status_code}: {res.text}")
                    raise RAGError(f"OpenAI API error: {res.text}")
                
                res_data = res.json()
                answer = res_data["choices"][0]["message"]["content"].strip()
                logger.info(f"RAG answer generated successfully via provider=openai model={model_name}")

        except httpx.RequestError as exc:
            logger.error(f"HTTP request to LLM API failed: {exc}")
            raise RAGError(f"Connection to LLM API failed: {str(exc)}")
        except Exception as exc:
            if not isinstance(exc, RAGError):
                logger.error(f"Unexpected error calling LLM API: {exc}")
                raise RAGError(f"LLM API failure: {str(exc)}")
            raise exc

    return {
        "answer": answer,
        "retrieved_files": retrieved_files,
        "retrieved_code_snippets": retrieved_code_snippets,
        "citations": citations
    }
