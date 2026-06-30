// ============================================
// status.js — System Health Panel
// Opens as a floating modal; auto-refreshes every 15 s.
// Follows the open() / close() / isOpen() interface used by every other
// tool modal so Escape, modalManager, and the /status deep-link all work
// without extra wiring in app.js.
// ============================================

const MODAL_ID = 'status-modal';
const REFRESH_MS = 15_000;

let _refreshTimer = null;

// ── Helpers ──────────────────────────────────────────────────────────────────

function _el(id) { return document.getElementById(id); }

function _badge(ok, text) {
  const span = document.createElement('span');
  span.className = 'status-badge ' + (ok ? 'status-ok' : 'status-err');
  span.textContent = text;
  return span;
}

function _card(title, rows) {
  // rows: [{label, value, ok}]
  const card = document.createElement('div');
  card.className = 'status-card';
  const h = document.createElement('h3');
  h.className = 'status-card-title';
  h.textContent = title;
  card.appendChild(h);
  for (const row of rows) {
    const div = document.createElement('div');
    div.className = 'status-row';
    const lbl = document.createElement('span');
    lbl.className = 'status-row-label';
    lbl.textContent = row.label;
    div.appendChild(lbl);
    if (typeof row.ok === 'boolean') {
      div.appendChild(_badge(row.ok, row.value));
    } else {
      const val = document.createElement('span');
      val.className = 'status-row-value';
      val.textContent = row.value;
      div.appendChild(val);
    }
    card.appendChild(div);
  }
  return card;
}

function _fmt(isoTs) {
  if (!isoTs) return '—';
  try {
    return new Date(isoTs).toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  } catch (_) { return isoTs; }
}

// ── Data fetch + render ───────────────────────────────────────────────────────

async function _fetchAll() {
  const [health, ready, version, runtime] = await Promise.allSettled([
    fetch('/api/health').then(r => r.json()),
    fetch('/api/ready').then(r => r.json()),
    fetch('/api/version').then(r => r.json()),
    fetch('/api/runtime').then(r => r.json()),
  ]);
  return {
    health:  health.status  === 'fulfilled' ? health.value  : null,
    ready:   ready.status   === 'fulfilled' ? ready.value   : null,
    version: version.status === 'fulfilled'