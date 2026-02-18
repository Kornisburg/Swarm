"""Code semantic index for vector storage."""

import json
from typing import Any, Optional, List

from .chroma_store import get_chroma_store
from ..config import get_settings


class CodeIndex:
    """Vector-based code index for semantic search."""

    def __init__(self, collection_name: str = "code_index"):
        """Initialize code index.

        Args:
            collection_name: Name of the vector collection
        """
        self.collection_name = collection_name
        self.chroma = get_chroma_store()

    async def index_code(
        self,
        code: str,
        file_path: str,
        language: str,
        metadata: Optional[dict[str, Any]] = None,
        workflow_id: Optional[str] = None,
    ) -> str:
        """Index a code snippet.

        Args:
            code: Code content
            file_path: File path
            language: Programming language
            metadata: Optional additional metadata
            workflow_id: Optional workflow ID

        Returns:
            Document ID
        """
        try:
            doc_metadata = {
                "file_path": file_path,
                "language": language,
                "workflow_id": workflow_id or "",
                "timestamp": str(__import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()),
            }
            if metadata:
                doc_metadata.update(metadata)

            # Create searchable text
            text = f"{file_path} {language} {code}"

            # Store in vector store
            doc_id = self.chroma.add_document(
                collection_name=self.collection_name,
                document=text,
                metadata=doc_metadata,
                embedding_text=text,
            )

            return doc_id
        except Exception as e:
            raise Exception(f"Failed to index code: {str(e)}")

    async def search_code(
        self,
        query: str,
        language: Optional[str] = None,
        workflow_id: Optional[str] = None,
        limit: int = 5,
    ) -> List[dict[str, Any]]:
        """Search code index.

        Args:
            query: Search query
            language: Filter by programming language
            workflow_id: Filter by workflow ID
            limit: Maximum results

        Returns:
            List of matching code snippets
        """
        try:
            # Build filter for metadata
            where = {}
            if language:
                where["language"] = language
            if workflow_id:
                where["workflow_id"] = workflow_id

            # Search vector store
            results = self.chroma.search(
                collection_name=self.collection_name,
                query_text=query,
                n_results=limit,
                where=where if where else None,
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
            raise Exception(f"Failed to search code index: {str(e)}")

    async def search_similar_functions(
        self,
        query: str,
        language: Optional[str] = None,
        limit: int = 5,
    ) -> List[dict[str, Any]]:
        """Search for similar functions in code.

        Args:
            query: Function name or description
            language: Filter by programming language
            limit: Maximum results

        Returns:
            List of similar functions
        """
        try:
            # Build filter
            where = {"type": "function"} if language else None
            if language:
                where["language"] = language

            # Search with function-focused query
            results = self.chroma.search(
                collection_name=self.collection_name,
                query_text=f"function {query}",
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
            raise Exception(f"Failed to search similar functions: {str(e)}")

    async def index_function(
        self,
        name: str,
        code: str,
        file_path: str,
        language: str,
        description: Optional[str] = None,
    ) -> str:
        """Index a function definition.

        Args:
            name: Function name
            code: Function code
            file_path: File path
            language: Programming language
            description: Optional function description

        Returns:
            Document ID
        """
        return await self.index_code(
            code=code,
            file_path=file_path,
            language=language,
            metadata={
                "name": name,
                "type": "function",
                "description": description or "",
            },
        )

    async def get_workflow_code(
        self, workflow_id: str, limit: int = 50
    ) -> List[dict[str, Any]]:
        """Get all code for a workflow.

        Args:
            workflow_id: Workflow ID
            limit: Maximum results

        Returns:
            List of code snippets
        """
        try:
            results = self.chroma.search(
                collection_name=self.collection_name,
                query_text=workflow_id,
                n_results=limit,
                where={"workflow_id": workflow_id},
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
            raise Exception(f"Failed to get workflow code: {str(e)}")

    async def delete_workflow_code(self, workflow_id: str) -> None:
        """Delete all code for a workflow.

        Args:
            workflow_id: Workflow ID
        """
        try:
            # Get all documents for workflow
            results = self.chroma.search(
                collection_name=self.collection_name,
                query_text=workflow_id,
                n_results=1000,
                where={"workflow_id": workflow_id},
            )

            # Delete documents
            if results and "ids" in results and results["ids"]:
                for doc_id in results["ids"][0]:
                    self.chroma.delete_document(
                        collection_name=self.collection_name,
                        document_id=doc_id,
                    )
        except Exception as e:
            raise Exception(f"Failed to delete workflow code: {str(e)}")


# Global code index instances
_code_indexes: dict[str, CodeIndex] = {}


def get_code_index(collection_name: str = "code_index") -> CodeIndex:
    """Get global code index instance.

    Args:
        collection_name: Name of the collection

    Returns:
        Code index instance
    """
    global _code_indexes
    if collection_name not in _code_indexes:
        _code_indexes[collection_name] = CodeIndex(collection_name)
    return _code_indexes[collection_name]
