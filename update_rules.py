#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Download multiple Surge rulesets, convert to Surge/Shadowrocket-compatible rules,
write per-source <name>.module (with #! headers), plus merged_rules.module and example.conf.

All #!url and example.conf:update-url point to this repository's raw.githubusercontent.com URL
(OWNER/REPO/BRANCH are read from env or GITHUB_* vars).
This version DOES NOT save raw_<name> files.
"""
from pathlib import Path
from datetime import datetime
import os
import re
import requests

# ========== SOURCES (外部来源，仅用于抓取原始内容) ==========
SOURCES = {
    "direct.txt": "https://raw.githubusercontent.com/Loyalsoldier/surge-rules/release/ruleset/direct.txt",
    "proxy.txt":  "https://raw.githubusercontent.com/Loyalsoldier/surge-rules/release/ruleset/proxy.txt",
    "reject.txt": "https://raw.githubusercontent.com/Loyalsoldier/surge-rules/release/ruleset/reject.txt",
    "private.txt":"https://raw.githubusercontent.com/Loyalsoldier/surge-rules/release/ruleset/private.txt",
    "apple.txt":  "https://raw.githubusercontent.com/Loyalsoldier/surge-rules/release/ruleset/apple.txt",
    "icloud.txt": "https://raw.githubusercontent.com/Loyalsoldier/surge-rules/release/ruleset/icloud.txt",
    "google.txt": "https://raw.githubusercontent.com/Loyalsoldier/surge-rules/release/ruleset/google.txt",
    "gfw.txt":    "https://raw.githubusercontent.com/Loyalsoldier/surge-rules/release/ruleset/gfw.txt",
    "tld-not-cn.txt": "https://raw.githubusercontent.com/Loyalsoldier/surge-rules/release/ruleset/tld-not-cn.txt",
    "telegramcidr.txt":"https://raw.githubusercontent.com/Loyalsoldier/surge-rules/release/ruleset/telegramcidr.txt",
    "cncidr.txt": "https://raw.githubusercontent.com/Loyalsoldier/surge-rules/release/ruleset/cncidr.txt",
}

# 默认策略（当原行没有指定策略时使用）
DEFAULT_POLICY = {
    "direct.txt": "DIRECT",
    "proxy.txt":  "PROXY",
    "reject.txt": "REJECT",
    "private.txt":"DIRECT",
    "apple.txt":  "DIRECT",
    "icloud.txt": "DIRECT",
    "google.txt": "DIRECT",
    "gfw.txt":    "PROXY",
    "tld-not-cn.txt": "PROXY",
    "telegramcidr.txt":"PROXY",
    "cncidr.txt": "DIRECT",
}

# 友好名称和描述（写入 #!name/#!desc）
META = {
    "direct.txt": ("Direct", "直连域名列表"),
    "proxy.txt": ("Proxy", "代理域名列表"),
    "reject.txt": ("Reject", "广告/拦截域名列表"),
    "private.txt":("Private", "私有网络专用域名列表"),
    "apple.txt": ("Apple", "Apple 在中国大陆可直连的域名列表"),
    "icloud.txt":("iCloud", "iCloud 域名列表"),
    "google.txt":("Google", "[慎用] Google 在中国大陆可直连的域名列表"),
    "gfw.txt": ("GFW", "GFWList 域名列表"),
    "tld-not-cn.txt":("TLD-Not-CN", "非中国大陆使用的顶级域名列表"),
    "telegramcidr.txt":("TelegramCIDR", "Telegram 使用的 IP 地址列表"),
    "cncidr.txt": ("CNCIDR", "中国大陆 IP 地址列表"),
}

OUT_DIR = Path("rules")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ========== regex helpers ==========
CIDR_RE = re.compile(r'^[0-9a-fA-F\.:]+/\d+$')
IPV4_RE = re.compile(r'^\d{1,3}(\.\d{1,3}){3}$')
ADBLOCK_DOUBLE = re.compile(r'^\|\|([^\/\^]+)(?:\^)?$')
ADBLOCK_EXACT = re.compile(r'^\|?(https?://[^\/\s]+)(/.*)?$')
SCHEME_RE = re.compile(r'^[a-zA-Z0-9+\-.]+://')

def normalize_text(text: str) -> str:
    if text.startswith("\ufeff"):
        text = text.lstrip("\ufeff")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [ln.rstrip() for ln in text.split("\n")]
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines) + ("\n" if lines else "")

def is_comment_or_empty(line: str) -> bool:
    if not line:
        return True
    return line.startswith("#") or line.startswith("!") or line.startswith("//") or line.startswith(";")

def convert_line(line: str, default_policy: str):
    """ Convert one input line to 0..n Surge-style lines """
    line = line.strip()
    if not line or is_comment_or_empty(line):
        return []
    # Already comma-separated (Surge-like)
    if "," in line:
        parts = [p.strip() for p in line.split(",")]
        t = parts[0].upper()
        v = parts[1] if len(parts) > 1 else ""
        if len(parts) >= 3 and parts[2].strip():
            policy = ",".join(parts[2:])
        else:
            policy = default_policy
        return [f"{t},{v},{policy}"]
    # adblock ||domain^
    m = ADBLOCK_DOUBLE.match(line)
    if m:
        domain = m.group(1).strip()
        if domain:
            return [f"DOMAIN-SUFFIX,{domain},{default_policy}"]
    # exact url or |http...
    m2 = ADBLOCK_EXACT.match(line)
    if m2:
        host = m2.group(1)
        path = m2.group(2) or ""
        pattern = re.escape(host + path) + ".*"
        return [f"URL-REGEX,{pattern},{default_policy}"]
    # CIDR / IPv6
    if CIDR_RE.match(line):
        return [f"IP-CIDR,{line},{default_policy}"]
    # IPv4 single
    if IPV4_RE.match(line):
        return [f"IP-CIDR,{line}/32,{default_policy}"]
    # wildcard -> keyword
    if "*" in line:
        kw = line.replace("*", "").strip()
        if kw:
            return [f"DOMAIN-KEYWORD,{kw},{default_policy}"]
    # contains scheme or path -> extract hostname
    if SCHEME_RE.match(line) or "/" in line or line.startswith("www."):
        tmp = SCHEME_RE.sub("", line)
        host = tmp.split("/")[0].split(":")[0]
        if host:
            return [f"DOMAIN-SUFFIX,{host},{default_policy}"]
    cleaned = line.lstrip("*.")
    if cleaned:
        return [f"DOMAIN-SUFFIX,{cleaned},{default_policy}"]
    return []

def fetch_text(url: str) -> str:
    print(f"Fetching {url} ...")
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return r.text

def detect_repo_vars():
    # Priority: explicit env OWNER/REPO/BRANCH > GITHUB_* vars > placeholders
    owner = os.getenv("OWNER") or os.getenv("GITHUB_REPOSITORY_OWNER") or ""
    repo_env = os.getenv("REPO") or os.getenv("GITHUB_REPOSITORY") or ""
    repo = ""
    if repo_env:
        if "/" in repo_env:
            parts = repo_env.split("/", 1)
            # repo_env may be "owner/repo"
            if not owner:
                owner = parts[0]
            repo = parts[1]
        else:
            repo = repo_env
    if not repo:
        repo = os.getenv("GITHUB_REPOSITORY","").split("/")[-1] or ""
    branch = os.getenv("BRANCH") or os.getenv("GITHUB_REF_NAME") or ""
    if not branch:
        gref = os.getenv("GITHUB_REF") or ""
        if gref.startswith("refs/heads/"):
            branch = gref.split("/", 2)[-1]
    if not owner:
        owner = "<OWNER>"
    if not repo:
        repo = "<REPO>"
    if not branch:
        branch = "main"
    return owner, repo, branch

def write_module_file(name: str, url_hosted: str, friendly_name: str, desc: str, rules: list):
    module_path = OUT_DIR / (name.replace(".txt", ".module"))
    header = [
        f"#!url={url_hosted}",
        f"#!name={friendly_name}",
        f"#!desc={desc}",
        ""
    ]
    content = "\n".join(header + rules) + ("\n" if rules else "\n")
    module_path.write_text(content, encoding="utf-8")
    print(f"Saved module: {module_path} ({len(rules)} rules)")
    return module_path

def generate_example_conf(merged_url: str):
    tpl = f"""# Shadowrocket: {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")}
[General]
update-url = {merged_url}
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

# Rule Sets

# LAN
IP-CIDR,192.168.0.0/16,DIRECT
IP-CIDR,10.0.0.0/8,DIRECT
IP-CIDR,172.16.0.0/12,DIRECT
IP-CIDR,127.0.0.0/8,DIRECT

# China
GEOIP,CN,DIRECT

# Final
FINAL,PROXY
"""
    path = Path("example.conf")
    path.write_text(tpl, encoding="utf-8")
    print(f"Saved {path}")

def main():
    owner, repo, branch = detect_repo_vars()
    print(f"Using OWNER={owner} REPO={repo} BRANCH={branch}")

    merged = []
    merged_set = set()

    for name, url in SOURCES.items():
        default_policy = DEFAULT_POLICY.get(name, "DIRECT")
        try:
            raw_text = fetch_text(url)
        except Exception as e:
            print(f"Failed to fetch {url}: {e}")
            continue
        raw_text = normalize_text(raw_text)

        rules = []
        seen = set()
        for ln in raw_text.splitlines():
            try:
                conv = convert_line(ln, default_policy)
            except Exception as e:
                print(f"convert error for line {ln!r}: {e}")
                conv = []
            for c in conv:
                cnorm = re.sub(r'\s*,\s*', ',', c).strip()
                if cnorm not in seen:
                    seen.add(cnorm)
                    rules.append(cnorm)
                    if cnorm not in merged_set:
                        merged_set.add(cnorm)
                        merged.append(cnorm)

        # hosted_url MUST point to this repo's raw path
        hosted_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/rules/{name.replace('.txt','.module')}"
        friendly_name, desc = META.get(name, (name, ""))
        write_module_file(name, hosted_url, friendly_name, desc, rules)

    # write merged module (hosted in this repo)
    merged_hosted_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/rules/merged_rules.module"
    write_module_file("merged_rules.txt", merged_hosted_url, "Merged Rules", "合并去重后的规则（自动生成）", merged)

    # write example.conf pointing to merged module hosted url (this repo)
    generate_example_conf(merged_hosted_url)

    print("Done.")

if __name__ == "__main__":
    main()
