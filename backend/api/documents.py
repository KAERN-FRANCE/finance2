"""
API routes for document management.
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks, Form
from typing import List, Optional
from pathlib import Path
import shutil
from sqlalchemy.orm import Session
import json

from backend.models.database import get_db, DocumentModel
from backend.models.schemas import (
    DocumentResponse, DocumentStats, DocumentStatus,
    DocumentType, DocumentCategory
)
from backend.config import settings
from backend.utils.logger import log
from backend.utils.helpers import sanitize_filename

# Try to import full processor, fallback to simple processor
try:
    from backend.services.document_processor import get_document_processor
    from backend.services.vector_store import get_vector_store
    USE_FULL_PROCESSOR = True
    log.info("Full AI processor available")
except ImportError as e:
    log.warning(f"Full processor not available ({e}), using simple processor")
    USE_FULL_PROCESSOR = False

# Always import simple processor as fallback
from backend.services.simple_document_processor import get_simple_document_processor

router = APIRouter(prefix="/api/documents", tags=["documents"])


async def process_document_background(
    doc_id: str,
    file_path: Path,
    filename: str,
    file_type: DocumentType,
    db: Session
):
    """Background task for processing documents."""
    try:
        # Use simple processor by default, or full processor if available
        if USE_FULL_PROCESSOR:
            try:
                processor = get_document_processor()
                log.info(f"Using FULL processor for {filename}")
            except Exception as e:
                log.warning(f"Full processor failed to initialize, using simple: {e}")
                processor = get_simple_document_processor()
        else:
            processor = get_simple_document_processor()
            log.info(f"Using SIMPLE processor for {filename}")

        # Process the document
        result = await processor.process_document(
            file_path=file_path,
            filename=filename,
            file_type=file_type,
            document_id=doc_id
        )

        # Update database
        doc = db.query(DocumentModel).filter(DocumentModel.id == doc_id).first()
        if doc:
            if result["success"]:
                doc.status = DocumentStatus.INDEXED
                doc.category = result["category"]
                doc.metadata = result["metadata"].dict()
            else:
                doc.status = DocumentStatus.ERROR
                doc.error_message = result.get("error", "Unknown error")

            db.commit()

    except Exception as e:
        log.error(f"Error in background processing: {e}")
        doc = db.query(DocumentModel).filter(DocumentModel.id == doc_id).first()
        if doc:
            doc.status = DocumentStatus.ERROR
            doc.error_message = str(e)
            db.commit()


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    problematiques: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Upload a document for processing and indexing.

    Args:
        file: Document file to upload
        problematiques: JSON array of problématiques (optional)
        db: Database session
    """
    try:
        # Validate file type
        file_ext = Path(file.filename).suffix.lower()
        file_type_map = {
            ".pdf": DocumentType.PDF,
            ".docx": DocumentType.DOCX,
            ".csv": DocumentType.CSV,
            ".xlsx": DocumentType.XLSX,
        }

        if file_ext not in file_type_map:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file_ext}. Supported: {', '.join(file_type_map.keys())}"
            )

        file_type = file_type_map[file_ext]

        # Sanitize filename
        safe_filename = sanitize_filename(file.filename)

        # Parse problematiques
        problematiques_list = []
        if problematiques:
            try:
                problematiques_list = json.loads(problematiques) if isinstance(problematiques, str) else problematiques
                if not isinstance(problematiques_list, list):
                    problematiques_list = [problematiques_list]
            except json.JSONDecodeError:
                # If not JSON, treat as single problematique
                problematiques_list = [problematiques] if problematiques.strip() else []

        # Create document record
        doc = DocumentModel(
            filename=safe_filename,
            file_type=file_type,
            size_bytes=0,  # Will update after saving
            status=DocumentStatus.UPLOADING,
            problematiques=problematiques_list
        )

        db.add(doc)
        db.commit()
        db.refresh(doc)

        # Save file
        upload_dir = Path(settings.upload_dir)
        file_path = upload_dir / f"{doc.id}_{safe_filename}"

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Update size
        doc.size_bytes = file_path.stat().st_size
        doc.status = DocumentStatus.PROCESSING
        db.commit()

        # Check size limit
        max_size_bytes = settings.max_upload_size_mb * 1024 * 1024
        if doc.size_bytes > max_size_bytes:
            doc.status = DocumentStatus.ERROR
            doc.error_message = f"File too large: {doc.size_bytes / 1024 / 1024:.1f}MB > {settings.max_upload_size_mb}MB"
            db.commit()
            raise HTTPException(status_code=400, detail=doc.error_message)

        # Process in background
        background_tasks.add_task(
            process_document_background,
            doc.id,
            file_path,
            safe_filename,
            file_type,
            db
        )

        log.info(f"Document uploaded: {safe_filename} ({doc.id})")

        return DocumentResponse.from_orm(doc)

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error uploading document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=List[DocumentResponse])
async def list_documents(
    skip: int = 0,
    limit: int = 100,
    category: str = None,
    db: Session = Depends(get_db)
):
    """
    List all documents with optional filtering.
    """
    try:
        query = db.query(DocumentModel)

        if category:
            try:
                cat_enum = DocumentCategory(category)
                query = query.filter(DocumentModel.category == cat_enum)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid category: {category}")

        documents = query.offset(skip).limit(limit).all()
        return [DocumentResponse.from_orm(doc) for doc in documents]

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error listing documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=DocumentStats)
async def get_documents_stats(db: Session = Depends(get_db)):
    """
    Get statistics about the document knowledge base.
    """
    try:
        documents = db.query(DocumentModel).all()

        total_size_bytes = sum(doc.size_bytes for doc in documents)
        total_size_mb = total_size_bytes / 1024 / 1024

        # Count by category
        by_category = {}
        for doc in documents:
            cat = doc.category.value if doc.category else "unknown"
            by_category[cat] = by_category.get(cat, 0) + 1

        # Count by type
        by_type = {}
        for doc in documents:
            typ = doc.file_type.value
            by_type[typ] = by_type.get(typ, 0) + 1

        # Get vector store stats (if available)
        total_chunks = 0
        if USE_FULL_PROCESSOR:
            try:
                vector_store = get_vector_store()
                vector_stats = vector_store.get_stats()
                total_chunks = vector_stats.get("total_chunks", 0)
            except Exception as e:
                log.warning(f"Vector store not available: {e}")
                total_chunks = 0

        # Last updated
        last_updated = None
        if documents:
            last_updated = max(doc.upload_date for doc in documents)

        return DocumentStats(
            total_documents=len(documents),
            total_size_mb=round(total_size_mb, 2),
            documents_by_category=by_category,
            documents_by_type=by_type,
            total_chunks=total_chunks,
            last_updated=last_updated
        )

    except Exception as e:
        log.error(f"Error getting document stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: str, db: Session = Depends(get_db)):
    """
    Get details of a specific document.
    """
    try:
        doc = db.query(DocumentModel).filter(DocumentModel.id == document_id).first()

        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        return DocumentResponse.from_orm(doc)

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error getting document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{document_id}")
async def delete_document(document_id: str, db: Session = Depends(get_db)):
    """
    Delete a document and its indexed data.
    """
    try:
        doc = db.query(DocumentModel).filter(DocumentModel.id == document_id).first()

        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        # Delete from vector store (if available)
        if USE_FULL_PROCESSOR:
            try:
                vector_store = get_vector_store()
                vector_store.delete_document(document_id)
            except Exception as e:
                log.warning(f"Could not delete from vector store: {e}")

        # Delete file
        upload_dir = Path(settings.upload_dir)
        file_path = upload_dir / f"{doc.id}_{doc.filename}"
        if file_path.exists():
            file_path.unlink()

        # Delete from database
        db.delete(doc)
        db.commit()

        log.info(f"Document deleted: {document_id}")

        return {"message": "Document deleted successfully", "id": document_id}

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error deleting document: {e}")
        raise HTTPException(status_code=500, detail=str(e))
