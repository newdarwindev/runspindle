"""Validate authored presentation scope without executing TeX.

This narrow static check is not a TeX parser or an execution sandbox. Independent
exact-hash review and a separately approved confined build remain required.
"""

import hashlib
import json
import re
from pathlib import Path
from typing import Any, cast

BASE_COMMIT = "bbc3b06fd0528ae604687dc84683a10b4304eede"
BASE_TREE = "ed428ef02b9d3be35bced3a5c305def22dccdba1"
SOURCE_IDS = ["SRC-003", "SRC-004"]
KEYS = ["webarena", "workarena", "xstest", "orbench", "taubench", "agentsmatter"]
SHARED = [
    "accepted-work",
    "diagnosis",
    "effort",
    "market",
    "economics",
    "durability",
    "references",
]
LOCAL = ["mechanism", "comparison", "evidence"]
TEX_FILES = (
    {"argument.tex", "fleet.tex", "presentations/style.tex"}
    | {f"presentations/shared/{name}.tex" for name in SHARED}
    | {
        f"presentations/{deck}/{name}.tex"
        for deck in ("argument", "fleet")
        for name in LOCAL
    }
)
SOURCE_FILES = TEX_FILES | {
    "SRC-003-004-disposition.json",
    "SRC-003-004-citations.json",
    "SRC-003-004-build-plan.json",
}
UNITS = (
    {"P00", "B01"}
    | {f"S{i:02}" for i in range(1, 10)}
    | {f"F{i:02}" for i in range(1, 8)}
    | {f"X{i:02}" for i in range(1, 11)}
)
STATUS_URL = "https://github.com/newdarwindev/runspindle/blob/main/STATUS.json"
# Immutable inherited files and prior ReportLab companions, pinned during review.
PRESERVED: dict[str, str] = {
    "argument.pdf": "b1727d0db5cb9568e91f4beb90a0b38a496299eb17379e6443a92cc1b17cdcac",
    "economics.md": "207d9fa497c7196a890830f96eed7fd7f64e87f3f8c5133406d59b666a9132d4",
    "fleet.pdf": "8fc9565bc3f992fdb58f82bbcffa6d03aa33c2e1ae1e0143bbf69384ae4b5978",
    "overview.md": "01292d82130d6eb9dac474b158b1234d14cb71d2c558239b9390e07375e92bb9",
    "runspindle-paper.pdf": "71f08dce2ea2ae2682a4b2af306e6b1da54cdfd4863fd6297806ce5c5bf2e2fb",
    "runspindle-paper.tex": "7c7a4e79fe2ee1120826505eebaee7ba8cdde0935ffa49d7b7d99a0ffb5cdf03",
    "vision.html": "39a546f71fce360129b06e4978c589769d79b19a05d14917066dadf0816d41e7",
    "economics-model.md": "ff1cbbe3ad5610f42b2a82c4ce1fae1d2948f4b76a3c844605fc12681a8296c8",
    "LICENSE-SRC-010.txt": "fcf64df3e04554728cc4f082f244fa3dc672c2c6368f22360e6491a113204895",
    "SRC-010-lift.json": "80e4fbae10af2b29b9712cfc3c4754bda32266f5597940244ed9b998afa40e0d",
    "SRC-010-validation.md": "d551d121efb1525d8a73ef2f73099935ad9092c4f3ec38cb20a438debe20bb6b",
    "LICENSE-SRC-013.txt": "fcf64df3e04554728cc4f082f244fa3dc672c2c6368f22360e6491a113204895",
    "SRC-013-NOTICES.md": "f37a72d29b7054b180f65f5b1c99e13c3128ac2237d2cc15e725804910efeed3",
    "build-evidence.json": "6155bf4ffe8652163e4927ea2623cfea141666edb96811fddaf524badd740960",
    "build-paper.py": "6eee7d3513778e27e73a78bcb9424f5f5eae421c46324c3014239a4fae813891",
    "figures/01-identity.pdf": "1e2a2783b9aa72e6c8b7061dce2c7bc34d437d27c31902d560880770f3b85245",
    "figures/02-lifecycle.pdf": "aacfb658176506f7ccba445d6445ca13df85d71afcee155ea5a98bb4ee9a7e75",
    "figures/03-approval.pdf": "b8b6b7721e0933a08604c611da96bf5b3e6d57053c7bf88ecefcc5fac5b91704",
    "figures/04-golden-data.pdf": "1697092f98162f7959cc001d722285ff250d9121dd7789cf35e5f90f1f3c4f07",
    "figures/05-control-planes.pdf": "489ae57fb48e81a27021ff2011fe9ecb4681965a4dd0bf12a0c79260983616d4",
    "figures/06-constellation.pdf": "4f171412f6e0aa17507a2797aaf9f1e0b4ddb0e1240804901966bdd66440716a",
    "figures/07-provenance.pdf": "908563c718c4db8623c55db0b42a8f83f09f8815d956295d0eb683e93fd317ab",
    "figures/08-observation.pdf": "e3d956582e24f75146ec897111676730a5d35856966035ac89bca9974dd2fac3",
    "source-disposition.json": "bf013b827882cd6f04cd9b69a6cf2b4446fbae6765947aea9ea8d7453e14bcec",
    "toolchain-lock.json": "973aa9d445df8cbbf33ce2261905ab6e6e26f4930d5e2c01bcb66d88c60afb7c",
    "workflow-refinery.pdf": "e02963543d6fda11432a34b1fc625aae0baeb3022b67c91b4fb636e27daecbcf",
    "workflow-refinery.tex": "47b03a76a2a2c83d163297928920a708d26badff3595867b408da0f8a145ffb7",
    "refinery_mirror.py": "f1b102b75fa935969ad8330cf172d09540e3d52c03c8fe9f355bd82b3d5d200a",
    "SRC-013-integration.json": "8254c45fa3e39ea5a2f4b3bc4ae0cb50994f0a522241fc252222dc3129021bf0",
    "SRC-013-final-validation.json": "66dd681eb9e363446bf2150567edaaf8babd772247de2561d77e6093bccf40cc",
    "SRC-005-disposition.json": "18572b9fae3282b5a207df3c18636674067c82883c05508685ac53f41e96fc71",
    "SRC-005-review.md": "66fd9b23fc69f44f7f41cfd608895b1c4ae30412ce1fda1c36c98311d7db70d4",
    "SRC-005-validation.json": "84984789615c8e00d85a8d1560a86bca813650b64cf918a8cfaacad006a6cff1",
    "SRC-002-build-plan.json": "b8edd23ebd32f8eeb96a5e0b4be0f1b57480c81bf953c73d5db10171596a8927",
    "SRC-002-citations.json": "fcd1bd0f80b3dd614afbde386743c84dc0a6d2dd83c3733cfc4c11d26986a3c6",
    "SRC-002-disposition.json": "f94f360dd605645970c48e778e11d22369be9259ffd4219548e8f644d1968bee",
    "SRC-002-review.md": "2f1f81f2712cfda3a135705412728d3dd267d83ba7cde84c71048c9d26ae8c5a",
    "SRC-002-source-receipt.json": "a60b6cddf0c4c0a909188bb89b8580d60a213b35a3f6c6239b6029eed68b347f",
    "paper/diagrams/comparison-contract.tex": "12ae466758e489563c7cfd0f700721fed70565404cfe635121f5370accec5155",
    "paper/diagrams/effort-ledger.tex": "a7b6b665d77832b0cf6f126c1632f4b5a5bb262c3804b5d68f92968f831afc95",
    "paper/diagrams/evaluation-register.tex": "02d8c787f963ecaea570df46648b91b02f04b8bf0d063b7bd439f841076bba40",
    "paper/diagrams/stop-triage.tex": "3b4065e983026e7837127c81b287c65985844cdb2184f112174d4f86a9c17044",
    "paper/diagrams/workflow-boundaries.tex": "4ad9437b29576046069e05b7aaa15a617196637ddcfd0cbacbfb23e819582c08",
    "paper/legacy/reportlab-paper.tex": "f2ec1b5bc4e4c85357dad8617a284294d970619828786f456f08bca58e0a5cff",
    "paper_source.py": "5cdd765843f4a13328d78a9db40a01b599cafcb68c695ec1493feb37a210bb34",
    "SRC-002-validation.json": "da8194979c1bd1ea43bde1990254cbe1e1ff2594127afced23631d139c512335",
    "paper/history/source-receipt-7fca776.json": "2ebb63e91c91ec68ca7eae5601fff7265328975ecb3015b050b4b91fa55f52e0",
    "paper/history/validation-7fca776.json": "c839ecc173b13430150b75aae897ee42f07f1eb44ad9ba765c9aefddb9f74d43",
    "paper/history/source-receipt-b1b4f9c.json": "a852429eff5ed57cb15ba740bfd7348ef8cf150a3e83a7ea4624f263d27a0ccc",
    "paper/history/validation-b1b4f9c.json": "9b4d833cac3114d4373147645794a3fe0458104bdc87260f1a879054420a7d09",
    "presentations/legacy/argument-reportlab.tex": "f82e8cbd628f8595a2e30e0003019575ad11ea560daef4e9fb84b56185c5b26c",
    "presentations/legacy/fleet-reportlab.tex": "9cfee958c6700005e2ffce8595697b6bd12785f206c3d63ccd9e447123ae2316",
}


