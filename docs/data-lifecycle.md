# Data lifecycle: annotation, quality, evaluation, and feedback

[简体中文](data-lifecycle.zh-CN.md)

## Purpose

Domena treats the information needed to make experience useful—not only the raw trajectory—as data assets with provenance. This document defines the boundaries that connect collection to a measurable improvement loop.

```text
Experience → structural validation → quality assessment / annotation → curated dataset
     ↑                                                               ↓
targeted collection ← failure analysis ← evaluation evidence ← model or policy evaluation
```

## Annotation

An annotation is semantic information attached to a declared target: an episode, time range, step, modality, or derived artifact. Its contract must identify the target, schema/version, producer (human, rule, or model), confidence where meaningful, and review status. Annotations are not source metadata and must not mutate raw experience. v0.1 only reserves the linkage and provenance requirements.

## Data quality

Quality is use-case-relative evidence, separate from structural validity. A quality report may assess completeness, temporal alignment, sensor health, diversity/coverage, duplication, safety or protocol compliance, and annotation agreement. Rules must declare their version, inputs, thresholds, result, and evidence. Domena must support a quality report being attached without asserting that one universal quality score exists.

## Evaluation and failure analysis

An evaluation compares a model or policy version against a defined task, conditions, metric definitions, and dataset/evaluation-set version. Results require reproducibility context and may cite individual episodes or segments as evidence. A failure case groups evidence with a typed, revisable hypothesis—data, perception, policy/control, hardware, environment, or collection protocol—without claiming causality before investigation.

## Feedback loop

A feedback recommendation connects observed failures or coverage gaps to an actionable next step: collect a condition, add or review annotations, change curation criteria, or add a quality rule. It records its input evidence and outcome so the project can measure whether an intervention improved later evaluation. Domena will initially model the linkage, not automate the decision or operate physical collection.

## Principles and open questions

- Every derived asset needs stable identity, version, provenance, and a reference to its inputs.
- Raw source data is immutable after ingestion; derived data is additive and versioned.
- Quality, annotation, and evaluation may disagree; disagreement is evidence, not a reason to overwrite history.
- Open questions include target-reference granularity, common taxonomies, review workflow, dataset/model version identifiers, and privacy/safety governance for real-robot data.
