// The applications own the navigation group. Server access is enforced by
// xdr-security; this plugin does not register a separate overview page.

export function createXdrSecurityPlugin() {
  return {
    setup(_core: unknown) {
      return {};
    },

    start() {
      return {};
    },

    stop() {},
  };
}
