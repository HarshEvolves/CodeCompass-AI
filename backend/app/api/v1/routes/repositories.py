"""
CodeCompass Repository Upload and Retrieval Route Handlers
"""
import logging
import os
import shutil
import uuid
from typing import List
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
from app.api.v1.deps import get_current_user
from app.db import get_db
from app.models.user import User
from app.models.repository import Repository
from app.schemas.repository import RepositoryResponse
from app.schemas.search import SearchRequest, SearchResultResponse
from app.schemas.chat import ChatRequest, ChatResponse

router = APIRouter(prefix="/repositories", tags=["Repositories"])
logger = logging.getLogger(__name__)

# Configuration settings
UPLOAD_DIR = settings.UPLOAD_DIR
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
    logger.info(f"CORS Check / Request received: parse_repository repository_id={repository_id}, user={current_user.email}")

    # 1. Fetch repository by ID and verify ownership
    query = select(Repository).where(
        Repository.id == repository_id,
        Repository.user_id == current_user.id
    )
    result = await db.execute(query)
    repo = result.scalars().first()

    if not repo:
        logger.error(f"Repository lookup failed: repository_id={repository_id} not found or access denied for user={current_user.email}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found."
        )

    logger.info(f"Repository lookup succeeded: repository_id={repository_id}, current_status={repo.upload_status}")

    # 2. Check repository state
    if repo.upload_status != "EXTRACTED":
        logger.error(f"Invalid state for parsing: repository_id={repository_id}, status={repo.upload_status}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Repository cannot be parsed unless it is in the EXTRACTED state. Current state: {repo.upload_status}"
        )

    # 3. Define workspace directory path
    from app.core.config import settings
    from app.services import parse_repository_files, ParsingError

    workspace_dir = os.path.join(settings.WORKSPACE_DIR, str(repo.id))
    logger.info(f"Determined workspace path for parsing: workspace_dir={workspace_dir}, repository_id={repository_id}")

    # 4. Trigger parsing and update status
    try:
        logger.info(f"Invoking parse_repository_files: repository_id={repo.id}, workspace_dir={workspace_dir}")
        await parse_repository_files(db, repo.id, workspace_dir)
        
        logger.info(f"parse_repository_files execution finished successfully for repository_id={repo.id}. Setting state to PARSED.")
        repo.upload_status = "PARSED"
        db.add(repo)
        await db.commit()
        await db.refresh(repo)
        logger.info(f"Database update complete: repository_id={repo.id} status is now PARSED.")
    except ParsingError as e:
        logger.exception(f"Parsing error occurred during execution on repository_id={repo.id}")
        # Roll back the failed transaction to allow status update
        await db.rollback()
        try:
            repo.upload_status = "FAILED"
            db.add(repo)
            await db.commit()
            await db.refresh(repo)
            logger.info(f"Successfully marked repository_id={repo.id} status as FAILED.")
        except Exception as rb_err:
            logger.exception(f"Failed to set status to FAILED after ParsingError rollback on repository_id={repo.id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.exception(f"Unexpected exception caught in parse_repository route for repository_id={repo.id}")
        # Roll back the failed transaction to allow status update
        await db.rollback()
        try:
            repo.upload_status = "FAILED"
            db.add(repo)
            await db.commit()
            await db.refresh(repo)
            logger.info(f"Successfully marked repository_id={repo.id} status as FAILED.")
        except Exception as rb_err:
            logger.exception(f"Failed to set status to FAILED after unexpected Exception rollback on repository_id={repo.id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
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


@router.post(
    "/{repository_id}/index",
    response_model=RepositoryResponse,
    status_code=status.HTTP_200_OK
)
async def index_repository(
    repository_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generates vector embeddings for all code chunks belonging to a repository
    and stores them in ChromaDB. Only allows indexing of repositories owned
    by the currently authenticated user that are in the 'CHUNKED' state.
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
    if repo.upload_status != "CHUNKED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Repository cannot be indexed unless it is in the CHUNKED state. Current state: {repo.upload_status}"
        )

    # 3. Trigger embedding generation and update status
    from app.services import index_repository_chunks, EmbeddingError

    try:
        total_indexed = await index_repository_chunks(db, repo.id)
        repo.upload_status = "INDEXED"
        db.add(repo)
        await db.commit()
        await db.refresh(repo)
    except EmbeddingError as e:
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
            detail=f"An unexpected error occurred during indexing: {str(e)}"
        )

    return repo


@router.post(
    "/{repository_id}/search",
    response_model=List[SearchResultResponse],
    status_code=status.HTTP_200_OK
)
async def search_repository(
    repository_id: uuid.UUID,
    search_req: SearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Performs a semantic search on the code chunks of a repository using the query string.
    Only allows searching repositories owned by the currently authenticated user
    that are in the 'INDEXED' state.
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
    if repo.upload_status != "INDEXED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Repository cannot be searched unless it is in the INDEXED state. Current state: {repo.upload_status}"
        )

    # 3. Trigger search and return results
    from app.services import search_repository_chunks, SearchError

    try:
        results = await search_repository_chunks(
            repository_id=repo.id,
            query=search_req.query,
            top_k=search_req.top_k
        )
        return results
    except SearchError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during search: {str(e)}"
        )


