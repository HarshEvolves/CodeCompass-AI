"""
CodeCompass Repository Upload and Retrieval Route Handlers
"""
import os
import uuid
from typing import List
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.api.v1.deps import get_current_user
from app.db import get_db
from app.models.user import User
from app.models.repository import Repository
from app.schemas.repository import RepositoryResponse

router = APIRouter(prefix="/repositories", tags=["Repositories"])

# Configuration settings
UPLOAD_DIR = "uploads"
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB limit


@router.post(
    "/upload",
    response_model=RepositoryResponse,
    status_code=status.HTTP_201_CREATED
)
async def upload_repository(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Uploads a repository ZIP file.
    Validates extension and file size, saves locally, and logs DB metadata.
    """
    # 1. Validate file extension
    filename = file.filename or ""
    if not filename.lower().endswith(".zip"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format. Only ZIP archives are allowed."
        )

    # 2. Check file size (Read chunks to verify size limit without full memory load)
    # We can also check content length headers or read a buffer limit.
    size = 0
    file_content = []
    chunk_size = 1024 * 1024  # 1MB chunks

    while True:
        chunk = await file.read(chunk_size)
        if not chunk:
            break
        size += len(chunk)
        if size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File exceeds maximum allowed upload size limit of 50MB."
            )
        file_content.append(chunk)

    # 3. Create target local uploads folder if not exists
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    # 4. Generate unique storage filename
    unique_filename = f"{uuid.uuid4()}.zip"
    storage_path = os.path.join(UPLOAD_DIR, unique_filename)

    # 5. Save the buffer content locally
    try:
        with open(storage_path, "wb") as out_file:
            for chunk in file_content:
                out_file.write(chunk)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not save file to disk: {str(e)}"
        )

    # 6. Extract repository name (original filename minus .zip)
    repo_name = os.path.splitext(filename)[0]

    # 7. Write database metadata record
    db_repo = Repository(
        user_id=current_user.id,
        name=repo_name,
        original_filename=filename,
        storage_path=storage_path,
        upload_status="uploaded"
    )

    db.add(db_repo)
    await db.flush()

    return db_repo


@router.get(
    "",
    response_model=List[RepositoryResponse],
    status_code=status.HTTP_200_OK
)
async def list_repositories(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Lists all repositories uploaded by the authenticated user.
    """
    query = select(Repository).where(Repository.user_id == current_user.id).order_by(Repository.created_at.desc())
    result = await db.execute(query)
    repositories = result.scalars().all()
    return repositories


@router.post(
    "/{repository_id}/extract",
    response_model=RepositoryResponse,
    status_code=status.HTTP_200_OK
)
async def extract_repository(
    repository_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Extracts the uploaded ZIP archive of a repository into a unique workspace directory.
    Only allows extraction of repositories owned by the currently authenticated user.
    """
    # 1. Fetch repository by ID and verify ownership
    query = select(Repository).where(
        Repository.id == repository_id,
        Repository.user_id == current_user.id
    )
    result = await db.execute(query)
    repo = result.scalars().first()

    if not repo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found."
        )

    # 2. Define unique extraction destination directory
    from app.core.config import settings
    from app.services import extract_zip_securely, ExtractionError
    
    workspace_dir = os.path.join(settings.WORKSPACE_DIR, str(repo.id))

    # 3. Perform extraction and update status
    try:
        extract_zip_securely(repo.storage_path, workspace_dir)
        repo.upload_status = "EXTRACTED"
        db.add(repo)
        await db.commit()
        await db.refresh(repo)
    except ExtractionError as e:
        repo.upload_status = "FAILED"
        db.add(repo)
        await db.commit()
        await db.refresh(repo)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        repo.upload_status = "FAILED"
        db.add(repo)
        await db.commit()
        await db.refresh(repo)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during extraction: {str(e)}"
        )

    return repo


@router.post(
    "/{repository_id}/parse",
    response_model=RepositoryResponse,
    status_code=status.HTTP_200_OK
)
async def parse_repository(
    repository_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Parses an extracted repository using Tree-sitter and stores the file metadata.
    Only allows parsing of repositories owned by the currently authenticated user
    that are in the 'EXTRACTED' state.
    """
    # 1. Fetch repository by ID and verify ownership
    query = select(Repository).where(
        Repository.id == repository_id,
        Repository.user_id == current_user.id
    )
    result = await db.execute(query)
    repo = result.scalars().first()

    if not repo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found."
        )

    # 2. Check repository state
    if repo.upload_status != "EXTRACTED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Repository cannot be parsed unless it is in the EXTRACTED state. Current state: {repo.upload_status}"
        )

    # 3. Define workspace directory path
    from app.core.config import settings
    from app.services import parse_repository_files, ParsingError

    workspace_dir = os.path.join(settings.WORKSPACE_DIR, str(repo.id))

    # 4. Trigger parsing and update status
    try:
        await parse_repository_files(db, repo.id, workspace_dir)
        repo.upload_status = "PARSED"
        db.add(repo)
        await db.commit()
        await db.refresh(repo)
    except ParsingError as e:
        repo.upload_status = "FAILED"
        db.add(repo)
        await db.commit()
        await db.refresh(repo)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        repo.upload_status = "FAILED"
        db.add(repo)
        await db.commit()
        await db.refresh(repo)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during parsing: {str(e)}"
        )

    return repo


@router.post(
    "/{repository_id}/chunk",
    response_model=RepositoryResponse,
    status_code=status.HTTP_200_OK
)
async def chunk_repository(
    repository_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Splits the parsed source code of a repository into semantic chunks and stores them.
    Only allows chunking of repositories owned by the currently authenticated user
    that are in the 'PARSED' state.
    """
    # 1. Fetch repository by ID and verify ownership
    query = select(Repository).where(
        Repository.id == repository_id,
        Repository.user_id == current_user.id
    )
    result = await db.execute(query)
    repo = result.scalars().first()

    if not repo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found."
        )

    # 2. Check repository state
    if repo.upload_status != "PARSED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Repository cannot be chunked unless it is in the PARSED state. Current state: {repo.upload_status}"
        )

    # 3. Define workspace directory path
    from app.core.config import settings
    from app.services import chunk_repository_files, ChunkingError

    workspace_dir = os.path.join(settings.WORKSPACE_DIR, str(repo.id))

    # 4. Trigger chunking and update status
    try:
        await chunk_repository_files(db, repo.id, workspace_dir)
        repo.upload_status = "CHUNKED"
        db.add(repo)
        await db.commit()
        await db.refresh(repo)
    except ChunkingError as e:
        repo.upload_status = "FAILED"
        db.add(repo)
        await db.commit()
        await db.refresh(repo)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        repo.upload_status = "FAILED"
        db.add(repo)
        await db.commit()
        await db.refresh(repo)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during chunking: {str(e)}"
        )

    return repo


