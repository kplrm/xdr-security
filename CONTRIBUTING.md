# Contributing to xdr-security

This repository owns suite navigation, shared access enforcement, and release packaging. Start with the [README](README.md) and [bundle workflow](.github/workflows/release-bundle.yml). Feature changes belong in the component that owns the behavior.

## Development and validation

Use Python 3 and the Node.js/dependency tooling required by your target OpenSearch Dashboards version. Point `OSD_ROOT` at a bootstrapped checkout matching that version:

```bash
export OSD_ROOT=/path/to/bootstrapped/OpenSearch-Dashboards
node --test scripts/test_access.cjs
python3 -m unittest discover -s tests -v
npm run build
```

The build targets the version of `OSD_ROOT` by default. An explicit `--opensearch-dashboards-version` must match that checkout. The build uses disposable staging; keep the upstream checkout untouched.

For bundle or deployment changes, follow the workflow's artifact verification and Docker smoke checks. Use disposable containers with Security enabled to validate role enforcement and app access. Report the component revisions and Dashboards version used.

## Engineering expectations

- Keep navigation and shared role enforcement consistent across the bundled apps.
- Keep each plugin's version in its own `package.json`; preserve exact Dashboards-version compatibility.
- Preserve pinned component revisions, source manifests, checksums, and third-party license notices in release artifacts.
- Keep build staging isolated from the upstream Dashboards checkout.
- Update bundle/deployment tests when packaging or Kubernetes configuration changes.
- Keep Sentry excluded from the current bundle; its redesign requires separate scope.

## Issues and pull requests

Use this repository's [issue tracker](https://github.com/kplrm/xdr-security/issues) for general questions, reproducible bugs, and proposals. Discuss substantial changes before implementation.

1. Fork the repository and branch from `main`.
2. Keep the change focused and follow the existing code style.
3. Add regression coverage for changed behavior and update affected documentation.
4. In your PR, explain the problem, resulting behavior, validation performed, and compatibility impact. List any checks you could not run, including the reason.

Use sanitized logs and fixtures; remove secrets and identifying customer data before posting.

## License and attribution

By submitting a contribution, you agree to license your original changes under the [GNU Affero General Public License, version 3 only](LICENSE) (`AGPL-3.0`). You retain copyright in your contributions. Submit only work you have the right to contribute, and preserve existing copyright and third-party license notices.

## Security reports

Report vulnerabilities through this repository's [private vulnerability reporting](https://github.com/kplrm/xdr-security/security/advisories/new) when enabled. Include affected versions, reproduction steps, impact, and sanitized supporting details. Keep vulnerability, bypass, and credential details out of public issues.

If private reporting is unavailable, open an issue asking the maintainer for a private reporting channel without describing the vulnerability.

## Conduct

Be respectful, direct, and technically concrete in issues, reviews, and discussions.
