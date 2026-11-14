#!/usr/bin/env python3
"""Package exact qualified development sources/artifacts, never a production release."""
import argparse
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    exec(compile(path.read_bytes(), str(path), "exec"), module.__dict__)
    return module


def build(destination, sources, core_prepared, *, variant="baseline"):
    core, refinery, platform = (
        sources[n]["path"] for n in ("core", "refinery", "platform")
    )
    # Execute only source-bound helper code; these checks inspect actual image,
    # executable, dependency notices, metadata and installed dependency bytes.
    runtime = load(
        core / "tools/runtime_artifact.py", "offline_runtime_artifact"
    ).validate(core, core_prepared)
    dependency_helper = load(
        refinery / "tools/offline_dspy.py", "offline_dependency_artifact"
    )
    dependency_record = json.loads(
        (refinery / "offline/dependencies.json").read_bytes()
    )
    if dependency_helper.inventory(refinery / "local/python-deps") != dependency_record:
        raise RuntimeError("offline dependency preparation mismatch")
    sys.path.insert(0, str(platform))
    try:
        stream = load(
            platform / "tools/streaming_bundle.py", "qualified_streaming_bundle"
        )
    finally:
        sys.path.pop(0)
    pins = {name: item["commit"] for name, item in sources.items()}
    files, licenses = {}, {}

    def add(name, path, *, notice=False):
        path = Path(path)
        if not path.is_file() or path.is_symlink() or name in files:
            raise RuntimeError("unavailable or duplicate bundle source: " + name)
        files[name] = path
        if notice:
            licenses[name] = stream.file_sha(path)

    for name, item in sources.items():
        for relative in ("LEGAL.md", "component.json", "provenance.json"):
            add(
                "components/" + name + "/" + relative,
                item["path"] / relative,
                notice=relative == "LEGAL.md",
            )
    for relative in (
        "docs/runtime-build.json",
        "docs/runtime-dependencies.json",
        "Cargo.lock",
        "temporal/toolchain.json",
    ):
        add("core/" + relative, core / relative)
    executable = Path(core_prepared) / "temporal-runtime"
    if stream.file_sha(executable) != runtime["binary_sha256"]:
        raise RuntimeError("qualified core binary mismatch")
    add("bin/temporal-runtime", executable)
    for path in sorted((Path(core_prepared) / "notices").iterdir()):
        add("notices/core/" + path.name, path, notice=True)
    for path in sorted((core / "licenses").rglob("*")):
        if path.is_file():
            add(
                "notices/core-source/" + str(path.relative_to(core / "licenses")),
                path,
                notice=True,
            )
    for name in subprocess.check_output(
        ["git", "ls-files", "refinery"], cwd=refinery, text=True
    ).splitlines():
        if name.endswith(".py"):
            add("refinery/" + name, refinery / name)
    for relative in (
        "offline/dependencies.json",
        "offline/toolchain.json",
        "offline/requirements.lock",
        "offline/python-LICENSE",
        "offline/tokenizers-LICENSE",
    ):
        add(
            "refinery/" + relative,
            refinery / relative,
            notice=relative.endswith("LICENSE"),
        )
    for name in dependency_record["installed_files"]:
        add(
            "dependencies/" + name,
            refinery / "local/python-deps" / name,
            notice=any(
                part.upper().startswith(("LICENSE", "COPYING", "NOTICE", "UNLICENSE"))
                for part in Path(name).parts
            ),
        )
    for relative in ("tools/development_bundle.py", "tools/streaming_bundle.py"):
        add("platform/" + relative, platform / relative)
    for relative in (
        "contracts/maintained-evidence-v1.json",
        "contracts/streaming-development-bundle-v1.json",
        "tools/maintained_lane_worker.py",
        "tools/run_saved_offline_bundle.py",
    ):
        add("composition/" + relative, ROOT / relative)
    with tempfile.TemporaryDirectory(prefix="offline-bundle-config-") as temporary:
        marker = Path(temporary) / "variant.txt"
        marker.write_text(
            variant
            + "\nSynthetic installation recovery fixture; no authority or code change.\n"
        )
        add("development/variant.txt", marker)
        return stream.build(
            destination,
            subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
            ).strip(),
            pins,
            files,
            dependencies={
                "core/inventory": "sha256:"
                + stream.file_sha(core / "docs/runtime-dependencies.json"),
                "refinery/inventory": "sha256:"
                + stream.file_sha(refinery / "offline/dependencies.json"),
                "python/runtime": dependency_helper.IMAGE.split("@")[1],
            },
            toolchains={
                "core/builder": runtime["builder_image_id"],
                "core/toolchain": "sha256:"
                + stream.file_sha(core / "temporal/toolchain.json"),
                "python/runtime": dependency_helper.IMAGE.split("@")[1],
            },
            licenses=licenses,
            entrypoints={"core": "bin/temporal-runtime"},
            executable=["bin/temporal-runtime"],
        )


def main():
    from maintained_scenarios import inventory

    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--component", action="append", default=[])
    parser.add_argument("--core-prepared", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    sources = inventory(
        json.loads(Path(args.manifest).read_bytes()),
        dict(v.split("=", 1) for v in args.component),
    )
    manifest, digest = build(args.output, sources, args.core_prepared)
    print(
        json.dumps(
            {
                "status": "built_development_only",
                "manifest_sha256": digest,
                "files": len(manifest["files"]),
                "payload_bytes": sum(r["size"] for r in manifest["files"].values()),
                "unsupported": manifest["unsupported"],
            }
        )
    )


if __name__ == "__main__":
    main()
