## ADDED Requirements

### Requirement: Immutable bounded transform plan
The system SHALL represent a bounded transform plan with an input DatasetManifest release fingerprint, a versioned transform identifier, deterministic configuration, and an explicit output schema identifier. The plan SHALL reject an input manifest whose declared release fingerprint does not validate.

#### Scenario: Construct a valid plan
- **WHEN** a caller supplies a valid immutable manifest and a supported deterministic transform declaration
- **THEN** the system creates a plan whose input and transform fingerprints are inspectable

#### Scenario: Reject invalid input release
- **WHEN** a caller supplies a manifest with an invalid release fingerprint
- **THEN** the system rejects plan construction before execution starts

### Requirement: Executor-independent job run record
The system SHALL expose an immutable job run record containing the logical processing `engine_name`, execution `runtime_name`, status, input release fingerprint, transform fingerprint, timestamps, and optional failure evidence. A successful run SHALL have a materialization reference; a failed or cancelled run SHALL NOT have one.

#### Scenario: Record successful execution
- **WHEN** an executor completes verification of a staged output
- **THEN** the system records a successful run with its materialization reference

#### Scenario: Record failed execution
- **WHEN** an executor encounters a transform or verification failure
- **THEN** the system records failure evidence and does not publish a materialization reference

#### Scenario: Identify processing engine and runtime independently
- **WHEN** a processing engine executes on a separately selected runtime
- **THEN** the job run identifies them independently, such as `engine_name=daft` with `runtime_name=ray`

### Requirement: Bounded executor extension contract
The system SHALL expose a minimal executor contract that accepts a `TransformPlan` plus explicit execution options and returns a `JobRun`. The contract SHALL NOT expose engine-specific operator graphs or optimizer settings. Local and Ray Data executors SHALL implement this contract, and a future Daft executor SHALL be able to implement it without changing plan, job-run, fingerprint, staging, or materialization-publication semantics.

#### Scenario: Add a future executor without changing release semantics
- **WHEN** a future Daft executor is added for an already supported plan
- **THEN** it can report a `JobRun` and publish only a verified materialization reference using the same Domena release identity and validation rules

### Requirement: Local and Ray Data execution parity
The system SHALL provide a deterministic local executor and an optional Ray Data executor for the same supported bounded transform plans. The Ray integration SHALL be lazily imported and SHALL fail with an actionable dependency error when its optional dependency is absent.

#### Scenario: Run a supported plan locally
- **WHEN** a caller submits a supported plan to the local executor
- **THEN** the system produces deterministic rows and a terminal job run

#### Scenario: Run the same plan through Ray Data
- **WHEN** Ray is installed and a caller submits the same supported plan to the Ray executor
- **THEN** the resulting canonical rows and plan fingerprints match the local execution result
