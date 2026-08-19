# rules-sync

[![Update Rules](https://github.com/dcsl88814-crypto/rules-sync/actions/workflows/update_rules.yml/badge.svg)](https://github.com/dcsl88814-crypto/rules-sync/actions/workflows/update_rules.yml)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)

> 每日自动将 [Loyalsoldier/surge-rules](https://github.com/Loyalsoldier/surge-rules) 的规则转换为 **sing-box** 可订阅的 `.srs` 二进制规则集。规则内容完全来自上游，本项目只做格式转换。

> 使用 Shadowrocket？请切换到 [module 分支](https://github.com/dcsl88814-crypto/rules-sync/tree/module)。

---

## 规则集

| 文件 | 内容 | 建议策略 |
|------|------|---------|
| `direct` | 直连域名 | 直连 |
| `proxy` | 代理域名 | 代理 |
| `reject` | 广告 / 恶意域名 | 拦截 |
| `gfw` | GFWList 域名 | 代理 |
| `tld-not-cn` | 非中国大陆顶级域名 | 代理 |
| `cncidr` | 中国大陆 IP | 直连 |
| `telegramcidr` | Telegram IP | 代理 |
| `private` | 私有网络域名 | 直连 |
| `apple` | Apple 可直连域名 | 直连 |
| `icloud` | iCloud 域名 | 直连 |
| `google` | Google 可直连域名（慎用） | 直连 |

每个规则集同时提供 `.srs`（二进制，推荐）和 `.json`（源格式）两个文件：

```
https://cdn.jsdelivr.net/gh/dcsl88814-crypto/rules-sync@srs/rules/<name>.srs
```

---

## 使用

在配置的 `route.rule_set` 中引用（URL 以 `.srs` 结尾时自动识别为二进制格式，`format` 可省略）：

```json
{
  "route": {
    "rule_set": [
      { "type": "remote", "tag": "reject", "url": "https://cdn.jsdelivr.net/gh/dcsl88814-crypto/rules-sync@srs/rules/reject.srs", "update_interval": "1d" },
      { "type": "remote", "tag": "direct", "url": "https://cdn.jsdelivr.net/gh/dcsl88814-crypto/rules-sync@srs/rules/direct.srs", "update_interval": "1d" },
      { "type": "remote", "tag": "proxy",  "url": "https://cdn.jsdelivr.net/gh/dcsl88814-crypto/rules-sync@srs/rules/proxy.srs",  "update_interval": "1d" }
    ],
    "rules": [
      { "rule_set": ["reject"], "action": "reject" },
      { "rule_set": ["direct"], "outbound": "direct" },
      { "rule_set": ["proxy", "gfw", "tld-not-cn"], "outbound": "proxy" }
    ]
  }
}
```

---

## 更新

GitHub Actions 每日 02:00 UTC 自动拉取上游规则，用官方 `sing-box rule-set compile` 编译出 `.srs`；也可在 Actions 页面手动触发。

## 部署到自己的仓库

1. Fork 本仓库的 `srs` 分支并启用 Actions


## License

[GPL v3](LICENSE)。规则数据版权归 [Loyalsoldier/surge-rules](https://github.com/Loyalsoldier/surge-rules) 所有。
