#!/usr/bin/env python3
"""PocketBrain Web — Servidor live. python3 brain_web.py [--port 8080] [--context personal]"""
import sys, os, json, re, http.server, urllib.parse, time, threading
from http.server import ThreadingHTTPServer
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, os.path.expanduser("~/.hermes/skills/productivity/pocketbase/scripts"))
sys.path.insert(0, os.path.expanduser("~/.hermes/skills/productivity/pocketbrain/scripts"))

p = os.path.expanduser("~/.hermes/.env")
env = {}
with open(p) as f:
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

COLORS = {"entity":"#4CAF50","concept":"#2196F3","comparison":"#FF9800","query":"#9C27B0","raw":"#607D8B","project":"#E91E63"}
CTX = "personal"

def parse_args():
    args = sys.argv[1:]
    ctx, port = "personal", 8080
    i = 0
    while i < len(args):
        if args[i] == "--context" and i+1 < len(args): ctx = args[i+1]; i+=2
        elif args[i] == "--port" and i+1 < len(args): port = int(args[i+1]); i+=2
        else: i += 1
    return ctx, port

# ── Brain cache (evita re-autenticar en cada request) ──────────
_brain_cache = {}  # ctx -> Brain
_brain_lock = threading.Lock()

def get_brain(ctx=None):
    if ctx is None:
        ctx = CTX
    with _brain_lock:
        if ctx in _brain_cache:
            return _brain_cache[ctx]
        pb = quick_pb(env["POCKETBRAIN_HOST"], env["POCKETBRAIN_EMAIL"], env["POCKETBRAIN_PASSWORD"])
        brain = Brain(ctx, pb=pb)
        brain.orient()
        _brain_cache[ctx] = brain
        return brain

def get_pages(ctx, include_archived=False):
    brain = get_brain(ctx)
    pages = brain.list_pages(include_archived=include_archived, per_page=500)
    smap = {p["slug"]: p for p in pages}
    slug_by_lower = {s.lower(): s for s in smap}
    bls = {p["slug"]: [] for p in pages}
    for pg in pages:
        for link in extract_wikilinks(pg.get("body","") or ""):
            t = link.split("|")[0].strip()
            target = slug_by_lower.get(t.lower())
            if target and target != pg["slug"]:
                bls[target].append(pg["slug"])
    result = []
    for pg in pages:
        ed = pg.get("expand",{}).get("domain")
        dn = ed.get("name","") if isinstance(ed,dict) else ""
        et = pg.get("expand",{}).get("tags",[])
        tns = []
        if et and isinstance(et,list) and len(et)>0:
            tns = [t.get("name","") for t in et] if isinstance(et[0],dict) else et
        bld = [{"slug":b,"title":smap[b].get("title",b)} for b in bls.get(pg["slug"],[]) if b in smap]
        result.append({"id":pg["id"],"slug":pg["slug"],"title":pg.get("title",pg["slug"]),
            "page_type":pg.get("page_type","concept"),"color":COLORS.get(pg.get("page_type","concept"),"#607D8B"),
            "confidence":pg.get("confidence",""),"summary":pg.get("summary","") or "",
            "domain":dn,"tags":tns,"body":pg.get("body","") or "","backlinks":bld,
            "status":pg.get("status","") or "","started_date":(pg.get("started_date","") or "")[:10],
            "completed_date":(pg.get("completed_date","") or "")[:10],
            "cancelled_date":(pg.get("cancelled_date","") or "")[:10],
            "comment":pg.get("comment","") or "",
            "source_url":pg.get("source_url","") or "",
            "source_sha256":pg.get("source_sha256","") or "",
            "contested":pg.get("contested",False),
            "contradictions":pg.get("contradictions","") or "",
            "created":(pg.get("created","") or "")[:10],"updated":(pg.get("updated","") or "")[:10]})
    return result

def get_lint(ctx):
    brain = get_brain(ctx)
    return brain.lint()

# ── Reports ──────────────────────────────────────────────────────

def report_projects(ctx):
    brain = get_brain(ctx)
    return brain.report_projects()

def report_project_status(ctx, slug):
    brain = get_brain(ctx)
    return brain.report_project_status(slug)

def report_todos(ctx, status=None, project_slug=None):
    brain = get_brain(ctx)
    return brain.report_todos(status=status, project_slug=project_slug)

