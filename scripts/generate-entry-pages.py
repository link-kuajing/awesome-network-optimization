#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成 airports/entry/ 下的机场"官网注册入口"页面（单仓库矩阵）
数据源:
  - _data/airports.json        每天凌晨由 sync-data.sh 从 API 同步（套餐/特点）
  - scripts/content-extra.json 人工维护的富内容库（点评/流媒体实测/优缺点/适合人群）

用法:
  python3 scripts/generate-entry-pages.py          # 只更新 AUTO-GENERATED 区块（套餐表）
  python3 scripts/generate-entry-pages.py --full   # 全量重建全部页面

内容深度三级:
  主推3家: 人工点评+流媒体实测表+优缺点+适合人群+总结（content-extra.json）
  合集10家: 人工点评+快速选择（content-extra.json）+ 自动性价比分析
  新入库5家: 全部自动生成（JSON 数据驱动）
"""
import json
import os
import re
import sys
from datetime import datetime

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(REPO_DIR, "_data", "airports.json")
EXTRA_FILE = os.path.join(REPO_DIR, "scripts", "content-extra.json")
OUT_DIR = os.path.join(REPO_DIR, "airports", "entry")

# 中文机场名 -> 英文 slug（文件名用）
SLUG_MAP = {
    "自由猫": "freecat",
    "SS-ID": "ss-id",
    "万达云": "wandacloud",
    "Now加速": "now-jiasu",
    "BoostNet": "boostnet",
    "大象网络": "daxiang",
    "一枝红杏": "yizhihongxing",
    "VikingLinks": "vikinglinks",
    "极速云": "jisuyun",
    "悠兔": "youtu",
    "红杏云": "hongxingyun",
    "瑶瑶领先": "yaoyaolingxian",
    "山水云": "shanshuiyun",
    "SKYLUMO": "skylumo",
    "仙路湾": "xianluwan",
    "闪狐云": "shanhuyun",
    "酷酷云": "kukuyun",
    "CyberGuard": "cyberguard",
    "极速Cloud": "jisucloud",
    "秒秒云": "miaomiaoyun",
}

FEATURED_REVIEW = {
    "自由猫": "freecat.md",
    "SS-ID": "ss-id.md",
    "万达云": "wandacloud.md",
    "仙路湾": "xianluwan.md",
    "瑶瑶领先": "yaoyaolingxian.md",
}

PLANS_MARKER_START = "<!-- AUTO-GENERATED: 套餐表，由同步数据自动更新，请勿手动编辑 -->"
PLANS_MARKER_END = "<!-- /AUTO-GENERATED -->"

PERIOD_DURS = {"月", "季", "半年", "年"}
LIFETIME_DURS = {"长期", "一次性", "不限时"}


def load_data():
    with open(DATA_FILE, encoding="utf-8") as f:
        return json.load(f)["data"]


def load_extra():
    if not os.path.exists(EXTRA_FILE):
        return {}
    with open(EXTRA_FILE, encoding="utf-8") as f:
        return json.load(f)


def parse_traffic_gb(text):
    """解析流量字段为 GB 数: '30GB'->30, '10,000,000 G'->1e7, '900GB/半年'->900, '每月50G'->50"""
    if not text:
        return None
    m = re.search(r"([\d,\.]+)\s*(T|TB|G|GB)", text, re.I)
    if not m:
        return None
    n = float(m.group(1).replace(",", ""))
    unit = m.group(2).upper()
    gb = n * 1024 if unit in ("T", "TB") else n
    # 异常值过滤：单套餐流量超过 10 万 G 视为促销展示数据，不参与单价计算
    if gb > 100000:
        return None
    return gb


def per_gb(plan):
    """月付套餐的每GB单价；非月付返回 None（避免季/年付流量口径误导）"""
    if plan.get("duration") != "月":
        return None
    gb = parse_traffic_gb(plan.get("traffic"))
    price = plan.get("price")
    if not gb or not price:
        return None
    return round(float(price) / gb, 3)


def sort_key(p):
    dur = p.get("duration", "")
    order = {"月": 0, "季": 1, "半年": 2, "年": 3, "一次性": 4, "长期": 5, "不限时": 6}
    return (order.get(dur, 7), float(p.get("price", 0)))


DEVICE_RE = re.compile(r"(?:支持|最多|允许|限制)\s*[^\s，,、]+?\s*(?:台|个)设备")


def extract_device(plans):
    """设备限制列：优先 device 字段，空则从 desc 提取。
    各家录法不统一（支持X台设备/最多X个设备/允许X台设备/最多支持5台设备），
    用正则提取首个有效片段，避免脏数据（如"最多 6 个设备最多 1 个设备…"）整串上表。"""
    out = []
    for p in plans:
        dev = (p.get("device") or "").strip()
        desc = (p.get("desc") or "")
        if not dev or dev in ("-", "无限制"):
            m = DEVICE_RE.search(desc)
            dev = m.group(0) if m else "不限"
        if "台设备" in dev or "个设备" in dev:
            m = DEVICE_RE.search(dev)
            if m:
                dev = m.group(0)
        if "台设备" not in dev and "个设备" not in dev and "客户端" not in dev and dev not in ("不限", "-"):
            dev = dev[:30] + "…" if len(dev) > 30 else dev
        out.append(dev)
    return out


def truncate_desc(desc, limit=45):
    desc = (desc or "").strip()
    # 只保留第一段（按中文标点/英文逗号+空格切分；不切数字里的千分位逗号）
    parts = re.split(r"[。；！？、，]\s*|,\s+", desc)
    desc = parts[0] if parts else desc
    if len(desc) > limit:
        return desc[: limit - 1].rstrip(" ，、") + "…"
    return desc


def compact_advantage(adv):
    if not adv:
        return ""
    text = adv.replace("（有家宽）", "").replace("(家宽)", "")
    if len(text) > 100:
        text = text[:97].rstrip("、，,") + "…"
    return text.strip()

def build_intro(airport, extra):
    name = airport["name"]
    if "blurb" in extra:
        return extra["blurb"]
    speed = airport.get("common_speed") or "高速"
    media = airport.get("common_media") or "主流流媒体"
    adv = compact_advantage(airport.get("common_advantage"))
    mainland = "支持国内直接访问" if airport.get("mainland_access") else "国内访问需自备网络环境"
    return (f"提供 {speed} 带宽，节点覆盖{adv}，"
            f"支持{media}，{mainland}。适合跨境办公、流媒体观看、AI 工具访问等场景。")


def plans_grouped(airport):
    """套餐分组: (周期类, 不限时类)，各自已排序"""
    plans = sorted(airport.get("plans") or [], key=sort_key)
    period, lifetime = [], []
    for p in plans:
        (lifetime if p.get("duration") in LIFETIME_DURS else period).append(p)
    return period, lifetime


def build_plans_table(plans):
    if not plans:
        return ""
    devices = extract_device(plans)
    lines = ["| 套餐 | 价格 | 流量 | ¥/G | 设备限制 | 说明 |",
             "|------|------|------|-----|---------|------|"]
    for i, p in enumerate(plans):
        price = f"¥{p.get('price')}"
        traffic = (p.get("traffic") or "").strip()
        pg = per_gb(p)
        pg_s = f"**¥{pg:.2f}**" if pg is not None else "-"
        dev = devices[i] if i < len(devices) else "-"
        dur = p.get("duration", "")
        lines.append(f"| {p.get('name','')} | {price} | {traffic} | {pg_s} | {dev} | {dur} | {truncate_desc(p.get('desc',''))} |")
    return "\n".join(lines)


def price_range(airport):
    plans = airport.get("plans") or []
    prices = [float(p.get("price", 0)) for p in plans if p.get("price")]
    if not prices:
        return "-"
    fmt = lambda x: str(int(x)) if x == int(x) else str(x)
    lo, hi = fmt(min(prices)), fmt(max(prices))
    return f"¥{lo}" if lo == hi else f"¥{lo} ~ ¥{hi}"


def value_analysis(airport):
    """自动性价比分析: 最低入门价 / 月付最划算 / 囤流量最划算（排除¥0体验套餐）"""
    plans = airport.get("plans") or []
    if not plans:
        return ""
    period, lifetime = plans_grouped(airport)
    monthly = [p for p in period if p.get("duration") == "月"]
    lines = []
    # 最低入门价（排除 ¥0 体验套餐）
    real = [p for p in period + lifetime if float(p.get("price", 0)) > 0]
    if real:
        cheap = min(real, key=lambda p: float(p.get("price", 0)))
        lines.append(f"- **最低入门价**：¥{cheap.get('price')}（{cheap.get('name')}）")
    # 月付最划算（¥/G 最低）
    month_pg = [(p, per_gb(p)) for p in monthly]
    month_pg = [(p, g) for p, g in month_pg if g]
    if month_pg:
        best = min(month_pg, key=lambda x: x[1])
        lines.append(f"- **月付最划算**：{best[0].get('name')}（约 ¥{best[1]:.2f}/G）")
    # 囤流量最划算
    if lifetime:
        life_pg = [(p, per_gb(p)) for p in lifetime if per_gb(p)]
        # 不限时套餐没有月口径，直接算总价/流量
        life_ratio = [(p, float(p.get("price", 0)) / g) for p in lifetime
                      for g in [parse_traffic_gb(p.get("traffic"))] if g]
        if life_ratio:
            bl = min(life_ratio, key=lambda x: x[1])
            lines.append(f"- **囤流量推荐**：{bl[0].get('name')}（约 ¥{bl[1]:.2f}/G，不限时）")
    return "\n".join(lines) if lines else ""


def build_media_section(airport, extra):
    if "media_table" in extra:
        lines = [f"### 流媒体解锁实测（{airport['name']}）", "",
                 "| 平台 | 状态 | 备注 |", "|:----:|:----:|------|"]
        for row in extra["media_table"]:
            lines.append(f"| **{row[0]}** | {row[1]} | {row[2]} |")
        return "\n".join(lines)
    media = airport.get("common_media") or "主流流媒体"
    return f">{media}。具体解锁表现随节点与时段波动，可切换线路解决。"


def build_page(airport, extra):
    name = airport["name"]
    slug = SLUG_MAP.get(name, name)
    updated = airport.get("updated_at", datetime.now().strftime("%Y-%m-%d"))[:10]
    intro = build_intro(airport, extra)
    if intro.startswith(name):
        intro = intro[len(name):]
    mainland = "✅ 是" if airport.get("mainland_access") else "❌ 否"

    # 深度评测链接
    review_link = ""
    if name in FEATURED_REVIEW:
        review_link = f"\n> 🔗 深度评测：[{name} 完整评测](../featured/{FEATURED_REVIEW[name]})"

    # 快速选择
    quick_pick = extra.get("quick_pick")
    quick_section = ""
    if quick_pick:
        quick_section = f"""## 🎯 快速选择

