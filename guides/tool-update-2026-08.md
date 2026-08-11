# 2026 年 8 月网络工具更新综述

> 每个月帮你看一遍核心网络工具的官方更新：Xray-core、mihomo、sing-box、Hysteria2、Shadow-TLS、Shadowsocks-rust。所有内容基于 GitHub Releases 官方数据整理，不编造、不猜测。
>
> 🕐 更新时间：2026-08-11 ｜ 数据抓取：2026-08-11

---

## 📋 目录

- [本月速览](#本月速览)
- [数据来源说明](#数据来源说明)
- [Xray-core](#xray-core)
- [mihomo（Clash Meta）](#mihomoclash-meta)
- [sing-box](#sing-box)
- [Hysteria2](#hysteria2)
- [Shadow-TLS / Shadowsocks-rust](#shadow-tls--shadowsocks-rust)
- [这些更新对我们意味着什么](#这些更新对我们意味着什么)
- [如何每月获取这份综述](#如何每月获取这份综述)
- [参考资源](#参考资源)

---

## 本月速览

近 30 天（2026-07-13 ~ 2026-08-11）各项目官方 release 情况：

| 项目 | 近期版本 | 主要动态 |
|:----|:----|:----|
| Xray-core | v26.7.28（预发布） | 发布预发布版，未附带详细说明 |
| mihomo | v1.19.29 | anytls 同步、OpenVPN 协商支持、restls/jls 支持 |
| sing-box | 1.13.x 稳定 + 1.14.0-beta 系列 | 稳定版 1.13.18 / 1.13.16 / 1.13.15，beta 密集迭代中 |
| Hysteria2 | app/v2.12.1 | Chrome QUIC 指纹仿冒、mimic 伪装、ECH 支持、重连修复 |
| Shadow-TLS | — | 近 30 天无新 release |
| Shadowsocks-rust | — | 近 30 天无新 release |

---

## 数据来源说明

本文数据由仓库内脚本 `scripts/fetch-tool-releases.py` 从 **GitHub Releases 公开 API** 拉取（2026-08-11 抓取，时间范围近 30 天），原始数据存档在 `_data/tool_releases.json`，可随时复核。每个项目的小节内容只基于官方 release 的标题与说明，**没有说明的部分如实标注**，不做推测。

---

## Xray-core

- **v26.7.28**（预发布，2026-07-28）
  - 该 release 未附带详细变更说明，仅发布版本本身。
  - 仓库：[XTLS/Xray-core](https://github.com/XTLS/Xray-core)

对自建用户来说，Xray 的正式版本线保持稳定，预发布版一般用于验证新特性；生产节点建议等正式版再升。

---

## mihomo（Clash Meta）

- **v1.19.29**（2026-07-18）
  - 同步 anytls 协议到 v0.0.13；
  - 新增对 OpenVPN 的 **TLS rekey 修复、data-ciphers 协商、tls-crypt-v2** 支持；
  - anytls 出站与监听支持 **restls**；
  - shadowsocks 出站与监听支持 **jls**；
  - 新增 `name-cert-verify`，支持为证书校验指定独立的验证域名。

仓库：[MetaCubeX/mihomo](https://github.com/MetaCubeX/mihomo)

解读：这一版 mihomo 明显在**协议兼容性**上发力——OpenVPN 的 tls-crypt-v2 属于 VPN 侧的能力对接，anytls 与 shadowsocks 的协议选项也进一步丰富（restls / jls 等）。对日常用 mihomo 做分流的用户，规则与策略组功能不受影响，正常升级即可。

---

## sing-box

近 30 天 sing-box 的发布节奏很快：稳定分支推出 **1.13.15 / 1.13.16 / 1.13.18**（7-29 / 8-3 / 8-9），同时 **1.14.0 的 beta 系列**高频迭代（beta.1 ~ beta.14，其中 8-3 之后几乎一天一个 beta）。

- 该项目的 GitHub release 说明很简短（仅 "Release Notes" 占位），详细变更一般在项目文档/频道发布，本文不展开推测具体内容；
- 对普通用户：稳定版 1.13.x 是安全选择；beta 系列适合想尝鲜且能接受潜在问题的用户。

仓库：[SagerNet/sing-box](https://github.com/SagerNet/sing-box)

---

## Hysteria2

本月更新最密集的项目，连续四个版本：

### app/v2.12.1（2026-08-09）
- 新增 Porkbun、Namecheap、Njalla 作为 ACME DNS 服务商；
- 修复客户端空闲/休眠后的慢重连（手机端最明显）：服务器现在会发送 QUIC stateless reset，客户端持有时连接失效时能立即重连，不再傻等超时；
- 修复 mimic 在可选内核模块未加载时拒绝启动的问题。

### app/v2.12.0（2026-08-06）
- 新增 **mimic 集成**：在限制 UDP 的网络环境下把连接伪装成 TCP（仅 Linux，需单独安装 mimic）；
- 提升 Chrome QUIC 指纹仿冒的准确度；
- 修复 2.11.0 引入的小 MTU 路径下 BBR panic。

### app/v2.11.0（2026-08-01）
- 新增 **Chrome QUIC 指纹仿冒**：客户端 QUIC 握手看起来与 Google Chrome 一致，**默认启用**，可用 `quic.disableChromeParrot` 关闭；
- 现代化重构 ACME 证书栈（CertMagic / ACMEz / libdns）；
- 移除未适配新 libdns API 的 namedotcom DNS 服务商；
- 升级 quic-go 到 v0.61.0。

### app/v2.10.0（2026-07-13）
- 新增 **ECH（Encrypted Client Hello）** 支持；
- 新增 `bandwidth.disableLossCompensation` 选项，可关闭 Brutal 拥塞控制的速率补偿机制，某些场景下更稳定。

仓库：[apernet/hysteria](https://github.com/apernet/hysteria) ｜ 官方文档：https://hysteria.network

解读：Hysteria2 这个月的关键词是"**可观测性补课**"——QUIC 系协议过去被诟病"特征明显、容易被针对"，现在官方在指纹仿冒（Chrome QUIC）、UDP 受限网络下的 TCP 伪装（mimic）、以及移动端弱网重连体验上连续补强，方向非常明确。

---

## Shadow-TLS / Shadowsocks-rust

- **Shadow-TLS**（ihciah/shadow-tls）：近 30 天无新 release；
- **Shadowsocks-rust**（shadowsocks/shadowsocks-rust）：近 30 天无新 release。

两个项目仍处于稳定维护状态，没有新版本不等于不维护——它们的协议本身已经很成熟，属于"低频发版"型项目。SS 生态近期的活跃点更多在 mihomo 对 SS 的 jls 支持这类周边能力上（见上文）。

---

## 这些更新对我们意味着什么

1. **Hysteria2 值得弱网用户再评估**：指纹仿冒 + mimic + 重连修复，补上了它过去在"被识别/被限制"上的短板；如果你所在网络 UDP 通畅，hy2 在弱网下的优势会更明显（协议原理见 [主流代理协议横评](protocols-comparison.md)）；
2. **mihomo 的"隧道兼容"在变厚**：OpenVPN/tls-crypt-v2、restls、jls 这类能力短期对普通分流用户无感，但对"需要接非标准隧道"的场景是实打实的能力增加；
3. **Xray 保持克制**：预发布版未带说明，正式版节奏稳定，自建节点用户无需追新。

---

## 如何每月获取这份综述

1. 仓库内已内置拉取脚本，随时手动更新：
   ```bash
   cd /root/awesome-network-optimization   # 或你的本地仓库路径
   python3 scripts/fetch-tool-releases.py --force   # 强制重新拉取（忽略 24h 缓存）
   ```
   - 脚本把原始数据缓存到 `_data/tool_releases.json`（默认缓存 24 小时，避免每次重复请求 GitHub API）；
   - 输出 markdown 素材草稿（按项目分组、版本号/日期/要点），文章基于该草稿人工整理；
   - 单项目失败会自动跳过并注明，不影响其他项目。
2. 我们会在每月中旬基于脚本数据更新一篇综述文章，保持 [教程区](../guides/README.md) 的时效性。

---

## 参考资源

- 原始数据存档：`_data/tool_releases.json`（本仓库，可复核）
- [XTLS/Xray-core releases](https://github.com/XTLS/Xray-core/releases)
- [MetaCubeX/mihomo releases](https://github.com/MetaCubeX/mihomo/releases)
- [SagerNet/sing-box releases](https://github.com/SagerNet/sing-box/releases)
- [apernet/hysteria releases](https://github.com/apernet/hysteria/releases)
- [ihciah/shadow-tls releases](https://github.com/ihciah/shadow-tls/releases)
- [shadowsocks/shadowsocks-rust releases](https://github.com/shadowsocks/shadowsocks-rust/releases)
- 配套阅读：[主流代理协议横评](protocols-comparison.md)

---

> 📝 本文内容截至 2026-08-11 抓取；版本以官方仓库为准。发现问题欢迎提 Issue 指正。
