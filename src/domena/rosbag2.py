"""ROS 2 MCAP import adapter for the source-neutral Domena contract.

The adapter deliberately keeps ROS/MCAP imports at the I/O boundary.  Pure
conversion helpers accept :class:`RosbagMessageRecord` values so they remain
testable without a ROS installation or an MCAP fixture.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from hashlib import sha256
from pathlib import Path
from typing import Any, Iterable, Mapping
from urllib.parse import quote

from .contract import Asset, AssetReference, Episode, Step, TaskContext

CONVERSION_EXTENSION_KEY = "io.domena.rosbag2:conversion"


class Rosbag2DependencyError(ImportError):
    """Raised when the optional ROS 2 MCAP adapter dependencies are absent."""


class ChannelGroup(StrEnum):
    """Domena step channel groups supported by an explicit topic binding."""

    OBSERVATIONS = "observations"
    ACTIONS = "actions"
    STATE = "state"
    FEEDBACK = "feedback"


@dataclass(frozen=True, slots=True)
class TopicBinding:
    """Map one ROS topic to a source-neutral Domena step channel."""

    topic: str
    channel_group: ChannelGroup
    channel_name: str


@dataclass(frozen=True, slots=True)
class RosbagSegment:
    """An explicitly declared half-open record-time range for one episode."""

    episode_id: str
    start_time_ns: int
    end_time_ns: int


@dataclass(frozen=True, slots=True)
class RosbagImportPlan:
    """Immutable caller-owned rules for importing a ROS 2 MCAP file."""

    task_id: str
    source_namespace: str
    topic_bindings: tuple[TopicBinding, ...]
    whole_bag_episode_id: str | None = None
    segments: tuple[RosbagSegment, ...] = ()
    task_success_criteria: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class RosbagMessageRecord:
    """One decoded ROS message plus MCAP record metadata.

    ``message`` can be a decoded ROS object or a mapping, which makes the
    transformation independent from ROS in unit tests and custom ingest jobs.
    """

    topic: str
    message_type: str
    record_time_ns: int
    message: Any
    sequence: int


def validate_import_plan(plan: RosbagImportPlan) -> None:
    """Reject ambiguous or malformed episode-boundary and topic rules."""
    if not plan.task_id.strip():
        raise ValueError("task_id must be non-empty")
    if not plan.source_namespace.strip():
        raise ValueError("source_namespace must be non-empty")
    if not plan.topic_bindings:
        raise ValueError("at least one topic binding is required")
    whole_bag = plan.whole_bag_episode_id is not None
    if whole_bag == bool(plan.segments):
        raise ValueError("declare exactly one of whole_bag_episode_id or segments")
    if whole_bag and not plan.whole_bag_episode_id.strip():
        raise ValueError("whole_bag_episode_id must be non-empty")

    topics: set[str] = set()
    for binding in plan.topic_bindings:
        if not binding.topic.strip() or not binding.channel_name.strip():
            raise ValueError("topic bindings require non-empty topic and channel_name")
        if binding.topic in topics:
            raise ValueError(f"duplicate topic binding for {binding.topic!r}")
        topics.add(binding.topic)

    previous_end: int | None = None
    episode_ids: set[str] = set()
    for segment in plan.segments:
        if not segment.episode_id.strip():
            raise ValueError("segment episode_id must be non-empty")
        if segment.episode_id in episode_ids:
            raise ValueError(f"duplicate segment episode_id {segment.episode_id!r}")
        if segment.start_time_ns >= segment.end_time_ns:
            raise ValueError("segment ranges must be non-empty half-open intervals")
        if previous_end is not None and segment.start_time_ns < previous_end:
            raise ValueError("segments must be ordered and non-overlapping")
        episode_ids.add(segment.episode_id)
        previous_end = segment.end_time_ns


def convert_rosbag_records(
    records: Iterable[RosbagMessageRecord],
    plan: RosbagImportPlan,
    *,
    source_path: str,
    source_checksum: str,
) -> tuple[Episode, ...]:
    """Convert selected decoded ROS records to valid Domena episodes.

    Message selection is driven only by the explicit plan.  Steps are sorted
    by effective Domena timestamp, then MCAP record time/topic/sequence so
    they always meet the core contract's non-decreasing timestamp invariant.
    """
    validate_import_plan(plan)
    if len(source_checksum) != 64 or any(char not in "0123456789abcdef" for char in source_checksum):
        raise ValueError("source_checksum must be a lowercase SHA-256 hexadecimal digest")

    bindings = {binding.topic: binding for binding in plan.topic_bindings}
    selected = [record for record in records if record.topic in bindings]
    if plan.whole_bag_episode_id is not None:
        return (_build_episode(plan.whole_bag_episode_id, selected, bindings, plan, source_path, source_checksum, None),)
    return tuple(
        _build_episode(
            segment.episode_id,
            [record for record in selected if segment.start_time_ns <= record.record_time_ns < segment.end_time_ns],
            bindings,
            plan,
            source_path,
            source_checksum,
            segment,
        )
        for segment in plan.segments
    )


def import_ros2_mcap(path: str | Path, plan: RosbagImportPlan) -> tuple[Episode, ...]:
    """Read a ROS 2 MCAP file through the optional ``domena[rosbag2]`` extra."""
    validate_import_plan(plan)
    try:
        from mcap_ros2.reader import read_ros2_messages
    except ImportError as error:  # pragma: no cover - exercised without optional dependency
        raise Rosbag2DependencyError(
            "ROS 2 MCAP import requires the optional dependency; install domena[rosbag2]"
        ) from error

    source = Path(path)
    checksum = _file_sha256(source)
    records: list[RosbagMessageRecord] = []
    with source.open("rb") as stream:
        for sequence, item in enumerate(read_ros2_messages(stream)):
            channel = getattr(item, "channel")
            message_record = getattr(item, "message")
            schema = getattr(item, "schema", None)
            records.append(
                RosbagMessageRecord(
                    topic=str(getattr(channel, "topic")),
                    message_type=str(getattr(schema, "name", None) or getattr(channel, "message_encoding", "unknown")),
                    record_time_ns=int(getattr(message_record, "log_time")),
                    message=getattr(item, "ros_msg"),
                    sequence=sequence,
                )
            )
    return convert_rosbag_records(records, plan, source_path=str(source), source_checksum=checksum)


def _build_episode(
    episode_id: str,
    records: list[RosbagMessageRecord],
    bindings: Mapping[str, TopicBinding],
    plan: RosbagImportPlan,
    source_path: str,
    source_checksum: str,
    segment: RosbagSegment | None,
) -> Episode:
    converted: list[tuple[int, int, str, int, TopicBinding, Any, RosbagMessageRecord, str]] = []
    for record in records:
        timestamp, timestamp_source = _effective_timestamp(record)
        converted.append((timestamp, record.record_time_ns, record.topic, record.sequence, bindings[record.topic], record.message, record, timestamp_source))
    converted.sort(key=lambda item: item[:4])

    assets: list[Asset] = []
    conversion_records: list[dict[str, Any]] = []
    steps: list[Step] = []
    for index, (timestamp, _record_time, _topic, _sequence, binding, message, record, timestamp_source) in enumerate(converted):
        value, new_assets, payload_metadata = _convert_message(record, message, source_checksum)
        assets.extend(new_assets)
        channels: dict[str, dict[str, Any]] = {group.value: {} for group in ChannelGroup}
        channels[binding.channel_group.value][binding.channel_name] = value
        steps.append(
            Step(
                index=index,
                timestamp_ns=timestamp,
                observations=channels[ChannelGroup.OBSERVATIONS.value],
                actions=channels[ChannelGroup.ACTIONS.value],
                state=channels[ChannelGroup.STATE.value],
                feedback=channels[ChannelGroup.FEEDBACK.value],
            )
        )
        conversion_records.append(
            {
                "step_index": index,
                "topic": record.topic,
                "message_type": record.message_type,
                "record_time_ns": record.record_time_ns,
                "timestamp_source": timestamp_source,
                "source_sequence": record.sequence,
                "payload_strategy": "inline" if not new_assets else "asset_reference",
                "payload_metadata": payload_metadata,
            }
        )

    boundary: dict[str, Any] = {"kind": "whole_bag"}
    if segment is not None:
        boundary = {"kind": "record_time_range", "start_time_ns": segment.start_time_ns, "end_time_ns": segment.end_time_ns}
    return Episode(
        episode_id=episode_id,
        task=TaskContext(task_id=plan.task_id, success_criteria=plan.task_success_criteria),
        steps=tuple(steps),
        assets=tuple(assets),
        provenance={"source_namespace": plan.source_namespace, "source_kind": "ros2_mcap"},
        extensions={
            CONVERSION_EXTENSION_KEY: {
                "adapter": "domena.rosbag2",
                "source_path": source_path,
                "source_checksum": source_checksum,
                "boundary": boundary,
                "topic_bindings": [
                    {
                        "topic": binding.topic,
                        "channel_group": binding.channel_group.value,
                        "channel_name": binding.channel_name,
                    }
                    for binding in plan.topic_bindings
                ],
                "message_type_inventory": sorted(
                    {record.message_type for record in records}
                ),
                "records": conversion_records,
            }
        },
    )


def _effective_timestamp(record: RosbagMessageRecord) -> tuple[int, str]:
    header_timestamp = _header_timestamp_ns(record.message)
    if header_timestamp is not None:
        return header_timestamp, "header_stamp"
    return record.record_time_ns, "record_time_fallback"


def _convert_message(record: RosbagMessageRecord, message: Any, checksum: str) -> tuple[Any, list[Asset], dict[str, Any]]:
    message_type = record.message_type
    if message_type == "sensor_msgs/msg/JointState":
        return _joint_state(message), [], {}
    if message_type == "sensor_msgs/msg/Imu":
        return _imu(message), [], {}
    if message_type == "geometry_msgs/msg/Twist":
        return _twist(message), [], {}
    if message_type == "tf2_msgs/msg/TFMessage":
        return _tf_message(message), [], {}

    metadata = {"message_type": message_type}
    media_type = "application/x-ros2-message"
    if message_type == "sensor_msgs/msg/Image":
        media_type = "application/x-ros-image"
        metadata.update(
            {
                key: _json_scalar(_value(message, key))
                for key in ("height", "width", "encoding", "is_bigendian", "step")
                if _value(message, key) is not None
            }
        )
    asset_id = "mcap-" + sha256(f"{checksum}:{record.topic}:{record.record_time_ns}:{record.sequence}".encode()).hexdigest()[:24]
    asset = Asset(
        asset_id=asset_id,
        uri=f"mcap://{checksum}/{quote(record.topic, safe='')}/{record.record_time_ns}/{record.sequence}",
        media_type=media_type,
    )
    return AssetReference(asset_id=asset_id), [asset], metadata


def _joint_state(message: Any) -> dict[str, Any]:
    return {key: _json_list(_value(message, key, [])) for key in ("name", "position", "velocity", "effort")}


def _imu(message: Any) -> dict[str, Any]:
    return {
        "orientation": _vector(message, "orientation", ("x", "y", "z", "w")),
        "angular_velocity": _vector(message, "angular_velocity", ("x", "y", "z")),
        "linear_acceleration": _vector(message, "linear_acceleration", ("x", "y", "z")),
    }


def _twist(message: Any) -> dict[str, Any]:
    return {
        "linear": _vector(message, "linear", ("x", "y", "z")),
        "angular": _vector(message, "angular", ("x", "y", "z")),
    }


def _tf_message(message: Any) -> dict[str, Any]:
    transforms = []
    for transform in _value(message, "transforms", []):
        header = _value(transform, "header", {})
        transforms.append(
            {
                "parent_frame_id": str(_value(header, "frame_id", "")),
                "child_frame_id": str(_value(transform, "child_frame_id", "")),
                "translation": _vector(_value(transform, "transform", {}), "translation", ("x", "y", "z")),
                "rotation": _vector(_value(transform, "transform", {}), "rotation", ("x", "y", "z", "w")),
            }
        )
    return {"transforms": transforms}


def _header_timestamp_ns(message: Any) -> int | None:
    header = _value(message, "header")
    stamp = _value(header, "stamp") if header is not None else None
    seconds = _value(stamp, "sec") if stamp is not None else None
    nanoseconds = _value(stamp, "nanosec") if stamp is not None else None
    if isinstance(seconds, int) and not isinstance(seconds, bool) and isinstance(nanoseconds, int) and not isinstance(nanoseconds, bool):
        return seconds * 1_000_000_000 + nanoseconds
    return None


def _value(value: Any, name: str, default: Any = None) -> Any:
    if isinstance(value, Mapping):
        return value.get(name, default)
    return getattr(value, name, default)


def _vector(value: Any, name: str, components: tuple[str, ...]) -> dict[str, Any]:
    vector = _value(value, name, {})
    return {component: _json_scalar(_value(vector, component, 0.0)) for component in components}


def _json_list(value: Any) -> list[Any]:
    return [_json_scalar(item) for item in value]


def _json_scalar(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    return str(value)


def _file_sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()
