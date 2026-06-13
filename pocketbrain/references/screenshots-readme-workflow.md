# Screenshots + README refresh workflow

Use this when the user asks to refresh screenshots and update the README after UI changes.

## 1. Prepare

- Ensure `brain_web.py` is running for the desired context:
  ```bash
  cd ~/.hermes/skills/productivity/pocketbrain/scripts
  python3 brain_web.py --context personal --port 8899
  ```
- Delete old screenshots from the repo's `screenshots/` directory (shared across all skills, root-level).
  ```bash
  rm -f /Users/alvaro/Workspace/repos/personal/hermes-skills/screenshots/*.png
  ```

## 2. Capture all views

Use `browser_vision` for each view. The tool returns a `screenshot_path` under `~/.hermes/cache/screenshots/`; copy that specific file to the repo's `screenshots/` folder with the numbered name. Do not pass a target path to `browser_vision` — it does not honor arbitrary save paths.

Recommended set (12 screenshots):

| # | View | Hash |
|---|------|------|
| 01 | Projects list | `#tab=projects` |
| 02 | Project detail | `#project=pocketbrain&ptab=content` |
| 03 | Project graph | `#project=pocketbrain&ptab=graph` |
| 04 | Global Todo kanban | `#tab=todos` |
| 05 | Project kanban | `#project=pocketbrain&ptab=todo` |
| 06 | Goals | `#tab=goals` |
| 07 | Reminders | `#tab=reminders` |
| 08 | Journal | `#tab=journal` |
| 09 | Wiki index | `#tab=wiki` |
| 10 | Wiki page | `#tab=wiki&page=pocketbrain&wtab=content` |
| 11 | Global graph | `#tab=graph` |
| 12 | Lint | `#tab=lint` |

Example copy after each `browser_vision` call:
```bash
# browser_vision returns screenshot_path in ~/.hermes/cache/screenshots/
# Copy the specific file it returned, not a wildcard.
cp /Users/alvaro/.hermes/cache/screenshots/browser_screenshot_xxxxxxxxxxxxxxxx.png \
   /Users/alvaro/Workspace/repos/personal/hermes-skills/screenshots/01-projects.png
```

## 3. Update README.md

- Open `pocketbrain/README.md`.
- Replace every screenshot reference with the new numbered paths. Because the README is inside the `pocketbrain/` directory, image paths must go up one level: `../screenshots/NN-name.png`. A plain `screenshots/NN-name.png` renders locally but breaks on GitHub.
- Add or update captions to describe the current UI accurately.
- Update the `Features` section with anything new shown in the screenshots (e.g., project graph, mobile layout, Heroicons, legend capitalization).
- Keep the README concise. Remove duplicated sections (dependency, architecture, hash URLs, tracing) that are covered by SKILL.md or references.
- Also simplify the root `README.md` so it only lists skills and links to `pocketbrain/README.md`. Do not duplicate pocketbrain content or embed broken `assets/screenshot-*.png` paths.

## 4. Validate before commit

```bash
cd ~/.hermes/skills/productivity/pocketbrain/scripts
python3 -m py_compile brain.py brain_web.py
node --check app.js router.js store.js api.js markdown.js components/Tabs.js components/Icon.js \
  views/projects.js views/todos.js views/reminders.js views/journal.js views/files.js \
  views/type.js views/goals.js views/wiki.js views/graph.js views/lint.js \
  views/milestones.js views/project-detail.js
```

## 5. Sync, commit, push

```bash
cd /Users/alvaro/Workspace/repos/personal/hermes-skills
rsync -av --delete ~/.hermes/skills/productivity/pocketbrain/ pocketbrain/
rm -f pocketbrain/scripts/web_ui.html.bak pocketbrain/scripts/reseed_personal.py
rm -rf pocketbrain/scripts/__pycache__
git add -A pocketbrain/ screenshots/
git commit --no-gpg-sign -m "docs(pocketbrain): refresh screenshots and README"
git push origin main
```

## Pitfalls

- **Image paths are relative to the README file.** `pocketbrain/README.md` must use `../screenshots/NN-name.png`; a plain `screenshots/NN-name.png` works when opened in an editor but fails on GitHub because the repo root is `screenshots/`.
- **Root README must link, not duplicate.** The top-level `README.md` should contain only a skills table that links to `pocketbrain/README.md`. Do not embed pocketbrain screenshots or duplicate feature lists there.
- **Do not use `/assets/screenshot-*.png` paths.** Screenshots live in the root `screenshots/` directory shared across all skills.
- **Don't forget to delete old PNGs** before copying new ones, or stale files remain in the repo.
- **Browser cache**: add `?nocache=N` to each hash URL so the served JS/CSS reflects the latest changes.
- **Verify legend capitalization** in the global graph screenshot: every legend label should start with an uppercase letter. If not, fix `views/graph.js` before capturing.
- **Verify mobile layout separately**: resize the viewport to 375-768 px and check `#tab=milestones` (or any view with H1 + breadcrumb + select) to confirm title/breadcrumb/select stack vertically.
