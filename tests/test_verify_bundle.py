import importlib.util
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "verify_bundle", Path(__file__).resolve().parents[1] / "scripts/verify_bundle.py"
)
bundle = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bundle)


class BundleVerificationTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        (self.root / "plugins").mkdir()
        (self.root / "meta").mkdir()
        for repo, plugin_id in bundle.PLUGINS.items():
            meta = {"pluginId": plugin_id, "version": "0.1.0", "osdVersion": "3.9.0"}
            (self.root / "meta" / f"{repo}.json").write_text(json.dumps(meta))
            self.write_zip(repo)

    def write_zip(self, repo, version="3.9.0", ui=True, package_version="0.1.0"):
        prefix = f"opensearch-dashboards/{bundle.PLUGINS[repo]}/"
        with zipfile.ZipFile(self.root / "plugins" / f"{repo}.zip", "w") as archive:
            manifest = {"id": bundle.PLUGINS[repo], "version": "0.1.0", "opensearchDashboardsVersion": version}
            archive.writestr(prefix + "opensearch_dashboards.json", json.dumps(manifest))
            archive.writestr(prefix + "package.json", json.dumps({"version": package_version}))
            if ui:
                archive.writestr(prefix + f"target/public/{bundle.PLUGINS[repo]}.plugin.js", "compiled_ui_marker")

    def test_complete_matching_bundle(self):
        bundle.verify(self.root, "3.9.0")

    def test_missing_component(self):
        (self.root / "plugins/xdr-defense.zip").unlink()
        with self.assertRaisesRegex(ValueError, "Plugin set mismatch"):
            bundle.verify(self.root, "3.9.0")

    def test_mixed_dashboards_versions(self):
        self.write_zip("xdr-defense", version="3.8.0")
        with self.assertRaisesRegex(ValueError, "Dashboards version mismatch"):
            bundle.verify(self.root, "3.9.0")

    def test_missing_compiled_ui(self):
        self.write_zip("xdr-defense", ui=False)
        with self.assertRaisesRegex(ValueError, "Missing compiled UI"):
            bundle.verify(self.root, "3.9.0")

    def test_package_manifest_version_mismatch(self):
        self.write_zip("xdr-defense", package_version="0.2.0")
        with self.assertRaisesRegex(ValueError, "Plugin version mismatch"):
            bundle.verify(self.root, "3.9.0")

    def test_corrupt_zip_content(self):
        path = self.root / "plugins/xdr-defense.zip"
        path.write_bytes(path.read_bytes().replace(b"compiled_ui_marker", b"corrupt_ui_marker!"))
        with self.assertRaisesRegex(ValueError, "Corrupt ZIP"):
            bundle.verify(self.root, "3.9.0")

    def test_unexpected_component(self):
        (self.root / "plugins/unexpected.zip").write_bytes(b"unused")
        with self.assertRaisesRegex(ValueError, "Plugin set mismatch"):
            bundle.verify(self.root, "3.9.0")


if __name__ == "__main__":
    unittest.main()
