"""Project context management for The Hive."""

import json
from datetime import datetime, timezone
from typing import Any, Optional

from .client import get_postgres_client
from .models import ProjectContext
from ..config import get_settings


class ProjectContextManager:
    """Manage project context for cross-session memory."""

    def __init__(self):
        """Initialize project context manager."""
        self.postgres = get_postgres_client()

    async def create_project(
        self,
        name: str,
        description: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> ProjectContext:
        """Create a new project context.

        Args:
            name: Project name
            description: Project description
            metadata: Optional project metadata

        Returns:
            Created project context
        """
        try:
            async with self.postgres.get_session() as session:
                project = ProjectContext(
                    name=name,
                    description=description,
                    metadata_json=json.dumps(metadata or {}),
                    created_at=datetime.now(timezone.utc),
                )
                session.add(project)
                await session.commit()
                await session.refresh(project)
                return project
        except Exception as e:
            raise Exception(f"Failed to create project context: {str(e)}")

    async def get_project(self, project_id: int) -> Optional[ProjectContext]:
        """Get project by ID.

        Args:
            project_id: Project ID

        Returns:
            Project context or None
        """
        try:
            async with self.postgres.get_session() as session:
                from sqlalchemy import select
                result = await session.execute(
                    select(ProjectContext).where(ProjectContext.id == project_id)
                )
                return result.scalar_one_or_none()
        except Exception as e:
            raise Exception(f"Failed to get project: {str(e)}")

    async def get_project_by_name(self, name: str) -> Optional[ProjectContext]:
        """Get project by name.

        Args:
            name: Project name

        Returns:
            Project context or None
        """
        try:
            async with self.postgres.get_session() as session:
                from sqlalchemy import select
                result = await session.execute(
                    select(ProjectContext).where(ProjectContext.name == name)
                )
                return result.scalar_one_or_none()
        except Exception as e:
            raise Exception(f"Failed to get project by name: {str(e)}")

    async def list_projects(self, limit: int = 100) -> list[ProjectContext]:
        """List all projects.

        Args:
            limit: Maximum number of projects to return

        Returns:
            List of project contexts
        """
        try:
            async with self.postgres.get_session() as session:
                from sqlalchemy import select
                result = await session.execute(
                    select(ProjectContext)
                    .order_by(ProjectContext.updated_at.desc())
                    .limit(limit)
                )
                return list(result.scalars().all())
        except Exception as e:
            raise Exception(f"Failed to list projects: {str(e)}")

    async def update_project(
        self,
        project_id: int,
        description: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> ProjectContext:
        """Update project context.

        Args:
            project_id: Project ID
            description: New description
            metadata: New metadata

        Returns:
            Updated project context
        """
        try:
            async with self.postgres.get_session() as session:
                from sqlalchemy import select
                result = await session.execute(
                    select(ProjectContext).where(ProjectContext.id == project_id)
                )
                project = result.scalar_one_or_none()

                if project is None:
                    raise ValueError(f"Project {project_id} not found")

                if description is not None:
                    project.description = description
                if metadata is not None:
                    project.metadata_json = json.dumps(metadata)

                project.updated_at = datetime.now(timezone.utc)

                await session.commit()
                await session.refresh(project)
                return project
        except Exception as e:
            raise Exception(f"Failed to update project: {str(e)}")

    async def delete_project(self, project_id: int) -> None:
        """Delete a project context.

        Args:
            project_id: Project ID
        """
        try:
            async with self.postgres.get_session() as session:
                from sqlalchemy import select, delete
                result = await session.execute(
                    select(ProjectContext).where(ProjectContext.id == project_id)
                )
                project = result.scalar_one_or_none()

                if project is None:
                    raise ValueError(f"Project {project_id} not found")

                await session.execute(
                    delete(ProjectContext).where(ProjectContext.id == project_id)
                )
                await session.commit()
        except Exception as e:
            raise Exception(f"Failed to delete project: {str(e)}")

    async def get_project_workflows(self, project_id: int) -> list[Any]:
        """Get all workflows for a project.

        Args:
            project_id: Project ID

        Returns:
            List of workflow sessions
        """
        try:
            async with self.postgres.get_session() as session:
                from sqlalchemy import select
                from .models import WorkflowSession

                result = await session.execute(
                    select(WorkflowSession)
                    .where(WorkflowSession.project_id == project_id)
                    .order_by(WorkflowSession.created_at.desc())
                )
                return list(result.scalars().all())
        except Exception as e:
            raise Exception(f"Failed to get project workflows: {str(e)}")

    async def get_project_timeline(
        self, project_id: int, limit: int = 50
    ) -> dict[str, Any]:
        """Get timeline of project activity.

        Args:
            project_id: Project ID
            limit: Maximum items per category

        Returns:
            Timeline with decisions, artifacts, and workflows
        """
        try:
            async with self.postgres.get_session() as session:
                from sqlalchemy import select
                from .models import DecisionRecord, Artifact, WorkflowSession

                # Get decisions
                decisions_result = await session.execute(
                    select(DecisionRecord)
                    .where(DecisionRecord.project_id == project_id)
                    .order_by(DecisionRecord.timestamp.desc())
                    .limit(limit)
                )
                decisions = list(decisions_result.scalars().all())

                # Get artifacts
                artifacts_result = await session.execute(
                    select(Artifact)
                    .where(Artifact.project_id == project_id)
                    .order_by(Artifact.created_at.desc())
                    .limit(limit)
                )
                artifacts = list(artifacts_result.scalars().all())

                # Get workflows
                workflows_result = await session.execute(
                    select(WorkflowSession)
                    .where(WorkflowSession.project_id == project_id)
                    .order_by(WorkflowSession.created_at.desc())
                    .limit(limit)
                )
                workflows = list(workflows_result.scalars().all())

                return {
                    "project_id": project_id,
                    "decisions": decisions,
                    "artifacts": artifacts,
                    "workflows": workflows,
                }
        except Exception as e:
            raise Exception(f"Failed to get project timeline: {str(e)}")


# Global project context manager instance
_project_context_manager: Optional[ProjectContextManager] = None


def get_project_context_manager() -> ProjectContextManager:
    """Get global project context manager instance.

    Returns:
        Project context manager instance
    """
    global _project_context_manager
    if _project_context_manager is None:
        _project_context_manager = ProjectContextManager()
    return _project_context_manager
