// DevTools Panel Client Logic — Connects to Service Worker & Controls DNR / State
(() => {
  const inspectedTabId = chrome.devtools.inspectedWindow.tabId;
  const port = chrome.runtime.connect({ name: 'devtools-qa-panel' });

  // UI Elements
  const ruleUrlInput = document.getElementById('rule-url-pattern');
  const ruleActionSelect = document.getElementById('rule-action-type');
  const redirectGroup = document.getElementById('redirect-url-group');
  const redirectUrlInput = document.getElementById('rule-redirect-url');
  const addRuleBtn = document.getElementById('add-fault-rule-btn');
  const clearRulesBtn = document.getElementById('clear-fault-rules-btn');
  const activeRulesList = document.getElementById('active-rules-list');
  const activeRulesCount = document.getElementById('active-rules-count');

  const stateKeyInput = document.getElementById('state-key');
  const stateJsonInput = document.getElementById('state-json');
  const injectStateBtn = document.getElementById('inject-state-btn');
  const evalScriptBtn = document.getElementById('eval-fault-script-btn');
  const customJsInput = document.getElementById('custom-js-snippet');

  const flowStreamLog = document.getElementById('flow-stream-log');
  const clearFlowLogBtn = document.getElementById('clear-flow-log-btn');

  let activeRules = [];
  let ruleIdCounter = 1000;

  // Initialize Port Connection with inspected tab ID
  port.postMessage({ type: 'INIT', tabId: inspectedTabId });

  // Handle incoming port messages from Background Service Worker
  port.onMessage.addListener((msg) => {
    if (msg.type === 'SYNC_STATE' || msg.type === 'RULES_UPDATED') {
      activeRules = msg.rules || [];
      renderRules();
    } else if (msg.type === 'CAPTURED_FLOW') {
      appendFlowLog(msg);
    } else if (msg.type === 'DOM_MUTATION_EVENT') {
      appendDomMutationLog(msg);
    } else if (msg.type === 'INJECTION_SUCCESS') {
      appendSystemLog('✅ Injection Success: ' + msg.message, 'success');
    } else if (msg.type === 'INJECTION_ERROR') {
      appendSystemLog('❌ Injection Error: ' + msg.error, 'error');
    }
  });

  // Toggle Redirect Input UI
  ruleActionSelect.addEventListener('change', () => {
    redirectGroup.style.display = ruleActionSelect.value === 'redirect' ? 'flex' : 'none';
  });

  // Add Dynamic Network Fault Rule (Declarative Net Request)
  addRuleBtn.addEventListener('click', () => {
    const urlFilter = ruleUrlInput.value.trim();
    if (!urlFilter) {
      alert('Please enter a URL match pattern.');
      return;
    }

    const actionType = ruleActionSelect.value;
    const ruleId = ruleIdCounter++;
    let ruleAction = { type: 'block' };

    if (actionType === 'redirect') {
      const redirectUrl = redirectUrlInput.value.trim();
      if (!redirectUrl) {
        alert('Please enter a valid redirect target URL.');
        return;
      }
      ruleAction = { type: 'redirect', redirect: { url: redirectUrl } };
    }

    const newRule = {
      id: ruleId,
      priority: 1,
      action: ruleAction,
      condition: {
        urlFilter,
        resourceTypes: ['xmlhttprequest', 'script', 'image', 'sub_frame', 'main_frame']
      }
    };

    port.postMessage({
      type: 'APPLY_DNR_RULES',
      rulesToAdd: [newRule],
      ruleIdsToRemove: []
    });

    ruleUrlInput.value = '';
    redirectUrlInput.value = '';
  });

  // Clear All Fault Rules
  clearRulesBtn.addEventListener('click', () => {
    const removeIds = activeRules.map(r => r.id);
    port.postMessage({
      type: 'APPLY_DNR_RULES',
      rulesToAdd: [],
      ruleIdsToRemove: removeIds
    });
  });

  // Inject Test Local State Hook into inspected page
  injectStateBtn.addEventListener('click', () => {
    const key = stateKeyInput.value.trim();
    const jsonRaw = stateJsonInput.value.trim();
    if (!key) {
      alert('Please enter a state key.');
      return;
    }

    let parsedVal = jsonRaw;
    try {
      parsedVal = JSON.parse(jsonRaw);
    } catch (_) {}

    chrome.devtools.inspectedWindow.eval(
      `window.__QA_WORKBENCH__ && window.__QA_WORKBENCH__.setLocalState(${JSON.stringify(key)}, ${JSON.stringify(parsedVal)})`,
      (result, isException) => {
        if (isException) {
          appendSystemLog('Failed to set local state: ' + JSON.stringify(isException), 'error');
        } else {
          appendSystemLog(`State injected into LocalStorage: ${key}`, 'success');
        }
      }
    );
  });

  // Run Custom JS Fault Snippet in Inspected Window
  evalScriptBtn.addEventListener('click', () => {
    const code = customJsInput.value.trim();
    if (!code) return;

    chrome.devtools.inspectedWindow.eval(code, (result, isException) => {
      if (isException) {
        appendSystemLog('Custom Fault JS Execution Error: ' + JSON.stringify(isException), 'error');
      } else {
        appendSystemLog('Custom Fault JS Executed: ' + (result || 'OK'), 'success');
      }
    });
  });

  // Render DNR Rules List
  function renderRules() {
    activeRulesCount.textContent = `${activeRules.length} Rules`;
    if (activeRules.length === 0) {
      activeRulesList.innerHTML = '<div style="color:var(--muted)">No active fault injection rules.</div>';
      return;
    }

    activeRulesList.innerHTML = activeRules.map(r => {
      const isBlock = r.action.type === 'block';
      const badgeClass = isBlock ? 'block' : 'redirect';
      const label = isBlock ? 'BLOCK' : `REDIRECT ➔ ${r.action.redirect?.url || ''}`;
      return `
        <div class="log-item">
          <div>
            <span class="badge ${badgeClass}">${label}</span>
            <span style="font-family:Consolas,monospace;margin-left:6px;">${r.condition.urlFilter}</span>
          </div>
          <button type="button" class="secondary danger remove-single-rule" data-id="${r.id}" style="padding:2px 6px;font-size:10px;">✖</button>
        </div>
      `;
    }).join('');

    activeRulesList.querySelectorAll('.remove-single-rule').forEach(btn => {
      btn.addEventListener('click', () => {
        const id = parseInt(btn.dataset.id, 10);
        port.postMessage({
          type: 'APPLY_DNR_RULES',
          rulesToAdd: [],
          ruleIdsToRemove: [id]
        });
      });
    });
  }

  // Append Flow Log to Stream
  function appendFlowLog(flow) {
    if (flowStreamLog.children.length === 1 && flowStreamLog.children[0].textContent.includes('Listening')) {
      flowStreamLog.innerHTML = '';
    }

    const item = document.createElement('div');
    const isErr = flow.flowType === 'FETCH_ERROR' || (flow.status && flow.status >= 400);
    item.className = `log-item ${isErr ? 'error' : 'success'}`;
    
    item.innerHTML = `
      <div>
        <strong style="color:var(--accent)">[${flow.method || 'FLOW'}]</strong>
        <span>${flow.url}</span>
        ${flow.status ? `<span style="opacity:0.7">(${flow.status})</span>` : ''}
      </div>
      <div style="opacity:0.5;font-size:10px;">${flow.duration}ms</div>
    `;

    flowStreamLog.prepend(item);
  }

  function appendDomMutationLog(evt) {
    if (flowStreamLog.children.length === 1 && flowStreamLog.children[0].textContent.includes('Listening')) {
      flowStreamLog.innerHTML = '';
    }

    const item = document.createElement('div');
    item.className = 'log-item';
    item.innerHTML = `
      <div style="color:var(--warning)">
        <strong>[DOM MUTATION]</strong> ${evt.count} nodes mutated
      </div>
      <div style="opacity:0.5;font-size:10px;">${new Date(evt.timestamp).toLocaleTimeString()}</div>
    `;
    flowStreamLog.prepend(item);
  }

  function appendSystemLog(msg, type = 'info') {
    const item = document.createElement('div');
    item.className = `log-item ${type}`;
    item.innerHTML = `<div>${msg}</div>`;
    flowStreamLog.prepend(item);
  }

  clearFlowLogBtn.addEventListener('click', () => {
    flowStreamLog.innerHTML = '<div style="color:var(--muted)">Listening for network flows and DOM events...</div>';
  });
})();
