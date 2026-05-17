#!/usr/bin/env python3
"""Export OpenAPI 3.1 spec from the running FastAPI app to spec/openapi.yaml.

Usage:
    # Export from a live server (CI / Docker):
    python scripts/export_openapi.py --url http://localhost:8000

    # Export directly from the Python module (no server required):
    python scripts/export_openapi.py --from-module

    # Validate route count after export:
    python scripts/export_openapi.py --from-module --expected-routes 114
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SPEC_PATH = Path(__file__).parent.parent / "spec" / "openapi.yaml"


def export_from_module() -> dict:
    """Import the FastAPI app and call app.openapi() directly — no server needed."""
    sys.path.insert(0, str(Path(__file__).parent.parent / "server"))
    from vhir_server.main import app  # noqa: PLC0415
    return app.openapi()


def export_from_url(url: str) -> dict:
    """Fetch the OpenAPI JSON from a running server."""
    import urllib.request
    openapi_url = url.rstrip("/") + "/v1/_openapi.json"
    with urllib.request.urlopen(openapi_url) as resp:  # noqa: S310
        return json.loads(resp.read())


def count_routes(spec: dict) -> int:
    total = 0
    for path_item in spec.get("paths", {}).values():
        total += sum(
            1 for method in ("get", "post", "put", "delete", "patch", "head", "options")
            if method in path_item
        )
    return total


def write_yaml(spec: dict, path: Path) -> None:
    try:
        import yaml  # type: ignore[import-untyped]
        path.write_text(yaml.dump(spec, allow_unicode=True, sort_keys=False, default_flow_style=False))
    except ImportError:
        # Fallback: write as JSON with .yaml extension (valid YAML superset)
        path.write_text(json.dumps(spec, indent=2, ensure_ascii=False))
        print("Warning: PyYAML not installed — wrote JSON-formatted YAML", file=sys.stderr)


def main() -> int:
    parser = argparse.ArgumentParser(description="Export VHIR OpenAPI spec to spec/openapi.yaml")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--url", default=None, help="Base URL of running server (e.g. http://localhost:8000)")
    group.add_argument("--from-module", action="store_true", help="Import app directly (no server required)")
    parser.add_argument("--expected-routes", type=int, default=0, help="Fail if route count differs")
    parser.add_argument("--output", default=str(SPEC_PATH), help="Output path")
    args = parser.parse_args()

    if args.from_module or (not args.url):
        print("Exporting spec from Python module…")
        spec = export_from_module()
    else:
        print(f"Fetching spec from {args.url}…")
        spec = export_from_url(args.url)

    route_count = count_routes(spec)
    print(f"Routes found: {route_count}")

    if args.expected_routes and route_count != args.expected_routes:
        print(
            f"ERROR: expected {args.expected_routes} routes, got {route_count}",
            file=sys.stderr,
        )
        return 1

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    write_yaml(spec, out)
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
