## Why

Embodied-AI data and algorithm roles consistently require a reproducible closed loop across collection, multimodal synchronisation, quality, training, evaluation, and failure-driven recollection. Domena has the architecture documentation but no executable source-neutral data boundary. Without one, every future ROS, simulator, teleoperation, quality, and dataset feature would invent incompatible trajectory semantics.

## What Changes

- Approve `Episode` as the M1a durable interchange unit and implement the `domena.experience/v0.1` contract.
- Add explicit task/outcome, temporal, physical-context, provenance, extension, and external-asset-reference boundaries.
- Add structural validation, deterministic local JSON serialisation/read-back, basic inspection, and one mock-source example.
- Update architecture, roadmap, and schema documentation to reflect the JD-derived closed-loop design while retaining M1a's local-first scope.

## Capabilities

### New Capabilities

- `experience-contract`: Source-neutral bounded interaction episode construction, validation, local serialisation, reading, and inspection.

## Impact

- New Python package modules and local unit tests; no runtime dependency beyond Python 3.11+.
- Specification 001 moves from proposed to approved for M1a.
- No real robot, ROS, simulator, distributed runtime, cloud service, training runner, or dataset registry is introduced.
