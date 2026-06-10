#!/usr/bin/env python3
"""
PocketBrain Sync — Exporta contextos de PocketBase a archivos markdown locales.

Sincronización UNIDIRECCIONAL: PocketBase → archivos locales.
Solo actualiza páginas modificadas desde la última sync (incremental).
Los attachments de páginas raw se descargan al mismo directorio.

Uso:
    python3 sync.py [--context CONTEXT_NAME] [--full] [--output DIR]

    --context  Solo sync de un contexto específico (default: todos)
    --full     Forzar sync completo (ignora estado incremental)
    --output   Directorio de salida (default: ~/brain-sync)

Ejemplos:
    python3 sync.py                          # todos los contextos, incremental
    python3 sync.py --context personal       # solo el contexto 'personal'
    python3 sync.py --full --output ~/wiki   # sync completo a ~/wiki
"""

import sys, os, json, hashlib, re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
import urllib.parse

# ── Setup ──────────────────────────────────────────────────────────

sys.path.insert(0, os.path.expanduser("~/.hermes/skills/productivity/pocketbase/scripts"))

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

from pb import PB, quick_pb


    # ═════════════════════════════════════════════════════════════════════
#  SYNC ENGINE
    # ═════════════════════════════════════════════════════════════════════

class SyncEngine:
    """Exporta cerebros PocketBase → archivos markdown locales."""

    def __init__(self, output_dir: str, full: bool = False):
        self.output_dir = Path(output_dir).expanduser().resolve()
        self.full = full
        self.pb = quick_pb(env["POCKETBRAIN_HOST"], env["POCKETBRAIN_EMAIL"], env["POCKETBRAIN_PASSWORD"])
        self.state_file = self.output_dir / ".sync_state.json"
        self.state = self._load_state()
        self.stats = {"created": 0, "updated": 0, "skipped": 0, "attachments": 0}

    # ── State ──────────────────────────────────────────────────────

    def _load_state(self) -> dict:
        if self.state_file.exists():
            return json.loads(self.state_file.read_text())
        return {}

    def _save_state(self):
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state_file.write_text(json.dumps(self.state, indent=2, default=str))

    def _needs_update(self, page_id: str, updated: str) -> bool:
        if self.full:
            return True
        last_sync = self.state.get(page_id, "")
        return last_sync != updated

    def _mark_synced(self, page_id: str, updated: str):
        self.state[page_id] = updated

    # ── Frontmatter ────────────────────────────────────────────────

    def _build_frontmatter(self, page: dict, tags: list, domain_name: str = "") -> str:
        """Construye YAML frontmatter para una pagina."""
        fm = {
            "title": page.get("title", ""),
            "slug": page.get("slug", ""),
            "page_type": page.get("page_type", ""),
            "confidence": page.get("confidence", ""),
            "contested": page.get("contested", False),
            "source_url": page.get("source_url", ""),
            "source_sha256": page.get("source_sha256", ""),
            "created": page.get("created", ""),
            "updated": page.get("updated", ""),
        }
        if domain_name:
            fm["domain"] = domain_name
        if page.get("contradictions"):
            fm["contradictions"] = page["contradictions"]
        if tags:
            fm["tags"] = tags

        lines = ["---"]
        for k, v in fm.items():
            if isinstance(v, list):
                lines.append(f"{k}: [{', '.join(v)}]")
            elif isinstance(v, bool):
                lines.append(f"{k}: {str(v).lower()}")
            elif v:
                # Escape YAML special chars minimally
                val = str(v).replace('"', '\\"')
                if any(c in val for c in ':{}[]&*!|>%#@`,'):
                    lines.append(f'{k}: "{val}"')
                else:
                    lines.append(f"{k}: {val}")
        lines.append("---")
        return "\n".join(lines) + "\n\n"

    # ── Schema export ──────────────────────────────────────────────

    def _write_schema(self, brain: dict, brain_dir: Path):
        """Genera SCHEMA.md desde schema_config."""
        schema = context.get("schema_config", {}) or {}
        lines = [
            "# Wiki Schema\n",
            f"## Domain\n{brain.get('description', brain.get('name', ''))}\n",
        ]
        if schema:
            lines.append("## Conventions\n")
            for k, v in schema.get("conventions", {}).items():
                lines.append(f"- **{k}**: {v}")
            lines.append("")
            lines.append("## Tag Taxonomy\n")
            for cat, tags_list in schema.get("tag_taxonomy", {}).items():
                lines.append(f"- **{cat}**: {', '.join(tags_list)}")
            lines.append("")

        (context_dir / "SCHEMA.md").write_text("\n".join(lines))

    # ── Log export ─────────────────────────────────────────────────

    def _write_log(self, context_id: str, brain_dir: Path):
        """Genera log.md desde brain_log."""
        logs = self.pb.all("brain_log",
            filter="(brain='" + context_id + "')", perPage=200)

        lines = [
            "# Wiki Log\n",
            "> Chronological record of all actions. Auto-generated from PocketBrain.\n",
            f"> Total entries: {len(logs)} | Generated: {datetime.now(timezone.utc).isoformat()}\n",
            "",
        ]
        for entry in logs:
            created = entry.get("created", "")[:10]
            action = entry.get("action", "?")
            desc = entry.get("description", "")
            page_name = ""
            if entry.get("expand", {}).get("page"):
                page_name = f" | [[{entry['expand']['page'].get('slug', '?')}]]"
            lines.append(f"## [{created}] {action}{page_name}")
            if desc:
                lines.append(f"- {desc}")
            lines.append("")

        (context_dir / "log.md").write_text("\n".join(lines))

    # ── Journal export ──────────────────────────────────────────────

    def _write_journal(self, context_id: str, brain_dir: Path):
        """Exporta brain_journal a journal.md."""
        entries = self.pb.all("brain_journal",
            filter="(brain='" + context_id + "')",
            sort="date", perPage=500)

        if not entries:
            return

        journal_dir = context_dir / "journal"
        journal_dir.mkdir(parents=True, exist_ok=True)

        lines = [
            "# Journal",
            "",
            "> Diario personal. Auto-generado desde PocketBrain.",
            "> Total entries: " + str(len(entries)),
            "",
        ]

        for entry in entries:
            date_str = entry.get("date", "?")[:10]
            mood = entry.get("mood", "")
            mood_icon = {"great": "🟢", "meh": "🟡", "bad": "🔴"}.get(mood, "")
            body = entry.get("body", "") or ""

            lines.append("## " + date_str + " " + mood_icon)
            if body:
                lines.append(body)
            lines.append("")

        (journal_dir / "journal.md").write_text("\n".join(lines))
        print("   Journal: " + str(len(entries)) + " entries")

    # ── Todos export ────────────────────────────────────────────────

    def _write_todos(self, context_id: str, brain_dir: Path):
        """Exporta brain_todos a todos.md agrupado por status."""
        todos = self.pb.all("brain_todos",
            filter="(brain='" + context_id + "')",
            perPage=500)

        if not todos:
            return

        order = ["in progress", "today", "this week", "backlog", "done", "cancelled"]
        by_status = {s: [] for s in order}
        for t in todos:
            s = t.get("status", "backlog")
            if s not in by_status:
                by_status[s] = []
            by_status[s].append(t)

        lines = [
            "# Todos",
            "",
            "> Tareas del cerebro. Auto-generado desde PocketBrain.",
            "> Total: " + str(len(todos)),
            "",
        ]

        for status in order:
            items = by_status.get(status, [])
            if not items:
                continue
            lines.append("## " + status.capitalize())
            lines.append("")
            for t in items:
                title = t.get("title", "?")
                domain = t.get("domain", "?")
                owner = t.get("owner", "?")
                content = (t.get("content", "") or "")[:200]
                comment = t.get("comment", "") or ""
                started = (t.get("started_date", "") or "")[:10]
                completed = (t.get("completed_date", "") or "")[:10]
                cancelled = (t.get("cancelled_date", "") or "")[:10]

                meta = []
                if domain:
                    meta.append("domain: " + domain)
                if owner and owner != "alvaro":
                    meta.append("owner: " + owner)
                if started:
                    meta.append("started: " + started)
                if completed:
                    meta.append("completed: " + completed)
                if cancelled:
                    meta.append("cancelled: " + cancelled)

                lines.append("- [ ] **" + title + "**")
                if meta:
                    lines.append("  _(" + ", ".join(meta) + ")_")
                if content:
                    lines.append("  " + content)
                if comment:
                    lines.append("  > " + comment)
                lines.append("")
            lines.append("")

        (context_dir / "todos.md").write_text("\n".join(lines))
        print("   Todos: " + str(len(todos)) + " tasks")

    # ── Files export ─────────────────────────────────────────────────

    def _write_files(self, context_id: str, brain_dir: Path):
        """Descarga archivos adjuntos de brain_files."""
        files = self.pb.all("brain_files",
            filter="(brain='" + context_id + "')",
            expand="page", perPage=500)

        if not files:
            return

        import subprocess
        t = self.pb.get_token()
        os.environ["SYNC_T"] = t
        downloaded = 0
        for f_rec in files:
            filename = f_rec.get("file", "")
            if not filename:
                continue
            page_slug = ""
            page_expand = f_rec.get("expand", {}).get("page")
            if isinstance(page_expand, dict):
                page_slug = page_expand.get("slug", "")

            if page_slug:
                dest_dir = context_dir / "files" / page_slug
            else:
                dest_dir = context_dir / "files"
            dest_dir.mkdir(parents=True, exist_ok=True)

            host = self.pb.host
            url = host + "/api/files/brain_files/" + f_rec["id"] + "/" + filename
            out = str(dest_dir / filename)
            # Use shell to expand SYNC_T env var
            subprocess.run(
                "curl -s -o " + out + " " + url + " -H " + chr(34) + "Authorization: Bearer $SYNC_T" + chr(34),
                shell=True, capture_output=True, env=os.environ)
            if Path(out).exists():
                downloaded += 1
                self.stats["attachments"] += 1

        if downloaded:
            print("   Files: " + str(downloaded) + " downloaded")


    # ── Index export ───────────────────────────────────────────────

    def _write_index(self, pages: list, brain_dir: Path):
        """Genera index.md con todas las páginas agrupadas por page_type."""
        by_type = {
            "entity": [], "concept": [], "comparison": [],
            "query": [], "raw": [], "project": [],
        }
        for p in pages:
            pt = p.get("page_type", "concept")
            if pt in by_type:
                by_type[pt].append(p)

        lines = [
            "# Wiki Index\n",
            "> Content catalog. Every page listed under its type with a one-line summary.\n",
            f"> Total pages: {len(pages)} | Generated: {datetime.now(timezone.utc).isoformat()}\n",
            "",
        ]
        for section, section_pages in by_type.items():
            if not section_pages:
                continue
            lines.append(f"## {section.capitalize()}\n")
            for p in sorted(section_pages, key=lambda x: x.get("title", "")):
                slug = p.get("slug", "")
                title = p.get("title", "")
                summary = p.get("summary", "")
                confidence = p.get("confidence", "")
                conf_str = f" `[{confidence}]`" if confidence else ""
                lines.append(f"- [[{slug}]] — {title}{conf_str}")
                if summary and summary != title:
                    lines.append(f"  {summary[:120]}")
            lines.append("")

        (context_dir / "index.md").write_text("\n".join(lines))

    # ── Page export ────────────────────────────────────────────────

    def _write_page(self, page: dict, brain_dir: Path, context_name: str):
        """Escribe una página individual como archivo .md."""
        pt = page.get("page_type", "concept")
        slug = page.get("slug", "")
        body = page.get("body", "") or ""

        # Determinar directorio según page_type
        type_dirs = {
            "entity": "entities", "concept": "concepts",
            "comparison": "comparisons", "query": "queries", "raw": "raw",
            "project": "projects",
        }
        subdir = type_dirs.get(pt, "concepts")
        page_dir = brain_dir / subdir
        page_dir.mkdir(parents=True, exist_ok=True)

        # Extraer tags y domain del expand
        expand = page.get("expand", {})
        expanded_tags = expand.get("tags", [])
        tag_names = []
        if expanded_tags and isinstance(expanded_tags, list) and len(expanded_tags) > 0:
            if isinstance(expanded_tags[0], dict):
                tag_names = [t.get("name", "") for t in expanded_tags]
            else:
                tag_names = expanded_tags  # IDs crudos

        domain_name = ""
        expanded_domain = expand.get("domain")
        if isinstance(expanded_domain, dict):
            domain_name = expanded_domain.get("name", "")
        elif isinstance(expanded_domain, str) and expanded_domain:
            domain_name = expanded_domain

        # Frontmatter + body
        md_content = self._build_frontmatter(page, tag_names, domain_name) + body
        if not body.endswith("\n"):
            md_content += "\n"

        md_path = page_dir / f"{slug}.md"
        md_path.write_text(md_content)

        # Download attachment for raw pages
        attachment = page.get("attachment", "")
        if attachment and pt == "raw":
            self._download_attachment(page["id"], attachment, page_dir, slug)

    def _download_attachment(self, page_id: str, filename: str,
                             page_dir: Path, slug: str):
        """Descarga el attachment de una pagina raw."""
        import subprocess

        host = self.pb.host
        token = self.pb.get_token()
        url = host + "/api/files/brain_pages/" + page_id + "/" + filename

        ext = Path(filename).suffix or ""
        out_path = page_dir / (slug + ext)

        auth = "Authorization: Bearer %s" % token
        result = subprocess.run(
            ["curl", "-s", "-o", str(out_path), url, "-H", auth],
            capture_output=True, text=True)

        if result.returncode == 0 and out_path.exists():
            self.stats["attachments"] += 1
        else:
            print("  WARN  Failed to download attachment: " + filename)

    # ── Main sync ──────────────────────────────────────────────────

    def sync_context(self, context: dict):
        """Sincroniza un cerebro completo."""
        context_id = context["id"]
        context_name = context["name"]
        context_dir = self.output_dir / context_name

        print(f"\n🧠 Syncing context: {brain_name}")
        context_dir.mkdir(parents=True, exist_ok=True)

        # Obtener todas las páginas (no archivadas) con tags y domain expandidos
        pages = self.pb.all("brain_pages",
            filter=f"(brain='{context_id}' && archived=false)",
            expand="tags,domain",
            sort="title")

        print(f"   Pages: {len(pages)}")

        # Sync cada página
        synced_pages = []
        for page in pages:
            pid = page["id"]
            updated = page.get("updated", "")
            slug = page.get("slug", "?")

            if self._needs_update(pid, updated):
                self._write_page(page, context_dir, context_name)
                self._mark_synced(pid, updated)
                synced_pages.append(page)
                self.stats["updated"] += 1
                print(f"   ✓ {slug}")
            else:
                synced_pages.append(page)
                self.stats["skipped"] += 1

        # Escribir archivos de navegación
        self._write_schema(context, context_dir)
        self._write_index(synced_pages, context_dir)
        self._write_log(context_id, context_dir)
        self._write_journal(context_id, context_dir)
        self._write_todos(context_id, context_dir)
        self._write_files(context_id, context_dir)

        # Limpiar páginas que ya no existen en PB
        self._cleanup_stale(brain, synced_pages)

        print(f"   Schema: ✓ | Index: ✓ | Log: ✓ | Journal: ✓ | Todos: ✓ | Files: ✓")
        print(f"   Updated: {self.stats['updated']} | Skipped: {self.stats['skipped']}"
              f" | Attachments: {self.stats['attachments']}")

    def _cleanup_stale(self, brain: dict, synced_pages: list):
        """Elimina archivos .md locales de páginas que ya no existen en PB."""
        context_dir = self.output_dir / context["name"]
        if not brain_dir.exists():
            return

        active_slugs = {p["slug"] for p in synced_pages}
        type_dirs = ["entities", "concepts", "comparisons", "queries", "raw", "projects"]

        for subdir in type_dirs:
            d = context_dir / subdir
            if not d.exists():
                continue
            for md_file in d.glob("*.md"):
                slug = md_file.stem
                if slug not in active_slugs:
                    md_file.unlink()
                    print(f"   🗑️  Removed stale: {subdir}/{slug}.md")
                    # También limpiar attachment
                    for ext_file in d.glob(f"{slug}.*"):
                        if ext_file.suffix != ".md":
                            ext_file.unlink()

    def sync_all(self):
        """Sincroniza todos los cerebros."""
        brains = self.pb.all("contexts")
        print(f"Found {len(brains)} brain(s)")
        for context in contexts:
            self.sync_context(context)
        self._save_state()
        self._print_summary()

    def _print_summary(self):
        print(f"\n{'='*50}")
        print(f"Sync complete!")
        print(f"  Created/Updated: {self.stats['updated']}")
        print(f"  Skipped: {self.stats['skipped']}")
        print(f"  Attachments: {self.stats['attachments']}")
        print(f"  Output: {self.output_dir}")


    # ═════════════════════════════════════════════════════════════════════
#  CLI
    # ═════════════════════════════════════════════════════════════════════

def parse_args():
    args = sys.argv[1:]
    context_name = None
    full = False
    output = os.path.expanduser("~/brain-sync")

    i = 0
    while i < len(args):
        if args[i] == "--context" and i + 1 < len(args):
            context_name = args[i + 1]
            i += 2
        elif args[i] == "--full":
            full = True
            i += 1
        elif args[i] == "--output" and i + 1 < len(args):
            output = args[i + 1]
            i += 2
        else:
            i += 1

    return brain_name, full, output


if __name__ == "__main__":
    context_name, full, output = parse_args()

    engine = SyncEngine(output_dir=output, full=full)

    if context_name:
        contexts = engine.pb.list("contexts", filter=f"(name='{brain_name}')")
        if not contexts:
            print(f"Brain '{brain_name}' not found.")
            sys.exit(1)
        engine.sync_context(contexts[0])
        engine._save_state()
        engine._print_summary()
    else:
        engine.sync_all()
