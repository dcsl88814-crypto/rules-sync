#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Download Loyalsoldier/domain-list-custom release lists and compile them into
sing-box rule sets:

  * domainlist/<name>.json   (sing-box source rule-set format, version 3)
  * domainlist/<name>.srs    (binary rule-set, compiled with the official
                              sing-box CLI: `sing-box rule-set compile`)

Input format (v2ray geosite text list), one entry per line:

    domain:example.com      -> domain_suffix   (v2ray "domain:" = suffix match)
    full:example.com        -> domain          (exact match)
    keyword:example         -> domain_keyword
    regexp:^...$            -> domain_regex
    domain:example.com:@cn  -> trailing ":@attr" is stripped, attribute ignored

NOTE on scope: this intentionally does NOT build cn / geolocation-cn. Those two
files in domain-list-custom are a customisation layer, not a China list —
verified with the compiled rule set: cn.txt matches only 7/16 mainstream CN
sites (no qq.com, taobao.com, jd.com, weibo.com, bilibili.com, 163.com,
alipay.com). For "cn direct" use the upstream v2fly list
(SagerNet/sing-geosite geosite-cn.srs). geolocation-!cn IS effectively complete
(16/16), and is the main reason to use this pipeline.
"""
from __future__ import annotations

import json
import logging
import os
import re
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

BASE = "https://raw.githubusercontent.com/Loyalsoldier/domain-list-custom/release"

# "!" is percent-encoded in the URL only; output names keep the literal "!".
#
# NOTE: Loyalsoldier's cn / geolocation-cn files are intentionally NOT built.
# They are a customisation layer, not a China list: verified with the compiled
# rule set, cn.txt matches only 7/16 mainstream CN sites (no qq.com, taobao.com,
# jd.com, weibo.com, bilibili.com, 163.com, alipay.com ...). For "cn direct" use
# the upstream v2fly list (SagerNet/sing-geosite geosite-cn.srs) instead.
SOURCES: dict[str, str] = {
    "geolocation-!cn": f"{BASE}/geolocation-%21cn.txt",
    "apple": f"{BASE}/apple.txt",
    "google": f"{BASE}/google.txt",
    "icloud": f"{BASE}/icloud.txt",
    "private": f"{BASE}/private.txt",
    "steam": f"{BASE}/steam.txt",
    "tld-cn": f"{BASE}/tld-cn.txt",
    "tld-!cn": f"{BASE}/tld-%21cn.txt",
    "category-ads-all": f"{BASE}/category-ads-all.txt",
}

OUT_DIR = Path(os.environ.get("OUT_DIR", "domainlist"))

# Optional hand-maintained exception lists, committed in the repo.
# Plain domain per line is treated as a suffix match; v2ray prefixes
# (domain:/full:/regexp:) are also accepted. These are normally filled in
# from connection-log reviews, so they stay tiny (tens of lines).
LOCAL_OVERRIDES: dict[str, Path] = {
    "overrides-direct": Path("overrides/direct.txt"),
    "overrides-proxy": Path("overrides/proxy.txt"),
}

# v2ray list type -> sing-box rule-set field
KEY_OF = {
    "domain": "domain_suffix",
    "full": "domain",
    "keyword": "domain_keyword",
    "regexp": "domain_regex",
}
FIELD_ORDER = ("domain", "domain_suffix", "domain_keyword", "domain_regex")

LINE_RE = re.compile(r"^(domain|full|keyword|regexp|include):(.*)$")
ATTR_RE = re.compile(r"(?::@[A-Za-z0-9!_\-]+)+$")  # e.g. "cf-china.info:@cn"


def make_session() -> requests.Session:
    retry = Retry(
        total=5,
        backoff_factor=1.0,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET",),
    )
    session = requests.Session()
    session.mount("https://", HTTPAdapter(max_retries=retry))
    session.headers.update({"User-Agent": "rules-sync-domainlist/1.0"})
    return session


def fetch(session: requests.Session, name: str, url: str) -> tuple[str, str]:
    log.info("download %s", url)
    response = session.get(url, timeout=60)
    response.raise_for_status()
    return name, response.text


def parse_list(text: str) -> tuple[dict[str, list[str]], int]:
    """Parse a v2ray geosite text list into sing-box rule-set fields."""
    acc: dict[str, list[str]] = {key: [] for key in FIELD_ORDER}
    skipped = 0
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        match = LINE_RE.match(line)
        if match:
            kind, value = match.group(1), match.group(2)
        else:
            kind, value = "domain", line  # bare line == "domain:" (suffix)
        value = ATTR_RE.sub("", value).strip()
        if not value:
            skipped += 1
            continue
        field = KEY_OF.get(kind)
        if field is None:  # include:/unknown — not present in release files
            skipped += 1
            continue
        acc[field].append(value)
    return acc, skipped


def build_rule_set(acc: dict[str, list[str]]) -> dict:
    """One rule per matcher field; rules inside a rule-set are OR'ed."""
    rules = []
    for field in FIELD_ORDER:
        values = sorted(set(acc[field]))
        if values:
            rules.append({field: values})
    return {"version": 3, "rules": rules}


def compile_srs(json_path: Path) -> None:
    srs_path = json_path.with_suffix(".srs")
    subprocess.run(
        ["sing-box", "rule-set", "compile", str(json_path), "-o", str(srs_path)],
        check=True,
    )
    log.info("compiled %s (%.1f KiB)", srs_path, srs_path.stat().st_size / 1024)


def main() -> int:
    if shutil.which("sing-box") is None:
        log.error("sing-box CLI not found in PATH (needed for .srs compilation)")
        return 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    session = make_session()

    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = [pool.submit(fetch, session, name, url) for name, url in SOURCES.items()]
        texts: dict[str, str] = {}
        for future in as_completed(futures):
            name, text = future.result()
            texts[name] = text

    total = 0
    rows = []
    for name, text in [(n, texts[n]) for n in SOURCES] + [
        (n, p.read_text(encoding="utf-8"))
        for n, p in LOCAL_OVERRIDES.items()
        if p.is_file()
    ]:
        acc, skipped = parse_list(text)
        rule_set = build_rule_set(acc)
        json_path = OUT_DIR / f"{name}.json"
        json_path.write_text(
            json.dumps(rule_set, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        compile_srs(json_path)

        entries = len(acc["domain"]) + len(acc["domain_suffix"]) + len(
            acc["domain_keyword"]
        ) + len(acc["domain_regex"])
        total += entries
        rows.append((name, len(acc["domain"]), len(acc["domain_suffix"]),
                     len(acc["domain_keyword"]), len(acc["domain_regex"]), skipped))

    log.info("%-18s %7s %8s %8s %7s %7s", "name", "exact", "suffix", "keyword", "regex", "skipped")
    for name, exact, suffix, keyword, regex, skipped in rows:
        log.info("%-18s %7d %8d %8d %7d %7d", name, exact, suffix, keyword, regex, skipped)

    log.info("Done. %d entries across %d rule sets -> %s/", total, len(rows), OUT_DIR)
    return 0


if __name__ == "__main__":
    sys.exit(main())
