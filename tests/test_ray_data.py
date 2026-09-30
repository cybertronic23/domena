from __future__ import annotations

import importlib.util
import shutil
import tempfile
import unittest
from pathlib import Path

from domena import ExecutionOptions, JobStatus, LocalExecutor
from domena.lance_backend import LanceMaterializer, LanceReader
from domena.ray_data import RayDataExecutor, RayDataOptions
from tests.test_execution import CapturingMaterializer, FIXTURE, make_plan

HAS_RAY = importlib.util.find_spec("ray") is not None
HAS_LANCE = (
    importlib.util.find_spec("lance") is not None
    and importlib.util.find_spec("pyarrow") is not None
)


class RayDependencyTests(unittest.TestCase):
    @unittest.skipIf(HAS_RAY, "dependency-error behavior applies only without Ray")
    def test_missing_ray_dependency_is_actionable_failure_evidence(self) -> None:
        run = RayDataExecutor(CapturingMaterializer()).execute(
            make_plan(), ExecutionOptions(".", "memory://ray")
        )
        self.assertEqual(run.status, JobStatus.FAILED)
        assert run.failure is not None
        self.assertEqual(run.failure.code, "OptionalDependencyError")
        self.assertIn("domena[ray]", run.failure.message)


@unittest.skipUnless(HAS_RAY, "install domena[ray] to run Ray Data integration tests")
class RayIntegrationTests(unittest.TestCase):
    def test_ray_and_local_produce_identical_canonical_rows(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            episode_dir = root / "episodes"
            episode_dir.mkdir()
            shutil.copyfile(FIXTURE, episode_dir / FIXTURE.name)
            local_sink = CapturingMaterializer()
            ray_sink = CapturingMaterializer()
            local_run = LocalExecutor(local_sink).execute(
                make_plan(), ExecutionOptions(root, "memory://local")
            )
            ray_run = RayDataExecutor(
                ray_sink, RayDataOptions(batch_size=1)
            ).execute(make_plan(), ExecutionOptions(root, "memory://ray"))

        self.assertEqual(local_run.status, JobStatus.SUCCEEDED)
        self.assertEqual(
            ray_run.status,
            JobStatus.SUCCEEDED,
            msg=f"Ray execution failed: {ray_run.failure!r}",
        )
        self.assertEqual(local_sink.rows, ray_sink.rows)

    def test_failed_publication_never_returns_a_materialization(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            episode_dir = root / "episodes"
            episode_dir.mkdir()
            shutil.copyfile(FIXTURE, episode_dir / FIXTURE.name)
            run = RayDataExecutor(
                CapturingMaterializer(fail=True)
            ).execute(make_plan(), ExecutionOptions(root, "memory://ray"))

        self.assertEqual(run.status, JobStatus.FAILED)
        self.assertIsNone(run.materialization)
        self.assertIsNotNone(run.failure)

    @unittest.skipUnless(
        HAS_LANCE, "install domena[ray-lance] to run Ray-to-Lance integration tests"
    )
    def test_ray_data_publishes_verified_lance_release(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            episode_dir = root / "episodes"
            episode_dir.mkdir()
            shutil.copyfile(FIXTURE, episode_dir / FIXTURE.name)
            output = root / "ray-release.lance"
            run = RayDataExecutor(
                LanceMaterializer(), RayDataOptions(batch_size=1)
            ).execute(make_plan(), ExecutionOptions(root, str(output)))

            self.assertEqual(
                run.status,
                JobStatus.SUCCEEDED,
                msg=f"Ray-to-Lance execution failed: {run.failure!r}",
            )
            assert run.materialization is not None
            row = LanceReader().lookup(run.materialization, 1, "mock-pick-001")
            self.assertIsNotNone(row)
            assert row is not None
            self.assertEqual(row["release_fingerprint"], make_plan().input_release_fingerprint)


if __name__ == "__main__":
    unittest.main()
