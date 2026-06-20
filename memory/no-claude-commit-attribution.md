---
name: no-claude-commit-attribution
description: User wants git commits without Claude co-author attribution
metadata:
  type: feedback
---

提交时不要加 `Co-Authored-By: Claude ...` 之类的署名,commit message 只写改动本身。

**Why:** 用户两次提交都明确要求"不要包含你的信息"。

**How to apply:** 在这个仓库做 `git commit` 时一律省略 Co-Authored-By 行(覆盖默认约定)。
