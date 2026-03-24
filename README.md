# xdr-security

Wrapper OpenSearch Dashboards plugin that groups XDR apps under a single
`XDR Security` navigation category and provides a simple launcher page.

## Build

```bash
cd /home/kplrm/github/xdr-security
yarn build --opensearch-dashboards-version 3.5.0
```

## Purpose

- Expose `XDR Security` as a first-class nav section.
- Provide a landing page that links to `xdrCoordinator` and `xdrDefense`.
- Keep plugin composition lightweight while preserving existing plugin APIs.
