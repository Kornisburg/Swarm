"""RAG knowledge base for vector storage."""

import json
from typing import Any, Optional, List

from .chroma_store import get_chroma_store
from ..config import get_settings


class KnowledgeBase:
    """Vector-based knowledge base for RAG."""

    def __init__(self, collection_name: str = "knowledge_base"):
        """Initialize knowledge base.

        Args:
            collection_name: Name of the vector collection
        """
        self.collection_name = collection_name
        self.chroma = get_chroma_store()

    async def add_document(
        self,
        content: str,
        title: str,
        category: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> str:
        """Add a document to knowledge base.

        Args:
            content: Document content
            title: Document title
            category: Document category
            metadata: Optional additional metadata

        Returns:
            Document ID
        """
        try:
            doc_metadata = {
                "title": title,
                "category": category,
                "timestamp": str(__import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()),
            }
            if metadata:
                doc_metadata.update(metadata)

            # Create searchable text
            text = f"{title} {category} {content}"

            # Store in vector store
            doc_id = self.chroma.add_document(
                collection_name=self.collection_name,
                document=text,
                metadata=doc_metadata,
                embedding_text=text,
            )

            return doc_id
        except Exception as e:
            raise Exception(f"Failed to add document to knowledge base: {str(e)}")

    async def search_knowledge(
        self,
        query: str,
        category: Optional[str] = None,
        limit: int = 5,
    ) -> List[dict[str, Any]]:
        """Search knowledge base.

        Args:
            query: Search query
            category: Filter by category
            limit: Maximum results

        Returns:
            List of matching documents with metadata
        """
        try:
            # Build filter for metadata
            where = {"category": category} if category else None

            # Search vector store
            results = self.chroma.search(
                collection_name=self.collection_name,
                query_text=query,
                n_results=limit,
                where=where,
            )

            # Format results
            formatted_results = []
            if results and "documents" in results:
                for doc, metadata, distance in zip(
                    results["documents"][0] if results["documents"] else [],
                    results["metadatas"][0] if results["metadatas"] else [],
                    results["distances"][0] if results["distances"] else [],
                ):
                    formatted_results.append({
                        "document": doc,
                        "metadata": metadata,
                        "distance": distance,
                        "similarity": 1 - distance,
                    })

            return formatted_results
        except Exception as e:
            raise Exception(f"Failed to search knowledge base: {str(e)}")

    async def get_documents_by_category(
        self, category: str, limit: int = 20
    ) -> List[dict[str, Any]]:
        """Get all documents in a category.

        Args:
            category: Category to filter by
            limit: Maximum results

        Returns:
            List of documents
        """
        try:
            results = self.chroma.search(
                collection_name=self.collection_name,
                query_text=category,
                n_results=limit,
                where={"category": category},
            )

            formatted_results = []
            if results and "documents" in results:
                for doc, metadata in zip(
                    results["documents"][0] if results["documents"] else [],
                    results["metadatas"][0] if results["metadatas"] else [],
                ):
                    formatted_results.append({
                        "document": doc,
                        "metadata": metadata,
                    })

            return formatted_results
        except Exception as e:
            raise Exception(f"Failed to get documents by category: {str(e)}")

    async def delete_document(self, doc_id: str) -> None:
        """Delete a document from knowledge base.

        Args:
            doc_id: Document ID
        """
        try:
            self.chroma.delete_document(
                collection_name=self.collection_name,
                document_id=doc_id,
            )
        except Exception as e:
            raise Exception(f"Failed to delete document: {str(e)}")

    async def add_code_snippet(
        self,
        code: str,
        language: str,
        description: str,
        file_path: Optional[str] = None,
    ) -> str:
        """Add a code snippet to knowledge base.

        Args:
            code: Code content
            language: Programming language
            description: Code description
            file_path: Optional file path

        Returns:
            Document ID
        """
        return await self.add_document(
            content=code,
            title=description,
            category="code",
            metadata={
                "language": language,
                "file_path": file_path or "",
                "type": "snippet",
            },
        )

    async def search_code_snippets(
        self, query: str, language: Optional[str] = None, limit: int = 5
    ) -> List[dict[str, Any]]:
        """Search code snippets.

        Args:
            query: Search query
            language: Filter by programming language
            limit: Maximum results

        Returns:
            List of matching code snippets
        """
        where = {"category": "code", "type": "snippet"}
        if language:
            where["language"] = language

        try:
            results = self.chroma.search(
                collection_name=self.collection_name,
                query_text=query,
                n_results=limit,
                where=where,
            )

            formatted_results = []
            if results and "documents" in results:
                for doc, metadata, distance in zip(
                    results["documents"][0] if results["documents"] else [],
                    results["metadatas"][0] if results["metadatas"] else [],
                    results["distances"][0] if results["distances"] else [],
                ):
                    formatted_results.append({
                        "document": doc,
                        "metadata": metadata,
                        "distance": distance,
                        "similarity": 1 - distance,
                    })

            return formatted_results
        except Exception as e:
            raise Exception(f"Failed to search code snippets: {str(e)}")


# Global knowledge base instances
_knowledge_bases: dict[str, KnowledgeBase] = {}


def get_knowledge_base(collection_name: str = "knowledge_base") -> KnowledgeBase:
    """Get global knowledge base instance.

    Args:
        collection_name: Name of the collection

    Returns:
        Knowledge base instance
    """
    global _knowledge_bases
    if collection_name not in _knowledge_bases:
        _knowledge_bases[collection_name] = KnowledgeBase(collection_name)
    return _knowledge_bases[collection_name]
