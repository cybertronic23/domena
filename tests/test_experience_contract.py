import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from domena import (
    AssetReference,
    Episode,
    Outcome,
    OutcomeStatus,
    Step,
    TaskContext,
    dumps_episode,
    inspect_episode,
    loads_episode,
    make_mock_episode,
    read_episode,
    validate_episode,
    write_episode,
)


class ExperienceContractTests(unittest.TestCase):
    def test_mock_episode_is_valid_and_inspectable(self) -> None:
        episode = make_mock_episode()

        result = validate_episode(episode)
        inspection = inspect_episode(episode)

        self.assertTrue(result.is_valid)
        self.assertEqual(inspection.step_count, 2)
        self.assertEqual(inspection.timestamp_count, 2)
        self.assertEqual(inspection.asset_count, 2)
        self.assertEqual(inspection.observation_channels, ("front_rgb",))
        self.assertEqual(inspection.action_channels, ("gripper",))

    def test_round_trip_preserves_asset_references_and_extensions(self) -> None:
        original = make_mock_episode()

        restored = loads_episode(dumps_episode(original))

        self.assertEqual(restored, original)
        self.assertEqual(restored.steps[0].observations["front_rgb"], AssetReference("front-image-0"))

    def test_file_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "episode.json"
            write_episode(make_mock_episode(), path)
            self.assertEqual(read_episode(path), make_mock_episode())

    def test_reports_sequence_time_and_asset_problems(self) -> None:
        original = make_mock_episode()
        bad_steps = (
            replace(original.steps[0], index=1, timestamp_ns=20),
            replace(original.steps[1], index=4, timestamp_ns=10, observations={"missing": AssetReference("absent")}),
        )
        episode = replace(original, steps=bad_steps)

        codes = {issue.code for issue in validate_episode(episode).issues}

        self.assertTrue({"invalid_step_order", "decreasing_timestamp", "unknown_asset"} <= codes)

    def test_reports_schema_and_extension_problems(self) -> None:
        episode = replace(make_mock_episode(), schema_version="other/v1", extensions={"no_namespace": True})

        result = validate_episode(episode)

        self.assertFalse(result.is_valid)
        self.assertEqual({issue.code for issue in result.issues}, {"unsupported_schema", "unnamespaced_extension"})

    def test_accepts_minimal_episode_without_optional_modalities(self) -> None:
        episode = Episode(
            episode_id="minimal",
            task=TaskContext(task_id="observe"),
            outcome=Outcome(status=OutcomeStatus.UNKNOWN),
        )

        self.assertTrue(validate_episode(episode).is_valid)
        self.assertEqual(loads_episode(dumps_episode(episode)), episode)

    def test_rejects_non_json_channel_values_during_validation_and_write(self) -> None:
        episode = replace(make_mock_episode(), steps=(Step(index=0, observations={"bad": {1, 2}}),))

        result = validate_episode(episode)

        self.assertIn("non_json_value", {issue.code for issue in result.issues})
        with self.assertRaises(ValueError):
            dumps_episode(episode)


if __name__ == "__main__":
    unittest.main()
