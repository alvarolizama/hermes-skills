/**
 * Hash-based router for the PocketBrain SPA shell.
 *
 * Exports:
 *   - getHashParams()   -> parse the current location.hash into an object.
 *   - setHashParams(p)  -> replace the hash with encoded key=value pairs.
 *   - restoreFromHash() -> convenience alias for Router.resolve().
 *   - Router            -> { register, go, resolve }
 */

export function getHashParams() {
  const hash = location.hash || '';
  if (!hash || hash === '#') return {};
  const params = {};
  hash.slice(1).split('&').forEach(part => {
    const [k, v] = part.split('=');
    if (k) params[k] = v !== undefined ? decodeURIComponent(v) : '';
  });
  return params;
}

export function setHashParams(params) {
  const parts = [];
  for (const key in params) {
    if (Object.prototype.hasOwnProperty.call(params, key)) {
      const value = params[key];
      if (value !== null && value !== undefined && value !== '') {
        parts.push(`${key}=${encodeURIComponent(value)}`);
      }
    }
  }
  history.replaceState(null, '', '#' + parts.join('&'));
}

export function restoreFromHash() {
  Router.resolve();
}

export const Router = {
  routes: {},

  register(name, handler) {
    if (typeof handler !== 'function') {
      throw new TypeError('Router.register expects a function handler');
    }
    this.routes[name] = handler;
  },

  go(name, params = {}) {
    const current = getHashParams();
    setHashParams({ ...current, ...params });
    this.resolve();
  },

  resolve() {
    const params = getHashParams();
    if (params.project && this.routes.project) {
      this.routes.project(params.project, params.ptab || 'content');
    } else if (params.page && this.routes.page) {
      this.routes.page(params.page);
    } else if (params.tab && this.routes.tab) {
      this.routes.tab(params.tab);
    } else if (this.routes.default) {
      this.routes.default();
    }
  }
};

export default Router;
