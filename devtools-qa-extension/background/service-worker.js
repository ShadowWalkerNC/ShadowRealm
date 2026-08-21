// Service Worker — Background controller for DNR Rules, Storage & Panel Messaging

const DEVTOOLS_PORTS = new Map(); // tabId -> port

chrome.runtime.onConnect.addListener((port) => {
  if (port.name === 'devtools-qa-panel') {
    let connectedTabId = null;

    port.onMessage.addListener(async (msg) => {
      if (msg.type === 'INIT') {
        connectedTabId = msg.tabId;
        DEVTOOLS_PORTS.set(connectedTabId, port);
        // Send initial state & dynamic rules
        const rules = await chrome.declarativeNetRequest.getDynamicRules();
        const storage = await chrome.storage.local.get(null);
        port.postMessage({ type: 'SYNC_STATE', rules, storage });
      } else if (msg.type === 'APPLY_DNR_RULES') {
        await applyDnrRules(msg.rulesToAdd, msg.ruleIdsToRemove);
        const updatedRules = await chrome.declarativeNetRequest.getDynamicRules();
        port.postMessage({ type: 'RULES_UPDATED', rules: updatedRules });
      } else if (msg.type === 'SET_STATE') {
        await chrome.storage.local.set(msg.data);
        port.postMessage({ type: 'STATE_SAVED', data: msg.data });
      } else if (msg.type === 'INJECT_FAULT_SCRIPT') {
        if (connectedTabId) {
          try {
            await chrome.scripting.executeScript({
              target: { tabId: connectedTabId },
              func: (scriptContent) => {
                const el = document.createElement('script');
                el.textContent = scriptContent;
                (document.head || document.documentElement).appendChild(el);
                el.remove();
              },
              args: [msg.script]
            });
            port.postMessage({ type: 'INJECTION_SUCCESS', message: 'Script injected successfully' });
          } catch (err) {
            port.postMessage({ type: 'INJECTION_ERROR', error: err.message });
          }
        }
      }
    });

    port.onDisconnect.addListener(() => {
      if (connectedTabId) {
        DEVTOOLS_PORTS.delete(connectedTabId);
      }
    });
  }
});

// Relay content script captured flows to matching DevTools panel
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'CAPTURED_FLOW' || message.type === 'DOM_MUTATION_EVENT') {
    const tabId = sender.tab?.id;
    if (tabId && DEVTOOLS_PORTS.has(tabId)) {
      DEVTOOLS_PORTS.get(tabId).postMessage(message);
    }
  }
  return true;
});

// Helper: Dynamic DNR rules updating
async function applyDnrRules(addRules, removeRuleIds) {
  try {
    await chrome.declarativeNetRequest.updateDynamicRules({
      addRules: addRules || [],
      removeRuleIds: removeRuleIds || []
    });
  } catch (err) {
    console.error('Failed to update DNR dynamic rules:', err);
  }
}