def report_journal(ctx, days=7):
    brain = get_brain(ctx)
    return brain.report_journal(days=days)

def report_reminders(ctx, date=''):
    brain = get_brain(ctx)
    return brain.report_reminders(date=date)

def report_lint(ctx):
    brain = get_brain(ctx)
    return brain.report_lint()

def get_goals(ctx):
    brain = get_brain(ctx)
    result = []
    for pt in ['goal', 'milestone']:
        pages = brain.pb.all("brain_pages",
            filter="(brain='{}' && page_type='{}' && archived=false)".format(brain._context_id, pt),
            expand="related_pages")
        for p in pages:
            rel = p.get("expand", {}).get("related_pages", [])
            ps = ""; parent_id = ""
            if isinstance(rel, dict):
                ps = rel.get("slug", "")
                parent_id = rel.get("id", "")
            elif rel and isinstance(rel, list) and len(rel) > 0 and isinstance(rel[0], dict):
                ps = rel[0].get("slug", "")
                parent_id = rel[0].get("id", "")
            result.append({
                "id": p["id"], "slug": p.get("slug", ""), "title": p.get("title", ""), "type": pt,
                "status": p.get("status", "planned"),
                "deadline": (p.get("deadline", "") or "")[:10],
                "description": p.get("body", "") or "",
                "page": ps, "page_slug": ps, "parent": parent_id,
            })
    goal_ids = {g["id"] for g in result}
    for g in result:
        if g["parent"] and g["parent"] in goal_ids:
            pass
        else:
            g["parent"] = ""
    return result

def get_todos(ctx):
    brain = get_brain(ctx)
    pages = brain.pb.all("brain_pages",
        filter="(brain='{}' && page_type='todo' && archived=false)".format(brain._context_id),
        expand="related_pages,domain")
    result = []
    for p in pages:
        rel = p.get("expand", {}).get("related_pages", [])
        ps = ""; pt = ""; goal_id = ""; goal_title = ""
        if isinstance(rel, dict):
            related = rel
            ps = related.get("slug", "")
            pt = related.get("title", "")
            if related.get("page_type") in ('goal', 'milestone', 'okr'):
                goal_id = related.get("id", "")
                goal_title = related.get("title", "")
        elif rel and isinstance(rel, list) and len(rel) > 0 and isinstance(rel[0], dict):
            related = rel[0]
            ps = related.get("slug", "")
            pt = related.get("title", "")
            if related.get("page_type") in ('goal', 'milestone', 'okr'):
                goal_id = related.get("id", "")
                goal_title = related.get("title", "")
        dom = p.get("expand", {}).get("domain", {})
        dn = dom.get("name", "") if isinstance(dom, dict) else p.get("domain", "")
        result.append({
            "id": p["id"], "title": p.get("title", ""), "status": p.get("status", "backlog"),
            "domain": dn, "owner": p.get("owner", ""),
            "content": p.get("body", "") or "",
            "page_slug": ps, "page_title": pt,
            "goal_id": goal_id, "goal_title": goal_title,
        })
    return result

def get_deps(ctx):
    brain = get_brain(ctx)
    pages = brain.pb.all("brain_pages",
        filter="(brain='{}' && page_type='deliverable' && archived=false)".format(brain._context_id),
        expand="related_pages")
    result = []
    for p in pages:
        rel = p.get("expand",{}).get("related_pages",[])
        ps = ""; pt = ""
        if isinstance(rel, dict):
            ps = rel.get("slug",""); pt = rel.get("title","")
        elif rel and isinstance(rel,list) and len(rel)>0 and isinstance(rel[0],dict):
            ps = rel[0].get("slug",""); pt = rel[0].get("title","")
        result.append({"id":p["id"],"title":p.get("title",""),"version":p.get("version",""),
            "status":p.get("status","draft"),
            "page_slug":ps,"page_title":pt,
            "milestone":p.get("milestone","") or ""})
    return result

