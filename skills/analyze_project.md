---
name: analyze-project
description: Scan a project directory, summarize structure, flag TODOs/bugs/inconsistencies, produce a local-only report.
category: coding
tags: [analyze, project, audit, local-only]
platforms: [all]
requires_toolsets: []
fallback_for_toolsets: []
when_to_use: |
  User asks to analyze/scan/audit a project directory, summarize repo structure,
  or find TODOs/obvious issues. Prefer triggering the named workflow
  `analyze-project` via POST /api/routing/pipelines/start.
  Do NOT use for implementing features or fixing a specific failing test.
status: active
version: 1.0.0
confidence: 0.9
source: user
---

## Instructions

1. Call `POST /api/routing/pipelines/start` with:
   `{"pipeline":"analyze-project","params":{"project_dir":"<path>"}}`
2. The pipeline is **local-only by default** (never route the scan to cloud).
3. Return the `result.report` markdown to the user.
4. If the run status is `waiting_for_input`, ask for `project_dir` and resume via
   `POST /api/routing/pipelines/runs/{run_id}/resume`.

## Examples

**Example:**
Input: `analyze-project /workspace/myapp`
Expected output: Structure summary + TODO/FIXME list + inconsistency flags.

## Failure Modes

- **Missing project_dir**: Pipeline waits for input — ask the user for the path.
- **Huge trees**: Scanner caps file walk; note truncation in the report.
