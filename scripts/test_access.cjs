const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const ts = require(path.join(process.env.OSD_ROOT || path.resolve(__dirname, '../../OpenSearch-Dashboards'), 'node_modules/typescript'));
require.extensions['.ts'] = (module, filename) => {
  const output = ts.transpileModule(fs.readFileSync(filename, 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2021 },
  });
  module._compile(output.outputText, filename);
};
const { XdrSecurityServerPlugin } = require('../server/plugin.ts');

function fixture({ status = 'authenticated', roles = [], backendRoles = [], error, basePath = '' } = {}) {
  let handler, checks = 0;
  const core = { http: {
    registerOnPostAuth: (value) => { handler = value; },
    auth: { get: () => ({ status, state: { authInfo: { roles: ['xdr_security'] } } }) },
    basePath: { remove: (value) => value.startsWith(basePath + '/') ? value.slice(basePath.length) : value },
  } };
  const plugin = new XdrSecurityServerPlugin();
  plugin.setup(core);
  plugin.start({ opensearch: { client: { asScoped: (request) => ({ asCurrentUser: { transport: {
    request: async (options) => {
      checks++;
      assert.ok(request.url);
      assert.deepEqual(options, { method: 'GET', path: '/_plugins/_security/authinfo' });
      if (error) throw error;
      return { body: { roles, backend_roles: backendRoles } };
    },
  } } }) } } });
  const response = {
    unauthorized: ({ body }) => ({ status: 401, body }),
    forbidden: ({ body }) => ({ status: 403, body }),
    badRequest: ({ body }) => ({ status: 400, body }),
    custom: ({ statusCode, body }) => ({ status: statusCode, body }),
  };
  return {
    plugin, roles,
    get checks() { return checks; },
    call: (pathname) => handler({ url: { pathname } }, response, { next: () => ({ status: 200 }) }),
  };
}

test('every XDR application and browser API requires the role', async () => {
  const auth = fixture();
  for (const pathname of [
    '/api/xdr_manager/policies', '/api/xdr-defense/telemetry/search',
    '/api/xdr-visualizer/alerts/summary', '/api/xdr-navigator/session',
    '/app/xdrCoordinator', '/app/xdrDefense', '/app/xdrVisualizer', '/app/xdrNavigator',
  ]) {
    assert.equal((await auth.call(pathname)).status, 403, pathname);
  }
});

test('an existing user with the resolved XDR role is allowed', async () => {
  const auth = fixture({ roles: ['kibana_user', 'xdr_security'] });
  assert.equal((await auth.call('/api/xdr_manager/policies')).status, 200);
  assert.equal(auth.checks, 1);
});

test('an unmapped backend group does not substitute for the OpenSearch role', async () => {
  const auth = fixture({ backendRoles: ['xdr_security'] });
  assert.equal((await auth.call('/api/xdr-navigator/session')).status, 403);
});

test('role revocation is effective on the next request despite cached auth state', async () => {
  const auth = fixture({ roles: ['xdr_security'] });
  assert.equal((await auth.call('/api/xdr-navigator/session')).status, 200);
  auth.roles.length = 0;
  assert.equal((await auth.call('/api/xdr-navigator/session')).status, 403);
  assert.equal(auth.checks, 2);
});

test('unsigned requests are rejected before querying OpenSearch', async () => {
  const auth = fixture({ status: 'unauthenticated' });
  assert.equal((await auth.call('/api/xdr_manager/policies')).status, 401);
  assert.equal(auth.checks, 0);
});

test('agent bearer-token routes and other applications retain their own authentication', async () => {
  const auth = fixture({ status: 'unauthenticated' });
  for (const pathname of ['/api/v1/agents/enroll', '/api/v1/agents/heartbeat', '/api/v1/agents/telemetry', '/api/status', '/app/discover']) {
    assert.equal((await auth.call(pathname)).status, 200, pathname);
  }
  assert.equal(auth.checks, 0);
});

test('base paths and encoded app/API names cannot bypass authorization', async () => {
  const auth = fixture({ basePath: '/dashboards' });
  for (const pathname of ['/dashboards/api/%78dr_manager/policies', '/dashboards/app/%78drNavigator']) {
    assert.equal((await auth.call(pathname)).status, 403, pathname);
  }
});

test('backend failure and stopped authorization client fail closed', async () => {
  const auth = fixture({ error: new Error('backend unavailable') });
  assert.equal((await auth.call('/api/xdr_manager/policies')).status, 503);
  auth.plugin.stop();
  assert.equal((await auth.call('/api/xdr_manager/policies')).status, 503);
});
