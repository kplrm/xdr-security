ARG OSD_VERSION=3.9.0
ARG OSD_BASE_IMAGE=opensearchproject/opensearch-dashboards:${OSD_VERSION}
FROM ${OSD_BASE_IMAGE}

# Preserve the upstream entrypoint and Security plugin. Install at image build time.
USER 1000
COPY --chown=1000:1000 plugins/*.zip /tmp/xdr-plugins/
RUN set -eu; \
    for plugin in /tmp/xdr-plugins/*.zip; do \
      /usr/share/opensearch-dashboards/bin/opensearch-dashboards-plugin install "file://${plugin}"; \
    done; \
    rm -rf /tmp/xdr-plugins
