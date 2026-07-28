"""
CodeCompass Repository Extraction Service

Provides secure extraction of ZIP archives into the workspace directory,
guarding against Zip Slip (directory traversal) vulnerabilities.
"""
import logging
import os
import zipfile
from pathlib import Path

logger = logging.getLogger(__name__)


class ExtractionError(Exception):
    """Custom exception raised when extraction fails or validation fails."""
    pass


def extract_zip_securely(zip_path: str, destination_dir: str) -> None:
    """
    Extracts a ZIP file to destination_dir ensuring safety against Zip Slip.
    
    Args:
        zip_path: Local filesystem path to the uploaded ZIP file.
        destination_dir: Directory where the zip contents will be extracted.
        
    Raises:
        ExtractionError: If the file is invalid/corrupted or contains malicious paths.
    """
    dest_path = Path(destination_dir).resolve()
    zip_file_path = Path(zip_path).resolve()

    if not zip_file_path.exists():
        logger.error(f"ZIP file not found: {zip_path}")
        raise ExtractionError(f"ZIP file not found at: {zip_path}")

    # Ensure the destination directory exists
    dest_path.mkdir(parents=True, exist_ok=True)

    try:
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            # First pass: Validate all members to prevent path traversal
            for member in zip_ref.infolist():
                # Get the absolute, resolved path where this member would be written
                target_path = Path(os.path.abspath(dest_path / member.filename))
                
                # Check that target_path is within dest_path
                # We use resolve() to handle any symlinks or relative navigations (..)
                try:
                    target_path.resolve().relative_to(dest_path)
                except ValueError:
                    logger.error(
                        f"Zip Slip attempt detected in ZIP '{zip_path}' for member '{member.filename}'"
                    )
                    raise ExtractionError(
                        f"Directory traversal attack detected in zip archive: {member.filename}"
                    )

            # Second pass: Extract all files if safe
            for member in zip_ref.infolist():
                zip_ref.extract(member, dest_path)
                
            logger.info(f"Successfully extracted {zip_path} to {destination_dir}")

    except zipfile.BadZipFile as e:
        logger.error(f"Failed to extract {zip_path}: Invalid or corrupted ZIP file. Error: {str(e)}")
        raise ExtractionError("The uploaded file is not a valid ZIP archive or is corrupted.")
    except Exception as e:
        if not isinstance(e, ExtractionError):
            logger.error(f"Unexpected error during extraction of {zip_path}: {str(e)}")
            raise ExtractionError(f"Extraction failed: {str(e)}")
        raise e
