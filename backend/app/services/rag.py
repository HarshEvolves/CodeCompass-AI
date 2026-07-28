"""
CodeCompass RAG AI Service
"""
import logging
import httpx
from typing import List, Dict, Any
from app.services.searcher import search_repository_chunks
from app.core.config import settings

logger = logging.getLogger(__name__)


class RAGError(Exception):
    """Custom exception raised when RAG generation fails."""
    pass


def build_rag_prompt(query: str, chunks: List[Dict[str, Any]]) -> str:
    """
    Constructs the prompt containing only the retrieved code snippets
    and instructions to strictly restrict answers to the context.
    """
    context_str = ""
    for idx, chunk in enumerate(chunks):
        context_str += f"--- FILE: {chunk['relative_path']} (Lines: {chunk['start_line']}-{chunk['end_line']}) ---\n"
        context_str += f"{chunk['code_content']}\n\n"

    prompt = f"""You are an expert AI code assistant for the repository.
Answer the user's question using ONLY the provided repository context below.
Strictly adhere to the following rules:
1. Do NOT use your own external knowledge to answer if the information is not explicitly present in the provided context.
2. If the context is insufficient or does not contain the answer to the question, you must respond EXACTLY with: "I couldn't find that information in the uploaded repository."
3. Do NOT make up facts, guess, or extrapolate.
4. Keep your answer technical, concise, and accurate to the provided code snippets.

Retrieved Repository Context:
{context_str}

User Question: {query}

Answer:"""
    return prompt


async def generate_rag_answer(
    repository_id: Any,
    query: str,
    top_k: int = 5
) -> Dict[str, Any]:
    """
    Executes the full RAG pipeline:
    1. Retrieves top-K code chunks for the query from ChromaDB.
    2. Constructs a context-isolated prompt.
    3. Calls the configured LLM API (Gemini or OpenAI).
    4. Formulates response containing the answer, retrieved files, code snippets, and citations.
    """
    # Check for API Keys
    gemini_key = getattr(settings, "GEMINI_API_KEY", None)
    openai_key = getattr(settings, "OPENAI_API_KEY", None)

    if not gemini_key and not openai_key:
        raise RAGError("API key configuration missing. Please set GEMINI_API_KEY or OPENAI_API_KEY in your environment.")

    # 1. Retrieve relevant code chunks
    try:
        chunks = await search_repository_chunks(repository_id, query, top_k=top_k)
    except Exception as e:
        logger.error(f"Search retrieval step in RAG failed: {str(e)}")
        raise RAGError(f"Retrieval failed: {str(e)}")

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
            if gemini_key:
                # Call Gemini API
                model_name = getattr(settings, "GEMINI_MODEL", "gemini-1.5-flash")
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={gemini_key}"
                payload = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"temperature": 0.0}
                }
                logger.info(f"Calling Gemini API ({model_name}) for RAG...")
                res = await client.post(url, json=payload, timeout=60.0)
                if res.status_code != 200:
                    logger.error(f"Gemini API returned error code {res.status_code}: {res.text}")
                    raise RAGError(f"Gemini API error: {res.text}")
                
                res_data = res.json()
                answer = res_data["candidates"][0]["content"]["parts"][0]["text"].strip()

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
                    "temperature": 0.0
                }
                logger.info(f"Calling OpenAI API ({model_name}) for RAG...")
                res = await client.post(url, json=payload, headers=headers, timeout=60.0)
                if res.status_code != 200:
                    logger.error(f"OpenAI API returned error code {res.status_code}: {res.text}")
                    raise RAGError(f"OpenAI API error: {res.text}")
                
                res_data = res.json()
                answer = res_data["choices"][0]["message"]["content"].strip()

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
