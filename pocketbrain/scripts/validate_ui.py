#!/usr/bin/env python3
"""Validador automático para web_ui.html — corre antes de deploy.

Verifica node --check y auto-fixea el patrón de comillas simples chocando en JS inline.
Uso:
    python3 scripts/validate_ui.py

Requiere: node.js instalado (para --check)
"""
import re, subprocess, sys
from pathlib import Path

HTML = Path(__file__).with_name("web_ui.html")


def extract_js(text: str) -> str:
    parts = re.split(r'<script>', text)
    if len(parts) < 2:
        return ""
    return re.split(r'</script>', parts[1])[0]


def fix_js_quotes(text: str) -> str:
    """Escapa comillas simples dentro de strings JS que generan HTML."""
    # 1. setXxxStatus('...') -> setXxxStatus(\'...\')
    text, c1 = re.subn(
        r"(set[A-Za-z]+Status)\(('[^']+)'\)",
        lambda m: m.group(1) + "(\\'" + m.group(2)[1:-1] + "\\')",
        text
    )
    # 2. _var='value'; -> _var=\'value\';
    text, c2 = re.subn(
        r"(;\w+=)('[^']+');",
        lambda m: m.group(1) + "\\'" + m.group(2)[1:-1] + "\\';",
        text
    )
    return text, c1 + c2


def node_check(js: str) -> tuple:
    tmp = Path("/tmp/pb_check.js")
    tmp.write_text(js, encoding="utf-8")
    res = subprocess.run(["node", "--check", str(tmp)], capture_output=True, text=True)
    return res.returncode == 0, res.stderr


def verify_css(text: str) -> tuple:
    """Verifica que #main>div tenga display:none"""
    m = re.search(r'#main>\s*div\s*\{([^}]*)\}', text, re.DOTALL)
    if not m:
        return False, "No se encontró #main>div CSS"
    css = m.group(1)
    if 'display:none' not in css:
        return False, f"#main>div NO tiene display:none: {css[:120]}..."
    return True, "OK"


def main():
    if not HTML.exists():
        print(f"ERROR: {HTML} no existe")
        sys.exit(1)
    raw = HTML.read_text(encoding="utf-8")
    js = extract_js(raw)
    if not js:
        print("ERROR: No se encontró <script> en web_ui.html")
        sys.exit(1)

    ok, err = node_check(js)
    if not ok:
        print(f"node --check FALLÓ: {err[:300]}")
        print("Auto-fixeando escapado de comillas...")
        fixed_js, count = fix_js_quotes(js)
        if count:
            print(f"  -> {count} reemplazos realizados")
            # Insertar de vuelta al HTML
            raw = re.sub(
                r'(<script>).*?(</script>)',
                lambda m: m.group(1) + '\n' + fixed_js + '\n\n' + m.group(2),
                raw,
                count=1,
                flags=re.DOTALL
            )
            HTML.write_text(raw, encoding="utf-8")
            ok, err = node_check(fixed_js)
            if not ok:
                print(f"  -> Aún falla después de auto-fix: {err[:300]}")
                print("Manual review needed. Abort.")
                sys.exit(1)
            print(f"  -> node --check OK después de auto-fix")
        else:
            print("  -> No se pudo auto-fix. Error:")
            print(err)
            sys.exit(1)

    css_ok, css_msg = verify_css(raw)
    if not css_ok:
        print(f"CSS ERROR: {css_msg}")
        sys.exit(1)
    print("OK: node --check + CSS display:none verificados")


if __name__ == "__main__":
    main()
