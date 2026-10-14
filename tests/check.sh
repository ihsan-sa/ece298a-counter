#!/usr/bin/env bash
# The fast check for this repo. GitHub runs it as the `check` job on every pull
# request and every push to main, and you can run the same thing locally:
#
#   bash tests/check.sh
#
# It needs Icarus Verilog (iverilog and vvp) and make on PATH, and python3 with
# cocotb and PyYAML (pip install -r test/requirements.txt pyyaml). It runs:
#   1. tests/check_info.py: info.yaml has what the Tiny Tapeout flow reads, and
#      its source list matches src/, test/Makefile and test/tb.v.
#   2. A lint: the listed sources compile under iverilog -Wall, and any warning
#      fails the check.
#   3. The cocotb tests in test/ against the RTL. They pass only if results.xml
#      holds at least one test and no failure or error.
# The heavy workflows (gds, fpga, docs) still run on their own.
set -euo pipefail
root=$(cd "$(dirname "$0")/.." && pwd)
cd "$root"

for tool in python3 iverilog vvp make cocotb-config; do
  if ! command -v "$tool" >/dev/null; then
    echo "check: $tool is not on PATH; see the top of tests/check.sh" >&2
    exit 2
  fi
done

echo "== 1/3 info.yaml"
python3 tests/check_info.py

echo "== 2/3 lint (iverilog -Wall)"
mapfile -t sources < <(python3 -c 'import yaml; print("\n".join("src/" + f for f in yaml.safe_load(open("info.yaml"))["project"]["source_files"]))')
lint=$(iverilog -g2012 -Wall -t null -I src "${sources[@]}" 2>&1) || { echo "$lint"; echo "lint: iverilog failed"; exit 1; }
if [ -n "$lint" ]; then
  echo "$lint"
  echo "lint: iverilog printed warnings, and a warning fails the check"
  exit 1
fi
echo "lint: ok (${sources[*]})"

echo "== 3/3 cocotb tests"
rm -f "${root:?}/test/results.xml"
# results.xml decides, so a failing make still reaches the line naming what failed.
(cd test && make clean >/dev/null && make) || echo "cocotb: make exited $?"
python3 - <<'EOF'
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

results = Path("test/results.xml")
if not results.is_file():
    sys.exit("cocotb: test/results.xml was not written, so the tests did not run")
cases = list(ET.parse(results).iter("testcase"))
bad = [c.get("name") for c in cases if c.find("failure") is not None or c.find("error") is not None]
if not cases:
    sys.exit("cocotb: results.xml holds no tests")
if bad:
    sys.exit(f"cocotb: {len(bad)} of {len(cases)} tests failed: {', '.join(bad)}")
print(f"cocotb: {len(cases)} tests passed")
EOF
echo "check: ok"
