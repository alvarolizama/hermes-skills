#!/usr/bin/env python3
"""PocketBrain Web — Servidor live. python3 brain_web.py [--port 8080] [--context personal]"""
import sys, os, json, re, http.server, urllib.parse, time
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
_brain_cache = {}  # CTX -> Brain

def get_brain():
    global CTX
    if CTX in _brain_cache:
        return _brain_cache[CTX]
    pb = quick_pb(env["POCKETBRAIN_HOST"], env["POCKETBRAIN_EMAIL"], env["POCKETBRAIN_PASSWORD"])
    brain = Brain(CTX, pb=pb)
    brain.orient()
    _brain_cache[CTX] = brain
    return brain

def get_pages(include_archived=False):
    brain = get_brain()
    pages = brain.list_pages(include_archived=include_archived, per_page=500)
    smap = {p["slug"]: p for p in pages}
    bls = {p["slug"]: [] for p in pages}
    for pg in pages:
        for link in extract_wikilinks(pg.get("body","") or ""):
            t = link.split("|")[0].strip()
            if t in smap and t != pg["slug"]: bls[t].append(pg["slug"])
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
            "created":(pg.get("created","") or "")[:10],"updated":(pg.get("updated","") or "")[:10]})
    return result

def get_lint():
    brain = get_brain()
    return brain.lint()

def get_goals():
    brain = get_brain()
    result = []
    for pt in ['goal', 'milestone', 'okr']:
        pages = brain.pb.all("brain_pages",
            filter="(brain='{}' && page_type='{}' && archived=false)".format(brain._context_id, pt),
            expand="related_pages")
        for p in pages:
            rel = p.get("expand", {}).get("related_pages", [])
            ps = ""
            if rel and isinstance(rel, list) and len(rel) > 0 and isinstance(rel[0], dict):
                ps = rel[0].get("slug", "")
            result.append({
                "id": p["id"], "title": p.get("title", ""), "type": pt,
                "status": p.get("status", "planned"),
                "deadline": (p.get("deadline", "") or "")[:10],
                "description": p.get("body", "") or "",
                "page": ps, "page_slug": ps, "parent": "",
            })
    return result

def get_todos():
    brain = get_brain()
    pages = brain.pb.all("brain_pages",
        filter="(brain='{}' && page_type='todo' && archived=false)".format(brain._context_id),
        expand="related_pages,domain")
    result = []
    for p in pages:
        rel = p.get("expand", {}).get("related_pages", [])
        ps = ""; pt = ""
        if rel and isinstance(rel, list) and len(rel) > 0 and isinstance(rel[0], dict):
            ps = rel[0].get("slug", "")
            pt = rel[0].get("title", "")
        dom = p.get("expand", {}).get("domain", {})
        dn = dom.get("name", "") if isinstance(dom, dict) else p.get("domain", "")
        result.append({
            "id": p["id"], "title": p.get("title", ""), "status": p.get("status", "backlog"),
            "domain": dn, "owner": p.get("owner", ""),
            "content": p.get("body", "") or "",
            "page_slug": ps, "page_title": pt,
            "goal_id": "", "goal_title": "",
        })
    return result

def get_deps():
    brain = get_brain()
    pages = brain.pb.all("brain_pages",
        filter="(brain='{}' && page_type='deliverable' && archived=false)".format(brain._context_id),
        expand="related_pages")
    result = []
    for p in pages:
        rel = p.get("expand",{}).get("related_pages",[])
        ps = ""; pt = ""
        if rel and isinstance(rel,list) and len(rel)>0 and isinstance(rel[0],dict):
            ps = rel[0].get("slug",""); pt = rel[0].get("title","")
        result.append({"id":p["id"],"title":p.get("title",""),"version":p.get("version",""),
            "status":p.get("status","draft"),
            "page_slug":ps,"page_title":pt,
            "milestone":p.get("milestone","") or ""})
    return result

def get_files():
    brain = get_brain()
    pages = brain.pb.all("brain_pages",
        filter="(brain='{}' && page_type='file' && archived=false)".format(brain._context_id),
        expand="related_pages")
    result = []
    for p in pages:
        rel = p.get("expand",{}).get("related_pages",[])
        ps = ""; pt = ""
        if rel and isinstance(rel,list) and len(rel)>0 and isinstance(rel[0],dict):
            ps = rel[0].get("slug",""); pt = rel[0].get("title","")
        result.append({"id":p["id"],"name":p.get("title",""),"file_type":p.get("file_type","other"),
            "page_slug":ps,"page_title":pt})
    return result

def get_reminders():
    brain = get_brain()
    pages = brain.pb.all("brain_pages",
        filter="(brain='{}' && page_type='reminder' && archived=false)".format(brain._context_id),
        expand="related_pages")
    result = []
    for p in pages:
        rel = p.get("expand", {}).get("related_pages", [])
        ps = ""; pt = ""
        if rel and isinstance(rel, list) and len(rel) > 0 and isinstance(rel[0], dict):
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

def get_journal():
    brain = get_brain()
    pages = brain.pb.all("brain_pages",
        filter="(brain='{}' && page_type='journal' && archived=false)".format(brain._context_id),
        expand="related_pages,tags", sort="date")
    result = []
    for p in pages:
        rel = p.get("expand", {}).get("related_pages", [])
        ps = ""; pt = ""
        if rel and isinstance(rel, list) and len(rel) > 0 and isinstance(rel[0], dict):
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