{name}适合以下场景的用户：

- {quick_pick}

> 具体是否适合你，请结合下方套餐与价格判断，或到官网查看实时详情。
"""
    else:
        quick_section = f"""## 🎯 快速选择

{name}适合跨境办公、流媒体观看、AI 工具访问、游戏加速等常见场景，按流量需求选择对应套餐即可。

> 具体是否适合你，请结合下方套餐与价格判断，或到官网查看实时详情。
"""

    # 套餐表（分组）
    period, lifetime = plans_grouped(airport)
    plans_blocks = []
    if period:
        plans_blocks.append(f"### 周期套餐（{period[0].get('duration')}付起）\n\n" + build_plans_table(period))
    if lifetime:
        plans_blocks.append(f"### 不限时套餐（长期有效）\n\n" + build_plans_table(lifetime))
    plans_body = "\n\n".join(plans_blocks) if plans_blocks else "> 暂无公开套餐数据，请以官网为准。"

    # 性价比分析
    value_section = ""
    va = value_analysis(airport)
    if va:
        value_section = f"""## 💰 性价比分析

{va}

> 单价按套餐标注流量计算，实际可用流量以官网订阅页为准。
"""

    # 流媒体
    media_section = build_media_section(airport, extra)

    # 优缺点/适合人群/总结（主推3家有）
    rich_section = ""
    if "pros" in extra and "cons" in extra:
        pros = "\n".join(f"- {x}" for x in extra["pros"])
        cons = "\n".join(f"- {x}" for x in extra["cons"])
        target = "\n".join(f"- 🎯 {x}" for x in extra.get("target_users", []))
        not_for = "\n".join(f"- ❌ {x}" for x in extra.get("not_for", []))
        summary = extra.get("summary", "")
        rich_section = f"""## ✅ 优点

