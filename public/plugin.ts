// The XDR Security nav group is owned by the XDR app plugins that register under
// category id 'xdrSecurity' (for example xdr-coordinator, xdr-defense,
// xdr-sentry, and xdr-visualizer). This wrapper plugin does not register its own
// overview page; it only preserves the bundle-level plugin identity.

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
