/*
 * Capa de datos del Monitor PEI y TIN para hosting propio.
 * Reemplaza el runtime del tablero de Claude con la misma interfaz que usa la página:
 *   dash.calc(id, {inputs, fn})  registra un cálculo derivado de otros datos
 *   dash.data(id)                devuelve {status: 'loading' | 'ok' | 'error', data}
 *   dash.onData(fn)              llama fn cada vez que llega o cambia un dato
 *   dash.setLink(id)             actualiza el ancla de la URL
 * Los datos se leen de data/<id>.json. Para cambiar la ruta, define window.DASH_DATA_URL
 * antes de cargar este archivo (por ejemplo, la URL de un bucket o de un API propio).
 */
(function () {
  var DATASETS = ['precios', 'indicadores', 'eventos', 'composicion', 'activos', 'finanzas', 'deuda', 'reportes'];
  var BASE = window.DASH_DATA_URL || 'data/';
  var raw = {};      // id -> {status, data}
  var calcs = {};    // id -> {inputs, fn}
  var cache = {};    // id -> {status, data}
  var listeners = [];
  var pending = false;

  function notify() {
    if (pending) return;
    pending = true;
    setTimeout(function () {
      pending = false;
      cache = {};
      listeners.slice().forEach(function (fn) {
        try { fn(); } catch (e) { console.error(e); }
      });
    }, 0);
  }

  function data(id) {
    if (raw[id]) return raw[id];
    var c = calcs[id];
    if (!c) return { status: 'loading', data: [] };
    if (cache[id]) return cache[id];
    var ins = c.inputs.map(data);
    if (ins.some(function (x) { return x.status === 'error'; })) return (cache[id] = { status: 'error', data: [] });
    if (ins.some(function (x) { return x.status !== 'ok'; })) return { status: 'loading', data: [] };
    try {
      cache[id] = { status: 'ok', data: c.fn.apply(null, ins.map(function (x) { return x.data; })) };
    } catch (e) {
      console.error('Cálculo ' + id + ': ' + e.message);
      cache[id] = { status: 'error', data: [] };
    }
    return cache[id];
  }

  window.dash = {
    calc: function (id, o) { calcs[id] = o; notify(); },
    data: data,
    onData: function (fn) { listeners.push(fn); notify(); },
    setLink: function (id) { try { history.replaceState(null, '', '#' + id); } catch (e) { /* sin ancla */ } },
    colors: [],
  };

  DATASETS.forEach(function (id) {
    raw[id] = { status: 'loading', data: [] };
    fetch(BASE + id + '.json', { cache: 'no-cache' })
      .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
      .then(function (d) { raw[id] = { status: 'ok', data: Array.isArray(d) ? d : (d.rows || []) }; })
      .catch(function (e) { console.error('No se pudo cargar ' + id + ': ' + e.message); raw[id] = { status: 'error', data: [] }; })
      .then(notify);
  });
})();
