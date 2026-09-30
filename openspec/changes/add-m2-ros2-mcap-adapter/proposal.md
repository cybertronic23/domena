## Status

**Ready for implementation — normative specifications and tasks are approved.**

中文版本：[proposal.zh-CN.md](proposal.zh-CN.md)

## Why

M1a established a source-neutral `Episode` contract and M1b made explicit dataset membership reproducible. The next practical boundary is a real, local robot-data source. ROS 2 bags in MCAP are a high-value first source because they preserve multimodal robot recordings while keeping the core independent of ROS.

## What Changes

- Add an optional, lazy-loaded `domena.rosbag2` adapter for offline local ROS 2 MCAP files.
- Translate supported ROS messages at the adapter boundary into source-neutral `Episode` values.
- Support either one declared episode per bag or caller-provided, non-overlapping record-time segment indexes.
- Materialize small numeric messages as JSON channel values; preserve images and deferred modalities as opaque, reproducible MCAP asset references.
- Preserve source, time, topic, type, and conversion evidence without adding ROS concepts to the core package.

## Non-Goals

- ROS 1 bags, live subscriptions, bag writing, playback control, cloud ingestion, UI, automatic segmentation, synchronization, calibration inference, or quality scoring.
- Decoding `PointCloud2`, force/tactile, or custom messages in M2.
- Direct LeRobot, RLDS, Open X-Embodiment, HDF5, or training-framework exports.

## Impact

- New optional `rosbag2` dependency extra; base `domena` remains dependency-free and does not require a ROS installation.
- New public adapter API only. M1a/M1b contracts and serialization remain source-neutral and backward compatible.