def get_graph():
    brain = get_brain()
    pages = brain.list_pages(include_archived=False, per_page=500)
    smap = {p["slug"]: p for p in pages}
    pid_map = {pg.get("id",""): pg["slug"] for pg in pages if pg.get("id")}
    goals = []
    for pt in ['goal', 'milestone', 'okr']:
        goals.extend(brain.pb.all("brain_pages",
            filter="(brain='{}' && page_type='{}' && archived=false)".format(brain._context_id, pt)))
    todos = brain.pb.all("brain_pages", filter="(brain='{}' && page_type='todo' && archived=false)".format(brain._context_id))
    deps = brain.pb.all("brain_pages", filter="(brain='{}' && page_type='deliverable' && archived=false)".format(brain._context_id))
    reminders = brain.pb.all("brain_pages", filter="(brain='{}' && page_type='reminder' && archived=false)".format(brain._context_id))
    nodes, edges, nids = [], [], set()
    for pg in pages:
        slug = pg["slug"]
        if slug not in nids:
            nids.add(slug)
            nodes.append({"id":slug,"label":pg.get("title",slug),"color":COLORS.get(pg.get("page_type","concept"),"#607D8B"),"group":pg.get("page_type","concept")})
        for link in extract_wikilinks(pg.get("body","") or ""):
            t = link.split("|")[0].strip()
            if t in smap and t != slug: edges.append({"from":slug,"to":t})
    gmap = {}
    for g in goals:
        gid = "g-"+g["id"]; gmap[g["id"]] = gid
        if gid not in nids:
            nids.add(gid)
            gc = {"goal":"#4CAF50","milestone":"#FF9800","okr":"#E91E63"}.get(g.get("page_type",""),"#888")
            nodes.append({"id":gid,"label":g.get("title",""),"color":gc,"group":"goal"})
        # Link via related_pages (first is project/page)
        rel = g.get("related_pages", []) or []
        if rel and isinstance(rel, list) and len(rel) > 0:
            first = rel[0] if isinstance(rel[0], str) else (rel[0].get("id","") if isinstance(rel[0], dict) else "")
            if first in pid_map: edges.append({"from":gid,"to":pid_map[first]})
    for t in todos:
        tid = "t-"+t["id"]
        if tid not in nids: nids.add(tid); nodes.append({"id":tid,"label":t.get("title",""),"color":"#9C27B0","group":"todo"})
        rel = t.get("related_pages", []) or []
        if rel and isinstance(rel, list) and len(rel) > 0:
            first = rel[0] if isinstance(rel[0], str) else (rel[0].get("id","") if isinstance(rel[0], dict) else "")
            if first in pid_map: edges.append({"from":tid,"to":pid_map[first]})
    for d in deps:
        did = "d-"+d["id"]
        if did not in nids: nids.add(did); nodes.append({"id":did,"label":d.get("title",""),"color":"#00BCD4","group":"deliverable"})
        if d.get("page") and d["page"] in pid_map: edges.append({"from":did,"to":pid_map[d["page"]]})
    for r in reminders:
        rid = "r-"+r["id"]
        if rid not in nids: nids.add(rid); nodes.append({"id":rid,"label":r.get("title",""),"color":"#FFC107","group":"reminder"})
        if r.get("related_pages"):
            rids = r["related_pages"]
            if isinstance(rids, list) and len(rids) > 0:
                first = rids[0] if isinstance(rids[0], str) else (rids[0].get("id","") if isinstance(rids[0], dict) else "")
                if first in pid_map: edges.append({"from":rid,"to":pid_map[first]})
    counts = {}
    for n in nodes:
        g = n.get("group", "unknown")
        counts[g] = counts.get(g, 0) + 1
    return {"nodes":nodes,"edges":edges,"counts":counts}



def get_logs():
    brain = get_brain()
    logs = brain.pb.all("brain_log", filter="(brain='{}')".format(brain._context_id), sort="-created", per_page=100)
    return [{"id":l["id"],"operation":l.get("operation",""),"created":(l.get("created") or "")[:10],"details":l.get("details","") or "","page":l.get("page","") or "","goal":l.get("goal","") or "","todo":l.get("todo","") or ""} for l in logs]

def get_versions(slug=None):
    try:
        from brain import Brain
    except Exception:
        pass
    brain = get_brain()
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

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        global CTX
        parts = urllib.parse.urlparse(self.path)
        path = parts.path
        qs = urllib.parse.parse_qs(parts.query)
        if 'context' in qs: CTX = qs['context'][0]
        if path == "/": self.serve_html()
        elif path == "/api/pages": self.serve_json(get_pages("archived" in qs))
        elif path == "/api/goals": self.serve_json(get_goals())
        elif path == "/api/todos": self.serve_json(get_todos())
        elif path == "/api/deps": self.serve_json(get_deps())
        elif path == "/api/files": self.serve_json(get_files())
        elif path == "/api/reminders": self.serve_json(get_reminders())
        elif path == "/api/journal": self.serve_json(get_journal())
        elif path == "/api/lint": self.serve_json(get_lint())
        elif path == "/api/graph": self.serve_json(get_graph())
        elif path == "/api/versions": 
            self.serve_json(get_versions(qs.get('slug',[None])[0]))
        elif path == "/api/logs": self.serve_json(get_logs())
        elif path == "/api/contexts":
            pb = quick_pb(env["POCKETBRAIN_HOST"], env["POCKETBRAIN_EMAIL"], env["POCKETBRAIN_PASSWORD"]); contexts = pb.list("contexts", perPage=50)
            self.serve_json([{"name":c["name"],"label":c.get("label",""),"id":c["id"]} for c in contexts])
        elif path == "/api/config":
            brain = get_brain()
            self.serve_json({"pb_url": env["POCKETBRAIN_HOST"], "token": brain.pb.get_token(), "context": CTX})
        else: self.send_response(404); self.end_headers()
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
