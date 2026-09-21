#!/usr/bin/env python3
# Source of truth: SCRIPTS/githubactions. Generated copies are overwritten.
"""Resolve the Core-pre Containerfile's source selection before any build/test."""
import argparse
import json
from pathlib import Path
import re
import subprocess


def read_pins(core: Path, build: Path) -> dict[str, str]:
    text = (core / "fedora45-ai-core-pre/Containerfile").read_text()
    def arg(name, pattern):
        found = re.findall(r"^ARG " + name + "=(" + pattern + ")$", text, re.M)
        if len(found) != 1:
            raise ValueError("Invalid Core-pre source pin: " + name)
        return found[0]
    version = arg("OPENCLAW_VERSION", r"\d+\.\d+\.\d+")
    override = arg("OPENCLAW_UPSTREAM_SHA", r"(?:[0-9a-f]{40})?")
    upstream = override or json.loads(subprocess.check_output([
        "gh", "api", f"repos/openclaw/openclaw/commits/v{version}",
    ], text=True))["sha"]
    if not re.fullmatch(r"[0-9a-f]{40}", upstream):
        raise ValueError("Selected release did not resolve to a commit")
    pins = build.read_text()
    # build.conf describes the reviewed patch/toolchain; Core-pre owns the target.
    if re.findall(r"^OPENCLAW_VERSION=(.*)$", pins, re.M) != [version]:
        raise ValueError("Port the Deterministic patch to the Core-pre version before building")
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
    prefix = version + "-deterministic."
    configured = re.findall(r"^OPENCLAW_DETERMINISTIC_RELEASE_TAG=" + re.escape(prefix) + r"(\d+)$", pins, re.M)
    if len(configured) != 1:
        raise ValueError("Invalid Deterministic release series")
    revisions = [int(configured[0]) - 1]
    for release in releases:
        tag = release["tag_name"]
        if tag.startswith(prefix) and tag[len(prefix):].isdigit():
            revisions.append(int(tag[len(prefix):]))
    release_tag = prefix + str(max(revisions) + 1)
    pins = re.sub(r"^OPENCLAW_DETERMINISTIC_RELEASE_TAG=.*$",
                  "OPENCLAW_DETERMINISTIC_RELEASE_TAG=" + release_tag, pins, flags=re.M)
    build.write_text(pins)
    return {"version": version, "upstream_sha": upstream, "ephemeral_sha": ephemeral[0]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("core", type=Path)
    parser.add_argument("build", type=Path)
    args = parser.parse_args()
    for key, value in read_pins(args.core, args.build).items():
        print(f"{key}={value}")
