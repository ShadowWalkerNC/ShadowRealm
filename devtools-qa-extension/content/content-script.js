// Content Script — Monitors network requests, DOM mutations, and local state injection
(() => {
  // 1. Capture Fetch & XHR Flow Requests
  const originalFetch = window.fetch;
  window.fetch = async function (...args) {
    const startTime = performance.now();
    const url = typeof args[0] === 'string' ? args[0] : (args[0]?.url || 'unknown');
    const method = args[1]?.method || 'GET';

    try {
      const response = await originalFetch.apply(this, args);
      const duration = Math.round(performance.now() - startTime);

      chrome.runtime.sendMessage({
        type: 'CAPTURED_FLOW',
        flowType: 'FETCH',
        url,
        method,
        status: response.status,
        duration,
        timestamp: new Date().toISOString()
      }).catch(() => {});

      return response;
    } catch (error) {
      const duration = Math.round(performance.now() - startTime);
      chrome.runtime.sendMessage({
        type: 'CAPTURED_FLOW',
        flowType: 'FETCH_ERROR',
        url,
        method,
        error: error.message,
        duration,
        timestamp: new Date().toISOString()
      }).catch(() => {});
      throw error;
    }
  };

  // 2. DOM Mutation & Flow Capture
  const observer = new MutationObserver((mutations) => {
    let relevantCount = 0;
    for (const m of mutations) {
      if (m.addedNodes.length > 0 || m.removedNodes.length > 0) {
        relevantCount++;
      }
    }

    if (relevantCount > 0) {
      chrome.runtime.sendMessage({
        type: 'DOM_MUTATION_EVENT',
        count: relevantCount,
        timestamp: new Date().toISOString()
      }).catch(() => {});
    }
  });

  if (document.documentElement) {
    observer.observe(document.documentElement, { childList: true, subtree: true });
  }

  // 3. Expose Test State Hook
  window.__QA_WORKBENCH__ = {
    setLocalState: (key, val) => {
      try {
        localStorage.setItem(key, JSON.stringify(val));
        console.log(`[QA Workbench] LocalStorage set: ${key}`, val);
      } catch (e) {
        console.error('[QA Workbench] Failed to set state', e);
      }
    },
    getLocalState: (key) => {
      try {
        return JSON.parse(localStorage.getItem(key));
      } catch (e) {
        return localStorage.getItem(key);
      }
    }
  };
})();
