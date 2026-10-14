#!/usr/bin/env bash
# Run only against disposable containers. Demo TLS is confined to this test.
set -euo pipefail
trap 'echo "Smoke test failed at line $LINENO" >&2' ERR
IMAGE="${1:?bundle image required}"
OSD_VERSION="${2:?Dashboards version required}"
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SMOKE_DIR="$(mktemp -d)"
SMOKE_NAME="xdr-smoke-${RANDOM}-$$"
cleanup() {
  result=$?
  if [[ "$result" != 0 ]]; then
    docker logs "${SMOKE_NAME}-os" --tail=100 || true
    docker logs "${SMOKE_NAME}-osd" --tail=200 || true
  fi
  docker rm -f "${SMOKE_NAME}-osd" "${SMOKE_NAME}-os" >/dev/null 2>&1 || true
  docker network rm "$SMOKE_NAME" >/dev/null 2>&1 || true
  rm -rf "$SMOKE_DIR"
  exit "$result"
}
trap cleanup EXIT
export OPENSEARCH_INITIAL_ADMIN_PASSWORD="$(openssl rand -hex 24)Aa1!"
export XDR_NAVIGATOR_ENCRYPTION_KEY="$(openssl rand -hex 32)"
if [[ "${GITHUB_ACTIONS:-}" == true ]]; then
  echo "::add-mask::${OPENSEARCH_INITIAL_ADMIN_PASSWORD}"
  echo "::add-mask::${XDR_NAVIGATOR_ENCRYPTION_KEY}"
fi
docker network create "$SMOKE_NAME" >/dev/null
docker run -d --name "${SMOKE_NAME}-os" --network "$SMOKE_NAME" --network-alias opensearch \
  -p 127.0.0.1::9200 -e discovery.type=single-node -e OPENSEARCH_JAVA_OPTS='-Xms512m -Xmx512m' \
  -e OPENSEARCH_INITIAL_ADMIN_PASSWORD "opensearchproject/opensearch:${OSD_VERSION}" >/dev/null
OS_URL="https://$(docker port "${SMOKE_NAME}-os" 9200/tcp)"
os_admin() { curl -fkSs --connect-timeout 3 --max-time 20 -u "admin:${OPENSEARCH_INITIAL_ADMIN_PASSWORD}" "$OS_URL$1" "${@:2}"; }
ready=false
for _ in {1..90}; do
  if os_admin '/_cluster/health?wait_for_status=yellow&timeout=1s' >"$SMOKE_DIR/health.json" 2>/dev/null \
    && jq -e '.timed_out == false' "$SMOKE_DIR/health.json" >/dev/null; then ready=true; break; fi
  sleep 5
done
[[ "$ready" == true ]] || { echo 'OpenSearch did not become ready' >&2; exit 1; }
os_admin '/_plugins/_security/api/roles/xdr_security' -X PUT -H 'Content-Type: application/json' \
  --data-binary "@${ROOT_DIR}/deploy/xdr-security-role.json" >/dev/null
# Start with the existing service account mapped; the existing admin is not mapped yet.
os_admin '/_plugins/_security/api/rolesmapping/xdr_security' -X PUT -H 'Content-Type: application/json' \
  -d '{"users":["kibanaserver"],"backend_roles":[],"hosts":[]}' >/dev/null
cat >"$SMOKE_DIR/opensearch_dashboards.yml" <<'EOF'
server.host: 0.0.0.0
opensearch.hosts: ["https://opensearch:9200"]
opensearch.username: kibanaserver
opensearch.password: kibanaserver
opensearch.ssl.verificationMode: none
opensearch.requestHeadersAllowlist: [authorization, securitytenant]
opensearch_security.cookie.secure: false
EOF
chmod 755 "$SMOKE_DIR"
chmod 644 "$SMOKE_DIR/opensearch_dashboards.yml"
docker run -d --name "${SMOKE_NAME}-osd" --network "$SMOKE_NAME" -p 127.0.0.1::5601 \
  -e XDR_NAVIGATOR_ENCRYPTION_KEY \
  -v "$SMOKE_DIR/opensearch_dashboards.yml:/usr/share/opensearch-dashboards/config/opensearch_dashboards.yml:ro" \
  "$IMAGE" >/dev/null
OSD_URL="http://$(docker port "${SMOKE_NAME}-osd" 5601/tcp)"
ready=false
for _ in {1..120}; do
  if curl -fSs --connect-timeout 3 --max-time 10 -u "admin:${OPENSEARCH_INITIAL_ADMIN_PASSWORD}" \
    "$OSD_URL/api/status" >"$SMOKE_DIR/status.json" 2>/dev/null; then ready=true; break; fi
  sleep 5
