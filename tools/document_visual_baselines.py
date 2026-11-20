#!/usr/bin/env python3
"""Build and compare confined, source-derived paper and deck review candidates."""

import argparse
import hashlib
import importlib
import json
import math
import pathlib
import platform
import re
import resource
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
MARKETING = ROOT / "docs/marketing"
CONFIG = MARKETING / "document-visual-toolchain.json"
OUTPUTS = {
    "paper": ("runspindle-paper", "SRC-002", "SRC-002-disposition.json"),
    "argument": ("argument", "SRC-003", "SRC-003-004-disposition.json"),
    "fleet": ("fleet", "SRC-004", "SRC-003-004-disposition.json"),
}
NAMESPACE = {"x": "http://www.w3.org/1999/xhtml"}


def require(condition: object, message: str) -> None:
    if not condition:
        raise ValueError(message)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_json(path: pathlib.Path) -> dict[str, Any]:
    value: dict[str, Any] = json.loads(path.read_bytes())
    return value


def file_digests(root: pathlib.Path) -> dict[str, str]:
    files = {}
    for path in sorted(root.rglob("*")):
        require(not path.is_symlink(), "symlink in input or output tree")
        if path.is_file():
            files[path.relative_to(root).as_posix()] = digest(path.read_bytes())
    return files


def confined_source() -> dict[str, str]:
    paper = read_json(MARKETING / "SRC-002-build-evidence.json")
    decks = read_json(MARKETING / "SRC-003-004-source-receipt.json")
    files = dict(paper["compiled_inputs"])
    files.update(
        {
            name: sha
            for name, sha in decks["source_files"].items()
            if name.endswith(".tex")
        }
    )
    for name, sha in files.items():
        path = MARKETING / name
        require(
            path.is_file()
            and not path.is_symlink()
            and path.resolve().is_relative_to(MARKETING)
            and digest(path.read_bytes()) == sha,
            f"unverified authored TeX input {name}",
        )
    return files


def stage_source(files: dict[str, str], folder: pathlib.Path) -> None:
    for name, sha in files.items():
        data = (MARKETING / name).read_bytes()
        require(digest(data) == sha, f"authored input changed during staging: {name}")
        path = folder / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)


def pinned_programs(config: dict[str, Any]) -> dict[str, pathlib.Path]:
    tools = {}
    for name, expected in config["tool_sha256"].items():
        selected = shutil.which(name)
        require(selected, f"missing local tool {name}")
        path = pathlib.Path(str(selected)).resolve()
        require(digest(path.read_bytes()) == expected, f"unexpected bytes for {name}")
        tools[name] = path
    return tools


def command(
    args: list[str], *, cwd: pathlib.Path, environment: dict[str, str] | None = None
) -> bytes:
    result = subprocess.run(
        args,
        cwd=cwd,
        env=environment,
        capture_output=True,
        timeout=45,
        check=False,
    )
    if result.returncode:
        detail = (result.stdout + result.stderr).decode(errors="replace")[-6000:]
        raise ValueError(
            f"{pathlib.Path(args[0]).name} exited {result.returncode}:\n{detail}"
        )
    return result.stdout


def sandbox_rule(operation: str, path: pathlib.Path) -> str:
    return f"(allow {operation} (subpath {json.dumps(str(path))}))"


def compile_tex(
    tools: dict[str, pathlib.Path],
    profile: dict[str, Any],
    source: pathlib.Path,
    home: pathlib.Path,
    output: pathlib.Path,
    name: str,
) -> dict[str, Any]:
    scratch = source.parent
    sandbox = "\n".join(
        [
            "(version 1)",
            "(allow default)",
            "(deny network*)",
            '(deny file-read-data (subpath "/Users") (subpath "/Volumes") (subpath "/private/var/folders"))',
            f'(deny file-read-data (require-all (subpath "/private/tmp") '
            f"(require-not (subpath {json.dumps(str(scratch))}))))",
            "(deny file-write*)",
            sandbox_rule("file-write*", output),
        ]
    )
    env = {
        "HOME": str(home),
        "TMPDIR": str(output),
        "PATH": "/usr/bin:/bin",
        "LC_ALL": "C",
        "TZ": "UTC",
        "SOURCE_DATE_EPOCH": str(profile["source_date_epoch"]),
    }
    command(
        [
            str(tools["sandbox-exec"]),
            "-p",
            sandbox,
            str(tools["tectonic"]),
            "-C",
            "--untrusted",
            "--keep-logs",
            "--makefile-rules",
            str(output / f"{name}.d"),
            "-o",
            str(output),
            "-b",
            profile["bundle_url"],
            f"{name}.tex",
        ],
        cwd=source,
        environment=env,
    )
    log = (output / f"{name}.log").read_text(errors="replace")
    overflow = re.findall(r"Overfull \\[hv]box.*", log)
    dependencies = [
        pathlib.Path(path)
        for path in (output / f"{name}.d").read_text().split()
        if path.endswith(".tex")
    ]
    paths = sorted(
        (path.relative_to(output) if path.is_absolute() else path).as_posix()
        for path in dependencies
    )
    require(f"{name}.tex" in paths, f"no recorded root TeX source for {name}")
    require(
        all(
            (source / path).resolve().is_relative_to(source)
            and (source / path).is_file()
            for path in paths
        ),
        f"unexpected TeX input for {name}",
    )
    return {"overfull_boxes": overflow, "authored_inputs": paths}


