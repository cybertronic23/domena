from __future__ import annotations

import importlib.util
import shutil
import tempfile
import unittest
from pathlib import Path

from domena import ExecutionOptions, JobStatus, LocalExecutor, OptionalDependencyError
from domena.lance_backend import LanceMaterializer, LanceReader
from tests.test_execution import FIXTURE, make_plan

HAS_LANCE = (
    importlib.util.find_spec("lance") is not None
    and importlib.util.find_spec("pyarrow") is not None
)


class LanceDependencyTests(unittest.TestCase):
    @unittest.skipIf(HAS_LANCE, "dependency-error behavior applies only without Lance")
    def test_missing_lance_dependency_is_actionable(self) -> None:
        with self.assertRaisesRegex(OptionalDependencyError, r"domena\[lance\]"):
            LanceMaterializer().materialize(make_plan(), (), "unused.lance")


@unittest.skipUnless(HAS_LANCE, "install domena[lance] to run Lance integration tests")
class LanceIntegrationTests(unittest.TestCase):
    def test_local_execution_publishes_and_reads_verified_lance_release(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            episode_dir = root / "episodes"
            episode_dir.mkdir()
            shutil.copyfile(FIXTURE, episode_dir / FIXTURE.name)
            output = root / "release.lance"
            run = LocalExecutor(LanceMaterializer()).execute(
                make_plan(), ExecutionOptions(root, str(output))
            )
            self.assertEqual(run.status, JobStatus.SUCCEEDED)
            assert run.materialization is not None
            row = LanceReader().lookup(run.materialization, 1, "mock-pick-001")
            self.assertIsNotNone(row)
            assert row is not None
            self.assertEqual(row["release_fingerprint"], make_plan().input_release_fingerprint)
            self.assertEqual(run.materialization.row_count, 1)

    def test_existing_release_is_not_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "release.lance"
            target.mkdir()
            with self.assertRaises(FileExistsError):
                LanceMaterializer().materialize(make_plan(), (), str(target))


if __name__ == "__main__":
    unittest.main()
