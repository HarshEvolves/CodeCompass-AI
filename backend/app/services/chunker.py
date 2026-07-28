"""
CodeCompass Code Chunking Service
"""
import os
import uuid
import logging
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from tree_sitter_languages import get_parser

from app.models.code_file import CodeFile
from app.models.code_chunk import CodeChunk

logger = logging.getLogger(__name__)


class ChunkingError(Exception):
    """Custom exception raised when repository chunking fails."""
    pass


def estimate_tokens(text: str) -> int:
    """Estimates the token count of a given text block."""
    return max(1, len(text) // 4)


def split_sliding_window(lines: list[str], start_offset: int, window_size: int = 50, overlap: int = 10) -> list[dict]:
    """Splits a list of lines into overlapping chunks of a fixed line count."""
    chunks = []
    total = len(lines)
    step = window_size - overlap
    if step <= 0:
        step = window_size

    i = 0
    while i < total:
        end = min(i + window_size, total)
        chunk_lines = lines[i:end]
        chunk_text = "\n".join(chunk_lines)
        chunks.append({
            "content": chunk_text,
            "start_line": start_offset + i,
            "end_line": start_offset + end - 1
        })
        if end == total:
            break
        i += step
    return chunks


def chunk_file_content(content: str, language: str) -> list[dict]:
    """
    Chunks file content using a hybrid approach:
    1. Parse with Tree-sitter and locate functions, classes, and methods.
    2. Fallback to sliding window for segments over the limit (50 lines) or remaining lines.
    """
    chunks = []
    lines = content.splitlines()
    total_lines = len(lines)

    if not lines:
        return []

    try:
        parser = get_parser(language)
        tree = parser.parse(bytes(content, "utf8"))
        root_node = tree.root_node

        semantic_nodes = []

        def traverse(node):
            node_type = node.type
            is_boundary = False
            if language == "python" and node_type in ("function_definition", "class_definition"):
                is_boundary = True
            elif language in ("javascript", "typescript") and node_type in ("function_declaration", "class_declaration", "method_definition"):
                is_boundary = True
            elif language == "java" and node_type in ("class_declaration", "method_declaration"):
                is_boundary = True
            elif language == "cpp" and node_type in ("function_definition", "class_specifier", "struct_specifier"):
                is_boundary = True

            if is_boundary:
                semantic_nodes.append(node)
            for child in node.children:
                traverse(child)

        traverse(root_node)

        # Sort semantic nodes by start line
        semantic_nodes.sort(key=lambda n: n.start_point[0])

        covered_lines = set()

        for node in semantic_nodes:
            start_line = node.start_point[0] + 1
            end_line = node.end_point[0] + 1

            # Get lines corresponding to this node
            node_lines = lines[start_line - 1 : end_line]
            node_text = "\n".join(node_lines)

            # If node is too large, split using sliding window
            if len(node_lines) > 60:
                sub_chunks = split_sliding_window(node_lines, start_line, window_size=50, overlap=10)
                chunks.extend(sub_chunks)
            else:
                chunks.append({
                    "content": node_text,
                    "start_line": start_line,
                    "end_line": end_line
                })

            for line_num in range(start_line, end_line + 1):
                covered_lines.add(line_num)

        # Process remaining (uncovered) lines
        uncovered_ranges = []
        start_uncovered = None
        for line_num in range(1, total_lines + 1):
            if line_num not in covered_lines:
                if start_uncovered is None:
                    start_uncovered = line_num
            else:
                if start_uncovered is not None:
                    uncovered_ranges.append((start_uncovered, line_num - 1))
                    start_uncovered = None
        if start_uncovered is not None:
            uncovered_ranges.append((start_uncovered, total_lines))

        for start, end in uncovered_ranges:
            range_lines = lines[start - 1 : end]
            sub_chunks = split_sliding_window(range_lines, start, window_size=50, overlap=10)
            chunks.extend(sub_chunks)

    except Exception as e:
        logger.warning(f"Failed to use tree-sitter chunking, falling back to sliding window. Error: {str(e)}")
        chunks = split_sliding_window(lines, 1, window_size=50, overlap=10)

    # Final fallback if no chunks were generated (e.g. Empty list)
    if not chunks and lines:
        chunks = split_sliding_window(lines, 1, window_size=50, overlap=10)

    # Sort final chunks by start_line
    chunks.sort(key=lambda x: x["start_line"])
    return chunks


async def chunk_repository_files(db: AsyncSession, repository_id: uuid.UUID, workspace_dir: str) -> None:
    """
    Loads all parsed files for a repository, generates chunks, and stores them in DB.
    """
    workspace_path = Path(workspace_dir).resolve()

    # 1. Load all CodeFile records
    query = select(CodeFile).where(CodeFile.repository_id == repository_id)
    result = await db.execute(query)
    code_files = result.scalars().all()

    if not code_files:
        raise ChunkingError("No parsed files found for this repository.")

    chunks_to_create = []

    try:
        for code_file in code_files:
            file_path = workspace_path / code_file.relative_path
            if not file_path.exists():
                logger.warning(f"File not found in workspace: {file_path}")
                continue

            try:
                # Read content
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                # Generate raw chunks
                raw_chunks = chunk_file_content(content, code_file.language)

                for index, rc in enumerate(raw_chunks):
                    # Filter out purely whitespace chunks
                    if not rc["content"].strip():
                        continue

                    # Create db model instance
                    chunk = CodeChunk(
                        code_file_id=code_file.id,
                        chunk_index=index,
                        content=rc["content"],
                        start_line=rc["start_line"],
                        end_line=rc["end_line"],
                        token_count=estimate_tokens(rc["content"])
                    )
                    chunks_to_create.append(chunk)

            except Exception as fe:
                logger.error(f"Failed to chunk file {code_file.relative_path}: {str(fe)}")
                # Continue with other files

        if not chunks_to_create:
            raise ChunkingError("No non-empty chunks could be generated for the repository.")

        # Bulk save
        db.add_all(chunks_to_create)
        await db.flush()
        logger.info(f"Successfully generated {len(chunks_to_create)} chunks for repository {repository_id}")

    except Exception as e:
        if not isinstance(e, ChunkingError):
            logger.error(f"Unexpected error during chunking for repository {repository_id}: {str(e)}")
            raise ChunkingError(f"Chunking failed: {str(e)}")
        raise e
