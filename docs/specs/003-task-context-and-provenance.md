# Specification 003: Task context and provenance

[简体中文](003-task-context-and-provenance.zh-CN.md)

**Status:** Proposed — no implementation authority before architecture review.

## Scope

Define source-neutral context references that make an experience interpretable and comparable: task definition, environment/scene, embodiment/device, collection protocol, and time/calibration context. Define a common reference mechanism used by raw and derived assets.

## Requirements

- Context is versioned and referenced, not copied into every step or made simulator-specific core fields.
- A task definition can identify instructions, success/failure criteria, relevant objects/conditions, and version without prescribing a task language.
- Collection context can record source/adaptor identity, operator or automation role, protocol version, and interruption/safety events with privacy-aware identifiers.
- Time provenance distinguishes ordering from source clock and records clock/synchronisation information when supplied.
- Sensor and coordinate-frame calibration may be referenced by version; Domena must not invent a universal robotics frame model.
- Derived assets retain references to their inputs and context versions, enabling an evidence graph across datasets and evaluations.

## Non-goals

- ROS message definitions, robot control APIs, calibration computation, a universal task ontology, or a real-robot operations system.

## Acceptance criteria

After approval, mock episodes can reference two task/context versions; a reader can resolve the context and reject missing or incompatible references without importing a source SDK.

## Decisions required

- Reference resolution and packaging rules for local/offline datasets.
- Privacy, retention, and redaction policy for operators and real-world recording.
- Minimum context required to compare simulated and real episodes of one task.
