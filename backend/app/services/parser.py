"""
CodeCompass Repository Code Parsing Service
"""
import os
import logging
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from tree_sitter_language_pack import get_parser

from app.models.code_file import CodeFile

logger = logging.getLogger(__name__)

# Map extensions to tree-sitter language names
EXTENSION_TO_LANGUAGE = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".java": "java",
    ".cpp": "cpp",
    ".hpp": "cpp",
    ".cc": "cpp",
    ".cxx": "cpp",
    ".h": "cpp",
}

IGNORED_DIRS = {
    "node_modules",
    ".git",
    "dist",
    "build",
    "venv",
    "__pycache__"
}


class ParsingError(Exception):
    """Custom exception raised when repository parsing fails."""
    pass


async def parse_repository_files(db: AsyncSession, repository_id: str, workspace_dir: str) -> None:
    """
    Scans the workspace directory, filters out ignored folders, parses
    supported source files using Tree-sitter, and stores file metadata.
    """
    workspace_path = Path(workspace_dir).resolve()
    
    # 1. Verify workspace directory exists
    if not workspace_path.exists() or not workspace_path.is_dir():
        logger.error(f"Workspace directory {workspace_dir} not found for parsing.")
        raise ParsingError("Repository workspace does not exist. Extract repository first.")

    # 2. Check if the workspace directory contains any files
    all_files = []
    for root, dirs, files in os.walk(workspace_path):
        for file in files:
            all_files.append(file)
            
    if not all_files:
        logger.error(f"Workspace directory {workspace_dir} is empty.")
        raise ParsingError("Repository extraction produced no files.")

    code_files_to_create = []
    total_files_discovered = 0
    supported_files = 0
    skipped_files = 0

    logger.info(
        f"Starting parser scanner for repository: {repository_id}. "
        f"Workspace target: {workspace_dir}."
    )

    try:
        # Walk recursively through the workspace
        for root, dirs, files in os.walk(workspace_path):
            # Prune ignored directories in-place to avoid descending into them
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]

            for file in files:
                total_files_discovered += 1
                file_path = Path(root) / file
                ext = file_path.suffix.lower()

                if ext in EXTENSION_TO_LANGUAGE:
                    lang = EXTENSION_TO_LANGUAGE[ext]

                    try:
                        # Get relative path from workspace root
                        relative_path = str(file_path.relative_to(workspace_path))

                        # Read content safely, ignoring decode errors
                        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()

                        # File stats
                        file_size = file_path.stat().st_size
                        total_lines = len(content.splitlines())

                        # Parse using tree-sitter to verify the file is parse-able
                        parser = get_parser(lang)
                        parser.parse(bytes(content, "utf8"))

                        # Build the DB model instance
                        code_file = CodeFile(
                            repository_id=repository_id,
                            relative_path=relative_path,
                            language=lang,
                            file_size=file_size,
                            total_lines=total_lines
                        )
                        code_files_to_create.append(code_file)
                        supported_files += 1
                        logger.info(f"Parsed file successfully: {relative_path} ({lang})")

                    except Exception as fe:
                        logger.exception(f"Failed to parse individual file {file_path}")
                        skipped_files += 1
                        # Continue to parse other files even if one fails
                else:
                    skipped_files += 1

        logger.info(
            f"Scanner completed for repository: {repository_id}. "
            f"Total files discovered: {total_files_discovered}. "
            f"Supported files parsed: {supported_files}. "
            f"Skipped/unsupported files: {skipped_files}."
        )

        if not code_files_to_create:
            logger.error(f"No supported source code files found in workspace: {workspace_dir}")
            raise ParsingError("No supported source code files found in the repository.")

        # Batch insert all parsed code files
        db.add_all(code_files_to_create)
        await db.flush()
        logger.info(f"Inserted {len(code_files_to_create)} code file records for repo {repository_id}")

    except Exception as e:
        if not isinstance(e, ParsingError):
            logger.error(f"Unexpected error during repository parsing {repository_id}: {str(e)}")
            raise ParsingError(f"Repository parsing failed: {str(e)}")
        raise e
