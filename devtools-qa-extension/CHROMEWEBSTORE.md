# CHROMEWEBSTORE.md — Chrome Web Store Listing & Store Metadata

> Single source of truth for DevTools QA & Fault Injection Workbench store listing details, permissions justifications, and privacy disclosures.

**Last Updated:** August 20, 2026  
**Extension Name:** DevTools QA & Fault Injection Workbench  
**Version:** 1.0.0  

---

## 1. Store Listing Metadata

- **Short Name:** DevTools QA
- **Summary Description (max 132 chars):** DevTools-Native QA environment for network fault injection, dynamic state control, and live flow capture.
- **Detailed Description:**
  DevTools QA & Fault Injection Workbench is a developer-centric extension designed for frontend engineers, QA testers, and automation developers. It seamlessly embeds inside Google Chrome DevTools to provide robust local fault injection, request mocking, dynamic state control, and network flow monitoring without touching your server code.

  **Key Features:**
  - ⚡ **Declarative Net Request Fault Injection**: Block, delay, or redirect API network traffic at the browser engine level using Chrome DeclarativeNetRequest.
  - ⚙️ **Test State Control & LocalStorage Injection**: Dynamically inject custom JSON state payloads directly into any tab's LocalStorage or runtime memory.
  - 📡 **Live Flow & DOM Capture Stream**: Monitor HTTP/Fetch requests, error flows, and DOM mutation events in real-time.
  - 🛠️ **Custom JS Fault Injection**: Run diagnostic fault scripts and error simulations in the context of the inspected window.

- **Category:** Developer Tools
- **Language:** English

---

## 2. Permissions Justification

Every permission declared in `manifest.json` is justified below for Chrome Web Store review compliance:

| Permission | Purpose & Justification |
| :--- | :--- |
| `declarativeNetRequest` | Required to perform browser-level network fault injections, URL redirections, and request blocking during local QA testing. |
| `declarativeNetRequestFeedback` | Required to provide visual feedback and active rule count indicators in the DevTools QA panel during development and testing. |
| `storage` | Needed to store user-configured fault rules and workbench preferences persistently across browser sessions. |
| `scripting` | Required to inject custom test state scripts and diagnostic fault snippets into inspected web page targets. |
| `activeTab` | Needed to grant temporary permission to interact with the currently inspected developer tab. |
| `tabs` | Needed to obtain the active tab ID for devtools window panel context matching. |
| `<all_urls>` (host permission) | Required to allow network fault injection and flow interception across local and remote QA target applications. |

---

## 3. Privacy & Data Handling Disclosure

- **Data Collection:** None. This extension operates 100% locally inside the user's browser.
- **Data Transmission:** No telemetry, analytics, or user data is transmitted to external servers.
- **Single Purpose Compliance:** The extension's single purpose is providing local web testing and fault injection tools within DevTools.

---

## 4. Version History

- **1.0.0 (2026-08-20):** Initial production release of DevTools QA Workbench featuring DNR fault rules, local state hooks, custom script evaluation, and real-time flow capture stream.
