"""Workflow checkpointing with LangGraph."""

from typing import Any

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from ...memory.postgres.client import get_postgres_client
from ...config import get_settings
from ...exceptions import WorkflowException


class CheckpointManager:
    """Manages workflow checkpoints with LangGraph."""

    def __init__(self):
        """Initialize checkpoint manager."""
        self.settings = get_settings()
        self.postgres = get_postgres_client()
        self._saver: Any = None

    async def get_saver(self) -> AsyncPostgresSaver:
        """Get LangGraph checkpoint saver.

        Returns:
            AsyncPostgresSaver instance

        Raises:
            WorkflowException: If saver cannot be initialized
        """
        if self._saver is None:
            try:
                # Create the checkpoint saver using PostgreSQL connection
                sync_engine = self.postgres.engine.sync_engine
                self._saver = AsyncPostgresSaver.from_conn_string(
                    f"postgresql://{self.settings.postgres_user}:"
                    f"{self.settings.postgres_password}@"
                    f"{self.settings.postgres_host}:"
                    f"{self.settings.postgres_port}/"
                    f"{self.settings.postgres_db}"
                )
                # Initialize the checkpoint tables
                await self._saver.setup()
            except Exception as e:
                raise WorkflowException(f"Failed to initialize checkpoint saver: {str(e)}")
        return self._saver

    async def save_checkpoint(
        self,
        thread_id: str,
        checkpoint: dict[str, Any],
        metadata: dict[str, Any],
    ) -> str:
        """Save a workflow checkpoint.

        Args:
            thread_id: Workflow/thread identifier
            checkpoint: Checkpoint data
            metadata: Checkpoint metadata

        Returns:
            Checkpoint ID
        """
        try:
            saver = await self.get_saver()
            config = {"configurable": {"thread_id": thread_id}}
            await saver.aput(config, checkpoint, metadata)
            return thread_id
        except Exception as e:
            raise WorkflowException(f"Failed to save checkpoint: {str(e)}")

    async def load_checkpoint(
        self, thread_id: str, checkpoint_id: Optional[str] = None
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        """Load a workflow checkpoint.

        Args:
            thread_id: Workflow/thread identifier
            checkpoint_id: Optional specific checkpoint ID

        Returns:
            Tuple of (checkpoint, metadata)
        """
        try:
            saver = await self.get_saver()
            config = {"configurable": {"thread_id": thread_id}}
            checkpoint_tuple = await saver.aget_tuple(config)
            if checkpoint_tuple:
                checkpoint, metadata = checkpoint_tuple
                return checkpoint, metadata
            return {}, {}
        except Exception as e:
            raise WorkflowException(f"Failed to load checkpoint: {str(e)}")

    async def list_checkpoints(
        self, thread_id: str
    ) -> list[dict[str, Any]]:
        """List all checkpoints for a workflow.

        Args:
            thread_id: Workflow/thread identifier

        Returns:
            List of checkpoint information
        """
        try:
            saver = await self.get_saver()
            config = {"configurable": {"thread_id": thread_id}}
            checkpoints = []
            async for checkpoint_config in saver.alist(config):
                checkpoint_info = {
                    "thread_id": thread_id,
                    "checkpoint_id": checkpoint_config.checkpoint.get("id"),
                    "timestamp": checkpoint_config.metadata.get("time"),
                    "step": checkpoint_config.metadata.get("step"),
                    "source": checkpoint_config.metadata.get("source"),
                }
                checkpoints.append(checkpoint_info)
            return checkpoints
        except Exception as e:
            raise WorkflowException(f"Failed to list checkpoints: {str(e)}")

    async def delete_checkpoint(self, thread_id: str) -> None:
        """Delete all checkpoints for a workflow.

        Args:
            thread_id: Workflow/thread identifier
        """
        try:
            saver = await self.get_saver()
            config = {"configurable": {"thread_id": thread_id}}
            await saver.adelete(config)
        except Exception as e:
            raise WorkflowException(f"Failed to delete checkpoint: {str(e)}")


# Global checkpoint manager instance
_checkpoint_manager: Optional[CheckpointManager] = None


def get_checkpoint_manager() -> CheckpointManager:
    """Get global checkpoint manager instance.

    Returns:
        Checkpoint manager instance
    """
    global _checkpoint_manager
    if _checkpoint_manager is None:
        _checkpoint_manager = CheckpointManager()
    return _checkpoint_manager
