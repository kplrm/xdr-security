# Local development

This setup builds all five plugins from source and runs OpenSearch/Dashboards **3.9.0** with Podman Compose. It uses the bundled demo certificates and accounts.

Requires Linux, Bash, Git, Podman with Compose, OpenSSL, Node.js 22, and Yarn 1.22.22. Install the native build tools required by the [upstream developer guide](https://github.com/opensearch-project/OpenSearch-Dashboards/blob/3.9.0/DEVELOPER_GUIDE.md#prerequisites).

```bash
sudo apt install git curl
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.8/install.sh | bash
source ~/.bashrc
nvm install 22
npm i -g corepack
corepack prepare yarn@1.22.22 --activate
```

## 1. Prepare the workspace

Choose any parent folder name. Keep the repository names below; `.build/` holds local dependencies, configuration, and plugin ZIPs outside the repositories.

```text
your-workspace/
├── xdr-security/
├── xdr-coordinator/
├── xdr-defense/
├── xdr-visualizer/
├── xdr-navigator/
└── .build/
  ├── OpenSearch-Dashboards/
  ├── plugins/
  ├── dev.env
  └── compose.local.yml
```

Start inside `your-workspace/` directory. Clone all xdr plugins and download a fixed OpenSearch Dashboards release archive:

```bash
for repo in xdr-security xdr-coordinator xdr-defense xdr-visualizer xdr-navigator; do
  git clone "https://github.com/kplrm/$repo.git"
done
mkdir -p .build/plugins
git clone --depth 1 --branch 3.9.0 https://github.com/opensearch-project/OpenSearch-Dashboards.git .build/OpenSearch-Dashboards
export OSD_ROOT="$PWD/.build/OpenSearch-Dashboards"
(cd "$OSD_ROOT" && yarn osd bootstrap)
```

Bootstrap requires Git metadata. The folder name is version-independent; change the `--branch` and version references below to use another release. Run all remaining commands from the parent folder. Builds use disposable copies of the upstream source.

Notes:
1. Use `yarn osd bootstrap --single-version=loose` if bootstrap fails.
2. You may want to add `"git.ignoredRepositories": [".build/OpenSearch-Dashboards"]` to your `.vscode/settings.json`

## 2. Configure once

The commands below create `.build/dev.env` and `.build/compose.local.yml`. Keep the generated `dev.env` for subsequent runs so Navigator can decrypt saved credentials. The Compose override mounts your local ZIPs and selects the existing demo Dashboards backend account.

```bash
sudo sysctl -w vm.max_map_count=262144
(
  umask 077
  cat > .build/dev.env <<EOF
OPENSEARCH_INITIAL_ADMIN_PASSWORD='$(openssl rand -hex 24)Aa1!'
XDR_NAVIGATOR_ENCRYPTION_KEY='$(openssl rand -hex 32)'
EOF
)
cat > .build/compose.local.yml <<'EOF'
services:
  opensearch-dashboards:
    environment:
      OPENSEARCH_USERNAME: kibanaserver
      OPENSEARCH_PASSWORD: kibanaserver
    volumes:
      - ../.build/plugins:/xdr-plugins:ro
EOF
```

## 3. Build the plugins

```bash
export OSD_ROOT="$PWD/.build/OpenSearch-Dashboards"
export NODE_PATH="$OSD_ROOT/node_modules"
index=0
for plugin in xdr-security xdr-coordinator xdr-defense xdr-visualizer xdr-navigator; do
  index=$((index + 1))
  printf '\n[%d/5] Building %s...\n' "$index" "$plugin"
  (cd "$plugin" && npm run build -- --opensearch-dashboards-version 3.9.0) || { printf '[%d/5] Build failed: %s\n' "$index" "$plugin"; exit 1; }
  cp "$plugin"/build/*-3.9.0.zip ".build/plugins/$plugin.zip"
  printf '[%d/5] Finished %s\n' "$index" "$plugin"
done
```

## 4. Start the stack

Start OpenSearch and wait for its API; `podman-compose` does not support `up --wait`. `--insecure` is used for the local demo certificate.

```bash
source .build/dev.env
podman compose --env-file .build/dev.env -f xdr-security/podman-compose.yml -f .build/compose.local.yml up -d opensearch-node
for attempt in {1..60}; do
  if curl --silent --fail --insecure --user "admin:$OPENSEARCH_INITIAL_ADMIN_PASSWORD" \
    https://localhost:9200/_cluster/health >/dev/null; then break; fi
  if [ "$attempt" -eq 60 ]; then echo "OpenSearch did not become ready within 5 minutes" >&2; exit 1; fi
  sleep 5
done
curl --fail-with-body --insecure --user "admin:$OPENSEARCH_INITIAL_ADMIN_PASSWORD" \
  --request PUT https://localhost:9200/_plugins/_security/api/roles/xdr_security \
  --header 'Content-Type: application/json' --data-binary @xdr-security/deploy/xdr-security-role.json
curl --fail-with-body --insecure --user "admin:$OPENSEARCH_INITIAL_ADMIN_PASSWORD" \
  --request PUT https://localhost:9200/_plugins/_security/api/rolesmapping/xdr_security \
  --header 'Content-Type: application/json' --data '{"users":["admin","kibanaserver"]}'
podman compose --env-file .build/dev.env -f xdr-security/podman-compose.yml \
  -f .build/compose.local.yml up -d --no-deps --force-recreate opensearch-dashboards
```

The final command installs the local ZIPs at startup; `--no-deps` skips the published-ZIP sidecar and demo reinitialization service. Once Dashboards finishes starting, open <http://localhost:5601> and sign in as `admin` with the password in `.build/dev.env`.

After code changes, repeat step 3 and the final Compose command. See [CONTRIBUTING](../CONTRIBUTING.md#development-and-validation) for validation commands. Use `http://localhost:5601` as the Coordinator URL.
