# modules/retrievers/chroma.py
"""ChromaDB retriever module implementation."""

from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
import logging
from pathlib import Path
import uuid

from modules.base import RetrieverModule
# TODO: Add import for Langfuse & refactor to be Pythonic
logger = logging.getLogger(__name__)


class ChromaRetriever(RetrieverModule):
    """
    ChromaDB-based retriever for local vector storage.
    
    Simple, fast, and perfect for prototyping.
    """
    
    implements = "nai.module.retriever.chroma@1.0.0"
    
    def setup(self) -> None:
        """Initialize ChromaDB client and collection."""
        super().setup()
        
        # Create persist directory
        persist_dir = Path(self.config.get("persist_dir", ".nai/chroma"))
        persist_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize client
        self.client = chromadb.PersistentClient(
            path=str(persist_dir),
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Get or create collection
        collection_name = self.config.get("collection", "nai_docs")
        distance_metric = self.config.get("distance_metric", "cosine")
        
        try:
            self.collection = self.client.get_collection(collection_name)
            logger.info(f"Loaded existing collection: {collection_name}")
        except:
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"hnsw:space": distance_metric}
            )
            logger.info(f"Created new collection: {collection_name}")
        
        self._doc_count = self.collection.count()
    
    def add(self, 
            texts: List[str], 
            embeddings: List[List[float]], 
            metadata: Optional[List[Dict]] = None) -> None:
        """
        Add documents to the collection.
        
        Args:
            texts: Document texts
            embeddings: Document embeddings
            metadata: Optional metadata for each document
        """
        if not self._setup_complete:
            self.setup()
        
        if not texts:
            return
        
        # Generate IDs
        ids = [str(uuid.uuid4()) for _ in texts]
        
        # Prepare metadata
        if metadata is None:
            metadata = [{"source": "unknown"} for _ in texts]
        
        # Add to collection
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadata
        )
        
        self._doc_count += len(texts)
        logger.info(f"Added {len(texts)} documents. Total: {self._doc_count}")
    
    def __call__(self, 
                 query_embedding: List[float], 
                 k: int = 5,
                 filter: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents.
        
        Args:
            query_embedding: Query vector
            k: Number of results to return
            filter: Optional metadata filter
            
        Returns:
            List of documents with text, score, and metadata
        """
        if not self._setup_complete:
            self.setup()
        
        @self._track_metrics
        def _retrieve():
            # Query collection
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=min(k, self._doc_count),
                where=filter
            )
            
            # Format results
            documents = []
            for i in range(len(results['ids'][0])):
                doc = {
                    'id': results['ids'][0][i],
                    'text': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'score': 1 - results['distances'][0][i]  # Convert distance to similarity
                }
                documents.append(doc)
            
            logger.debug(f"Retrieved {len(documents)} documents")
            return documents
        
        return _retrieve()
    
    def delete(self, ids: Optional[List[str]] = None, filter: Optional[Dict] = None) -> None:
        """Delete documents by ID or metadata filter."""
        if ids:
            self.collection.delete(ids=ids)
            logger.info(f"Deleted {len(ids)} documents by ID")
        elif filter:
            self.collection.delete(where=filter)
            logger.info(f"Deleted documents matching filter: {filter}")
    
    def reset(self) -> None:
        """Clear all documents from the collection."""
        # Recreate collection
        collection_name = self.collection.name
        self.client.delete_collection(collection_name)
        self.collection = self.client.create_collection(
            name=collection_name,
            metadata={"hnsw:space": self.config.get("distance_metric", "cosine")}
        )
        self._doc_count = 0
        logger.info("Reset collection")
    
    @property
    def count(self) -> int:
        """Return number of documents in collection."""
        return self._doc_count
    
    def get_stats(self) -> Dict[str, Any]:
        """Get collection statistics."""
        return {
            "count": self.count,
            "collection": self.collection.name,
            "persist_dir": str(self.config.get("persist_dir")),
            **self.metrics
        }