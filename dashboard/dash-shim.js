/*
 * dash-shim.js — a small stand-in for the Claude "Dashboard" runtime, so the
 * original page (index.original.html) runs in any browser with no Claude account.
 *
 * It provides only the parts of the `dash` API the PSX page uses:
 *   dash.data(id)          -> {status, data, columns, meta, refreshing, message}
 *   dash.draw(name, fn)    -> registers fn and runs it on every visible [data-draw=name]
 *   dash.draw(name)        -> re-runs that drawing (after a sort, a filter, a tab switch)
 *   dash.onData(fn)        -> runs fn once data is ready (data is static here)
 *   dash.colors            -> 8 series colours
 *   dash.setLink(name)     -> sets location.hash
 *   dash.params / setParams / resetParams / refresh / calc / loader -> simple versions
 *
 * Data comes from window.PSX_DATA = {stocks:[...], strategies:[...], ...}
 * which data.js sets (build_standalone.py writes data.js from data/current/*.json).
 */
(function () {
  'use strict';
  const DATA = window.PSX_DATA || {};
  const drawings = new Map();      // name -> fn | {mount, update, unmount}
  const mounted = new WeakMap();   // el -> what mount() returned
  const onDataFns = [];
  let started = false;
  let params = {};
  const calcs = {};

  const isVisible = (el) => el.isConnected && !el.closest('[hidden]');

  function data(id) {
    if (calcs[id]) {
      try {
        const rows = calcs[id].inputs.map((i) => data(i).data);
        const out = calcs[id].fn(...rows);
        return { status: 'ok', data: out, rows: out, columns: Array.isArray(out) && out[0] ? Object.keys(out[0]) : [], meta: [], refreshing: false };
      } catch (e) {
        return { status: 'error', data: [], rows: [], columns: [], meta: [], refreshing: false, message: String(e) };
      }
    }
    if (!(id in DATA)) return { status: 'missing', data: [], rows: [], columns: [], meta: [], refreshing: false, message: 'No dataset "' + id + '" in data.js' };
    const d = DATA[id];
    const columns = Array.isArray(d) && d.length ? Object.keys(d[0]) : [];
    return { status: 'ok', data: d, rows: d, columns, meta: [], refreshing: false, value: d };
  }

  function runOne(name, el) {
    const fn = drawings.get(name);
    if (!fn) return;
    try {
      if (typeof fn === 'function') {
        fn(el);
      } else {
        if (!mounted.has(el)) { el.replaceChildren(); mounted.set(el, fn.mount ? fn.mount(el) : undefined); }
        if (fn.update) fn.update(el, mounted.get(el));
      }
      el.removeAttribute('data-dash-source-state');
    } catch (e) {
      console.error('[dash-shim] drawing "' + name + '" threw:', e);
    }
  }

  function runDrawing(name) {
    document.querySelectorAll('[data-draw="' + CSS.escape(name) + '"]').forEach((el) => { if (isVisible(el)) runOne(name, el); });
  }

  function runAll() {
    onDataFns.forEach((fn) => { try { fn(); } catch (e) { console.error('[dash-shim] onData threw:', e); } });
    for (const name of drawings.keys()) runDrawing(name);
  }

  function draw(name, fn) {
    if (fn !== undefined) {
      drawings.set(name, fn);
      if (started) runDrawing(name);
    } else if (started) {
      runDrawing(name);
    }
  }

  const colors = ['#2563eb', '#d97706', '#059669', '#db2777', '#7c3aed', '#0891b2', '#65a30d', '#dc2626'];

  window.dash = {
    data,
    draw,
    colors,
    onData(fn) { onDataFns.push(fn); if (started) fn(); },
    setLink(name) { try { history.replaceState(null, '', '#' + name); } catch (e) { /* file:// may refuse */ } },
    params() { return { ...params }; },
    setParams(p) { params = { ...params, ...p }; Object.keys(params).forEach((k) => params[k] == null && delete params[k]); if (started) runAll(); },
    resetParams() { params = {}; if (started) runAll(); },
    refresh() { /* static data: nothing to refresh; re-run build_standalone.py after a pipeline run */ },
    calc(id, spec) { calcs[id] = spec; },
    loader() { /* only used for live connector queries, which this export does not have */ },
  };

  // Called once, after all of the page's scripts have run.
  window.DASH_SHIM_START = function () {
    started = true;
    runAll();
    // Re-run drawings that become visible when a tab's `hidden` attribute is removed.
    const root = document.getElementById('dash-root') || document.body;
    new MutationObserver((muts) => {
      const shown = muts.some((m) => m.type === 'attributes' && m.attributeName === 'hidden' && !m.target.hasAttribute('hidden'));
      if (shown) for (const name of drawings.keys()) runDrawing(name);
    }).observe(root, { subtree: true, attributes: true, attributeFilter: ['hidden'] });
    // Re-run on width change (charts are sized from clientWidth).
    let t = null, lastW = window.innerWidth;
    window.addEventListener('resize', () => {
      if (window.innerWidth === lastW) return;
      lastW = window.innerWidth;
      clearTimeout(t); t = setTimeout(() => { for (const name of drawings.keys()) runDrawing(name); }, 150);
    });
  };
})();
