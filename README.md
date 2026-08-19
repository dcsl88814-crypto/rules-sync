# rules-sync

> 每日自动将 [Loyalsoldier/surge-rules](https://github.com/Loyalsoldier/surge-rules) 的规则同步为多客户端可订阅格式，规则内容完全来自上游，本项目只做格式转换。

[![module 分支](https://github.com/dcsl88814-crypto/rules-sync/actions/workflows/update_rules.yml/badge.svg?branch=module)](https://github.com/dcsl88814-crypto/rules-sync/actions/workflows/update_rules.yml)
[![srs 分支](https://github.com/dcsl88814-crypto/rules-sync/actions/workflows/update_rules.yml/badge.svg?branch=srs)](https://github.com/dcsl88814-crypto/rules-sync/actions/workflows/update_rules.yml)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)

本项目按分支分发不同格式的规则集，请按客户端选择：

| 分支 | 适用客户端 | 格式 | 快速订阅 |
|------|-----------|------|---------|
| [module](https://github.com/dcsl88814-crypto/rules-sync/tree/module) | Shadowrocket | `.module` | `https://cdn.jsdelivr.net/gh/dcsl88814-crypto/rules-sync@module/rules/merged_all.module` |
| [srs](https://github.com/dcsl88814-crypto/rules-sync/tree/srs) | sing-box | `.srs` / `.json` | `https://cdn.jsdelivr.net/gh/dcsl88814-crypto/rules-sync@srs/rules/direct.srs` |

规则集每日 02:00 UTC 自动更新（各分支的 GitHub Actions 各自维护对应格式）。

## 部署到自己的仓库

1. Fork 本仓库（保留所有分支）
2. 在 module / srs 分支的 README 中替换 `dcsl88814-crypto` 为你的 GitHub 用户名；若仓库改名为 `rules-sync`，同时替换 URL 中的 `sr-rules`
3. 各分支的 Actions 会自动更新对应格式的规则文件

## License

[GPL v3](LICENSE)。规则数据版权归 [Loyalsoldier/surge-rules](https://github.com/Loyalsoldier/surge-rules) 所有。