done
[[ "$ready" == true ]] || { echo 'Dashboards did not become ready' >&2; exit 1; }
osd_admin() { curl -fSs --connect-timeout 3 --max-time 20 -u "admin:${OPENSEARCH_INITIAL_ADMIN_PASSWORD}" "$OSD_URL$1" "${@:2}"; }
for route in /api/xdr_manager/policies /api/xdr-visualizer/alerts/summary /api/xdr-navigator/session /app/xdrDefense; do
  code="$(curl -sS -o /dev/null -w '%{http_code}' -u "admin:${OPENSEARCH_INITIAL_ADMIN_PASSWORD}" "$OSD_URL$route")"
  [[ "$code" == 403 ]] || { echo "XDR role not enforced for $route: $code" >&2; exit 1; }
done
code="$(curl -sS -o /dev/null -w '%{http_code}' -u "admin:${OPENSEARCH_INITIAL_ADMIN_PASSWORD}" \
  -X POST "$OSD_URL/api/xdr-defense/telemetry/search" -H 'osd-xsrf: true' -H 'Content-Type: application/json' -d '{}')"
[[ "$code" == 403 ]] || { echo "Defense role not enforced: $code" >&2; exit 1; }
# Grant the same role to an existing user; no new OpenSearch user is created.
os_admin '/_plugins/_security/api/rolesmapping/xdr_security' -X PUT -H 'Content-Type: application/json' \
  -d '{"users":["kibanaserver","admin"],"backend_roles":[],"hosts":[]}' >/dev/null
osd_admin '/api/xdr-navigator/session' >"$SMOKE_DIR/session.json"
if ! jq -e '.encryptionReady == true and .user.admin == true and .user.name == "admin"' "$SMOKE_DIR/session.json" >/dev/null; then
  echo 'Navigator session check failed: expected encryptionReady=true and admin=true for the xdr_security role. Check the Navigator source commit in the bundle manifest.' >&2
  jq '{user, encryptionReady}' "$SMOKE_DIR/session.json" >&2
  exit 1
fi
osd_admin '/api/xdr_manager/policies' >/dev/null
osd_admin '/api/xdr-visualizer/alerts/summary' >/dev/null
osd_admin '/api/xdr-defense/telemetry/search' -X POST -H 'osd-xsrf: true' -H 'Content-Type: application/json' \
  -d '{"module":"process","from":"now-1h","to":"now","page":1,"query":{"match_all":{}}}' >/dev/null
osd_admin '/api/xdr-navigator/models' -X POST -H 'osd-xsrf: true' -H 'Content-Type: application/json' \
  -d '{"name":"Role test","url":"https://example.invalid/v1/chat/completions","model":"test","apiKey":"test-credential"}' \
  | jq -e '.hasApiKey == true' >/dev/null
docker exec "${SMOKE_NAME}-osd" node/bin/node -e '
  const fs = require("fs");
  const ids = ["xdrSecurity", "xdrCoordinator", "xdrDefense", "xdrVisualizer", "xdrNavigator"];
  for (const id of ids) {
    const m = JSON.parse(fs.readFileSync(`plugins/${id}/opensearch_dashboards.json`));
    if (m.id !== id || m.opensearchDashboardsVersion !== process.argv[1]) process.exit(1);
  }
' "$OSD_VERSION"
wait_json() {
  for _ in {1..15}; do
    if os_admin "$1" >"$SMOKE_DIR/check.json" 2>/dev/null \
      && jq -e "$2" "$SMOKE_DIR/check.json" >/dev/null; then return 0; fi
    sleep 2
  done
  echo "Startup resource missing: $1" >&2
  return 1
}
for template in xdr-telemetry-template xdr-security-template xdr-agent-logs-template; do
  wait_json "/_index_template/$template" '.index_templates | length == 1'
done
for policy in xdr-telemetry-retention xdr-security-retention xdr-agent-logs-retention; do
  wait_json "/_plugins/_ism/policies/$policy" '.policy'
done
# Exercise the same service-account bulk permission used by agent intake.
printf '{"index":{"_index":".xdr-agent-telemetry-smoke"}}\n{"@timestamp":"2026-01-01T00:00:00Z","event.module":"process"}\n' \
  | curl -fkSs -u kibanaserver:kibanaserver "$OS_URL/_bulk" -H 'Content-Type: application/x-ndjson' --data-binary @- \
  | jq -e '.errors == false' >/dev/null
code="$(curl -sS -o /dev/null -w '%{http_code}' "$OSD_URL/api/xdr-navigator/session")"
[[ "$code" == 401 || "$code" == 302 ]] || { echo "Unexpected anonymous session response: $code" >&2; exit 1; }
echo "Authenticated bundle startup, templates, retention, service writes and single-role authorization passed for ${OSD_VERSION}"
