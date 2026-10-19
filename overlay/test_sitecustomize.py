#!/usr/bin/env python3
"""Checks for the two fixed helpers in ``overlay/sitecustomize.py``.

Stdlib only, no pytest needed. Loads the REAL functions out of the patch file
(not re-implementations) and exercises them:

    python3 -S overlay/test_sitecustomize.py

Exit status is 0 when everything passes, 1 otherwise.
"""
from __future__ import annotations

import ast
import difflib
import os
import re

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sitecustomize.py")

# Pull the functions + module constants we test straight out of the file, so a
# drift between the file and this test is impossible.
_WANTED = {
    "_patched_benign_tld", "_hosts_in",
    "_collapse_restated_answer", "_norm_offset_to_text_offset", "_nearest_restart",
}
tree = ast.parse(open(SRC, encoding="utf-8").read())
ns: dict = {"re": re, "_re": re, "difflib": difflib, "_difflib": difflib, "__name__": "sc"}
for node in tree.body:
    keep = (isinstance(node, ast.FunctionDef) and node.name in _WANTED) or (
        isinstance(node, ast.Assign)
        and any(getattr(t, "id", None) in {"_BENIGN_TLDS", "_BENIGN_SUFFIXES",
                                           "_HOST_TOKEN_RE", "_HOST_FIELDS"}
                for t in node.targets)
    )
    if keep:
        exec(compile(ast.Module([node], type_ignores=[]), "<sc>", "exec"), ns)

fails: list[str] = []


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + (f"   [{detail}]" if detail else ""))
    if not cond:
        fails.append(name)


benign = ns["_patched_benign_tld"]


def f(**kw):
    return {"rule_id": "lookalike_tld", **kw}


# ---------- Fix 1: the finding's HOST must end in the gTLD ----------
print("-- TLD suppression --")
for v in ["queue.fal.run", "foo.app", "a.run", "x.APP", "https://queue.fal.run/v1/x"]:
    check(f"suppress {v!r}", benign(f(value=v)) is True)

# over-match fixed: longer labels
for v in ["foo.apple", "foo.application", "foo.running", "foo.runner", "sn.apple.com"]:
    check(f"keep {v!r}", benign(f(value=v)) is False)

# spoofing shape fixed: .app as an INNER label must still warn
for v in ["paypal.app.evil.example", "evil.run.example.com", "app.evil.example"]:
    check(f"keep spoof {v!r}", benign(f(value=v)) is False)

# structured field wins; wrong TLD still warns
check("tld field 'app'", benign(f(tld="app")) is True)
check("tld field '.run'", benign(f(tld=".run")) is True)
check("tld field 'com'", benign(f(tld="com")) is False)
# host field is honoured
check("host field", benign(f(host="queue.fal.run")) is True)
check("free-text not trusted", benign(f(detail="flagged host queue.fal.run")) is False)
check("other rule untouched", benign(f(rule_id="other", value="foo.app")) is False)
check("non-dict", benign(None) is False)
check("url userinfo/port", benign(f(url="https://u:p@q.fal.run:443/x")) is True)

# ---------- Fix 2: collapse preserves formatting ----------
print("-- doubled-answer collapse --")
copy = ("## Heading\n\nHere is a list:\n\n- alpha\n- beta\n- gamma\n\n"
        "```python\nprint('hi')\n    indented()\n```\n")
copy += "".join(f"Filler sentence number {i} with several words adding length.\n"
                for i in range(40))
assert len(copy) > 1600

out, seam = ns["_collapse_restated_answer"](copy + copy)
check("doubled message detected", seam is not None, f"seam={seam}")
check("kept copy is the FIRST copy, character-exact", out == copy.rstrip(),
      f"{len(out)} vs {len(copy.rstrip())}")
check("newlines preserved", "\n" in out and out.count("\n") > 10)
check("code block preserved", "```python" in out and "    indented()" in out)
check("output not whitespace-collapsed", "## Heading\n\nHere is a list:" in out)

# NEGATIVE (reviewer request): a legitimate answer that repeats its opening
# HEADING must NOT be collapsed, and must come back untouched.
print("-- negative: legitimate repeated heading must survive --")
legit = "".join(
    f"## Findings\n\nSection {i} covers a distinct topic.\n"
    + ("Body text for section %d that is unique.\n" % i) * 25
    + "\n"
    for i in range(6)
)
out2, seam2 = ns["_collapse_restated_answer"](legit)
check("repeated-heading answer untouched", out2 is legit and seam2 is None,
      f"seam={seam2}")

# NEGATIVE: long, non-repeated answer untouched
distinct = "".join(f"Unrelated paragraph {i}: " + ("word%d " % i) * 60 + "\n"
                   for i in range(40))
out3, seam3 = ns["_collapse_restated_answer"](distinct)
check("distinct long answer untouched", out3 is distinct and seam3 is None)

# ---------- the seam-mapping helper ----------
print("-- seam offset mapping --")
t = "alpha\n\nbeta   gamma\n\ndelta"
for off, expect in [(0, 0), (6, 7), (11, 14)]:
    got = ns["_norm_offset_to_text_offset"](t, off)
    check(f"norm_off {off} -> text_off {expect}", got == expect, f"got {got}")
check("past-the-end -> len(text)",
      ns["_norm_offset_to_text_offset"](t, len(" ".join(t.split()))) == len(t))

print("\n" + ("ALL TESTS PASSED" if not fails else f"{len(fails)} FAILURES: {fails}"))
raise SystemExit(1 if fails else 0)
