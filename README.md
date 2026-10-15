# XDR Security

OpenSearch Dashboards bundle: Security, Coordinator, Defense, Visualizer and Navigator. Endpoint protection runs in XDR Agent.

## Install on Kubernetes

Requires OpenSearch/Dashboards **3.7+**, with OpenSearch Security enabled.

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

This creates or updates `xdr_security`. No new permission groups or existing XDR indices are needed. If the API certificate is already trusted by your system, omit `--cacert "$OS_CA"`.

Assign the role in **OpenSearch Dashboards**:

1. Sign in as `admin`, then open **Security → Roles → xdr_security**.
2. Select **Mapped users → Manage mapping**.
3. Under **Internal users**, add `admin` (your XDR login) and `kibanaserver` (the existing Dashboards backend account). Keep any existing mapped users/groups.
4. Click **Map** and confirm both users appear under **Mapped users**.

`admin` is the person signing in to Dashboards. `kibanaserver` is the OpenSearch account that the Dashboards server uses for background requests, including XDR event writes and retention setup. Its name is set by `opensearch.username` in **`opensearch_dashboards.yml`**. If your deployment uses different account names, map those existing accounts instead.

XDR agents enroll using **Coordinator tokens**; direct event ingestion uses the restricted account below. Retain the mapped accounts' other roles. `xdr_security` grants full suite access, including Navigator administration; template/ISM permissions are cluster-wide.

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

Edit `/tmp/dashboards-values.yaml`: update `image` and `plugins.enabled`, and append the encryption entry to `extraEnvs`. **Keep existing environment entries and all other settings; do not duplicate YAML keys.** Use the image tag matching your exact Dashboards version:

```yaml
image:
  repository: ghcr.io/kplrm/opensearch-dashboards-xdr-bundle
  tag: "xdr-security-osd-3.9.0"
  pullPolicy: Always
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
  --version 3.9.0 -f /tmp/dashboards-values.yaml \
  --rollback-on-failure --wait --timeout 5m --debug
```

Each release refreshes the same image tag. To install a newer build for the same Dashboards version, restart the deployment after the Helm upgrade:

```bash
kubectl -n "$NAMESPACE" rollout restart deployment/opensearch-dashboards
```

In a new terminal, inspect the logs:

```bash
kubectl -n "$NAMESPACE" logs deploy/opensearch-dashboards -f
```

Sign in with `xdr_security` and check the apps and Dashboards logs. Coordinator creates three data streams with rollover and 90-day retention by default, plus Discover index patterns in the **Global tenant**: select `xdr-agent-*` for all Agent events or an individual stream. Snapshot before upgrades; Helm rollback restores configuration, not OpenSearch data.

### 4. Send Agent events directly to OpenSearch

Create the restricted write role, then create the `xdr-agent` user and assign that role. Requires `jq`; the second command prompts for the new Agent password and your administrator password:

```bash
curl --fail-with-body --cacert "$OS_CA" --user "$OS_ADMIN" \
  --request PUT "$OS_URL/_plugins/_security/api/roles/xdr_agent_ingest" \
  --header 'Content-Type: application/json' \
  --data-binary @deploy/xdr-agent-ingest-role.json

read -rsp 'New xdr-agent password: ' XDR_AGENT_PASSWORD
printf '\n'
jq -n --arg password "$XDR_AGENT_PASSWORD" \
  '{password: $password, opendistro_security_roles: ["xdr_agent_ingest"]}' |
curl --fail-with-body --cacert "$OS_CA" --user "$OS_ADMIN" \
  --request PUT "$OS_URL/_plugins/_security/api/internalusers/xdr-agent" \
  --header 'Content-Type: application/json' --data-binary @-
unset XDR_AGENT_PASSWORD
```

This creates/replaces the dedicated account. Its role permits writes and dynamic mapping updates only on the three XDR streams; Agents do not need the full `xdr_security` role.

On each Agent, set `opensearch.username` to `xdr-agent` in `/etc/xdr-agent/config.json` and store `XDR_OPENSEARCH_PASSWORD='YOUR_USER_PASSWORD'` in `/etc/xdr-agent/opensearch.env` (mode `600`). Configure the API URL and trusted CA, then restart the updated Agent using the [direct-ingestion steps](https://github.com/kplrm/xdr-agent/blob/main/docs/api-endpoints.md#direct-opensearch-ingestion). Events use **Basic authentication over HTTPS**; enrollment tokens remain separate. The same account can serve multiple Agents without changing their Agent IDs.

## Release and build

[GitHub Actions](.github/workflows/release-bundle.yml) validates and publishes versioned GHCR images, ZIP bundles, checksums and source manifests on code pushes to `main` or manual runs. PRs validate without publishing. Targets: 3.7.0–3.9.0, each built against matching source; never mix versions. Private component repositories need `XDR_SOURCE_TOKEN`; public releases use `GITHUB_TOKEN`. Images support AMD64/ARM64; runtime smoke tests cover AMD64. Component commits are pinned when a run starts; after pushing a component fix, start a new run to rebuild its ZIPs.

```bash
OSD_ROOT=/path/to/bootstrapped/OpenSearch-Dashboards-3.9.0 \
  npm run build -- --opensearch-dashboards-version 3.9.0
```

Builds use isolated staging and leave the upstream checkout untouched. Sentry is excluded.
