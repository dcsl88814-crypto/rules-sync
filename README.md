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
- `examples/example_whitelist.conf`、`examples/example_blacklist.conf`、`examples/only_reject_list.conf`：三种预设的静态示例配置（脚本不会生成或修改它们），可直接导入使用。
- `rules/*.module`：生成的模块文件（由 Actions 自动更新，勿手动编辑）。

## 在 Shadowrocket 中使用

Shadowrocket 支持导入 `.conf` 配置和订阅 `.module` 模块。有两种用法：

### 方式一：导入示例配置（推荐，快速上手）

提供了三种预设配置，按需选择，用 Shadowrocket 打开链接即可导入：

| 配置 | 说明 | CDN 链接 | GitHub raw 链接 |
| --- | --- | --- | --- |
| `example_whitelist.conf` | 白名单模式：默认走代理，直连域名走直连 | `https://cdn.jsdelivr.net/gh/dcsl88814-crypto/sr-rules@main/examples/example_whitelist.conf` | `https://raw.githubusercontent.com/dcsl88814-crypto/sr-rules/refs/heads/main/examples/example_whitelist.conf` |
| `example_blacklist.conf` | 黑名单模式：默认直连，仅代理/拦截黑名单域名 | `https://cdn.jsdelivr.net/gh/dcsl88814-crypto/sr-rules@main/examples/example_blacklist.conf` | `https://raw.githubusercontent.com/dcsl88814-crypto/sr-rules/refs/heads/main/examples/example_blacklist.conf` |
| `only_reject_list.conf` | 仅拦截模式：只拦截广告/恶意域名，其余全部直连 | `https://cdn.jsdelivr.net/gh/dcsl88814-crypto/sr-rules@main/examples/only_reject_list.conf` | `https://raw.githubusercontent.com/dcsl88814-crypto/sr-rules/refs/heads/main/examples/only_reject_list.conf` |

导入后，Shadowrocket 会按 `update-url` 定时拉取最新的配置，规则则由各 `RULE-SET` 模块按需加载更新（均使用 jsDelivr CDN 链接）。

### 方式二：订阅模块（按需加载，自动更新）

两种域名形式，国内用户推荐使用 CDN：

| 域名 | URL 形式 | 说明 |
| --- | --- | --- |
| **jsDelivr CDN** | `https://cdn.jsdelivr.net/gh/dcsl88814-crypto/sr-rules@main/<path>` | 国内可直连，推荐使用；分支缓存约 7 天，可加 `?v=日期` 强制刷新 |
| **GitHub raw** | `https://raw.githubusercontent.com/dcsl88814-crypto/sr-rules/refs/heads/main/<path>` | 需要能访问 GitHub |

1. 打开 Shadowrocket，进入 **配置 (Config)** 页，点击右上角 **+**，选择 **添加模块 (Add Module)**。
2. 从下表复制模块链接（国内推荐用 jsDelivr CDN 列；若需绕过 CDN 缓存，可在 URL 末尾加 `?v=日期`）。
3. 添加后可手动更新，或等仓库的 Actions 每天 02:00 UTC 自动更新规则后下拉刷新。

> 提示：`merged_all.module` 包含全部规则（直连/代理/拦截去重合并），普通用户订阅这一个即可。

合并模块（按策略去重合并，订阅一个即可）：

| 模块 | 策略 | CDN 链接 | GitHub raw 链接 |
| --- | --- | --- | --- |
| `merged_all.module` | 全部 | `https://cdn.jsdelivr.net/gh/dcsl88814-crypto/sr-rules@main/rules/merged_all.module` | `https://raw.githubusercontent.com/dcsl88814-crypto/sr-rules/refs/heads/main/rules/merged_all.module` |
| `merged_direct.module` | 仅直连 | `https://cdn.jsdelivr.net/gh/dcsl88814-crypto/sr-rules@main/rules/merged_direct.module` | `https://raw.githubusercontent.com/dcsl88814-crypto/sr-rules/refs/heads/main/rules/merged_direct.module` |
| `merged_proxy.module` | 仅代理 | `https://cdn.jsdelivr.net/gh/dcsl88814-crypto/sr-rules@main/rules/merged_proxy.module` | `https://raw.githubusercontent.com/dcsl88814-crypto/sr-rules/refs/heads/main/rules/merged_proxy.module` |
| `merged_reject.module` | 仅拦截 | `https://cdn.jsdelivr.net/gh/dcsl88814-crypto/sr-rules@main/rules/merged_reject.module` | `https://raw.githubusercontent.com/dcsl88814-crypto/sr-rules/refs/heads/main/rules/merged_reject.module` |

