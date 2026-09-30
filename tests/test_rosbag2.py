import tempfile
import unittest
from pathlib import Path

from domena.contract import AssetReference
from domena.rosbag2 import (
    CONVERSION_EXTENSION_KEY,
    ChannelGroup,
    Rosbag2DependencyError,
    RosbagImportPlan,
    RosbagMessageRecord,
    RosbagSegment,
    TopicBinding,
    convert_rosbag_records,
    import_ros2_mcap,
    validate_import_plan,
)
from domena.validation import validate_episode


CHECKSUM = "a" * 64


def bindings() -> tuple[TopicBinding, ...]:
    return (
        TopicBinding("/joint_states", ChannelGroup.OBSERVATIONS, "joint_state"),
        TopicBinding("/imu", ChannelGroup.STATE, "imu"),
        TopicBinding("/cmd_vel", ChannelGroup.ACTIONS, "cmd_vel"),
        TopicBinding("/tf", ChannelGroup.FEEDBACK, "tf"),
        TopicBinding("/camera", ChannelGroup.OBSERVATIONS, "camera"),
        TopicBinding("/points", ChannelGroup.OBSERVATIONS, "points"),
    )


def plan(**changes: object) -> RosbagImportPlan:
    values: dict[str, object] = {
        "task_id": "pick-cup",
        "source_namespace": "example.robot.alpha",
        "topic_bindings": bindings(),
        "whole_bag_episode_id": "episode-whole",
    }
    values.update(changes)
    return RosbagImportPlan(**values)  # type: ignore[arg-type]


class Rosbag2ConversionTests(unittest.TestCase):
    def test_whole_bag_converts_known_messages_and_preserves_opaque_payloads(self) -> None:
        records = (
            RosbagMessageRecord(
                "/joint_states",
                "sensor_msgs/msg/JointState",
                100,
                {"header": {"stamp": {"sec": 1, "nanosec": 0}}, "name": ["joint_a"], "position": [0.2], "velocity": [], "effort": []},
                0,
            ),
            RosbagMessageRecord(
                "/camera",
                "sensor_msgs/msg/Image",
                200,
                {"height": 2, "width": 3, "encoding": "rgb8", "data": b"never-inline"},
                1,
            ),
            RosbagMessageRecord(
                "/imu",
                "sensor_msgs/msg/Imu",
                300,
                {"header": {"stamp": {"sec": 0, "nanosec": 250}}, "orientation": {"x": 0, "y": 0, "z": 0, "w": 1}, "angular_velocity": {"x": 1, "y": 2, "z": 3}, "linear_acceleration": {"x": 4, "y": 5, "z": 6}},
                2,
            ),
            RosbagMessageRecord(
                "/cmd_vel",
                "geometry_msgs/msg/Twist",
                400,
                {"linear": {"x": 0.1, "y": 0, "z": 0}, "angular": {"x": 0, "y": 0, "z": 0.2}},
                3,
            ),
            RosbagMessageRecord(
                "/tf",
                "tf2_msgs/msg/TFMessage",
                500,
                {"transforms": [{"header": {"frame_id": "base"}, "child_frame_id": "camera", "transform": {"translation": {"x": 1, "y": 2, "z": 3}, "rotation": {"x": 0, "y": 0, "z": 0, "w": 1}}}]},
                4,
            ),
            RosbagMessageRecord("/points", "sensor_msgs/msg/PointCloud2", 600, {"data": b"opaque"}, 5),
        )

        (episode,) = convert_rosbag_records(records, plan(), source_path="recording.mcap", source_checksum=CHECKSUM)

        self.assertTrue(validate_episode(episode).is_valid)
        self.assertEqual([step.timestamp_ns for step in episode.steps], [200, 250, 400, 500, 600, 1_000_000_000])
        self.assertEqual(episode.steps[-1].observations["joint_state"]["position"], [0.2])
        self.assertEqual(episode.steps[1].state["imu"]["orientation"]["w"], 1)
        self.assertEqual(episode.steps[2].actions["cmd_vel"]["angular"]["z"], 0.2)
        self.assertEqual(episode.steps[3].feedback["tf"]["transforms"][0]["child_frame_id"], "camera")
        self.assertIsInstance(episode.steps[0].observations["camera"], AssetReference)
        self.assertIsInstance(episode.steps[4].observations["points"], AssetReference)
        self.assertEqual(len(episode.assets), 2)
        self.assertTrue(episode.assets[0].uri.startswith("mcap://"))
        evidence = episode.extensions[CONVERSION_EXTENSION_KEY]
        self.assertEqual(evidence["adapter"], "domena.rosbag2")
        self.assertEqual(evidence["topic_bindings"][0], {
            "topic": "/joint_states",
            "channel_group": "observations",
            "channel_name": "joint_state",
        })
        self.assertEqual(
            evidence["message_type_inventory"],
            [
                "geometry_msgs/msg/Twist",
                "sensor_msgs/msg/Image",
                "sensor_msgs/msg/Imu",
                "sensor_msgs/msg/JointState",
                "sensor_msgs/msg/PointCloud2",
                "tf2_msgs/msg/TFMessage",
            ],
        )
        self.assertEqual(evidence["records"][0]["timestamp_source"], "record_time_fallback")
        self.assertEqual(evidence["records"][-1]["timestamp_source"], "header_stamp")
        self.assertEqual(evidence["records"][0]["payload_metadata"]["width"], 3)

    def test_explicit_segments_are_half_open_and_do_not_heuristically_split(self) -> None:
        records = (
            RosbagMessageRecord("/cmd_vel", "geometry_msgs/msg/Twist", 50, {"linear": {}, "angular": {}}, 0),
            RosbagMessageRecord("/cmd_vel", "geometry_msgs/msg/Twist", 100, {"linear": {}, "angular": {}}, 1),
            RosbagMessageRecord("/cmd_vel", "geometry_msgs/msg/Twist", 199, {"linear": {}, "angular": {}}, 2),
            RosbagMessageRecord("/cmd_vel", "geometry_msgs/msg/Twist", 200, {"linear": {}, "angular": {}}, 3),
        )
        segmented_plan = plan(
            whole_bag_episode_id=None,
            segments=(RosbagSegment("episode-a", 0, 100), RosbagSegment("episode-b", 100, 200)),
        )

        episodes = convert_rosbag_records(records, segmented_plan, source_path="recording.mcap", source_checksum=CHECKSUM)

        self.assertEqual([episode.episode_id for episode in episodes], ["episode-a", "episode-b"])
        self.assertEqual([len(episode.steps) for episode in episodes], [1, 2])
        self.assertEqual(episodes[1].extensions[CONVERSION_EXTENSION_KEY]["boundary"], {"kind": "record_time_range", "start_time_ns": 100, "end_time_ns": 200})

    def test_invalid_plan_boundaries_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            validate_import_plan(plan(whole_bag_episode_id=None, segments=()))
        with self.assertRaises(ValueError):
            validate_import_plan(plan(segments=(RosbagSegment("a", 0, 10),)))
        with self.assertRaises(ValueError):
            validate_import_plan(
                plan(
                    whole_bag_episode_id=None,
                    segments=(RosbagSegment("a", 0, 10), RosbagSegment("b", 9, 20)),
                )
            )

    def test_missing_optional_reader_has_a_clear_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "empty.mcap"
            path.touch()
            with self.assertRaises(Rosbag2DependencyError):
                import_ros2_mcap(path, plan())


if __name__ == "__main__":
    unittest.main()
