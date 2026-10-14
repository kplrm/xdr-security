#!/usr/bin/env python3
"""Generate official-chart values without dropping existing environment entries."""
import argparse
import copy
import json
from pathlib import Path


def overlay(existing, repository, tag, secret, key_already_configured=False):
    if not isinstance(existing, dict):
        raise ValueError("Expected a JSON object from 'helm get values -o json'")
    env = copy.deepcopy(existing.get("extraEnvs") or [])
    if not isinstance(env, list) or any(not isinstance(item, dict) for item in env):
        raise ValueError("extraEnvs must be a list of environment entries")
    keys = [item for item in env if item.get("name") == "XDR_NAVIGATOR_ENCRYPTION_KEY"]
    if len(keys) > 1:
        raise ValueError("Duplicate XDR_NAVIGATOR_ENCRYPTION_KEY entries; resolve them before upgrading")
    # Existing installations must retain their key and its original secret source.
    if not keys and not key_already_configured:
        env.append({
            "name": "XDR_NAVIGATOR_ENCRYPTION_KEY",
            "valueFrom": {"secretKeyRef": {"name": secret, "key": "XDR_NAVIGATOR_ENCRYPTION_KEY"}},
        })
    return {"image": {"repository": repository, "tag": tag}, "extraEnvs": env, "plugins": {"enabled": False}}


def image_parts(image):
    reference, separator, digest = image.partition("@")
    repository, colon, tag = reference.rpartition(":")
    if not colon or not repository or not tag or "/" in tag:
        raise ValueError("Use a versioned image reference: registry/repository:tag")
    if separator:
        if not digest.startswith("sha256:") or len(digest.removeprefix("sha256:")) != 64:
            raise ValueError("Image digest must be sha256 followed by 64 hex characters")
        int(digest.removeprefix("sha256:"), 16)
        tag += "@" + digest
    return repository, tag


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("existing_values", type=Path)
    parser.add_argument("--image", required=True)
    parser.add_argument("--secret", default="xdr-navigator")
    parser.add_argument("--key-already-configured", action="store_true",
                        help="Retain an existing Navigator key supplied through envFrom or chart defaults")
    args = parser.parse_args()
    existing = json.loads(args.existing_values.read_text())
    repository, tag = image_parts(args.image)
    # Helm returns null when the release has no user-supplied values.
    print(json.dumps(overlay(existing if existing is not None else {}, repository, tag, args.secret, args.key_already_configured), indent=2))


if __name__ == "__main__":
    main()
