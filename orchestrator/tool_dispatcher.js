/**
 * tool_dispatcher.js — Routes tool calls to the correct SRN app
 *
 * Usage:
 *   const result = await dispatcher.call('post-pilot', 'publish_post', { caption: '...' });
 */
const registry        = require('./registry');
const manifestFetcher = require('./manifest_fetcher');

async function call(appName, toolName, input = {}) {
    const app = registry.getApp(appName);
    if (!app) return { success: false, error: `Unknown app: ${appName}`, code: 'APP_NOT_FOUND' };

    const manifest = manifestFetcher.getManifest(appName);
    const tool     = manifest?.tools?.find(t => t.name === toolName);
    if (!tool) return { success: false, error: `Tool '${toolName}' not found on '${appName}'`, code: 'TOOL_NOT_FOUND' };

    const url    = `${app.url}${tool.path}`;
    const method = (tool.method || 'POST').toUpperCase();

    try {
        const res = await fetch(url, {
            method,
            headers: {
                'Authorization': `Bearer ${process.env.SRN_SECRET}`,
                'X-SRN-App':    'shadowrealm',
                'Content-Type': 'application/json',
            },
            body:   method !== 'GET' ? JSON.stringify(input) : undefined,
            signal: AbortSignal.timeout(10_000),
        });
        return await res.json();
    } catch (err) {
        console.error(`[SRN Dispatcher] ${appName}/${toolName} failed: ${err.message}`);
        return { success: false, error: err.message, code: 'DISPATCH_ERROR' };
    }
}

function findTool(toolName) {
    return manifestFetcher.getAllTools().find(({ tool }) => tool.name === toolName) || null;
}

module.exports = { call, findTool };