def word_inside(word: ET.Element, width: float, height: float) -> bool:
    x0, y0, x1, y1 = (
        float(word.attrib[key]) for key in ("xMin", "yMin", "xMax", "yMax")
    )
    return (
        all(math.isfinite(value) for value in (x0, y0, x1, y1))
        and -0.5 <= x0 < x1 <= width + 0.5
        and -0.5 <= y0 < y1 <= height + 0.5
    )


def inspect_pdf(
    tools: dict[str, pathlib.Path], pdf: pathlib.Path
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    def call(name: str, *args: str) -> bytes:
        return command([str(tools[name]), *args], cwd=pdf.parent)

    info = call("pdfinfo", str(pdf)).decode()
    require(
        "JavaScript:      no" in info and "Encrypted:       no" in info,
        "unexpected PDF features",
    )
    root = ET.fromstring(call("pdftotext", "-bbox-layout", str(pdf), "-"))
    measurements = []
    for index, page in enumerate(root.findall(".//x:page", NAMESPACE), 1):
        width, height = float(page.attrib["width"]), float(page.attrib["height"])
        words = page.findall(".//x:word", NAMESPACE)
        require(words, f"page {index} has no extractable words")
        require(
            all(word_inside(word, width, height) for word in words),
            f"page {index} clips a word",
        )
        require(
            not any("\ufffd" in "".join(word.itertext()) for word in words),
            f"unmapped glyph on page {index}",
        )
        smallest = min(
            float(word.attrib["yMax"]) - float(word.attrib["yMin"]) for word in words
        )
        measurements.append(
            {
                "page": index,
                "geometry_points": [width, height],
                "words": len(words),
                "smallest_word_box_points": round(smallest, 3),
            }
        )
    matched = re.search(r"^Pages:\s+(\d+)", info, re.M)
    require(
        matched and int(matched[1]) == len(measurements),
        "page count and text extraction differ",
    )
    font_lines = call("pdffonts", str(pdf)).decode().splitlines()[2:]
    require(
        font_lines and all(line.split()[-5] == "yes" for line in font_lines),
        "unembedded font",
    )
    urls = [
        line.split(None, 2)[2]
        for line in call("pdfinfo", "-url", str(pdf)).decode().splitlines()[1:]
        if line.strip()
    ]
    require(
        urls and all(re.fullmatch(r"https://[^\s]+", url) for url in urls),
        "invalid or missing external link",
    )
    return measurements, {
        "tagged_pdf": bool(re.search(r"^Tagged:\s+yes$", info, re.M)),
        "embedded_fonts": sorted(line.split()[0] for line in font_lines),
        "external_link_targets": sorted(set(urls)),
    }


def contact_sheet(pages: list[pathlib.Path], path: pathlib.Path) -> None:
    image = importlib.import_module("PIL.Image")
    draw_api = importlib.import_module("PIL.ImageDraw")
    tile_width = 360
    thumbnails = []
    for page in pages:
        with image.open(page) as png:
            thumb = png.convert("RGB")
            thumb.thumbnail((tile_width, 440), image.Resampling.LANCZOS)
            thumbnails.append(thumb)
    tile_height = max(thumb.height for thumb in thumbnails) + 26
    columns = 3
    rows = math.ceil(len(pages) / columns)
    sheet = image.new(
        "RGB",
        (columns * (tile_width + 20) + 20, rows * (tile_height + 15) + 15),
        "#e6e8e7",
    )
    draw = draw_api.Draw(sheet)
    for index, thumb in enumerate(thumbnails):
        x, y = (
            20 + index % columns * (tile_width + 20),
            15 + index // columns * (tile_height + 15),
        )
        draw.text((x, y), f"{index + 1:02d}", fill="#102f21")
        sheet.paste(thumb, (x, y + 20))
    sheet.save(path)


def render(
    tools: dict[str, pathlib.Path],
    profile: dict[str, Any],
    pdf: pathlib.Path,
    folder: pathlib.Path,
) -> dict[str, Any]:
    folder.mkdir()
    shutil.copyfile(pdf, folder / "candidate.pdf")
    command(
        [
            str(tools["pdftoppm"]),
            "-png",
            "-r",
            str(profile["dpi"]),
            str(pdf),
            str(folder / "page"),
        ],
        cwd=folder,
    )
    pages, observations = inspect_pdf(tools, pdf)
    pngs = sorted(folder.glob("page-*.png"))
    require(len(pngs) == len(pages), "page count and raster output differ")
    contact_sheet(pngs, folder / "contact-sheet.png")
    text = command([str(tools["pdftotext"]), "-layout", str(pdf), "-"], cwd=folder)
    (folder / "text.txt").write_bytes(text)
    return {"pages": pages, **observations}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-home", required=True, type=pathlib.Path)
    parser.add_argument("--output", required=True, type=pathlib.Path)
    parser.add_argument("--compare", type=pathlib.Path)
    args = parser.parse_args()
    profile = read_json(CONFIG)
    require(
        platform.machine() == profile["arch"]
        and platform.mac_ver()[0] == profile["macos"],
        "render profile differs",
    )
    require(not args.output.exists(), "use a new output directory")
    require(
        importlib.import_module("PIL").__version__ == profile["pillow"],
        "contact-sheet library differs",
    )
    cache = args.cache_home.resolve()
    cache_files = file_digests(cache)
    require(cache_files == profile["cache_sha256"], "prepared dependency bytes differ")
    tools = pinned_programs(profile)
    source_inputs = confined_source()
    resource.setrlimit(resource.RLIMIT_FSIZE, (150_000_000, 150_000_000))
    with tempfile.TemporaryDirectory(
        dir="/private/tmp", prefix="runspindle-document-review-"
    ) as temporary:
        scratch = pathlib.Path(temporary)
        source, home, compile_dir = (
            scratch / "src",
            scratch / "home",
            scratch / "compile",
        )
        stage_source(source_inputs, source)
        shutil.copytree(cache, home)
        require(
            file_digests(home) == cache_files,
            "prepared dependencies changed during staging",
        )
        compile_dir.mkdir()
        reference = scratch / "reference"
        reference.mkdir()
        git_sha = command(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip()
        for key, (tex, sid, disposition) in OUTPUTS.items():
            compile_observations = compile_tex(
                tools, profile, source, home, compile_dir, tex
            )
            facts = render(tools, profile, compile_dir / f"{tex}.pdf", reference / key)
            if key == "paper":
                expected_links = read_json(MARKETING / "SRC-002-build-evidence.json")[
                    "native_review"
                ]["uri_targets"]
            else:
                expected_links = [
                    row["url"]
                    for row in read_json(MARKETING / "SRC-003-004-citations.json")[
                        "citations"
                    ]
                ] + ["https://github.com/newdarwindev/runspindle/blob/main/STATUS.json"]
            require(
                facts["external_link_targets"] == sorted(set(expected_links)),
                f"link targets differ for {key}",
            )
            receipt = {
                "source": f"docs/marketing/{tex}.tex",
                "source_id": sid,
                "disposition": disposition,
                "commit": git_sha,
                "source_hashes": {
                    name: source_inputs[name]
                    for name in compile_observations["authored_inputs"]
                },
                "disposition_sha256": digest((MARKETING / disposition).read_bytes()),
                "profile_sha256": digest(CONFIG.read_bytes()),
                "classification": "offline_tex_candidate",
                "review_status": "pending_confirmation",
                "previous_publication_sha256": digest(
                    (MARKETING / f"{tex}.pdf").read_bytes()
                ),
                "compile": compile_observations,
                "output": facts,
                "artifacts": file_digests(reference / key),
            }
            (reference / key / "receipt.json").write_text(
                json.dumps(receipt, indent=2, sort_keys=True) + "\n"
            )
            if args.compare:
                candidate_root = args.compare / key
                baseline = read_json(candidate_root / "receipt.json")
                for field in ("source_hashes", "compile", "output", "artifacts"):
                    require(
                        receipt[field] == baseline[field],
                        f"{key} reference differs in {field}",
                    )
                artifacts = file_digests(candidate_root)
                artifacts.pop("receipt.json")
                # Published review sets can omit the locally generated PDF.
                expected_artifacts = dict(receipt["artifacts"])
                if "candidate.pdf" not in artifacts:
                    expected_artifacts.pop("candidate.pdf")
                require(
                    artifacts == expected_artifacts,
                    f"{key} retained reference files differ",
                )
        shutil.copytree(reference, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
