# Local development

This setup builds all five plugins from source and runs OpenSearch/Dashboards **3.9.0** with Docker Compose. It uses the bundled demo certificates and accounts.

Requires Linux, Bash, Git, Docker with Compose, OpenSSL, Node.js 22, and Yarn 1.22.22. Install the native build tools required by the [upstream developer guide](https://github.com/opensearch-project/OpenSearch-Dashboards/blob/3.9.0/DEVELOPER_GUIDE.md#prerequisites).

## 1. Prepare the workspace

Choose any parent folder name. Keep the repository names below; `.build/` holds local dependencies, configuration, and plugin ZIPs outside the repositories.

```text
your-workspace/
├── xdr-security/
├── xdr-coordinator/
├── xdr-defense/
├── xdr-visualizer/
├── xdr-navigator/
├── xdr-agent/
└── .build/
    ├── OpenSearch-Dashboards-3.9.0/
    ├── plugins/
    ├── dev.env
    └── compose.local.yml
```

Start inside your cloned `xdr-security/` repository. Clone only the siblings you do not already have:

```bash
cd ..
for repo in xdr-coordinator xdr-defense xdr-visualizer xdr-navigator xdr-agent; do
  git clone "https://github.com/kplrm/$repo.git"
done
mkdir -p .build/plugins
git clone --depth 1 --branch 3.9.0 https://github.com/opensearch-project/OpenSearch-Dashboards.git .build/OpenSearch-Dashboards-3.9.0
export OSD_ROOT="$PWD/.build/OpenSearch-Dashboards-3.9.0"
(cd "$OSD_ROOT" && yarn osd bootstrap --single-version=loose)
```

Run all remaining commands from the parent folder. Builds use disposable copies of the upstream source.

## 2. Configure once

Keep `dev.env` for subsequent runs so Navigator can decrypt saved credentials. The Compose override mounts your local ZIPs and selects the existing demo Dashboards backend account.

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
export OSD_ROOT="$PWD/.build/OpenSearch-Dashboards-3.9.0"
export NODE_PATH="$OSD_ROOT/node_modules"
for plugin in xdr-security xdr-coordinator xdr-defense xdr-visualizer xdr-navigator; do
  (cd "$plugin" && npm run build -- --opensearch-dashboards-version 3.9.0) || break
  cp "$plugin"/build/*-3.9.0.zip ".build/plugins/$plugin.zip"
done
```

## 4. Start the stack

Start OpenSearch and assign the suite role to the demo login and backend accounts. `--insecure` is used for the local demo certificate.

```bash
docker compose --env-file .build/dev.env -f xdr-security/docker-compose.yml \
  -f .build/compose.local.yml up -d --wait opensearch-node
source .build/dev.env
curl --fail-with-body --insecure --user "admin:$OPENSEARCH_INITIAL_ADMIN_PASSWORD" \
  --request PUT https://localhost:9200/_plugins/_security/api/roles/xdr_security \
  --header 'Content-Type: application/json' --data-binary @xdr-security/deploy/xdr-security-role.json
curl --fail-with-body --insecure --user "admin:$OPENSEARCH_INITIAL_ADMIN_PASSWORD" \
  --request PUT https://localhost:9200/_plugins/_security/api/rolesmapping/xdr_security \
  --header 'Content-Type: application/json' --data '{"users":["admin","kibanaserver"]}'
docker compose --env-file .build/dev.env -f xdr-security/docker-compose.yml \
  -f .build/compose.local.yml up -d --no-deps --force-recreate opensearch-dashboards
```

The final command installs the local ZIPs at startup; `--no-deps` skips the published-ZIP sidecar and demo reinitialization service. Once Dashboards finishes starting, open <http://localhost:5601> and sign in as `admin` with the password in `.build/dev.env`.

After code changes, repeat step 3 and the final Compose command. See [CONTRIBUTING](../CONTRIBUTING.md#development-and-validation) for validation commands. For Agent builds, tests, installation, and enrollment, follow the [Agent README](https://github.com/kplrm/xdr-agent/blob/main/README.md#build-test-and-install-locally-debianubuntu-amd64), using `http://localhost:5601` as the Coordinator URL.
