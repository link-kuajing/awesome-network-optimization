#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fetch-tool-releases.py — 网络工具官方 GitHub Releases 拉取器（月度素材引擎）

用途：
    拉取核心网络工具（Xray-core / mihomo / sing-box / Hysteria2 / Shadow-TLS /
    Shadowsocks-rust）官方仓库最近 N 天（默认 30 天）的 releases，输出 markdown
    素材草稿，供人工/agent 整理成《工具动态综述》文章。

特性：
    - 使用 GitHub 公开 API，无需 token（匿名 rate limit 60 次/小时，够用）
    - 结果缓存到 _data/tool_releases.json（默认缓存 24 小时，避免重复拉取）
    - 单个仓库失败不影响其他仓库（容错：记录错误并继续）
    - 跳过 draft 状态的 release；prerelease 保留并标注

用法：
    python3 scripts/fetch-tool-releases.py             # 正常模式（命中缓存则直接生成草稿）
    python3 scripts/fetch-tool-releases.py --force     # 强制重新拉取（忽略缓存）
    python3 scripts/fetch-tool-releases.py --days 60   # 拉最近 60 天
    python3 scripts/fetch-tool-releases.py --out /tmp/draft.md   # 指定草稿输出路径

输出：
    - _data/tool_releases.json        （原始数据缓存，提交仓库，数据可溯源）
    - _data/tool-releases-YYYY-MM.md  （markdown 素材草稿，gitignore，不入库）
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(REPO_DIR, "_data")
CACHE_FILE = os.path.join(DATA_DIR, "tool_releases.json")
CACHE_TTL_SECONDS = 24 * 3600  # 缓存 24 小时
API_BASE = "https://api.github.com/repos"
UA = "Mozilla/5.0 (awesome-network-optimization content script)"

# 项目清单：key = GitHub owner/repo，value = 中文名 + 一句话简介
PROJECTS = [
    ("XTLS/Xray-core", "Xray-core", "V2Ray 继任者，VLESS/XTLS/Reality 等协议的核心实现"),
    ("MetaCubeX/mihomo", "mihomo", "Clash Meta 内核（原 Clash.Meta），规则分流/TUN 模式"),
    ("SagerNet/sing-box", "sing-box", "通用代理平台，支持全平台与多协议"),
    ("apernet/hysteria", "Hysteria2", "基于 QUIC 的代理协议，抗丢包、速度快"),
    ("ihciah/shadow-tls", "Shadow-TLS", "把流量伪装成普通 TLS 的加密混淆层"),
    ("shadowsocks/shadowsocks-rust", "Shadowsocks-rust", "Shadowsocks 官方 Rust 实现（含 2022 版）"),
]


def log(msg):
    print(msg, file=sys.stderr)


def http_get_json(url):
    """GET 一个 JSON 接口，带 UA 与超时，返回 (data, error)。"""
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode("utf-8")), None
    except urllib.error.HTTPError as e:
        return None, f"HTTP {e.code}"
    except urllib.error.URLError as e:
        return None, f"网络错误: {e.reason}"
    except Exception as e:  # noqa: BLE001
        return None, f"未知错误: {e}"


def fetch_repo_releases(repo, since_dt):
    """拉取某个仓库最近 releases，按时间过滤。返回 (list, error)。"""
    url = f"{API_BASE}/{repo}/releases?per_page=30"
    data, err = http_get_json(url)
    if err:
        return None, err
    if not isinstance(data, list):
        return None, f"响应格式异常: {str(data)[:120]}"
    out = []
    for rel in data:
        if rel.get("draft"):
            continue
        pub = rel.get("published_at") or rel.get("created_at") or ""
        try:
            pub_dt = datetime.fromisoformat(pub.replace("Z", "+00:00"))
        except Exception:  # noqa: BLE001
            pub_dt = None
        if pub_dt and pub_dt < since_dt:
            continue
        body = (rel.get("body") or "").strip()
        out.append({
            "tag": rel.get("tag_name", ""),
            "name": rel.get("name") or "",
            "published_at": pub,
            "prerelease": bool(rel.get("prerelease")),
            "html_url": rel.get("html_url", ""),
            "body": body,
        })
    return out, None


def short_notes(body, max_lines=6, max_chars=900):
    """取 release notes 的前几行非空内容，控制长度。"""
    if not body:
        return []
    lines = [ln.rstrip() for ln in body.splitlines()]
    picked = []
    for ln in lines:
        if not ln.strip():
            if picked:
                break  # 连续内容后的空行视为正文结束
            continue
        picked.append(ln.strip())
        if len(picked) >= max_lines:
            break
    # 截断长度
    text = " | ".join(picked)
    if len(text) > max_chars:
        text = text[:max_chars] + "…"
    return picked


