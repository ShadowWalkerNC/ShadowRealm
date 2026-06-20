require('dotenv').config();
const express         = require('express');
const manifestFetcher = require('./orchestrator/manifest_fetcher');
const healthMonitor   = require('./orchestrator/health_monitor');
const dispatcher      = require('./orchestrator/tool_dispatcher');
const registry        = require('./orchestrator/registry');

const app  = express();
const PORT = process.env.PORT || 4000;

app.use(express.json());

function requireAuth(req, res, next) {
    const token = (req.headers['authorization'] || '').replace(/^Bearer\s+/i, '');
    if (!token || token !== process.env.SRN_SECRET) {
        return res.status(401).json({ success: false, error: 'Unauthorized', code: 'UNAUTHORIZED' });
    }
    next();
}

// Public
app.get('/v1/health', (_req, res) => res.json({
    status: 'ok', app: 'shadowrealm', version: '1.0.0', uptime: Math.floor(process.uptime()),
}));

// Manifest
app.get('/v1/manifest', requireAuth, (_req, res) => res.json({
    app: 'shadowrealm', version: '1.0.0',
    tools: [
        { name: 'call_tool',      description: 'Dispatch a tool call to any SRN app',            method: 'POST', path: '/v1/call_tool' },
        { name: 'health_status',  description: 'Get live health status of all SRN apps',          method: 'GET',  path: '/v1/health_status' },
        { name: 'list_apps',      description: 'List all registered SRN apps and their tools',    method: 'GET',  path: '/v1/apps' },
        { name: 'find_tool',      description: 'Find which app owns a given tool name',            method: 'GET',  path: '/v1/find_tool' },
    ],
}));

app.get('/v1/health_status', requireAuth, (_req, res) =>
    res.json({ success: true, data: healthMonitor.getStatus() }));

app.get('/v1/apps', requireAuth, (_req, res) => {
    const apps = registry.getApps().map(a => ({
        ...a,
        manifest_cached: !!manifestFetcher.getManifest(a.name),
        tools: manifestFetcher.getManifest(a.name)?.tools?.map(t => t.name) || [],
    }));
    res.json({ success: true, data: apps });
});

app.get('/v1/find_tool', requireAuth, (req, res) => {
    const { tool } = req.query;
    if (!tool) return res.status(400).json({ success: false, error: 'tool query param required', code: 'MISSING_PARAMS' });
    const found = dispatcher.findTool(tool);
    if (!found) return res.status(404).json({ success: false, error: `Tool '${tool}' not found`, code: 'TOOL_NOT_FOUND' });
    res.json({ success: true, data: found });
});

app.post('/v1/call_tool', requireAuth, async (req, res) => {
    const { app: appName, tool: toolName, input } = req.body || {};
    if (!appName || !toolName)
        return res.status(400).json({ success: false, error: '"app" and "tool" are required', code: 'MISSING_PARAMS' });
    res.json(await dispatcher.call(appName, toolName, input || {}));
});

app.listen(PORT, async () => {
    console.log(`🌐 ShadowRealm running on port ${PORT}`);
    await manifestFetcher.fetchAll();
    healthMonitor.startMonitor();
    console.log(`✅ ShadowRealm ready — ${registry.getApps().length} apps in registry`);
});
