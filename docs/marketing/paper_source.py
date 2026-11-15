"""Narrow source preflight, not a TeX parser or execution sandbox.

Exact hash review and separately approved external confinement are the execution
boundary. These checks never compile TeX or repeat a PDF review; they bind reviewed evidence.
"""

import ast
import hashlib
import json
import re
from pathlib import Path
from typing import Any, cast

PARENT = "ce7143962c341d81f07aa1217832c39c0996283b"
ECONOMICS_SHA = "aaf6527918e8d73d35e3340cfec0c7615dba715531f97cc2422305b4d3f66a72"
PRESERVED = {
    "runspindle-paper.pdf": "71f08dce2ea2ae2682a4b2af306e6b1da54cdfd4863fd6297806ce5c5bf2e2fb",
    "paper/legacy/reportlab-paper.tex": "f2ec1b5bc4e4c85357dad8617a284294d970619828786f456f08bca58e0a5cff",
    "economics.md": "207d9fa497c7196a890830f96eed7fd7f64e87f3f8c5133406d59b666a9132d4",
    "overview.md": "01292d82130d6eb9dac474b158b1234d14cb71d2c558239b9390e07375e92bb9",
    "SRC-005-review.md": "66fd9b23fc69f44f7f41cfd608895b1c4ae30412ce1fda1c36c98311d7db70d4",
    "SRC-005-validation.json": "84984789615c8e00d85a8d1560a86bca813650b64cf918a8cfaacad006a6cff1",
    "economics-model.md": "ff1cbbe3ad5610f42b2a82c4ce1fae1d2948f4b76a3c844605fc12681a8296c8",
    "paper/history/source-receipt-7fca776.json": "2ebb63e91c91ec68ca7eae5601fff7265328975ecb3015b050b4b91fa55f52e0",
    "paper/history/validation-7fca776.json": "c839ecc173b13430150b75aae897ee42f07f1eb44ad9ba765c9aefddb9f74d43",
    "paper/history/source-receipt-b1b4f9c.json": "a852429eff5ed57cb15ba740bfd7348ef8cf150a3e83a7ea4624f263d27a0ccc",
    "paper/history/validation-b1b4f9c.json": "9b4d833cac3114d4373147645794a3fe0458104bdc87260f1a879054420a7d09",
}
CURRENT_PRESERVED = PRESERVED | {
    "paper/history/source-receipt-2f37dc9.json": "a60b6cddf0c4c0a909188bb89b8580d60a213b35a3f6c6239b6029eed68b347f",
    "paper/history/economics-disposition-2f37dc9.json": "18572b9fae3282b5a207df3c18636674067c82883c05508685ac53f41e96fc71",
    "SRC-002-validation.json": "da8194979c1bd1ea43bde1990254cbe1e1ff2594127afced23631d139c512335",
}
# Current artifact transition; historical PRESERVED remains an immutable inventory.
CURRENT_PRESERVED = {
    name: value
    for name, value in CURRENT_PRESERVED.items()
    if name != "runspindle-paper.pdf"
} | {
    "paper/legacy/reportlab-paper.pdf": PRESERVED["runspindle-paper.pdf"],
    "paper/history/source-receipt-9844e5a.json": "6a7cb0013eaa7371852834a8b3a9b42b03b07bd4c7d78632d03a328dc7335cb5",
    "paper/history/economics-disposition-9844e5a.json": "e694f8731573e057ab32ea52d3e07871ef35b3dcefc67ab24d42f6d27c6d294c",
    "SRC-002-wrap-validation.json": "24ff7e350da2e679d9e25a5738a1119a4b9fb7ca1840b63b00d6728311c4094f",
}
COMPILED_PDF_SHA = "e463f5ea1d2df7301792d22c08485f9c5c6aaca17beda88eeaab2d326dbc5b23"
COMPILED_FILES: dict[str, str] = {
    "SRC-002-build-evidence.json": "a40ca528eb4232e38ee9e18d594ad47ad06cdd6f7522be553d27b08bafc34064",
    "SRC-002-toolchain.json": "12bd3e035745bc7596d899da1531531089a82052bee959486d151ddec67a7c3f",
    "SRC-002-NOTICES.md": "0d90ef26cf884d8be5bd47e92541b0828dfa208a5f23573f8444f240e2efc581",
    "SRC-002-COMPILED.md": "3803ed4c59920d6f3ec5a503a513dc6d6e9c90b730c56310cfba9dc4cc30e624",
}
WRAP_CORRECTION_SHA = "14f30abb0b745430cf408b5d14219d0943bb5a8bdec56f8027e98fcc45548ca4"
DIAGRAMS = {
    "paper/diagrams/comparison-contract.tex",
    "paper/diagrams/stop-triage.tex",
    "paper/diagrams/effort-ledger.tex",
    "paper/diagrams/workflow-boundaries.tex",
    "paper/diagrams/evaluation-register.tex",
}
SOURCE_FILES = DIAGRAMS | {
    "runspindle-paper.tex",
    "SRC-002-citations.json",
    "SRC-002-disposition.json",
    "SRC-002-build-plan.json",
}
CITATIONS = [
    "agentsmatter",
    "anthropic2026",
    "jcurve",
    "react",
    "sweagent",
    "xstest",
    "orbench",
    "webarena",
    "workarena",
    "taubench",
    "agentcompany",
    "compound",
    "anthropiceffective",
    "anthropiclong",
    "chatgptagent",
    "openaiagents",
    "genaiwork",
    "metr2026",
]
CITATION_URLS = [
    "https://arxiv.org/abs/2407.01502",
    "https://www.anthropic.com/research/harness-design-long-running-apps",
    "https://www.nber.org/papers/w25148",
    "https://arxiv.org/abs/2210.03629",
    "https://arxiv.org/abs/2405.15793",
    "https://arxiv.org/abs/2308.01263",
    "https://arxiv.org/abs/2405.20947",
    "https://arxiv.org/abs/2307.13854",
    "https://arxiv.org/abs/2403.07718",
    "https://arxiv.org/abs/2406.12045",
    "https://arxiv.org/abs/2412.14161",
    "https://bair.berkeley.edu/blog/2024/02/18/compound-ai-systems/",
    "https://www.anthropic.com/research/building-effective-agents",
    "https://www.anthropic.com/research/effective-harnesses-for-long-running-agents",
    "https://help.openai.com/en/articles/11752874-chatgpt-agent",
    "https://openai.github.io/openai-agents-python/",
    "https://academic.oup.com/qje/article/140/2/889/7990658",
    "https://metr.org/blog/2026-02-24-uplift-update/",
]
PACKAGES = {
    "geometry",
    "fontenc",
    "lmodern",
    "amsmath",
    "amssymb",
    "graphicx",
    "hyperref",
}
UNITS = (
    {"P00", "B01"}
    | {f"S{i:02}" for i in range(1, 10)}
    | {f"F{i:02}" for i in range(1, 8)}
    | {f"X{i:02}" for i in range(1, 11)}
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError("SRC-002: " + message)


def regular_file(folder: Path, name: str) -> Path:
    path = folder / name
    require(
        not Path(name).is_absolute() and ".." not in Path(name).parts,
        "unsafe relative file",
    )
    require(
        all(
            not parent.is_symlink()
            for parent in (path, *path.parents)
            if parent != folder.parent
        ),
        "symlink in source closure: " + name,
    )
    require(path.is_file(), "missing file: " + name)
    return path


def digest(folder: Path, name: str) -> str:
    return hashlib.sha256(regular_file(folder, name).read_bytes()).hexdigest()


def document(folder: Path, name: str) -> dict[str, Any]:
    data = json.loads(regular_file(folder, name).read_text())
    require(isinstance(data, dict), "expected object: " + name)
    return cast(dict[str, Any], data)


def economics_text(folder: Path) -> str:
    tree = ast.parse(regular_file(folder, "build_documents.py").read_text())
    assignments = [
        node
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "sections"
            for target in node.targets
        )
    ]
    require(len(assignments) == 1, "ambiguous economics source")
    sections = ast.literal_eval(assignments[0].value)
    require(isinstance(sections, list) and len(sections) > 5, "missing narrative")
    require(sections[5][0] == "Economics of accepted work", "economics heading")
    body = sections[5][1]
    require(isinstance(body, str), "economics narrative type")
    return cast(str, body)


