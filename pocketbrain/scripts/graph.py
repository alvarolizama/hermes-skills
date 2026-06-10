#!/usr/bin/env python3
"""
PocketBrain Graph — Visualización interactiva de nodos de un cerebro.

Genera un archivo HTML autocontenido con un force-directed graph
que muestra páginas (nodos) y sus [[wikilinks]] (edges).

Uso:
    python3 graph.py --context personal
    python3 graph.py --context personal --output ~/Desktop/mi-cerebro.html

Requiere conexión a internet para cargar vis.js CDN.
"""

import sys, os, json, re
from pathlib import Path

sys.path.insert(0, os.path.expanduser("~/.hermes/skills/productivity/pocketbase/scripts"))
sys.path.insert(0, os.path.expanduser("~/.hermes/skills/productivity/pocketbrain/scripts"))

# Load env
env_path = os.path.expanduser("~/.hermes/.env")
env = {}
with open(env_path) as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
os.environ["POCKETBRAIN_HOST"] = env["POCKETBRAIN_HOST"]
os.environ["POCKETBRAIN_EMAIL"] = env["POCKETBRAIN_EMAIL"]
os.environ["POCKETBRAIN_PASSWORD"] = env["POCKETBRAIN_PASSWORD"]

from brain import Brain, extract_wikilinks
from pb import quick_pb


# ═══════════════════════════════════════════════════════
#  COLORS
# ═══════════════════════════════════════════════════════

PAGE_COLORS = {
    "entity":     "#4CAF50",  # green
    "concept":    "#2196F3",  # blue
    "comparison": "#FF9800",  # orange
    "query":      "#9C27B0",  # purple
    "raw":        "#607D8B",  # grey
    "project":    "#E91E63",  # pink
}

EDGE_COLOR = "#999999"
BG_COLOR = "#1a1a2e"
TEXT_COLOR = "#e0e0e0"


# ═══════════════════════════════════════════════════════
#  GRAPH BUILDER
# ═══════════════════════════════════════════════════════

def build_graph(ctx: Brain) -> dict:
    """Construye nodos y edges desde las páginas del contexto."""
    ctx.orient()
    pages = ctx.list_pages(include_archived=False)

    slug_map = {p["slug"]: p for p in pages}

    nodes = []
    edges = []
    node_ids = set()

    for page in pages:
        slug = page["slug"]
        if slug in node_ids:
            continue
        node_ids.add(slug)

        pt = page.get("page_type", "concept")
        nodes.append({
            "id": slug,
            "label": page.get("title", slug),
            "color": PAGE_COLORS.get(pt, "#607D8B"),
            "page_type": pt,
            "confidence": page.get("confidence", ""),
            "summary": (page.get("summary", "") or "")[:100],
        })

        # Extraer wikilinks del body
        body = page.get("body", "") or ""
        links = extract_wikilinks(body)

        for link in links:
            # Normalizar: quitar aliases [[page|alias]] → page
            target = link.split("|")[0].strip()
            if target in slug_map and target != slug:
                edges.append({
                    "from": slug,
                    "to": target,
                })
                # Asegurar que el target también sea nodo
                if target not in node_ids:
                    node_ids.add(target)
                    tp = slug_map[target]
                    nodes.append({
                        "id": target,
                        "label": tp.get("title", target),
                        "color": PAGE_COLORS.get(tp.get("page_type", "concept"), "#607D8B"),
                        "page_type": tp.get("page_type", "concept"),
                        "confidence": tp.get("confidence", ""),
                        "summary": (tp.get("summary", "") or "")[:100],
                    })

    return {"nodes": nodes, "edges": edges, "context": ctx.context_name}


# ═══════════════════════════════════════════════════════
#  HTML TEMPLATE
# ═══════════════════════════════════════════════════════

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>PocketBrain Graph — CTX_NAME</title>
<script src="https://unpkg.com/vis-network@9.1.6/dist/vis-network.min.js"></script>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { background: BG_COLOR; font-family: -apple-system, BlinkMacSystemFont, sans-serif; overflow: hidden; }
  #graph { width: 100vw; height: 100vh; }
  #info {
    position: fixed; bottom: 20px; left: 20px;
    background: rgba(0,0,0,0.7); color: TEXT_COLOR;
    padding: 12px 18px; border-radius: 8px;
    font-size: 13px; max-width: 400px;
    pointer-events: none; opacity: 0; transition: opacity 0.2s;
  }
  #info.visible { opacity: 1; }
  #info h3 { margin-bottom: 4px; }
  #info .type { font-size: 11px; opacity: 0.7; }
  #info .summary { margin-top: 6px; font-size: 12px; opacity: 0.8; }
  #legend {
    position: fixed; top: 20px; right: 20px;
    background: rgba(0,0,0,0.7); color: TEXT_COLOR;
    padding: 12px 16px; border-radius: 8px; font-size: 12px;
  }
  #legend span { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 6px; }
  #legend div { margin: 3px 0; }
  #stats {
    position: fixed; top: 20px; left: 20px;
    background: rgba(0,0,0,0.7); color: TEXT_COLOR;
    padding: 8px 14px; border-radius: 8px; font-size: 12px;
  }
