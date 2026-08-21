// Creates DevTools Panel. Path MUST be relative to extension root!
chrome.devtools.panels.create(
  "⚡ QA & Faults",
  "icons/icon-16.png",
  "devtools/panel/panel.html",
  (panel) => {
    console.log("DevTools QA & Fault Injection Panel initialized.");
  }
);
