"""Verify a reviewed Browser derivative before any marketing generator writes."""

from __future__ import annotations

import ast
import hashlib
import json
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath
from typing import Any

CANONICAL = {
    "repository": "newdarwindev/runspindle-browser",
    "commit": "a5446d9fab1f2384b0d2ea0a051b7fd56a8af00b",
    "tree": "03f5e9d2f0388ea8f948de2b0c85e065eef877ba",
    "path": "docs/product/browser.html",
    "sha256": "afab98f2e8fab8ac27ef29e9ee2499ae2a2fffd9e2aa09fbdcb877bbb1ef2f9e",
}
TRANSFORMS = [
    {
        "id": "L01",
        "old": 'href="../../specs/synthetic-vault-fixtures.md"',
        "new": 'href="https://github.com/newdarwindev/runspindle-browser/blob/a5446d9fab1f2384b0d2ea0a051b7fd56a8af00b/specs/synthetic-vault-fixtures.md"',
        "occurrences": 1,
        "reason": "Keep this Browser-owned document at its verified immutable canonical location.",
    },
    {
        "id": "L02",
        "old": 'href="../../specs/effect-journal-v1.md"',
        "new": 'href="https://github.com/newdarwindev/runspindle-browser/blob/a5446d9fab1f2384b0d2ea0a051b7fd56a8af00b/specs/effect-journal-v1.md"',
        "occurrences": 1,
        "reason": "Keep this Browser-owned document at its verified immutable canonical location.",
    },
    {
        "id": "L03",
        "old": 'href="../../specs/trusted-credential-resolver.md"',
        "new": 'href="https://github.com/newdarwindev/runspindle-browser/blob/a5446d9fab1f2384b0d2ea0a051b7fd56a8af00b/specs/trusted-credential-resolver.md"',
        "occurrences": 1,
        "reason": "Keep this Browser-owned document at its verified immutable canonical location.",
    },
    {
        "id": "L04",
        "old": 'href="../../specs/openbao-kv-adapter.md"',
        "new": 'href="https://github.com/newdarwindev/runspindle-browser/blob/a5446d9fab1f2384b0d2ea0a051b7fd56a8af00b/specs/openbao-kv-adapter.md"',
        "occurrences": 1,
        "reason": "Keep this Browser-owned document at its verified immutable canonical location.",
    },
    {
        "id": "L05",
        "old": 'href="../../specs/credentials-handoff.md"',
        "new": 'href="https://github.com/newdarwindev/runspindle-browser/blob/a5446d9fab1f2384b0d2ea0a051b7fd56a8af00b/specs/credentials-handoff.md"',
        "occurrences": 1,
        "reason": "Keep this Browser-owned document at its verified immutable canonical location.",
    },
    {
        "id": "L06",
        "old": 'href="../../specs/desired-intent.md"',
        "new": 'href="https://github.com/newdarwindev/runspindle-browser/blob/a5446d9fab1f2384b0d2ea0a051b7fd56a8af00b/specs/desired-intent.md"',
        "occurrences": 1,
        "reason": "Keep this Browser-owned document at its verified immutable canonical location.",
    },
    {
        "id": "L07",
        "old": 'href="browser-source-review.md"',
        "new": 'href="https://github.com/newdarwindev/runspindle-browser/blob/a5446d9fab1f2384b0d2ea0a051b7fd56a8af00b/docs/product/browser-source-review.md"',
        "occurrences": 1,
        "reason": "Keep this Browser-owned document at its verified immutable canonical location.",
    },
    {
        "id": "L08",
        "old": 'href="THIRD_PARTY_NOTICES.md"',
        "new": 'href="https://github.com/newdarwindev/runspindle-browser/blob/a5446d9fab1f2384b0d2ea0a051b7fd56a8af00b/docs/product/THIRD_PARTY_NOTICES.md"',
        "occurrences": 1,
        "reason": "Keep this Browser-owned document at its verified immutable canonical location.",
    },
    {
        "id": "L09",
        "old": "The composition repository mirror remains pending.",
        "new": "This composition mirror records source and link normalization only; rendered and keyboard acceptance remain pending.",
        "occurrences": 1,
        "reason": "Replace the canonical snapshot's pending-mirror location statement without advancing rendered or keyboard acceptance.",
    },
    {
        "id": "L10",
        "old": "Canonical Browser source: this repository's docs/product/browser.html.",
        "new": 'Canonical Browser source: <a href="https://github.com/newdarwindev/runspindle-browser/blob/a5446d9fab1f2384b0d2ea0a051b7fd56a8af00b/docs/product/browser.html">runspindle-browser at the recorded revision</a>. This composition copy applies <a href="SRC-009-mirror.md">documented link and location normalization</a>.',
        "occurrences": 1,
        "reason": "Identify the actual canonical repository and disclose the normalized derivative at its new location.",
    },
]
EXTERNAL_LINKS = [
    "https://github.com/newdarwindev/runspindle-browser/blob/a5446d9fab1f2384b0d2ea0a051b7fd56a8af00b/docs/product/browser.html",
    "https://github.com/newdarwindev/runspindle-browser/blob/a5446d9fab1f2384b0d2ea0a051b7fd56a8af00b/specs/synthetic-vault-fixtures.md",
    "https://github.com/newdarwindev/runspindle-browser/blob/a5446d9fab1f2384b0d2ea0a051b7fd56a8af00b/specs/effect-journal-v1.md",
    "https://github.com/newdarwindev/runspindle-browser/blob/a5446d9fab1f2384b0d2ea0a051b7fd56a8af00b/specs/trusted-credential-resolver.md",
    "https://github.com/newdarwindev/runspindle-browser/blob/a5446d9fab1f2384b0d2ea0a051b7fd56a8af00b/specs/openbao-kv-adapter.md",
    "https://github.com/newdarwindev/runspindle-browser/blob/a5446d9fab1f2384b0d2ea0a051b7fd56a8af00b/specs/credentials-handoff.md",
    "https://github.com/newdarwindev/runspindle-browser/blob/a5446d9fab1f2384b0d2ea0a051b7fd56a8af00b/specs/desired-intent.md",
    "https://github.com/newdarwindev/runspindle-browser/blob/a5446d9fab1f2384b0d2ea0a051b7fd56a8af00b/docs/product/browser-source-review.md",
    "https://github.com/newdarwindev/runspindle-browser/blob/a5446d9fab1f2384b0d2ea0a051b7fd56a8af00b/docs/product/THIRD_PARTY_NOTICES.md",
]
VERIFICATION = {
    "source_mapping": "checked_separately",
    "rendered_desktop_mobile": "not_run",
    "keyboard_navigation": "not_run",
    "root_independent_review": "required_before_publication",
    "runtime": "not_run",
}
PINS = {
    "browser.html": "29e95738298a933c28de6ba1d9e38be6f5b330c2c6b920fce7d75c2668fb717e",
    "SRC-009-mirror.json": "2d2bcf66f300127f62725d53f2c5a8b72e2bfacb4330150134a66bbe0e477df7",
    "SRC-009-mirror.md": "82eb3200a074f57636630fbd85b0f58c007cc7040f635e3d02ae14b0dfd2be58",
}


