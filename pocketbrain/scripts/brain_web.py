#!/usr/bin/env python3
"""PocketBrain Web — Servidor live. python3 brain_web.py [--port 8080] [--brain personal]"""
import sys, os, json, re, http.server, urllib.parse
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
os.environ["POCKETBASE_HOST"] = env["POCKETBASE_HOST"]
os.environ["POCKETBASE_EMAIL"] = env["POCKETBASE_EMAIL"]
os.environ["POCKETBASE_PASSWORD"] = env["POCKETBASE_PASSWORD"]

from brain import Brain, extract_wikilinks
from pb import quick_pb

COLORS = {"entity":"#4CAF50","concept":"#2196F3","comparison":"#FF9800","query":"#9C27B0","raw":"#607D8B","project":"#E91E63"}
BN = "personal"

def parse_args():
    args = sys.argv[1:]
    bn, port = "personal", 8080
    i = 0
    while i < len(args):
        if args[i] == "--brain" and i+1 < len(args): bn = args[i+1]; i+=2
        elif args[i] == "--port" and i+1 < len(args): port = int(args[i+1]); i+=2
        else: i+=1
    return bn, port

def get_brain():
    pb = quick_pb()
    brain = Brain(BN, pb=pb)
    brain.orient()
    return brain

def get_pages():
    brain = get_brain()
    pages = brain.list_pages(include_archived=False, per_page=500)
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
        result.append({"slug":pg["slug"],"title":pg.get("title",pg["slug"]),
            "page_type":pg.get("page_type","concept"),"color":COLORS.get(pg.get("page_type","concept"),"#607D8B"),
            "confidence":pg.get("confidence",""),"summary":pg.get("summary","") or "",
            "domain":dn,"tags":tns,"body":pg.get("body","") or "","backlinks":bld})
    return result

def get_goals():
    brain = get_brain()
    goals = brain.pb.all("brain_goals", filter="(brain='" + brain._brain_id + "')")
    return [{"id":g["id"],"title":g.get("title",""),"type":g.get("type","goal"),
        "status":g.get("status","planned"),"progress":g.get("progress",0) or 0,
        "deadline":(g.get("deadline","") or "")[:10],"description":g.get("description","") or "",
        "page":g.get("page","") or "","parent":g.get("parent","") or ""} for g in goals]

def get_todos():
    brain = get_brain()
    todos = brain.pb.all("brain_todos", filter="(brain='" + brain._brain_id + "')", expand="page,goal")
    result = []
    for t in todos:
        pg = t.get("expand",{}).get("page",{})
        gl = t.get("expand",{}).get("goal",{})
        result.append({"id":t["id"],"title":t.get("title",""),"status":t.get("status","backlog"),
            "domain":t.get("domain",""),"owner":t.get("owner",""),
            "content":t.get("content","") or "",
            "page_slug":pg.get("slug","") if isinstance(pg,dict) else "",
            "page_title":pg.get("title","") if isinstance(pg,dict) else "",
            "goal_id":t.get("goal","") or "","goal_title":gl.get("title","") if isinstance(gl,dict) else ""})
    return result

def get_deps():
    brain = get_brain()
    deps = brain.pb.all("brain_deliverables", filter="(brain='" + brain._brain_id + "')", expand="page")
    result = []
    for d in deps:
        pg = d.get("expand",{}).get("page",{})
        result.append({"id":d["id"],"title":d.get("title",""),"version":d.get("version",""),
            "status":d.get("status","draft"),
            "page_slug":pg.get("slug","") if isinstance(pg,dict) else "",
            "page_title":pg.get("title","") if isinstance(pg,dict) else "",
            "milestone":d.get("milestone","") or ""})
    return result

def get_files():
    brain = get_brain()
    files = brain.pb.all("brain_files", expand="page")
    result = []
    for f in files:
        pg = f.get("expand",{}).get("page",{})
        result.append({"id":f["id"],"name":f.get("name",""),"file_type":f.get("file_type","other"),
            "page_slug":pg.get("slug","") if isinstance(pg,dict) else "",
            "page_title":pg.get("title","") if isinstance(pg,dict) else ""})
    return result

def get_reminders():
    brain = get_brain()
    rems = brain.pb.all("brain_reminders", filter="(brain='" + brain._brain_id + "')", expand="page")
    result = []
    for r in rems:
        pg = r.get("expand",{}).get("page",{})
        result.append({"id":r["id"],"title":r.get("title",""),"content":r.get("content","") or "",
            "date":(r.get("date","") or "")[:10],"time":r.get("time","") or "",
            "done":r.get("done",False),"done_date":(r.get("done_date","") or "")[:10],
            "page_slug":pg.get("slug","") if isinstance(pg,dict) else "",
            "page_title":pg.get("title","") if isinstance(pg,dict) else ""})
    return result

