# xdr-security

`xdr-security` is the thin OpenSearch Dashboards wrapper plugin for XDR navigation grouping.

## Current Status

- Plugin id: `xdrSecurity`
- Version: `0.1.0`
- Target OSD: `3.5.0`
- Runtime role today: lightweight wrapper only

## What It Does

- Provides a stable XDR grouping point in OpenSearch Dashboards navigation
- Keeps the XDR app surface cohesive while `xdr-coordinator` and `xdr-defense` own operational functionality
- Avoids duplicate overview UI and business logic

## Design Choices

- Keep this plugin intentionally minimal:
  no duplicate APIs, no duplicate dashboards, no competing state model.
- Let domain plugins own behavior:
  - `xdr-coordinator`: fleet + telemetry operations
  - `xdr-defense`: policy/rule/hash/artifact lifecycle

## Build

```bash
cd /home/kplrm/github/xdr-security
yarn build --opensearch-dashboards-version 3.5.0
```

## Roadmap

### Near term
- Keep navigation behavior stable and low-maintenance
- Improve cross-app routing ergonomics where needed

### Mid term
- Add only minimal shared UX utilities if both core plugins require them

## Features To Avoid

- New server APIs in this plugin
- Business logic duplicated from coordinator/defense
- Additional persistence models that fragment XDR ownership