def verify_paper_source(folder: Path) -> dict[str, object]:
    receipt = document(folder, "SRC-002-source-receipt.json")
    require(receipt["source_id"] == "SRC-002", "source identity")
    require(receipt["base_commit"] == PARENT, "unreviewed dependent parent")
    require(
        receipt["status"] == "compiled_candidate_pending_independent_review",
        "build status",
    )
    require(receipt["native_compile"] == "passed", "recorded native compile")
    require(receipt["pdf_matches_authored_source"] is True, "compiled PDF pairing")
    require(receipt["migration_status"] == "partial", "migration gate")
    require(receipt["live_acceptance"] == "not_run", "live evidence gate")
    require(receipt["preserved_files"] == CURRENT_PRESERVED, "preserved identities")
    for name, expected in CURRENT_PRESERVED.items():
        require(digest(folder, name) == expected, "preserved bytes changed: " + name)
    old = receipt["preserved_pdf"]
    require(
        old["path"] == "docs/marketing/paper/legacy/reportlab-paper.pdf"
        and old["renderer"] == "ReportLab 4.4.9 / Python 3.12.14"
        and old["source_commit"] == PARENT
        and old["generated_tex_sha256"] == PRESERVED["paper/legacy/reportlab-paper.tex"]
        and old["pdf_sha256"] == PRESERVED["runspindle-paper.pdf"]
        and old["renderer_sha256"]
        == "c1274f295a3836b71b05d2651ab8a6a8861a66192f33ca993ee3d87063899a73"
        and old["tex_compiled"] is False,
        "prior ReportLab identity",
    )
    files = receipt["source_files"]
    require(set(files) == SOURCE_FILES, "source dependency closure")
    manifest = document(folder, "artifacts.json")["artifacts"]
    for name, expected in files.items():
        require(digest(folder, name) == expected, "source hash mismatch: " + name)
        records = [a for a in manifest if a["path"] == "docs/marketing/" + name]
        require(len(records) == 1, "missing or duplicate manifest entry: " + name)
        require(records[0]["sha256"] == expected, "artifact hash mismatch: " + name)
        require("SRC-002" in records[0]["source_ids"], "source association: " + name)

    body = economics_text(folder)
    require(
        hashlib.sha256(body.encode()).hexdigest() == ECONOMICS_SHA, "economics drift"
    )
    master = regular_file(folder, "runspindle-paper.tex").read_text()
    split = master.split("\\section{Economics of accepted work}\n")
    require(len(split) == 2, "economics section missing or duplicate")
    actual = split[1].split("\n\\section{", 1)[0]
    escaped = body.replace("&", r"\&").replace("%", r"\%").replace("_", r"\_")
    require(actual == escaped, "economics section drift")
    integration = receipt["economics_integration"]
    require(
        integration["canonical_body_sha256"] == ECONOMICS_SHA
        and integration["narrative_changed"] is False
        and integration["old_container_sha256"]
        == PRESERVED["paper/legacy/reportlab-paper.tex"]
        and integration["new_container_sha256"]
        == digest(folder, "runspindle-paper.tex")
        and integration["economic_reference_keys_in_number_order"] == CITATIONS[:3]
        and integration["economic_diagram_expression"] == "excluded",
        "economics integration receipt",
    )
    require(len(re.findall(r"\\section\{", master)) == 9, "nine-section scope")
    require("@@" not in master, "unfinished source placeholder")
    packages = {
        item
        for group in re.findall(r"\\usepackage(?:\[[^]]*\])?\{([^}]+)\}", master)
        for item in group.split(",")
    }
    require(packages == PACKAGES, "unreviewed package requirements")
    inputs = re.findall(r"\\input\{([^}]+)\}", master)
    require(len(inputs) == len(DIAGRAMS) and set(inputs) == DIAGRAMS, "diagram closure")
    full = (
        master
        + "\n"
        + "\n".join(regular_file(folder, f).read_text() for f in sorted(DIAGRAMS))
    )
    require(
        len(re.findall(r"\\input(?![A-Za-z])", full)) == len(DIAGRAMS),
        "nested or undeclared TeX input",
    )
    require(
        receipt["historical_paper_dependencies"] == 18
        and receipt["authored_tex_inputs"]
        == {name: files[name] for name in sorted(DIAGRAMS | {"runspindle-paper.tex"})},
        "historical scope versus authored input closure",
    )
    require(
        not re.search(
            r"\\(?:write|openin|openout|read|immediate|directlua|special|include|includegraphics|bibliography|bibliographystyle|catcode|csname)(?![A-Za-z])",
            full,
        ),
        "unexpected TeX primitive or dependency",
    )
    labels = re.findall(r"\\label\{([^}]+)\}", full)
    refs = re.findall(r"\\(?:ref|pageref)\{([^}]+)\}", full)
    require(
        len(labels) == len(set(labels)) and set(refs) <= set(labels),
        "label reference closure",
    )
    require(
        re.findall(r"\\bibitem\{([^}]+)\}", master) == CITATIONS, "bibliography order"
    )
    cited = {
        key
        for group in re.findall(r"\\cite\{([^}]+)\}", master)
        for key in group.split(",")
    }
    require(cited == set(CITATIONS), "citation use closure")
    citations = document(folder, "SRC-002-citations.json")["citations"]
    require([c["key"] for c in citations] == CITATIONS, "citation review closure")
    require([c["url"] for c in citations] == CITATION_URLS, "reviewed citation URLs")
    for number, citation in enumerate(citations, 1):
        require(citation["number"] == number, "citation numbering")
        require(
            citation["source_type"] == "primary"
            and citation["source_expression_imported"] is False,
            "citation rights boundary",
        )
        require(
            bool(citation["applicability_limit"]) and citation["url"] in master,
            "citation applicability or link",
        )

    scope = document(folder, "SRC-002-disposition.json")
    units = scope["units"]
    require(
        len(units) == 28 and {u["id"] for u in units} == UNITS,
        "recursive disposition closure",
    )
    require(sum(u["in_paper_closure"] for u in units) == 18, "paper closure count")
    require(
        {u["id"] for u in units if u["in_paper_closure"]}
        == {name for name in UNITS if not name.startswith("X")},
        "paper closure membership",
    )
    require(scope["migration_status"] == "partial", "historical disposition gate")
    for unit in units:
        require(
            unit["source_expression_copied"] is False, "ambiguous expression imported"
        )
        require(
            bool(unit["reason"]) and bool(unit["destinations"]),
            "missing unit disposition",
        )
    require(
        {
            u["id"]
            for u in units
            if u["disposition"] == "excluded_diagram_concept_in_frozen_text"
        }
        == {"F05", "F06"},
        "economics figure exclusions",
    )
    plan = document(folder, "SRC-002-build-plan.json")
    require(
        plan["native_compile"] == "not_run"
        and plan["dependency_closure_complete"] is False,
        "native plan evidence",
    )
    require(
        plan["status"] == "proposed_native_build_requires_independent_review"
        and plan["passes_maximum"] == 2
        and plan["timeout_seconds_per_pass"] == 120,
        "unreviewed native action proposal",
    )
    require(
        {
            "-no-shell-escape",
            "-no-parse-first-line",
            "-no-mktex=tex",
            "-no-mktex=tfm",
            "-no-mktex=pk",
        }
        <= set(plan["proposed_command"]),
        "native action proposal flags",
    )
    require(
        all(
            plan["proposed_environment"].get(name) == "0"
            for name in (
                "shell_escape",
                "MKTEXFMT",
                "MKTEXTFM",
                "MKTEXPK",
                "MKTEXMF",
                "MKTEXTEX",
                "MKTEXOFM",
            )
        ),
        "automatic generation proposal",
    )
    require(set(plan["direct_packages"]) == PACKAGES, "build plan package drift")
    require(
        plan["installation"] == "none_requested_or_performed", "unexpected installation"
    )
    require(
        receipt["source_files"]["SRC-002-build-plan.json"]
        == digest(folder, "SRC-002-build-plan.json"),
        "build proposal hash",
    )
    require(
        digest(folder, "SRC-002-wrap-correction.json") == WRAP_CORRECTION_SHA,
        "wrapping transition receipt changed",
    )
    change = document(folder, "SRC-002-wrap-correction.json")
    require(
        change["corrected_source_native_compile"] == "not_run"
        and change["prior_diagnostic_output"]["accepted"] is False,
        "wrapping transition acceptance claim",
    )
    require(
        master.count(change["new_phrase"]) == 1 and change["old_phrase"] not in master,
        "wrapping correction occurrence",
    )
    require(
        hashlib.sha256(
            master.replace(change["new_phrase"], change["old_phrase"]).encode()
        ).hexdigest()
        == change["prior_source_sha256"]
        == "7c7a4e79fe2ee1120826505eebaee7ba8cdde0935ffa49d7b7d99a0ffb5cdf03"
        and digest(folder, "runspindle-paper.tex") == change["corrected_source_sha256"],
        "change exceeds the single reviewed wrapping correction",
    )
    revision = receipt["current_source_revision"]
    require(
        revision["base_commit"] == change["base_commit"]
        and revision["base_tree"] == change["base_tree"]
        and revision["change_receipt_sha256"] == WRAP_CORRECTION_SHA
        and revision["publication"] == "not_performed"
        and revision["native_compile"] == "passed",
        "current source transition mapping",
    )
    verify_compiled_output(folder, receipt)
    return {
        "source_id": "SRC-002",
        "status": "passed",
        "evidence_class": "static_source_and_compiled_artifact_integrity",
        "scope_units": 28,
        "historical_paper_dependencies": 18,
        "authored_tex_inputs": 6,
        "citations": 18,
        "native_compile": "passed",
        "pdf_matches_authored_source": True,
        "independent_final_review": "pending",
        "live_acceptance": "not_run",
        "migration_status": "partial",
    }


