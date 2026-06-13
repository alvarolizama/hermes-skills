/**
 * Lightweight Markdown renderer for PocketBrain Web.
 *
 * Supports:
 * - Headings (# to ######)
 * - Bold, italic, bold-italic
 * - Links [text](url)
 * - Wiki links [[slug]] or [[slug|alias]]
 * - Reference links ^[slug]
 * - Unordered and ordered lists
 * - Code fences with optional language
 * - Tables (GitHub-flavored)
 * - Horizontal rules
 * - Blockquotes (single and nested levels)
 *
 * All plain text and code block content is HTML-escaped.
 *
 * @param {string} text
 * @param {Object} [pmap={}] - slug -> page map for resolving wiki links and references.
 * @returns {string}
 */
export function mdToHtml(text, pmap = {}) {
  if (!text) return '';

  const lines = text.split('\n');
  const out = [];
  let inCode = false;
  let lang = '';
  let ul = false;
  let ol = false;

  function closeLists() {
    if (ul) {
      out.push('</ul>');
      ul = false;
    }
    if (ol) {
      out.push('</ol>');
      ol = false;
    }
  }

  function esc(s) {
    return String(s)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  function resolveSlug(name) {
    return Object.keys(pmap).find(k => k.toLowerCase() === name.toLowerCase()) || null;
  }

  function inline(tx) {
    // Code spans first so their contents are not transformed.
    tx = tx.replace(/`([^`]+)`/g, (_, code) => `<code>${esc(code)}</code>`);

    // Bold + italic.
    tx = tx.replace(/\*\*\*(.+?)\*\*\*/g, '<strong><em>$1</em></strong>');
    tx = tx.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    tx = tx.replace(/\*(?!\*)(.+?)\*/g, '<em>$1</em>');

    // External links.
    tx = tx.replace(/\[([^\]]+)\]\(([^)]+)\)/g, (_, label, url) => {
      return `<a href="${esc(url)}" target="_blank" rel="noopener noreferrer" class="external-link">${esc(label)}</a>`;
    });

    // Wiki links.
    tx = tx.replace(/\[\[([^\]]+)\]\]/g, (_, target) => {
      let alias = target;
      if (target.includes('|')) {
        [target, alias] = target.split('|').map(s => s.trim());
      }
      const resolved = resolveSlug(target) || resolveSlug(target.toLowerCase());
      const slugArg = JSON.stringify(resolved || target).replace(/"/g, '&quot;');
      const safeAlias = esc(alias);
      if (resolved) {
        return `<a href="javascript:void(0)" class="wl" data-slug="${esc(resolved)}" onclick="window.showPage(${slugArg});return false;">${safeAlias}</a>`;
      }
      return `<span class="bl" title="${esc(target)}">${safeAlias}</span>`;
    });

    // Reference links ^[slug].
    tx = tx.replace(/\^\[([^\]]+)\]/g, (_, slug) => {
      const resolved = resolveSlug(slug);
      const slugArg = JSON.stringify(resolved || slug).replace(/"/g, '&quot;');
      const label = esc(slug);
      if (resolved) {
        return `<sup><a href="javascript:void(0)" class="ref" onclick="window.showPage(${slugArg});return false;">${label}</a></sup>`;
      }
      return `<sup class="bl" title="${esc(slug)}">${label}</sup>`;
    });

    return tx;
  }

  function flushParagraph(buf) {
    if (!buf.length) return;
    const joined = buf.join(' ').replace(/\s+/g, ' ').trim();
    if (joined) out.push(`<p>${inline(esc(joined))}</p>`);
    buf.length = 0;
  }

  function renderBlockquote(startIdx) {
    const rows = [];
    let i = startIdx;
    while (i < lines.length) {
      const raw = lines[i];
      if (!raw.startsWith('>')) break;
      let depth = 0;
      let idx = 0;
      while (idx < raw.length) {
        if (raw[idx] === '>') {
          depth++;
          idx++;
          if (raw[idx] === ' ') idx++;
        } else {
          break;
        }
      }
      if (depth === 0) break;
      rows.push({ depth, content: raw.slice(idx) });
      i++;
    }

    let html = '';
    let depth = 0;
    for (const row of rows) {
      while (depth < row.depth) {
        html += '<blockquote>';
        depth++;
      }
      while (depth > row.depth) {
        html += '</blockquote>';
        depth--;
      }
      html += inline(row.content) + ' ';
    }
    while (depth > 0) {
      html += '</blockquote>';
      depth--;
    }
    out.push(html.trimEnd());
    return i - 1;
  }

  function renderTable(startIdx) {
    const rows = [lines[startIdx]];
    let i = startIdx;
    while (i + 1 < lines.length && lines[i + 1].trim().startsWith('|')) {
      i++;
      rows.push(lines[i]);
    }

    const cells = r => r.split('|').slice(1, -1).map(c => c.trim());
    if (rows.length < 2) {
      out.push(esc(lines[startIdx]));
      return i;
    }

    const header = cells(rows[0]);
    const body = rows.slice(2).filter(r => !/^\|[-\s|]*\|$/.test(r.trim()));

    let h = '<table style="border-collapse:collapse;width:100%;margin:12px 0">';
    h += '<thead><tr>' +
      header.map(c => `<th style="border:1px solid var(--hairline);padding:6px 12px;text-align:left">${inline(esc(c))}</th>`).join('') +
      '</tr></thead>';
    h += '<tbody>' +
      body.map(r => `<tr>${cells(r).map(c => `<td style="border:1px solid var(--hairline);padding:6px 12px">${inline(esc(c))}</td>`).join('')}</tr>`).join('') +
      '</tbody>';
    h += '</table>';
    out.push(h);
    return i;
  }

  let paraBuf = [];

  for (let i = 0; i < lines.length; i++) {
    const raw = lines[i];
    const tl = raw.trim();
    const codeMatch = tl.match(/^```(\w*)/);

    if (codeMatch) {
      flushParagraph(paraBuf);
      if (!inCode) {
        closeLists();
        inCode = true;
        lang = codeMatch[1];
        out.push(`<pre><code${lang ? ` class="language-${esc(lang)}"` : ''}>`);
      } else {
        out.push('</code></pre>');
        inCode = false;
        lang = '';
      }
      continue;
    }

    if (inCode) {
      out.push(esc(raw));
      continue;
    }

    if (!tl) {
      flushParagraph(paraBuf);
      closeLists();
      out.push('');
      continue;
    }

    if (tl.startsWith('|')) {
      flushParagraph(paraBuf);
      closeLists();
      i = renderTable(i);
      continue;
    }

    if (tl === '---' || tl === '***' || tl === '___') {
      flushParagraph(paraBuf);
      closeLists();
      out.push('<hr>');
      continue;
    }

    const ulMatch = tl.match(/^[-\*]\s+(.+)$/);
    if (ulMatch) {
      flushParagraph(paraBuf);
      if (ol) closeLists();
      if (!ul) {
        out.push('<ul>');
        ul = true;
      }
      out.push(`<li>${inline(esc(ulMatch[1]))}</li>`);
      continue;
    }

    const olMatch = tl.match(/^\d+\.\s+(.+)$/);
    if (olMatch) {
      flushParagraph(paraBuf);
      if (ul) closeLists();
      if (!ol) {
        out.push('<ol>');
        ol = true;
      }
      out.push(`<li>${inline(esc(olMatch[1]))}</li>`);
      continue;
    }

    const hMatch = raw.match(/^(#{1,6})\s+(.+)$/);
    if (hMatch) {
      flushParagraph(paraBuf);
      closeLists();
      const level = hMatch[1].length;
      out.push(`<h${level}>${inline(esc(hMatch[2]))}</h${level}>`);
      continue;
    }

    if (raw.startsWith('>')) {
      flushParagraph(paraBuf);
      closeLists();
      i = renderBlockquote(i);
      continue;
    }

    paraBuf.push(raw);
  }

  flushParagraph(paraBuf);
  closeLists();
  return out.join('\n');
}

export default mdToHtml;
export function bindMarkdownLinks(root) {
  if (!root) return;
  root.querySelectorAll('a.wl').forEach(a => {
    a.addEventListener('click', e => {
      e.preventDefault();
      const slug = a.dataset.slug;
      if (slug && typeof window.showPage === 'function') window.showPage(slug);
    });
  });
}
