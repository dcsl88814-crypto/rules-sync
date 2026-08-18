# rules-sync

[![Update Rules](https://github.com/dcsl88814-crypto/sr-rules/actions/workflows/update_rules.yml/badge.svg)](https://github.com/dcsl88814-crypto/sr-rules/actions/workflows/update_rules.yml)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)

> 每日自动将 [Loyalsoldier/surge-rules](https://github.com/Loyalsoldier/surge-rules) 的规则转换为 **Shadowrocket** 可订阅的 `.module` 模块。规则内容完全来自上游，本项目只做格式转换。

> 使用 sing-box？请切换到 [srs 分支](https://github.com/dcsl88814-crypto/sr-rules/tree/srs)。

---

## 规则模块

| 模块 | 内容 | 策略 |
|------|------|------|
| `direct` | 直连域名 | DIRECT |
| `proxy` | 代理域名 | PROXY |
| `reject` | 广告 / 恶意域名 | REJECT |
| `gfw` | GFWList 域名 | PROXY |
| `tld-not-cn` | 非中国大陆顶级域名 | PROXY |
| `cncidr` | 中国大陆 IP | DIRECT |
| `telegramcidr` | Telegram IP | PROXY |
| `private` | 私有网络域名 | DIRECT |
| `apple` | Apple 可直连域名 | DIRECT |
| `icloud` | iCloud 域名 | DIRECT |
| `google` | Google 可直连域名（慎用） | DIRECT |

模块地址：

```
https://cdn.jsdelivr.net/gh/dcsl88814-crypto/sr-rules@module/rules/<name>.module
```

---

## 使用

**直接添加合并模块**（订阅一个即可，含全部策略规则）：

```
https://cdn.jsdelivr.net/gh/dcsl88814-crypto/sr-rules@module/rules/merged_all.module
```

**或导入预设配置模板**：

- 白名单：[example_whitelist.conf](https://cdn.jsdelivr.net/gh/dcsl88814-crypto/sr-rules@module/examples/example_whitelist.conf)
- 黑名单：[example_blacklist.conf](https://cdn.jsdelivr.net/gh/dcsl88814-crypto/sr-rules@module/examples/example_blacklist.conf)
- 仅拦截：[only_reject_list.conf](https://cdn.jsdelivr.net/gh/dcsl88814-crypto/sr-rules@module/examples/only_reject_list.conf)

---

## 更新

GitHub Actions 每日 02:00 UTC 自动拉取上游规则并重新生成；也可在 Actions 页面手动触发。

## 部署到自己的仓库

1. Fork 本仓库的 `module` 分支并启用 Actions
2. 全局替换 `dcsl88814-crypto` 为你的 GitHub 用户名（涉及 `README.md` 和 `examples/*.conf`）；若 GitHub 仓库已改名为 `rules-sync`，同时替换 URL 中的 `sr-rules`

## License

[GPL v3](LICENSE)。规则数据版权归 [Loyalsoldier/surge-rules](https://github.com/Loyalsoldier/surge-rules) 所有。
