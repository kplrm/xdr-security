// The XDR Security nav group ("XDR Security" category header with XDR Defense and
// XDR Coordinator links) is fully owned by the xdr-defense and xdr-coordinator plugins,
// which both register their apps under category id 'xdrSecurity'. This wrapper plugin
// no longer registers its own overview page so the nav shows only the two useful apps.

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
