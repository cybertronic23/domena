# Domena

[简体中文](README.zh-CN.md)

**Experience data infrastructure for embodied intelligence and Physical AI.**

Domena is an open-source Python data-plane project for the experience data produced as robots and agents interact with the physical world: simulation, real robots, and human teleoperation.

Its intended data loop is:

> Experience → Dataset → Training / Evaluation → Better Experience

The project is in its architecture and domain-design phase. It does not yet provide a public experience schema, simulator adapter, or dataset format.

## Direction

Domena will provide clear boundaries from data sources through experience validation and processing to datasets consumed by training and evaluation workflows. It is designed to stay independent of any individual simulator or robot platform.

See the [architecture](docs/architecture.md), [experience-model discussion](docs/experience-model.md), [roadmap](docs/roadmap.md), and the first [engineering specification](docs/specs/001-experience-schema.md).

## License

[MIT](LICENSE)
