#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Convert Loyalsoldier (v2ray format) geosite.dat / geoip.dat into sing-box rule-sets.

Loyalsoldier only publishes v2ray `.dat` (and plain text lists); sing-box cannot read
those (`unknown version` / `invalid MaxMind DB file`). This script parses the protobuf
directly and emits sing-box source rule-sets, then compiles them to `.srs`.

Output layout (matches the `{tag}` templating used by sing-box remote rule-sets):

    out/geo/geosite/<category>.srs      e.g. geosite/cn
    out/geo/geoip/<country>.srs         e.g. geoip/cn

Usage:
    python3 loyalsoldier-srs.py --out out [--only cn,geolocation-!cn] [--geoip-cn-only]

Type mapping (verified against Loyalsoldier's own text lists):
    v2ray type 1 (Regex)  -> domain_regex
    v2ray type 2 (Domain) -> domain_suffix      # his build uses "Domain" for bare lines
    v2ray type 3 (Full)   -> domain             # his `full:` lines
    v2ray type 0 (Plain)  -> domain_suffix
    v2ray type 4 (Keyword)-> domain_keyword
"""
from __future__ import annotations

import argparse
import ipaddress
import json
import shutil
import subprocess
import sys
from pathlib import Path

GEOSITE_URL = "https://github.com/Loyalsoldier/v2ray-rules-dat/releases/latest/download/geosite.dat"
GEOIP_URL = "https://github.com/Loyalsoldier/v2ray-rules-dat/releases/latest/download/geoip.dat"

TYPE_MAP = {0: "domain_suffix", 1: "domain_regex", 2: "domain_suffix", 3: "domain", 4: "domain_keyword"}
FIELD_ORDER = ("domain", "domain_suffix", "domain_keyword", "domain_regex", "ip_cidr")


def read_varint(buf: bytes, pos: int):
    result = 0
    shift = 0
    while True:
        b = buf[pos]
        pos += 1
        result |= (b & 0x7F) << shift
        if not (b & 0x80):
            return result, pos
        shift += 7


def fields(buf: bytes):
    """Minimal protobuf reader: yields (field_number, value)."""
    pos = 0
    end = len(buf)
    while pos < end:
        key, pos = read_varint(buf, pos)
        fn, wt = key >> 3, key & 7
        if wt == 0:
            val, pos = read_varint(buf, pos)
        elif wt == 2:
            ln, pos = read_varint(buf, pos)
            val = buf[pos:pos + ln]
            pos += ln
        elif wt == 1:
            val = buf[pos:pos + 8]
            pos += 8
        elif wt == 5:
            val = buf[pos:pos + 4]
            pos += 4
        else:
            raise ValueError(f"unsupported wire type {wt}")
        yield fn, val


def parse_geosite(path: Path) -> dict[str, list[tuple[int, str]]]:
    """GeoSiteList{ 1: GeoSite{ 1: country_code, 2: Domain{ 1: type, 2: value } } }"""
    out: dict[str, list[tuple[int, str]]] = {}
    for fn, val in fields(path.read_bytes()):
        if fn != 1:
            continue
        code, domains = "", []
        for gfn, gval in fields(val):
            if gfn == 1:
                code = gval.decode("utf-8", "replace")
            elif gfn == 2:
                dtype, value = 0, ""
                for dfn, dval in fields(gval):
                    if dfn == 1:
                        dtype = dval
                    elif dfn == 2:
                        value = dval.decode("utf-8", "replace")
                if value:
                    domains.append((dtype, value))
        if code:
            out[code] = domains
    return out


def parse_geoip(path: Path) -> dict[str, list[str]]:
    """GeoIPList{ 1: GeoIP{ 1: country_code, 2: CIDR{ 1: ip bytes, 2: prefix } } }"""
    out: dict[str, list[str]] = {}
    for fn, val in fields(path.read_bytes()):
        if fn != 1:
            continue
        code, cidrs = "", []
        for gfn, gval in fields(val):
            if gfn == 1:
                code = gval.decode("utf-8", "replace")
            elif gfn == 2:
                raw, prefix = b"", 0
                for cfn, cval in fields(gval):
                    if cfn == 1:
                        raw = cval
                    elif cfn == 2:
                        prefix = cval
                if raw:
                    cidrs.append(f"{ipaddress.ip_address(raw)}/{prefix}")
        if code:
            out[code] = cidrs
    return out


def build_rule_set(fields_map: dict[str, list[str]]) -> dict:
    rules = []
    for field in FIELD_ORDER:
        values = sorted(set(fields_map.get(field, [])))
        if values:
            rules.append({field: values})
    return {"version": 3, "rules": rules}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="out")
    ap.add_argument("--only", default="", help="comma separated geosite categories (default: all)")
    ap.add_argument("--no-compile", action="store_true")
    ap.add_argument("--keep-json", action="store_true")
    args = ap.parse_args()

    out = Path(args.out)
    (out / "geo" / "geosite").mkdir(parents=True, exist_ok=True)
    (out / "geo" / "geoip").mkdir(parents=True, exist_ok=True)

    geosite_dat = Path("geosite.dat")
    geoip_dat = Path("geoip.dat")
    if not geosite_dat.exists():
        subprocess.run(["curl", "-sfL", "-o", str(geosite_dat), GEOSITE_URL], check=True)
    if not geoip_dat.exists():
        subprocess.run(["curl", "-sfL", "-o", str(geoip_dat), GEOIP_URL], check=True)

    singbox = shutil.which("sing-box") or "/usr/local/bin/sing-box"

    def emit(name: str, rule_set: dict, sub: str) -> int:
        json_path = out / "geo" / sub / f"{name}.json"
        srs_path = out / "geo" / sub / f"{name}.srs"
        json_path.write_text(json.dumps(rule_set, ensure_ascii=False), encoding="utf-8")
        if args.no_compile:
            return 0
        subprocess.run([singbox, "rule-set", "compile", str(json_path), "-o", str(srs_path)], check=True)
        if not args.keep_json:
            json_path.unlink()
        return srs_path.stat().st_size

    only = {s.strip().lower() for s in args.only.split(",") if s.strip()}
    total = 0
    counts = []

    geosite = parse_geosite(geosite_dat)
    for code, domains in sorted(geosite.items()):
        name = code.lower()
        if only and name not in only:
            continue
        fields_map: dict[str, list[str]] = {f: [] for f in FIELD_ORDER}
        skipped = 0
        for dtype, value in domains:
            field = TYPE_MAP.get(dtype)
            if field is None:
                skipped += 1
                continue
            fields_map[field].append(value)
        size = emit(name, build_rule_set(fields_map), "geosite")
        n = sum(len(v) for v in fields_map.values())
        counts.append((n, name, size, skipped))
        total += n

    print(f"geosite: {len(counts)} categories, {total} entries total")
    print("  top 12 by entry count:")
    for n, name, size, skipped in sorted(counts, reverse=True)[:12]:
        print(f"    {name:<28} {n:>7} 条  {size/1024:>8.1f} KiB  (skipped {skipped})")
    for probe in ("cn", "geolocation-!cn", "geolocation-cn"):
        hit = next((c for c in counts if c[1] == probe), None)
        if hit:
            print(f"    {probe:<28} {hit[0]:>7} 条  {hit[2]/1024:>8.1f} KiB")

    geoip = parse_geoip(geoip_dat)
    gtotal = 0
    for code, cidrs in sorted(geoip.items()):
        name = code.lower()
        if only and "geoip" not in args.only and name not in only:
            continue
        size = emit(name, build_rule_set({"ip_cidr": cidrs}), "geoip")
        gtotal += len(cidrs)
    print(f"geoip: {len(geoip)} countries, {gtotal} CIDRs total")
    return 0


if __name__ == "__main__":
    sys.exit(main())
