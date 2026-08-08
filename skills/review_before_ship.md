---
name: review-before-ship
description: Final handoff review — run tests, summarize what changed and why, flag uncertainty. Not an auto-merge.
category: coding
tags: [review, ship, handoff, tests]
platforms: [all]
requires_toolsets: []
fallback_for_toolsets: []
when_to_use: |
  User asks for a final review before shipping/merging, a handoff checkpoint,
  or "is this ready?". Trigger workflow `review-before-ship`.
  Do NOT auto-merge or push.
status: active
version: 1.0.0
confidence: 0.9
source: user
---

## Instructions

1. Start pipeline:
   `POST /api/routing/pipelines/start`
   body: `{"pipeline":"review-before-ship","params":{"project_dir":"<path>","diff_summary":"<optional>"}}`
2. Present `result.handoff`, test outcome, change summary, and `uncertain` flags.
3. This is a **human handoff checkpoint** — never merge or push as part of this skill.
4. If tests failed or could not run, say so explicitly in the handoff.

## Examples

**Example:**
Input: `review-before-ship on /workspace`
Expected: test status + change summary + uncertainty list + "ready for human review".

## Failure Modes

- **No git / empty diff**: Fall back to provided diff_summary or status --short.
- **Test suite missing**: Self-test gate still runs compile checks; report method used.