{pros}

## ❌ 不足

{cons}
"""
        if target:
            rich_section += f"""
## 💡 适合谁买？

{target}
"""
        if not_for:
            rich_section += f"""
## ❌ 不适合谁？

{not_for}
"""
        if summary:
            rich_section += f"""
## 🏁 总结

{summary}
"""

    return f"""# {name} 官网注册入口说明与使用指南

**{name}** {intro}

> 📌 本页面仅整理公开信息与使用指引，不提供账号、节点或配置文件。内容均为原创整理，仅供参考与学习，禁止整段复制或镜像搬运。
> 🔔 最后更新：{updated}（套餐详情与活动请以官网为准）
{review_link}
---

## 🚀 官网注册入口

👉 [**立即进入 {name} 官网**]({airport['short_url']})

> 如遇无法打开，请尝试更换浏览器或网络环境后重新访问。建议使用 Chrome、Edge 等桌面浏览器访问，以获得更好的注册与配置体验。

---

{quick_section}
## 🧩 核心特点

- **带宽**：{airport.get('common_speed', '-') or '-'}
- **节点覆盖**：{extra.get('advantage') or compact_advantage(airport.get('common_advantage')) or '详见官网'}
- **流媒体**：{airport.get('common_media', '-') or '-'}
- **国内可访问**：{mainland}

