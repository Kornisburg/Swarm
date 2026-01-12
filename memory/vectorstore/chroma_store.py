"""Chroma vector store wrapper for The Hive."""

import os
from typing import Any, Optional, List

import chromadb
from chromadb.config import Settings


class ChromaStore:
    """ChromaDB vector store for semantic search."""

    def __init__(self, persist_directory: Optional[str] = None):
        """Initialize ChromaDB client.

        Args:
            persist_directory: Directory for persistence. If None, reads from env vars.
        """
        if persist_directory is None:
            persist_directory = os.getenv("CHROMA_PERSIST_DIR", "./data/chroma")

        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False),
        )

        # Create collections for different memory channels
        self._init_collections()

    def _init_collections(self) -> None:
        """Initialize ChromaDB collections."""
        # Agent Cognitive Memory - decisions and rationale
        self.cognitive_memory = self.client.get_or_create_collection(
            name="agent_cognitive_memory",
            metadata={"hnsw:space": "cosine", "hnsw:M": 16},
        )

        # Knowledge Base - best practices and patterns
        self.knowledge_base = self.client.get_or_create_collection(
            name="knowledge_base",
            metadata={"hnsw:space": "cosine"},
        )

        # Code Semantic Index - for impact analysis
        self.code_index = self.client.get_or_create_collection(
            name="code_semantic_index",
            metadata={"hnsw:space": "cosine"},
        )

    def add_decision(
        self,
        decision_id: str,
        text: str,
        embedding: List[float],
        metadata: dict[str, Any],
    ) -> None:
        """Add decision to cognitive memory.

        Args:
            decision_id: Unique decision identifier
            text: Decision summary text
            embedding: Vector embedding
            metadata: Additional metadata
        """
        self.cognitive_memory.add(
            ids=[decision_id],
            embeddings=[embedding],
            documents=[text],
            metadatas=[metadata],
        )

    def search_decisions(
        self,
        query_embedding: List[float],
        n_results: int = 5,
        where: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Search cognitive memory for similar decisions.

        Args:
            query_embedding: Query vector embedding
            n_results: Number of results to return
            where: Metadata filter

        Returns:
            Search results
        """
        return self.cognitive_memory.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where,
        )

    def add_knowledge(
        self,
        knowledge_id: str,
        text: str,
        embedding: List[float],
        metadata: dict[str, Any],
    ) -> None:
        """Add knowledge to knowledge base.

        Args:
            knowledge_id: Unique knowledge identifier
            text: Knowledge content
            embedding: Vector embedding
            metadata: Additional metadata
        """
        self.knowledge_base.add(
            ids=[knowledge_id],
            embeddings=[embedding],
            documents=[text],
            metadatas=[metadata],
        )

    def search_knowledge(
        self,
        query_embedding: List[float],
        n_results: int = 5,
        where: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Search knowledge base.

        Args:
            query_embedding: Query vector embedding
            n_results: Number of results to return
            where: Metadata filter

        Returns:
            Search results
        """
        return self.knowledge_base.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where,
        )

    def health_check(self) -> bool:
        """Check ChromaDB connection health.

        Returns:
            True if accessible, False otherwise
        """
        try:
            self.cognitive_memory.count()
            return True
        except Exception:
            return False


# Global client instance
_store: Optional[ChromaStore] = None


def get_vector_store() -> ChromaStore:
    """Get global vector store instance.

    Returns:
        ChromaStore client
    """
    global _store
    if _store is None:
        _store = ChromaStore()
    return _store
