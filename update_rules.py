#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Download Surge rulesets from Loyalsoldier/surge-rules, then generate:

  * Shadowrocket: per-source <name>.module (with #! headers), plus
    merged_direct/proxy/reject/all.module
  * sing-box:     per-source <name>.json (source rule-set format) and
    <name>.srs (binary rule-set, compiled with the official sing-box CLI:
    `sing-box rule-set compile <name>.json -o <name>.srs`)

Features:
- Concurrent downloads with ThreadPoolExecutor
- Automatic retry on transient network failures
- Structured logging with timestamps
"""
from __future__ import annotations

import json
import logging
import os
import re
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

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

# regex
CIDR_RE = re.compile(r'^[0-9a-fA-F\.:]+/\d+$')
IPV4_RE = re.compile(r'^\d{1,3}(\.\d{1,3}){3}$')
ADBLOCK_DOUBLE = re.compile(r'^\|\|([^\/\^]+)(?:\^)?$')
ADBLOCK_EXACT = re.compile(r'^\|?(https?://[^\/\s]+)(/.*)?$')
SCHEME_RE = re.compile(r'^[a-zA-Z0-9+\-.]+://')

def normalize_text(text: str) -> str:
    """Normalize line endings, strip BOM, and remove trailing blank lines."""
    text = text.removeprefix("\ufeff")
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
    line = line.strip()
    if not line or is_comment_or_empty(line):
        return []
    if "," in line:
        parts = [p.strip() for p in line.split(",")]
        t = parts[0].upper()
        v = parts[1] if len(parts) > 1 else ""
        if len(parts) >= 3 and parts[2].strip():
            policy = ",".join(parts[2:])
        else:
            policy = default_policy
        return [f"{t},{v},{policy}"]
    m = ADBLOCK_DOUBLE.match(line)
    if m:
        domain = m.group(1).strip()
        if domain:
            return [f"DOMAIN-SUFFIX,{domain},{default_policy}"]
    m2 = ADBLOCK_EXACT.match(line)
    if m2:
        host = m2.group(1)
        path = m2.group(2) or ""
        pattern = "^" + re.escape(host + path) + ".*"
        return [f"URL-REGEX,{pattern},{default_policy}"]
    if CIDR_RE.match(line):
        return [f"IP-CIDR,{line},{default_policy}"]
    if IPV4_RE.match(line):
        return [f"IP-CIDR,{line}/32,{default_policy}"]
    if "*" in line:
        kw = line.replace("*", "").strip()
        if kw:
            return [f"DOMAIN-KEYWORD,{kw},{default_policy}"]
    if SCHEME_RE.match(line) or "/" in line or line.startswith("www."):
        tmp = SCHEME_RE.sub("", line)
        host = tmp.split("/")[0].split(":")[0]
        if host:
            return [f"DOMAIN-SUFFIX,{host},{default_policy}"]
    cleaned = line.lstrip("*.")
    if cleaned:
        return [f"DOMAIN-SUFFIX,{cleaned},{default_policy}"]
    return []

def _build_session() -> requests.Session:
    """Create a requests Session with retry logic."""
    retry_strategy = Retry(
        total=3,
        backoff_factor=2,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session = requests.Session()
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update({
        "User-Agent": "sr-rules-updater/1.0 (+https://github.com/sr-rules)",
    })
    return session


def fetch_text(session: requests.Session, url: str) -> str:
    """Download a URL with retry and return decoded text."""
    log.info("Fetching %s ...", url)
    r = session.get(url, timeout=(10, 30))
    r.raise_for_status()
    r.encoding = "utf-8"
    return r.text

def detect_repo_vars():
    owner = os.getenv("OWNER") or os.getenv("GITHUB_REPOSITORY_OWNER") or ""
    repo_env = os.getenv("REPO") or os.getenv("GITHUB_REPOSITORY") or ""
    repo = ""
    if repo_env:
        if "/" in repo_env:
            parts = repo_env.split("/", 1)
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
        "",
        "[Rule]",
        ""
    ]
    content = "\n".join(header + rules) + ("\n" if rules else "\n")
    module_path.write_text(content, encoding="utf-8")
    log.info("Saved %s (%d rules)", module_path, len(rules))
    return module_path

def classify_policy(policy: str) -> str:
    p = policy.strip().upper()
    if p.startswith("DIRECT"):
        return "DIRECT"
    if p.startswith("PROXY"):
        return "PROXY"
    if p.startswith("REJECT"):
        return "REJECT"
    return "OTHER"

# ---------------------------------------------------------------------------
# sing-box rule-set generation
#
# JSON source format (https://sing-box.sagernet.org/configuration/rule-set/source-format/):
#   {"version": 1, "rules": [{"domain": [...]}, {"domain_suffix": [...]}, ...]}
# Note: multiple fields inside ONE headless rule are ANDed, so each matcher
# type must live in its own rule object. The binary .srs is produced by the
# official CLI, not hand-rolled, because the domain matcher uses a succinct
# set that is impractical to reimplement.
# ---------------------------------------------------------------------------
SINGBOX_RULESET_VERSION = 1

def build_singbox_ruleset(rules: list) -> dict:
    """Group converted module rule strings into sing-box headless rules."""
    categories = {
        "domain": [],
        "domain_suffix": [],
        "domain_keyword": [],
        "domain_regex": [],
        "ip_cidr": [],
    }
    seen = {key: set() for key in categories}
    for line in rules:
        parts = line.split(",")
        if len(parts) < 2:
            continue
        rule_type = parts[0].strip().upper()
        value = parts[1].strip()
        if not value:
            continue
        if rule_type == "DOMAIN":
            key = "domain"
        elif rule_type == "DOMAIN-SUFFIX":
            key = "domain_suffix"
        elif rule_type == "DOMAIN-KEYWORD":
            key = "domain_keyword"
        elif rule_type == "URL-REGEX":
            # Best effort: sing-box domain_regex only matches the domain part.
            key = "domain_regex"
        elif rule_type in ("IP-CIDR", "IP-CIDR6"):
            key = "ip_cidr"
        else:
            continue
        if value not in seen[key]:
            seen[key].add(value)
            categories[key].append(value)
    ruleset = {
        "version": SINGBOX_RULESET_VERSION,
        "rules": [{key: values} for key, values in categories.items() if values],
    }
    return ruleset

def write_singbox_files(name: str, rules: list, out_dir: Path):
    """Write <name>.json rule-set and compile <name>.srs with sing-box CLI."""
    json_path = out_dir / name.replace(".txt", ".json")
    srs_path = out_dir / name.replace(".txt", ".srs")
    data = build_singbox_ruleset(rules)
    json_path.write_text(
        json.dumps(data, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    count = sum(len(values) for rule in data["rules"] for values in rule.values())
    log.info("Saved %s (%d sing-box rules)", json_path, count)

    singbox_bin = shutil.which("sing-box")
    if not singbox_bin:
        log.warning(
            "sing-box binary not found in PATH, skipping %s (install it to "
            "enable SRS compilation, see .github/workflows/update_rules.yml)",
            srs_path,
        )
        return
    result = subprocess.run(
        [singbox_bin, "rule-set", "compile", str(json_path), "-o", str(srs_path)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        log.error("sing-box compile failed for %s: %s", srs_path, result.stderr.strip())
        return
    log.info("Saved %s (%d bytes)", srs_path, srs_path.stat().st_size)

def main() -> None:
    owner, repo, branch = detect_repo_vars()
    log.info("OWNER=%s REPO=%s BRANCH=%s", owner, repo, branch)

    session = _build_session()
    all_results: dict[str, tuple[list[str], str | None]] = {}  # name -> (rules, error_message)

    # ------------------------------------------------------------------
    # Phase 1: concurrent download & conversion
    # ------------------------------------------------------------------
    def _fetch_and_convert(name: str, url: str) -> tuple[str, list[str], str | None]:
        """Worker: download one source and convert. Returns (name, rules, error)."""
        default_policy = DEFAULT_POLICY.get(name, "DIRECT")
        try:
            raw_text = fetch_text(session, url)
        except Exception as exc:
            log.warning("Failed to fetch %s: %s", name, exc)
            return (name, [], str(exc))

        raw_text = normalize_text(raw_text)
        rules: list[str] = []
        seen: set[str] = set()
        for ln in raw_text.splitlines():
            try:
                conv = convert_line(ln, default_policy)
            except Exception as exc:
                log.debug("Convert error in %s for line %r: %s", name, ln, exc)
                conv = []
            for c in conv:
                cnorm = re.sub(r"\s*,\s*", ",", c).strip()
                if cnorm not in seen:
                    seen.add(cnorm)
                    rules.append(cnorm)
        return (name, rules, None)

    max_workers = min(8, len(SOURCES))
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(_fetch_and_convert, name, url): name
            for name, url in SOURCES.items()
        }
        for future in as_completed(futures):
            name, rules, err = future.result()
            all_results[name] = (rules, err)

    # ------------------------------------------------------------------
    # Phase 2: merge & classify (single-threaded, deterministic order)
    # ------------------------------------------------------------------
    merged_all: list[str] = []
    merged_set: set[str] = set()
    groups: dict[str, list[str]] = {"DIRECT": [], "PROXY": [], "REJECT": [], "OTHER": []}
    group_sets: dict[str, set[str]] = {k: set() for k in groups}

    for name in SOURCES:  # preserve deterministic order
        rules, err = all_results.get(name, ([], "not processed"))
        if err:
            log.warning("Skipping %s due to fetch error: %s", name, err)
            continue
        for cnorm in rules:
            if cnorm not in merged_set:
                merged_set.add(cnorm)
                merged_all.append(cnorm)
            parts = cnorm.rsplit(",", 1)
            policy = parts[-1] if len(parts) > 1 else ""
            cls = classify_policy(policy)
            if cnorm not in group_sets[cls]:
                group_sets[cls].add(cnorm)
                groups[cls].append(cnorm)

        hosted_url = (
            f"https://cdn.jsdelivr.net/gh/{owner}/{repo}@{branch}"
            f"/rules/{name.replace('.txt', '.module')}"
        )
        friendly_name, desc = META.get(name, (name, ""))
        write_module_file(name, hosted_url, friendly_name, desc, rules)

        # sing-box rule sets (json + compiled srs)
        write_singbox_files(name, rules, OUT_DIR)

    # ------------------------------------------------------------------
    # Phase 3: write merged modules
    # ------------------------------------------------------------------
    base = f"https://cdn.jsdelivr.net/gh/{owner}/{repo}@{branch}/rules"
    write_module_file("merged_direct.txt", f"{base}/merged_direct.module", "Merged Direct", "合并: DIRECT 规则", groups["DIRECT"])
    write_module_file("merged_proxy.txt", f"{base}/merged_proxy.module", "Merged Proxy", "合并: PROXY 规则", groups["PROXY"])
    write_module_file("merged_reject.txt", f"{base}/merged_reject.module", "Merged Reject", "合并: REJECT 规则", groups["REJECT"])
    write_module_file("merged_all.txt", f"{base}/merged_all.module", "Merged All", "合并: 所有策略规则（去重）", merged_all)

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    total_rules = sum(
        len(rules) for rules, err in all_results.values() if err is None
    )
    srs_count = len(list(OUT_DIR.glob("*.srs")))
    log.info(
        "Done. %d sources processed, %d total rules (pre-merge), %d unique merged, "
        "%d sing-box .srs rule sets.",
        sum(1 for _, err in all_results.values() if err is None),
        total_rules,
        len(merged_all),
        srs_count,
    )

if __name__ == "__main__":
    start = time.monotonic()
    try:
        main()
    except KeyboardInterrupt:
        log.warning("Interrupted by user")
        sys.exit(130)
    except Exception:
        log.exception("Fatal error")
        sys.exit(1)
    else:
        elapsed = time.monotonic() - start
        log.info("Total elapsed: %.1fs", elapsed)
