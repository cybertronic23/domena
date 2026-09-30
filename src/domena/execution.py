"""Engine-neutral bounded execution contracts for Domena data releases."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from types import MappingProxyType
from typing import Mapping, Protocol, Sequence, runtime_checkable
from uuid import uuid4

from .dataset import DatasetManifest, fingerprint_manifest, resolve_local_member, validate_manifest
from .serialization import dumps_episode

IDENTITY_TRANSFORM_ID = "domena.identity"
IDENTITY_TRANSFORM_VERSION = "1"
MATERIALIZED_EPISODE_SCHEMA_ID = "domena.materialized-episode-row/v0.1"

_ROW_SCHEMA: tuple[tuple[str, str], ...] = (
    ("source_namespace_id", "int64"),
    ("source_namespace_name", "utf8"),
    ("episode_id", "utf8"),
    ("episode_fingerprint", "utf8"),
    ("dataset_name", "utf8"),
    ("release_id", "utf8"),
    ("release_fingerprint", "utf8"),
    ("split", "utf8?"),
    ("experience_schema_version", "utf8"),
    ("task_id", "utf8"),
    ("outcome_status", "utf8"),
    ("step_count", "int64"),
    ("episode_json", "utf8"),
    ("asset_locators_json", "utf8"),
)


class OptionalDependencyError(RuntimeError):
    """Raised when a requested optional execution backend is not installed."""


class JobStatus(StrEnum):
    """Terminal status of a bounded execution attempt."""

    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _fingerprint(value: object) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _is_sha256_hex(value: str) -> bool:
    if len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


def _validate_json_value(value: object, path: str = "configuration") -> None:
    if value is None or isinstance(value, (str, int, float, bool)):
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _validate_json_value(item, f"{path}[{index}]")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError(f"{path} keys must be strings")
            _validate_json_value(item, f"{path}.{key}")
        return
    raise TypeError(f"{path} must contain only JSON-compatible values")


@dataclass(frozen=True, slots=True)
class TransformPlan:
    """Immutable, fingerprinted declaration of a bounded release transform."""

    input_manifest: DatasetManifest
    transform_id: str
    transform_version: str
    configuration: Mapping[str, object]
    output_schema_id: str

    def __post_init__(self) -> None:
        if not self.transform_id.strip():
            raise ValueError("transform_id must not be empty")
        if not self.transform_version.strip():
            raise ValueError("transform_version must not be empty")
        if not self.output_schema_id.strip():
            raise ValueError("output_schema_id must not be empty")
        configuration = dict(self.configuration)
        _validate_json_value(configuration)
        object.__setattr__(self, "configuration", MappingProxyType(configuration))
        validation = validate_manifest(self.input_manifest)
        if not validation.is_valid:
            raise ValueError(
                "input_manifest is invalid: "
                + "; ".join(f"{issue.path}: {issue.message}" for issue in validation.issues)
            )
        if self.input_manifest.release_fingerprint is None:
            raise ValueError("input_manifest must carry a release_fingerprint")
        if self.input_manifest.release_fingerprint != fingerprint_manifest(self.input_manifest):
            raise ValueError(
                "input_manifest.release_fingerprint does not match its semantic content"
            )
        if (
            self.transform_id != IDENTITY_TRANSFORM_ID
            or self.transform_version != IDENTITY_TRANSFORM_VERSION
        ):
            raise ValueError(
                "unsupported transform; use domena.identity version 1 for the M3 data plane"
            )
        if self.output_schema_id != MATERIALIZED_EPISODE_SCHEMA_ID:
            raise ValueError(
                f"unsupported output schema: {self.output_schema_id}; "
                f"expected {MATERIALIZED_EPISODE_SCHEMA_ID}"
            )
        if configuration:
            raise ValueError("domena.identity version 1 requires an empty configuration")

    @property
    def input_release_fingerprint(self) -> str:
        value = self.input_manifest.release_fingerprint
        assert value is not None
        return value

    @property
    def transform_fingerprint(self) -> str:
        return _fingerprint(
            {
                "transform_id": self.transform_id,
                "transform_version": self.transform_version,
                "configuration": dict(self.configuration),
                "output_schema_id": self.output_schema_id,
            }
        )


@dataclass(frozen=True, slots=True)
class ExecutionOptions:
    """Engine-neutral inputs required to execute and materialize a bounded plan."""

    manifest_directory: str | Path
    output_uri: str

    def __post_init__(self) -> None:
        if not self.output_uri.strip():
            raise ValueError("output_uri must not be empty")


@dataclass(frozen=True, slots=True)
class FailureEvidence:
    code: str
    message: str
    details: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        if not self.code.strip() or not self.message.strip():
            raise ValueError("failure evidence requires non-empty code and message")


@dataclass(frozen=True, slots=True)
class MaterializationReference:
    """Immutable pointer from a Domena release to a verified physical snapshot."""

    release_fingerprint: str
    backend_name: str
    uri: str
    backend_version: str
    schema_fingerprint: str
    row_count: int
    checksums: tuple[tuple[str, str], ...]

    def __post_init__(self) -> None:
        if not _is_sha256_hex(self.release_fingerprint):
            raise ValueError("release_fingerprint must be a SHA-256 hex digest")
        if not _is_sha256_hex(self.schema_fingerprint):
            raise ValueError("schema_fingerprint must be a SHA-256 hex digest")
        if not self.backend_name.strip() or not self.uri.strip():
            raise ValueError("backend_name and uri must not be empty")
        if not self.backend_version.strip():
            raise ValueError("backend_version must not be empty")
        if self.row_count < 0:
            raise ValueError("row_count must be non-negative")


@dataclass(frozen=True, slots=True)
class JobRun:
    """Immutable terminal evidence for one bounded execution attempt."""

    run_id: str
    engine_name: str
    runtime_name: str
    status: JobStatus
    input_release_fingerprint: str
    transform_fingerprint: str
    started_at: str
    finished_at: str
    materialization: MaterializationReference | None = None
    failure: FailureEvidence | None = None

    def __post_init__(self) -> None:
        if not self.run_id.strip() or not self.engine_name.strip() or not self.runtime_name.strip():
            raise ValueError("run_id, engine_name, and runtime_name must not be empty")
        if self.status is JobStatus.SUCCEEDED:
            if self.materialization is None or self.failure is not None:
                raise ValueError("successful JobRun requires materialization and no failure")
            if self.materialization.release_fingerprint != self.input_release_fingerprint:
                raise ValueError("materialization must reference the JobRun input release")
        elif self.materialization is not None or self.failure is None:
            raise ValueError("failed or cancelled JobRun requires failure and no materialization")


@runtime_checkable
class BoundedMaterializer(Protocol):
    def materialize(
        self,
        plan: TransformPlan,
        rows: Sequence[Mapping[str, object]],
        output_uri: str,
    ) -> MaterializationReference: ...


@runtime_checkable
class BoundedExecutor(Protocol):
    def execute(self, plan: TransformPlan, options: ExecutionOptions) -> JobRun: ...


def materialized_schema_fingerprint() -> str:
    """Return the engine-independent logical schema fingerprint for M3 rows."""

    return _fingerprint(
        {"schema_id": MATERIALIZED_EPISODE_SCHEMA_ID, "columns": list(_ROW_SCHEMA)}
    )


def build_transform_rows(
    plan: TransformPlan, manifest_directory: str | Path
) -> tuple[dict[str, object], ...]:
    """Resolve a release and build canonical rows in stable identity order."""

    rows: list[dict[str, object]] = []
    manifest = plan.input_manifest
    for member in manifest.members:
        episode = resolve_local_member(manifest_directory, member)
        if episode is None:
            raise ValueError(
                f"external member locator is not readable by the M3 local source: {member.locator}"
            )
        asset_locators = [
            {
                "asset_id": asset.asset_id,
                "media_type": asset.media_type,
                "uri": asset.uri,
                "checksum": asset.checksum,
            }
            for asset in episode.assets
        ]
        rows.append(
            {
                "source_namespace_id": member.source_namespace.namespace_id,
                "source_namespace_name": member.source_namespace.name,
                "episode_id": member.episode_id,
                "episode_fingerprint": member.episode_fingerprint,
                "dataset_name": manifest.dataset_name,
                "release_id": manifest.release_id,
                "release_fingerprint": plan.input_release_fingerprint,
                "split": member.split,
                "experience_schema_version": episode.schema_version,
                "task_id": episode.task.task_id,
                "outcome_status": episode.outcome.status.value,
                "step_count": len(episode.steps),
                "episode_json": dumps_episode(episode),
                "asset_locators_json": _canonical_json(asset_locators),
            }
        )
    rows.sort(key=lambda row: (int(row["source_namespace_id"]), str(row["episode_id"])))
    return tuple(rows)


class LocalExecutor:
    """Deterministic single-process reference executor."""

    def __init__(self, materializer: BoundedMaterializer) -> None:
        self._materializer = materializer

    def execute(self, plan: TransformPlan, options: ExecutionOptions) -> JobRun:
        run_id = str(uuid4())
        started_at = _utc_now()
        try:
            rows = build_transform_rows(plan, options.manifest_directory)
            materialization = self._materializer.materialize(plan, rows, options.output_uri)
            return JobRun(
                run_id=run_id,
                engine_name="local",
                runtime_name="python",
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
                engine_name="local",
                runtime_name="python",
                status=JobStatus.FAILED,
                input_release_fingerprint=plan.input_release_fingerprint,
                transform_fingerprint=plan.transform_fingerprint,
                started_at=started_at,
                finished_at=_utc_now(),
                failure=FailureEvidence(
                    code=exc.__class__.__name__, message=str(exc) or "local execution failed"
                ),
            )