def load_cache():
    """读缓存文件；不存在或过期返回 None。"""
    if not os.path.exists(CACHE_FILE):
        return None
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:  # noqa: BLE001
        return None
    fetched = data.get("fetched_at", "")
    try:
        fetched_dt = datetime.fromisoformat(fetched)
        age = (datetime.now(timezone.utc) - fetched_dt).total_seconds()
    except Exception:  # noqa: BLE001
        return None
    if age > CACHE_TTL_SECONDS:
        return None
    return data


def build_markdown(result):
    """把缓存/拉取结果渲染成 markdown 素材草稿。"""
    since = result.get("since_days", 30)
    lines = []
    lines.append(f"# 网络工具 Releases 素材草稿（近 {since} 天）")
    lines.append("")
    lines.append(f"> 数据源：GitHub Releases API（公开接口）｜抓取时间：{result.get('fetched_at', '')}")
    lines.append("> 本文档为自动生成的素材草稿，供整理成月度综述文章，不直接发布。")
    lines.append("")
    for full, cn_name, desc in PROJECTS:
        lines.append(f"## {cn_name}（{full}）")
        lines.append("")
        lines.append(f"> {desc}")
        lines.append("")
        entry = result["repos"].get(full, {})
        if not entry.get("ok"):
            lines.append(f"- ⚠️ 拉取失败：{entry.get('error', '未知错误')}（本次跳过）")
            lines.append("")
            continue
        rels = entry.get("releases", [])
        if not rels:
            lines.append(f"- 近 {since} 天无正式 release。")
            lines.append("")
            continue
        for r in rels:
            tag = r["tag"]
            date_s = (r.get("published_at") or "")[:10]
            pre = "（预发布）" if r.get("prerelease") else ""
            title = r.get("name") or tag
            lines.append(f"### {tag}{pre} — {title}")
            lines.append("")
            lines.append(f"- 发布时间：{date_s}")
            lines.append(f"- 链接：{r.get('html_url', '')}")
            notes = short_notes(r.get("body", ""))
            if notes:
                lines.append("- 要点：")
                for n in notes:
                    n = n.lstrip("#*- ").strip()
                    if n:
                        lines.append(f"  - {n}")
            lines.append("")
    lines.append("---")
    lines.append("> 生成自 scripts/fetch-tool-releases.py，原始数据见 _data/tool_releases.json")
    lines.append("")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="拉取网络工具官方 GitHub Releases")
    ap.add_argument("--force", action="store_true", help="忽略缓存，强制重新拉取")
    ap.add_argument("--days", type=int, default=30, help="只看最近 N 天（默认 30）")
    ap.add_argument("--out", default=None, help="markdown 草稿输出路径（默认 _data/tool-releases-YYYY-MM.md）")
    args = ap.parse_args()

    since_dt = datetime.now(timezone.utc) - timedelta(days=args.days)

    result = None
    if not args.force:
        result = load_cache()
        if result:
            log(f"[cache] 命中缓存 {CACHE_FILE}，抓取时间 {result.get('fetched_at')}（--force 可强制刷新）")
            if result.get("since_days") != args.days:
                log("[cache] 缓存天数与本次请求不同，重新拉取")
                result = None

    if result is None:
        result = {"fetched_at": datetime.now(timezone.utc).isoformat(),
                  "since_days": args.days,
                  "repos": {}}
        for full, _cn, _desc in PROJECTS:
            log(f"[fetch] {full} ...")
            rels, err = fetch_repo_releases(full, since_dt)
            if err:
                result["repos"][full] = {"ok": False, "error": err}
                continue
            result["repos"][full] = {"ok": True, "releases": rels or []}
            log(f"[fetch] {full} 完成，{len(rels or [])} 个 release")
            time.sleep(1)  # 温和限速，避免打满 rate limit

        os.makedirs(DATA_DIR, exist_ok=True)
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        log(f"[save] 缓存写入 {CACHE_FILE}")

    md = build_markdown(result)
    out_path = args.out
    if not out_path:
        month = datetime.now().strftime("%Y-%m")
        out_path = os.path.join(DATA_DIR, f"tool-releases-{month}.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(md)
    print(md)
    log(f"[save] 素材草稿写入 {out_path}")


if __name__ == "__main__":
    main()
