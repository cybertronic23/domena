from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path
from typing import Mapping, Sequence

from domena import (
    IDENTITY_TRANSFORM_ID,
    IDENTITY_TRANSFORM_VERSION,
    MATERIALIZED_EPISODE_SCHEMA_ID,
    DatasetManifest,
    DatasetMember,
    Construction,
    ExecutionOptions,
    JobStatus,
    LocalExecutor,
    MaterializationReference,
    SourceNamespace,
    TransformPlan,
    fingerprint_manifest,
    materialized_schema_fingerprint,
)

FIXTURE = Path(__file__).parent / "fixtures" / "m1a-episodes" / "mock-pick-001.json"


class CapturingMaterializer:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.rows: tuple[Mapping[str, object], ...] = ()

    def materialize(
        self,
        plan: TransformPlan,
        rows: Sequence[Mapping[str, object]],
        output_uri: str,
    ) -> MaterializationReference:
        if self.fail:
            raise RuntimeError("publication rejected")
        self.rows = tuple(rows)
        return MaterializationReference(
            release_fingerprint=plan.input_release_fingerprint,
            backend_name="test",
            uri=output_uri,
            backend_version="1",
            schema_fingerprint=materialized_schema_fingerprint(),
            row_count=len(rows),
            checksums=(("rows", "sha256:test"),),
        )


def make_manifest() -> DatasetManifest:
    manifest = DatasetManifest(
        dataset_name="execution-fixture",
        release_id="release-001",
        members=(
            DatasetMember(
                source_namespace=SourceNamespace(1, "domena.mock"),
                episode_id="mock-pick-001",
                episode_fingerprint="533477df1a9b313341d554a3149bf878173eea0c7d65d39d80fc023a721a3237",
                split="train",
                locator="episodes/mock-pick-001.json",
            ),
        ),
        construction=Construction("domena.tests", "0.1"),
    )
    return DatasetManifest(
        dataset_name=manifest.dataset_name,
        release_id=manifest.release_id,
        members=manifest.members,
        construction=manifest.construction,
        release_fingerprint=fingerprint_manifest(manifest),
    )


def make_plan(manifest: DatasetManifest | None = None) -> TransformPlan:
    return TransformPlan(
        input_manifest=manifest or make_manifest(),
        transform_id=IDENTITY_TRANSFORM_ID,
        transform_version=IDENTITY_TRANSFORM_VERSION,
        configuration={},
        output_schema_id=MATERIALIZED_EPISODE_SCHEMA_ID,
    )


class ExecutionContractTests(unittest.TestCase):
    def test_plan_rejects_missing_release_fingerprint(self) -> None:
        manifest = DatasetManifest(
            dataset_name="invalid",
            release_id="release-001",
            members=make_manifest().members,
            construction=Construction("domena.tests", "0.1"),
        )
        with self.assertRaisesRegex(ValueError, "release_fingerprint"):
            make_plan(manifest)

    def test_transform_fingerprint_is_stable(self) -> None:
        self.assertEqual(make_plan().transform_fingerprint, make_plan().transform_fingerprint)

    def test_transform_configuration_is_immutable(self) -> None:
        configuration: dict[str, object] = {}
        plan = TransformPlan(
            input_manifest=make_manifest(),
            transform_id=IDENTITY_TRANSFORM_ID,
            transform_version=IDENTITY_TRANSFORM_VERSION,
            configuration=configuration,
            output_schema_id=MATERIALIZED_EPISODE_SCHEMA_ID,
        )

        configuration["changed_after_creation"] = True

        self.assertEqual(dict(plan.configuration), {})
        with self.assertRaises(TypeError):
            plan.configuration["cannot_mutate"] = True  # type: ignore[index]

    def test_local_executor_builds_canonical_identity_row(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            episode_dir = root / "episodes"
            episode_dir.mkdir()
            shutil.copyfile(FIXTURE, episode_dir / FIXTURE.name)
            materializer = CapturingMaterializer()
            run = LocalExecutor(materializer).execute(
                make_plan(),
                ExecutionOptions(manifest_directory=root, output_uri="memory://release-001"),
            )

        self.assertEqual(run.status, JobStatus.SUCCEEDED)
        self.assertEqual(run.engine_name, "local")
        self.assertEqual(run.runtime_name, "python")
        self.assertIsNotNone(run.materialization)
        self.assertEqual(len(materializer.rows), 1)
        row = materializer.rows[0]
        self.assertEqual(row["source_namespace_id"], 1)
        self.assertEqual(row["episode_id"], "mock-pick-001")
        self.assertEqual(row["release_fingerprint"], make_plan().input_release_fingerprint)
        self.assertEqual(row["step_count"], 2)
        self.assertIn('"schema_version":"domena.experience/v0.1"', str(row["episode_json"]))

    def test_failed_publication_returns_failure_evidence_without_reference(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            episode_dir = root / "episodes"
            episode_dir.mkdir()
            shutil.copyfile(FIXTURE, episode_dir / FIXTURE.name)
            run = LocalExecutor(CapturingMaterializer(fail=True)).execute(
                make_plan(),
                ExecutionOptions(manifest_directory=root, output_uri="memory://release-001"),
            )

        self.assertEqual(run.status, JobStatus.FAILED)
        self.assertIsNone(run.materialization)
        self.assertIsNotNone(run.failure)
        assert run.failure is not None
        self.assertEqual(run.failure.code, "RuntimeError")
        self.assertIn("publication rejected", run.failure.message)


if __name__ == "__main__":
    unittest.main()
