# xdr-security

`xdr-security` is the thin OpenSearch Dashboards wrapper plugin for XDR navigation grouping.

This repository is also the release orchestrator for the full XDR OpenSearch Dashboards plugin bundle:

- `xdr-security`
- `xdr-coordinator`
- `xdr-defense`
- `xdr-visualizer`

## Current Status

- Plugin id: `xdrSecurity`
- Version: `0.1.0`
- Target OSD: `3.5.0`
- Runtime role today: lightweight wrapper only

## What It Does

- Provides a stable XDR grouping point in OpenSearch Dashboards navigation
- Keeps the XDR app surface cohesive while `xdr-coordinator` and `xdr-defense` own operational functionality
- Avoids duplicate overview UI and business logic

## Design Choices

- Keep this plugin intentionally minimal:
  no duplicate APIs, no duplicate dashboards, no competing state model.
- Let domain plugins own behavior:
  - `xdr-coordinator`: fleet + telemetry operations
  - `xdr-defense`: policy/rule/hash/artifact lifecycle

## Build

```bash
cd /home/kplrm/github/xdr-security
yarn build --opensearch-dashboards-version 3.5.0
```

## Unified Plugin Bundle Release

The GitHub workflow `.github/workflows/release-bundle.yml` runs on every push to `main` and creates:

- A GitHub release with a unique immutable tag: `xdr-bundle-<UTC timestamp>-<commit>`
- A bundled artifact containing all four plugin ZIPs
- SHA256 checksums and a machine-readable manifest
- A Docker Compose override snippet for the released bundle image
- A multi-arch container image with all plugins pre-installed:
  `ghcr.io/<org>/opensearch-dashboards-xdr-bundle:<tag>` and `:latest`

See [docs/xdr-plugin-bundle-contract.md](docs/xdr-plugin-bundle-contract.md) for the release contract.

## Deploy On Existing OpenSearch (Container-Based)

### Option 1: Run the prebuilt XDR Dashboards image

1. Pull the release image tag from the latest GitHub release.
2. Update your Dashboards service image to that tag.
3. Restart the Dashboards container.

Example override:

```yaml
services:
  opensearch-dashboards:
    image: ghcr.io/<org>/opensearch-dashboards-xdr-bundle:xdr-bundle-<timestamp>-<sha>
    ports:
      - "5601:5601"
    environment:
      OPENSEARCH_HOSTS: '["https://opensearch:9200"]'
```

### Option 2: Install from bundle ZIPs into your own image

1. Download `xdr-plugins_<tag>_osd-<version>.tar.gz` from the release.
2. Extract it during your image build.
3. Install each ZIP with `opensearch-dashboards-plugin install`.

Example Dockerfile fragment:

```dockerfile
FROM opensearchproject/opensearch-dashboards:3.5.0

COPY plugins/*.zip /tmp/xdr-plugins/
RUN set -eux; \
    for plugin in /tmp/xdr-plugins/*.zip; do \
      /usr/share/opensearch-dashboards/bin/opensearch-dashboards-plugin install --allow-root "file://${plugin}"; \
    done; \
    rm -rf /tmp/xdr-plugins
```

## Upgrade Strategy (Replace Bundle With New Version)

Use immutable release tags for deterministic upgrades:

1. Pick the target release tag from GitHub Releases.
2. Update your Dashboards image tag from old bundle tag to new bundle tag.
3. Recreate the Dashboards container (`docker compose up -d --force-recreate opensearch-dashboards`).
4. Validate plugin load in logs and UI.

Rollback is symmetric: redeploy the previous known-good bundle tag.

Recommended operational practices:

- Promote tags across environments (`dev -> staging -> prod`) instead of rebuilding.
- Keep at least one previous release available for rapid rollback.
- Record deployed bundle tag with each environment change.

## Roadmap

### Near term
- Keep navigation behavior stable and low-maintenance
- Improve cross-app routing ergonomics where needed

### Mid term
- Add only minimal shared UX utilities if both core plugins require them

## Features To Avoid

- New server APIs in this plugin
- Business logic duplicated from coordinator/defense
- Additional persistence models that fragment XDR ownership
