#!/usr/bin/env python3
"""Reject missing, corrupt, or incompatible release ZIPs before image publication."""
import json
import sys
import zipfile
from pathlib import Path

PLUGINS = {
    "xdr-security": "xdrSecurity",
    "xdr-coordinator": "xdrCoordinator",
    "xdr-defense": "xdrDefense",
    "xdr-visualizer": "xdrVisualizer",
    "xdr-navigator": "xdrNavigator",
}


def verify(directory, version):
    root = Path(directory)
    expected = {f"{repo}.zip" for repo in PLUGINS}
    actual = {path.name for path in (root / "plugins").glob("*.zip")}
    if actual != expected:
        raise ValueError(f"Plugin set mismatch: missing={expected - actual}, extra={actual - expected}")
    for repo, plugin_id in PLUGINS.items():
        meta = json.loads((root / "meta" / f"{repo}.json").read_text())
        with zipfile.ZipFile(root / "plugins" / f"{repo}.zip") as archive:
            if archive.testzip() is not None:
                raise ValueError(f"Corrupt ZIP: {repo}")
            prefix = f"opensearch-dashboards/{plugin_id}/"
            manifest = json.loads(archive.read(prefix + "opensearch_dashboards.json"))
            package = json.loads(archive.read(prefix + "package.json"))
            if prefix + f"target/public/{plugin_id}.plugin.js" not in archive.namelist():
                raise ValueError(f"Missing compiled UI: {repo}")
        if manifest["id"] != plugin_id or meta["pluginId"] != plugin_id:
            raise ValueError(f"Plugin identity mismatch: {repo}")
        if manifest["opensearchDashboardsVersion"] != version or meta["osdVersion"] != version:
            raise ValueError(f"Dashboards version mismatch: {repo}")
        if manifest["version"] != package["version"] or manifest["version"] != meta["version"]:
            raise ValueError(f"Plugin version mismatch: {repo}")
    print(f"Verified all five plugin ZIPs for Dashboards {version}")


if __name__ == "__main__":
    verify(*sys.argv[1:])
