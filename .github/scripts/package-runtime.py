#!/usr/bin/env python3
# Source of truth: SCRIPTS/githubactions. Generated copies are overwritten.
"""Bundle upstream-packed OpenClaw and Codex from one pinned source commit."""

import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path
import re
import tarfile
import tempfile


def package_runtime(root: Path, codex: Path, config: Path, destination: Path) -> None:
    pins = dict(line.split("=", 1) for line in config.read_text().splitlines()
                if line and not line.startswith("#"))
    version = pins["OPENCLAW_VERSION"]
    commit = pins["OPENCLAW_UPSTREAM_SHA"]
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version):
        raise ValueError("The update baseline must be a stable numeric version")
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("The upstream source must be an exact commit")
    artifacts = {"openclaw.tgz": root, "codex.tgz": codex}
    for filename, expected_name in (("openclaw.tgz", "openclaw"), ("codex.tgz", "@openclaw/codex")):
        with tarfile.open(artifacts[filename]) as archive:
            package = json.load(archive.extractfile("package/package.json"))
            if package["name"] != expected_name or package["version"] != version:
                raise ValueError(f"Package identity differs from build pins: {filename}")
            if filename == "openclaw.tgz":
                archive.getmember("package/dist/deterministic-gateway-replies.txt")
                archive.getmember("package/dist/control-ui/index.html")
    manifest = {
        "schemaVersion": 1,
        "version": version,
        "displayVersion": pins["OPENCLAW_BUILD_LABEL"],
        "upstreamCommit": commit,
        "releaseTag": pins["OPENCLAW_DETERMINISTIC_RELEASE_TAG"],
        "artifacts": {name: hashlib.sha256(path.read_bytes()).hexdigest()
                      for name, path in artifacts.items()},
    }
    payloads = {name: path.read_bytes() for name, path in artifacts.items()}
    payloads["manifest.json"] = (json.dumps(manifest, sort_keys=True, indent=2) + "\n").encode()
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=destination.parent) as scratch:
        candidate = Path(scratch) / "runtime.tar.gz"
        with candidate.open("wb") as raw:
            with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0, compresslevel=6) as compressed:
                with tarfile.open(fileobj=compressed, mode="w|") as archive:
                    for name, data in sorted(payloads.items()):
                        member = tarfile.TarInfo(name)
                        member.size = len(data)
                        member.mode = 0o644
                        archive.addfile(member, io.BytesIO(data))
        candidate.replace(destination)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("root", "codex", "config", "destination"):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    package_runtime(args.root, args.codex, args.config, args.destination)
