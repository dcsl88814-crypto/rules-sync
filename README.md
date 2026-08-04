# sr-rules

Shadowrocket / Surge 规则模块管理仓库。自动从 [Loyalsoldier/surge-rules](https://github.com/Loyalsoldier/surge-rules) 拉取规则源，转换成 Shadowrocket 兼容的 `.module` 模块，并按策略拆分合并，方便直接订阅使用。

## 规则来源与致谢

所有规则数据均来自 **Loyalsoldier** 的 [surge-rules](https://github.com/Loyalsoldier/surge-rules) 项目（GPL-3.0 License），感谢他长期维护高质量规则集。本仓库只负责抓取、转换与自动更新，规则内容的所有权与版权归原作者所有。

Sources: [Loyalsoldier/surge-rules](https://github.com/Loyalsoldier/surge-rules)

## 规则转换与正则规则

`update_rules.py` 会把上游规则逐行转换成 Shadowrocket 兼容的规则，其中包含用正则表达式生成的规则：

- `||example.com^`（adblock 域名）→ `DOMAIN-SUFFIX,example.com,POLICY`
- `|http://example.com/path`（adblock 完整 URL）→ `URL-REGEX,^http://example\.com/path.*,POLICY`（通过 `re.escape` 把 URL 转成正则）
- `1.2.3.4/24` → `IP-CIDR,1.2.3.4/24,POLICY`
- 含 `*` 的域名 → `DOMAIN-KEYWORD,xxx,POLICY`

生成的规则按策略拆分合并成 `merged_direct/proxy/reject/all.module`，方便直接订阅。

## 项目结构

- `update_rules.py`：下载规则源，转换为 `.module` 文件，并生成 `merged_direct/proxy/reject/all.module`。
- `.github/workflows/update_rules.yml`：每天 02:00 UTC 自动更新 `rules/` 下的模块（支持手动触发）。
- `examples/example.conf`：静态示例配置（脚本不会生成或修改它），可直接导入使用。
- `rules/*.module`：生成的模块文件（由 Actions 自动更新，勿手动编辑）。

## 在 Shadowrocket 中使用

Shadowrocket 支持订阅 `.module` 模块和导入 `.conf` 配置。有两种用法：

### 订阅链接一览

两种域名形式，国内用户推荐使用 CDN：

| 域名 | URL 形式 | 说明 |
| --- | --- | --- |
| **jsDelivr CDN** | `https://cdn.jsdelivr.net/gh/dcsl88814-crypto/sr-rules@main/<path>` | 国内可直连，推荐使用；分支缓存约 7 天，可加 `?v=日期` 强制刷新 |
| **GitHub raw** | `https://raw.githubusercontent.com/dcsl88814-crypto/sr-rules/refs/heads/main/<path>` | 需要能访问 GitHub |

合并模块（按策略去重合并，订阅一个即可）：

| 模块 | 策略 | CDN 链接 | GitHub raw 链接 |
| --- | --- | --- | --- |
| `merged_all.module` | 全部 | `https://cdn.jsdelivr.net/gh/dcsl88814-crypto/sr-rules@main/rules/merged_all.module` | `https://raw.githubusercontent.com/dcsl88814-crypto/sr-rules/refs/heads/main/rules/merged_all.module` |
| `merged_direct.module` | 仅直连 | `https://cdn.jsdelivr.net/gh/dcsl88814-crypto/sr-rules@main/rules/merged_direct.module` | `https://raw.githubusercontent.com/dcsl88814-crypto/sr-rules/refs/heads/main/rules/merged_direct.module` |
| `merged_proxy.module` | 仅代理 | `https://cdn.jsdelivr.net/gh/dcsl88814-crypto/sr-rules@main/rules/merged_proxy.module` | `https://raw.githubusercontent.com/dcsl88814-crypto/sr-rules/refs/heads/main/rules/merged_proxy.module` |
| `merged_reject.module` | 仅拦截 | `https://cdn.jsdelivr.net/gh/dcsl88814-crypto/sr-rules@main/rules/merged_reject.module` | `https://raw.githubusercontent.com/dcsl88814-crypto/sr-rules/refs/heads/main/rules/merged_reject.module` |

> 单文件模块（`rules/` 下的 `direct` / `proxy` / `reject` / `private` / `apple` / `icloud` / `google` / `gfw` / `tld-not-cn` / `telegramcidr` / `cncidr`）用于配置里的 `RULE-SET` 引用，把上面链接中的文件名替换即可。

### 方式一：订阅模块（推荐，自动更新）

1. 打开 Shadowrocket，进入 **配置 (Config)** 页，点击右上角 **+**，选择 **添加模块 (Add Module)**。
2. 从上方「订阅链接一览」表格中复制模块链接（国内推荐用 jsDelivr CDN 列；若需绕过 CDN 缓存，可在 URL 末尾加 `?v=日期`）。
3. 添加后可手动更新，或等仓库的 Actions 每天 02:00 UTC 自动更新规则后下拉刷新。

> 提示：`merged_all.module` 包含全部规则（直连/代理/拦截去重合并），普通用户订阅这一个即可。

### 方式二：导入示例配置

1. 下载示例配置：**CDN** `https://cdn.jsdelivr.net/gh/dcsl88814-crypto/sr-rules@main/examples/example.conf`，或 **GitHub raw** `https://raw.githubusercontent.com/dcsl88814-crypto/sr-rules/refs/heads/main/examples/example.conf`。
2. 把文件保存为 `example.conf`，用 Shadowrocket 打开即可导入。
3. 导入后，Shadowrocket 会按 `update-url` 定时拉取最新的配置，规则则由各 `RULE-SET` 模块按需加载更新。`update-url` 与 `RULE-SET` 均使用上方表格中的 CDN 链接。

## License

本项目采用 [GNU General Public License v3.0](LICENSE)（GPL-3.0）。

Copyright (c) 2026 vycsl-dev

> 注意：本项目仅转换/聚合上游规则。上游规则数据版权归 [Loyalsoldier/surge-rules](https://github.com/Loyalsoldier/surge-rules)（GPL-3.0 License）所有。
