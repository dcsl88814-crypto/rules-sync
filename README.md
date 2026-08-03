# hope

Shadowrocket / Surge rulesets 管理仓库。

- `update_rules.py`：下载规则源，转换为 `.module` 文件，并生成 `merged_direct/proxy/reject/all.module`。
- `.github/workflows/update_rules.yml`：每天 02:00 UTC 自动更新 `rules/` 下的模块。
- `examples/example.conf`：静态示例配置（脚本不会生成或修改它）。使用前请把 `<OWNER>` / `<REPO>` / `<BRANCH>` 替换为你的实际值。

> 提示：`example.conf` 由人工维护，Actions 只更新 `rules/` 下的模块文件。
