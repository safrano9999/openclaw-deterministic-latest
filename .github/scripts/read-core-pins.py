#!/usr/bin/env python3
# Source of truth: SCRIPTS/githubactions. Generated copies are overwritten.
"""Resolve the Core-pre Containerfile's source selection before any build/test."""
import argparse
import hashlib
import os
import json
from pathlib import Path
import re
import subprocess

TARGET_TOOL_PINS = {
    # OpenClaw 2026.9.4 was released with these exact toolchain pins.
    "2026.9.4": {
        "OPENCLAW_PNPM_VERSION": "12.3.4",
        "OPENCLAW_NODE_VERSION": "26.8.2",
    },
}


def read_pins(core: Path, build: Path) -> dict[str, str]:
    text = (core / "fedora45-ai-core-pre/Containerfile").read_text()
    def arg(name, pattern):
        found = re.findall(r"^ARG " + name + "=(" + pattern + ")$", text, re.M)
        if len(found) != 1:
            raise ValueError("Invalid Core-pre source pin: " + name)
        return found[0]
    requested_version = os.environ.get("TARGET_OPENCLAW_VERSION", "").strip()
    if requested_version and not re.fullmatch(r"\d+\.\d+\.\d+", requested_version):
        raise ValueError("Invalid requested OpenClaw target version")
    version = requested_version or arg("OPENCLAW_VERSION", r"\d+\.\d+\.\d+")
    override = "" if requested_version else arg("OPENCLAW_UPSTREAM_SHA", r"(?:[0-9a-f]{40})?")
    upstream = override or json.loads(subprocess.check_output([
        "gh", "api", f"repos/openclaw/openclaw/commits/v{version}",
    ], text=True))["sha"]
    if not re.fullmatch(r"[0-9a-f]{40}", upstream):
        raise ValueError("Selected release did not resolve to a commit")
    pins = build.read_text()
    if requested_version:
        patch_candidates = (
            Path("patches") / f"openclaw-{version}-deterministic-main.patch",
            Path("patches") / f"openclaw-{version}-deterministic.patch",
        )
        patch_file = next((path for path in patch_candidates if path.is_file()), None)
        if patch_file is not None:
            patch_name = patch_file.as_posix()
            patch_sha = hashlib.sha256(patch_file.read_bytes()).hexdigest()
            pins = re.sub(r"^OPENCLAW_PATCH_FILE=.*$", "OPENCLAW_PATCH_FILE=" + patch_name, pins, flags=re.M)
            pins = re.sub(r"^OPENCLAW_PATCH_SHA256=.*$", "OPENCLAW_PATCH_SHA256=" + patch_sha, pins, flags=re.M)
        for key, value in TARGET_TOOL_PINS.get(version, {}).items():
            pins, count = re.subn(r"^" + key + r"=.*$", key + "=" + value, pins, flags=re.M)
            if count != 1:
                raise ValueError("Missing toolchain pin: " + key)
    # Reuse the reviewed patch only if it applies and all compatibility tests pass.
    # A new stable clears the Core-pre override; failed tests publish nothing.
    for key, value in {"OPENCLAW_VERSION": version,
                       "OPENCLAW_BUILD_LABEL": version + "-patched",
                       "OPENCLAW_DETERMINISTIC_ASSET": f"openclaw-{version}-deterministic.tar.gz"}.items():
        pins = re.sub(r"^" + key + r"=.*$", key + "=" + value, pins, flags=re.M)
    pins, count = re.subn(r"^OPENCLAW_UPSTREAM_SHA=.*$", "OPENCLAW_UPSTREAM_SHA=" + upstream, pins, flags=re.M)
    if count != 1:
        raise ValueError("Missing Deterministic source pin")
    ephemeral = re.findall(r"^OPENCLAW_EPHEMERAL_COMMIT=([0-9a-f]{40})$",
        (core / "fedora45-ai-core/build.conf").read_text(), re.M)
    if len(ephemeral) != 1:
        raise ValueError("Core has no exact Ephemeral source pin")
    releases = json.loads(subprocess.check_output([
        "gh", "api", "repos/safrano9999/openclaw-deterministic-latest/releases?per_page=100",
    ], text=True))
    identity = {"version": version, "upstream": upstream, "ephemeral": ephemeral[0],
                "patch_source": os.environ["PATCH_COMMIT"],
                "probes": {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                           for p in sorted((core / "upgrade-loop/probes").glob("openclaw*"))}}
    fingerprint = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
    asset = f"openclaw-{version}-deterministic.tar.gz"
    for release in releases:
        if (not release.get("draft") and not release.get("prerelease")
                and release["tag_name"].startswith(version + "-deterministic.")
                and f"Build fingerprint: {fingerprint}." in (release.get("body") or "")
                and any(a["name"] == asset and re.fullmatch(r"sha256:[0-9a-f]{64}", a.get("digest", ""))
                        for a in release.get("assets", []))):
            return {"version": version, "upstream_sha": upstream, "ephemeral_sha": ephemeral[0],
                    "needs_build": "false", "fingerprint": fingerprint, "release_tag": release["tag_name"]}
    prefix = version + "-deterministic."
    configured = re.findall(r"^OPENCLAW_DETERMINISTIC_RELEASE_TAG=" + re.escape(prefix) + r"(\d+)$", pins, re.M)
    revisions = [int(configured[0]) - 1] if configured else [0]
    for release in releases:
        tag = release["tag_name"]
        if tag.startswith(prefix) and tag[len(prefix):].isdigit():
            revisions.append(int(tag[len(prefix):]))
    release_tag = prefix + str(max(revisions) + 1)
    pins = re.sub(r"^OPENCLAW_DETERMINISTIC_RELEASE_TAG=.*$",
                  "OPENCLAW_DETERMINISTIC_RELEASE_TAG=" + release_tag, pins, flags=re.M)
    build.write_text(pins)
    return {"version": version, "upstream_sha": upstream, "ephemeral_sha": ephemeral[0],
            "needs_build": "true", "fingerprint": fingerprint, "release_tag": release_tag}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("core", type=Path)
    parser.add_argument("build", type=Path)
    args = parser.parse_args()
    for key, value in read_pins(args.core, args.build).items():
        print(f"{key}={value}")
