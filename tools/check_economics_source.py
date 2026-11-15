"""Check SRC-005 scope and generated agreement, not empirical or legal claims."""

import ast
import hashlib
import json
from pathlib import Path
from typing import Any, cast

ROOT = Path(__file__).resolve().parents[1]
UNITS = {*(f"P{i:02}" for i in range(1, 7)), "E01", "D01", "D02", "C01", "C02", "C03"}
CITATIONS = {
    "agentsmatter": "https://arxiv.org/abs/2407.01502",
    "anthropic2026": "https://www.anthropic.com/research/harness-design-long-running-apps",
    "jcurve": "https://www.nber.org/papers/w25148",
}
DESTINATIONS = {
    "docs/marketing/economics.md",
    "docs/marketing/overview.md",
    "docs/marketing/runspindle-paper.tex",
    "docs/marketing/runspindle-paper.pdf",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError("SRC-005: " + message)


def document(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text())
    require(isinstance(value, dict), "expected an object: " + path.name)
    return cast(dict[str, Any], value)


def economics_text(root: Path) -> str:
    tree = ast.parse((root / "docs/marketing/build_documents.py").read_text())
    assignments = [
        node
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "sections" for t in node.targets)
    ]
    require(len(assignments) == 1, "ambiguous narrative source")
    sections = ast.literal_eval(assignments[0].value)
    require(
        isinstance(sections, list)
        and len(sections) > 6
        and sections[5][0] == "Economics of accepted work"
        and isinstance(sections[5][1], str),
        "missing economics narrative",
    )
    return cast(str, sections[5][1])


def check(root: Path) -> dict[str, object]:
    folder = root / "docs/marketing"
    body = economics_text(root)
    note = (folder / "economics.md").read_text()
    prefix = "# Runspindle economics\n\nStatus: proposed accounting model; no measured results.\n\n"
    require(
        note.startswith(prefix + body + "\n\nSource concept: SRC-005.\n"), "note drift"
    )
    tex = (folder / "runspindle-paper.tex").read_text()
    actual = tex.split("\\section{Economics of accepted work}\n", 1)[1].split(
        "\n\\section{", 1
    )[0]
    escaped = body.replace("&", r"\&").replace("%", r"\%").replace("_", r"\_")
    require(actual == escaped, "paper drift")
    overview = (folder / "overview.md").read_text()
    actual = overview.split("## Economics of accepted work\n\n", 1)[1].split(
        "\n\n## ", 1
    )[0]
    require(actual == body, "overview drift")
    require(
        (folder / "runspindle-paper.pdf").read_bytes().startswith(b"%PDF-"),
        "missing rendered paper",
    )

    data = document(folder / "SRC-005-disposition.json")
    require(
        data["source_id"] == "SRC-005" and data["bundle_source_id"] == "SRC-002",
        "source identity",
    )
    require(data["migration_status"] == "partial", "unresolved rights/build limits")
    require(
        data["historical_expression"] == "excluded_no_verified_reuse_license",
        "expression reuse",
    )
    require(
        data["historical_reference"]
        == "exact_selected_bytes_and_hashes_retained_privately",
        "private reference boundary",
    )
    units = data["units"]
    require(
        len(units) == len(UNITS) and {u["id"] for u in units} == UNITS,
        "incomplete or duplicate disposition",
    )
    for unit in units:
        require(unit["adaptation_marker"] in body, "missing concept: " + unit["id"])
        require(
            set(unit["destinations"]) == DESTINATIONS,
            "destination mapping: " + unit["id"],
        )
        require(bool(unit["review_decision"]), "missing review decision")
        require(
            unit["source_expression_copied"] is False, "ambiguous expression copied"
        )
    require(
        {
            u["id"]
            for u in units
            if u["disposition"] == "excluded_diagram_replaced_by_text"
        }
        == {"D01", "D02"},
        "diagram exclusions",
    )
    citations = data["citations"]
    require(
        len(citations) == 3 and {c["key"]: c["url"] for c in citations} == CITATIONS,
        "citation closure",
    )
    for citation in citations:
        require(
            citation["url"] in body and bool(citation["applicability_limit"]),
            "citation missing or unbounded",
        )
    model = data["executable_implementation"]
    require(
        model["historical_code_import"] == "none" and model["measurement"] == "not_run",
        "implementation evidence boundary",
    )
    require(
        data["verified_behavior"] == "synthetic_arithmetic_and_document_integrity_only",
        "unsupported verification",
    )

    manifest = document(folder / "artifacts.json")
    entries = {item["path"]: item for item in manifest["artifacts"]}
    require(set(data["result_files"]) == DESTINATIONS, "result hash mapping")
    for name, digest in data["result_files"].items():
        require(
            hashlib.sha256((root / name).read_bytes()).hexdigest() == digest,
            "result hash: " + name,
        )
        require(
            entries[name]["sha256"] == digest
            and "SRC-005" in entries[name]["source_ids"],
            "artifact association: " + name,
        )
    provenance = document(root / "provenance.json")
    sources = [s for s in provenance["sources"] if s["source_id"] == "SRC-005"]
    require(len(sources) == 1, "provenance identity")
    source = sources[0]
    require(
        source["migration_status"] == "partial"
        and source["disposition_map"] == "docs/marketing/SRC-005-disposition.json",
        "provenance scope",
    )
    require(
        source["verified_behavior"] == data["verified_behavior"],
        "provenance verification",
    )
    return {
        "source_id": "SRC-005",
        "status": "passed",
        "units": len(units),
        "evidence_class": "document_consistency_and_scope_integrity",
        "measurement": "not_run",
        "migration_status": "partial",
    }


if __name__ == "__main__":
    print(json.dumps(check(ROOT), sort_keys=True))