def get_graph():
    brain = get_brain()
    pages = brain.list_pages(include_archived=False, per_page=500)
    smap = {p["slug"]: p for p in pages}
    pid_map = {pg.get("id",""): pg["slug"] for pg in pages if pg.get("id")}
    goals = brain.pb.all("brain_goals", filter="(brain='" + brain._brain_id + "')")
    todos = brain.pb.all("brain_todos", filter="(brain='" + brain._brain_id + "')")
    deps = brain.pb.all("brain_deliverables", filter="(brain='" + brain._brain_id + "')")
    reminders = brain.pb.all("brain_reminders", filter="(brain='" + brain._brain_id + "')")
    nodes, edges, nids = [], [], set()
    for pg in pages:
        slug = pg["slug"]
        if slug not in nids:
            nids.add(slug)
            nodes.append({"id":slug,"label":pg.get("title",slug),"color":COLORS.get(pg.get("page_type","concept"),"#607D8B"),"group":"page"})
        for link in extract_wikilinks(pg.get("body","") or ""):
            t = link.split("|")[0].strip()
            if t in smap and t != slug: edges.append({"from":slug,"to":t})
    gmap = {}
    for g in goals:
        gid = "g-"+g["id"]; gmap[g["id"]] = gid
        if gid not in nids:
            nids.add(gid)
            gc = {"goal":"#4CAF50","milestone":"#FF9800","okr":"#E91E63"}.get(g.get("type",""),"#888")
            nodes.append({"id":gid,"label":g.get("title",""),"color":gc,"group":"goal"})
        if g.get("page") and g["page"] in pid_map: edges.append({"from":gid,"to":pid_map[g["page"]]})
        if g.get("parent") and g["parent"] in gmap: edges.append({"from":gid,"to":gmap[g["parent"]]})
    for t in todos:
        tid = "t-"+t["id"]
        if tid not in nids: nids.add(tid); nodes.append({"id":tid,"label":t.get("title",""),"color":"#9C27B0","group":"todo"})
        if t.get("page") and t["page"] in pid_map: edges.append({"from":tid,"to":pid_map[t["page"]]})
        if t.get("goal") and t["goal"] in gmap: edges.append({"from":tid,"to":gmap[t["goal"]]})
    for d in deps:
        did = "d-"+d["id"]
        if did not in nids: nids.add(did); nodes.append({"id":did,"label":d.get("title",""),"color":"#00BCD4","group":"deliverable"})
        if d.get("page") and d["page"] in pid_map: edges.append({"from":did,"to":pid_map[d["page"]]})
    for r in reminders:
        rid = "r-"+r["id"]
        if rid not in nids: nids.add(rid); nodes.append({"id":rid,"label":r.get("title",""),"color":"#FFC107","group":"reminder"})
        if r.get("page") and r["page"] in pid_map: edges.append({"from":rid,"to":pid_map[r["page"]]})
    return {"nodes":nodes,"edges":edges}

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        global BN
        parts = urllib.parse.urlparse(self.path)
        path = parts.path
        qs = urllib.parse.parse_qs(parts.query)
        if 'brain' in qs: BN = qs['brain'][0]
        if path == "/": self.serve_html()
        elif path == "/api/pages": self.serve_json(get_pages())
        elif path == "/api/goals": self.serve_json(get_goals())
        elif path == "/api/todos": self.serve_json(get_todos())
        elif path == "/api/deps": self.serve_json(get_deps())
        elif path == "/api/files": self.serve_json(get_files())
        elif path == "/api/reminders": self.serve_json(get_reminders())
        elif path == "/api/graph": self.serve_json(get_graph())
        elif path == "/api/brain": self.serve_json({"name":BN})
        elif path == "/api/brains":
            pb = quick_pb(); brains = pb.list("brains", perPage=50)
            self.serve_json([{"name":b["name"],"label":b.get("label",""),"id":b["id"]} for b in brains])
        else: self.send_response(404); self.end_headers()
    def serve_json(self, data):
        self.send_response(200); self.send_header("Content-Type","application/json"); self.send_header("Access-Control-Allow-Origin","*"); self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode())
    def serve_html(self):
        self.send_response(200); self.send_header("Content-Type","text/html; charset=utf-8"); self.end_headers()
        self.wfile.write(HTML.encode())

