## Status

**Ready for implementation — normative specifications and tasks are approved.**

中文版本：[design.zh-CN.md](design.zh-CN.md)

## Design

### Boundary and optional loading

`domena.rosbag2` is an outer adapter package. It imports only M1a contract objects and uses lazy imports for `mcap` and `mcap_ros2`. Importing `domena` or unrelated core APIs never imports either dependency. If a caller invokes MCAP reading without the extra, the adapter raises a focused installation error explaining `pip install "domena[rosbag2]"`.

### Explicit import plan

`RosbagImportPlan` has a non-empty task ID, a source namespace, an explicit `topic_bindings` map, and exactly one boundary mode:

- `whole_bag_episode_id`: the entire bag becomes one episode; or
- `segments`: an ordered tuple of `RosbagSegment(episode_id, start_time_ns, end_time_ns)`.

Segments use bag record time and half-open `[start_time_ns, end_time_ns)` ranges. They must be non-empty, ordered, and non-overlapping. No heuristic segmentation is performed. Topic bindings explicitly name a Domena channel group (`observations`, `actions`, `state`, or `feedback`) and a non-empty source-neutral channel name; message type never silently determines semantic role.

### Event-native conversion

The adapter emits one `Step` for each selected, bound message record, ordered deterministically by `(effective_step_timestamp_ns, record_time_ns, topic, source_sequence)`. It does not resample or synchronize modalities. A message header stamp is the step timestamp when present; otherwise bag record time is used. The original record time and whether fallback occurred remain in adapter-namespaced extension evidence.

### Supported message materialization

`sensor_msgs/msg/JointState`, `sensor_msgs/msg/Imu`, `geometry_msgs/msg/Twist`, and `tf2_msgs/msg/TFMessage` become JSON-compatible values. `sensor_msgs/msg/Image` becomes an `AssetReference` without extracting or copying bytes. The asset ID is deterministic from the bag SHA-256, topic, record time, and source sequence. Its opaque `mcap://` locator and image metadata live in episode assets and `io.domena.rosbag2:conversion` evidence.

Unimplemented message types, including `PointCloud2`, force/tactile, and custom messages, are not decoded. When a caller binds one, it is preserved as an opaque MCAP asset reference together with its original ROS type. Unbound messages remain represented in source inventory evidence, not inferred into channels.

### Provenance

Each output episode records the source bag path, bag SHA-256, selected segment mode/range, topic bindings, source message types, and adapter identity in JSON-compatible provenance/extensions. The adapter uses `io.domena.rosbag2:conversion` as its extension key, satisfying the core extension namespace requirement. No source resolver is added to the core.

### Local test seam

Message enumeration is represented by an internal record protocol. Tests use synthetic decoded records and do not require ROS, MCAP, or hardware. The production enumerator delegates to `mcap_ros2.reader.read_ros2_messages` and adapts its values at the source boundary.
