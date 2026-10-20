#!/usr/bin/env python3
"""Checks for the hardened ABI guard in ``overlay/sitecustomize.py``.

Loads the REAL ``_deactivate_foreign_dependency_env`` out of the patch file via
``ast`` (same trick as ``test_sitecustomize.py``) and drives it against crafted
``sys.path`` states, with a fake ``sysconfig`` so "own site-packages" points at a
temp dir. Stdlib only:

    python3 -S overlay/test_abi_guard.py

Exit status is 0 when everything passes, 1 otherwise.
"""
from __future__ import annotations

import ast
import os
import sys
import tempfile
import types

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sitecustomize.py")

tree = ast.parse(open(SRC, encoding="utf-8").read())
# `sys` is the real module (the guard reads sys.path / sys.version_info);
# `_RE_FOREIGN_SITE_PACKAGES` is the module-level cache the function mutates.
ns: dict = {"re": __import__("re"), "__name__": "sc", "sys": sys,
            "_RE_FOREIGN_SITE_PACKAGES": None}
for node in tree.body:
    if isinstance(node, ast.FunctionDef) and node.name == "_deactivate_foreign_dependency_env":
        exec(compile(ast.Module([node], type_ignores=[]), "<sc>", "exec"), ns)
guard = ns["_deactivate_foreign_dependency_env"]

fails: list[str] = []


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + (f"   [{detail}]" if detail else ""))
    if not cond:
        fails.append(name)


own_dir = tempfile.mkdtemp(prefix="ownsp-")
real_sysconfig = sys.modules.get("sysconfig")
_fake_sysconfig = types.ModuleType("sysconfig")
setattr(_fake_sysconfig, "get_paths", lambda: {"purelib": own_dir})
sys.modules["sysconfig"] = _fake_sysconfig

current = "python%d.%d" % sys.version_info[:2]

try:
    # ---- case 1: matching-tag managed env replaced site-packages (the 3.14 case).
    # This is the regression the hardening fixes: previously the guard returned
    # early and `own_dir` was left OFF sys.path (so PyYAML disappeared). ----
    saved = list(sys.path)
    managed = "/data/installs/x/environments/y/venv/lib/%s/site-packages" % current
    sys.path[:] = ["", "/opt/hermes", managed]
    guard()
    check("matching-tag: own site-packages re-added", own_dir in sys.path,
          f"path={sys.path}")
    check("matching-tag: managed env still present",
          any("installs" in p for p in sys.path))
    sys.path[:] = saved

    # ---- case 2: foreign-tag env (the 3.13 case the guard was built for). ----
    saved = list(sys.path)
    sys.path[:] = ["", "/data/installs/x/environments/y/venv/lib/python9.9/site-packages"]
    guard()
    check("foreign-tag: foreign env removed",
          not any("python9.9" in p for p in sys.path))
    check("foreign-tag: own site-packages present", own_dir in sys.path)
    sys.path[:] = saved

    # ---- case 3: no managed env at all (normal boot) — must not duplicate. ----
    saved = list(sys.path)
    sys.path[:] = ["", own_dir]
    guard()
    check("no-managed-env: own present exactly once", sys.path.count(own_dir) == 1)
    sys.path[:] = saved
finally:
    if real_sysconfig is not None:
        sys.modules["sysconfig"] = real_sysconfig
    else:
        sys.modules.pop("sysconfig", None)

print("\n" + ("ALL TESTS PASSED" if not fails else f"{len(fails)} FAILURES: {fails}"))
raise SystemExit(1 if fails else 0)
