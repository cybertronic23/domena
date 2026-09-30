## 1. Core execution contract

- [x] 1.1 Add immutable transform-plan, job-run with separate engine/runtime identity, materialization-reference value objects, and the minimal `BoundedExecutor` protocol with canonical fingerprinting and validation.
- [x] 1.2 Implement the deterministic local bounded executor and focused core tests.

## 2. Lance data lake integration

- [x] 2.1 Add optional `lance` dependency extra and lazy integration boundary.
- [x] 2.2 Implement staged Lance materialization, verification, and release-scoped reading.
- [x] 2.3 Add Lance integration tests using a curated M1b/M2-compatible fixture release.

## 3. Ray Data execution integration

- [x] 3.1 Add optional `ray` and combined `ray,lance` extras with lazy import errors.
- [x] 3.2 Implement Ray Data execution for the supported bounded transform set, including explicit batch/resource configuration.
- [x] 3.3 Add Ray/local parity tests and failed-run publication-safety tests.

## 4. Verification

- [x] 4.1 Run core tests without optional dependencies and engine integration tests with installed extras.
- [x] 4.2 Validate this OpenSpec change in strict mode.

## Reserved next iteration (not implemented in M3)

- [ ] D1 Implement `DaftExecutor`: map the same `TransformPlan` to a Daft DataFrame, reusing `JobRun`, Lance materialization, and publication validation.