HTML = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>PocketBrain</title>
<script src="https://unpkg.com/vis-network@9.1.6/dist/vis-network.min.js"></script>
<style>
:root{--ink:#000;--canvas:#fff;--soft:#fafafa;--hairline:#e5e5e5;--body:#737373;--mute:#a3a3a3;--red:#e74c3c;--green:#4CAF50;--orange:#FF9800;--pink:#E91E63;--purple:#9C27B0;--cyan:#00BCD4;--yellow:#FFC107}
*{margin:0;padding:0;box-sizing:border-box}
body{background:var(--canvas);color:var(--ink);font-family:ui-sans-serif,system-ui,-apple-system,sans-serif;display:flex;height:100vh;overflow:hidden}
#sidebar{width:240px;min-width:240px;background:var(--canvas);border-right:1px solid var(--hairline);display:flex;flex-direction:column;z-index:10;padding:16px}
#sidebar h2{font-family:SF Pro Rounded,system-ui,sans-serif;font-size:18px;font-weight:600;margin-bottom:8px}
#sidebar h2 a{color:var(--ink);text-decoration:none}
#brain-selector{width:100%;padding:6px 10px;border:1px solid var(--hairline);border-radius:9999px;font-size:12px;background:var(--canvas);color:var(--body);margin-bottom:8px}
#search{width:100%;padding:8px 14px;border:1px solid var(--hairline);border-radius:9999px;background:var(--soft);color:var(--ink);font-size:13px;margin-bottom:12px;outline:none}
#search:focus{background:var(--canvas);border-color:var(--ink)}
#nav{flex:1;overflow-y:auto;font-size:13px}
#nav .nav-section{font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:.5px;color:var(--mute);padding:10px 4px 6px;cursor:pointer}
#nav .nav-section:hover{color:var(--ink)}
#nav .nav-sub{display:none;padding-left:4px}
#nav .nav-sub.open{display:block}
#nav .nav-sub a{font-size:12px;padding:3px 8px;display:block;color:var(--body);text-decoration:none;border-radius:6px;cursor:pointer}
#nav .nav-sub a:hover,#nav .nav-sub a.active{color:var(--ink);background:var(--soft)}
#nav .group{color:var(--mute);font-size:10px;text-transform:uppercase;letter-spacing:1px;padding:10px 4px 4px}
#status{font-size:10px;color:var(--mute);padding:8px 4px;border-top:1px solid var(--hairline)}
#main{flex:1;overflow-y:auto}
#view-projects,#view-todos,#view-goals,#view-journal,#view-reminders,#view-wiki,#view-graph{display:none;padding:40px 60px;max-width:900px}
#view-projects.active,#view-todos.active,#view-goals.active,#view-journal.active,#view-reminders.active,#view-wiki.active,#view-graph.active{display:block}
#view-graph.active{display:flex;flex-direction:column;max-width:none;padding:0;height:100%}
#graph-view{position:absolute;top:0;left:0;right:0;bottom:0;min-height:400px}
#graph-legend{position:absolute;top:12px;right:12px;background:var(--canvas);border:1px solid var(--hairline);padding:8px 12px;border-radius:12px;font-size:11px;display:flex;gap:12px;flex-wrap:wrap}
#graph-legend span{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:4px;vertical-align:middle}
h1{font-family:SF Pro Rounded,system-ui,sans-serif;font-size:30px;font-weight:500;margin-bottom:8px}
h2{font-family:SF Pro Rounded,system-ui,sans-serif;font-size:20px;font-weight:600;margin:28px 0 10px}
h3{font-size:16px;font-weight:500;margin:16px 0 6px}
p,li{line-height:1.6;margin-bottom:6px;font-size:15px;color:var(--body)}
.wl{color:var(--ink);text-decoration:underline;cursor:pointer}
.bl{color:var(--red);text-decoration:line-through;cursor:help}
.meta{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:16px;font-size:12px;color:var(--mute)}
.meta span{background:var(--soft);padding:2px 8px;border-radius:9999px}
.meta .tag{background:var(--ink);color:var(--canvas);font-size:11px}
.bl-section{margin-top:32px;padding-top:16px;border-top:1px solid var(--hairline)}
.bl-section h3{font-size:13px;color:var(--mute)}
.bl-section a{display:inline-block;margin:2px 8px 2px 0;font-size:12px}
.card{background:var(--canvas);border:1px solid var(--hairline);border-radius:12px;padding:20px;margin-bottom:12px}
.card h3{font-size:15px;font-weight:600;margin-bottom:4px}
.chip{display:inline-block;padding:2px 10px;border-radius:9999px;font-size:11px;font-weight:500;margin-right:4px}
.chip-goal{background:#E8F5E9;color:var(--green)}.chip-milestone{background:#FFF3E0;color:var(--orange)}
.chip-okr{background:#FCE4EC;color:var(--pink)}.chip-todo{background:#F3E5F5;color:var(--purple)}
.chip-dep{background:#E0F7FA;color:var(--cyan)}.chip-rem{background:#FFF8E1;color:var(--yellow)}
.progress-bar{height:6px;background:var(--soft);border-radius:9999px;margin-top:6px;overflow:hidden}
.progress-fill{height:100%;background:var(--green);border-radius:9999px;transition:width .3s}
.kanban{display:flex;gap:16px;overflow-x:auto;padding-bottom:20px}
.kanban-col{flex:1;min-width:180px;background:var(--soft);border-radius:12px;padding:12px}
.kanban-col h3{font-size:13px;font-weight:600;text-transform:uppercase;letter-spacing:.5px;margin-bottom:8px;color:var(--mute)}
.kanban-card{background:var(--canvas);border:1px solid var(--hairline);border-radius:8px;padding:10px 12px;margin-bottom:8px;font-size:13px}
.kanban-card .meta2{font-size:10px;color:var(--mute);margin-top:4px}
.hamburger{display:none;position:fixed;top:12px;left:12px;z-index:100;background:var(--canvas);border:1px solid var(--hairline);color:var(--ink);font-size:20px;padding:6px 10px;border-radius:9999px;cursor:pointer}
.nav-filter{margin:8px 0}
.nav-filter select{padding:6px 12px;border:1px solid var(--hairline);border-radius:9999px;font-size:13px;background:var(--canvas);color:var(--body);max-width:100%}
@media(max-width:768px){
.hamburger{display:block}
#sidebar{position:fixed;top:0;left:0;bottom:0;z-index:99;transform:translateX(-100%);transition:transform .3s;box-shadow:2px 0 12px rgba(0,0,0,.1)}
#sidebar.open{transform:translateX(0)}
#main{margin-left:0}
#view-projects,#view-todos,#view-goals,#view-journal,#view-reminders,#view-wiki{padding:16px;padding-top:56px;max-width:100%}
.kanban{overflow-x:auto;flex-direction:row;gap:8px;-webkit-overflow-scrolling:touch}
.kanban-col{min-width:150px;flex:none;flex-shrink:0}
.card{padding:16px;margin-bottom:8px}
h1{font-size:24px}h2{font-size:18px}
#nav .nav-section{font-size:13px;padding:12px 4px 8px}
#nav .nav-sub a{padding:8px 12px;font-size:14px}
}
</style>
</head>
<body>
<button class="hamburger" onclick="document.getElementById('sidebar').classList.toggle('open')">☰</button>
<div id="sidebar">
  <h2>PocketBrain</h2>
  <select id="brain-selector" onchange="switchBrain(this.value)" style="width:100%;padding:6px 10px;border:1px solid var(--hairline);border-radius:9999px;font-size:12px;background:var(--canvas);color:var(--body);margin-bottom:8px"><option>Cargando...</option></select>
  <input type="text" id="search" placeholder="Buscar..." oninput="filterSidebar()">
  <div id="nav"></div>
  <div id="status">● cargando...</div>
</div>
<div id="main">
  <div id="view-projects" class="active"><p style="color:var(--mute)">Cargando...</p></div>
  <div id="view-todos"></div>
  <div id="view-goals"></div>
  <div id="view-journal"></div>
  <div id="view-reminders"></div>
  <div id="view-wiki"></div>
  <div id="view-graph"><div id="graph-view"></div><div id="graph-legend"></div></div>
</div>
<script>
var PAGES=[],GOALS=[],TODOS=[],DEPS=[],FILES=[],REMINDERS=[],GRAPH={nodes:[],edges:[]};
var pmap={},gmap={};
var _todoFilter='',_goalFilter='',_journalFilter='',_reminderFilter='';
var currentBrain='',ALL_TABS=['projects','todos','goals','journal','reminders','wiki','graph'];

function api(path){var b=currentBrain||'personal';var sep=path.indexOf('?')>-1?'&':'?';return fetch('/api'+path+sep+'brain='+b).then(function(r){return r.json();});}
function loadBrains(){api('/brains').then(function(brains){var sel=document.getElementById('brain-selector');sel.innerHTML=brains.map(function(b){var s=b.name===currentBrain?' selected':'';return'<option value="'+b.name+'"'+s+'>'+b.name+'</option>';}).join('');currentBrain=sel.value||brains[0]?.name||'personal';loadAll();});}
function switchBrain(name){currentBrain=name;_graphInit=false;PAGES=[];GOALS=[];TODOS=[];DEPS=[];FILES=[];REMINDERS=[];loadAll();}
function loadAll(){document.getElementById('status').textContent='● cargando...';var b=currentBrain||'personal';Promise.all([api('/pages'),api('/goals'),api('/todos'),api('/deps'),api('/files'),api('/reminders'),api('/graph')]).then(function(results){PAGES=results[0];GOALS=results[1];TODOS=results[2];DEPS=results[3];FILES=results[4];REMINDERS=results[5];GRAPH=results[6];pmap={};PAGES.forEach(function(p){pmap[p.slug]=p;});gmap={};GOALS.forEach(function(g){gmap[g.id]=g;});buildSidebar();renderProjectsList();document.getElementById('status').textContent='● live';}).catch(function(e){document.getElementById('status').textContent='● error';console.error(e);setTimeout(loadAll,2000);});}
function filterSidebar(){var q=document.getElementById('search').value.toLowerCase();document.querySelectorAll('#nav a[data-search]').forEach(function(a){a.style.display=(q&&!a.getAttribute('data-search').includes(q))?'none':'block';});}
function toggleSection(id){document.getElementById(id).classList.toggle('open');}
function activateView(id){ALL_TABS.forEach(function(t){document.getElementById('view-'+t).classList.toggle('active',t===id);});document.getElementById('sidebar').classList.remove('open');}
function buildSidebar(){var nav=document.getElementById('nav');var projects=PAGES.filter(function(p){return p.page_type==='project';});var h='';h+='<div class="nav-section" onclick="toggleSection(\\'sub-todo\\')">☐ Todo</div><div class="nav-sub open" id="sub-todo"><a href="#" onclick="showTab(\\'todos\\');setTodoFilter(\\'noproject\\')">Sin proyecto</a><a href="#" onclick="showTab(\\'todos\\');setTodoFilter(\\'\\')">Ver todas</a></div>';h+='<div class="nav-section" onclick="toggleSection(\\'sub-goals\\')">◈ Goals</div><div class="nav-sub" id="sub-goals"><a href="#" onclick="showTab(\\'goals\\');setGoalFilter(\\'noproject\\')">Sin proyecto</a><a href="#" onclick="showTab(\\'goals\\');setGoalFilter(\\'\\')">Ver todos</a></div>';h+='<div class="nav-section" onclick="toggleSection(\\'sub-journal\\')">📓 Journal</div><div class="nav-sub" id="sub-journal"><a href="#" onclick="showTab(\\'journal\\');setJournalFilter(\\'noproject\\')">Sin proyecto</a><a href="#" onclick="showTab(\\'journal\\');setJournalFilter(\\'\\')">Ver todos</a></div>';h+='<div class="nav-section" onclick="toggleSection(\\'sub-reminders\\')">⏰ Reminders</div><div class="nav-sub" id="sub-reminders"><a href="#" onclick="showTab(\\'reminders\\');setReminderFilter(\\'noproject\\')">Sin proyecto</a><a href="#" onclick="showTab(\\'reminders\\');setReminderFilter(\\'\\')">Ver todos</a><a href="#" onclick="showTab(\\'reminders\\');setReminderFilter(\\'today\\')">Hoy</a></div>';h+='<div class="nav-section" onclick="toggleSection(\\'sub-projects\\')">📁 Proyectos</div><div class="nav-sub" id="sub-projects">';projects.forEach(function(p){h+='<a href="#" onclick="showProject(\\''+p.slug+'\\')">'+p.title+'</a>';});if(!projects.length)h+='<div style="font-size:11px;color:var(--mute);padding:4px 8px">Sin proyectos</div>';h+='</div>';h+='<div class="nav-section" onclick="toggleSection(\\'sub-wiki\\')">📄 Wiki</div><div class="nav-sub" id="sub-wiki">';var byType={};PAGES.forEach(function(p){var pt=p.page_type||'concept';byType[pt]=byType[pt]||[];byType[pt].push(p);});var tn={project:'Proyectos',concept:'Conceptos',entity:'Entidades',comparison:'Comparaciones',query:'Consultas',raw:'Raw'};['project','concept','entity','comparison','query','raw'].forEach(function(pt){var items=byType[pt]||[];if(!items.length)return;h+='<div class="group">'+tn[pt]+' ('+items.length+')</div>';items.sort(function(a,b){return a.title.localeCompare(b.title);});items.forEach(function(p){h+='<a href="#" data-search="'+(p.title+' '+p.slug).toLowerCase()+'" onclick="showPage(\\''+p.slug+'\\')">'+p.title+'</a>';});});h+='</div>';h+='<div class="nav-section" style="cursor:pointer" onclick="showTab(\\'graph\\')">◉ Graph</div>';nav.innerHTML=h;}
function showTab(tab){activateView(tab);if(tab==='projects')renderProjectsList();if(tab==='todos')renderTodosView();if(tab==='goals')renderGoalsView();if(tab==='journal')renderJournalView();if(tab==='reminders')renderRemindersView();if(tab==='wiki')showPage('index');if(tab==='graph')setTimeout(renderGraph,300);}
function setTodoFilter(v){_todoFilter=v;renderTodosView();}
function setGoalFilter(v){_goalFilter=v;renderGoalsView();}
function setJournalFilter(v){_journalFilter=v;renderJournalView();}
function setReminderFilter(v){_reminderFilter=v;renderRemindersView();}
function renderProjectsList(){activateView('projects');var projects=PAGES.filter(function(p){return p.page_type==='project';});var h='<h1>Proyectos</h1><p style="color:var(--mute);margin-bottom:20px">'+projects.length+' proyectos</p>';projects.forEach(function(p){var pg=GOALS.filter(function(g){return g.page===p.slug;}).length;var pt=TODOS.filter(function(t){return t.page_slug===p.slug;}).length;var pd=DEPS.filter(function(d){return d.page_slug===p.slug;}).length;h+='<div class="card" style="cursor:pointer" onclick="showProject(\\''+p.slug+'\\')"><h3>'+p.title+'</h3><div style="font-size:12px;color:var(--mute)">'+pg+' goals &middot; '+pt+' tareas &middot; '+pd+' entregables</div>'+(p.summary?'<p style="font-size:13px;color:var(--body);margin-top:4px">'+p.summary.substring(0,120)+'</p>':'')+'</div>';});document.getElementById('view-projects').innerHTML=h||'<p style="color:var(--mute)">No hay proyectos.</p>';}
function showProject(slug){activateView('projects');var p=pmap[slug];if(!p)return;var pgoals=GOALS.filter(function(g){return g.page===slug;});var ptodos=TODOS.filter(function(t){return t.page_slug===slug;});var pdeps=DEPS.filter(function(d){return d.page_slug===slug;});var pfiles=FILES.filter(function(f){return f.page_slug===slug;});var h='<div style="font-size:12px;color:var(--mute);margin-bottom:12px"><a href="#" onclick="renderProjectsList()" style="color:var(--ink)">Proyectos</a> &raquo; '+p.title+'</div><h1>'+p.title+'</h1>';if(p.summary)h+='<p style="color:var(--body)">'+p.summary+'</p>';h+='<h2>Goals ('+pgoals.length+')</h2>';pgoals.forEach(function(g){var chip=g.type==='okr'?'chip-okr':g.type==='milestone'?'chip-milestone':'chip-goal';h+='<div class="card"><h3><span class="chip '+chip+'">'+g.type+'</span> '+g.title+'</h3><div style="font-size:12px;color:var(--mute)">'+g.status+(g.deadline?' &middot; '+g.deadline:'')+'</div>'+(g.type==='goal'?'<div class="progress-bar"><div class="progress-fill" style="width:'+g.progress+'%"></div></div><div style="font-size:11px;color:var(--mute)">'+g.progress+'%</div>':'')+'</div>';});var ss=['backlog','this week','today','in progress','done','cancelled'];var sl={backlog:'Backlog','this week':'This Week',today:'Today','in progress':'In Progress',done:'Done',cancelled:'Cancelled'};h+='<h2>Kanban</h2><div class="kanban">';var bs={};ss.forEach(function(s){bs[s]=[];});ptodos.forEach(function(t){var s=t.status||'backlog';if(bs[s])bs[s].push(t);});ss.forEach(function(s){h+='<div class="kanban-col"><h3>'+sl[s]+' ('+bs[s].length+')</h3>';bs[s].forEach(function(t){h+='<div class="kanban-card">'+t.title+'<div class="meta2">'+t.domain+'</div></div>';});h+='</div>';});h+='</div>';if(pdeps.length){h+='<h2>Entregables ('+pdeps.length+')</h2>';pdeps.forEach(function(d){h+='<div class="card"><h3>'+d.title+' <span class="chip chip-dep">'+d.version+'</span> <span class="chip chip-dep">'+d.status+'</span></h3><div style="font-size:12px;color:var(--mute)">'+d.milestone+'</div></div>';});}if(pfiles.length){h+='<h2>Archivos ('+pfiles.length+')</h2>';pfiles.forEach(function(f){h+='<div class="card"><h3>'+f.name+' <span class="chip chip-dep">'+f.file_type+'</span></h3></div>';});}document.getElementById('view-projects').innerHTML=h;document.getElementById('view-projects').scrollTop=0;}
function renderTodosView(){activateView('todos');var filtered=TODOS;if(_todoFilter==='noproject')filtered=TODOS.filter(function(t){return !t.page_slug;});else if(_todoFilter)filtered=TODOS.filter(function(t){return t.page_slug===_todoFilter;});var projects=PAGES.filter(function(p){return p.page_type==='project';});var popts=projects.map(function(p){var sel=p.slug===_todoFilter?' selected':'';return'<option value="'+p.slug+'"'+sel+'>'+p.title+'</option>';}).join('');var h='<h1>Todo</h1><div class="nav-filter"><select onchange="setTodoFilter(this.value)" style="padding:6px 12px;border:1px solid var(--hairline);border-radius:9999px;font-size:13px;background:var(--canvas);color:var(--body)"><option value="">Todas las tareas</option><option value="noproject"'+( _todoFilter==='noproject'?' selected':'')+'>Sin proyecto</option>'+popts+'</select></div><p style="color:var(--mute);margin-bottom:16px">'+filtered.length+' tareas</p><div class="kanban">';var ss=['backlog','this week','today','in progress','done','cancelled'];var sl={backlog:'Backlog','this week':'This Week',today:'Today','in progress':'In Progress',done:'Done',cancelled:'Cancelled'};var bs={};ss.forEach(function(s){bs[s]=[];});filtered.forEach(function(t){var s=t.status||'backlog';if(bs[s])bs[s].push(t);});ss.forEach(function(s){h+='<div class="kanban-col"><h3>'+sl[s]+' ('+bs[s].length+')</h3>';bs[s].forEach(function(t){h+='<div class="kanban-card">'+t.title+'<div class="meta2">'+t.domain+(t.goal_title?' &middot; '+t.goal_title:'')+(t.page_title?' &middot; '+t.page_title:'')+'</div></div>';});h+='</div>';});h+='</div>';document.getElementById('view-todos').innerHTML=h;}
function renderGoalsView(){activateView('goals');var filtered=GOALS;if(_goalFilter==='noproject')filtered=GOALS.filter(function(g){return !g.page;});else if(_goalFilter)filtered=GOALS.filter(function(g){return g.page===_goalFilter;});var projects=PAGES.filter(function(p){return p.page_type==='project';});var popts=projects.map(function(p){var sel=p.slug===_goalFilter?' selected':'';return'<option value="'+p.slug+'"'+sel+'>'+p.title+'</option>';}).join('');var parents=filtered.filter(function(g){return !g.parent;});var h='<h1>Goals</h1><div class="nav-filter"><select onchange="setGoalFilter(this.value)" style="padding:6px 12px;border:1px solid var(--hairline);border-radius:9999px;font-size:13px;background:var(--canvas);color:var(--body)"><option value="">Todos los goals</option><option value="noproject"'+( _goalFilter==='noproject'?' selected':'')+'>Sin proyecto</option>'+popts+'</select></div><p style="color:var(--mute);margin-bottom:20px">'+parents.length+' goals</p>';parents.forEach(function(g){var kids=GOALS.filter(function(k){return k.parent===g.id;});var chip=g.type==='okr'?'chip-okr':g.type==='milestone'?'chip-milestone':'chip-goal';h+='<div class="card"><h3><span class="chip '+chip+'">'+g.type+'</span> '+g.title+'</h3><div style="font-size:12px;color:var(--mute)">'+g.status+(g.deadline?' &middot; '+g.deadline:'')+'</div>'+(g.type==='goal'?'<div class="progress-bar"><div class="progress-fill" style="width:'+g.progress+'%"></div></div><div style="font-size:11px;color:var(--mute)">'+g.progress+'%</div>':'')+(kids.length?'<div style="margin-top:8px;font-size:13px;color:var(--body)">Key Results:</div>'+kids.map(function(k){return'<div style="font-size:12px;padding:4px 0">'+k.title+' <span style="color:var(--mute)">'+k.progress+'%</span></div>';}).join(''):'')+'</div>';});document.getElementById('view-goals').innerHTML=h||'<p style="color:var(--mute)">No goals.</p>';}
function renderRemindersView(){activateView('reminders');var filtered=REMINDERS;if(_reminderFilter==='noproject')filtered=REMINDERS.filter(function(r){return !r.page_slug;});else if(_reminderFilter==='today'){var today=new Date().toISOString().slice(0,10);filtered=REMINDERS.filter(function(r){return r.date===today;});}else if(_reminderFilter)filtered=REMINDERS.filter(function(r){return r.page_slug===_reminderFilter;});var projects=PAGES.filter(function(p){return p.page_type==='project';});var popts=projects.map(function(p){var sel=p.slug===_reminderFilter?' selected':'';return'<option value="'+p.slug+'"'+sel+'>'+p.title+'</option>';}).join('');var h='<h1>⏰ Reminders</h1><div class="nav-filter"><select onchange="setReminderFilter(this.value)" style="padding:6px 12px;border:1px solid var(--hairline);border-radius:9999px;font-size:13px;background:var(--canvas);color:var(--body)"><option value="">Todos</option><option value="noproject"'+( _reminderFilter==='noproject'?' selected':'')+'>Sin proyecto</option><option value="today"'+( _reminderFilter==='today'?' selected':'')+'>Hoy</option>'+popts+'</select></div><p style="color:var(--mute);margin-bottom:16px">'+filtered.length+' recordatorios</p>';var upcoming=filtered.filter(function(r){return !r.done;}).sort(function(a,b){return a.date.localeCompare(b.date)||(a.time||'').localeCompare(b.time||'');});var completed=filtered.filter(function(r){return r.done;});upcoming.forEach(function(r){h+='<div class="card"><h3>'+r.title+'</h3><div style="font-size:12px;color:var(--mute)">'+r.date+(r.time?' &middot; '+r.time:'')+(r.page_title?' &middot; '+r.page_title:'')+'</div>'+(r.content?'<p style="font-size:13px;color:var(--body);margin-top:4px">'+r.content+'</p>':'')+'</div>';});if(completed.length){h+='<h2>Completados ('+completed.length+')</h2>';completed.forEach(function(r){h+='<div class="card" style="opacity:0.5"><h3><s>'+r.title+'</s></h3><div style="font-size:12px;color:var(--mute)">'+r.date+' &middot; completado '+r.done_date+'</div></div>';});}document.getElementById('view-reminders').innerHTML=h;}
function renderJournalView(){activateView('journal');document.getElementById('view-journal').innerHTML='<h1>📓 Journal</h1><p style="color:var(--mute)">Entradas del diario. Usa <code>brain.journal_write()</code> desde el agente.</p>';}
function showPage(slug){activateView('wiki');if(slug==='index')return showIndex();var p=pmap[slug];if(!p){document.getElementById('view-wiki').innerHTML='<p>Pagina no encontrada</p>';return;}var bh='';if(p.backlinks.length>0){bh='<div class="bl-section"><h3>Referenciado por ('+p.backlinks.length+')</h3>';p.backlinks.forEach(function(b){bh+='<a href="#" class="wl" onclick="showPage(\\''+b.slug+'\\')">'+b.title+'</a>';});bh+='</div>';}var body=mdToHtml(p.body);document.getElementById('view-wiki').innerHTML='<div style="font-size:12px;color:var(--mute);margin-bottom:12px"><a href="#" onclick="showPage(\\'index\\')" style="color:var(--ink)">Inicio</a> &raquo; '+p.page_type+'</div><h1>'+p.title+'</h1><div class="meta"><span>'+p.page_type+'</span>'+(p.confidence?'<span>'+p.confidence+'</span>':'')+(p.domain?'<span>'+p.domain+'</span>':'')+p.tags.map(function(t){return'<span class="tag">'+t+'</span>';}).join('')+'</div>'+body+bh;document.getElementById('view-wiki').scrollTop=0;}
function showIndex(){var h='<h1>Indice</h1><p style="color:var(--mute)">'+PAGES.length+' paginas</p>';var byType={};PAGES.forEach(function(p){var pt=p.page_type||'concept';byType[pt]=byType[pt]||[];byType[pt].push(p);});var tn={project:'Proyectos',concept:'Conceptos',entity:'Entidades',comparison:'Comparaciones',query:'Consultas',raw:'Raw'};['project','concept','entity','comparison','query','raw'].forEach(function(pt){var items=byType[pt]||[];if(!items.length)return;h+='<h2>'+tn[pt]+' ('+items.length+')</h2>';items.sort(function(a,b){return a.title.localeCompare(b.title);});items.forEach(function(p){var tH=(p.tags||[]).map(function(t){return'<span class="tag">'+t+'</span>';}).join(' ');h+='<div class="card"><a href="#" class="wl" style="font-size:15px;font-weight:600" onclick="showPage(\\''+p.slug+'\\')">'+p.title+'</a>'+(p.confidence?' <span style="font-size:11px;color:var(--mute)">['+p.confidence+']</span>':'')+(tH?' <span style="margin-left:6px">'+tH+'</span>':'')+(p.summary?'<p style="font-size:13px;color:var(--mute);margin-top:4px">'+p.summary.substring(0,150)+'</p>':'')+'</div>';});});document.getElementById('view-wiki').innerHTML=h;}
function mdToHtml(text){if(!text)return'';var lines=text.split('\\n'),out=[],ic=false,il=false,sm=pmap;function rl(tx){return tx.replace(/\\[\\[([^\\]]+)\\]\\]/g,function(_,target){var alias=target;if(target.indexOf('|')>-1){var parts=target.split('|');target=parts[0].trim();alias=parts[1].trim();}target=target.trim();alias=alias.trim();if(sm[target])return'<a href="#" class="wl" data-slug="'+target+'">'+alias+'</a>';else return'<span class="bl" title="'+target+'">'+alias+'</span>';});}lines.forEach(function(line){if(line.trim().startsWith('```')){ic=!ic;out.push(ic?'<pre><code>':'</code></pre>');return;}if(ic){out.push(line);return;}var m=line.match(/^(#{1,6})\\s+(.+)$/);if(m){if(il){out.push('</ul>');il=false;}out.push('<h'+m[1].length+'>'+rl(m[2])+'</h'+m[1].length+'>');return;}m=line.match(/^[-*]\\s+(.+)$/);if(m){if(!il){out.push('<ul>');il=true;}out.push('<li>'+rl(m[1])+'</li>');return;}if(!line.trim()){if(il){out.push('</ul>');il=false;}return;}if(il){out.push('</ul>');il=false;}out.push('<p>'+rl(line)+'</p>');});if(il)out.push('</ul>');return out.join('\\n');}
var _graphInit=false;
function renderGraph(){if(_graphInit){if(window._net)window._net.fit();return;}_graphInit=true;var GCOLORS={entity:"#4CAF50",concept:"#2196F3",comparison:"#FF9800",query:"#9C27B0",raw:"#607D8B",project:"#E91E63",goal:"#4CAF50",milestone:"#FF9800",okr:"#E91E63",todo:"#9C27B0",deliverable:"#00BCD4",reminder:"#FFC107"};var lh='';for(var k in GCOLORS){lh+='<div><span style=\"background:'+GCOLORS[k]+'\"></span> '+k+'</div>';}document.getElementById('graph-legend').innerHTML=lh;var nodes=new vis.DataSet(GRAPH.nodes.map(function(n){return{id:n.id,label:n.label,color:{background:n.color,border:'#333'},font:{color:'#333',size:11},shape:'dot',size:18};}));var edges=new vis.DataSet(GRAPH.edges.map(function(e){return{from:e.from,to:e.to,color:{color:'#ccc',opacity:0.6},arrows:{to:{enabled:true,scaleFactor:0.5}}};}));window._net=new vis.Network(document.getElementById('graph-view'),{nodes:nodes,edges:edges},{physics:{forceAtlas2Based:{gravitationalConstant:-50,centralGravity:0.01,springLength:150,springConstant:0.08},maxVelocity:50,solver:'forceAtlas2Based',timestep:0.35,stabilization:{iterations:150}},interaction:{hover:true,zoomView:true,dragView:true},edges:{smooth:{type:'continuous'}}});}
loadBrains();
setInterval(function(){if(!document.hidden)loadAll();},30000);
</script>
</body>
</html>"""

if __name__ == "__main__":
    BN, PORT = parse_args()
    print("PocketBrain Web :: http://localhost:%d (brain: %s)" % (PORT, BN))
    server = http.server.HTTPServer(("0.0.0.0", PORT), Handler)
    try: server.serve_forever()
    except KeyboardInterrupt: print("\nStopped")