def require(value: bool, reason: str) -> None:
    if not value:
        raise ValueError("SRC-009 mirror: " + reason)


def regular_file(folder: Path, name: str) -> Path:
    require(type(name) is str and bool(name), "invalid path")
    relative = PurePosixPath(name)
    require(
        not relative.is_absolute()
        and str(relative) == name
        and not set(relative.parts) & {".", ".."}
        and "\\" not in name,
        "unsafe path",
    )
    path = folder / name
    require(
        not any(item.is_symlink() for item in (path, *path.parents)) and path.is_file(),
        "missing or symlink file",
    )
    return path


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    data: dict[str, Any] = {}
    for key, value in pairs:
        require(key not in data, "duplicate JSON key")
        data[key] = value
    return data


def document(folder: Path, name: str) -> dict[str, Any]:
    data = json.loads(regular_file(folder, name).read_text(), object_pairs_hook=unique)
    require(type(data) is dict, "expected JSON object")
    return dict(data)


class Navigation(HTMLParser):
    """Extract navigation from already pinned HTML; not an HTML sanitizer."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: set[str] = set()
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        identity = values.get("id")
        if identity is not None:
            require(bool(identity) and identity not in self.ids, "duplicate HTML ID")
            self.ids.add(identity)
        if tag == "a":
            target = values.get("href")
            require(type(target) is str and bool(target), "anchor lacks target")
            self.links.append(str(target))


def check_navigation(folder: Path, body: str) -> None:
    page = Navigation()
    page.feed(body)
    page.close()
    local: set[str] = set()
    external: list[str] = []
    for target in page.links:
        if target.startswith("#"):
            require(target[1:] in page.ids, "missing page fragment")
        elif target in EXTERNAL_LINKS:
            external.append(target)
        else:
            require(
                target
                in {"index.html", "browser.html", "vision.html", "SRC-009-mirror.md"},
                "unreviewed navigation",
            )
            regular_file(folder, target)
            local.add(target)
    require(
        sorted(external) == sorted(EXTERNAL_LINKS), "canonical link closure changed"
    )
    require(
        local == {"index.html", "browser.html", "vision.html", "SRC-009-mirror.md"},
        "local navigation changed",
    )


def check_generator(folder: Path) -> None:
    tree = ast.parse(regular_file(folder, "build_documents.py").read_text())
    guard_names = [
        "verify_vision_mirror",
        "verify_refinery_mirror",
        "verify_paper_source",
        "verify_presentation_source",
        "verify_browser_mirror",
    ]
    guards: list[str] = []
    page_calls: list[str] = []
    for node in tree.body:
        if not isinstance(node, ast.Expr) or not isinstance(node.value, ast.Call):
            continue
        call = node.value
        if isinstance(call.func, ast.Name) and call.func.id in guard_names:
            require(
                len(call.args) == 1
                and isinstance(call.args[0], ast.Name)
                and call.args[0].id == "P",
                "guard call changed",
            )
            guards.append(call.func.id)
        if isinstance(call.func, ast.Name) and call.func.id == "page":
            require(guards == guard_names, "page write before all guards")
            require(
                bool(call.args)
                and isinstance(call.args[0], ast.Constant)
                and call.args[0].value == "index.html",
                "obsolete or unreviewed page writer",
            )
            page_calls.append("index.html")
        if isinstance(call.func, ast.Attribute) and call.func.attr in {
            "write_text",
            "write_bytes",
        }:
            require(guards == guard_names, "direct write before all guards")
            target = call.func.value
            require(
                isinstance(target, ast.BinOp)
                and isinstance(target.op, ast.Div)
                and isinstance(target.left, ast.Name)
                and target.left.id == "P"
                and isinstance(target.right, ast.Constant)
                and target.right.value
                in {"economics.md", "overview.md", "THIRD_PARTY_NOTICES.md"},
                "unreviewed direct output writer",
            )
    require(
        guards == guard_names and page_calls == ["index.html"],
        "guard or output inventory changed",
    )


def verify_browser_mirror(folder: Path) -> dict[str, object]:
    """Check exact source/link mapping, not rendered or runtime acceptance."""
    entries = document(folder, "artifacts.json")["artifacts"]
    require(type(entries) is list, "invalid artifact inventory")
    for name, expected in PINS.items():
        require(
            digest(regular_file(folder, name)) == expected, "unreviewed mirror bytes"
        )
        records = [
            item for item in entries if item.get("path") == "docs/marketing/" + name
        ]
        require(len(records) == 1, "missing or duplicate artifact record")
        item = records[0]
        require(
            item.get("sha256") == expected
            and item.get("source_ids") == ["SRC-009"]
            and item.get("historical_original") is False
            and item.get("implementation_evidence") is False,
            "artifact identity changed",
        )
        if name == "browser.html":
            require(
                item.get("canonical") == CANONICAL
                and item.get("transformation") == "docs/marketing/SRC-009-mirror.json"
                and item.get("verification") == VERIFICATION
                and item.get("kind") == "normalized_canonical_html",
                "canonical derivative metadata changed",
            )
        else:
            require(
                item.get("canonical") is None
                and item.get("kind") == "browser_mirror_accounting",
                "accounting misclassified",
            )
    receipt = document(folder, "SRC-009-mirror.json")
    require(
        receipt["canonical"] == CANONICAL
        and receipt["transforms"] == TRANSFORMS
        and receipt["verification"] == VERIFICATION,
        "receipt mapping changed",
    )
    require(
        receipt["relationship"]
        == "link_and_location_normalized_derivative_not_byte_identical"
        and receipt["destination_sha256"] == PINS["browser.html"],
        "derivative relationship changed",
    )
    body = regular_file(folder, "browser.html").read_text()
    reconstructed = body
    for row in reversed(TRANSFORMS):
        require(
            reconstructed.count(str(row["new"])) == 1, "replacement absent or ambiguous"
        )
        reconstructed = reconstructed.replace(str(row["new"]), str(row["old"]))
    require(
        hashlib.sha256(reconstructed.encode("utf-8")).hexdigest()
        == CANONICAL["sha256"],
        "canonical reconstruction failed",
    )
    check_navigation(folder, body)
    check_generator(folder)
    return {
        "source_id": "SRC-009",
        "status": "passed",
        "canonical_commit": CANONICAL["commit"],
        "canonical_sha256": CANONICAL["sha256"],
        "derivative_sha256": PINS["browser.html"],
        "transformations": len(TRANSFORMS),
        "external_navigation_targets": len(EXTERNAL_LINKS),
        "verification": VERIFICATION,
    }
