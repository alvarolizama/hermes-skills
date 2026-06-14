# Screenshots & README refresh workflow

End-to-end workflow for refreshing UI screenshots and keeping the README in sync.

## When to run

Run this after any UI change that affects:
- layout (headers, breadcrumbs, sidebar)
- graph rendering or legends
- card content / markdown rendering
- tabs, kanban, filters
- new or removed views

## 1. Delete old screenshots

```bash
rm -f ~/Workspace/repos/skills/hermes-skills/screenshots/*.png
```

Do not keep old names. Use the numbered sequence below.

## 2. Capture each view

Use `browser_navigate` + `browser_vision` to render and save the current view cache to the target path. Example list:

| # | View | URL hash |
|---|------|----------|
| 01 | Projects | `#tab=projects` |
| 02 | Project detail | `#project=pocketbrain&ptab=content` |
| 03 | Project graph | `#project=pocketbrain&ptab=graph` |
| 04 | Todo | `#tab=todos` |
| 05 | Project kanban | `#project=pocketbrain&ptab=todo` |
| 06 | Goals | `#tab=goals` |
| 07 | Reminders | `#tab=reminders` |
| 08 | Journal | `#tab=journal` |
| 09 | Wiki index | `#tab=wiki` |
| 10 | Wiki page | `#tab=wiki&page=pocketbrain&wtab=content` |
| 11 | Global graph | `#tab=graph` |
| 12 | Lint | `#tab=lint` |

Copy the `browser_vision` screenshot cache to the final path:

```bash
cp /Users/alvaro/.hermes/cache/screenshots/browser_screenshot_xxxx.png \
   ~/Workspace/repos/skills/hermes-skills/screenshots/NN-name.png
```

## 3. Keep image paths relative

Inside `pocketbrain/README.md` use `../screenshots/NN-name.png` (goes up one level from `pocketbrain/`).

Inside the root `README.md` use `screenshots/NN-name.png` directly.

## 4. Keep README concise

- No duplicated sections (architecture, hash URLs, tracing).
- No real context names as examples (no `personal`, `bravo`, etc. in docs).
- No fake domain values that are actually contexts.
- Link to `pocketbrain/README.md` from the root README.

## 5. Sync, commit, push

```bash
cd ~/Workspace/repos/skills/hermes-skills
rsync -av --delete ~/.hermes/skills/productivity/pocketbrain/ pocketbrain/
rm -f pocketbrain/scripts/web_ui.html.bak pocketbrain/scripts/reseed_personal.py
rm -rf pocketbrain/scripts/__pycache__
git add -A pocketbrain/ screenshots/
git commit --no-gpg-sign -m "docs(pocketbrain): refresh screenshots and README"
git push origin main
```

## 6. Verify

- README renders images on GitHub.
- No broken links in root or pocketbrain README.
- `node --check` passes on all modified JS.
- `python3 -m py_compile` passes on modified Python.