单文件模块（`rules/` 下，供配置里的 `RULE-SET` 引用）：

| 模块 | 策略 | CDN 链接 | GitHub raw 链接 |
| --- | --- | --- | --- |
| `direct.module` | DIRECT | `https://cdn.jsdelivr.net/gh/dcsl88814-crypto/sr-rules@main/rules/direct.module` | `https://raw.githubusercontent.com/dcsl88814-crypto/sr-rules/refs/heads/main/rules/direct.module` |
| `proxy.module` | PROXY | `https://cdn.jsdelivr.net/gh/dcsl88814-crypto/sr-rules@main/rules/proxy.module` | `https://raw.githubusercontent.com/dcsl88814-crypto/sr-rules/refs/heads/main/rules/proxy.module` |
| `reject.module` | REJECT | `https://cdn.jsdelivr.net/gh/dcsl88814-crypto/sr-rules@main/rules/reject.module` | `https://raw.githubusercontent.com/dcsl88814-crypto/sr-rules/refs/heads/main/rules/reject.module` |
| `private.module` | DIRECT | `https://cdn.jsdelivr.net/gh/dcsl88814-crypto/sr-rules@main/rules/private.module` | `https://raw.githubusercontent.com/dcsl88814-crypto/sr-rules/refs/heads/main/rules/private.module` |
| `apple.module` | DIRECT | `https://cdn.jsdelivr.net/gh/dcsl88814-crypto/sr-rules@main/rules/apple.module` | `https://raw.githubusercontent.com/dcsl88814-crypto/sr-rules/refs/heads/main/rules/apple.module` |
| `icloud.module` | DIRECT | `https://cdn.jsdelivr.net/gh/dcsl88814-crypto/sr-rules@main/rules/icloud.module` | `https://raw.githubusercontent.com/dcsl88814-crypto/sr-rules/refs/heads/main/rules/icloud.module` |
| `google.module` | DIRECT | `https://cdn.jsdelivr.net/gh/dcsl88814-crypto/sr-rules@main/rules/google.module` | `https://raw.githubusercontent.com/dcsl88814-crypto/sr-rules/refs/heads/main/rules/google.module` |
| `gfw.module` | PROXY | `https://cdn.jsdelivr.net/gh/dcsl88814-crypto/sr-rules@main/rules/gfw.module` | `https://raw.githubusercontent.com/dcsl88814-crypto/sr-rules/refs/heads/main/rules/gfw.module` |
| `tld-not-cn.module` | PROXY | `https://cdn.jsdelivr.net/gh/dcsl88814-crypto/sr-rules@main/rules/tld-not-cn.module` | `https://raw.githubusercontent.com/dcsl88814-crypto/sr-rules/refs/heads/main/rules/tld-not-cn.module` |
| `telegramcidr.module` | PROXY | `https://cdn.jsdelivr.net/gh/dcsl88814-crypto/sr-rules@main/rules/telegramcidr.module` | `https://raw.githubusercontent.com/dcsl88814-crypto/sr-rules/refs/heads/main/rules/telegramcidr.module` |
| `cncidr.module` | DIRECT | `https://cdn.jsdelivr.net/gh/dcsl88814-crypto/sr-rules@main/rules/cncidr.module` | `https://raw.githubusercontent.com/dcsl88814-crypto/sr-rules/refs/heads/main/rules/cncidr.module` |

## License

本项目采用 [GNU General Public License v3.0](LICENSE)（GPL-3.0）。

Copyright (c) 2026 vycsl-dev

> 注意：本项目仅转换/聚合上游规则。上游规则数据版权归 [Loyalsoldier/surge-rules](https://github.com/Loyalsoldier/surge-rules)（GPL-3.0 License）所有。
