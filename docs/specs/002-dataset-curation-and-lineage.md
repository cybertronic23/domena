# Specification 002: Dataset curation and lineage

[简体中文](002-dataset-curation-and-lineage.zh-CN.md)

**Status:** Proposed — no implementation authority before architecture review.

## Scope

Define a reproducible dataset as a named, versioned snapshot of selected experience and derived assets. Define the provenance links from that snapshot to source experiences, annotations, quality reports, and selection rules.

## Requirements

- A dataset snapshot has stable identity, version, creation context, immutable membership manifest, and declared intended use.
- Membership is selected by an explicit, versioned curation rule or an auditable manual decision; it must not be an opaque mutable query.
- A snapshot records references to input experience, annotation and quality versions, plus exclusions and their reasons where available.
- Selection can express task/context, modality availability, quality evidence, coverage strata, and failure-derived criteria without making these fields mandatory in v0.1.
- Lineage must allow a reader to answer: what was included, why, which input versions were used, and what changed between two snapshots.

## Non-goals

- A data lake, registry service, distributed query engine, visual curation UI, or access-control system.
- Automated data-mixing optimisation, universal quality scoring, or automatic deduplication.

## Acceptance criteria

After approval, a local implementation can create two dataset snapshots from mock experience, reproduce the first from its manifest, explain membership, and report a structured difference between them.

## Decisions required

- Canonical identifier/reference format and snapshot-manifest format.
- Whether memberships are ordered and how large media assets are referenced.
- Minimal representation of manual curation decisions and exclusion reasons.
