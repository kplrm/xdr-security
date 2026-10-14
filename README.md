# XDR Security

OpenSearch Dashboards bundle: Security, Coordinator, Defense, Visualizer and Navigator. Endpoint protection runs in XDR Agent.

## Install on Kubernetes

Use an image matching your **exact Dashboards version**, with OpenSearch Security enabled. No new OpenSearch user is needed.

### 1. Create and assign the role

Replace the three values below: `OS_URL` is your reachable **OpenSearch API** URL and port, `OS_CA` is its trusted CA certificate file, and `OS_ADMIN` is an existing administrator authorized to manage Security roles. Curl prompts for the password. Add `@` to send the file’s contents.

```bash
OS_URL='https://OPENSEARCH_HOST:PORT'
OS_CA='/path/to/opensearch-ca.pem'
OS_ADMIN='EXISTING_SECURITY_ADMIN'
curl --fail-with-body --cacert "$OS_CA" --user "$OS_ADMIN" \
  --request PUT "$OS_URL/_plugins/_security/api/roles/xdr_security" \
  --header 'Content-Type: application/json' \
  --data-binary @deploy/xdr-security-role.json
```

This creates or updates `xdr_security` with every permission in the JSON file; no new permission groups or existing XDR indices are needed. If the API certificate is already trusted by your system, omit `--cacert "$OS_CA"`.

Assign the role in **OpenSearch Dashboards**:

1. Sign in as `admin`, then open **Security → Roles → xdr_security**.
2. Select **Mapped users → Manage mapping**.
3. Under **Internal users**, add `admin` (your XDR login) and `kibanaserver` (the existing Dashboards backend account). Keep any existing mapped users/groups.
4. Click **Map** and confirm both users appear under **Mapped users**.

`admin` is the person signing in to Dashboards. `kibanaserver` is the OpenSearch account that the Dashboards server uses for background requests, including XDR event writes and retention setup. Its name is set by `opensearch.username` in **`opensearch_dashboards.yml`**. If your deployment uses different account names, map those existing accounts instead.

XDR agents use **Coordinator enrollment tokens**, not OpenSearch user accounts; do not create a user for each agent. Retain the mapped accounts' other roles. `xdr_security` grants full suite access, including Navigator administration; template/ISM permissions are cluster-wide.

### 2. Supply the encryption key

Navigator uses `XDR_NAVIGATOR_ENCRYPTION_KEY` to encrypt saved model API keys and MCP access tokens before storing them in OpenSearch, rather than saving them as plaintext. Keep it in a Secret and reuse it on every replica and upgrade.

```bash
NAMESPACE=YOUR_NAMESPACE
kubectl -n "$NAMESPACE" create secret generic xdr-navigator \
  --from-literal=XDR_NAVIGATOR_ENCRYPTION_KEY="$(openssl rand -hex 32)"
```

### 3. Update Dashboards

For the [official Helm chart](https://github.com/opensearch-project/helm-charts/blob/opensearch-dashboards-3.9.0/charts/opensearch-dashboards/values.yaml), use `NAMESPACE` from step 2 and export your current values:

```bash
umask 077
helm -n "$NAMESPACE" get values opensearch-dashboards -o yaml > /tmp/dashboards-values.yaml
```

Edit `/tmp/dashboards-values.yaml`: update `image` and `plugins.enabled`, and append the encryption entry to `extraEnvs`. **Keep existing environment entries and all other settings; do not duplicate YAML keys.** Replace `XDR_BUNDLE_TAG` with a published bundle tag:

```yaml
image:
  repository: ghcr.io/kplrm/opensearch-dashboards-xdr-bundle
  tag: "XDR_BUNDLE_TAG-osd-3.9.0"
extraEnvs:
  # Keep existing entries here, then add:
  - name: XDR_NAVIGATOR_ENCRYPTION_KEY
    valueFrom:
      secretKeyRef:
        name: xdr-navigator
        key: XDR_NAVIGATOR_ENCRYPTION_KEY
```

If the encryption key is already supplied (including through `envFrom`), retain it instead of adding another entry. Apply the edited values:

```bash
helm upgrade opensearch-dashboards opensearch/opensearch-dashboards -n "$NAMESPACE" \
  --version 3.9.0 -f /tmp/dashboards-values.yaml --atomic --wait --timeout 10m
```

These commands use your manual's release name `opensearch-dashboards` and chart/Dashboards version `3.9.0`. For other installations, find the release and chart version with `helm -n "$NAMESPACE" list`; match the bundle's `osd-…` suffix to your exact Dashboards version. Keep required registry pull credentials.

For other charts/manifests/operators, set the same image and Secret-backed encryption variable. Preserve required custom plugins with a [custom image](deploy/Dockerfile).

Sign in with `xdr_security` and check the apps and Dashboards logs. XDR defaults to zero index replicas and 90-day retention. Snapshot before upgrades; Helm rollback restores configuration, not OpenSearch data.

## Release and build

[GitHub Actions](.github/workflows/release-bundle.yml) validates and publishes versioned GHCR images, ZIP bundles, checksums and source manifests on code pushes to `main` or manual runs. PRs validate without publishing. Targets: 3.6.0–3.9.0, each built against matching source; never mix versions. Private component repositories need `XDR_SOURCE_TOKEN`; public releases use `GITHUB_TOKEN`. Images support AMD64/ARM64; runtime smoke tests cover AMD64. Component commits are pinned when a run starts; after pushing a component fix, start a new run to rebuild its ZIPs.

```bash
OSD_ROOT=/path/to/bootstrapped/OpenSearch-Dashboards-3.9.0 \
  npm run build -- --opensearch-dashboards-version 3.9.0
```

Builds use isolated staging and leave the upstream checkout untouched. Sentry is excluded.
