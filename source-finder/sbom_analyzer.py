#!/usr/bin/env python3
import json
import os
import sys

from cyclonedx.model.bom import Bom
from packageurl import PackageURL

from maven_resolver import MavenArtifact, MavenResolver, POMNotFound


def purl_to_maven_coords(purl_str: str) -> MavenArtifact:
    p = PackageURL.from_string(purl_str)

    if p.type != "maven":
        raise ValueError(f"Expected maven purl, got type={p.type!r}")

    if not p.namespace or not p.name or not p.version:
        raise ValueError(f"Incomplete Maven purl: {p}")

    return MavenArtifact(p.namespace, p.name, p.version)


def parse_bom(path: str) -> Bom:
    """
    Parse a CycloneDX SBOM from JSON into a Bom object.
    """
    with open(path, "rb") as f:
        data = f.read()

    bom = Bom.from_json(data=json.loads(data))
    return bom


def is_jar(purl_str: str) -> bool:
    try:
        p = PackageURL.from_string(purl_str)
    except ValueError:
        return False
    return p.type == "maven" and isinstance(p.qualifiers, dict) and p.qualifiers.get("type") == "jar"


def spdx_connection_to_github_repo(connection: str) -> str | None:
    """
    Convert an SCM connection string to a GitHub repository URL, if possible.
    """
    if not connection.startswith("git+"):
        return None

    connection = connection[4:]
    prefixes = [
        "git@github.com:",
        "git://github.com/",
        "ssh://github.com/",
        "https://github.com/",
        "https://gitbox.apache.org/repos/asf/"
    ]
    for prefix in prefixes:
        if connection.startswith(prefix):
            repo_path = connection[len(prefix):]
            if repo_path.endswith(".git"):
                repo_path = repo_path[:-4]
            return repo_path

    return None


def process_bom(path: str):
    bom = parse_bom(path)

    print(f"Loaded BOM from {path}", file=sys.stderr)
    print(f"Components: {len(bom.components)}", file=sys.stderr)
    print()

    resolver = MavenResolver()

    print("[")

    for comp in bom.components:
        # comp.purl may be a string or a PackageURL depending on library version;
        # handle both.
        raw_purl = None

        if hasattr(comp, "purl") and comp.purl:
            raw_purl = str(comp.purl)

        if not raw_purl:
            # No PURL -> skip
            continue

        if not is_jar(raw_purl):
            # Only handling JARs
            continue

        artifact = purl_to_maven_coords(raw_purl)
        print("=" * 80, file=sys.stderr)
        print(f"Artifact: {artifact}", file=sys.stderr)

        try:
            location = resolver.resolve_source_location(artifact)
        except Exception as e:
            print(f"SCM       : error while fetching SCM info: {e}", file=sys.stderr)
            continue

        if location is None:
            print("Location: <none>", file=sys.stderr)
            continue
        print(f"Location URL: {location.connection}", file=sys.stderr)
        print(f"Location tag: {location.tag or '<none>'}", file=sys.stderr)

        repository = spdx_connection_to_github_repo(location.connection)
        if not repository or not location.tag:
            continue

        print("{")
        print(f"  \"repository\": \"{repository}\",")
        print(f"  \"tag\": \"{location.tag or ''}\",")
        print(f"  \"path\": \"\",")
        print(f"  \"artifact\": \"{artifact.group_id}:{artifact.artifact_id}:{artifact.version}\"")
        print("},")

    print("]")


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <cyclonedx-sbom.json>", file=sys.stderr)
        sys.exit(1)

    sbom_path = sys.argv[1]
    if not os.path.isfile(sbom_path):
        print(f"Error: file not found: {sbom_path}", file=sys.stderr)
        sys.exit(2)

    process_bom(sbom_path)


if __name__ == "__main__":
    main()
