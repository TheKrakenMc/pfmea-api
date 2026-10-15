"""Generate reviewable API contracts and endpoint authorization inventory."""

import json
from pathlib import Path
from app.main import app

PUBLIC = {
    "/api/v1/health",
    "/api/v1/readiness",
    "/api/v1/auth/login",
    "/api/v1/auth/csrf",
    "/api/v1/auth/refresh",
    "/api/v1/auth/verify-email",
    "/api/v1/auth/forgot-password",
    "/api/v1/auth/reset-password",
}


def policy(path, method):
    if path in PUBLIC:
        return "Public; purpose-bound credentials/rate limits where applicable"
    write = method not in {"get", "head", "options"}
    if "/users" in path and not path.endswith("/lookup"):
        return "Administrator; server-resolved actor and plant assignments"
    if "/auth/" in path:
        return "Active authenticated account; persisted session; CSRF for writes"
    if "/control-plans" in path:
        return "Assigned PFMEA project and authorized plant; Viewer reads; project Owner manages lifecycle; revision required for writes"
    if "/pfmea-project" in path:
        return "Assigned project and selected authorized plant; Viewer reads; Owner manages team/approval; revision required for document writes"
    if "/flowcharts" in path:
        return "Assigned project/creator or Process Engineer authorized plant; Owner approves; revision required for writes"
    if "/document-versions" in path:
        return (
            "Authorization resolved through source document; server-generated snapshots"
        )
    return (
        "Authenticated authorized plant/catalog; Viewer reads; Administrator deletes/administers shared catalogs"
        if write
        else "Authenticated authorized plant/catalog; parent resources checked for child IDs"
    )


def main():
    schema = app.openapi()
    target = Path("docs/contracts")
    target.mkdir(parents=True, exist_ok=True)
    (target / "openapi.json").write_text(
        json.dumps(schema, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    lines = [
        "# Endpoint authorization inventory",
        "",
        "Generated from registered OpenAPI routes. Each private route is tested anonymously; every private write is tested with Viewer. Resource isolation, revisions and business validation have additional targeted regressions.",
        "",
        "| Method | Endpoint | Authorization / integrity | Tests |",
        "|---|---|---|---|",
    ]
    for path, operations in schema["paths"].items():
        for method in operations:
            if method not in {
                "get",
                "post",
                "put",
                "patch",
                "delete",
                "head",
                "options",
            }:
                continue
            tests = (
                "test_security.py; test_auth.py"
                if path in PUBLIC
                else "test_security.py; test_audit_regressions.py; test_integrity.py"
            )
            lines.append(
                f"| {method.upper()} | {path} | {policy(path, method)} | {tests} |"
            )
    (target / "endpoint-inventory.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    print("Exported API contracts and endpoint inventory")


if __name__ == "__main__":
    main()
