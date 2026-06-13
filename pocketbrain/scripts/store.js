/* Centralized reactive store for PocketBrain Web.
 * Holds all shared frontend state and notifies subscribers on changes.
 */

const initialState = {
  context: 'personal',
  pages: [],
  goals: [],
  todos: [],
  deps: [],
  files: [],
  reminders: [],
  journal: [],
  graph: { nodes: [], edges: [] },
  logs: [],

  loading: false,
  offline: false,
  error: null,

  filters: {
    page: '',
    goal: '',
    todo: '',
    reminder: '',
    file: '',
    dep: '',
    journal: ''
  }
};

const Store = {
  state: { ...initialState },
  listeners: [],

  subscribe(fn) {
    if (typeof fn !== 'function') {
      throw new TypeError('Store.subscribe expects a function');
    }
    this.listeners.push(fn);
    // Return unsubscribe callback.
    return () => {
      this.listeners = this.listeners.filter(listener => listener !== fn);
    };
  },

  notify() {
    // Iterate over a snapshot in case a listener unsubscribes during notify.
    this.listeners.slice().forEach(fn => fn(this.state));
  },

  set(key, value) {
    if (key && typeof key === 'object') {
      Object.assign(this.state, key);
    } else if (typeof key === 'string' || typeof key === 'symbol') {
      this.state[key] = value;
    } else {
      throw new TypeError('Store.set expects an object or a key string');
    }
    this.notify();
  },

  get(key) {
    if (key === undefined) return this.state;
    return this.state[key];
  },

  mapPages() {
    const map = {};
    for (const page of this.state.pages) {
      if (page && page.slug) {
        map[page.slug] = page;
      }
    }
    return map;
  },

  setLoading(value) {
    this.set('loading', Boolean(value));
  },

  setOffline(value) {
    this.set('offline', Boolean(value));
  },

  setError(value) {
    this.set('error', value);
  },

  setFilter(view, value) {
    if (!Object.prototype.hasOwnProperty.call(this.state.filters, view)) {
      throw new Error(`Unknown filter view: ${view}`);
    }
    this.state.filters = { ...this.state.filters, [view]: String(value ?? '') };
    this.notify();
  },

  resetFilters() {
    this.state.filters = { ...initialState.filters };
    this.notify();
  },

  reset() {
    this.state = { ...initialState };
    this.notify();
  }
};

export default Store;
