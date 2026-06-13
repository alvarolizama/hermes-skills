/**
 * Reusable Tabs component for PocketBrain Web.
 *
 * Generates a `.project-tabs` container with anchor tags. Tabs communicate
 * through data attributes and a delegated click handler — no inline `onclick`
 * strings are emitted.
 *
 * Usage:
 *   import { Tabs, bindTabs, renderTabs } from './components/Tabs.js';
 *
 *   const html = Tabs({
 *     items: [{id:'all', label:'All'}, {id:'active', label:'Active'}],
 *     active: 'all',
 *     counts: {all: 12, active: 3}
 *   });
 *
 *   container.innerHTML = html;
 *   bindTabs(container, id => console.log('selected', id));
 *
 * Or simply:
 *   renderTabs(container, { items, active, counts }, id => { ... });
 */

const ESCAPE_MAP = {
  '&': '&amp;',
  '<': '&lt;',
  '>': '&gt;',
  '"': '&quot;',
  "'": '&#39;'
};

function escapeHtml(str) {
  return String(str).replace(/[&<>"']/g, ch => ESCAPE_MAP[ch]);
}

function escapeAttr(str) {
  return escapeHtml(str);
}

/**
 * Render tabs markup.
 *
 * @param {Object} props
 * @param {{id:string,label:string}[]} props.items
 * @param {string} props.active
 * @param {Record<string,number>} [props.counts={}]
 * @returns {string}
 */
export function Tabs({ items, active, counts = {} }) {
  if (!Array.isArray(items)) {
    throw new TypeError('Tabs expects an array of items');
  }

  const tabs = items.map(it => {
    const id = String(it.id ?? '');
    const label = String(it.label ?? '');
    const count = counts[id];
    const display = count !== undefined ? `${label} (${count})` : label;
    const cls = id === active ? 'active' : '';

    return `<a href="javascript:void(0)" class="${escapeAttr(cls)}" data-tab-id="${escapeAttr(id)}">${escapeHtml(display)}</a>`;
  }).join('');

  return `<div class="project-tabs">${tabs}</div>`;
}

/**
 * Attach a delegated click listener to a container holding tabs.
 *
 * @param {Element} root - Container with `.project-tabs` children.
 * @param {(id:string) => void} [onChange]
 */
export function bindTabs(root, onChange) {
  if (typeof root === 'string') {
    root = document.querySelector(root);
  }
  if (!(root instanceof Element)) {
    throw new TypeError('bindTabs expects a DOM element');
  }

  root.addEventListener('click', event => {
    const link = event.target.closest('a[data-tab-id]');
    if (!link) return;

    event.preventDefault();
    const id = link.dataset.tabId;

    // Update active state dynamically without re-rendering the whole view.
    root.querySelectorAll('a[data-tab-id]').forEach(a => {
      a.classList.toggle('active', a.dataset.tabId === id);
    });

    onChange?.(id);
    root.dispatchEvent(new CustomEvent('tab-change', { detail: id, bubbles: true }));
  });
}

/**
 * Render tabs into a container and bind their click behaviour.
 *
 * @param {Element} container
 * @param {Object} props
 * @param {(id:string) => void} [onChange]
 */
export function renderTabs(container, props, onChange) {
  if (typeof container === 'string') {
    container = document.querySelector(container);
  }
  if (!(container instanceof Element)) {
    throw new TypeError('renderTabs expects a DOM element');
  }
  container.innerHTML = Tabs(props);
  bindTabs(container, onChange);
}

export default Tabs;
