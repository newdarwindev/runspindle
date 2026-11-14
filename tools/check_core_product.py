#!/usr/bin/env python3
"""Validate selected requirement coverage, not operational product acceptance."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
COVERAGE = "docs/core-product/coverage.json"
MANIFEST = "docs/core-product/artifact-manifest.json"
README = "docs/core-product/README.md"
COMPOSITION_ISSUE = "https://github.com/newdarwindev/runspindle/issues/1"
COMPONENTS = {"core", "host", "browser", "tether", "refinery", "console", "platform"}
SECTION_COUNTS = {
    "scope": 1,
    "boundary": 5,
    "capabilities": 11,
    "interfaces": 5,
    "acceptance": 10,
    "maintenance": 7,
    "coordination": 7,
}
FILES = {
    COVERAGE,
    README,
    "specs/system.md",
    "tools/check_core_product.py",
    "tests/test_core_product.py",
    "tools/validate.py",
}
GATE_LANES = {
    "G01": "H02",
    "G02": None,
    "G03": None,
    "G04": None,
    "G05": "H07",
    "G06": "H08",
    "G07": "H10",
    "G08": "H11",
}
# These independent identifiers encode the reviewed requirement inventory.
# Their natural-language meaning is checked against the retained source in review.
REQUIRED_OBLIGATIONS: dict[str, tuple[str, ...]] = {
    "I01": ("scope",),
    "B01": ("outcome", "supporting_work"),
    "B02": ("separation",),
    "B03": ("execution",),
    "B04": ("learning",),
    "B05": ("authority",),
    "O01": ("labels",),
    "P01": ("scope", "trusted_origin", "deny", "privacy"),
    "P02": ("encryption", "restore", "retention"),
    "P03": ("binding", "uncertainty", "upstream"),
    "P04": ("fence", "handback", "recovery"),
    "P05": ("host_pin", "native_identity", "launch", "cancellation"),
    "P06": ("states", "bytes", "restart", "destination"),
    "P07": ("identity", "readback", "privacy"),
    "P08": ("freshness", "view", "authority"),
    "P09": ("lineage", "quarantine", "splits", "collection"),
    "P10": ("evaluation", "approval", "load", "rollback"),
    "C01": ("request", "host", "cancel"),
    "C02": ("reference", "observation", "handoff", "permission"),
    "C03": ("acceptance", "receipt", "reconcile"),
    "C04": ("envelope", "transport", "projection"),
    "C05": ("lineage", "evaluation", "serving"),
    "A00": ("isolation", "reuse"),
    "G01": ("evidence", "negative"),
    "G02": ("evidence", "negative"),
    "G03": ("evidence", "negative"),
    "G04": ("evidence", "negative"),
    "G05": ("evidence", "negative"),
    "G06": ("evidence", "negative"),
    "G07": ("evidence", "negative"),
    "G08": ("evidence", "negative"),
    "A09": ("states", "classes"),
    "M01": ("maintenance",),
    "M02": ("maintenance",),
    "M03": ("maintenance",),
    "M04": ("maintenance",),
    "M05": ("maintenance",),
    "M06": ("maintenance",),
    "M07": ("maintenance",),
    "X01": ("replacement",),
    "X02": ("replacement",),
    "X03": ("replacement",),
    "X04": ("replacement",),
    "X05": ("replacement",),
    "X06": ("replacement",),
    "X07": ("currency",),
}
REQUIRED_OWNERS: dict[str, tuple[str, ...]] = {
    "I01": ("core", "platform"),
    "B01": ("core", "host", "browser", "tether", "refinery", "console", "platform"),
    "B02": ("core", "refinery"),
    "B03": ("core", "host", "browser", "tether", "console"),
    "B04": ("refinery", "tether"),
    "B05": ("core", "browser", "refinery", "tether"),
    "O01": ("core", "platform"),
    "P01": ("browser", "platform"),
    "P02": ("browser",),
    "P03": ("browser", "core"),
    "P04": ("browser", "console"),
    "P05": ("core", "host"),
    "P06": ("core", "tether", "console"),
    "P07": ("platform", "host"),
    "P08": ("console", "core", "host", "browser", "platform"),
    "P09": ("refinery", "tether"),
    "P10": ("refinery",),
    "C01": ("core", "host", "tether"),
    "C02": ("browser", "core", "host", "console"),
    "C03": ("core", "tether", "console"),
    "C04": ("host", "platform", "console", "tether"),
    "C05": ("tether", "refinery"),
    "A00": ("core", "platform"),
    "G01": ("core", "host", "tether"),
    "G02": ("browser", "core"),
    "G03": ("browser", "console"),
    "G04": ("browser", "core"),
    "G05": ("core", "tether", "console"),
    "G06": ("platform", "host", "console"),
    "G07": ("tether", "refinery"),
    "G08": ("refinery",),
    "A09": ("core", "platform"),
    "M01": ("core", "platform"),
    "M02": ("core", "platform"),
    "M03": ("core", "platform"),
    "M04": ("core", "platform", "console"),
    "M05": ("core", "platform"),
    "M06": ("core", "platform"),
    "M07": ("core", "platform"),
    "X01": ("core", "platform"),
    "X02": ("core", "platform"),
    "X03": ("core", "platform"),
    "X04": ("core", "platform"),
    "X05": ("core", "platform"),
    "X06": ("core", "platform"),
    "X07": ("core", "platform"),
}
REQUIRED_TARGETS: dict[str, tuple[str, ...]] = {
    "I01": ("specs/system.md",),
    "B01": ("specs/system.md",),
    "B02": ("specs/system.md",),
    "B03": ("specs/system.md",),
    "B04": ("specs/system.md",),
    "B05": ("specs/system.md",),
    "O01": ("specs/system.md",),
    "P01": (
        "components/browser/specs/credentials-handoff.md",
        "components/platform/specs/native-monitoring.md",
    ),
    "P02": ("components/browser/specs/credentials-handoff.md",),
    "P03": (
        "components/browser/specs/credentials-handoff.md",
        "components/core/specs/contracts.md",
    ),
    "P04": (
        "components/browser/specs/credentials-handoff.md",
        "components/console/specs/fleet-view.md",
    ),
    "P05": (
        "components/core/specs/host-runtime.md",
        "components/host/specs/durable-lifecycle.md",
        "components/host/specs/native-sessions.md",
    ),
    "P06": (
        "components/core/specs/durable-artifacts.md",
        "components/core/specs/durable-delivery.md",
        "components/tether/specs/slack-events.md",
        "components/console/specs/fleet-view.md",
    ),
    "P07": (
        "components/platform/specs/native-monitoring.md",
        "components/host/specs/native-sessions.md",
    ),
    "P08": (
        "components/console/specs/fleet-view.md",
        "components/core/specs/contracts.md",
        "components/platform/specs/native-monitoring.md",
    ),
    "P09": (
        "components/refinery/specs/experiments.md",
        "components/refinery/specs/durable-offline.md",
        "components/tether/specs/slack-events.md",
    ),
    "P10": (
        "components/refinery/specs/experiments.md",
        "components/refinery/specs/durable-offline.md",
    ),
    "C01": (
        "specs/runtime-v1.md",
        "specs/runtime-integration-v1.md",
        "components/core/specs/host-runtime.md",
        "components/host/specs/durable-lifecycle.md",
    ),
    "C02": (
        "components/browser/specs/credentials-handoff.md",
        "specs/runtime-v1.md",
        "components/console/specs/fleet-view.md",
    ),
    "C03": (
        "specs/runtime-integration-v1.md",
        "components/core/specs/durable-artifacts.md",
        "components/core/specs/durable-delivery.md",
        "components/tether/specs/slack-events.md",
    ),
    "C04": (
        "components/platform/specs/native-monitoring.md",
        "components/console/specs/fleet-view.md",
        "specs/maintained-evidence-v1.md",
    ),
    "C05": (
        "components/refinery/specs/experiments.md",
        "components/refinery/specs/durable-offline.md",
        "specs/maintained-evidence-v1.md",
    ),
    "A00": ("docs/FIXTURE_KIT.md", "specs/runtime-integration-scenarios-v1.json"),
    "G01": ("docs/H02-integration-evidence.json", "specs/runtime-integration-v1.md"),
    "G02": ("components/browser/specs/credentials-handoff.md",),
    "G03": ("components/browser/specs/credentials-handoff.md",),
    "G04": ("components/browser/specs/credentials-handoff.md",),
    "G05": ("docs/H07-integration-evidence.json", "specs/runtime-integration-v1.md"),
    "G06": ("docs/MAINTAINED_OFFLINE.md", "specs/maintained-evidence-v1.md"),
    "G07": ("docs/FEEDBACK_HERO.md", "docs/MAINTAINED_OFFLINE.md"),
    "G08": ("docs/MAINTAINED_OFFLINE.md", "specs/maintained-evidence-v1.md"),
    "A09": ("docs/IMPLEMENTATION.md",),
    "M01": ("AGENTS.md", "specs/desired-intent.md"),
    "M02": ("AGENTS.md", "specs/desired-intent.md"),
    "M03": ("AGENTS.md", "specs/desired-intent.md"),
    "M04": ("AGENTS.md", "specs/desired-intent.md"),
    "M05": ("AGENTS.md", "specs/desired-intent.md"),
    "M06": ("AGENTS.md", "specs/desired-intent.md"),
    "M07": ("AGENTS.md", "specs/desired-intent.md"),
    "X01": ("specs/desired-intent.md",),
    "X02": ("specs/runtime-integration-v1.md",),
    "X03": ("specs/maintained-evidence-v1.md",),
    "X04": ("components/host/specs/native-sessions.md",),
    "X05": ("specs/desired-intent.md",),
    "X06": ("components/platform/specs/native-monitoring.md",),
    "X07": ("docs/IMPLEMENTATION.md",),
}

REQUIRED_SECTIONS: dict[str, str] = {
    "I01": "scope",
    "B01": "boundary",
    "B02": "boundary",
    "B03": "boundary",
    "B04": "boundary",
    "B05": "boundary",
    "O01": "capabilities",
    "P01": "capabilities",
    "P02": "capabilities",
    "P03": "capabilities",
    "P04": "capabilities",
    "P05": "capabilities",
    "P06": "capabilities",
    "P07": "capabilities",
    "P08": "capabilities",
    "P09": "capabilities",
    "P10": "capabilities",
    "C01": "interfaces",
    "C02": "interfaces",
    "C03": "interfaces",
    "C04": "interfaces",
    "C05": "interfaces",
    "A00": "acceptance",
    "G01": "acceptance",
    "G02": "acceptance",
    "G03": "acceptance",
    "G04": "acceptance",
    "G05": "acceptance",
    "G06": "acceptance",
    "G07": "acceptance",
    "G08": "acceptance",
    "A09": "acceptance",
    "M01": "maintenance",
    "M02": "maintenance",
    "M03": "maintenance",
    "M04": "maintenance",
    "M05": "maintenance",
    "M06": "maintenance",
    "M07": "maintenance",
    "X01": "coordination",
    "X02": "coordination",
    "X03": "coordination",
    "X04": "coordination",
    "X05": "coordination",
    "X06": "coordination",
    "X07": "coordination",
}

GATE_REQUIREMENTS: dict[str, list[str]] = {
    "G01": ["P05", "C01"],
    "G02": ["P01", "P02", "P03", "C02"],
    "G03": ["P04", "C02"],
    "G04": ["P03", "C02"],
    "G05": ["P06", "C03"],
    "G06": ["P07", "P08", "C04"],
    "G07": ["P09", "C05"],
    "G08": ["P10", "C05"],
}
RELATED_EVIDENCE = "Existing bounded results remain at their own exact revisions; they do not establish this full slice or transfer to newer code."


class CoverageError(ValueError):
    """An integrity, completeness, scope or privacy gate did not pass."""


def require(condition: object, message: str) -> None:
    if not condition:
        raise CoverageError(message)


def mapping(value: object, label: str) -> dict[str, Any]:
    require(isinstance(value, dict), f"{label}: expected object")
    if not isinstance(value, dict):
        raise CoverageError(label)
    require(all(isinstance(k, str) for k in value), f"{label}: invalid key")
    return value


def sequence(value: object, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise CoverageError(f"{label}: expected list")
    return value


def string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CoverageError(f"{label}: expected nonempty text")
    return value


def document(root: Path, name: str) -> dict[str, Any]:
    return mapping(json.loads(safe_file(root, name).read_text()), name)


def safe_file(root: Path, name: str) -> Path:
    relative = Path(name)
    require(not relative.is_absolute() and ".." not in relative.parts, "unsafe target")
    path = root / relative
    require(path.is_file() and not path.is_symlink(), f"missing regular file: {name}")
    require(path.resolve().is_relative_to(root.resolve()), "target escapes repository")
    return path


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def scoped_provenance(root: Path) -> dict[str, Any]:
    records = sequence(document(root, "provenance.json").get("sources"), "sources")
    selected = [
        mapping(v, "source")
        for v in records
        if mapping(v, "source").get("source_id") == "SRC-001"
    ]
    require(len(selected) == 1, "SRC-001 provenance must be unique")
    return selected[0]


def provenance_digest(root: Path) -> str:
    content = json.dumps(scoped_provenance(root), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(content.encode()).hexdigest()


def render_system(data: dict[str, Any]) -> str:
    lines = [
        "# Runspindle system contract",
        "",
        "This is the complete reviewed SRC-001 requirement adaptation, not a report",
        "of implemented or deployed behavior. Original source identity and hashes stay",
        "in the private source record. [Coverage and rights review](../docs/core-product/README.md)",
        "records the per-unit dispositions and reproducible artifact checks.",
        "",
        "## Current repository boundaries",
        "",
        "| Component | Responsibility |",
        "|---|---|",
        "| core | Rust/Temporal admission, durable coordination and accepted artifact receipts |",
        "| host | Explicit machine/workspace binding and actual native sessions |",
        "| browser | OpenBao-scoped secrets, encrypted profiles, PinchTab and fenced KasmVNC control |",
        "| tether | Existing sanitized event/delivery and feedback integration |",
        "| refinery | Python DSPy, replayable lineage, evaluation and approved serving |",
        "| console | Actual observed views and freshness-aware projections, never authority |",
        "| platform | Pinned upstream composition, local CI and target-specific distribution/rollback |",
        "",
        "These are seven ownership/release boundaries, not seven required microservices.",
        "Reuse Temporal, OpenBao, PinchTab, KasmVNC, standard Collectors, Langfuse and DSPy.",
        "Do not introduce Slack Bolt, Presidio, Argilla or a separate Playwright service.",
        "Versioned fixture, runtime, integration and maintained-evidence contracts retain",
        "their existing meanings; the identifiers below introduce no runtime wire enums.",
        "",
        "## Requirement and disposition inventory",
        "",
        "Every source requirement and navigation reference has one stable opaque unit.",
        "The JSON inventory is canonical; this section is a deterministic readable projection.",
        "Owning specs are the pinned component versions in composition.lock.json, not",
        "unqualified remote main branches. Full-slice gates below are not_run; related",
        "bounded evidence retains its original scope and does not transfer to this lift.",
        "",
    ]
    for item in sequence(data.get("records"), "records"):
        row = mapping(item, "record")
        unit = string(row.get("id"), "id")
        lines.extend(
            [
                f"### {unit}: {row['title']}",
                "",
                f"Disposition: **{row['disposition']}**. {row['reason']}",
                "",
                "Owners: " + ", ".join(row["owners"]) + ".",
                "",
            ]
        )
        for statement in mapping(row.get("obligations"), unit).values():
            lines.extend(["- " + string(statement, unit)])
        lines.extend(
            [
                "",
                "Targets: "
                + "; ".join(f"[{path}](../{path})" for path in row["targets"])
                + ".",
                "",
            ]
        )
        if "gate" in row:
            gate = mapping(row["gate"], unit)
            lane = gate["existing_lane"] or "no qualified integrated lane"
            lines.extend(
                [
                    f"Full-slice status: **{gate['full_slice_status']}**; evidence class: "
                    f"{gate['evidence_class']}. Existing lane reference: {lane}.",
                    "",
                    "Requirements: " + ", ".join(gate["requirements"]) + ". "
                    f"Reuse [composition issue #1]({COMPOSITION_ISSUE}). "
                    + gate["related_evidence"],
                    "",
                ]
            )
    return "\n".join(lines)


def check_privacy(text: str) -> None:
    require(
        not re.search(
            r"(?<![A-Za-z0-9])/(?:home|Users|workspace|private-provenance)/", text
        ),
        "private filesystem location",
    )
    require(
        not re.search(
            r"(?:xox[baprs]-[A-Za-z0-9-]{10,}|sk-[A-Za-z0-9]{20,}|"
            r"-----BEGIN [A-Z ]*PRIVATE KEY-----)",
            text,
        ),
        "credential pattern",
    )
    for repository in re.findall(
        r"https://github\.com/[^/\s\"<>]+/([^/\s\"<>]+)", text
    ):
        require(
            repository in {"runspindle", *("runspindle-" + c for c in COMPONENTS)},
            "uncleared repository reference",
        )


def validate(root: Path) -> dict[str, object]:
    data = document(root, COVERAGE)
    manifest = document(root, MANIFEST)
    require(
        data.get("schema_version") == 1 and data.get("source_id") == "SRC-001",
        "unsupported coverage identity",
    )
    require(data.get("scope") == "selected_core_product_artifact_only", "scope changed")
    require(data.get("artifact_status") == "accounted_adaptation", "artifact status")
    require(data.get("source_expression_imported") is False, "source import claim")
    require(
        data.get("executable_implementation") == "not_changed", "implementation claim"
    )
    require(data.get("verified_runtime_behavior") == "not_claimed", "runtime claim")
    require(
        data.get("historical_source")
        == "retained_privately_with_original_identity_and_hash",
        "original identity must remain private and preserved",
    )
    require(
        "no blanket license" in string(data.get("rights"), "rights"), "rights scope"
    )
    require(
        data.get("source_section_counts") == SECTION_COUNTS, "source section counts"
    )
    rows = [mapping(v, "record") for v in sequence(data.get("records"), "records")]
    ids = [string(row.get("id"), "id") for row in rows]
    require(
        ids == list(REQUIRED_OBLIGATIONS), "missing, duplicate or reordered source unit"
    )
    require(
        Counter(row.get("source_section") for row in rows) == SECTION_COUNTS,
        "source section allocation",
    )
    for row in rows:
        unit = row["id"]
        require(
            row.get("source_section") == REQUIRED_SECTIONS[unit],
            f"{unit}: source section",
        )
        string(row.get("title"), unit)
        string(row.get("reason"), unit)
        require(
            row.get("disposition")
            == ("excluded" if unit in {f"X{n:02}" for n in range(1, 7)} else "adapted"),
            f"{unit}: disposition",
        )
        require(row.get("owners") == list(REQUIRED_OWNERS[unit]), f"{unit}: ownership")
        require(
            row.get("targets") == list(REQUIRED_TARGETS[unit]),
            f"{unit}: target mapping",
        )
        for target in row["targets"]:
            safe_file(root, target)
        obligations = mapping(row.get("obligations"), unit)
        require(
            list(obligations) == list(REQUIRED_OBLIGATIONS[unit]),
            f"{unit}: obligations",
        )
        for value in obligations.values():
            string(value, unit)
        if unit in GATE_LANES:
            gate = mapping(row.get("gate"), unit)
            require(gate.get("existing_lane") == GATE_LANES[unit], f"{unit}: lane")
            require(
                gate.get("full_slice_status") == "not_run", f"{unit}: full-slice claim"
            )
            require(
                gate.get("evidence_class") == "requirement_not_execution",
                f"{unit}: class",
            )
            require(
                gate.get("composition_issue") == COMPOSITION_ISSUE, "duplicate harness"
            )
            require(
                gate.get("requirements") == GATE_REQUIREMENTS[unit],
                f"{unit}: gate bindings",
            )
            require(
                gate.get("related_evidence") == RELATED_EVIDENCE,
                "historical evidence transfer",
            )
        else:
            require("gate" not in row, f"{unit}: unexpected gate")
    pins = {
        v["component"]: v["commit"]
        for v in sequence(
            document(root, "composition.lock.json").get("components"), "components"
        )
    }
    require(
        set(pins) == COMPONENTS and data.get("component_pins") == pins, "component pins"
    )
    expected_specs = {
        p
        for values in REQUIRED_TARGETS.values()
        for p in values
        if p.startswith("components/")
    }
    spec_hashes = mapping(data.get("component_spec_hashes"), "spec hashes")
    require(set(spec_hashes) == expected_specs, "component spec inventory")
    for name, expected in spec_hashes.items():
        require(
            digest(safe_file(root, name)) == expected, f"component spec drift: {name}"
        )
    require(
        safe_file(root, "specs/system.md").read_text() == render_system(data),
        "system contract and coverage disagree",
    )
    source = scoped_provenance(root)
    require(
        source.get("status") == "adapted_spec",
        "source provenance status",
    )
    require(
        source.get("migration_status") == "selected_artifact_accounted",
        "source migration scope",
    )
    require(source.get("destination") == "specs/system.md", "source destination")
    require(
        source.get("coverage") == COVERAGE
        and source.get("artifact_manifest") == MANIFEST,
        "source provenance links",
    )
    require(
        manifest.get("source_id") == "SRC-001" and manifest.get("schema_version") == 1,
        "manifest identity",
    )
    require(
        manifest.get("artifact_status") == "accounted_adaptation",
        "manifest artifact status",
    )
    require(
        manifest.get("overall_migration_status") == "partial", "overall migration claim"
    )
    require(manifest.get("runtime_acceptance") == "not_run", "manifest runtime claim")
    require(
        manifest.get("provenance_record_sha256") == provenance_digest(root),
        "provenance hash",
    )
    files = mapping(manifest.get("file_sha256"), "file hashes")
    require(set(files) == FILES, "artifact file inventory")
    for name, expected in files.items():
        require(
            digest(safe_file(root, name)) == expected, f"artifact hash mismatch: {name}"
        )
    status = document(root, "STATUS.json")
    require(
        status.get("selected_source_migration") == "partial", "global migration status"
    )
    require(
        status.get("implementation") == "not_implemented",
        "integrated implementation claim",
    )
    require(status.get("live_acceptance") == "not_run", "live acceptance claim")
    aggregate = safe_file(root, "tools/validate.py").read_text()
    require(
        'run([sys.executable, "tools/check_core_product.py"])' in aggregate,
        "artifact checker must be mandatory in aggregate",
    )
    for name in (COVERAGE, MANIFEST, README, "specs/system.md"):
        check_privacy(safe_file(root, name).read_text())
    check_privacy(json.dumps(source))
    return {
        "source_id": "SRC-001",
        "status": "passed",
        "evidence_class": "artifact_validation",
        "source_units": len(rows),
        "capabilities": 10,
        "interfaces": 5,
        "gates": 8,
        "resolved_navigation_exclusions": 6,
        "runtime_acceptance": "not_run",
    }


def main() -> None:
    result = validate(ROOT)
    result["tested_commit"] = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()
    result["tracked_changes"] = bool(
        subprocess.check_output(
            ["git", "status", "--porcelain", "--untracked-files=all"],
            cwd=ROOT,
            text=True,
        )
    )
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
