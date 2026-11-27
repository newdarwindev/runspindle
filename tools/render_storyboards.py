#!/usr/bin/env python3
"""Render and verify original synthetic composition storyboards locally."""

import argparse
import hashlib
import html
import importlib
import io
import json
import pathlib
import platform
import re
import subprocess
from importlib import metadata
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
CONFIG = "visual/storyboards.json"
STYLE = "visual/storyboards.css"
SOURCE_FILES = [CONFIG, STYLE, "tools/render_storyboards.py", "requirements-visual.txt"]


def git(cwd: pathlib.Path, *args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=cwd, timeout=15)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def require(condition: object, reason: str) -> None:
    if not condition:
        raise ValueError(reason)


def source_inventory(config: dict[str, Any], console: pathlib.Path) -> dict[str, Any]:
    paths = {
        path: sha((ROOT / path).read_bytes())
        for path in [
            *SOURCE_FILES,
            "composition.lock.json",
            "fixtures/v1/manifest.json",
        ]
    }
    for path, digest in paths.items():
        require(
            sha(git(ROOT, "show", f"HEAD:{path}")) == digest,
            f"uncommitted input {path}",
        )
    lock = json.loads((ROOT / "composition.lock.json").read_bytes())
    pins = {}
    for component in lock["components"]:
        path, commit = component["path"], component["commit"]
        require(
            git(ROOT, "ls-files", "--stage", "--", path).startswith(
                f"160000 {commit} 0\t".encode()
            ),
            f"gitlink mismatch for {component['component']}",
        )
        pins[component["component"]] = commit
    require(len(pins) == 7, "missing composition pins")
    references = {}
    for family, root in (("tether", ROOT / "components/tether"), ("console", console)):
        reference = config["references"][family]
        require(
            family != "tether" or reference["commit"] == pins["tether"],
            "Tether visual revision differs from the composition pin",
        )
        data = git(root, "show", f"{reference['commit']}:{reference['source']}")
        artifact_digests = {}
        if family == "tether":
            states = {entry["id"] for entry in json.loads(data)["scenarios"]}
        else:
            fixture = reference["fixtures"]
            fixture_bytes = git(root, "show", f"{reference['commit']}:{fixture}")
            artifact_digests[fixture] = sha(fixture_bytes)
            states = {
                state.decode()
                for state in re.findall(rb'"([a-z][-a-z]+)"', data + fixture_bytes)
            }
            if (
                b"syntheticViewerFixtures" in fixture_bytes
                and b"simulated:" in fixture_bytes
            ):
                states.add("simulated")
        selected = {
            frame[5]
            for case in config["cases"]
            for frame in case["frames"]
            if frame[4] == family
        }
        require(
            selected <= states,
            f"missing canonical states in {family}",
        )
        if family == "tether":
            for state in sorted(selected):
                path = f"docs/visual-reference/{state}.png"
                artifact_digests[path] = sha(
                    git(root, "show", f"{reference['commit']}:{path}")
                )
        references[family] = {
            **reference,
            "sha256": sha(data),
            "assets": artifact_digests,
        }
    return {
        "composition_head": git(ROOT, "rev-parse", "HEAD").decode().strip(),
        "composition_pins": pins,
        "files": paths,
        "canonical_references": references,
    }