def verify_compiled_output(folder: Path, receipt: dict[str, Any]) -> None:
    """Bind exact output and sanitized records; do not execute or parse the PDF."""
    expected_names = {
        "SRC-002-build-evidence.json",
        "SRC-002-toolchain.json",
        "SRC-002-NOTICES.md",
        "SRC-002-COMPILED.md",
    }
    require(set(COMPILED_FILES) == expected_names, "compiled receipt pin closure")
    require(
        receipt["compiled_evidence_files"] == COMPILED_FILES, "compiled receipt pins"
    )
    for name, value in COMPILED_FILES.items():
        require(digest(folder, name) == value, "compiled evidence changed: " + name)
    require(
        digest(folder, "runspindle-paper.pdf") == COMPILED_PDF_SHA,
        "unreviewed compiled PDF bytes",
    )
    require(
        regular_file(folder, "runspindle-paper.pdf").stat().st_size == 248153,
        "compiled PDF size",
    )
    evidence = document(folder, "SRC-002-build-evidence.json")
    require(
        evidence["status"] == "compiled_candidate_pending_independent_review"
        and evidence["output"]
        == {
            "path": "docs/marketing/runspindle-paper.pdf",
            "sha256": COMPILED_PDF_SHA,
            "bytes": 248153,
            "pages": 12,
        },
        "compiled output evidence",
    )
    require(
        evidence["compiled_inputs"] == receipt["authored_tex_inputs"],
        "compiled input binding",
    )
    require(
        evidence["compiled_source"]["commit"]
        == "9844e5af51d03d7d1cd9e4284ce591ea2a00feff"
        and evidence["compiled_source"]["tree"]
        == "5ce7fe57377918aeba09d3ac6dfcea873a6d5440",
        "compiled local source identity",
    )
    require(
        evidence["whole_integration_tree_compiled"] is False,
        "unperformed integration-tree build claim",
    )
    require(
        evidence["native_review"]["uri_targets"] == CITATION_URLS,
        "compiled citation URL evidence",
    )
    require(
        evidence["native_review"]["annotations"]
        == {
            "total": 54,
            "uri_rectangles": 22,
            "unique_uri_targets": 18,
            "internal_goto": 32,
        },
        "compiled link counts",
    )
    toolchain = document(folder, "SRC-002-toolchain.json")
    known = toolchain["known_pins"]
    require(len(known) == 121, "known toolchain pin count")
    loaded = toolchain["loaded_stock_records"]
    require(
        len(loaded) == 104
        and len({row["loaded_path"] for row in loaded}) == 104
        and len({row["resolved_path"] for row in loaded}) == 103
        and all(known.get(row["resolved_path"]) == row["sha256"] for row in loaded),
        "loaded stock hash mismatch",
    )
    require(
        toolchain["pass_audits"]
        == [
            {
                "pass": i,
                "stock_loaded_paths": 104,
                "authored_inputs": 6,
                "expected_auxiliary_inputs": 2,
                "unknown_stock_inputs": 0,
            }
            for i in (1, 2)
        ],
        "loaded pass closure",
    )
    entries = document(folder, "artifacts.json")["artifacts"]
    for name, value in (
        COMPILED_FILES | {"runspindle-paper.pdf": COMPILED_PDF_SHA}
    ).items():
        matches = [row for row in entries if row["path"] == "docs/marketing/" + name]
        require(
            len(matches) == 1
            and matches[0]["sha256"] == value
            and "SRC-002" in matches[0]["source_ids"],
            "compiled artifact manifest binding: " + name,
        )
    pdf_record = next(
        row for row in entries if row["path"] == "docs/marketing/runspindle-paper.pdf"
    )
    require(
        pdf_record["kind"] == "compiled_original_paper_candidate"
        and pdf_record["implementation_evidence"] is False,
        "compiled PDF evidence classification",
    )
    require(
        receipt["independent_review"] == "pending"
        and receipt["publication"] == "not_performed_by_artifact_integration",
        "pending publication/review gates",
    )
