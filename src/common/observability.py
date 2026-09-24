import json
import logging
import os
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


def _get_memory_mb() -> float:
    """Get current process RSS memory in MB."""
    try:
        import resource
        # macOS/Linux: ru_maxrss is in bytes on Linux, KB on macOS
        usage = resource.getrusage(resource.RUSAGE_SELF)
        import platform
        if platform.system() == "Darwin":
            return usage.ru_maxrss / (1024 * 1024)  # bytes → MB
        return usage.ru_maxrss / 1024  # KB → MB
    except Exception:
        return 0.0


@dataclass
class StageMetrics:
    """Metrics for a single pipeline stage."""
    name: str
    start_time: float = 0.0
    end_time: float = 0.0
    duration_seconds: float = 0.0
    memory_start_mb: float = 0.0
    memory_end_mb: float = 0.0
    records_processed: int = 0
    error: Optional[str] = None
    extra: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "duration_seconds": round(self.duration_seconds, 2),
            "memory_start_mb": round(self.memory_start_mb, 1),
            "memory_end_mb": round(self.memory_end_mb, 1),
            "memory_delta_mb": round(self.memory_end_mb - self.memory_start_mb, 1),
            "records_processed": self.records_processed,
            "error": self.error,
            **self.extra,
        }


class PipelineReport:
    """
    Accumulates metrics across pipeline stages and generates a summary report.

    Usage as context manager per stage, or manual start/stop.
    """

    def __init__(self, pipeline_name: str, output_dir: str = "data/logs"):
        self.pipeline_name = pipeline_name
        self.output_dir = Path(output_dir)
        self.stages: list[StageMetrics] = []
        self.global_metrics: dict[str, Any] = {}
        self.start_time = time.time()
        self.start_memory = _get_memory_mb()

    @contextmanager
    def stage(self, name: str):
        """
        Context manager that times a pipeline stage and tracks memory.

        Usage:
            with report.stage("extract"):
                extract_data()
        """
        metrics = StageMetrics(name=name)
        metrics.start_time = time.time()
        metrics.memory_start_mb = _get_memory_mb()

        logger.info("▶ [%s] %s — iniciando...", self.pipeline_name, name)

        try:
            yield metrics
        except Exception as exc:
            metrics.error = str(exc)
            logger.error("✗ [%s] %s — falhou: %s", self.pipeline_name, name, exc)
            raise
        finally:
            metrics.end_time = time.time()
            metrics.duration_seconds = metrics.end_time - metrics.start_time
            metrics.memory_end_mb = _get_memory_mb()
            self.stages.append(metrics)

            status = "✓" if metrics.error is None else "✗"
            logger.info(
                "%s [%s] %s — %.1fs | mem: %.0f→%.0f MB | registros: %d",
                status, self.pipeline_name, name,
                metrics.duration_seconds,
                metrics.memory_start_mb, metrics.memory_end_mb,
                metrics.records_processed,
            )

    def record(self, key: str, value: Any) -> None:
        """Record a global metric (not tied to a specific stage)."""
        self.global_metrics[key] = value

    def record_stage_metric(self, key: str, value: Any) -> None:
        """Record a metric on the most recent stage."""
        if self.stages:
            self.stages[-1].extra[key] = value

    def summary(self) -> dict:
        """Generate full summary report as a dictionary."""
        total_duration = time.time() - self.start_time
        end_memory = _get_memory_mb()

        return {
            "pipeline": self.pipeline_name,
            "timestamp": datetime.now().isoformat(),
            "total_duration_seconds": round(total_duration, 2),
            "total_stages": len(self.stages),
            "failed_stages": sum(1 for s in self.stages if s.error is not None),
            "memory": {
                "start_mb": round(self.start_memory, 1),
                "end_mb": round(end_memory, 1),
                "peak_mb": round(max((s.memory_end_mb for s in self.stages), default=0), 1),
            },
            "stages": [s.to_dict() for s in self.stages],
            "metrics": self.global_metrics,
        }

    def save(self) -> Path:
        """Save the report as a JSON file and return the path."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"pipeline_report_{self.pipeline_name}_{timestamp}.json"
        path = self.output_dir / filename

        report = self.summary()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        logger.info("📊 Report salvo: %s", path)
        self._log_summary(report)
        return path

    def _log_summary(self, report: dict) -> None:
        """Log a human-readable summary to the console."""
        logger.info("=" * 60)
        logger.info("📊 PIPELINE REPORT — %s", self.pipeline_name)
        logger.info("=" * 60)
        logger.info("  Duração total : %.1fs", report["total_duration_seconds"])
        logger.info("  Stages        : %d (%d falhas)", report["total_stages"], report["failed_stages"])
        logger.info("  Memória       : %.0f → %.0f MB (pico: %.0f MB)",
                    report["memory"]["start_mb"],
                    report["memory"]["end_mb"],
                    report["memory"]["peak_mb"])
        logger.info("-" * 60)
        for stage in report["stages"]:
            status = "✓" if stage["error"] is None else "✗"
            logger.info(
                "  %s %-30s %6.1fs  %+.0f MB  %d registros",
                status, stage["name"],
                stage["duration_seconds"],
                stage["memory_delta_mb"],
                stage["records_processed"],
            )
        if report["metrics"]:
            logger.info("-" * 60)
            for k, v in report["metrics"].items():
                logger.info("  %s: %s", k, v)
        logger.info("=" * 60)
