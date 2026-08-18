---
name: shadowrealm-bridge
description: >-
  Connects Antigravity directly to ShadowRealm server capabilities (Armada Swarms,
  Cascading Intelligence Router, CactusNeedle Local AI, CodeBurn Token Tracker,
  Self-Healing Test Engine, and AST Indexer). Use whenever the user asks to run
  ShadowRealm tools, execute self-healing test loops, trigger multi-agent armada swarms,
  or route zero-cost local AI queries.
---

# ShadowRealm Bridge Skill

This skill grants Antigravity full access to all ShadowRealm engine capabilities running locally at `http://localhost:7000`.

---

## Available ShadowRealm Endpoints & Workflows

### 1. Cascading Intelligence Router (Tier 0 - Tier 3)
Route queries dynamically through ShadowRealm's low-overhead tiers:
- **Tier 0**: In-memory cache + AST Symbol Outline ($0.00, <1ms)
- **Tier 1**: CactusNeedle 14MB local AI tool calling (Zero cloud tokens)
- **Tier 2**: Muse Code / Meta AI fast code generation
- **Tier 3**: Deep cloud reasoning pass

**Invoke via PowerShell / `run_command`**:
```powershell
Invoke-RestMethod -Uri "http://localhost:7000/api/repos/cascade/route" -Method POST -ContentType "application/json" -Body '{"prompt": "outline symbols in src/tool_harness.py"}'
```

---

### 2. Self-Healing Autonomous Test Loop
Execute repo unit tests (`pytest`, `cargo test`, `npm test`) with automated error parsing, traceback extraction, and local patch attempts:

**Invoke via PowerShell / `run_command`**:
```powershell
Invoke-RestMethod -Uri "http://localhost:7000/api/repos/test/auto-heal" -Method POST -ContentType "application/json" -Body '{"repo_name": "ShadowRealm", "max_attempts": 2}'
```

---

### 3. Launch Armada Swarm Engine
Spawn multi-agent swarm harnesses (ShadowCoder, ShadowTester, ShadowOps) for any repository:

**Invoke via PowerShell / `run_command`**:
```powershell
Invoke-RestMethod -Uri "http://localhost:7000/api/repos/armada/launch" -Method POST -ContentType "application/json" -Body '{"repo_name": "ShadowRealm", "task_prompt": "Audit and build features"}'
```

---

### 4. Direct CLI Anything Host Execution
Execute arbitrary host CLI commands (`needle`, `codeburn`, `strix`, `docker`, `cargo`, `rg`) with ShadowRealm diagnostics:

**Invoke via PowerShell / `run_command`**:
```powershell
Invoke-RestMethod -Uri "http://localhost:7000/api/repos/harness/execute" -Method POST -ContentType "application/json" -Body '{"command": "needle playground"}'
```

---

### 5. CactusNeedle 14MB Local AI Tool Dispatch
Run zero-cloud-token local AI inference directly:

**Invoke via PowerShell / `run_command`**:
```powershell
Invoke-RestMethod -Uri "http://localhost:7000/api/repos/harness/needle" -Method POST -ContentType "application/json" -Body '{"prompt": "Run security check on current directory"}'
```

---

### 6. 4-Stage Repository Security & Health Audit
Run automated multi-stage linting, dependency health, and security checks on a target repo:

**Invoke via PowerShell / `run_command`**:
```powershell
Invoke-RestMethod -Uri "http://localhost:7000/api/repos/audit/run" -Method POST -ContentType "application/json" -Body '{"repo_name": "ShadowRealm"}'
```
