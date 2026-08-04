# sr-rules

Shadowrocket / Surge 规则模块管理仓库。自动从 [Loyalsoldier/surge-rules](https://github.com/Loyalsoldier/surge-rules) 拉取规则源，转换成 Shadowrocket 兼容的 `.module` 模块，并按策略拆分合并，方便直接订阅使用。

## 规则来源与致谢

所有规则数据均来自 **Loyalsoldier** 的 [surge-rules](https://github.com/Loyalsoldier/surge-rules) 项目（MIT License），感谢他长期维护高质量规则集。本仓库只负责抓取、转换与自动更新，规则内容的所有权与版权归原作者所有。

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

### 方式一：订阅模块（推荐，自动更新）

1. 打开 Shadowrocket，进入 **配置 (Config)** 页，点击右上角 **+**，选择 **添加模块 (Add Module)**。
2. 粘贴模块订阅 URL（jsDelivr CDN，国内可直连；若需绕过 CDN 缓存，可在 URL 末尾加 `?v=日期`，或改用下方 raw 链接）：
   - 全部规则（去重合并）：`https://cdn.jsdelivr.net/gh/dcsl88814-crypto/sr-rules@main/rules/merged_all.module`
   - 仅直连：`https://cdn.jsdelivr.net/gh/dcsl88814-crypto/sr-rules@main/rules/merged_direct.module`
   - 仅代理：`https://cdn.jsdelivr.net/gh/dcsl88814-crypto/sr-rules@main/rules/merged_proxy.module`
   - 仅拦截：`https://cdn.jsdelivr.net/gh/dcsl88814-crypto/sr-rules@main/rules/merged_reject.module`
3. 添加后可手动更新，或等仓库的 Actions 每天 02:00 UTC 自动更新规则后下拉刷新。

> 提示：`merged_all.module` 包含全部规则（直连/代理/拦截去重合并），普通用户订阅这一个即可。
>
> 备用（GitHub raw，需能访问 GitHub）：`https://raw.githubusercontent.com/dcsl88814-crypto/sr-rules/refs/heads/main/rules/merged_all.module`（其余文件同理，把文件名替换为 `merged_direct` / `merged_proxy` / `merged_reject`）。

### 方式二：导入示例配置

1. 打开 `examples/example.conf`。
2. 把文件保存为 `example.conf`，用 Shadowrocket 打开即可导入。
3. 导入后，Shadowrocket 会按 `update-url` 定时拉取最新的配置，规则则由各 `RULE-SET` 模块按需加载更新。

### 示例配置

```conf
[General]
update-url = https://cdn.jsdelivr.net/gh/dcsl88814-crypto/sr-rules@main/examples/example.conf
bypass-system = true
skip-proxy = 192.168.0.0/16, 10.0.0.0/8, 172.16.0.0/12, localhost, *.local, captive.apple.com
tun-excluded-routes = 10.0.0.0/8, 100.64.0.0/10, 127.0.0.0/8, 169.254.0.0/16, 172.16.0.0/12, 192.0.0.0/24, 192.0.2.0/24, 192.88.99.0/24, 192.168.0.0/16, 198.51.100.0/24, 203.0.113.0/24, 224.0.0.0/4, 255.255.255.255/32, 239.255.255.250/32, ff02::fb/128
dns-server = https://cloudflare-dns.com/dns-query, https://dns.google/dns-query
fallback-dns-server = https://dns.alidns.com/dns-query

# Enable full IPv6 support
ipv6 = false
prefer-ipv6 = false

# If a domain uses the direct policy, after enabling this, Shadowrocket will use the system DNS to resolve it.
dns-direct-system = false

# If true, Shadowrocket will automatically reply to ICMP packets.
icmp-auto-reply = true

# If true, Shadowrocket always executes reject urlrewrite rules even though the global routing is not config.
always-reject-url-rewrite = false

# If false, the domain resolution returns a private IP and Shadowrocket assumes that the domain is hijacked and forces the use of a proxy.
private-ip-answer = false

# If a domain uses the direct policy, automatically switch to the proxy rule if direct DNS resolution fails.
dns-direct-fallback-proxy = false

# The fallback behavior when UDP traffic matches a policy that doesn't support the UDP relay. Possible values: DIRECT, REJECT.
udp-policy-not-supported-behaviour = REJECT

# By default, DNS lookup is always performed on the remote server with a proxy policy.
# If true, Shadowrocket will use the mapped address for the proxy connection instead of the host if a local DNS mapping exists.
use-local-host-item-for-proxy = false

[Rule]
# Block HTTP3/QUIC
AND,((PROTOCOL,UDP),(DEST-PORT,443)),REJECT-NO-DROP

# Rule Sets (individual modules from rules/)
RULE-SET,https://cdn.jsdelivr.net/gh/dcsl88814-crypto/sr-rules@main/rules/direct.module,DIRECT
RULE-SET,https://cdn.jsdelivr.net/gh/dcsl88814-crypto/sr-rules@main/rules/proxy.module,PROXY
RULE-SET,https://cdn.jsdelivr.net/gh/dcsl88814-crypto/sr-rules@main/rules/reject.module,REJECT
RULE-SET,https://cdn.jsdelivr.net/gh/dcsl88814-crypto/sr-rules@main/rules/private.module,DIRECT
RULE-SET,https://cdn.jsdelivr.net/gh/dcsl88814-crypto/sr-rules@main/rules/apple.module,DIRECT
RULE-SET,https://cdn.jsdelivr.net/gh/dcsl88814-crypto/sr-rules@main/rules/icloud.module,DIRECT
RULE-SET,https://cdn.jsdelivr.net/gh/dcsl88814-crypto/sr-rules@main/rules/google.module,DIRECT
RULE-SET,https://cdn.jsdelivr.net/gh/dcsl88814-crypto/sr-rules@main/rules/gfw.module,PROXY
RULE-SET,https://cdn.jsdelivr.net/gh/dcsl88814-crypto/sr-rules@main/rules/tld-not-cn.module,PROXY
RULE-SET,https://cdn.jsdelivr.net/gh/dcsl88814-crypto/sr-rules@main/rules/telegramcidr.module,PROXY
RULE-SET,https://cdn.jsdelivr.net/gh/dcsl88814-crypto/sr-rules@main/rules/cncidr.module,DIRECT

# LAN
IP-CIDR,192.168.0.0/16,DIRECT
IP-CIDR,10.0.0.0/8,DIRECT
IP-CIDR,172.16.0.0/12,DIRECT
IP-CIDR,127.0.0.0/8,DIRECT

# China
GEOIP,CN,DIRECT

# Final
FINAL,PROXY
```

## License

本项目采用 [MIT License](LICENSE)。

Copyright (c) 2026 vycsl-dev

> 注意：本项目仅转换/聚合上游规则。上游规则数据版权归 [Loyalsoldier/surge-rules](https://github.com/Loyalsoldier/surge-rules)（MIT License）所有。
