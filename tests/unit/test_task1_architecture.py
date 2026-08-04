from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ENGINE_ROOT = REPO_ROOT / "packages" / "credit_engine" / "credit_engine"


def engine_modules() -> list[Path]:
    assert ENGINE_ROOT.is_dir(), f"engine root was not created: {ENGINE_ROOT}"
    modules = list(ENGINE_ROOT.rglob("*.py"))
    assert modules, f"no engine modules were scanned under {ENGINE_ROOT}"
    return modules


def test_credit_engine_never_imports_apps_or_web_frameworks() -> None:
    forbidden_roots = {
        "apps",
        "datetime",
        "fastapi",
        "httpx",
        "json",
        "math",
        "numpy",
        "os",
        "pandas",
        "pathlib",
        "random",
        "requests",
        "socket",
        "sqlalchemy",
        "time",
        "urllib",
    }
    violations: list[str] = []
    for path in engine_modules():
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                roots = {alias.name.split(".")[0] for alias in node.names}
            elif isinstance(node, ast.ImportFrom) and node.module:
                roots = {node.module.split(".")[0]}
            else:
                continue
            if roots & forbidden_roots:
                violations.append(f"{path}: {sorted(roots & forbidden_roots)}")
    assert not violations, violations


def test_engine_contains_no_binary_float_path() -> None:
    violations: list[str] = []
    for path in engine_modules():
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "float"
            ):
                violations.append(f"{path}:{node.lineno}")
            if isinstance(node, ast.Constant) and isinstance(node.value, float):
                violations.append(f"{path}:{node.lineno} float literal {node.value!r}")
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id in {"Decimal", "Money"}
                and any(
                    isinstance(arg, ast.Constant) and isinstance(arg.value, float)
                    for arg in node.args
                )
            ):
                violations.append(
                    f"{path}:{node.lineno} {node.func.id} constructed from float"
                )
    assert not violations, violations
