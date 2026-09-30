"""Optional Ray Data executor for bounded Domena transform plans."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from .execution import (
    BoundedMaterializer,
    ExecutionOptions,
    FailureEvidence,
    JobRun,
    JobStatus,
    OptionalDependencyError,
    TransformPlan,
    build_transform_rows,
)


def _require_ray() -> Any:
    try:
        import ray
        import ray.data
    except ModuleNotFoundError as exc:
        missing_module = exc.name or "an unknown module"
        raise OptionalDependencyError(
            "Ray Data execution is missing a required module "
            f"({missing_module}); install domena[ray] or domena[ray-lance] "
            "in the Python environment running Domena"
        ) from exc
    return ray


def _identity_batch(batch: Any) -> Any:
    """Approved M3 identity operator; kept top-level for worker serialization."""

    return batch


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


@dataclass(frozen=True, slots=True)
class RayDataOptions:
    """Ray-specific physical settings kept outside the engine-neutral plan."""

    batch_size: int = 256
    num_cpus: float | None = None
    num_gpus: float | None = None
    address: str | None = None

    def __post_init__(self) -> None:
        if self.batch_size <= 0:
            raise ValueError("batch_size must be positive")
        if self.num_cpus is not None and self.num_cpus <= 0:
            raise ValueError("num_cpus must be positive when provided")
        if self.num_gpus is not None and self.num_gpus < 0:
            raise ValueError("num_gpus must be non-negative when provided")


class RayDataExecutor:
    """Execute approved deterministic transforms with Ray Data, then publish centrally."""

    def __init__(
        self,
        materializer: BoundedMaterializer,
        options: RayDataOptions | None = None,
    ) -> None:
        self._materializer = materializer
        self._options = options or RayDataOptions()

    def execute(self, plan: TransformPlan, options: ExecutionOptions) -> JobRun:
        run_id = str(uuid4())
        started_at = _utc_now()
        ray: Any | None = None
        started_runtime = False
        try:
            ray = _require_ray()
            if not ray.is_initialized():
                init_options: dict[str, object] = {
                    "ignore_reinit_error": True,
                    "include_dashboard": False,
                }
                if self._options.address is not None:
                    init_options["address"] = self._options.address
                ray.init(**init_options)
                started_runtime = True

            source_rows = list(build_transform_rows(plan, options.manifest_directory))
            dataset = ray.data.from_items(source_rows)
            operator_options: dict[str, object] = {
                "batch_size": self._options.batch_size,
                "batch_format": "pyarrow",
            }
            if self._options.num_cpus is not None:
                operator_options["num_cpus"] = self._options.num_cpus
            if self._options.num_gpus is not None:
                operator_options["num_gpus"] = self._options.num_gpus
            transformed = dataset.map_batches(_identity_batch, **operator_options)
            rows = transformed.take_all()
            rows.sort(
                key=lambda row: (int(row["source_namespace_id"]), str(row["episode_id"]))
            )
            materialization = self._materializer.materialize(plan, rows, options.output_uri)
            return JobRun(
                run_id=run_id,
                engine_name="ray-data",
                runtime_name="ray",
                status=JobStatus.SUCCEEDED,
                input_release_fingerprint=plan.input_release_fingerprint,
                transform_fingerprint=plan.transform_fingerprint,
                started_at=started_at,
                finished_at=_utc_now(),
                materialization=materialization,
            )
        except Exception as exc:
            return JobRun(
                run_id=run_id,
                engine_name="ray-data",
                runtime_name="ray",
                status=JobStatus.FAILED,
                input_release_fingerprint=plan.input_release_fingerprint,
                transform_fingerprint=plan.transform_fingerprint,
                started_at=started_at,
                finished_at=_utc_now(),
                failure=FailureEvidence(
                    code=exc.__class__.__name__, message=str(exc) or "Ray Data execution failed"
                ),
            )
        finally:
            if started_runtime and ray is not None:
                ray.shutdown()
