"""Optional Lance materialization backend for verified Domena releases."""

from __future__ import annotations

import hashlib
import os
import shutil
from pathlib import Path
from typing import Any, Mapping, Sequence
from urllib.parse import urlparse
from uuid import uuid4

from .execution import (
    MaterializationReference,
    OptionalDependencyError,
    TransformPlan,
    materialized_schema_fingerprint,
)


def _require_lance() -> tuple[Any, Any]:
    try:
        import lance
        import pyarrow as pa
    except ImportError as exc:
        raise OptionalDependencyError(
            "Lance support requires optional dependencies; install domena[lance] "
            "or domena[ray-lance]"
        ) from exc
    return lance, pa


def _local_path(uri: str) -> Path:
    parsed = urlparse(uri)
    if parsed.scheme not in ("", "file"):
        raise ValueError("M3 Lance publication currently supports local paths and file:// URIs")
    if parsed.scheme == "file":
        return Path(parsed.path)
    return Path(uri)


def _arrow_schema(pa: Any) -> Any:
    return pa.schema(
        [
            pa.field("source_namespace_id", pa.int64(), nullable=False),
            pa.field("source_namespace_name", pa.string(), nullable=False),
            pa.field("episode_id", pa.string(), nullable=False),
            pa.field("episode_fingerprint", pa.string(), nullable=False),
            pa.field("dataset_name", pa.string(), nullable=False),
            pa.field("release_id", pa.string(), nullable=False),
            pa.field("release_fingerprint", pa.string(), nullable=False),
            pa.field("split", pa.string(), nullable=True),
            pa.field("experience_schema_version", pa.string(), nullable=False),
            pa.field("task_id", pa.string(), nullable=False),
            pa.field("outcome_status", pa.string(), nullable=False),
            pa.field("step_count", pa.int64(), nullable=False),
            pa.field("episode_json", pa.string(), nullable=False),
            pa.field("asset_locators_json", pa.string(), nullable=False),
        ]
    )


def _tree_checksum(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
    return digest.hexdigest()


def _verify_table(table: Any, plan: TransformPlan, expected_rows: int) -> None:
    if table.num_rows != expected_rows:
        raise ValueError(
            f"Lance row-count verification failed: expected {expected_rows}, got {table.num_rows}"
        )
    fingerprints = set(table.column("release_fingerprint").to_pylist())
    if fingerprints != {plan.input_release_fingerprint}:
        raise ValueError("Lance release-fingerprint verification failed")


class LanceMaterializer:
    """Stage, verify, and atomically publish canonical rows as a Lance dataset."""

    def materialize(
        self,
        plan: TransformPlan,
        rows: Sequence[Mapping[str, object]],
        output_uri: str,
    ) -> MaterializationReference:
        lance, pa = _require_lance()
        target = _local_path(output_uri).resolve()
        if target.exists():
            raise FileExistsError(f"immutable Lance release already exists: {target}")
        target.parent.mkdir(parents=True, exist_ok=True)
        staging = target.parent / f".{target.name}.staging-{uuid4().hex}"
        try:
            table = pa.Table.from_pylist([dict(row) for row in rows], schema=_arrow_schema(pa))
            lance.write_dataset(table, str(staging), mode="create")
            staged_dataset = lance.dataset(str(staging))
            staged_table = staged_dataset.to_table()
            _verify_table(staged_table, plan, len(rows))
            if not staged_table.schema.equals(_arrow_schema(pa), check_metadata=False):
                raise ValueError("Lance physical schema verification failed")
            os.replace(staging, target)
        except Exception:
            if staging.exists():
                shutil.rmtree(staging)
            raise

        published = lance.dataset(str(target))
        _verify_table(published.to_table(), plan, len(rows))
        return MaterializationReference(
            release_fingerprint=plan.input_release_fingerprint,
            backend_name="lance",
            uri=str(target),
            backend_version=str(published.version),
            schema_fingerprint=materialized_schema_fingerprint(),
            row_count=len(rows),
            checksums=(("dataset_tree_sha256", _tree_checksum(target)),),
        )


class LanceReader:
    """Release-scoped reads that preserve Domena episode identity."""

    def scan(self, reference: MaterializationReference) -> tuple[dict[str, object], ...]:
        lance, _ = _require_lance()
        self._validate_reference(reference)
        rows = lance.dataset(reference.uri).to_table().to_pylist()
        if any(row["release_fingerprint"] != reference.release_fingerprint for row in rows):
            raise ValueError("Lance snapshot contains rows from another Domena release")
        return tuple(rows)

    def lookup(
        self,
        reference: MaterializationReference,
        source_namespace_id: int,
        episode_id: str,
    ) -> dict[str, object] | None:
        for row in self.scan(reference):
            if (
                row["source_namespace_id"] == source_namespace_id
                and row["episode_id"] == episode_id
            ):
                return row
        return None

    @staticmethod
    def _validate_reference(reference: MaterializationReference) -> None:
        if reference.backend_name != "lance":
            raise ValueError("LanceReader requires a Lance materialization reference")
        if reference.schema_fingerprint != materialized_schema_fingerprint():
            raise ValueError("unsupported materialized schema fingerprint")
