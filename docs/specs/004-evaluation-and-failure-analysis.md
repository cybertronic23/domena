# Specification 004: Evaluation and failure analysis

[简体中文](004-evaluation-and-failure-analysis.zh-CN.md)

**Status:** Proposed — no implementation authority before architecture review.

## Scope

Define provenance-bearing records for evaluations and failure cases. The contract connects a model/policy and its configuration, task/context and evaluation-set versions, metric definitions, aggregate outcomes, and episode/segment evidence.

## Requirements

- An evaluation run records immutable identifiers for the evaluated artifact, code/configuration where available, task/context, input dataset or evaluation-set snapshot, metric definitions, and execution time.
- Results retain aggregate metrics and links to supporting evidence; metric values without definitions or input versions are not comparable.
- A failure case can link one or more evidence targets and a typed, confidence-qualified, revisable hypothesis. Initial categories include data, perception, policy/control, hardware, environment, and collection protocol.
- Evaluation records may create feedback recommendations, but must not claim causal attribution solely from correlation.
- Reproducibility requires the evaluation to disclose held-out/split policy and relevant conditions; release gates are future policy, not hard-coded domain logic.

## Non-goals

- Model training, online evaluation execution, benchmark hosting, dashboards, release approvals, or automatic root-cause analysis.

## Acceptance criteria

After approval, a local mock evaluation can persist a versioned result with metric definitions and cited episode evidence; a failure case and feedback recommendation can be attached without changing raw experience or the dataset snapshot.

## Decisions required

- Model/policy artifact reference format and minimum execution provenance.
- Metric-definition representation and compatibility policy.
- Failure taxonomy governance, review workflow, and policy for sensitive safety incidents.
