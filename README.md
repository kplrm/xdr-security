# XDR Security

OpenSearch Dashboards bundle: Security, Coordinator, Defense, Visualizer and Navigator. Endpoint protection runs in XDR Agent.

## Install on Kubernetes

Use an image matching your **exact Dashboards version**, with OpenSearch Security enabled. No new OpenSearch user is needed.

1. In **Security → Roles**, create `xdr_security` using [this definition](deploy/xdr-security-role.json). Select the built-in action groups `cluster_monitor` and `indices_all`; enter the remaining `indices:...` / `cluster:...` strings directly as [custom permissions](https://docs.opensearch.org/latest/security/access-control/permissions/), including their wildcards. **No new action groups are required.** Map the role to existing users/groups and your existing Dashboards service account (`opensearch.username`), retaining their current roles. It grants full suite access; template/ISM permissions are cluster-wide.
2. Supply a persistent `XDR_NAVIGATOR_ENCRYPTION_KEY` through a Kubernetes Secret or your secret manager. It encrypts saved AI credentials; reuse the same key on every replica and upgrade. For a first installation:

```bash
NAMESPACE=YOUR_NAMESPACE
kubectl -n "$NAMESPACE" create secret generic xdr-navigator \
  --from-literal=XDR_NAVIGATOR_ENCRYPTION_KEY="$(openssl rand -hex 32)"
```

3. For the **official Dashboards Helm chart**, run from this checkout. Set the existing release/chart version and a successful release image:

```bash
RELEASE=YOUR_DASHBOARDS_RELEASE
CHART_VERSION=3.9.0
IMAGE=ghcr.io/kplrm/opensearch-dashboards-xdr-bundle:RELEASE_TAG-osd-3.9.0
umask 077
helm -n "$NAMESPACE" get values "$RELEASE" -o json > /tmp/dashboards-current.json
python3 scripts/kubernetes_overlay.py /tmp/dashboards-current.json \
  --image "$IMAGE" > /tmp/dashboards-xdr.json
helm upgrade "$RELEASE" opensearch/opensearch-dashboards -n "$NAMESPACE" \
  --version "$CHART_VERSION" -f /tmp/dashboards-current.json \
  -f /tmp/dashboards-xdr.json --atomic --wait --timeout 10m
```

The helper retains existing credentials, TLS, ingress and environment settings. If the Navigator key already comes from `envFrom` or chart defaults, add `--key-already-configured`; `--secret NAME` selects another Secret. Private registries require your existing image-pull credentials.

For **other charts, manifests or operators**, set the same image and inject `XDR_NAVIGATOR_ENCRYPTION_KEY` from your Secret in the existing Dashboards container configuration. Retain its backend connection, authentication and required plugins. Customized images can install the release ZIPs using [deploy/Dockerfile](deploy/Dockerfile) with `OSD_BASE_IMAGE` set to the matching base image.

Sign in as an existing user mapped to `xdr_security`; check all four applications and Navigator settings. Users without the role receive `403` on XDR requests. Check Dashboards logs for template/retention errors and enroll a test endpoint. Templates default to one shard, zero replicas and 90-day retention. Take an OpenSearch snapshot before upgrades; Helm rollback restores workload configuration, not data.

## Release and build

[GitHub Actions](.github/workflows/release-bundle.yml) validates and publishes versioned GHCR images, ZIP bundles, checksums and source manifests on `main` pushes or manual runs. PRs validate without publishing. Targets: 3.5.0–3.9.0, each built against matching source; never mix versions. Private component repositories need `XDR_SOURCE_TOKEN`; public releases use `GITHUB_TOKEN`. Images support AMD64/ARM64; runtime smoke tests cover AMD64.

```bash
OSD_ROOT=/path/to/bootstrapped/OpenSearch-Dashboards-3.9.0 \
  npm run build -- --opensearch-dashboards-version 3.9.0
```

Builds use isolated staging and leave the upstream checkout untouched. Sentry is excluded.
