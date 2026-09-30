## ADDED Requirements

### Requirement: Verified Lance materialization
The system SHALL materialize a valid Domena dataset release to a staged Lance dataset containing Domena member identity, release provenance, step representation, and explicit asset locators. It SHALL validate the output row count, input release fingerprint, and output schema fingerprint before publication.

#### Scenario: Materialize an immutable release
- **WHEN** a successful bounded transform is submitted to the Lance materializer
- **THEN** the system writes and verifies a staged Lance dataset before publishing it

#### Scenario: Reject incomplete output
- **WHEN** staged Lance output does not match the expected row count or fingerprints
- **THEN** the system does not publish a materialization reference

### Requirement: Domena release identity remains authoritative
The system SHALL retain the Domena release fingerprint in every Lance materialization reference and SHALL record the Lance URI and backend version or snapshot separately. The system SHALL NOT use a Lance version as the Domena release identifier.

#### Scenario: Refer to a physical Lance output
- **WHEN** a Lance materialization is successfully published
- **THEN** its reference contains both the Domena release fingerprint and the separately identified Lance output

### Requirement: Optional Lance integration
The Lance materializer and reader SHALL be available only through the optional Lance dependency and SHALL NOT make core episode or manifest imports depend on Lance or PyArrow.

#### Scenario: Use core without Lance
- **WHEN** Lance is not installed
- **THEN** importing and using the M1a, M1b, and M2 public APIs remains possible

#### Scenario: Read a published Lance output
- **WHEN** Lance is installed and a caller provides a published materialization reference
- **THEN** the reader returns rows only for that referenced Domena release and preserves source namespace and episode identity
