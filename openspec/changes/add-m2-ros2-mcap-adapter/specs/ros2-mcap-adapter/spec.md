## ADDED Requirements

### Requirement: Optional source adapter boundary

The system SHALL expose ROS 2 MCAP import only from an outer adapter module. Importing core Domena contracts SHALL NOT require ROS 2, MCAP, or ROS message packages.

#### Scenario: Report a missing optional adapter dependency

- **WHEN** a caller invokes local MCAP reading without the `rosbag2` optional dependencies installed
- **THEN** the adapter raises a focused error that names the `domena[rosbag2]` installation extra

### Requirement: Explicit episode boundaries and topic semantics

The system SHALL accept exactly one import boundary mode: one declared whole-bag episode or an ordered set of caller-provided record-time segments. Segment ranges SHALL be half-open, non-empty, and non-overlapping. Every imported topic SHALL use an explicit Domena channel-group and channel-name binding.

#### Scenario: Import multiple declared segments

- **WHEN** a caller supplies two non-overlapping segment ranges with distinct episode IDs
- **THEN** records in each half-open range are converted only to their declared episode and no automatic segmentation occurs

#### Scenario: Reject ambiguous import boundaries

- **WHEN** a caller supplies both a whole-bag episode ID and segments, or neither
- **THEN** import-plan validation fails before source reading

### Requirement: Event-native time preservation

The system SHALL emit selected records as deterministically ordered event-native steps without automatic synchronization or resampling. It SHALL use a message header timestamp where present, otherwise the bag record timestamp, and SHALL preserve both the record time and fallback status in adapter evidence.

#### Scenario: Fall back for a message without a header stamp

- **WHEN** a selected message does not expose a valid header stamp
- **THEN** its step uses the bag record timestamp and the conversion evidence marks the fallback

### Requirement: Supported and opaque payload conversion

The system SHALL materialize `JointState`, `Imu`, `Twist`, and `TFMessage` as JSON-compatible values. It SHALL represent `Image` and deferred message families as deterministic `AssetReference` values whose assets contain opaque MCAP locators and source metadata, without copying their payload bytes by default.

#### Scenario: Preserve an image without materializing bytes

- **WHEN** a bound ROS image record is imported
- **THEN** the step channel contains an `AssetReference` and the corresponding asset identifies the MCAP record without embedding image bytes

#### Scenario: Preserve a deferred point cloud record

- **WHEN** a caller binds a `sensor_msgs/msg/PointCloud2` record
- **THEN** the adapter preserves it as an opaque asset reference including its original ROS type rather than attempting decode

### Requirement: Reproducible source evidence

The system SHALL record a bag checksum, selected boundary, bindings, source message-type inventory, and conversion evidence in source-adapter-namespaced episode metadata.

#### Scenario: Identify the source of a converted episode

- **WHEN** an adapter converts a local MCAP source
- **THEN** the resulting episode contains JSON-compatible evidence sufficient to identify the source bag and conversion configuration without requiring a source resolver in the core