def get_files(ctx):
    brain = get_brain(ctx)
    pages = brain.pb.all("brain_pages",
        filter="(brain='{}' && page_type='file' && archived=false)".format(brain._context_id),
        expand="related_pages")
    result = []
    for p in pages:
        rel = p.get("expand",{}).get("related_pages",[])
        ps = ""; pt = ""
        if isinstance(rel, dict):
            ps = rel.get("slug",""); pt = rel.get("title","")
        elif rel and isinstance(rel,list) and len(rel)>0 and isinstance(rel[0],dict):
            ps = rel[0].get("slug",""); pt = rel[0].get("title","")
        result.append({"id":p["id"],"name":p.get("title",""),"file_type":p.get("file_type","other"),
            "page_slug":ps,"page_title":pt})
    return result

def get_reminders(ctx):
    brain = get_brain(ctx)
    pages = brain.pb.all("brain_pages",
        filter="(brain='{}' && page_type='reminder' && archived=false)".format(brain._context_id),
        expand="related_pages")
    result = []
    for p in pages:
        rel = p.get("expand", {}).get("related_pages", [])
        ps = ""; pt = ""
        if isinstance(rel, dict):
            ps = rel.get("slug", "")
            pt = rel.get("title", "")
        elif rel and isinstance(rel, list) and len(rel) > 0 and isinstance(rel[0], dict):
            ps = rel[0].get("slug", "")
            pt = rel[0].get("title", "")
        result.append({
            "id": p["id"], "title": p.get("title", ""),
            "content": p.get("body", "") or "",
            "date": (p.get("date", "") or "")[:10],
            "time": p.get("time", "") or "",
            "done": p.get("done", False),
            "done_date": (p.get("done_date", "") or "")[:10],
            "page_slug": ps, "page_title": pt,
        })
    return result

def get_journal(ctx):
    brain = get_brain(ctx)
    pages = brain.pb.all("brain_pages",
        filter="(brain='{}' && page_type='journal' && archived=false)".format(brain._context_id),
        expand="related_pages,tags", sort="date")
    result = []
    for p in pages:
        rel = p.get("expand", {}).get("related_pages", [])
        ps = ""; pt = ""
        if isinstance(rel, dict):
            ps = rel.get("slug", "")
            pt = rel.get("title", "")
        elif rel and isinstance(rel, list) and len(rel) > 0 and isinstance(rel[0], dict):
            ps = rel[0].get("slug", "")
            pt = rel[0].get("title", "")
        result.append({
            "id": p["id"], "title": p.get("title", ""),
            "body": p.get("body", "") or "",
            "date": (p.get("date", "") or "")[:10],
            "mood": p.get("mood", "") or "",
            "page_slug": ps, "page_title": pt,
        })
    return result

def _first_related_id(page):
    rel = page.get("expand", {}).get("related_pages") or page.get("related_pages") or []
    if isinstance(rel, dict):
        return rel.get("id")
    if isinstance(rel, str):
        return rel if rel else None
    if not rel:
        return None
    first = rel[0]
    if isinstance(first, dict):
        return first.get("id")
    return first

