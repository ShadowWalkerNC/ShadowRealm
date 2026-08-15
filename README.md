<p align="center">
  <img src="docs/odysseus-wordmark.png" alt="Odysseus" width="238">
</p>

<p align="center">
  A self-hosted AI workspace for chat, agents, research, documents, email, notes, calendar, and local model workflows.
</p>

<p align="center">
  <a href="#quick-start">Quick Start</a> ·
  <a href="docs/setup.md">Setup Guide</a> ·
  <a href="CONTRIBUTING.md">Contributing</a> ·
  <a href="ROADMAP.md">Roadmap</a>
</p>

<p align="center">
  <a href="https://repology.org/project/odysseus-ai/versions"><img src="https://repology.org/badge/vertical-allrepos/odysseus-ai.svg" alt="Packaging status"></a>
</p>

<p align="center">
  <img src="docs/odysseus-browser.jpg" alt="Odysseus interface">
</p>

---

## Quick Start

> `dev` is the default branch and gets the newest changes first. Use [`main`](https://github.com/pewdiepie-archdaemon/odysseus/tree/main) if you want the more curated branch.

```bash
git clone https://github.com/pewdiepie-archdaemon/odysseus.git
cd odysseus
cp .env.example .env
docker compose up -d --build
```

Open `http://localhost:7000` when the containers are healthy. The first admin password is printed in `docker compose logs odysseus`.

Native installs, GPU notes, Windows/macOS instructions, HTTPS, and configuration live in the [setup guide](docs/setup.md).

## Features

- **Autonomous AI Developer Suite** — 100% open-source Cursor, Goose, and Claude Code alternative with AST symbol indexing (`src/ast_indexer.py`), CLI Anything engine, and dynamic tool discovery.
- **Odysseus Terminal CLI Hub (`odysseus.py`)** — Interactive terminal menu interface to manage repos, run 4-stage audits, trigger swarms, launch servers, and mass update tools directly under CLI.
- **Windows Desktop Executable (`.exe`) & Electron App** — Native Windows desktop application with system tray integration and 1-click NSIS installer (`dist/Odysseus AI Suite Setup 2.0.0.exe`).
- **GitHub Repositories Hub & Armada Swarms** — Central dashboard (`/repos`) managing 20+ local projects with stack detection, git branches, 4-stage audits, and multi-agent Armada swarms.
- **Strix AI Audit & 25+ Toolchains** — Built-in integration for Strix autonomous AI pen-testing, Semgrep, Trivy, Bandit, Pipelock, Agent-Audit, Docker, Cargo, UV, and GH extensions with mass multi-package manager updates (`/api/repos/harness/update`).
- **Interactive Swarm Progress Drawer** — Live collapsible monospace logs with SVG iconography and one-click **Approve & Commit** / **Reject & Rollback** controls.
- **Native Git & Branch Pipelines** — Isolated feature branch creation (`feature/armada-swarm-xyz`), staged diff reviews, and GitHub PR drafting.
- **Full Web & HTML Viewer** — Live interactive HTML, JavaScript, CSS, and form previewing in the Document Panel.
- **Chat + Agents** — local/API models, tools, MCP, files, shell, skills, and vector memory.
- **Cookbook** — hardware-aware model recommendations, downloads, and serving.
- **Deep Research** — multi-step web research with source reading and report generation.
- **Compare** — blind side-by-side model testing and synthesis.
- **Documents** — writing-first editor with AI edits, suggestions, Markdown, HTML, CSV, and syntax highlighting.
- **Mobile PWA & 100% Free Remote Access** — Native iOS/Android standalone PWA with Cloudflare Tunnel (`cloudflared`) and LAN access (`0.0.0.0:7000`) for zero-cost remote chat prompts and swarm monitoring on your phone.
- **Email, Notes, Tasks & Calendar** — IMAP/SMTP inbox, triage, todos, scheduled agent tasks, and CalDAV sync.

## Demo

A full hover-to-play tour lives on the landing page: [`docs/index.html`](docs/index.html).

## Contributing

Help is welcome. The best entry points are fresh-install testing, provider setup bugs, mobile/editor polish, docs, and small focused refactors. See [CONTRIBUTING.md](CONTRIBUTING.md) and [ROADMAP.md](ROADMAP.md).

## Security

Odysseus is a self-hosted workspace with powerful local tools. Keep auth enabled, keep private data out of Git, and do not expose raw model/service ports publicly. Deployment details are in the [setup guide](docs/setup.md#security-notes).

## Star History

<a href="https://www.star-history.com/?repos=pewdiepie-archdaemon%2Fodysseus&type=date&legend=top-left">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/chart?repos=pewdiepie-archdaemon/odysseus&type=date&theme=dark&legend=top-left" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/chart?repos=pewdiepie-archdaemon/odysseus&type=date&legend=top-left" />
   <img alt="Star History Chart" src="https://api.star-history.com/chart?repos=pewdiepie-archdaemon/odysseus&type=date&legend=top-left" />
 </picture>
</a>

## License

AGPL-3.0-or-later -- see [LICENSE](LICENSE) and [ACKNOWLEDGMENTS.md](ACKNOWLEDGMENTS.md).
