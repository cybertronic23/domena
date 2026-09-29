## Status

**Ready for implementation — normative specifications and tasks are approved.**

中文版本：[design.zh-CN.md](design.zh-CN.md)

## Context

The JD research consistently requires dataset versioning, lineage, rapid dataset slicing, quality evidence, experiment comparison, and failure-driven recollection. M1a deliberately stopped at a validated episode boundary. M1b should add reproducible dataset composition without assuming a data lake, query engine, annotation vendor, object-store provider, or training framework.

## Goals / Non-Goals

**Goals**

- Make dataset membership explicit, immutable, inspectable, and reproducible on a local filesystem.
- Preserve a chain from a dataset release to episode identifiers, episode fingerprints, source references, the M1a schema version, and declared construction inputs.
- Allow future experiments and failure reports to name a dataset release and episode/step ranges without coupling Domena to a model runner.
- Distinguish data identity from storage location so a manifest can move without silently changing its meaning.

**Non-Goals**

- No query service, web UI, vector search, cloud registry, lakehouse, distributed execution, or fleet ingestion.
- No quality-score algorithm, annotation UI, active-learning policy, train/serve system, or benchmark runner.
- No automatic resolution of ROS bags, simulator files, media assets, or remote URIs.
- No source-specific split conventions or embodiment-specific dataset format.

## Proposed Design

### 1. Immutable manifest as the dataset release unit

The durable unit is a JSON-compatible `DatasetManifest`, initially proposed as `domena.dataset-manifest/v0.1`. A manifest represents one exact release, not a mutable folder and not a saved query.

It would contain:

- a human-readable `dataset_name` and optional logical lineage name;
- a release identifier and canonical SHA-256 content fingerprint;
- the supported experience schema version(s);
- explicit ordered membership entries for every episode;
- a `construction` record containing generator version, selection rationale, inputs, and timestamps;
- aggregate statistics that can be recomputed from membership;
- optional split labels and opaque extension fields;
- references to quality/evaluation/failure evidence, without interpreting that evidence in M1b.

### 2. Explicit membership, not live selection

Each member records a `source_namespace_id`, `episode_id`, mandatory SHA-256 episode fingerprint, and a locator/reference sufficient for a local consumer to resolve the serialized M1a episode. The composite `(source_namespace_id, episode_id)` is the member identity; a bare `episode_id` is not globally unique. Membership is materialized into the release. A query or curation recipe may be captured as provenance, but must not be required to recreate membership.

`source_namespace_id` is an internally registered stable numeric identifier. A manifest stores both the identifier and a human-readable namespace string snapshot. The registry can rename a namespace for future use without making past releases uninterpretable.

This makes a dataset stable even when source folders later receive new episodes or when selection logic changes.

### 3. Identity and fingerprint separation

The draft separates two concepts:

- **logical identity**: a human-meaningful name such as `tabletop-pick-v1`;
- **release fingerprint**: a deterministic digest of canonical manifest content, intended to detect changes in membership or declared compatibility.

The release fingerprint is SHA-256 over canonical semantic content: ordered member identities and episode fingerprints, split labels, supported experience schema versions, and required conversion/compatibility configuration. It excludes volatile metadata such as creation time, author, free-text description, and notes. Thus equivalent releases rebuilt at different times have the same fingerprint.

Every M1b member requires an Episode content fingerprint. M1a will expose a stable SHA-256 fingerprint over canonical Episode JSON so a changed episode cannot silently retain its identity in a dataset release.

### 4. Provenance as declared evidence

Manifest provenance is append-free and describes how this release was constructed: M1a contract version, source manifest/release parents if any, selection recipe reference or free-text rationale, tool/version identity, and declared quality or curation evidence references.

M1b records provenance; it does not certify that a remote URI remains reachable or that a referenced quality report is true.

### 5. Compatibility and validation

M1b validation should be structural and local:

- required IDs are present and unique;
- each member has a supported M1a schema version and valid fingerprint syntax;
- split labels, extensions, and provenance references follow documented rules; split labels are optional member metadata, not first-class split objects;
- aggregate counts match declared membership;
- the release fingerprint matches canonical content when a fingerprint is supplied.

M1b guarantees local relative-path resolution. It may preserve other URIs as uninterpreted source references but does not introduce a generic URI resolver protocol. Optional local resolution may verify that referenced episode files can be read and that their IDs/fingerprints match membership; URI availability and large-asset checking remain outside core manifest validation.

### 6. Evaluation and failure linkage boundary

M1b defines only stable references: an evaluation or failure record can identify `dataset_release`, `source_namespace_id`, `episode_id`, and an optional step interval. Quality, annotation, and failure evidence use a small shared evidence-reference type with `kind`, stable external `id`, and optional `uri`; M1b does not interpret the evidence. It does not define metric schemas, scoring, failure taxonomies, dashboard behavior, or model execution. Those belong to M3 or a later approved change.

## Candidate Local Workflow

1. Validate and serialize M1a episodes, then calculate their canonical SHA-256 fingerprints.
2. Select a finite list of episode references.
3. Build and validate a manifest from that explicit list.
4. Write the canonical manifest locally and compute its release fingerprint.
5. Inspect the manifest, resolve local episode references when requested, and hand the release ID to future training/evaluation tools.

## Confirmed Decisions

1. Dataset member identity is `(source_namespace_id, episode_id)`; internal source namespaces maintain a stable numeric ID to string-enum registry, and manifests retain both values.
2. Release fingerprints use SHA-256 over semantic content and exclude volatile metadata.
3. Every member must include a SHA-256 Episode content fingerprint, provided by M1a canonical JSON fingerprinting.
4. Train/validation/test remain optional member-level labels in M1b.
5. M1b supports local relative-path resolution only; other URIs are preserved but not resolved.
6. M1b introduces a minimal shared evidence-reference type for quality, annotation, evaluation, and failure references.
7. Acceptance uses a curated local directory of serialized M1a JSON episodes, rather than mock-only in-memory objects.

## Approval Gate

Implementation is authorized by the approved normative OpenSpec specifications and tasks in this change.
