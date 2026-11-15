"""Fail closed on the reviewed SRC-013 document closure before renderer writes."""

import hashlib
import json
from pathlib import Path

COMMIT = "bfa8f760c1d56ec1c2ce07ea49e4d37ce4c01e5b"
PINS = {
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
}


def verify_refinery_mirror(folder: Path) -> None:
    """Local byte/pin validation only; no compilation or runtime acceptance."""
    entries = json.loads((folder / "artifacts.json").read_text())["artifacts"]
    for name, digest in PINS.items():
        matches = [x for x in entries if x["path"] == "docs/marketing/" + name]
        if len(matches) != 1:
            raise ValueError("Missing or duplicate SRC-013 mirror entry: " + name)
        item = matches[0]
        source = "THIRD_PARTY_NOTICES.md" if name == "SRC-013-NOTICES.md" else name
        canonical = {
            "repository": "newdarwindev/runspindle-refinery",
            "commit": COMMIT,
            "path": "docs/design/" + source,
            "sha256": digest,
        }
        path = folder / name
        if any(x.is_symlink() for x in (path, *path.parents)) or not path.is_file():
            raise ValueError("Missing or symlink SRC-013 mirror: " + name)
        if (
            item.get("canonical") != canonical
            or item.get("source_ids") != ["SRC-013"]
            or item.get("sha256") != digest
            or hashlib.sha256(path.read_bytes()).hexdigest() != digest
        ):
            raise ValueError("SRC-013 canonical mirror mismatch: " + name)
