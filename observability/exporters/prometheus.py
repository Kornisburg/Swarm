"""Prometheus metrics exporter for The Hive."""

from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry
from typing import Any, Optional


class PrometheusExporter:
    """Prometheus metrics collection and export."""

    def __init__(self):
        """Initialize Prometheus metrics."""
        self.registry = CollectorRegistry()

        # Token usage and cost metrics
        self.tokens_used = Counter(
            "hive_tokens_total",
            "Total tokens consumed",
            ["provider", "model", "agent_type"],
            registry=self.registry,
        )
        self.cost_incurred = Counter(
            "hive_cost_total_usd",
            "Total cost in USD",
            ["provider", "agent_type"],
            registry=self.registry,
        )

        # Workflow performance metrics
        self.workflow_duration = Histogram(
            "hive_workflow_duration_seconds",
            "Workflow duration",
            ["stage"],
            registry=self.registry,
        )
        self.workflow_status = Counter(
            "hive_workflow_status_total",
            "Workflow completion status",
            ["status"],
            registry=self.registry,
        )

        # Agent performance metrics
        self.agent_invocations = Counter(
            "hive_agent_invocations_total",
            "Agent invocations",
            ["agent_type"],
            registry=self.registry,
        )
        self.agent_duration = Histogram(
            "hive_agent_duration_seconds",
            "Agent duration",
            ["agent_type"],
            registry=self.registry,
        )

        # Resource usage metrics
        self.active_workflows = Gauge(
            "hive_active_workflows",
            "Number of active workflows",
            registry=self.registry,
        )
        self.sandbox_containers = Gauge(
            "hive_sandbox_containers",
            "Number of running sandbox containers",
            registry=self.registry,
        )

    def record_token_usage(
        self,
        provider: str,
        model: str,
        agent_type: str,
        tokens: int,
        cost_usd: float,
    ) -> None:
        """Record token usage and cost.

        Args:
            provider: LLM provider name
            model: Model name
            agent_type: Agent type
            tokens: Number of tokens consumed
            cost_usd: Cost in USD
        """
        self.tokens_used.labels(
            provider=provider,
            model=model,
            agent_type=agent_type,
        ).inc(tokens)
        self.cost_incurred.labels(
            provider=provider,
            agent_type=agent_type,
        ).inc(cost_usd)

    def record_workflow_start(self) -> None:
        """Record workflow start."""
        self.active_workflows.inc()

    def record_workflow_complete(self, status: str, duration: float) -> None:
        """Record workflow completion.

        Args:
            status: Final status (COMPLETED, FAILED, CANCELLED)
            duration: Duration in seconds
        """
        self.active_workflows.dec()
        self.workflow_status.labels(status=status).inc()
        self.workflow_duration.labels(stage="total").observe(duration)

    def record_agent_invocation(self, agent_type: str, duration: float) -> None:
        """Record agent invocation.

        Args:
            agent_type: Type of agent
            duration: Duration in seconds
        """
        self.agent_invocations.labels(agent_type=agent_type).inc()
        self.agent_duration.labels(agent_type=agent_type).observe(duration)

    def get_metrics(self) -> dict[str, Any]:
        """Get current metrics values.

        Returns:
            Dictionary of metric values
        """
        return {
            "active_workflows": self.active_workflows._value.get(),
            "sandbox_containers": self.sandbox_containers._value.get(),
        }


# Global Prometheus exporter instance
_prometheus_exporter: Optional[PrometheusExporter] = None


def get_prometheus_exporter() -> PrometheusExporter:
    """Get global Prometheus exporter instance.

    Returns:
        Prometheus exporter instance
    """
    global _prometheus_exporter
    if _prometheus_exporter is None:
        _prometheus_exporter = PrometheusExporter()
    return _prometheus_exporter
