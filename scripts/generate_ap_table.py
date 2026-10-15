"""Generate the provisional shared AP fixture without importing runtime settings or connecting to a database."""

import ast
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
source = (root / "app/services/pfmea_service.py").read_text(encoding="utf-8")
function = next(
    node
    for node in ast.parse(source).body
    if isinstance(node, ast.FunctionDef) and node.name == "calculate_action_priority"
)
namespace = {}
exec(
    compile(ast.Module(body=[function], type_ignores=[]), "ap_source", "exec"),
    namespace,
)
calculate = namespace["calculate_action_priority"]
table = {
    f"{s},{o},{d}": calculate(s, o, d)
    for s in range(1, 11)
    for o in range(1, 11)
    for d in range(1, 11)
}
target = root.parent / "pfmea-ui/src/data/actionPriority.json"
encoded = json.dumps(table, sort_keys=True, indent=2) + "\n"
local = root / "app/data/action_priority.json"
local.parent.mkdir(parents=True, exist_ok=True)
local.write_text(encoded, encoding="utf-8")
if target.parent.exists():
    target.write_text(encoded, encoding="utf-8")
print("Generated 1,000 provisional AP combinations")
