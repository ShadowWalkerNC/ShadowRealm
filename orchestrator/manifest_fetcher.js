/**
 * manifest_fetcher.js — Fetches /v1/manifest from every active SRN app
 * Caches in memory, auto-refreshes every 5 minutes.
 */
const registry = require('./registry');

const _cache  = {};
const REFRESH = 5 * 60 * 1000;

async function fetchManifest(app) {
    try {
        const res = await fetch(app.manifest, {
            headers: {
                'Authorization': `Bearer ${process.env.SRN_SECRET}`,
                'X-SRN-App':    'shadowrealm',
            },
            signal: AbortSignal.timeout(5000),
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const manifest = await res.json();
        _cache[app.name] = { manifest, fetchedAt: Date.now() };
        console.log(`[SRN Manifest] loaded: ${app.name} (${manifest.tools?.length ?? 0} tools)`);
        return manifest;
    } catch (err) {
        console.warn(`[SRN Manifest] fetch failed: ${app.name} — ${err.message}`);
        return null;
    }
}

async function fetchAll() {
    await Promise.all(registry.getActiveApps().map(fetchManifest));
}

function getManifest(appName)  { return _cache[appName]?.manifest || null; }

function getAllTools() {
    return Object.entries(_cache).flatMap(([appName, { manifest }]) =>
        (manifest?.tools || []).map(tool => ({ app: appName, tool }))
    );
}

setInterval(fetchAll, REFRESH);

module.exports = { fetchAll, fetchManifest, getManifest, getAllTools };
