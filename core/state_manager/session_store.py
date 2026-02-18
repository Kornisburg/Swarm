"""Redis session store for active workflows."""

import json
from typing import Any, Optional

from memory.redis.client import get_redis_client
from core.config import get_settings
from core.exceptions import WorkflowException


class SessionStore:
    """Redis-based session store for active workflow state."""

    def __init__(self):
        """Initialize session store."""
        self.redis = get_redis_client()
        self.settings = get_settings()
        self.ttl = 3600  # 1 hour TTL for active sessions

    async def save_session(self, workflow_id: str, state: dict[str, Any]) -> None:
        """Save workflow session state.

        Args:
            workflow_id: Workflow identifier
            state: Workflow state dictionary
        """
        try:
            key = f"workflow:{workflow_id}"
            await self.redis.set(key, json.dumps(state), ex=self.ttl)
        except Exception as e:
            raise WorkflowException(f"Failed to save session: {str(e)}")

    async def get_session(self, workflow_id: str) -> Optional[dict[str, Any]]:
        """Retrieve workflow session state.

        Args:
            workflow_id: Workflow identifier

        Returns:
            Session state or None if not found
        """
        try:
            key = f"workflow:{workflow_id}"
            data = await self.redis.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            raise WorkflowException(f"Failed to get session: {str(e)}")

    async def update_stage(self, workflow_id: str, stage: str) -> None:
        """Update workflow stage.

        Args:
            workflow_id: Workflow identifier
            stage: Current stage name
        """
        try:
            key = f"workflow:{workflow_id}:stage"
            await self.redis.set(key, stage, ex=self.ttl)
        except Exception as e:
            raise WorkflowException(f"Failed to update stage: {str(e)}")

    async def get_stage(self, workflow_id: str) -> Optional[str]:
        """Get current workflow stage.

        Args:
            workflow_id: Workflow identifier

        Returns:
            Current stage or None
        """
        try:
            key = f"workflow:{workflow_id}:stage"
            return await self.redis.get(key)
        except Exception as e:
            raise WorkflowException(f"Failed to get stage: {str(e)}")

    async def add_artifact(self, workflow_id: str, artifact_id: str) -> None:
        """Add artifact to workflow.

        Args:
            workflow_id: Workflow identifier
            artifact_id: Artifact identifier
        """
        try:
            key = f"workflow:{workflow_id}:artifacts"
            await self.redis.lpush(key, artifact_id)
            await self.redis.expire(key, self.ttl)
        except Exception as e:
            raise WorkflowException(f"Failed to add artifact: {str(e)}")

    async def get_artifacts(self, workflow_id: str) -> list[str]:
        """Get workflow artifacts.

        Args:
            workflow_id: Workflow identifier

        Returns:
            List of artifact IDs
        """
        try:
            key = f"workflow:{workflow_id}:artifacts"
            return await self.redis.lrange(key, 0, -1)
        except Exception as e:
            raise WorkflowException(f"Failed to get artifacts: {str(e)}")

    async def delete_session(self, workflow_id: str) -> None:
        """Delete workflow session.

        Args:
            workflow_id: Workflow identifier
        """
        try:
            keys = [
                f"workflow:{workflow_id}",
                f"workflow:{workflow_id}:stage",
                f"workflow:{workflow_id}:artifacts",
            ]
            for key in keys:
                await self.redis.delete(key)
        except Exception as e:
            raise WorkflowException(f"Failed to delete session: {str(e)}")

    async def health_check(self) -> bool:
        """Check Redis health.

        Returns:
            True if healthy
        """
        return self.redis.health_check()


# Global session store instance
_session_store: Optional[SessionStore] = None


def get_session_store() -> SessionStore:
    """Get global session store instance.

    Returns:
        Session store instance
    """
    global _session_store
    if _session_store is None:
        _session_store = SessionStore()
    return _session_store
