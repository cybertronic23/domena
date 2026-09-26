# Experience model

[简体中文](experience-model.zh-CN.md)

## Working vocabulary

**Experience** is the domain-level account of an agent or robot interacting with an environment. It is deliberately broader than a file, row, or message. It may span a complete run, a collection of runs, or a unit of data lineage depending on the later workflow.

**Episode** is a candidate bounded interaction trajectory: it has a beginning and end and can usually be processed independently. It is the leading candidate for the first durable data boundary, but is not yet a final decision.

**Step** is a candidate ordered interaction unit within an episode. It represents an observation/action transition at a source-defined or normalised time boundary. Steps must not be assumed to have a universal, fixed tensor shape or sampling rate.

The proposed components of a step are:

| Concept | Boundary |
| --- | --- |
| Observation | Information made available to the agent at the decision point: sensors, images, proprioception, and derived inputs. |
| Action | Command selected or applied for the transition; distinguish intended from executed action when a source can provide both. |
| State | Environment or robot state used for replay, diagnostics, or provenance but not necessarily exposed to the agent. |
| Feedback | Transition outcome such as reward, success/failure, termination signals, and source diagnostics. |

These are semantic categories, not yet required Python fields or Pydantic models. A modality may be absent, asynchronous, externally stored, or represented by a reference.

## Decisions recorded now

- Experience is first-class vocabulary and guides all layers; it is not yet declared to be one persistable entity.
- Domena must support multimodal data over time, including RGB, depth, video, point clouds, proprioception, joint/robot state, actions, rewards, outcomes, timestamps, and arbitrary metadata.
- Source-specific structures are translated at adapter boundaries and do not define the core model.
- The model must support extension without assuming every future modality belongs in a fixed class hierarchy.
- Validation must distinguish generic structural invariants from source- or task-specific quality rules.

## Open questions

1. Is an episode the v0.1 storage/interchange boundary, and which workflows require a larger experience grouping?
2. What is the minimum common temporal contract: per-step ordering, wall-clock timestamps, source clocks, or all of these?
3. How should asynchronous modalities and variable-rate sensors be associated with decision steps?
4. Which fields are required for a minimally useful generic episode, versus optional extension data?
5. How should media be addressed: inline values, content-addressed assets, URI references, or a hybrid?
6. What semantics distinguish action requested, action sent, and action executed?
7. Which outcome signals can be made generic without conflating environment termination, task success, safety aborts, and collection failures?
8. How will arbitrary metadata be namespaced, versioned, and validated?

The schema specification turns these questions into bounded v0.1 decisions before implementation begins.
