"""Fail when sensitive dependencies cross forbidden architecture boundaries."""

import ast
from pathlib import Path

RULES: dict[str, set[str]] = {
    "app/users/domain": {"fastapi", "pydantic", "sqlalchemy", "punq"},
    "app/users/application": {"fastapi", "sqlalchemy", "punq"},
    "app/ingestion/application": {"fastapi", "httpx", "punq", "sqlalchemy"},
    "app/ingestion/domain": {"fastapi", "httpx", "pydantic", "punq", "sqlalchemy"},
}


def module_root(path: Path) -> str | None:
    normalized = path.as_posix()
    for root in RULES:
        if normalized.startswith(root + "/"):
            return root
    return None


def main() -> int:
    violations: list[str] = []
    for path in Path("app").rglob("*.py"):
        root = module_root(path)
        if root is None:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        forbidden = RULES[root]
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported = [alias.name.split(".", 1)[0] for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported = [node.module.split(".", 1)[0]]
            else:
                continue
            for name in imported:
                if name in forbidden:
                    violations.append(f"{path}: import proibido {name}")
    if violations:
        print("\n".join(violations))
        return 1
    print("Regras de dependência arquitetural: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
