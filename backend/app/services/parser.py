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
    workspace_exists = workspace_path.exists() and workspace_path.is_dir()

    # 1. Log pre-scan details
    logger.info(
        f"Parser Pre-Scan Status: "
        f"workspace_path={workspace_path}, "
        f"repository_id={repository_id}, "
        f"workspace_exists={workspace_exists}"
    )

    if not workspace_exists:
        logger.error(f"Workspace directory {workspace_dir} not found for parsing.")
        raise ParsingError("Repository workspace does not exist. Extract repository first.")

    # 2. Count files discovered in the workspace directory
    total_files_discovered = 0
    for root, dirs, files in os.walk(workspace_path):
        total_files_discovered += len(files)

    logger.info(
        f"Parser Pre-Scan Files Count: "
        f"workspace_path={workspace_path}, "
        f"repository_id={repository_id}, "
        f"total_files_discovered={total_files_discovered}"
    )

    if total_files_discovered == 0:
        logger.error(f"Workspace directory {workspace_dir} contains zero files.")
        raise ParsingError("Repository extraction produced no files.")

    code_files_to_create = []
    supported_files = 0
    skipped_files = 0
    failed_files = 0
    failed_languages = set()

    try:
        # Walk recursively through the workspace
        for root, dirs, files in os.walk(workspace_path):
            # Prune ignored directories in-place to avoid descending into them
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]

            for file in files:
                file_path = Path(root) / file
                ext = file_path.suffix.lower()

                if ext in EXTENSION_TO_LANGUAGE:
                    lang = EXTENSION_TO_LANGUAGE[ext]
                    
                    # Log language targeting
                    logger.info(f"Targeting file parsing: file_path={file_path}, language={lang}")

                    try:
                        # Get relative path from workspace root
                        relative_path = str(file_path.relative_to(workspace_path))

                        # Read content safely, ignoring decode errors
                        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()

                        # File stats
                        file_size = file_path.stat().st_size
                        total_lines = len(content.splitlines())

                        # Wrap get_parser(lang) separately and log traceback if it fails
                        try:
                            logger.info(f"Retrieving tree-sitter parser for language: {lang}")
                            parser = get_parser(lang)
                        except Exception as gpe:
                            logger.exception(f"Failed to retrieve tree-sitter get_parser for language {lang}")
                            failed_files += 1
                            failed_languages.add(lang)
                            continue

                        # Wrap parser.parse(...) separately and log traceback if it fails
                        try:
                            logger.info(f"Running parser.parse for language {lang} on file: {relative_path}")
                            parser.parse(bytes(content, "utf8"))
                        except Exception as pe:
                            logger.exception(f"Parser parse call failed for language {lang} on file: {file_path}")
                            failed_files += 1
                            failed_languages.add(lang)
                            continue

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
                        logger.exception(f"General file processing failure for path: {file_path}")
                        failed_files += 1
                        # Continue to parse other files even if one fails
                else:
                    skipped_files += 1

        # 3. Log post-scan stats
        logger.info(
            f"Scanner completed for repository: {repository_id}. "
            f"Supported files parsed: {supported_files}. "
            f"Skipped files: {skipped_files}. "
            f"Failed files: {failed_files}."
        )

        # 4. If every file fails, raise clear message indicating missing parser
        if supported_files == 0:
            if failed_files > 0:
                missing_langs = ", ".join(sorted(list(failed_languages)))
                logger.error(f"All supported files failed to parse. Missing language parsers: {missing_langs}")
                raise ParsingError(f"All supported files failed to parse. Missing or unavailable language parsers: {missing_langs}")
            else:
                logger.error(f"No supported source code files found in workspace: {workspace_dir}")
                raise ParsingError("No supported source code files found in the repository.")

        # 5. Batch insert and verify database write success
        try:
            db.add_all(code_files_to_create)
            await db.flush()
            logger.info(f"Successfully inserted {len(code_files_to_create)} CodeFile records for repo {repository_id}")
        except Exception as dbe:
            logger.exception(f"Database insertion failed for CodeFile records of repo {repository_id}")
            raise ParsingError(f"Database write failure: {str(dbe)}")

    except Exception as e:
        if not isinstance(e, ParsingError):
            logger.exception(f"Unexpected error during repository parsing {repository_id}")
            raise ParsingError(f"Repository parsing failed: {str(e)}")
        raise e
