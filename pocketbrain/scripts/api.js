/* Centralized API module for PocketBrain Web.
 * All requests automatically include the active `context` query param.
 */
const API = {
  ctx: 'personal',

  setContext(name) {
    this.ctx = name || 'personal';
  },

  async request(method, path, body = null) {
    const sep = path.includes('?') ? '&' : '?';
    const url = `/api${path}${sep}context=${encodeURIComponent(this.ctx)}`;
    const opts = {
      method,
      headers: {}
    };
    if (body !== null && body !== undefined) {
      opts.headers['Content-Type'] = 'application/json';
      opts.body = JSON.stringify(body);
    }
    const res = await fetch(url, opts);
    if (!res.ok) {
      const text = await res.text().catch(() => '');
      throw new Error(`${method} ${path} -> ${res.status}: ${text}`);
    }
    // Some endpoints may return 204 No Content; guard against empty body.
    const text = await res.text();
    return text ? JSON.parse(text) : null;
  },

  get(path) {
    return this.request('GET', path);
  },

  post(path, body) {
    return this.request('POST', path, body);
  },

  patch(path, body) {
    return this.request('PATCH', path, body);
  },

  del(path) {
    return this.request('DELETE', path);
  },

  loadAll() {
    return Promise.all([
      this.get('/pages'),
      this.get('/goals'),
      this.get('/todos'),
      this.get('/deps'),
      this.get('/files'),
      this.get('/reminders'),
      this.get('/journal'),
      this.get('/graph'),
      this.get('/logs')
    ]);
  }
};

export default API;
