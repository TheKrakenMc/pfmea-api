"""Move module imports before executable declarations without changing their order."""

import ast
from pathlib import Path


def organize(path):
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports = [
        node for node in tree.body if isinstance(node, (ast.Import, ast.ImportFrom))
    ]
    lines = source.splitlines(keepends=True)
    blocks = ["".join(lines[node.lineno - 1 : node.end_lineno]) for node in imports]
    remove = {
        line for node in imports for line in range(node.lineno - 1, node.end_lineno)
    }
    insert = (
        tree.body[0].end_lineno
        if tree.body
        and isinstance(tree.body[0], ast.Expr)
        and isinstance(tree.body[0].value, ast.Constant)
        and isinstance(tree.body[0].value.value, str)
        else 0
    )
    futures = [block for block in blocks if block.startswith("from __future__")]
    normal = [block for block in blocks if not block.startswith("from __future__")]
    output = (
        "".join(
            line for index, line in enumerate(lines[:insert]) if index not in remove
        )
        + "\n"
        + "".join(futures + normal)
        + "\n"
        + "".join(
            line
            for index, line in enumerate(lines[insert:], insert)
            if index not in remove
        )
    )
    path.write_text(output, encoding="utf-8")


if __name__ == "__main__":
    for path in Path("app").rglob("*.py"):
        organize(path)
