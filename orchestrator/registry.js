/**
 * registry.js — Loads and caches SRN_REGISTRY.json
 */
const path = require('path');
let _registry = null;

function load() {
    if (_registry) return _registry;
    _registry = require(path.join(__dirname, '..', 'SRN_REGISTRY.json'));
    return _registry;
}

function getApps()        { return load().apps; }
function getApp(name)     { return load().apps.find(a => a.name === name) || null; }
function getActiveApps()  { return load().apps.filter(a => a.status === 'active'); }

module.exports = { getApps, getApp, getActiveApps };
