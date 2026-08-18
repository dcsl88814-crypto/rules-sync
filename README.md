# sr-rules

[![Update Rules](https://github.com/dcsl88814-crypto/sr-rules/actions/workflows/update_rules.yml/badge.svg)](https://github.com/dcsl88814-crypto/sr-rules/actions/workflows/update_rules.yml)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)

> 每日自动将 [Loyalsoldier/surge-rules](https://github.com/Loyalsoldier/surge-rules) 的规则转换为 **sing-box**（`.srs`）和 **Shadowrocket**（`.module`）可订阅格式。规则内容完全来自上游，本项目只做格式转换。

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

每个规则集同时提供 `.srs` 和 `.module` 两种格式：

```
https://cdn.jsdelivr.net/gh/dcsl88814-crypto/sr-rules@main/rules/<name>.<srs|module>
```

---

## sing-box 使用

在配置的 `route.rule_set` 中引用（URL 以 `.srs` 结尾时自动识别为二进制格式，`format` 可省略）：

```json
{
  "route": {
    "rule_set": [
      { "type": "remote", "tag": "reject", "url": "https://cdn.jsdelivr.net/gh/dcsl88814-crypto/sr-rules@main/rules/reject.srs", "update_interval": "1d" },
      { "type": "remote", "tag": "direct", "url": "https://cdn.jsdelivr.net/gh/dcsl88814-crypto/sr-rules@main/rules/direct.srs", "update_interval": "1d" },
      { "type": "remote", "tag": "proxy",  "url": "https://cdn.jsdelivr.net/gh/dcsl88814-crypto/sr-rules@main/rules/proxy.srs",  "update_interval": "1d" }
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

## Shadowrocket 使用

直接添加模块（合并模块，订阅一个即可）：

```
https://cdn.jsdelivr.net/gh/dcsl88814-crypto/sr-rules@main/rules/merged_all.module
```

或导入预设配置模板：

- 白名单：[example_whitelist.conf](https://cdn.jsdelivr.net/gh/dcsl88814-crypto/sr-rules@main/examples/example_whitelist.conf)
- 黑名单：[example_blacklist.conf](https://cdn.jsdelivr.net/gh/dcsl88814-crypto/sr-rules@main/examples/example_blacklist.conf)
- 仅拦截：[only_reject_list.conf](https://cdn.jsdelivr.net/gh/dcsl88814-crypto/sr-rules@main/examples/only_reject_list.conf)

---

## 更新

GitHub Actions 每日 02:00 UTC 自动拉取上游规则并重新生成；也可在 Actions 页面手动触发。

## 部署到自己的仓库

1. Fork 本仓库并启用 Actions
2. 全局替换 `dcsl88814-crypto` 为你的 GitHub 用户名（涉及 `README.md` 和 `examples/*.conf`）

## License

[GPL v3](LICENSE)。规则数据版权归 [Loyalsoldier/surge-rules](https://github.com/Loyalsoldier/surge-rules) 所有。
