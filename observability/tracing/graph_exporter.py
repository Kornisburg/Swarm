"""Execution graph visualization and export."""

import json
from typing import Any, Optional

from ..exporters.prometheus import get_prometheus_exporter


class GraphExporter:
    """Export LangGraph execution graph for visualization."""

    def __init__(self):
        """Initialize graph exporter."""
        self.prometheus = get_prometheus_exporter()

    def export_graph_structure(
        self, graph: Any, workflow_id: str
    ) -> dict[str, Any]:
        """Export graph structure as JSON.

        Args:
            graph: LangGraph or StateGraph instance
            workflow_id: Workflow ID

        Returns:
            Graph structure as dictionary
        """
        nodes = []
        edges = []

        try:
            # Extract nodes from graph
            if hasattr(graph, "nodes"):
                for node_name in graph.nodes:
                    nodes.append({
                        "id": node_name,
                        "type": "agent",
                        "workflow_id": workflow_id,
                    })

            # Extract edges from graph
            if hasattr(graph, "edges"):
                for edge in graph.edges:
                    edges.append({
                        "source": edge[0] if isinstance(edge, tuple) else str(edge),
                        "target": edge[1] if isinstance(edge, tuple) else str(edge),
                        "workflow_id": workflow_id,
                    })
        except Exception as e:
            # Return basic structure if extraction fails
            return {
                "workflow_id": workflow_id,
                "nodes": [],
                "edges": [],
                "error": str(e),
            }

        return {
            "workflow_id": workflow_id,
            "nodes": nodes,
            "edges": edges,
        }

    def export_execution_path(
        self,
        workflow_id: str,
        stage_history: list[str],
        current_stage: str,
    ) -> dict[str, Any]:
        """Export execution path through graph.

        Args:
            workflow_id: Workflow ID
            stage_history: List of completed stages
            current_stage: Current stage

        Returns:
            Execution path as dictionary
        """
        path = stage_history.copy()
        if current_stage and current_stage not in path:
            path.append(current_stage)

        return {
            "workflow_id": workflow_id,
            "execution_path": path,
            "current_stage": current_stage,
            "total_stages": len(path),
            "completed_stages": len(stage_history),
        }

    def export_node_states(
        self, workflow_id: str, node_states: dict[str, dict[str, Any]]
    ) -> dict[str, Any]:
        """Export state of each node in graph.

        Args:
            workflow_id: Workflow ID
            node_states: Dictionary of node_name -> state_dict

        Returns:
            Node states as dictionary
        """
        nodes = []

        for node_name, state in node_states.items():
            nodes.append({
                "workflow_id": workflow_id,
                "node_name": node_name,
                "status": state.get("status", "UNKNOWN"),
                "start_time": state.get("start_time"),
                "end_time": state.get("end_time"),
                "duration": state.get("duration"),
                "tokens": state.get("tokens", 0),
            })

        return {
            "workflow_id": workflow_id,
            "nodes": nodes,
        }

    def calculate_progress(
        self, stage_history: list[str], current_stage: str, total_stages: int
    ) -> dict[str, Any]:
        """Calculate workflow progress.

        Args:
            stage_history: List of completed stages
            current_stage: Current stage
            total_stages: Total number of stages

        Returns:
            Progress metrics
        """
        completed = len(stage_history)
        current_stage_index = completed if current_stage in stage_history else completed

        # Stage percent (0-100 for current stage)
        stage_percent = (current_stage_index / total_stages) * 100 if total_stages > 0 else 0

        # Overall percent (including current stage progress)
        overall_percent = min(stage_percent, 100)

        return {
            "completed_stages": completed,
            "total_stages": total_stages,
            "current_stage": current_stage,
            "current_stage_index": current_stage_index,
            "stage_percent_complete": round(stage_percent, 2),
            "overall_percent_complete": round(overall_percent, 2),
            "is_complete": completed >= total_stages,
        }

    def to_mermaid(self, graph_data: dict[str, Any]) -> str:
        """Convert graph data to Mermaid.js syntax.

        Args:
            graph_data: Graph structure from export_graph_structure

        Returns:
            Mermaid.js diagram string
        """
        lines = ["graph TD"]

        # Add nodes
        for node in graph_data.get("nodes", []):
            lines.append(f'    {node["id"]}["{node["id"]}"]')

        # Add edges
        for edge in graph_data.get("edges", []):
            lines.append(f'    {edge["source"]} --> {edge["target"]}')

        return "\n".join(lines)

    def to_json(self, data: dict[str, Any]) -> str:
        """Convert data to JSON string.

        Args:
            data: Data to convert

        Returns:
            JSON string
        """
        return json.dumps(data, indent=2, default=str)


# Global graph exporter instance
_graph_exporter: Optional[GraphExporter] = None


def get_graph_exporter() -> GraphExporter:
    """Get global graph exporter instance.

    Returns:
        Graph exporter instance
    """
    global _graph_exporter
    if _graph_exporter is None:
        _graph_exporter = GraphExporter()
    return _graph_exporter
