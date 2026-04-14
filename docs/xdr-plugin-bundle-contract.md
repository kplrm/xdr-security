# XDR Plugin Bundle Contract

This document is the source of truth for the multi-plugin release produced by `xdr-security`.

## Ownership

- Release orchestrator repository: `xdr-security`
- Included plugin repositories:
  - `xdr-security`
  - `xdr-coordinator`
  - `xdr-defense`
  - `xdr-sentry`
  - `xdr-visualizer`

## Triggering

- Workflow: `.github/workflows/release-bundle.yml`
- Trigger: every push to `main` (and manual `workflow_dispatch`)
- Release model: immutable release per push

## Release Tag Format

`xdr-plugins-<YYYYMMDD>`

Examples:
- `xdr-plugins-20260405`
- `xdr-plugins-20260410`

Tag format is deterministic: generated from UTC date at release time.

## Release Assets

For release tag `T` and OpenSearch Dashboards version `O`:

- `xdr-plugins_T_osd-O.tar.gz`
  - tarball containing 5 ZIP files:
    - `xdr-security.zip`
    - `xdr-coordinator.zip`
    - `xdr-defense.zip`
    - `xdr-sentry.zip`
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

## Smoke Testing Contract

After all plugins are built, a platform matrix smoke test runs on the bundle image:

- **Platforms**: Linux amd64, Linux arm64
- **Distros**: Debian (stable-slim), AlmaLinux 9
- **Test method**: Builds OSD from scratch in each test container, installs all plugin ZIPs, validates plugins are present.
- **Purpose**: Ensure bundle artifacts work across Linux variants before publishing release.

## Container Image Contracts

### 1. Bundle image (OSD + plugins)

- Image: `ghcr.io/<org>/opensearch-dashboards-xdr-bundle`
- Tags published per release:
  - `:<release-tag>` (immutable)
  - `:latest` (moving pointer)
- Contents:
  - Official OpenSearch Dashboards base image for target version
  - All five plugin ZIPs installed via `opensearch-dashboards-plugin install --allow-root`

### 2. Plugin-only sidecar image (new)

- Image: `ghcr.io/<org>/xdr-plugins`
- Tags published per release:
  - `:<release-tag>` (immutable)
  - `:latest` (moving pointer)
- Contents:
  - Minimal Alpine base image
  - All five plugin ZIPs at `/plugins/`
  - Designed to be mounted as a volume into an official OSD container
- Use case: Decouples plugin upgrades from OSD version upgrades; allows using xdr-plugins with any OSD version.

## Deployment Models

- **Tight coupling**: Use `opensearch-dashboards-xdr-bundle` image directly; OSD and plugins upgrade together.
- **Loose coupling**: Mount `xdr-plugins` sidecar volume into a separate, independently-versioned OSD container.
- **Custom**: Download plugin bundle ZIPs and build your own image.

## Upgrade Contract

- Upgrade unit is the bundle release tag.
- Deploy by changing one container image tag.
- Roll back by restoring prior image tag.
- No partial plugin replacement is supported in this contract.
