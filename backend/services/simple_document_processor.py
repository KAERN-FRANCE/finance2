"""
Simplified document processor for testing without AI dependencies.
Works with minimal dependencies - just stores documents in DB without full processing.
"""
from pathlib import Path
from typing import Dict, Any
from backend.config import settings
from backend.utils.logger import log
from backend.models.schemas import DocumentType, DocumentCategory, DocumentMetadata


class SimpleDocumentProcessor:
    """Simplified document processor that works without AI dependencies."""

    def __init__(self):
        """Initialize the simple processor."""
        self.upload_dir = Path(settings.upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def extract_text_simple(self, file_path: Path, file_type: DocumentType) -> tuple[str, Dict[str, Any]]:
        """
        Simple text extraction without heavy dependencies.

        Args:
            file_path: Path to file
            file_type: Type of document

        Returns:
            Tuple of (text, metadata)
        """
        metadata = {
            'page_count': 1,
            'word_count': 0,
        }

        # For now, just read text files directly
        # PDF, DOCX, etc. will need proper libraries
        if file_type == DocumentType.PDF:
            text = f"[PDF Document: {file_path.name}]"
            metadata['page_count'] = 1
        elif file_type == DocumentType.DOCX:
            text = f"[DOCX Document: {file_path.name}]"
        elif file_type in [DocumentType.CSV, DocumentType.XLSX]:
            text = f"[Data File: {file_path.name}]"
        else:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read()
            except:
                text = f"[Binary File: {file_path.name}]"

        metadata['word_count'] = len(text.split())
        return text, metadata

    async def process_document(
        self,
        file_path: Path,
        filename: str,
        file_type: DocumentType,
        document_id: str
    ) -> Dict[str, Any]:
        """
        Process document in simplified mode.

        Args:
            file_path: Path to file
            filename: Original filename
            file_type: Document type
            document_id: Document ID

        Returns:
            Processing results
        """
        try:
            log.info(f"Processing document in SIMPLE mode: {filename}")

            # Simple text extraction
            text, base_metadata = self.extract_text_simple(file_path, file_type)

            # Create basic metadata
            metadata = DocumentMetadata(
                page_count=base_metadata.get('page_count', 1),
                word_count=base_metadata.get('word_count', 0),
                extracted_kpis=[],
                extracted_dates=[],
                extracted_amounts=[],
                key_entities=[]
            )

            # Simple categorization based on filename
            filename_lower = filename.lower()
            if any(word in filename_lower for word in ['budget', 'finance', 'comptab', 'bilan']):
                category = DocumentCategory.FINANCE
            elif any(word in filename_lower for word in ['strateg', 'plan', 'objectif']):
                category = DocumentCategory.STRATEGY
            elif any(word in filename_lower for word in ['rh', 'personnel', 'equipe', 'recrutement']):
                category = DocumentCategory.HR
            elif any(word in filename_lower for word in ['projet', 'project']):
                category = DocumentCategory.PROJECTS
            elif any(word in filename_lower for word in ['legal', 'juridique', 'contrat']):
                category = DocumentCategory.LEGAL
            elif any(word in filename_lower for word in ['operation', 'process', 'procedure']):
                category = DocumentCategory.OPERATIONS
            else:
                category = DocumentCategory.OTHER

            log.info(f"Document processed (simple mode): {filename} - Category: {category.value}")

            return {
                'success': True,
                'category': category,
                'metadata': metadata,
                'chunks_created': 0,  # No vector indexing in simple mode
                'summary': f'Document indexed in simple mode (no AI processing)'
            }

        except Exception as e:
            log.error(f"Error processing document {filename}: {e}")
            return {
                'success': False,
                'error': str(e)
            }


# Global instance
_simple_processor = None


def get_simple_document_processor() -> SimpleDocumentProcessor:
    """Get or create the simple document processor instance."""
    global _simple_processor
    if _simple_processor is None:
        _simple_processor = SimpleDocumentProcessor()
    return _simple_processor