def render_html(config: dict[str, Any]) -> str:
    escape = html.escape
    sections = []
    navigation = []
    for case in config["cases"]:
        ident = escape(case["id"])
        parent = int(case["parent"])
        navigation.append(f'<a href="#{ident}">{escape(case["navigation"])}</a>')
        frames = []
        for surface, state, tone, description, family, canonical in case["frames"]:
            reference = config["references"][family]
            base = f"https://github.com/newdarwindev/{reference['repository']}/blob/{reference['commit']}"
            path = (
                f"docs/visual-reference/{canonical}.png"
                if family == "tether"
                else reference["source"]
            )
            if canonical == "simulated":
                path = reference["fixtures"]
            label = f"{surface} reference · {canonical}"
            frames.append(
                f'<li class="step {escape(tone)}"><p class="surface">{escape(surface)}</p>'
                f'<h3>{escape(state)}</h3><p class="detail">{escape(description)}</p>'
                f'<a class="reference" href="{escape(f"{base}/{path}")}">{escape(label)}</a></li>'
            )
        sections.append(
            f'<section class="case" id="{ident}" aria-labelledby="{ident}-title">'
            f'<div class="case-head"><h2 id="{ident}-title">{escape(case["title"])}</h2>'
            f'<a class="case-id" href="https://github.com/newdarwindev/runspindle/issues/{parent}">'
            f"SYNTHETIC · {ident.upper()} · ISSUE {parent}</a></div>"
            f'<p class="summary">{escape(case["intro"])}</p>'
            f'<ol class="steps">{"".join(frames)}</ol></section>'
        )
    identity = "".join(
        f"<div><dt>{escape(key)}</dt><dd>{escape(value)}</dd></div>"
        for key, value in config["identity"].items()
    )
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Runspindle workflow storyboards</title>
<style>{(ROOT / STYLE).read_text()}</style></head><body>
<header class="masthead"><div class="shell">
<div class="masthead-line"><span class="wordmark">RUNSPINDLE</span>
<span class="boundary">Synthetic visual reference</span></div>
<div class="hero"><h1>Workflow storyboards</h1>
<p>Follow one task across messages, session control, artifact delivery and fleet observation.</p></div>
<nav aria-label="Storyboard sections">{"".join(navigation)}</nav></div></header>
<main class="shell"><dl class="identity" aria-label="Shared synthetic identity">{identity}</dl>
{"".join(sections)}</main><footer class="shell">Actual application captures and behavioral acceptance are pending.</footer>
</body></html>
"""


def fits(page: Any) -> bool:
    return bool(
        page.evaluate("""() => {
      const width = window.innerWidth;
      const onScreen = box => box.left >= -1 && box.right <= width + 1;
      return document.documentElement.scrollWidth === document.documentElement.clientWidth
        && [...document.querySelectorAll('a, h1, h2, h3, .step, dd')].every(node => {
          const box = node.getBoundingClientRect();
          const text = document.createRange();
          text.selectNodeContents(node);
          return box.width > 0 && onScreen(box)
            && [...text.getClientRects()].every(onScreen);
        });
    }""")
    )


def capture(browser: Any, config: dict[str, Any], markup: str) -> dict[str, bytes]:
    profile = config["render_profile"]
    outputs = {}
    blocked: list[str] = []

    def deny(route: Any) -> None:
        blocked.append(route.request.url)
        route.abort()

    for width, height in profile["viewports"]:
        context = browser.new_context(
            viewport={"width": width, "height": height},
            device_scale_factor=profile["device_scale"],
            locale=profile["locale"],
            timezone_id=profile["timezone"],
            color_scheme="light",
            reduced_motion="reduce",
            service_workers="block",
        )
        try:
            context.route("**/*", deny)
            page = context.new_page()
            page.set_content(markup)
            page.evaluate("document.fonts.ready")
            require(fits(page), f"clipped or overflowing content at {width}px")
            require(
                page.get_by_role(
                    "heading", level=1, name="Workflow storyboards"
                ).count()
                == 1,
                "missing accessible page heading",
            )
            require(
                page.evaluate(r"""() => {
                  const rgb = paint => paint.match(/[\d.]+/g).map(Number);
                  const light = paint => rgb(paint).slice(0, 3).map(channel => {
                    const value = channel / 255;
                    return value <= .04045 ? value / 12.92 : ((value + .055) / 1.055) ** 2.4;
                  }).reduce((total, channel, index) => total + channel * [.2126, .7152, .0722][index], 0);
                  const background = node => {
                    const paint = getComputedStyle(node).backgroundColor;
                    return rgb(paint)[3] === 0 ? background(node.parentElement) : light(paint);
                  };
                  return [...document.querySelectorAll('a, h1, h2, h3, p, dt, dd, .boundary')]
                    .every(node => {
                      const foreground = light(getComputedStyle(node).color);
                      const back = background(node);
                      return (Math.max(foreground, back) + .05) /
                        (Math.min(foreground, back) + .05) >= 4.5;
                    });
                }"""),
                f"low text contrast at {width}px",
            )
            for case in config["cases"]:
                headings = page.locator(f"#{case['id']} h3").all_text_contents()
                require(
                    headings == [row[1] for row in case["frames"]],
                    "missing state label",
                )
            outputs[f"viewport-{width}.png"] = page.screenshot(animations="disabled")
            if width == 1440:
                outputs["contact-sheet.png"] = page.screenshot(full_page=True)
                for case in config["cases"]:
                    outputs[f"{case['id']}.png"] = page.locator(
                        f"#{case['id']}"
                    ).screenshot()
                page.evaluate("scrollTo(0, 0)")
            for link in page.get_by_role("navigation").get_by_role("link").all():
                page.keyboard.press("Tab")
                require(
                    link.evaluate("""node => {
                      const box = node.getBoundingClientRect();
                      return node === document.activeElement
                        && getComputedStyle(node).outlineStyle === 'solid'
                        && box.top >= 6 && box.bottom <= innerHeight - 6;
                    }"""),
                    f"keyboard navigation missed visible focus at {width}px",
                )
            page.keyboard.press("Enter")
            require(
                page.evaluate("location.hash") == "#h08", "keyboard activation failed"
            )
            if width == 390:
                page = context.new_page()
                page.set_content(markup)
                page.locator("dd").first.evaluate(
                    "node => node.textContent += '-long-unbroken-identity'.repeat(16)"
                )
                page.add_style_tag(content="html { zoom: 2; }")
                require(fits(page), "clipping at 200% zoom with long content")
                outputs["zoom-200.png"] = page.screenshot()
                page.add_style_tag(content="h1 { white-space: nowrap; }")
                require(
                    not fits(page), "heading text clipping mutation escaped detection"
                )
                page = context.new_page()
                page.set_content(markup)
                page.add_style_tag(content=".step { min-width: 1000px !important; }")
                require(not fits(page), "clipping mutation escaped detection")
        finally:
            context.close()
    require(not blocked, "unexpected external asset request")
    return outputs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--console-source", type=pathlib.Path, required=True)
    parser.add_argument("--browser", type=pathlib.Path, required=True)
    parser.add_argument("--output", type=pathlib.Path, required=True)
    parser.add_argument("--compare", type=pathlib.Path)
    args = parser.parse_args()
    require(
        not args.output.exists() or not any(args.output.iterdir()),
        "use an empty output directory",
    )
    config = json.loads((ROOT / CONFIG).read_bytes())
    profile = config["render_profile"]
    source = source_inventory(config, args.console_source)
    require(platform.mac_ver()[0] == profile["os"], "visual reference OS differs")
    require(
        platform.machine() == profile["arch"], "visual reference architecture differs"
    )
    require(
        metadata.version("playwright") == profile["playwright"],
        "Playwright version differs",
    )
    require(
        sha(args.browser.read_bytes()) == profile["chromium_sha256"],
        "browser bytes differ",
    )
    for font, digest in profile["fonts"].items():
        require(
            sha((pathlib.Path("/System/Library/Fonts") / font).read_bytes()) == digest,
            f"font bytes differ for {font}",
        )
    markup = render_html(config)
    playwright = importlib.import_module("playwright.sync_api")
    image = importlib.import_module("PIL.Image")
    image_chops = importlib.import_module("PIL.ImageChops")
    with playwright.sync_playwright() as driver:
        browser = driver.chromium.launch(
            executable_path=str(args.browser.resolve()),
            args=[
                "--disable-background-networking",
                "--host-resolver-rules=MAP * ~NOTFOUND",
            ],
            timeout=15_000,
        )
        try:
            require(browser.version == profile["chromium"], "Chromium version differs")
            first = capture(browser, config, markup)
            second = capture(browser, config, markup)
        finally:
            browser.close()
    require(
        first == second,
        "exact-pixel repeat differs in "
        + ", ".join(name for name in first if first[name] != second[name]),
    )
    baseline = image.open(io.BytesIO(first["contact-sheet.png"])).convert("RGB")
    repeated = image.open(io.BytesIO(second["contact-sheet.png"])).convert("RGB")
    difference = image_chops.difference(baseline, repeated)
    diff_bytes = io.BytesIO()
    difference.save(diff_bytes, format="PNG")
    assets = {
        **first,
        "repeat-diff.png": diff_bytes.getvalue(),
        "index.html": markup.encode(),
    }
    if args.compare:
        require(
            all(
                (args.compare / name).read_bytes() == data
                for name, data in assets.items()
            ),
            "candidate differs from the supplied reference",
        )
    args.output.mkdir(parents=True, exist_ok=True)
    for name, data in assets.items():
        (args.output / name).write_bytes(data)
    evidence = {
        "schema": config["schema"],
        "source": source,
        "render_profile": profile,
        "toolchain": {
            "python": platform.python_version(),
            "pillow": metadata.version("Pillow"),
            "greenlet": metadata.version("greenlet"),
        },
        "generation": "generated",
        "review": "candidate_pending_approval",
        "actual_render": "not_run",
        "behavioral_acceptance": "not_run",
        "coverage": {
            case["id"]: {
                "issue": case["parent"],
                "criterion": case["criterion"],
                "fixture": CONFIG,
                "viewports": profile["viewports"],
                "canonical_states": [frame[4:] for frame in case["frames"]],
                "reference": f"{case['id']}.png",
                "actual_render": case["actual_render"],
            }
            for case in config["cases"]
        },
        "checks": {
            "repeat_pixel_difference": 0,
            "comparison_threshold_changed_pixels": 0,
            "keyboard_navigation": "passed",
            "minimum_text_contrast_ratio": 4.5,
            "long_identity_200_percent_css_zoom": "passed",
            "clipping_mutation": "detected",
            "heading_clipping_mutation": "detected",
            "external_requests": 0,
        },
        "assets": {name: sha(data) for name, data in sorted(assets.items())},
    }
    (args.output / "evidence.json").write_text(json.dumps(evidence, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