---

## 📦 套餐价格一览

{PLANS_MARKER_START}
{plans_body}
{PLANS_MARKER_END}

> 💡 套餐与价格以官网实时显示为准，本表仅供参考。

---
{value_section}
## 🎬 流媒体与平台支持

{media_section}

---
{rich_section}
## ⚙️ 客户端使用指南

{name}支持主流代理客户端，注册后按以下步骤即可开始使用：

1. **注册账号**：通过上方官网入口注册并登录
2. **购买套餐**：按需选择套餐并完成支付
3. **获取订阅**：在官网"我的订阅"页面复制订阅链接
4. **导入客户端**：将订阅链接粘贴到客户端一键导入

支持平台（示例）：

- **Windows**：Clash for Windows / Clash Verge / v2rayN
- **macOS**：ClashX / Clash Verge
- **iOS**：Shadowrocket / Stash / Loon
- **Android**：Clash Meta / v2rayNG

> 具体配置步骤请以官网帮助文档为准。

---

## ❓ 常见问题

**Q1：{name} 支持哪些客户端？**
主流 Clash 系（Clash Verge / ClashX / Clash Meta）、Shadowrocket、v2rayN 等第三方客户端均可使用，具体以官网说明为准。

**Q2：可以同时几台设备使用？**
不同套餐的设备数限制不同，详见上方套餐价格一览表。

**Q3：官网打不开怎么办？**
可尝试更换浏览器（建议 Chrome / Edge）、切换网络环境后重新访问。

**Q4：流量重置规则是什么？**
月付套餐流量按月重置，不限时套餐用完为止，具体以官网订阅页面显示为准。

**Q5：套餐怎么选？**
先看月流量需求：日常上网 100G 内选入门档，重度视频/AI 用户选大流量档；需要长期备用可考虑不限时套餐。单价对比可参考上方"性价比分析"。

---