def get_graph(ctx):
    brain = get_brain(ctx)
    pages = brain.list_pages(include_archived=False, per_page=500)
    smap = {p["slug"]: p for p in pages}
    slug_by_lower = {s.lower(): s for s in smap}
    pid_map = {pg.get("id",""): pg["slug"] for pg in pages if pg.get("id")}
    goals = []
    for pt in ['goal', 'milestone', 'okr']:
        goals.extend(brain.pb.all("brain_pages",
            filter="(brain='{}' && page_type='{}' && archived=false)".format(brain._context_id, pt),
            expand="related_pages"))
    todos = brain.pb.all("brain_pages", filter="(brain='{}' && page_type='todo' && archived=false)".format(brain._context_id), expand="related_pages")
    deps = brain.pb.all("brain_pages", filter="(brain='{}' && page_type='deliverable' && archived=false)".format(brain._context_id), expand="related_pages")
    reminders = brain.pb.all("brain_pages", filter="(brain='{}' && page_type='reminder' && archived=false)".format(brain._context_id), expand="related_pages")
    nodes, edges, nids = [], [], set()
    for pg in pages:
        slug = pg["slug"]
        if slug not in nids:
            nids.add(slug)
            nodes.append({"id":slug,"label":pg.get("title",slug),"color":COLORS.get(pg.get("page_type","concept"),"#607D8B"),"group":pg.get("page_type","concept")})
        for link in extract_wikilinks(pg.get("body","") or ""):
            t = link.split("|")[0].strip()
            target = slug_by_lower.get(t.lower())
            if target and target != slug:
                edges.append({"from":slug,"to":target})
    gmap = {}
    for g in goals:
        gid = "g-"+g["id"]; gmap[g["id"]] = gid
        if gid not in nids:
            nids.add(gid)
            gc = {"goal":"#4CAF50","milestone":"#FF9800","okr":"#E91E63"}.get(g.get("page_type",""),"#888")
            nodes.append({"id":gid,"label":g.get("title",""),"color":gc,"group":"goal"})
        rel_id = _first_related_id(g)
        if rel_id and rel_id in pid_map:
            edges.append({"from":gid,"to":pid_map[rel_id]})
    for t in todos:
        tid = "t-"+t["id"]
        if tid not in nids: nids.add(tid); nodes.append({"id":tid,"label":t.get("title",""),"color":"#9C27B0","group":"todo"})
        rel_id = _first_related_id(t)
        if rel_id and rel_id in pid_map:
            edges.append({"from":tid,"to":pid_map[rel_id]})
    for d in deps:
        did = "d-"+d["id"]
        if did not in nids: nids.add(did); nodes.append({"id":did,"label":d.get("title",""),"color":"#00BCD4","group":"deliverable"})
        rel_id = _first_related_id(d)
        if rel_id and rel_id in pid_map:
            edges.append({"from":did,"to":pid_map[rel_id]})
    for r in reminders:
        rid = "r-"+r["id"]
        if rid not in nids: nids.add(rid); nodes.append({"id":rid,"label":r.get("title",""),"color":"#FFC107","group":"reminder"})
        rel_id = _first_related_id(r)
        if rel_id and rel_id in pid_map:
            edges.append({"from":rid,"to":pid_map[rel_id]})
    counts = {}
    for n in nodes:
        g = n.get("group", "unknown")
        counts[g] = counts.get(g, 0) + 1
    return {"nodes":nodes,"edges":edges,"counts":counts}



def get_logs(ctx):
    brain = get_brain(ctx)
    logs = brain.pb.all("brain_log", filter="(brain='{}')".format(brain._context_id), sort="-created", per_page=100)
    return [{"id":l["id"],"operation":l.get("operation",""),"created":(l.get("created") or "")[:10],"details":l.get("details","") or "","page":l.get("page","") or "","goal":l.get("goal","") or "","todo":l.get("todo","") or ""} for l in logs]

def get_versions(ctx, slug=None):
    brain = get_brain(ctx)
    page_id = None
    if slug:
        try:
            pages = brain.pb.all("brain_pages", filter="(slug='{}' && brain='{}')".format(slug, brain._context_id))
            if pages:
                page_id = pages[0].get("id")
        except Exception:
            pass
    if not page_id:
        return []
    try:
        vers = brain.pb.all("brain_page_versions", filter="(page='{}')".format(page_id), sort="-version")
    except Exception:
        return []
    result = []
    for v in vers:
        result.append({
            "version": v.get("version", 0),
            "title": v.get("title", "") or "",
            "change_summary": v.get("change_summary", "") or "",
            "body_preview": (v.get("body", "") or "")[:300],
            "created": (v.get("created", "") or "")[:10],
            "updated": (v.get("updated", "") or "")[:10],
            "page_type": v.get("page_type", "") or "",
        })
    return result

# ── CRUD helpers ───────────────────────────────────────────────

def _ctx_from_qs(path):
    qs = urllib.parse.parse_qs(urllib.parse.urlparse(path).query)
    return qs.get('context', [CTX])[0]

def _read_json(handler):
    length = int(handler.headers.get('Content-Length', 0))
    if not length:
        return {}
    return json.loads(handler.rfile.read(length).decode('utf-8'))

def create_todo(ctx, payload):
    brain = get_brain(ctx)
    return brain.create_todo(
        title=payload["title"],
        domain=payload.get("domain", ""),
        page_slug=payload.get("page_slug"),
        goal_id=payload.get("goal_id"),
        content=payload.get("content", ""),
        status=payload.get("status", "backlog"),
        owner=payload.get("owner", "alvaro"),
    )

