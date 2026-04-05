# xdr-security

OpenSearch Dashboards (OSD) plugin bundle for XDR (Extended Detection and Response).

**Package Contents**: Four integrated plugins for fleet management, threat hunting, attack graph analysis, and threat intelligence.
- `xdr-coordinator`: Agent fleet lifecycle and telemetry dashboards
- `xdr-defense`: Detection and prevention rule management
- `xdr-visualizer`: Attack-footprint investigation UI
- `xdr-security`: Navigation wrapper (this repository)

## Quick Start

Assuming you already have OpenSearch and OpenSearch Dashboards running:

### Option 1: Use the pre-built plugin container (simplest)

Pull and run the plugin container, which will make plugins available via Docker volume:

```bash
# Run the plugin container in the background
docker run -d --name xdr-plugins \
  -v xdr-plugins:/plugins \
  ghcr.io/<your-org>/xdr-plugins:latest

# Restart your Dashboards container to pick up plugins
docker restart opensearch-dashboards
```

In your Docker Compose for Dashboards, add the volume mount:

```yaml
services:
  opensearch-dashboards:
    image: opensearchproject/opensearch-dashboards:3.5.0
    ports:
      - "5601:5601"
    volumes:
      - xdr-plugins:/usr/share/opensearch-dashboards/plugins
    environment:
      OPENSEARCH_HOSTS: '["https://opensearch:9200"]'

volumes:
  xdr-plugins:
```

Then restart:

```bash
docker compose down
docker compose up -d
```

### Option 2: Use the all-in-one bundle image (single container)

If you don't mind using our specific OpenSearch Dashboards version:

```bash
# Replace your Dashboards with the bundle image
docker run -d --name opensearch-dashboards \
  -p 5601:5601 \
  -e OPENSEARCH_HOSTS='["https://opensearch:9200"]' \
  ghcr.io/<your-org>/opensearch-dashboards-xdr-bundle:latest
```

Or in Docker Compose:

```yaml
services:
  opensearch-dashboards:
    image: ghcr.io/<your-org>/opensearch-dashboards-xdr-bundle:latest
    ports:
      - "5601:5601"
    environment:
      OPENSEARCH_HOSTS: '["https://opensearch:9200"]'
```

### Option 3: Manual install into your existing Dashboards image

1. Download plugin ZIPs from [GitHub Releases](https://github.com/kplrm/xdr-security/releases):
   ```bash
   wget https://github.com/kplrm/xdr-security/releases/download/xdr-plugins-20260405/xdr-plugins_xdr-plugins-20260405_osd-3.5.0.tar.gz
   tar -xz xdr-plugins_*.tar.gz
   ```

2. Install into your running Dashboards:
   ```bash
   docker exec opensearch-dashboards \
     /usr/share/opensearch-dashboards/bin/opensearch-dashboards-plugin install \
     file:///path/to/xdr-coordinator.zip
   
   docker exec opensearch-dashboards \
     /usr/share/opensearch-dashboards/bin/opensearch-dashboards-plugin install \
     file:///path/to/xdr-defense.zip
   
   docker exec opensearch-dashboards \
     /usr/share/opensearch-dashboards/bin/opensearch-dashboards-plugin install \
     file:///path/to/xdr-security.zip
   
   docker exec opensearch-dashboards \
     /usr/share/opensearch-dashboards/bin/opensearch-dashboards-plugin install \
     file:///path/to/xdr-visualizer.zip
   ```

3. Restart Dashboards:
   ```bash
   docker restart opensearch-dashboards
   ```

## Upgrade to Latest Release

### Option 1 container (recommended for decoupled updates):

```bash
# Stop the old plugin container
docker stop xdr-plugins
docker rm xdr-plugins

# Pull and run the new version
docker run -d --name xdr-plugins \
  -v xdr-plugins:/plugins \
  ghcr.io/<your-org>/xdr-plugins:latest

# Restart Dashboards to pick up new plugins
docker restart opensearch-dashboards
```

### Option 2 container (all-in-one):

```bash
docker stop opensearch-dashboards
docker rm opensearch-dashboards

docker run -d --name opensearch-dashboards \
  -p 5601:5601 \
  -e OPENSEARCH_HOSTS='["https://opensearch:9200"]' \
  ghcr.io/<your-org>/opensearch-dashboards-xdr-bundle:latest
```

### Manual install (Option 3):

Repeat the install steps above with new plugin ZIP files from the latest release.

## Finding Your OpenSearch Info

If you need to verify your cluster details before deploying:

```bash
# Endpoint (usually cluster host + port 9200)
# Example: https://opensearch.example.com:9200

# Dashboards endpoint
# Example: https://opensearch-dashboards.example.com:5601

# Can test connectivity with:
curl -u admin:admin https://opensearch.example.com:9200 -k
```

## Verify Installation

After containers restart, visit `http://localhost:5601` (or your Dashboards URL), then:

1. Look for the **XDR** section in the left navigation
2. You should see sub-items:
   - **Coordinator**: Agent management and telemetry
   - **Defense**: Rule and policy management
   - **Visualizer**: Investigation UI

If you don't see XDR apps, check Dashboards logs:

```bash
docker logs opensearch-dashboards
```

Look for errors related to plugin installation (e.g., "Failed to load plugin").

## Supported Versions

- **OpenSearch Dashboards**: 3.5.0 (see release notes for version compatibility)
- **OpenSearch**: 3.5.0+
- **Architectures**: Linux x86_64, ARM64

## Support & Documentation

- [Architecture & API docs](docs/xdr-plugin-bundle-contract.md)
- [Release history](https://github.com/kplrm/xdr-security/releases)
- [Main workspace README](../README.md)

## For Developers

To build plugins locally:

```bash
cd xdr-security
yarn build --opensearch-dashboards-version 3.5.0

cd ../xdr-coordinator
yarn build --opensearch-dashboards-version 3.5.0

cd ../xdr-defense
yarn build --opensearch-dashboards-version 3.5.0

cd ../xdr-visualizer
yarn build --opensearch-dashboards-version 3.5.0
```

See individual plugin READMEs for development setup.
