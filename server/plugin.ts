import type { CoreSetup, CoreStart, IClusterClient } from '../../OpenSearch-Dashboards/src/core/server';

const XDR_ROLE = 'xdr_security';
const XDR_PATH = /^\/(?:api\/(?:xdr_manager|xdr-defense|xdr-visualizer|xdr-navigator)|app\/(?:xdrCoordinator|xdrDefense|xdrVisualizer|xdrNavigator))(?:\/|$)/;

export class XdrSecurityServerPlugin {
  private client?: IClusterClient;

  public setup(core: CoreSetup) {
    core.http.registerOnPostAuth(async (request, response, toolkit) => {
      // Decode before matching so encoded paths cannot bypass the role check.
      let path: string;
      try { path = decodeURIComponent(request.url.pathname); }
      catch { return response.badRequest({ body: 'Invalid request path' }); }
      if (!XDR_PATH.test(core.http.basePath.remove(path))) return toolkit.next();
      if (core.http.auth.get(request).status !== 'authenticated') {
        return response.unauthorized({ body: 'Sign in to use XDR Security' });
      }
      if (!this.client) return response.custom({ statusCode: 503, body: 'XDR authorization unavailable' });
      try {
        // Always resolve the caller's current identity; never use the service account.
        const { body } = await this.client.asScoped(request).asCurrentUser.transport.request({
          method: 'GET', path: '/_plugins/_security/authinfo',
        });
        const roles = Array.isArray(body?.roles) ? body.roles : [];
        if (!roles.includes(XDR_ROLE)) return response.forbidden({ body: `Role ${XDR_ROLE} required` });
        return toolkit.next();
      } catch {
        return response.custom({ statusCode: 503, body: 'Unable to verify XDR role' });
      }
    });
    return {};
  }

  public start(core: CoreStart) {
    this.client = core.opensearch.client;
    return {};
  }

  public stop() { this.client = undefined; }
}
