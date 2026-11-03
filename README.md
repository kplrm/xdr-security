# XDR Security

XDR Security combines Linux endpoint protection with an OpenSearch Dashboards plugin suite for fleet management, telemetry exploration, alert investigation, and AI assistance. XDR Agent collects endpoint activity and applies protection; OpenSearch stores the events, and the plugins provide the operator workflows.

## Components

Each component lives in a separate repository. Links below open its README on GitHub.

| Component | Responsibility |
| --- | --- |
| [XDR Security](README.md) | Shared access enforcement, suite navigation integration, and release packaging |
| [XDR Coordinator](https://github.com/kplrm/xdr-coordinator/blob/main/README.md) | Agent enrollment, health, upgrades, grouped policies, and event intake |
| [XDR Defense](https://github.com/kplrm/xdr-defense/blob/main/README.md) | DNS, network, process, file, and authentication telemetry exploration |
| [XDR Visualizer](https://github.com/kplrm/xdr-visualizer/blob/main/README.md) | Alert inspection and investigations |
| [XDR Navigator](https://github.com/kplrm/xdr-navigator/blob/main/README.md) | Persistent AI chat, model connections, agents, and remote MCP tools |
| [XDR Agent](https://github.com/kplrm/xdr-agent/blob/main/README.md) | Linux telemetry, release-bundled YARA Forge Core detection, execution prevention, and termination of matched processes |

Agent protection content updates arrive with Agent upgrades. Ransomware, memory protection, and behavioral rules are outside the current scope. Sentry is excluded pending redesign.

## Screenshots

- **Suite overview — TODO:** add a full Dashboards screenshot showing XDR navigation and the Navigator chat panel.
- **Component views — TODO:** add screenshots of Coordinator fleet/policies, Defense telemetry, Visualizer investigations, and Navigator configuration.

<!-- Add images here, for example: ![XDR Security overview](images/xdr-security-overview.png) -->

## Local development

See [local development setup](docs/local-development.md) for the folder structure, source builds, and local installation.

## Install on Kubernetes

See [Kubernetes installation](docs/kubernetes.md) for roles, secrets, Helm configuration, and Agent ingestion.

## Architecture and contracts

- Agent: [architecture](https://github.com/kplrm/xdr-agent/blob/main/docs/architecture.md), [roadmap](https://github.com/kplrm/xdr-agent/blob/main/docs/roadmap.md), and [API contract](https://github.com/kplrm/xdr-agent/blob/main/docs/api-endpoints.md).
- Coordinator: [architecture](https://github.com/kplrm/xdr-coordinator/blob/main/docs/architecture.md) and [API/data model](https://github.com/kplrm/xdr-coordinator/blob/main/docs/api-data-model.md).
- Visualizer: [investigation architecture](https://github.com/kplrm/xdr-visualizer/blob/main/docs/architecture.md).

## Release and build

[GitHub Actions](.github/workflows/release-bundle.yml) validates and publishes versioned GHCR images, ZIP bundles, checksums and source manifests on code pushes to `main` or manual runs. PRs validate without publishing. Targets: 3.7.0–3.9.0, each built against matching source; never mix versions. Private component repositories need `XDR_SOURCE_TOKEN`; public releases use `GITHUB_TOKEN`. Images support AMD64/ARM64; runtime smoke tests cover AMD64. Component commits are pinned when a run starts; after pushing a component fix, start a new run to rebuild its ZIPs.

Each plugin's `package.json` owns its version; builds copy it into the staged manifest. Only XDR Agent keeps a `VERSION` file and releases independently. Coordinator reads Agent's `VERSION` on GitHub; Agent and plugin versions need not match.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development, validation, and reporting guidelines.

## License

Copyright (C) 2026 Diego A. Guillen-Rosaperez

Licensed under the [GNU Affero General Public License, version 3](LICENSE) (`AGPL-3.0`). Third-party components retain their own licenses and notices.
