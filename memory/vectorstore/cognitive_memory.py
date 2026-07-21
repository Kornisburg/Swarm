"""Agent cognitive memory for vector storage."""

import json
from typing import Any, Optional, List

from .chroma_store import get_vector_store
from core.config import get_settings


class CognitiveMemory:
    """Vector-based cognitive memory for agent decisions."""

    def __init__(self, collection_name: str = "cognitive_memory"):
        """Initialize cognitive memory.

        Args:
            collection_name: Name of the vector collection
        """
        self.collection_name = collection_name
        self.chroma = get_vector_store()

    async def store_decision(
        self,
        agent_type: str,
        decision_type: str,
        decision: dict[str, Any],
        context: dict[str, Any],
        confidence: float,
        workflow_id: Optional[str] = None,
    ) -> str:
        """Store a decision in cognitive memory.

        Args:
            agent_type: Type of agent
            decision_type: Type of decision
            decision: Decision content
            context: Decision context
            confidence: Confidence score
            workflow_id: Optional workflow ID

        Returns:
            Document ID
        """
        try:
            metadata = {
                "agent_type": agent_type,
                "decision_type": decision_type,
                "workflow_id": workflow_id or "",
                "confidence": str(confidence),
                "timestamp": str(__import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()),
            }

            # Create searchable text from decision
            text = f"{agent_type} {decision_type} {json.dumps(decision, default=str)}"

            # Store in vector store
            doc_id = self.chroma.add_document(
                collection_name=self.collection_name,
                document=text,
                metadata=metadata,
                embedding_text=text,
            )

            return doc_id
        except Exception as e:
            raise Exception(f"Failed to store decision in cognitive memory: {str(e)}")

    async def search_similar_decisions(
        self,
        query: str,
        agent_type: Optional[str] = None,
        decision_type: Optional[str] = None,
        workflow_id: Optional[str] = None,
        limit: int = 5,
    ) -> List[dict[str, Any]]:
        """Search for similar decisions.

        Args:
            query: Search query
            agent_type: Filter by agent type
            decision_type: Filter by decision type
            workflow_id: Filter by workflow ID
            limit: Maximum results

        Returns:
            List of similar decisions with metadata
        """
        try:
            # Build filter for metadata
            where = {}
            if agent_type:
                where["agent_type"] = agent_type
            if decision_type:
                where["decision_type"] = decision_type
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
                        "similarity": 1 - distance,  # Convert to similarity score
                    })

            return formatted_results
        except Exception as e:
            raise Exception(f"Failed to search cognitive memory: {str(e)}")

    async def get_agent_memory(
        self,
        agent_type: str,
        limit: int = 10,
    ) -> List[dict[str, Any]]:
        """Get recent decisions for an agent.

        Args:
            agent_type: Type of agent
            limit: Maximum results

        Returns:
            List of recent decisions
        """
        try:
            results = self.chroma.search(
                collection_name=self.collection_name,
                query_text=agent_type,  # Use agent type as query
                n_results=limit,
                where={"agent_type": agent_type},
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
            raise Exception(f"Failed to get agent memory: {str(e)}")

    async def get_workflow_memory(
        self, workflow_id: str, limit: int = 20
    ) -> List[dict[str, Any]]:
        """Get all decisions for a workflow.

        Args:
            workflow_id: Workflow ID
            limit: Maximum results

        Returns:
            List of workflow decisions
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
            raise Exception(f"Failed to get workflow memory: {str(e)}")

    async def delete_workflow_memory(self, workflow_id: str) -> None:
        """Delete all memory for a workflow.

        Args:
            workflow_id: Workflow ID
        """
        try:
            # Get all documents for workflow
            results = self.chroma.search(
                collection_name=self.collection_name,
                query_text=workflow_id,
                n_results=1000,  # Large number to get all
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
            raise Exception(f"Failed to delete workflow memory: {str(e)}")


# Global cognitive memory instances
_cognitive_memories: dict[str, CognitiveMemory] = {}


def get_cognitive_memory(collection_name: str = "cognitive_memory") -> CognitiveMemory:
    """Get global cognitive memory instance.

    Args:
        collection_name: Name of the collection

    Returns:
        Cognitive memory instance
    """
    global _cognitive_memories
    if collection_name not in _cognitive_memories:
        _cognitive_memories[collection_name] = CognitiveMemory(collection_name)
    return _cognitive_memories[collection_name]
