import importlib.util
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "kubernetes_overlay", Path(__file__).resolve().parents[1] / "scripts/kubernetes_overlay.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class KubernetesOverlayTest(unittest.TestCase):
    def test_retains_password_cookie_and_custom_environment(self):
        original = {"extraEnvs": [
            {"name": "OS_PASSWORD", "valueFrom": {"secretKeyRef": {"name": "service", "key": "password"}}},
            {"name": "COOKIE_PASSWORD", "valueFrom": {"secretKeyRef": {"name": "cookies", "key": "password"}}},
            {"name": "CUSTOM_SETTING", "value": "unchanged"},
        ], "envFrom": [{"configMapRef": {"name": "existing-config"}}]}
        result = module.overlay(original, "registry.example/xdr", "release-osd-3.9.0", "custom-key")
        self.assertEqual(result["extraEnvs"][:-1], original["extraEnvs"])
        self.assertEqual(result["extraEnvs"][-1]["valueFrom"]["secretKeyRef"]["name"], "custom-key")
        self.assertNotIn("envFrom", result)
        self.assertNotIn("startupProbe", result)
        self.assertEqual(len(original["extraEnvs"]), 3)

    def test_preserves_existing_key_source_and_avoids_duplicates(self):
        entry = {"name": "XDR_NAVIGATOR_ENCRYPTION_KEY", "valueFrom": {"secretKeyRef": {"name": "original-key", "key": "key"}}}
        result = module.overlay({"extraEnvs": [entry]}, "registry/xdr", "tag", "new-key")
        self.assertEqual(result["extraEnvs"], [entry])

    def test_empty_chart_values_and_custom_image(self):
        result = module.overlay({}, "private.registry/xdr", "custom-tag", "key")
        self.assertEqual(result["image"], {"repository": "private.registry/xdr", "tag": "custom-tag"})
        self.assertEqual(len(result["extraEnvs"]), 1)
        self.assertEqual(result['plugins'], {'enabled': False})

    def test_full_image_reference_with_registry_port_and_digest(self):
        image = 'registry.example:5000/xdr:release@sha256:' + 'a' * 64
        self.assertEqual(module.image_parts(image), ('registry.example:5000/xdr', 'release@sha256:' + 'a' * 64))

    def test_image_without_tag_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'versioned image'):
            module.image_parts('registry.example:5000/xdr')

    def test_existing_key_supplied_via_envfrom_is_retained(self):
        original = {"extraEnvs": [{"name": "CUSTOM", "value": "keep"}],
                    "envFrom": [{"secretRef": {"name": "existing-secrets"}}]}
        result = module.overlay(original, "repo", "tag", "new-key", key_already_configured=True)
        self.assertEqual(result["extraEnvs"], original["extraEnvs"])
        self.assertNotIn("envFrom", result)

    def test_ambiguous_existing_key_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            module.overlay({"extraEnvs": [{"name": "XDR_NAVIGATOR_ENCRYPTION_KEY"}] * 2}, "repo", "tag", "key")

    def test_nonstandard_environment_shape_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "extraEnvs must be a list"):
            module.overlay({"extraEnvs": "custom template"}, "repo", "tag", "key")


if __name__ == "__main__":
    unittest.main()
