---
name: fix-and-verify
description: Take a bug report or failing test, attempt a local fix, run tests, iterate up to N times, then flag cloud escalation.
category: coding
tags: [fix, verify, tests, escalate]
platforms: [all]
requires_toolsets: []
fallback_for_toolsets: []
when_to_use: |
  User provides a bug report or failing test and wants a fix with verification.
  Trigger workflow `fix-and-verify`. Always run self-tests before declaring done.
  Do NOT use for broad architecture redesign (use review/analyze or escalate path).
status: active
version: 1.0.0
confidence: 0.9
source: user
---

## Instructions

1. Start pipeline:
   `POST /api/routing/pipelines/start`
   body: `{"pipeline":"fix-and-verify","params":{"project_dir":"<path>","bug_report":"<text>","max_attempts":3}}`
2. When status is `waiting_for_input` for a fix attempt:
   - Apply the minimal local patch with tools.
   - Resume with `{"fix_applied": true}`.
3. Pipeline runs tests after each attempt.
4. If local attempts exhaust, surface the escalation package (unresolved only) —
   do not send the whole task to cloud if OpenRouter is connected later.
5. Never mark done if self-tests failed — say so explicitly.

## Examples

**Example:**
Input: `fix-and-verify: tests/test_foo.py fails on test_bar`
Expected: local fix attempts + test results + escalate only if still failing.

## Failure Modes

- **No project_dir / bug_report**: Wait for input.
- **Tests cannot run**: Report self-test gate blocker; do not claim success.
