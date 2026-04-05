# XDR Plugin Bundle Contract

This document is the source of truth for the multi-plugin release produced by `xdr-security`.

## Ownership

- Release orchestrator repository: `xdr-security`
- Included plugin repositories:
  - `xdr-security`
  - `xdr-coordinator`
  - `xdr-defense`
  - `xdr-visualizer`

## Triggering

- Workflow: `.github/workflows/release-bundle.yml`
- Trigger: every push to `main` (and manual `workflow_dispatch`)
- Release model: immutable release per push

## Release Tag Format

`xdr-bundle-<YYYYMMDDhhmmss UTC>-<short sha>`

Examples:

- `xdr-bundle-20260405103045-a1b2c3d`

## Release Assets

For release tag `T` and OpenSearch Dashboards version `O`:

- `xdr-plugins_T_osd-O.tar.gz`
  - tarball containing 4 ZIP files:
    - `xdr-security.zip`
    - `xdr-coordinator.zip`
    - `xdr-defense.zip`
    - `xdr-visualizer.zip`
- `xdr-plugins_T_osd-O.sha256`
  - SHA256 for each ZIP in the tarball
- `xdr-plugins_T_manifest.json`
  - plugin ids and versions used in the build
- `docker-compose.xdr-plugins.T.yml`
  - compose override snippet pointing to the released bundle image tag

## Build Contract

- OpenSearch Dashboards source is checked out once at pinned ref/version.
- Each plugin is staged into `opensearch-dashboards/plugins/<plugin-name>`.
- Build command:
  - `node ../../scripts/plugin_helpers build --opensearch-dashboards-version=<O>`
- Version guard:
  - `package.json.version` must equal `opensearch_dashboards.json.version` for each plugin.

## Container Image Contract

- Image: `ghcr.io/<org>/opensearch-dashboards-xdr-bundle`
- Tags published per release:
  - `:<release-tag>` (immutable)
  - `:latest` (moving pointer)
- Contents:
  - Official OpenSearch Dashboards base image for target version
  - All four plugin ZIPs installed via `opensearch-dashboards-plugin install --allow-root`

## Upgrade Contract

- Upgrade unit is the bundle release tag.
- Deploy by changing one container image tag.
- Roll back by restoring prior image tag.
- No partial plugin replacement is supported in this contract.