> 🔗 更多机场入口与选购指南：[机场入口索引](./README.md) ｜ [机场选购指南](../README.md)
"""


def update_plans_section(path, airport, extra):
    """只更新 AUTO-GENERATED 区块（套餐表），保留人工编辑区"""
    with open(path, encoding="utf-8") as f:
        content = f.read()
    period, lifetime = plans_grouped(airport)
    blocks = []
    if period:
        blocks.append(f"### 周期套餐（{period[0].get('duration')}付起）\n\n" + build_plans_table(period))
    if lifetime:
        blocks.append(f"### 不限时套餐（{airport['name']} 长期有效）\n\n" + build_plans_table(lifetime))
    joined = "\n\n".join(blocks) if blocks else "> 暂无公开套餐数据，请以官网为准。"
    new_table = f"{PLANS_MARKER_START}\n{joined}\n{PLANS_MARKER_END}"
    pattern = re.compile(re.escape(PLANS_MARKER_START) + r".*?" + re.escape(PLANS_MARKER_END), re.S)
    if pattern.search(content):
        return pattern.sub(new_table, content)
    return build_page(airport, extra)


def highlight_of(extra, airport):
    """入口表格的亮点列：优先人工 quick_pick，其次流媒体描述"""
    if extra.get("quick_pick"):
        return extra["quick_pick"]
    return (airport.get("common_media") or "").strip()[:20]


def build_index(airports, extras):
    lines = [
        "# 机场官网入口索引",
        "",
        "> 按品牌整理的官网注册入口与使用指南页面。所有入口链接均指向对应机场官网，请通过官网注册获取服务。",
        f"> 最后更新：{datetime.now().strftime('%Y-%m-%d')}",
        "",
        "## 全部机场入口",
        "",
        "| 机场 | 带宽 | 价格区间 | 亮点 | 官网入口 |",
        "|------|------|---------|------|---------|",
    ]
    for a in sorted(airports, key=lambda x: (not x.get("is_featured"), x["name"])):
        name = a["name"]
        slug = SLUG_MAP.get(name)
        if not slug:
            continue
        star = "⭐ " if a.get("is_featured") else ""
        extra = extras.get(name, {})
        highlight = highlight_of(extra, a)
        entry = f"[进入官网 →](./{slug}.md)"
        lines.append(f"| {star}{name} | {a.get('common_speed','-')} | {price_range(a)} | {highlight} | {entry} |")
    lines += [
        "",
        "---",
        "",
        "> 🔗 深度评测：[主推机场评测](../featured/) ｜ 其他机场合集：[others.md](../others.md) ｜ [机场选购指南](../README.md)",
        "",
    ]
    return "\n".join(lines)


def build_readme_entry_section(airports, extras):
    """生成主 README 的机场官网入口板块（插入 <!-- ENTRY-INDEX --> 标记区）"""
    lines = [
        "## 🛩️ 机场官网入口",
        "",
        "> 每家机场都有独立的官网注册入口与使用指南页，套餐价格每日自动同步更新。",
        "",
        "| 机场 | 带宽 | 价格区间 | 亮点 | 官网入口 |",
        "|------|------|---------|------|---------|",
    ]
    for a in sorted(airports, key=lambda x: (not x.get("is_featured"), x["name"])):
        name = a["name"]
        slug = SLUG_MAP.get(name)
        if not slug:
            continue
        star = "⭐ " if a.get("is_featured") else ""
        extra = extras.get(name, {})
        highlight = highlight_of(extra, a)
        entry = f"[进入官网 →](airports/entry/{slug}.md)"
        lines.append(f"| {star}{name} | {a.get('common_speed','-')} | {price_range(a)} | {highlight} | {entry} |")
    lines += [
        "",
        "> 🔗 [全部机场入口索引](airports/entry/README.md)",
        "",
    ]
    return "\n".join(lines)


def update_readme(airports, extras):
    """更新主 README 的入口板块（标记区间）"""
    path = os.path.join(REPO_DIR, "README.md")
    with open(path, encoding="utf-8") as f:
        content = f.read()
    section = build_readme_entry_section(airports, extras)
    start_marker = "<!-- ENTRY-INDEX:START -->"
    end_marker = "<!-- ENTRY-INDEX:END -->"
    block = f"{start_marker}\n{section}{end_marker}"
    pattern = re.compile(re.escape(start_marker) + r".*?" + re.escape(end_marker), re.S)
    if pattern.search(content):
        content = pattern.sub(block, content)
    else:
        content = content.replace("## 🛩️ 机场服务评测", f"{block}\n\n## 🛩️ 机场服务评测", 1)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("✅ 主 README 入口板块已更新")


def main():
    full = "--full" in sys.argv
    os.makedirs(OUT_DIR, exist_ok=True)
    airports = load_data()
    extras = load_extra()
    generated, updated = [], []
    for a in airports:
        name = a["name"]
        slug = SLUG_MAP.get(name)
        if not slug:
            print(f"[SKIP] {name}: 缺少 slug 映射")
            continue
        extra = extras.get(name, {})
        path = os.path.join(OUT_DIR, f"{slug}.md")
        if full or not os.path.exists(path):
            content = build_page(a, extra)
            mode = "新建"
        else:
            content = update_plans_section(path, a, extra)
            mode = "更新套餐表"
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        (generated if mode == "新建" else updated).append(name)
    index_path = os.path.join(OUT_DIR, "README.md")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(build_index(airports, extras))
    update_readme(airports, extras)
    print(f"✅ 新建 {len(generated)}: {', '.join(generated) if generated else '无'}")
    print(f"✅ 更新 {len(updated)}: {', '.join(updated) if updated else '无'}")
    print(f"✅ 索引页: {index_path}")


if __name__ == "__main__":
    main()
