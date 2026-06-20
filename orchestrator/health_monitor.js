/**
 * health_monitor.js — Polls /v1/health on every registered SRN app every 60s
 */
const registry = require('./registry');

const _status  = {};
const INTERVAL = 60 * 1000;

async function pingApp(app) {
    try {
        const res  = await fetch(app.health, { signal: AbortSignal.timeout(4000) });
        const json = await res.json().catch(() => ({}));
        _status[app.name] = res.ok ? 'ok' : 'degraded';
        return { app: app.name, status: _status[app.name], data: json };
    } catch (err) {
        _status[app.name] = 'down';
        console.warn(`[SRN Health] ${app.name} DOWN — ${err.message}`);
        return { app: app.name, status: 'down', error: err.message };
    }
}

async function pingAll() {
    const results = await Promise.all(registry.getApps().map(pingApp));
    const down    = results.filter(r => r.status !== 'ok');
    if (down.length) console.warn(`[SRN Health] ${down.length} unhealthy:`, down.map(d => d.app).join(', '));
    return results;
}

function getStatus()     { return { ..._status }; }
function startMonitor()  {
    pingAll();
    setInterval(pingAll, INTERVAL);
    console.log('[SRN Health] Monitor started — pinging every 60s');
}

module.exports = { startMonitor, pingAll, pingApp, getStatus };