def move_todo(ctx, todo_id, status):
    brain = get_brain(ctx)
    return brain.move_todo(todo_id, status)

def create_page(ctx, payload):
    brain = get_brain(ctx)
    return brain.create_page(
        title=payload["title"],
        body=payload.get("body", ""),
        page_type=payload.get("page_type", "concept"),
        domain=payload.get("domain"),
        tags=payload.get("tags"),
        summary=payload.get("summary", ""),
        confidence=payload.get("confidence"),
        related_slugs=payload.get("related_slugs", []),
    )

def update_page(ctx, slug, payload):
    brain = get_brain(ctx)
    return brain.update_page(slug, **payload)

def delete_page(ctx, slug):
    brain = get_brain(ctx)
    return brain.delete_page(slug)

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parts = urllib.parse.urlparse(self.path)
        path = parts.path
        qs = urllib.parse.parse_qs(parts.query)
        ctx = qs.get('context', [CTX])[0]
        try:
            if path == "/": self.serve_html()
            elif path == "/api/pages": self.serve_json(get_pages(ctx, "archived" in qs))
            elif path == "/api/goals": self.serve_json(get_goals(ctx))
            elif path == "/api/todos": self.serve_json(get_todos(ctx))
            elif path == "/api/deps": self.serve_json(get_deps(ctx))
            elif path == "/api/files": self.serve_json(get_files(ctx))
            elif path == "/api/reminders": self.serve_json(get_reminders(ctx))
            elif path == "/api/journal": self.serve_json(get_journal(ctx))
            elif path == "/api/lint": self.serve_json(get_lint(ctx))
            elif path == "/api/graph": self.serve_json(get_graph(ctx))
            elif path == "/api/reports/projects": self.serve_json(report_projects(ctx))
            elif path.startswith("/api/reports/project/"):
                self.serve_json(report_project_status(ctx, path.split('/')[-1]))
            elif path == "/api/reports/todos":
                self.serve_json(report_todos(ctx, status=qs.get('status', [None])[0], project_slug=qs.get('project', [None])[0]))
            elif path == "/api/reports/journal":
                self.serve_json(report_journal(ctx, days=int(qs.get('days', ['7'])[0] or '7')))
            elif path == "/api/reports/reminders":
                self.serve_json(report_reminders(ctx, date=qs.get('date', [''])[0] or ''))
            elif path == "/api/reports/lint": self.serve_json(report_lint(ctx))
            elif path == "/api/versions": 
                self.serve_json(get_versions(ctx, qs.get('slug',[None])[0]))
            elif path == "/api/logs": self.serve_json(get_logs(ctx))
            elif path == "/api/contexts":
                pb = quick_pb(env["POCKETBRAIN_HOST"], env["POCKETBRAIN_EMAIL"], env["POCKETBRAIN_PASSWORD"]); contexts = pb.list("contexts", perPage=50)
                self.serve_json([{"name":c["name"],"label":c.get("label",""),"id":c["id"]} for c in contexts])
            elif path == "/api/config":
                self.serve_json({"pb_url": env["POCKETBRAIN_HOST"], "context": ctx})
            elif path == "/api.js":
                self.send_response(200); self.send_header("Content-Type","application/javascript; charset=utf-8"); self.send_header("Cache-Control","max-age=3600"); self.end_headers()
                js_path = Path(__file__).parent / "api.js"
                self.wfile.write(js_path.read_bytes())
            elif path == "/vis-network.min.js":
                self.send_response(200); self.send_header("Content-Type","application/javascript; charset=utf-8"); self.send_header("Cache-Control","max-age=3600"); self.end_headers()
                js_path = Path(__file__).parent / "vis-network.min.js"
                self.wfile.write(js_path.read_bytes())
            elif path == "/web_ui.css":
                self.send_response(200); self.send_header("Content-Type","text/css; charset=utf-8"); self.send_header("Cache-Control","max-age=3600"); self.end_headers()
                css_path = Path(__file__).parent / "web_ui.css"
                self.wfile.write(css_path.read_bytes())
            elif path == "/app.js":
                self.send_response(200); self.send_header("Content-Type","application/javascript; charset=utf-8"); self.send_header("Cache-Control","max-age=3600"); self.end_headers()
                js_path = Path(__file__).parent / "app.js"
                self.wfile.write(js_path.read_bytes())
            elif path == "/router.js":
                self.send_response(200); self.send_header("Content-Type","application/javascript; charset=utf-8"); self.send_header("Cache-Control","max-age=3600"); self.end_headers()
                js_path = Path(__file__).parent / "router.js"
                self.wfile.write(js_path.read_bytes())
            elif path == "/store.js":
                self.send_response(200); self.send_header("Content-Type","application/javascript; charset=utf-8"); self.send_header("Cache-Control","max-age=3600"); self.end_headers()
                js_path = Path(__file__).parent / "store.js"
                self.wfile.write(js_path.read_bytes())
            elif path == "/markdown.js":
                self.send_response(200); self.send_header("Content-Type","application/javascript; charset=utf-8"); self.send_header("Cache-Control","max-age=3600"); self.end_headers()
                js_path = Path(__file__).parent / "markdown.js"
                self.wfile.write(js_path.read_bytes())
            elif path == "/components/Tabs.js":
                self.send_response(200); self.send_header("Content-Type","application/javascript; charset=utf-8"); self.send_header("Cache-Control","max-age=3600"); self.end_headers()
                js_path = Path(__file__).parent / "components" / "Tabs.js"
                self.wfile.write(js_path.read_bytes())
            elif path == "/components/Icon.js":
                self.send_response(200); self.send_header("Content-Type","application/javascript; charset=utf-8"); self.send_header("Cache-Control","max-age=3600"); self.end_headers()
                js_path = Path(__file__).parent / "components" / "Icon.js"
                self.wfile.write(js_path.read_bytes())
            elif path.startswith("/views/"):
                js_path = Path(__file__).parent / path.lstrip('/')
                if js_path.exists() and js_path.is_file():
                    self.send_response(200); self.send_header("Content-Type","application/javascript; charset=utf-8"); self.send_header("Cache-Control","max-age=3600"); self.end_headers()
                    self.wfile.write(js_path.read_bytes())
                else:
                    self.send_response(404); self.end_headers()
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def do_POST(self):
        path = urllib.parse.urlparse(self.path).path
        ctx = _ctx_from_qs(self.path)
        try:
            body = _read_json(self)
            if path == "/api/todos":
                self.serve_json(create_todo(ctx, body))
            elif path == "/api/pages":
                self.serve_json(create_page(ctx, body))
            else:
                self.send_response(404); self.end_headers()
        except Exception as e:
            self._send_error(500, str(e))

    def do_PATCH(self):
        path = urllib.parse.urlparse(self.path).path
        ctx = _ctx_from_qs(self.path)
        try:
            body = _read_json(self)
            m = re.match(r"^/api/todos/([^/]+)/status/([^/]+)$", path)
            if m:
                self.serve_json(move_todo(ctx, m.group(1), m.group(2)))
                return
            m = re.match(r"^/api/pages/([^/]+)$", path)
            if m:
                self.serve_json(update_page(ctx, m.group(1), body))
                return
            self.send_response(404); self.end_headers()
        except Exception as e:
            self._send_error(500, str(e))

    def do_DELETE(self):
        path = urllib.parse.urlparse(self.path).path
        ctx = _ctx_from_qs(self.path)
        try:
            m = re.match(r"^/api/pages/([^/]+)$", path)
            if m:
                self.serve_json({"deleted": delete_page(ctx, m.group(1))})
                return
            self.send_response(404); self.end_headers()
        except Exception as e:
            self._send_error(500, str(e))

    def _send_error(self, code, msg):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps({"error": msg}).encode())

    def serve_json(self, data):
        self.send_response(200); self.send_header("Content-Type","application/json"); self.send_header("Access-Control-Allow-Origin","*"); self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode())
    def serve_html(self):
        self.send_response(200); self.send_header("Content-Type","text/html; charset=utf-8"); self.end_headers()
        self.wfile.write(_load_html().encode())

def _load_html():
    html_path = Path(__file__).parent / "web_ui.html"
    return html_path.read_text()
if __name__ == "__main__":
    CTX, PORT = parse_args()
    print("PocketBrain Web :: http://localhost:%d (context: %s)" % (PORT, CTX))
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    try: server.serve_forever()
    except KeyboardInterrupt: print("\nStopped")
