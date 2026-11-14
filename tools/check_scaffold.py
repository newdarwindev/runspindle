#!/usr/bin/env python3
"""Dependency-free structural checks. Passing is not product acceptance."""

import configparser, json, pathlib, re, subprocess, sys

root = pathlib.Path(__file__).resolve().parents[1]
required = [
    "README.md",
    "AGENTS.md",
    "component.json",
    "specs/README.md",
    "provenance.json",
    "STATUS.json",
]
for name in required:
    assert (root / name).is_file(), f"Missing {name}"
c = json.loads((root / "component.json").read_text())
s = json.loads((root / "STATUS.json").read_text())
assert c["stage"] == "scaffold"
assert s["implementation"] in {"not_implemented", "bounded_implementation"}
if s["implementation"] == "bounded_implementation":
    assert s["implementation_scope"] == "composition_evidence_reconciliation"
    assert s["integrated_system"] == "not_implemented"
    assert (root / "tools/reconcile_evidence.py").is_file()
    assert s["evidence_reconciliation"]["system_acceptance"] == "not_inferred"
assert s["live_acceptance"] == "not_run"
p = json.loads((root / "provenance.json").read_text())
for item in p["sources"]:
    assert re.fullmatch(r"SRC-[0-9]{3}", item["source_id"])
    assert item["status"] in [
        "adapted_spec",
        "adapted_document",
        "pending_review",
        "reference_only",
    ]
for path in (root / ".github/workflows").glob("*.yml"):
    text = path.read_text()
    lanes = re.findall(r"^\s*runs-on:\s*(.+)$", text, re.MULTILINE)
    allowed_lanes = {
        "[self-hosted, linux, x64, runspindle-isolated, strix]",
        "[self-hosted, linux, ARM64, runspindle-isolated, macbook]",
        "[self-hosted, macOS, ARM64, runspindle-isolated, macbook]",
    }
    assert lanes and all(lane in allowed_lanes for lane in lanes), path
    assert "pull_request_target:" not in text and "pull_request:" not in text, path
    assert "persist-credentials: false" in text, path
    assert "contents: read" in text, path
    for action in re.findall(r"uses:\s*([^\s]+)", text):
        assert re.fullmatch(r"[A-Za-z0-9_./-]+@[0-9a-f]{40}", action), (path, action)
    assert (
        "ubuntu-latest" not in text
        and "macos-latest" not in text
        and "windows-latest" not in text
    ), path
lock = json.loads((root / "composition.lock.json").read_text())
assert lock["schema_version"] == 1 and len(lock["components"]) == 7
modules = configparser.ConfigParser()
modules.read(root / ".gitmodules")
expected = {"core", "host", "browser", "tether", "refinery", "console", "platform"}
assert {item["component"] for item in lock["components"]} == expected
for item in lock["components"]:
    name = item["component"]
    path = "components/" + name
    assert item["path"] == path
    assert re.fullmatch(r"[0-9a-f]{40}", item["commit"])
    assert item["url"] == "https://github.com/newdarwindev/runspindle-" + name + ".git"
    section = 'submodule "' + path + '"'
    assert modules[section]["path"] == path and modules[section]["url"] == item["url"]
    entry = subprocess.check_output(
        ["git", "ls-files", "--stage", "--", path], cwd=root, text=True
    )
    assert entry.startswith("160000 " + item["commit"] + " 0\t"), path
subprocess.run([sys.executable, str(root / "tools/check_artifacts.py")], check=True)
print(
    json.dumps(
        {
            "status": "passed",
            "evidence_class": "scaffold_structure",
            "repository": c["repository"],
            "product_acceptance": "not_run",
        },
        sort_keys=True,
    )
)
