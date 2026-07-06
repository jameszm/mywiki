#!/usr/bin/env python3
"""Build a self-contained wiki HTML file from a graph JSON and the viewer template.

Usage:
    python3 tools/build.py <graph.json> <output.html>
    python3 tools/build.py            # defaults to the requests example
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "viewer" / "template.html"
PLACEHOLDER = "__GRAPH_DATA__"


def build(graph_path: Path, out_path: Path) -> None:
    graph = json.loads(graph_path.read_text(encoding="utf-8"))

    # Basic validation: every edge must reference existing nodes
    node_ids = {n["id"] for n in graph["nodes"]}
    for edge in graph["edges"]:
        for end in (edge["source"], edge["target"]):
            if end not in node_ids:
                sys.exit(f"error: edge {edge['id']!r} references unknown node {end!r}")

    data = json.dumps(graph, ensure_ascii=False)
    # "</" inside a <script> block can terminate the script tag early; escape it
    # ("<\/" is a valid, identical string escape in both JSON and JS).
    data = data.replace("</", "<\\/")

    template = TEMPLATE.read_text(encoding="utf-8")
    if PLACEHOLDER not in template:
        sys.exit(f"error: placeholder {PLACEHOLDER} not found in {TEMPLATE}")

    out_path.write_text(template.replace(PLACEHOLDER, data), encoding="utf-8")
    print(f"built {out_path} ({out_path.stat().st_size / 1024:.0f} KB, "
          f"{len(graph['nodes'])} nodes, {len(graph['edges'])} edges)")


if __name__ == "__main__":
    if len(sys.argv) == 3:
        build(Path(sys.argv[1]), Path(sys.argv[2]))
    elif len(sys.argv) == 1:
        build(ROOT / "examples" / "requests.graph.json",
              ROOT / "examples" / "requests-wiki.html")
    else:
        sys.exit(__doc__)
