# sr-rules

[![Update Rules](https://github.com/dcsl88814-crypto/sr-rules/actions/workflows/update_rules.yml/badge.svg)](https://github.com/dcsl88814-crypto/sr-rules/actions/workflows/update_rules.yml)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)

> 将 [Loyalsoldier/surge-rules](https://github.com/Loyalsoldier/surge-rules) 的规则集自动转换为 Shadowrocket 可订阅的 `.module` 模块，每日定时同步更新。

---

## 这个项目做了什么？

本项目的规则数据取自 [Loyalsoldier/surge-rules](https://github.com/Loyalsoldier/surge-rules)，其规则格式为 **Surge** 原生语法。本项目的定位是一个**格式适配层**，为 Shadowrocket 用户提供即用的订阅体验：

| 本项目提供 | 说明 |
|-----------|------|
| **格式转换** | 将上游 Surge 语法规则转为 Shadowrocket 兼容的 `DOMAIN-SUFFIX` / `IP-CIDR` / `URL-REGEX` 等类型 |
| **策略拆分** | 按 DIRECT / PROXY / REJECT 拆分为独立模块，并生成合并模块 |
| **自动更新** | 通过 GitHub Actions 每日 02:00 UTC 自动拉取上游最新规则并重新生成 |
| **配置模板** | 提供白名单、黑名单、仅拦截三种 `.conf` 预设，一键导入 |
| **CDN 分发** | 所有文件通过 jsDelivr CDN 分发，方便各地区用户访问 |

> 本项目的规则内容完全来自上游，不做任何增删修改。如果你使用 Surge 或其他客户端，推荐直接使用 [上游仓库](https://github.com/Loyalsoldier/surge-rules)。

---

## 快速开始

### 方式一：导入配置模板（推荐新手）

三种预设覆盖常见使用场景，在 Shadowrocket 中打开对应链接即可导入：

**白名单模式** — 默认走代理，仅列表中的域名直连

```
https://cdn.jsdelivr.net/gh/dcsl88814-crypto/sr-rules@main/examples/example_whitelist.conf
```

**黑名单模式** — 默认直连，仅列表中的域名走代理/拦截

```
https://cdn.jsdelivr.net/gh/dcsl88814-crypto/sr-rules@main/examples/example_blacklist.conf
```

**仅拦截模式** — 仅拦截广告/恶意域名，其余全部直连

```
https://cdn.jsdelivr.net/gh/dcsl88814-crypto/sr-rules@main/examples/only_reject_list.conf
```

### 方式二：订阅模块（适合自定义配置）

在 Shadowrocket 中：**配置 → 右上角 `+` → 添加模块**，粘贴以下任一链接：

#### 合并模块（订阅一个即可）

> 每个模块一行，点代码块右上角「复制」即可单独复制该 URL。

**merged_all — 包含全部规则（推荐大多数用户）**

```
https://cdn.jsdelivr.net/gh/dcsl88814-crypto/sr-rules@main/rules/merged_all.module
```

**merged_direct — 仅直连**

```
https://cdn.jsdelivr.net/gh/dcsl88814-crypto/sr-rules@main/rules/merged_direct.module
```

**merged_proxy — 仅代理**

```
https://cdn.jsdelivr.net/gh/dcsl88814-crypto/sr-rules@main/rules/merged_proxy.module
```

**merged_reject — 仅拦截**

```
https://cdn.jsdelivr.net/gh/dcsl88814-crypto/sr-rules@main/rules/merged_reject.module
```

#### 单文件模块（供 `.conf` 中 `RULE-SET` 引用）

> 每个模块一行，点代码块右上角「复制」即可单独复制该 URL。

**DIRECT**

```
https://cdn.jsdelivr.net/gh/dcsl88814-crypto/sr-rules@main/rules/direct.module
```

```
https://cdn.jsdelivr.net/gh/dcsl88814-crypto/sr-rules@main/rules/private.module
```

```
https://cdn.jsdelivr.net/gh/dcsl88814-crypto/sr-rules@main/rules/apple.module
```

```
https://cdn.jsdelivr.net/gh/dcsl88814-crypto/sr-rules@main/rules/icloud.module
```

```
https://cdn.jsdelivr.net/gh/dcsl88814-crypto/sr-rules@main/rules/google.module
```

```
https://cdn.jsdelivr.net/gh/dcsl88814-crypto/sr-rules@main/rules/cncidr.module
```

**PROXY**

```
https://cdn.jsdelivr.net/gh/dcsl88814-crypto/sr-rules@main/rules/proxy.module
```

```
https://cdn.jsdelivr.net/gh/dcsl88814-crypto/sr-rules@main/rules/gfw.module
```

```
https://cdn.jsdelivr.net/gh/dcsl88814-crypto/sr-rules@main/rules/tld-not-cn.module
```

```
https://cdn.jsdelivr.net/gh/dcsl88814-crypto/sr-rules@main/rules/telegramcidr.module
```

**REJECT**

```
https://cdn.jsdelivr.net/gh/dcsl88814-crypto/sr-rules@main/rules/reject.module
```

> **备选**：如 jsDelivr 缓存未及时刷新，可在 URL 末尾加 `?v=YYYYMMDD` 强制绕过缓存；也可将域名替换为 `https://raw.githubusercontent.com/dcsl88814-crypto/sr-rules/refs/heads/main/rules/<file>` 直连 GitHub。

---

## 规则转换逻辑

`update_rules.py` 将上游规则逐行转换为 Shadowrocket 兼容格式：

| 上游格式示例 | 转换后 | 类型 |
|-------------|--------|------|
| `\|\|example.com^` | `DOMAIN-SUFFIX,example.com,POLICY` | 域名通配 |
| `\|http://example.com/path` | `URL-REGEX,^http://example\\.com/path.*,POLICY` | 完整 URL |
| `1.2.3.4/24` | `IP-CIDR,1.2.3.4/24,POLICY` | IP 段 |
| 含 `*` 的域名 | `DOMAIN-KEYWORD,xxx,POLICY` | 关键词 |

---

## 项目结构

```
sr-rules/
├── update_rules.py              # 核心脚本：下载 → 转换 → 输出 .module
├── .github/workflows/           # GitHub Actions 每日自动更新
├── rules/                       # 生成的模块文件（自动更新，勿手动编辑）
│   ├── direct.module            # 单源模块
│   ├── ...
│   ├── merged_all.module        # 合并模块
│   └── merged_reject.module
└── examples/                    # 预设 .conf 配置模板
    ├── example_whitelist.conf
    ├── example_blacklist.conf
    └── only_reject_list.conf
```

---

## Fork 后自行部署

如果你希望在自己的仓库中维护独立副本：

1. **Fork** 本仓库
2. 进入 Settings → Actions → General，确保 Actions 已启用
3. 全局替换 `dcsl88814-crypto` 为你的 GitHub 用户名（涉及 `examples/*.conf` 和 `README.md`）
4. Actions 将每日 02:00 UTC 自动运行，也可在 Actions 页面手动触发

> `update_rules.py` 会自动读取 GitHub 环境变量（`GITHUB_REPOSITORY` 等），无需修改脚本本身。

---

## 规则来源

所有规则数据来自 [@Loyalsoldier](https://github.com/Loyalsoldier) 的 [surge-rules](https://github.com/Loyalsoldier/surge-rules) 项目（GPL-3.0）。感谢该项目长期维护高质量的分流规则。本项目不修改规则内容，仅做格式转换与分发。

---

## License

本项目采用 [GNU General Public License v3.0](LICENSE)。

> 上游规则数据版权归 [Loyalsoldier/surge-rules](https://github.com/Loyalsoldier/surge-rules) 所有。
