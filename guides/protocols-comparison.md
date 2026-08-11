# 主流代理协议横评：VLESS+Reality / Shadowsocks / Trojan / Hysteria2 / TUIC

> 选了机场、配了客户端，但你有没有想过：节点后面那个协议到底是什么？这篇把五种主流代理协议讲透——原理、加密、被墙风险、速度特性、客户端支持、适用场景，帮你从"会连"进化到"会选"。
>
> 🕐 更新时间：2026-08-11

---

## 📋 目录

- [协议是什么？为什么值得了解](#协议是什么为什么值得了解)
- [VLESS + Reality](#vless--reality)
- [Shadowsocks（AEAD / 2022 版）](#shadowsocksaead--2022-版)
- [Trojan](#trojan)
- [Hysteria2](#hysteria2)
- [TUIC](#tuic)
- [五张图看懂：横向对比总表](#五张图看懂横向对比总表)
- [怎么选：按场景对号入座](#怎么选按场景对号入座)
- [我们的实操：自用节点 = Xray + VLESS + Reality](#我们的实操自用节点--xray--vless--reality)
- [2026 年 8 月协议生态动态](#2026-年-8-月协议生态动态)
- [常见问题](#常见问题)
- [参考资源](#参考资源)

---

## 协议是什么？为什么值得了解

代理协议是客户端与服务器之间"怎么说话"的约定：**加密怎么加、握手怎么握、流量怎么装**。它决定了三件事：

1. **能不能连上**：GFW（防火长城）会识别特征明显的流量并阻断，协议决定了流量看起来像什么；
2. **连上快不快**：TCP 还是 UDP、有没有 0-RTT、拥塞控制算法，直接影响速度和弱网表现；
3. **哪些客户端能用**：不同客户端对协议的支持不一样，协议太新可能"没软件可用"。

现在主流的协议分两大阵营：

- **TCP 系（伪装 HTTPS）**：VLESS+Reality、Trojan、Shadowsocks——流量走 TCP，核心思路是"像普通网页访问"；
- **UDP 系（QUIC 系）**：Hysteria2、TUIC——流量走 QUIC（基于 UDP），核心思路是"抗丢包、低延迟、0-RTT"。

下面逐个拆解。

---

## VLESS + Reality

### 原理

VLESS 是 XTLS 项目设计的一款无状态传输协议，本身**不内置加密**（配置里就是 `encryption: none`），它的加密与伪装完全交给外层传输层——最常见的就是 Reality 或 TLS/WS。

Reality 是 XTLS 团队提出的传输层方案，核心思路是**"借用"真实网站的 TLS 握手**：

> 服务器自己不需要证书、不需要域名。客户端来握手时，服务器把 ClientHello 原样转发给一个真实存在的目标网站（比如某个支持 TLS 1.3 的国外站点），目标网站返回真实的 ServerHello，服务器再把它带回给客户端。从中间设备（包括 GFW）的视角看，这条连接就是**一条到你指定 SNI 的真实 TLS 连接**，全程握手和真实网站一模一样。

官方对 Reality 的原话是：**"消除服务端 TLS 指纹特征……证书链攻击无效，安全性超越常规 TLS"**，并且"可以指向别人的网站，无需自己买域名、配置 TLS 服务端"。客户端侧需要用 uTLS 库模拟浏览器 TLS 指纹（默认模拟 Chrome），并持有服务器公钥（X25519 密钥对）来验证握手。

### 加密与指纹

- 加密：X25519 密钥交换 + TLS 1.3 加密（借的是目标网站的真实 TLS），外加 XTLS `xtls-rprx-vision` 流控减少 TLS in TLS 特征；
- 指纹：客户端 uTLS 模拟浏览器指纹（默认 chrome），服务端无自签证书，指纹干净。

### 被墙风险

目前公认**抗封锁能力最强**的组合之一。原因：没有自签证书（主动探测无从下手）、握手与真实网站完全一致（被动特征几乎为零）。2024 年后新协议里它一直是"能不能抗住"的标杆。

### 速度特性

走 TCP，普通线路下速度与 Trojan 相当；配合 vision 流控在部分场景比传统 TLS 封装更快（少了重复的 TLS 包裹开销）。

### 客户端支持

Xray 系客户端支持最好：v2rayN（Windows）、v2rayNG（Android）、Shadowrocket / Stash（iOS）都能直接填 Reality 参数；mihomo（Clash Meta）和 sing-box 也支持。**老版 Clash（premium 内核）不支持 VLESS+Reality**，这是很多人"订阅导入后节点是空的"的原因。

---

## Shadowsocks（AEAD / 2022 版）

### 原理

Shadowsocks（SS）是历史最悠久的代理协议之一，思路很直接：客户端与服务器之间做一层"加了密的隧道"，目标网站看到的是服务器 IP 发起的正常请求。SS 本身没有 TLS 握手伪装，流量特征就是"一段看起来随机的加密流"。

- **AEAD 版（2017 版）**：每个连接开头发一段随机 salt，用 salt 派生会话子密钥，之后按块做 AEAD 加密。解决早期"流密码可重放"的问题。
- **2022 版（SIP022 规范）**：2022 年推出的新版本，用 BLAKE3 做密钥派生、引入多用户认证（Extensible Identity Headers），丢弃了旧版过时的密码学原语，速度和安全性都有提升。

### 加密与指纹

- 加密：AEAD 系（aes-128-gcm 等，2022 版可选 BLAKE3 派生），加密强度没问题；
- 指纹：**没有 TLS 握手**，流量特征相对简单，这是它的短板。

### 被墙风险

历史上 SS 是"用最简单的方式被识别"的典型：特征简单、没有伪装层，多次出现大规模识别与阻断事件。现在裸 SS 直连风险较高，通常要配合**中转/专线**（流量不过公网直连段）或者叠加 Shadow-TLS 这类伪装层来用。

### 速度特性

TCP 传输，加密开销小，在优质线路上速度表现好；支持 UDP（Full Cone 取决于实现）。

### 客户端支持

**最广**：几乎所有客户端都支持（Clash 系、v2ray 系、sing-box、手机端一键客户端），老设备、老内核都不挑剔。这也是机场大量用它做"通用兜底"协议的原因。

---

## Trojan

### 原理

Trojan 的思路是**把自己完全伪装成一次正常的 HTTPS 访问**：服务器部署在 443 端口，持有**真实的域名和 TLS 证书**，完成完整的 TLS 握手；握完手后，客户端用约定好的"密码"（Trojan 协议里叫 password）发起请求，服务器校验通过就转发流量；校验不通过（比如浏览器直接访问 443）就回落到一个正常网页——看起来就是一台普通 HTTPS 网站。

### 加密与指纹

- 加密：完整 TLS（真实证书）+ 密码认证；
- 指纹：有真实证书、完整握手，主动探测时表现和正常网站一致（回落逻辑），**抗主动探测能力很强**。

### 被墙风险

比裸 SS 强很多，但在"TLS 内再套一层代理流量"时存在 **TLS in TLS 特征**（代理流量本身有自己的握手特征，藏在一层 TLS 里），深度检测仍可能识别。这也是 Trojan 系通常建议配合 XTLS 流控的原因。

### 速度特性

TCP 传输，TLS 开销比 SS 略大，但强在稳定；回落机制让它很适合长时间挂着。

### 客户端支持

广：Clash 系、v2ray 系、sing-box 都支持。需要域名+证书，**自建门槛比 Reality 高**。

---

## Hysteria2

### 原理

Hysteria2（hy2）是 Hysteria 的第二代，**基于 QUIC（UDP）**的高速代理协议。QUIC 是谷歌主导、HTTP/3 使用的传输协议，自带加密、多路复用、连接迁移等能力。Hysteria2 最大的特点是用 **Brutal 拥塞控制算法**：不按丢包退避，而是按你设定的固定速率"硬推"，丢包再多也不降速——**专为高丢包、弱网环境设计**（官方自述：卫星网络、拥挤公共 Wi-Fi、跨墙链路这类场景）。

### 加密与指纹

- 加密：TLS 1.3（QUIC 内建）；
- 指纹：2026 年的 v2.11.0 开始默认启用 **Chrome QUIC 指纹仿冒**（客户端 QUIC 握手看起来和 Google Chrome 一致），v2.12.0 又提高了仿冒精度；还支持 ECH（Encrypted Client Hello）和 UDP 受限网络下的 mimic 伪装（把连接伪装成 TCP，仅 Linux）。

### 被墙风险

QUIC 系协议在**只放行 TCP、限制 UDP 的网络**里会直接不可用或被 QoS 限速；但 UDP 流量本身比 TCP 更难深度检测，配合指纹仿冒后特征不明显。风险点主要是"UDP 被运营商针对"。

### 速度特性

弱网（高丢包）下**显著快于 TCP 系协议**，这是它的核心卖点；支持 0-RTT 降低握手延迟。代价：UDP 在某些网络环境（部分公司/校园网、运营商 QoS）会被限速甚至掐断。

### 客户端支持

mihomo（Clash Meta）、sing-box、官方客户端（Windows/macOS/Linux/Android）都支持；**Xray 系客户端不支持**（Xray-core 没有 Hysteria2 出站）。

---

## TUIC

### 原理

TUIC 是另一个 **基于 QUIC 的代理协议**，官方定位是"Delicately-TUICed 0-RTT proxy protocol"。它的设计目标：TCP/UDP 流量 **0-RTT** 代理、UDP 代理做到 Full Cone NAT 兼容、利用 QUIC 的多路复用和连接迁移能力。相比 Hysteria2 的"暴力提速"，TUIC 更强调**简单、低延迟**。注意：TUIC 官方仓库只维护**协议规范**（目前是 0x05 版），没有官方实现，实际用到的都是社区实现（如 Rust 版 hikari 等）。

### 加密与指纹

- 加密：TLS 1.3（QUIC 内建），支持 0-RTT；
- 指纹：QUIC 握手特征，社区实现陆续加入指纹仿冒能力。

### 被墙风险

与 Hysteria2 同类：走 UDP，受运营商 UDP 策略影响；没有 TLS 证书伪装需求，部署简单。

### 速度特性

0-RTT 让首包延迟很低，适合游戏、交互类场景；同样受"UDP 是否被 QoS"制约。

### 客户端支持

mihomo、sing-box 支持；Xray 系不支持。生态比 Hysteria2 小一些。

---

## 五张图看懂：横向对比总表

| 维度 | VLESS+Reality | Shadowsocks | Trojan | Hysteria2 | TUIC |
|:----|:----|:----|:----|:----|:----|
| 传输层 | TCP（TLS 1.3 借用手法） | TCP | TCP（真实 TLS） | UDP（QUIC） | UDP（QUIC） |
| 是否需要域名/证书 | ❌ 不需要 | ❌ 不需要 | ✅ 需要 | ❌ 不需要 | ❌ 不需要 |
| 指纹伪装能力 | 极强（真实网站握手） | 无（无 TLS 握手） | 强（真实证书+回落） | 强（Chrome QUIC 指纹仿冒） | 中（QUIC 指纹） |
| 抗主动探测 | 极强（无自签证书） | 弱 | 强（回落伪装） | 中 | 中 |
| 抗丢包/弱网 | 一般 | 一般 | 一般 | **极强**（Brutal） | 较强（QUIC） |
| 0-RTT 支持 | 规划中 | 无 | 无 | ✅ | ✅ |
| 客户端普及度 | 高（Xray 系/mihomo/sing-box） | **最高** | 高 | 中（mihomo/sing-box/官方客户端） | 中（mihomo/sing-box） |
| 老版 Clash 支持 | ❌ | ✅ | ✅ | ❌ | ❌ |
| 上手难度（自建） | 低（一键脚本多） | 低 | 中（要域名证书） | 低 | 低 |

---

## 怎么选：按场景对号入座

- **追求抗封锁 + 自建**：首选 **VLESS + Reality**。不用买域名、不用配证书、指纹干净，是目前自建最省心的方案（教程见下文）。
- **弱网环境（丢包高、信号差）**：考虑 **Hysteria2 / TUIC**。高铁、跨境、拥挤 Wi-Fi 下 QUIC 系有明显优势；但先确认你的网络不限制 UDP。
- **老设备 / 老客户端兼容**：**Shadowsocks** 是万能兜底，几乎所有客户端都能连。
- **已有域名证书、想低调稳定**：**Trojan** 表现稳，回落机制让它"看起来就是个网站"。
- **直接用机场**：协议由机场决定，你只需要选线路和客户端。机场普遍提供多协议订阅（同一订阅里 mihomo 会自动选可用协议），把 `clash-meta-guide.md` 里的策略组配好即可。

---

## 我们的实操：自用节点 = Xray + VLESS + Reality

我们自己搭的自用节点就是这套组合：VPS 上跑 Xray，VLESS + Reality（`flow: xtls-rprx-vision`），443 端口，指向一个国外支持 TLS 1.3 的目标网站做"借用"，客户端用 v2rayN / Clash Meta 连接。实际使用下来最直接的感受：

- 配置简单：没有域名、没有证书申请步骤，服务器端几段 JSON 就完事；
- 指纹干净：客户端模拟 Chrome，服务器无自签证书，连"证书链"这个攻击面都没有；
- 稳：作为长期自用节点没有遇到过针对性封端口的情况（当然，线路被 QoS 是另一回事，那是链路问题不是协议问题）。

完整搭建步骤（购买 VPS → 初始化 → Xray 安装 → Reality 配置 → 客户端连接）见我们的教程：
👉 [VPS 自建代理节点（Xray+Reality）](vps-xray-setup.md)

> 💡 不想折腾自建？机场订阅里其实也大量使用 VLESS+Reality / Hysteria2 这些协议，你完全不用关心底层——选对线路就行。不知道选哪家，看 [热门推荐](../README.md#-热门推荐)。

---

## 2026 年 8 月协议生态动态

- **Hysteria2 连续迭代**：v2.11.0（8/1）默认启用 Chrome QUIC 指纹仿冒；v2.12.0（8/6）加入 mimic（UDP 受限网络下伪装 TCP，仅 Linux）、提高仿冒精度；v2.12.1（8/9）修复手机待机/休眠后的慢重连（服务器发 QUIC stateless reset）。QUIC 系的"可观测性"正在快速补齐。
- **mihomo v1.19.29（7/18）**：同步 anytls 0.0.13，并支持 OpenVPN 的 TLS rekey / tls-crypt-v2 协商，shadowsocks 出站支持 jls、anytls 出站支持 restls。
- **Xray-core v26.7.28（7/28）**：发布预发布版（该版本未附带详细更新说明，正式版请关注仓库）。

更多细节与数据来源见 👉 [2026 年 8 月网络工具更新综述](tool-update-2026-08.md)

---

## 常见问题

### ❓ VLESS 和 VMess 有什么区别？

VLESS 是 XTLS 项目的新一代协议，设计上更精简（去掉了 VMess 的内置混淆与时间戳校验，`encryption: none`），把加密与伪装完全交给传输层（TLS/Reality）。VMess 是 V2Ray 老协议，自带加密，兼容老客户端。

### ❓ Hysteria2 比 VLESS+Reality 快吗？

看场景。弱网/高丢包下 Hysteria2（UDP + Brutal 固定速率）通常更快；普通干净线路上两者差距不大，VLESS+Reality 的生态和兼容性反而更好。另外 Hysteria2 依赖 UDP 畅通，公司网/部分运营商网络可能直接不可用。

### ❓ 为什么我的订阅在 Clash 里"节点全空"？

最常见原因是老版 Clash 内核不支持 VLESS/Hysteria2/TUIC。换 mihomo 内核的客户端（Clash Verge Rev、Clash Meta for Android 等）即可，我们的 [Clash Meta 规则实战](clash-meta-rules.md) 里有客户端选型说明。

### ❓ Shadowsocks 还值得用吗？

值得，但建议只作为兜底/兼容用途。2022 版协议本身很安全，但裸 SS 流量特征简单，直连被针对的风险高于带伪装层的协议。机场用 SS 时通常都会配中转/专线，用户体验反而好。

### ❓ 自建选哪个协议最省心？

VLESS+Reality。不需要域名证书、一键脚本多、客户端支持好，抗封锁能力也是第一梯队。我们的 [自建教程](vps-xray-setup.md) 就是用它。

### ❓ 协议会决定流媒体解锁吗？

不会。解锁取决于**落地节点的 IP**（是否原生 IP、是否被流媒体标记），协议只负责"怎么传"。所以看解锁表现要看线路和落地，不是看协议。

---

## 参考资源

- [XTLS/REALITY 官方仓库](https://github.com/XTLS/REALITY)（Reality 原理与配置）
- [XTLS/Xray-core](https://github.com/XTLS/Xray-core)（VLESS/Reality 实现）
- [Shadowsocks 2022 规范 SIP022](https://shadowsocks.org/doc/sip022.html)
- [apernet/hysteria 官方仓库](https://github.com/apernet/hysteria)（Hysteria2）
- [tuic-protocol/tuic 协议规范](https://github.com/tuic-protocol/tuic)
- [Clash Meta 官方文档](https://wiki.metacubex.one)（客户端规则与协议支持）
- 配套阅读：[VPS 自建代理节点（Xray+Reality）](vps-xray-setup.md) · [2026 年 8 月网络工具更新综述](tool-update-2026-08.md)

---

> 📝 本文为技术科普，协议能力以官方文档为准。协议在快速演进，建议每季度回看一次官方仓库的更新。
