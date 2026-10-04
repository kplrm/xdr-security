# XDR Security

A thin navigation identity and release wrapper for the active XDR Security plugins: Coordinator, Defense, and Visualizer. Endpoint protection runs in XDR Agent. Sentry is excluded pending redesign.

The wrapper registers no overview page. Each active application registers under the XDR Security navigation group.

[Bundle release contract](docs/xdr-plugin-bundle-contract.md)

```bash
npm run build -- --opensearch-dashboards-version 3.5.0
```

Local builds stage into a disposable Dashboards copy. They do not modify the upstream workspace checkout. Previously installed Sentry instances remain until removed from that deployment; this repository does not change Sentry itself.
