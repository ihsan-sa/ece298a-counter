#!/usr/bin/env python3
"""Check info.yaml against what the Tiny Tapeout flow reads from it.

Run from the repository root (tests/check.sh does). Prints one line and exits 0
when info.yaml is sound; prints each problem and exits 1 when it is not.
"""
import re
import sys
from pathlib import Path

import yaml

TILES = {"1x1", "1x2", "2x2", "3x2", "4x2", "3x4", "4x4"}
PINS = [f"{bus}[{i}]" for bus in ("ui", "uo", "uio") for i in range(8)]


def main() -> int:
    info = yaml.safe_load(Path("info.yaml").read_text())
    problems = []
    project = info.get("project") or {}

    if info.get("yaml_version") != 6:
        problems.append(f"yaml_version is {info.get('yaml_version')!r}, the template wants 6")
    for key in ("title", "author", "description", "language"):
        if not str(project.get(key) or "").strip():
            problems.append(f"project.{key} is empty")
    if not isinstance(project.get("clock_hz"), int) or project["clock_hz"] < 0:
        problems.append(f"project.clock_hz is {project.get('clock_hz')!r}, not a whole number of Hz")
    if project.get("tiles") not in TILES:
        problems.append(f"project.tiles is {project.get('tiles')!r}, not one of {sorted(TILES)}")

    top = str(project.get("top_module") or "")
    if not top.startswith("tt_um_"):
        problems.append(f"project.top_module {top!r} does not start with tt_um_")

    sources = project.get("source_files") or []
    if not sources:
        problems.append("project.source_files lists no files")
    missing = [f for f in sources if not (Path("src") / f).is_file()]
    for f in missing:
        problems.append(f"project.source_files names src/{f}, which does not exist")
    present = [Path("src") / f for f in sources if f not in missing]
    declares = re.compile(rf"^\s*module\s+{re.escape(top)}\b", re.M)
    if top and present and not any(declares.search(p.read_text()) for p in present):
        problems.append(f"no listed source declares module {top}")

    makefile = Path("test/Makefile").read_text()
    m = re.search(r"^PROJECT_SOURCES\s*=\s*(.*)$", makefile, re.M)
    listed = m.group(1).split() if m else []
    if listed != list(sources):
        problems.append(f"test/Makefile PROJECT_SOURCES is {listed}, info.yaml lists {list(sources)}")
    if top and not re.search(rf"\b{re.escape(top)}\b", Path("test/tb.v").read_text()):
        problems.append(f"test/tb.v does not instantiate {top}")

    pinout = info.get("pinout") or {}
    if sorted(pinout) != sorted(PINS):
        extra = sorted(set(pinout) - set(PINS))
        lost = sorted(set(PINS) - set(pinout))
        problems.append(f"pinout must keep the template's 24 pins (missing {lost}, extra {extra})")

    if problems:
        for p in problems:
            print(f"info.yaml: {p}")
        return 1
    print(f"info.yaml: ok ({top}, {len(sources)} source file(s), {len(pinout)} pins)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
