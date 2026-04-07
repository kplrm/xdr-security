# xdr-security

XDR plugin bundle for OpenSearch Dashboards.

This repository is for adding XDR plugins to an existing OpenSearch + OpenSearch Dashboards deployment without repacking or rebuilding the Dashboards image.

## What this repository provides

- `xdr-security` (navigation wrapper)
- `xdr-coordinator` (agent fleet + telemetry operations)
- `xdr-defense` (rule/hash/policy operations)
- `xdr-visualizer` (investigation UI)

## Authoritative test reference files

Use these files as the out-of-the-box baseline for local testing of all XDR plugins:

- `docker-compose.yml`
- `opensearch_dashboards.no-security.yml`

The current compose setup is intentionally plugin-first:

- Uses `ghcr.io/kplrm/xdr-plugins:latest` as an `xdr-plugins` sidecar volume source.
- Uses the official `opensearchproject/opensearch-dashboards:latest` image.
- Installs plugin zip files into Dashboards at container start.

The current no-security Dashboards config sets:

- `server.host`
- `opensearch.hosts`
- `opensearch.ssl.verificationMode: none`
- `opensearch.requestHeadersAllowlist`
- `opensearch_security.enabled: false`

## Run (local test stack)

```bash
cd xdr-security
docker compose up -d
```

Open Dashboards at `http://localhost:5601`.

## Verify plugin load

1. Confirm containers are healthy:

```bash
docker compose ps
```

2. Confirm plugin install happened during Dashboards startup:

```bash
docker logs opensearch-dashboards | grep -Ei "xdr-|plugin"
```

3. In the Dashboards UI, confirm the **XDR** navigation group appears with Coordinator, Defense, and Visualizer apps.

## Install latest xdr-agent package (install only, no enrollment)

Use the commands below to fetch the latest xdr-agent package directly from GitHub Releases and install the correct architecture automatically.

Debian/Ubuntu (auto-detect `amd64` or `arm64`):

```bash
ARCH=$(dpkg --print-architecture)
case "$ARCH" in amd64|arm64) ;; *) echo "Unsupported Debian arch: $ARCH"; exit 1 ;; esac
ASSET_URL=$(curl -fsSL https://api.github.com/repos/kplrm/xdr-agent/releases/latest | grep -Eo "https://[^\"]+_${ARCH}\\.deb" | head -1)
curl -fL "$ASSET_URL" -o "/tmp/xdr-agent_latest_${ARCH}.deb"
sudo dpkg -i "/tmp/xdr-agent_latest_${ARCH}.deb"
sudo systemctl stop xdr-agent || true
sudo systemctl disable xdr-agent || true
```

CentOS/RHEL/Rocky/Alma (auto-detect `x86_64` or `aarch64`):

```bash
ARCH=$(uname -m)
case "$ARCH" in x86_64|aarch64) ;; *) echo "Unsupported RPM arch: $ARCH"; exit 1 ;; esac
ASSET_URL=$(curl -fsSL https://api.github.com/repos/kplrm/xdr-agent/releases/latest | grep -Eo "https://[^\"]+\\.${ARCH}\\.rpm" | head -1)
curl -fL "$ASSET_URL" -o "/tmp/xdr-agent_latest_${ARCH}.rpm"
sudo rpm -Uvh "/tmp/xdr-agent_latest_${ARCH}.rpm"
sudo systemctl stop xdr-agent || true
sudo systemctl disable xdr-agent || true
```

This keeps the step install-only (package present, not enrolled, and not running).

## Troubleshooting

### Hostname mismatch / TLS verification issues

Symptoms: Dashboards cannot connect to OpenSearch with certificate or hostname errors.

Actions:

- Use the provided `opensearch_dashboards.no-security.yml` for local no-security testing.
- Confirm `opensearch.ssl.verificationMode: none` is present in that file.
- Confirm Dashboards is using that mounted config file.

### Login screen appears unexpectedly

Symptoms: Dashboards shows a login page even though local test mode is expected.

Actions:

- Confirm `opensearch_security.enabled: false` in `opensearch_dashboards.no-security.yml`.
- Confirm Dashboards container has `DISABLE_SECURITY_DASHBOARDS_PLUGIN=true`.
- Recreate containers after config changes:

```bash
docker compose down
docker compose up -d
```

### Duplicate plugin registration after restarts

Symptoms: duplicate plugin errors or unstable plugin startup after repeated restarts.

Cause: plugins were reinstalled into an existing Dashboards container state.

Fix (clean recreate of Dashboards container):

```bash
docker compose stop opensearch-dashboards
docker compose rm -f opensearch-dashboards
docker compose up -d opensearch-dashboards
```

If needed, fully recreate the stack:

```bash
docker compose down
docker compose up -d
```

## Related docs

- Plugin bundle contract: `docs/xdr-plugin-bundle-contract.md`
- Workspace overview: `../README.md`
