## ADDED Requirements

### Requirement: Stable source namespace registry

The system SHALL represent every dataset member source with a positive integer `source_namespace_id` and a non-empty `source_namespace` string. A `DatasetManifest` SHALL embed the string snapshot corresponding to each member's numeric identifier. The numeric identifier SHALL remain the stable identity within the manifest; a bare `episode_id` SHALL NOT be treated as globally unique.

#### Scenario: Distinguish same episode IDs from two sources

- **WHEN** two members use the same `episode_id` with different `source_namespace_id` values
- **THEN** validation accepts both members and treats their composite identities as distinct

#### Scenario: Reject conflicting namespace snapshots

- **WHEN** two members use the same `source_namespace_id` with different `source_namespace` strings
- **THEN** validation reports a path-addressable namespace-registry conflict

### Requirement: Explicit immutable membership

The system SHALL expose an immutable `DatasetManifest` contract identified by `domena.dataset-manifest/v0.1`. A manifest SHALL carry a non-empty dataset name, release identifier, supported experience schema versions, and an explicitly ordered finite list of episode members. Each member SHALL carry its composite identity, a SHA-256 episode content fingerprint, and a local-relative locator or an uninterpreted external locator.

#### Scenario: Preserve a finite local dataset release

- **WHEN** a caller creates a manifest from a finite ordered list of M1a episode references
- **THEN** serialisation retains the exact member order, identities, fingerprints, locators, and compatibility declaration without evaluating a live query

### Requirement: Canonical release fingerprint

The system SHALL calculate a lower-case SHA-256 release fingerprint from canonical semantic manifest content: ordered member identities and episode fingerprints, member split labels, supported experience schema versions, and required compatibility configuration. Creation timestamps, author metadata, free-text descriptions, and notes SHALL NOT affect this fingerprint.

#### Scenario: Ignore volatile creation metadata

- **WHEN** two otherwise equivalent manifests differ only in creation time or free-text notes
- **THEN** their calculated release fingerprints are identical

#### Scenario: Detect a changed member

- **WHEN** a member's episode fingerprint or split label changes
- **THEN** the calculated release fingerprint changes and validation rejects a mismatching declared release fingerprint

### Requirement: Structural local validation

The system SHALL report path-addressable validation issues for unsupported schema identifiers, malformed SHA-256 fingerprints, duplicate composite member identities, missing local-relative locators, invalid split labels, invalid extension keys, invalid evidence references, and mismatched aggregate member counts.

#### Scenario: Reject duplicate member identity

- **WHEN** a manifest contains two members with the same `source_namespace_id` and `episode_id`
- **THEN** validation reports the duplicate member path

### Requirement: Local reference resolution boundary

The system SHALL resolve only local relative member locators against a caller-provided manifest directory. It SHALL preserve non-local URIs as opaque references and SHALL NOT attempt network or source-adapter resolution.

#### Scenario: Resolve a serialized M1a episode locally

- **WHEN** a member references a local relative M1a JSON file and resolution is requested
- **THEN** the system reads the local episode and verifies its episode ID and canonical SHA-256 fingerprint against the member declaration

#### Scenario: Preserve a remote URI without resolution

- **WHEN** a member contains an `s3://` or other non-local URI
- **THEN** manifest validation preserves the locator and does not perform network access

### Requirement: Evidence references and member-level split labels

The system SHALL support optional member split labels limited to `train`, `validation`, and `test`. It SHALL support source-neutral evidence references with non-empty `kind`, stable `id`, and optional `uri`, without interpreting referenced quality, annotation, evaluation, or failure semantics.

#### Scenario: Link a failure report to a member

- **WHEN** a manifest includes a failure evidence reference for a member or release
- **THEN** serialisation and validation retain its kind, ID, and optional URI without requiring a failure taxonomy