</style>
</head>
<body>
<div id="graph"></div>
<div id="info"></div>
<div id="stats"></div>
<div id="legend"></div>

<script>
var data = GRAPH_DATA;

// Legend
var legendHtml = '';
var colors = LEGEND_COLORS;
for (var pt in colors) {
  legendHtml += '<div><span style="background:' + colors[pt] + '"></span> ' + pt + '</div>';
}
document.getElementById('legend').innerHTML = legendHtml;

// Stats
document.getElementById('stats').innerHTML =
  '<strong>CTX_NAME</strong><br>' +
  data.nodes.length + ' nodos &middot; ' + data.edges.length + ' conexiones';

// Build network
var nodes = new vis.DataSet(data.nodes.map(function(n) {
  return {
    id: n.id,
    label: n.label,
    color: { background: n.color, border: '#333' },
    font: { color: '#e0e0e0', size: 13 },
    shape: 'dot',
    size: 25,
    page_type: n.page_type,
    confidence: n.confidence,
    summary: n.summary,
  };
}));

var edges = new vis.DataSet(data.edges.map(function(e) {
  return {
    from: e.from,
    to: e.to,
    color: { color: '#555', opacity: 0.6 },
    arrows: { to: { enabled: true, scaleFactor: 0.5 } },
  };
}));

var container = document.getElementById('graph');
var network = new vis.Network(container, { nodes: nodes, edges: edges }, {
  physics: {
    forceAtlas2Based: {
      gravitationalConstant: -50,
      centralGravity: 0.01,
      springLength: 150,
      springConstant: 0.08,
    },
    maxVelocity: 50,
    solver: 'forceAtlas2Based',
    timestep: 0.35,
    stabilization: { iterations: 150 },
  },
  interaction: {
    hover: true,
    tooltipDelay: 100,
    zoomView: true,
    dragView: true,
  },
  edges: {
    smooth: { type: 'continuous' },
  },
});

// Hover info
var info = document.getElementById('info');
network.on('hoverNode', function(params) {
  var node = nodes.get(params.node);
  info.innerHTML =
    '<h3>' + node.label + '</h3>' +
    '<div class="type">' + node.page_type + (node.confidence ? ' [' + node.confidence + ']' : '') + '</div>' +
    (node.summary ? '<div class="summary">' + node.summary + '</div>' : '');
  info.classList.add('visible');
});
network.on('blurNode', function() {
  info.classList.remove('visible');
});

// Double-click to open page (if hosted)
network.on('doubleClick', function(params) {
  if (params.nodes.length > 0) {
    var slug = params.nodes[0];
    console.log('Open:', slug);
  }
});
</script>
</body>
</html>"""


# ═══════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════

def parse_args():
    args = sys.argv[1:]
    context = "personal"
    output = None
    i = 0
    while i < len(args):
        if args[i] == "--context" and i + 1 < len(args):
            context = args[i + 1]; i += 2
        elif args[i] == "--output" and i + 1 < len(args):
            output = args[i + 1]; i += 2
        else:
            i += 1
    return context, output


if __name__ == "__main__":
    context, output = parse_args()
    output = output or os.path.expanduser(f"~/context-graph-{context}.html")

    pb = quick_pb(env["POCKETBRAIN_HOST"], env["POCKETBRAIN_EMAIL"], env["POCKETBRAIN_PASSWORD"])
    ctx = Brain(context, pb=pb)
    graph = build_graph(ctx)

    legend_json = json.dumps(PAGE_COLORS)
    graph_json = json.dumps(graph, ensure_ascii=False)

    html = HTML_TEMPLATE
    html = html.replace("GRAPH_DATA", graph_json)
    html = html.replace("LEGEND_COLORS", legend_json)
    html = html.replace("CTX_NAME", context)
    html = html.replace("BG_COLOR", BG_COLOR)
    html = html.replace("TEXT_COLOR", TEXT_COLOR)

    Path(output).write_text(html, encoding="utf-8")
    print(f"Graph: {graph['nodes']} nodos, {len(graph['edges'])} conexiones")
    print(f"Output: {output}")
    print(f"Abrir: open {output}")
