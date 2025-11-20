"""
Vector store service using ChromaDB for semantic search.
Handles embedding generation and document retrieval.
"""
import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Optional
from pathlib import Path
from backend.config import settings
from backend.utils.logger import log
from backend.utils.helpers import chunk_text
import uuid


class VectorStoreService:
    """Service for managing vector embeddings and semantic search."""

    def __init__(self):
        """Initialize the vector store and embedding model."""
        self.embedding_model_name = settings.embedding_model
        self.dimension = settings.embedding_dimension
        self.chunk_size = settings.chunk_size
        self.chunk_overlap = settings.chunk_overlap

        # Initialize ChromaDB
        db_path = Path(settings.vector_db_path)
        db_path.mkdir(parents=True, exist_ok=True)

        self.client = chromadb.PersistentClient(
            path=str(db_path),
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name="company_documents",
            metadata={"hnsw:space": "cosine"}
        )

        # Initialize embedding model
        log.info(f"Loading embedding model: {self.embedding_model_name}")
        self.embedding_model = SentenceTransformer(self.embedding_model_name)
        log.info("Embedding model loaded successfully")

    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding vector for text.

        Args:
            text: Input text

        Returns:
            Embedding vector
        """
        try:
            embedding = self.embedding_model.encode(text, show_progress_bar=False)
            return embedding.tolist()
        except Exception as e:
            log.error(f"Error generating embedding: {e}")
            raise

    def add_document(
        self,
        document_id: str,
        text: str,
        metadata: Dict[str, Any]
    ) -> int:
        """
        Add a document to the vector store by chunking and embedding it.

        Args:
            document_id: Unique document identifier
            text: Full text of the document
            metadata: Document metadata (filename, category, etc.)

        Returns:
            Number of chunks created
        """
        try:
            # Chunk the text
            chunks = chunk_text(text, self.chunk_size, self.chunk_overlap)

            if not chunks:
                log.warning(f"No chunks created for document {document_id}")
                return 0

            # Prepare data for ChromaDB
            chunk_ids = []
            chunk_texts = []
            chunk_embeddings = []
            chunk_metadatas = []

            for chunk in chunks:
                chunk_id = f"{document_id}_chunk_{chunk['id']}"
                chunk_ids.append(chunk_id)
                chunk_texts.append(chunk['text'])

                # Generate embedding
                embedding = self.generate_embedding(chunk['text'])
                chunk_embeddings.append(embedding)

                # Combine metadata
                chunk_metadata = {
                    **metadata,
                    'document_id': document_id,
                    'chunk_id': chunk['id'],
                    'start_char': chunk['start_char'],
                    'end_char': chunk['end_char'],
                    'length': chunk['length']
                }
                chunk_metadatas.append(chunk_metadata)

            # Add to ChromaDB
            self.collection.add(
                ids=chunk_ids,
                embeddings=chunk_embeddings,
                documents=chunk_texts,
                metadatas=chunk_metadatas
            )

            log.info(f"Added {len(chunks)} chunks for document {document_id}")
            return len(chunks)

        except Exception as e:
            log.error(f"Error adding document to vector store: {e}")
            raise

    def search(
        self,
        query: str,
        n_results: int = 10,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant documents using semantic similarity.

        Args:
            query: Search query
            n_results: Number of results to return
            filter_metadata: Optional metadata filters

        Returns:
            List of matching chunks with metadata and scores
        """
        try:
            # Generate query embedding
            query_embedding = self.generate_embedding(query)

            # Search in ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=filter_metadata if filter_metadata else None
            )

            # Format results
            formatted_results = []
            if results['ids'] and results['ids'][0]:
                for i in range(len(results['ids'][0])):
                    formatted_results.append({
                        'id': results['ids'][0][i],
                        'text': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'distance': results['distances'][0][i],
                        'similarity': 1 - results['distances'][0][i]  # Convert distance to similarity
                    })

            return formatted_results

        except Exception as e:
            log.error(f"Error searching vector store: {e}")
            raise

    def delete_document(self, document_id: str) -> bool:
        """
        Delete all chunks of a document from the vector store.

        Args:
            document_id: Document identifier

        Returns:
            Success status
        """
        try:
            # Find all chunks for this document
            results = self.collection.get(
                where={"document_id": document_id}
            )

            if results['ids']:
                self.collection.delete(ids=results['ids'])
                log.info(f"Deleted {len(results['ids'])} chunks for document {document_id}")
                return True

            return False

        except Exception as e:
            log.error(f"Error deleting document from vector store: {e}")
            raise

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector store.

        Returns:
            Statistics dictionary
        """
        try:
            count = self.collection.count()

            # Get sample to analyze categories
            sample = self.collection.get(limit=min(count, 1000))

            categories = {}
            if sample['metadatas']:
                for metadata in sample['metadatas']:
                    category = metadata.get('category', 'unknown')
                    categories[category] = categories.get(category, 0) + 1

            return {
                'total_chunks': count,
                'categories': categories,
                'embedding_model': self.embedding_model_name,
                'dimension': self.dimension
            }

        except Exception as e:
            log.error(f"Error getting vector store stats: {e}")
            return {'total_chunks': 0, 'categories': {}}

    def reset(self) -> bool:
        """
        Reset the vector store (delete all data).

        Returns:
            Success status
        """
        try:
            self.client.delete_collection("company_documents")
            self.collection = self.client.get_or_create_collection(
                name="company_documents",
                metadata={"hnsw:space": "cosine"}
            )
            log.warning("Vector store has been reset")
            return True

        except Exception as e:
            log.error(f"Error resetting vector store: {e}")
            return False


# Global instance
_vector_store = None


def get_vector_store() -> VectorStoreService:
    """Get or create the global vector store instance."""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStoreService()
    return _vector_store
