# rules-sync

[![Update Rules](https://github.com/dcsl88814-crypto/sr-rules/actions/workflows/update_rules.yml/badge.svg)](https://github.com/dcsl88814-crypto/sr-rules/actions/workflows/update_rules.yml)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)

> 每日自动将 [Loyalsoldier/surge-rules](https://github.com/Loyalsoldier/surge-rules) 的规则转换为 **Shadowrocket** 可订阅的 `.module` 模块，规则内容完全来自上游，本项目只做格式转换。

> 使用 sing-box？请切换到 [srs 分支](https://github.com/dcsl88814-crypto/sr-rules/tree/srs)。

---

## 使用

Shadowrocket 中：**配置 → 添加模块**，粘贴以下链接即可订阅全部规则：

```
https://cdn.jsdelivr.net/gh/dcsl88814-crypto/sr-rules@module/rules/merged_all.module
```

如只需单个规则集，可单独订阅（完整列表见 [rules/](https://github.com/dcsl88814-crypto/sr-rules/tree/module/rules)）：

```
https://cdn.jsdelivr.net/gh/dcsl88814-crypto/sr-rules@module/rules/direct.module   # 直连
https://cdn.jsdelivr.net/gh/dcsl88814-crypto/sr-rules@module/rules/proxy.module    # 代理
https://cdn.jsdelivr.net/gh/dcsl88814-crypto/sr-rules@module/rules/reject.module   # 拦截
```

---

## 更新

GitHub Actions 每日 02:00 UTC 自动拉取上游规则并重新生成；也可在 Actions 页面手动触发。

## License

[GPL v3](LICENSE)。规则数据版权归 [Loyalsoldier/surge-rules](https://github.com/Loyalsoldier/surge-rules) 所有。
