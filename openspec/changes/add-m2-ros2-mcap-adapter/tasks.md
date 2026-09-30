## 1. Import-plan contract

- [x] 1.1 Add source-adapter-only import plan, segments, topic bindings, and focused optional-dependency error.
- [x] 1.2 Validate mutually exclusive boundary modes, half-open segment ranges, and explicit source-neutral topic bindings.

## 2. ROS 2 MCAP conversion

- [x] 2.1 Add lazy production enumeration through optional MCAP ROS 2 dependencies.
- [x] 2.2 Convert supported numeric ROS message families to JSON values and large/deferred payloads to deterministic asset references.
- [x] 2.3 Preserve record-time, header-time fallback, message inventory, bindings, segment evidence, and bag fingerprint in namespaced provenance.

## 3. Tests and packaging

- [x] 3.1 Add synthetic-record tests for whole-bag and explicit multi-segment import, ordering, timestamp fallback, and validation failures.
- [x] 3.2 Add coverage for supported conversion, opaque image/deferred assets, and absent optional dependencies.
- [x] 3.3 Add the optional `rosbag2` project dependency extra without adding it to the core install.

## 4. Verification

- [x] 4.1 Run the complete local unit-test suite.
- [x] 4.2 Validate this OpenSpec change in strict mode.