@router.post(
    "/{repository_id}/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK
)
async def chat_repository(
    repository_id: uuid.UUID,
    chat_req: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generates an AI RAG answer for the user query using only retrieved repository chunks.
    Only allows chatting with repositories owned by the currently authenticated user
    that are in the 'INDEXED' state.
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
    if repo.upload_status != "INDEXED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Repository cannot be queried via chat unless it is in the INDEXED state. Current state: {repo.upload_status}"
        )

    # 3. Trigger RAG generation and return results
    from app.services import generate_rag_answer, RAGError

    try:
        results = await generate_rag_answer(
            repository_id=repo.id,
            query=chat_req.query,
            top_k=chat_req.top_k,
            conversation_history=chat_req.conversation_history
        )
        return results
    except RAGError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during chat: {str(e)}"
        )


@router.delete(
    "/{repository_id}",
    status_code=status.HTTP_200_OK
)
async def delete_repository(
    repository_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Permanently deletes a repository: its ChromaDB embeddings, on-disk workspace
    files, and database record. Only allows deletion of repositories owned by
    the currently authenticated user. Each removal step is independently
    fault-tolerant so a partial failure never blocks the overall deletion.
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

    # 2. Remove ChromaDB embeddings (best-effort)
    from app.services.embedder import get_chroma_collection

    try:
        collection = get_chroma_collection()
        existing = collection.get(where={"repository_id": str(repo.id)})
        if existing and existing["ids"]:
            collection.delete(ids=existing["ids"])
            logger.info(f"Deleted {len(existing['ids'])} ChromaDB embeddings for repository {repo.id}")
    except Exception as e:
        logger.warning(f"Could not remove ChromaDB embeddings for repository {repo.id}: {str(e)}")

    # 3. Remove on-disk workspace files (best-effort)
    workspace_dir = os.path.join(settings.WORKSPACE_DIR, str(repo.id))
    try:
        shutil.rmtree(workspace_dir)
        logger.info(f"Removed workspace directory: {workspace_dir}")
    except FileNotFoundError:
        pass
    except Exception as e:
        logger.warning(f"Could not remove workspace directory {workspace_dir}: {str(e)}")

    # 4. Remove the original uploaded archive (best-effort)
    try:
        os.remove(repo.storage_path)
        logger.info(f"Removed uploaded archive: {repo.storage_path}")
    except FileNotFoundError:
        pass
    except Exception as e:
        logger.warning(f"Could not remove uploaded archive {repo.storage_path}: {str(e)}")

    # 5. Delete the database record
    await db.delete(repo)
    await db.commit()

    return {"detail": "Repository deleted successfully."}


@router.get(
    "/{repository_id}/file",
    status_code=status.HTTP_200_OK
)
async def get_repository_file(
    repository_id: uuid.UUID,
    file_path: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves the complete content of a file within the workspace.
    Only allows access to repositories owned by the currently authenticated user.
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

    # 2. Resolve safe path
    workspace_dir = os.path.abspath(os.path.join(settings.WORKSPACE_DIR, str(repo.id)))
    target_path = os.path.abspath(os.path.join(workspace_dir, file_path))

    # Path traversal validation (Zip Slip style protection)
    if not target_path.startswith(workspace_dir + os.sep) and target_path != workspace_dir:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Access denied: Directory traversal path detected."
        )

    if not os.path.exists(target_path) or not os.path.isfile(target_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File not found in repository: {file_path}"
        )

    try:
        with open(target_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        return {"content": content, "relative_path": file_path}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not read file: {str(e)}"
        )



