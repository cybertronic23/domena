# Domena

[简体中文](README.zh-CN.md)

**Experience data infrastructure for embodied intelligence and Physical AI.**

Domena is an open-source Python data-plane project for the experience data produced as robots and agents interact with the physical world: simulation, real robots, and human teleoperation.

Its intended data loop is:

> Experience → Dataset → Training / Evaluation → Better Experience

The project is starting M1a: the source-neutral experience-contract implementation. It does not yet provide a real-robot or simulator adapter, a dataset format, or a training framework.

## Project status

Domena is in its initial implementation stage. Public user and contributor documentation will be published under `docs/` when the corresponding interfaces and behavior are stable.

Implementation-ready changes are specified and tracked in [`openspec/`](openspec/). Exploratory design notes and research sources are deliberately kept local and are not part of the repository.

## License

[MIT](LICENSE)
