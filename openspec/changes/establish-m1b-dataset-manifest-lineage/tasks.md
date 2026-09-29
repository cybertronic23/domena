## 1. Contract and fingerprints

- [x] 1.1 Add canonical SHA-256 fingerprinting for M1a `Episode` JSON envelopes.
- [x] 1.2 Add immutable source namespace, evidence reference, dataset member, construction, and dataset manifest value objects.
- [x] 1.3 Implement deterministic manifest semantic-content and release-fingerprint calculation.

## 2. Validation and local operations

- [x] 2.1 Add path-addressable structural validation for manifest membership, namespaces, fingerprints, splits, extensions, aggregates, and declared release fingerprint.
- [x] 2.2 Add lossless local JSON serialisation/read-back and source-neutral manifest inspection.
- [x] 2.3 Add opt-in local-relative episode resolution with ID/fingerprint verification; preserve external URIs without resolution.

## 3. Curated acceptance data and tests

- [x] 3.1 Add a curated local directory of serialized M1a JSON episode fixtures.
- [x] 3.2 Add unit coverage for canonical fingerprints, identity collisions, deterministic release fingerprints, invalid manifests, JSON round trips, and local episode resolution.
- [x] 3.3 Run the full local test suite.

## 4. Verification

- [x] 4.1 Validate this OpenSpec change in strict mode.
