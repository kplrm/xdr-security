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

### Option 1: Run the prebuilt bundle image (simplest; tight OSD coupling)

Use the complete OpenSearch Dashboards image with all four XDR plugins pre-installed.

**Pros**: One image, nothing to configure.  
**Cons**: You're locked to the specific OSD version in the bundle image; requires rebuilding for OSD updates.

Example Docker Compose:

```yaml
services:
  opensearch-dashboards:
    image: ghcr.io/<org>/opensearch-dashboards-xdr-bundle:xdr-240405-a1b2c3d
    ports:
      - "5601:5601"
    environment:
      OPENSEARCH_HOSTS: '["https://opensearch:9200"]'
```

### Option 2: Install plugins from bundle ZIPs into a custom OSD image

Download the plugin bundle tarball, extract ZIPs, and build your own OSD image with the exact version you need.

**Pros**: Full control over OSD version; can use Dockerfile in CI/CD.  
**Cons**: Requires building and maintaining an image per OSD version.

Steps:

1. Download `xdr-plugins_<tag>_osd-<version>.tar.gz` from [GitHub Releases](https://github.com/kplrm/xdr-security/releases).
2. Extract: `tar -xz xdr-plugins_<tag>_osd-<version>.tar.gz`
3. Build with Dockerfile:

```dockerfile
FROM opensearchproject/opensearch-dashboards:3.5.0

COPY xdr-security.zip xdr-coordinator.zip xdr-defense.zip xdr-visualizer.zip /tmp/plugins/
RUN set -eux; \
    for plugin in /tmp/plugins/*.zip; do \
      /usr/share/opensearch-dashboards/bin/opensearch-dashboards-plugin install --allow-root "file://${plugin}"; \
    done
```

### Option 3: Plugin-only sidecar image (recommended for decoupled OSD; new)

Keep your existing OpenSearch Dashboards image unchanged. Mount a lightweight plugin-only container as a volume to inject plugins at runtime.

**Pros**: Zero coupling to OSD version; upgrade OSD independently from plugins; works across all OSD releases.  
**Cons**: Requires volume mount setup; slightly more complex than Option 1.

Example Docker Compose:

```yaml
services:
  # Your existing OSD image, unchanged
  opensearch-dashboards:
    image: opensearchproject/opensearch-dashboards:3.5.0
    ports:
      - "5601:5601"
    volumes:
      - xdr-plugins:/usr/share/opensearch-dashboards/plugins  # Mount from sidecar
    environment:
      OPENSEARCH_HOSTS: '["https://opensearch:9200"]'
    depends_on:
      xdr-plugins-sidecar:
        condition: service_completed_successfully

  # Sidecar that provides plugins via volume
  xdr-plugins-sidecar:
    image: ghcr.io/<org>/xdr-plugins:xdr-240405-a1b2c3d
    volumes:
      - xdr-plugins:/plugins  # Volume is read from this container

volumes:
  xdr-plugins:
```

Then upgrade OSD and plugins independently:

- **New OSD version**: Update `opensearch-dashboards` image tag; keep `xdr-plugins` unchanged.
- **New plugins**: Update `xdr-plugins-sidecar` image tag; keep `opensearch-dashboards` unchanged.

## Upgrade Strategy

Each Option has a different upgrade path:

### Option 1: Update the bundle image tag
```bash
# old: xdr-240405-a1b2c3d
# new: xdr-240410-f5e6d7c
docker compose pull
docker compose up -d --force-recreate opensearch-dashboards
```

### Option 2: Build a new image with newer OSD + download fresh plugins
```bash
# Re-download ZIPs from release, rebuild Dockerfile with new OSD base
docker build -t myrepo/osd-xdr:3.5.1 .
docker compose up -d --force-recreate opensearch-dashboards
```

### Option 3: Update plugin sidecar (leaves OSD running)
```bash
# Plugins update independently
docker compose up -d --force-recreate xdr-plugins-sidecar
# Optional: restart OSD if plugins aren't hot-reloaded
docker compose restart opensearch-dashboards
```

**Recommended operational practices**:
- Use Option 3 if you need to decouple plugin and OSD release cycles.
- Use Option 1 if you want the simplest single-image deployment.
- Use Option 2 if you need to customize the OSD build.
- Store release tags in your deployment manifests for reproducibility.
- Keep at least one previous release available for quick rollback.

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