# Current paper-only correction; immutable presentation-era PRESERVED stays historical.
CURRENT_PAPER_PROTECTED: dict[str, str] = {
    "runspindle-paper.tex": "c8424f8ab26cc0146bfa98da57daee6d386b92d747fb0223c7b4afd235068f29",
    "paper_source.py": "94d3401e4f4da40ba21173cf0c8e4799d112323ec4de3ce395e276fc196b05a7",
    "SRC-002-source-receipt.json": "6a7cb0013eaa7371852834a8b3a9b42b03b07bd4c7d78632d03a328dc7335cb5",
    "SRC-005-disposition.json": "e694f8731573e057ab32ea52d3e07871ef35b3dcefc67ab24d42f6d27c6d294c",
    "SRC-002-wrap-correction.json": "14f30abb0b745430cf408b5d14219d0943bb5a8bdec56f8027e98fcc45548ca4",
    "paper/history/source-receipt-2f37dc9.json": "a60b6cddf0c4c0a909188bb89b8580d60a213b35a3f6c6239b6029eed68b347f",
    "paper/history/economics-disposition-2f37dc9.json": "18572b9fae3282b5a207df3c18636674067c82883c05508685ac53f41e96fc71",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError("SRC-003/004: " + message)


def regular_file(folder: Path, name: str) -> Path:
    path = folder / name
    require(
        not Path(name).is_absolute() and ".." not in Path(name).parts,
        "unsafe file path",
    )
    require(
        not any(p.is_symlink() for p in (path, *path.parents)),
        "symlink in closure: " + name,
    )
    require(path.is_file(), "missing file: " + name)
    return path


def digest(folder: Path, name: str) -> str:
    return hashlib.sha256(regular_file(folder, name).read_bytes()).hexdigest()


def document(folder: Path, name: str) -> dict[str, Any]:
    data = json.loads(regular_file(folder, name).read_text())
    require(isinstance(data, dict), "expected JSON object: " + name)
    return cast(dict[str, Any], data)


def deck_inputs(deck: str) -> list[str]:
    return [
        "presentations/style.tex",
        "presentations/shared/accepted-work.tex",
        "presentations/shared/diagnosis.tex",
        "presentations/shared/effort.tex",
        f"presentations/{deck}/mechanism.tex",
        "presentations/shared/market.tex",
        f"presentations/{deck}/comparison.tex",
        "presentations/shared/economics.tex",
        "presentations/shared/durability.tex",
        f"presentations/{deck}/evidence.tex",
        "presentations/shared/references.tex",
    ]


def deck_labels(deck: str) -> list[str]:
    mechanism = (
        ["argument-mechanism"]
        if deck == "argument"
        else ["fleet-identity", "fleet-observation", "fleet-control"]
    )
    return [
        "opening",
        "accepted-work",
        "diagnosis",
        "effort",
        *mechanism,
        "market",
        f"{deck}-comparison",
        "economics",
        "durability",
        f"{deck}-evidence",
        "references-web",
        "references-evaluation",
    ]


def slide_targets(deck: str, page: int) -> list[str]:
    if page == 5:
        return (
            ["argument-mechanism"]
            if deck == "argument"
            else ["fleet-identity", "fleet-observation", "fleet-control"]
        )
    return [
        ["opening"],
        ["accepted-work"],
        ["diagnosis"],
        ["effort"],
        [],
        ["market"],
        [f"{deck}-comparison"],
        ["economics"],
        ["durability"],
        [f"{deck}-evidence"],
    ][page - 1]


def verify_presentation_source(folder: Path) -> dict[str, object]:
    receipt = document(folder, "SRC-003-004-source-receipt.json")
    require(receipt["source_ids"] == SOURCE_IDS, "source identity")
    require(
        receipt["base_commit"] == BASE_COMMIT and receipt["base_tree"] == BASE_TREE,
        "dependent parent",
    )
    for key, expected in {
        "status": "source_prepared_native_compile_not_run",
        "native_compile": "not_run",
        "pdf_matches_authored_source": False,
        "migration_status": "partial",
        "live_acceptance": "not_run",
    }.items():
        require(receipt[key] == expected, "unperformed evidence: " + key)
    require(receipt["preserved_files"] == PRESERVED, "preserved file identities")
    for name, expected_hash in (PRESERVED | CURRENT_PAPER_PROTECTED).items():
        require(
            digest(folder, name) == expected_hash, "preserved bytes changed: " + name
        )
    sources = receipt["source_files"]
    require(set(sources) == SOURCE_FILES, "authored source closure")
    manifest = document(folder, "artifacts.json")["artifacts"]
    for name, expected_hash in sources.items():
        require(
            digest(folder, name) == expected_hash, "authored hash mismatch: " + name
        )
        entries = [e for e in manifest if e["path"] == "docs/marketing/" + name]
        require(
            len(entries) == 1 and entries[0]["sha256"] == expected_hash,
            "manifest identity: " + name,
        )
        require(
            set(SOURCE_IDS) <= set(entries[0]["source_ids"]), "manifest scope: " + name
        )
        require(
            entries[0]["historical_original"] is False
            and entries[0]["implementation_evidence"] is False,
            "source evidence class: " + name,
        )
    for deck in ("argument", "fleet"):
        pair = receipt["pdf_pairing"][deck]
        legacy = f"presentations/legacy/{deck}-reportlab.tex"
        require(
            pair
            == {
                "pdf": deck + ".pdf",
                "pdf_sha256": PRESERVED[deck + ".pdf"],
                "legacy_source": legacy,
                "legacy_source_sha256": PRESERVED[legacy],
                "renderer": "ReportLab 4.4.9 / Python 3.12.14",
                "native_tex_compiled": False,
                "authored_source_matches_old_pdf": False,
            },
            "old PDF pairing",
        )
        entries = [e for e in manifest if e["path"] == f"docs/marketing/{deck}.pdf"]
        require(
            len(entries) == 1
            and entries[0]["sha256"] == PRESERVED[deck + ".pdf"]
            and entries[0]["kind"]
            == "preserved_prior_ReportLab_pdf_not_authored_source_rendering",
            "stale PDF manifest status",
        )
    texts = {name: regular_file(folder, name).read_text() for name in TEX_FILES}
    full = "\n".join(texts.values())
    for deck in ("argument", "fleet"):
        master = texts[deck + ".tex"]
        require(
            re.findall(r"\\documentclass(?:\[[^]]*\])?\{([^}]+)\}", master)
            == ["beamer"],
            "document class",
        )
        inputs = re.findall(r"\\input\{([^}]+)\}", master)
        require(inputs == deck_inputs(deck), "ordered deck input closure")
        require(
            len(re.findall(r"\\input(?![A-Za-z])", master)) == len(inputs),
            "unbraced or undeclared input",
        )
        expanded = re.sub(r"\\input\{([^}]+)\}", lambda m: texts[m[1]], master)
        labels = re.findall(r"\\begin\{frame\}\[label=([^]]+)\]", expanded)
        require(labels == deck_labels(deck), "frame coverage or label order")
        require(
            len(re.findall(r"\\begin\{frame\}", expanded)) == len(labels),
            "undeclared frame",
        )
        require(
            receipt["authored_frame_counts"][deck] == len(labels), "source frame count"
        )
    fragments = "\n".join(
        v for k, v in texts.items() if k not in {"argument.tex", "fleet.tex"}
    )
    require(not re.search(r"\\input(?![A-Za-z])", fragments), "nested TeX input")
    require(
        not re.search(
            r"\\(?:write|openin|openout|read|immediate|directlua|special|include|includegraphics|bibliography|bibliographystyle|catcode|csname)(?![A-Za-z])",
            full,
        ),
        "unexpected TeX primitive or dependency",
    )
    packages = [
        x
        for group in re.findall(r"\\usepackage(?:\[[^]]*\])?\{([^}]+)\}", full)
        for x in group.split(",")
    ]
    require(sorted(packages) == ["fontenc", "lmodern"], "direct package closure")
    for name, body in texts.items():
        # Basic environment consistency only, not proof that TeX will compile.
        stack: list[str] = []
        for action, env in re.findall(r"\\(begin|end)\{([^}]+)\}", body):
            if action == "begin":
                stack.append(env)
            else:
                require(
                    bool(stack) and stack.pop() == env, "environment nesting: " + name
                )
        require(not stack, "unclosed environment: " + name)
    canonical = {
        c["key"]: c for c in document(folder, "SRC-002-citations.json")["citations"]
    }
    citations = document(folder, "SRC-003-004-citations.json")["citations"]
    require([c["key"] for c in citations] == KEYS, "citation closure")
    for citation in citations:
        prior = canonical[citation["key"]]
        require(
            all(citation[k] == v for k, v in prior.items() if k != "number"),
            "citation attribution drift",
        )
        require(citation["source_expression_imported"] is False, "citation rights")
    urls = set(re.findall(r"\\href\{([^}]+)\}", full))
    require(
        urls == {canonical[k]["url"] for k in KEYS} | {STATUS_URL}, "link allowlist"
    )
    economics = texts["presentations/shared/economics.tex"]
    for token in (
        "C=M+T+H+V+K+R+F",
        "U=C/A",
        "A>0",
        "At $A=0$, unit cost is undefined",
        "including when $C=0$",
        "Each cost appears once",
        "Failures still cost money",
    ):
        require(token in economics, "economics invariant")
    require(
        receipt["economics_body_sha256"]
        == "aaf6527918e8d73d35e3340cfec0c7615dba715531f97cc2422305b4d3f66a72",
        "canonical economics identity",
    )
    scope = document(folder, "SRC-003-004-disposition.json")
    require(
        scope["migration_status"] == "partial"
        and scope["source_expression_imported"] is False,
        "disposition status",
    )
    units = scope["source_bundle_units"]
    require(
        len(units) == 28 and {u["id"] for u in units} == UNITS,
        "28-file bundle accounting",
    )
    for unit in units:
        require(
            unit["source_expression_copied"] is False and bool(unit["reason"]),
            "unit rights or reason",
        )
        require(bool(unit["destinations"]), "missing unit destination")
        for name in unit["destinations"]:
            regular_file(folder, name)
    slides = scope["source_slides"]
    require(
        len(slides) == 20
        and {(s["source_id"], s["original_page"]) for s in slides}
        == {(sid, n) for sid in SOURCE_IDS for n in range(1, 11)},
        "20 original-slide accounting",
    )
    for slide in slides:
        deck = "argument" if slide["source_id"] == "SRC-003" else "fleet"
        require(
            slide["destination"] == deck + ".tex"
            and bool(slide["frame_labels"])
            and set(slide["frame_labels"]) <= set(deck_labels(deck)),
            "slide destination",
        )
        require(
            slide["frame_labels"] == slide_targets(deck, slide["original_page"]),
            "original slide mapping",
        )
        require(
            slide["source_expression_copied"] is False and bool(slide["reason"]),
            "slide rights or reason",
        )
    require(
        scope["bibliography_disposition"]["cited_primary_keys"] == KEYS,
        "cited reference accounting",
    )
    require(
        set(scope["bibliography_disposition"]["unused_paper_only_keys"])
        == set(canonical) - set(KEYS),
        "unused reference accounting",
    )
    plan = document(folder, "SRC-003-004-build-plan.json")
    require(
        plan["native_compile"] == "not_run"
        and plan["dependency_closure_complete"] is False
        and plan["installation"] == "none_requested_or_performed"
        and plan["observed_toolchain_files"] == [],
        "unperformed native build/inventory",
    )
    require(
        set(plan["authored_tex_inputs"]) == TEX_FILES
        and plan["direct_packages"] == ["fontenc", "lmodern"]
        and plan["binary_assets"] == []
        and plan["document_class"] == "beamer 11pt aspectratio=169",
        "build proposal closure",
    )
    return {
        "source_ids": SOURCE_IDS,
        "status": "passed",
        "evidence_class": "static_source_integrity",
        "original_slide_instances": 20,
        "retained_bundle_units": 28,
        "authored_tex_inputs": len(TEX_FILES),
        "authored_frames": {"argument": 12, "fleet": 14},
        "native_compile": "not_run",
        "pdf_matches_authored_source": False,
        "migration_status": "partial",
        "live_acceptance": "not_run",
    }
