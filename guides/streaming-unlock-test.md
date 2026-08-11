# 流媒体/服务解锁检测方法与工具

> "这个节点能不能看 Netflix？ChatGPT 能用吗？"——与其到处问人，不如自己测。这篇教你怎么用开源脚本、在线检测站和 curl 命令，自己判断一个节点/一台 VPS 的解锁情况，并讲清楚测试结果怎么看、有哪些坑。
>
> 🕐 更新时间：2026-08-11

---

## 📋 目录

- [为什么需要自己测解锁](#为什么需要自己测解锁)
- [先理解"解锁"的三种状态](#先理解解锁的三种状态)
- [方法一：curl 快速探测](#方法一curl-快速探测)
- [方法二：开源检测脚本（推荐）](#方法二开源检测脚本推荐)
- [方法三：在线检测站](#方法三在线检测站)
- [专项：ChatGPT 解锁检测](#专项chatgpt-解锁检测)
- [专项：Netflix 解锁检测](#专项netflix-解锁检测)
- [检测时的注意事项与坑](#检测时的注意事项与坑)
- [关于"实测数据"的说明](#关于实测数据的说明)
- [常见问题](#常见问题)
- [参考资源](#参考资源)

---

## 为什么需要自己测解锁

- 节点"能连上"≠"能解锁"：线路负责通不通，**落地 IP 负责解锁不解锁**，两者是两回事；
- 同一个机场不同节点解锁不同：香港、日本、美国节点的可用性各不一样，得按节点测；
- 解锁状态会变：流媒体平台会持续封禁被识别的机房 IP，今天解锁明天可能就不行。

掌握方法后，你可以在买机场前试用检测，也可以日常监测自己常用的节点。

---

## 先理解"解锁"的三种状态

| 状态 | 含义 | 典型表现 |
|:----|:----|:----|
| ✅ 解锁（原生可看） | 落地 IP 被目标服务认可，内容按该地区提供 | Netflix 显示当地片库、ChatGPT 正常可用 |
| ⚠️ 半解锁/仅浏览器 | 部分入口可用（如网页可开、App 被拒） | ChatGPT 网页能开、客户端提示"此区域不可用" |
| ❌ 未解锁 | IP 被识别为代理/机房或地区不支持 | Netflix 显示"您的地区无法观看"、ChatGPT 403 |

检测脚本的输出大多就是帮你区分这三者——注意别把"能打开登录页"当成"解锁"，下面会讲怎么区分。

---

## 方法一：curl 快速探测

零安装、任何电脑/手机终端都能跑的快速法：

### 1. 看出口 IP 与地区

```bash
# 走代理后执行（或在代理终端里），看你的出口 IP 属于哪个地区
curl -s https://ipinfo.io
curl -s https://ip.sb
```

### 2. 看 Cloudflare 边缘判断地区（cdn-cgi/trace）

ChatGPT、很多大站前端挂在 Cloudflare，访问它们的 `/cdn-cgi/trace` 能看到 Cloudflare 认为你来自哪个国家：

```bash
curl -s https://chat.openai.com/cdn-cgi/trace
# 关注 loc= 字段，比如 loc=US 表示 Cloudflare 判定你从美国访问
```

> ⚠️ `loc` 是 Cloudflare 边缘根据出口 IP 判断的国家，能快速确认"出口在哪"，但不等于目标服务一定解锁——解锁还要看目标服务的风控判断（见专项检测）。

### 3. 看 HTTP 状态码

```bash
# -o /dev/null 丢弃响应体，-w 输出状态码
curl -s -o /dev/null -w "%{http_code}\n" --max-time 10 https://www.netflix.com
```

403/451 通常意味着被区域限制或风控拒绝；200 也不能直接等于解锁（登录页人人都能开）。**状态码适合做初步判断，精确结论靠专项方法**。

---

## 方法二：开源检测脚本（推荐）

### 🏆 RegionRestrictionCheck（最全，推荐）

社区最主流的检测脚本，作者 lmc999，基于 CoiaPrant/MediaUnlock_Test 修改，覆盖几十项服务（Netflix、Disney+、YouTube、ChatGPT、Gemini、Claude、Bilibili、各流媒体……）。

```bash
# 一键安装并检测（在终端执行，脚本会检测当前网络出口）
bash <(curl -L -s check.unlock.media)

# 只看 IPv4 / 只看 IPv6
bash <(curl -L -s check.unlock.media) -M 4
bash <(curl -L -s check.unlock.media) -M 6

# 指定网卡检测（多网卡/软路由场景）
bash <(curl -L -s check.unlock.media) -I eth0

# 中文输出
bash <(curl -L -s check.unlock.media) -E zh
```

- 适合：Linux 服务器、软路由、装了代理客户端的电脑（终端里挂上代理即可测节点）；
- 输出示例格式：`Netflix: Yes (Region: US)` / `ChatGPT: No` / `YouTube Premium: Yes (Region: US)`；
- 想从源码看它怎么测的：仓库 [lmc999/RegionRestrictionCheck](https://github.com/lmc999/RegionRestrictionCheck) 的 check.sh，每个服务的检测函数都公开。

### netflix-verify（Netflix 专项）

作者 sjlleo 的 Go 脚本，专注 Netflix：能区分"原生解锁 / 仅自制剧 / 未解锁"，还会告诉你解锁的地区。

```bash
# 直接运行（当前出口）
bash <(curl -sL https://raw.githubusercontent.com/sjlleo/netflix-verify/master/netflix-verify.sh)
```

仓库：[sjlleo/netflix-verify](https://github.com/sjlleo/netflix-verify)

### StreamUnlockTest（多地区流媒体）

作者 LovelyHaochi 的脚本，覆盖香港/台湾/日本/韩国/美国/欧洲地区流媒体平台（Netflix、Disney+、YouTube、TikTok、iQiyi Global 等）。

```bash
bash <(curl -sSL "https://git.io/JswGm")
```

仓库：[LovelyHaochi/StreamUnlockTest](https://github.com/LovelyHaochi/StreamUnlockTest)

### IPQuality（IP 质量体检）

侧重"IP 干不干净"：是否被标记为机房/代理、欺诈风险分、IP 类型（原生/广播/家宽）等。对 ChatGPT、TikTok、跨境电商等风控敏感场景很有参考价值。

```bash
bash <(curl -sL https://raw.githubusercontent.com/xykt/IPQuality/main/ipq.sh)
```

仓库：[xykt/IPQuality](https://github.com/xykt/IPQuality)

> 💡 脚本检测的是"当前网络出口"。想在电脑上测某个节点：先让终端走该节点的代理（Clash/Mihomo 的 TUN 模式、或设置 http_proxy 环境变量），再运行脚本。测 VPS：直接 SSH 到服务器上跑。

---

## 方法三：在线检测站

不想装脚本？用网页检测站。原理同样是"以你的出口 IP 去探测各服务"：

- **[IP.Check.Place](https://ip.check.place)**：较知名的 IP 解锁/质量在线检测站，同时提供命令行版（`bash <(curl -Ls https://IP.Check.Place)`）；
- **[IPCheck.ing](https://ipcheck.ing/)**：开源的 IP 工具箱，IP 归属/类型、流媒体与 AI 服务解锁、IP 纯净度、WebRTC/DNS 泄露检测都有；
- **其他 IP 透视类站点**（如 iptoushi.com 等）：主打 IP 纯净度与风险评分，适合跨境电商账号安全自查。

在线站的注意点：它测的是你**浏览器的出口**，和脚本是同一原理；选择支持"以你当前 IP 检测"的站点即可，不需要登录注册。

---

## 专项：ChatGPT 解锁检测

ChatGPT 的检测逻辑公开透明（RegionRestrictionCheck 源码里就有），核心是两个接口：

```bash
# 1. OpenAI 合规接口：返回内容里含 unsupported_country 说明该地区不被支持
curl -s https://api.openai.com/compliance/cookie_requirements

# 2. iOS 入口：返回内容里含 "VPN" 相关提示说明你的 IP 被标记（仅网页可用）
curl -s https://ios.chat.openai.com/
```

组合解读（与脚本逻辑一致）：

| 接口1（api.openai.com） | 接口2（ios.chat.openai.com） | 结论 |
|:----|:----|:----|
| 无 unsupported_country | 无 VPN 提示 | ✅ 完全解锁 |
| 无 unsupported_country | 有 VPN 提示 | ⚠️ 仅浏览器可用（App 被拒） |
| 有 unsupported_country | 有 VPN 提示 | ❌ 未解锁 |
| 有 unsupported_country | 无 VPN 提示 | ⚠️ 仅移动 App 可用 |

另外可以配合 `curl -s https://chat.openai.com/cdn-cgi/trace` 看 `loc=` 判断出口地区。

---

## 专项：Netflix 解锁检测

Netflix 的判断关键是"**能不能看到该地区的片库**"，而不是"能不能打开 netflix.com"。社区脚本的通用做法：请求一个**指定的剧集页面**（比如 `https://www.netflix.com/title/81280792` 这类公开测试标题），带上浏览器 UA 和 Cookie：

- 页面内容包含 **Not Available / 该地区无法观看** 之类的提示 → 该地区**未解锁**；
- 页面正常返回剧集内容（可看、有片名信息）→ **解锁**，同时可以通过返回内容判断解锁地区；
- 配合 Netflix 的注册地区接口可以区分"原生解锁 / 仅看自制剧 / 完全不可用"。

这一套逻辑直接用现成脚本最省事（RegionRestrictionCheck 的 Netflix 函数、netflix-verify 都能给出"原生/自制剧/不可用+地区"的结论），不必自己拼请求。

---

## 检测时的注意事项与坑

1. **区分"能开页面"与"能播放"**：登录页/落地页人人能开，判断解锁要看片库/内容接口的返回，脚本和上述专项方法就是为此设计的；
2. **IPv4 / IPv6 分开测**：很多节点 IPv4 解锁但 IPv6 没走代理（或反之），脚本的 `-M 4` / `-M 6` 就是干这个的；软路由场景还要留意 DNS 是否把请求解析到直连的 IPv6；
3. **别在直连状态下测节点**：脚本测的是"当前出口"，忘了挂代理会测成你自己的宽带 IP，结论毫无意义；
4. **DNS 污染/本地解析会干扰**：DNS 配置不对时，域名可能被解析到错误地址，检测结果失真——Clash 用户先确认 [DNS 配置](clash-meta-guide.md#22-dns-配置防-dns-泄露) 正常；
5. **解锁状态会变**：一次 Yes 不代表永远 Yes，风控是动态的；重要场景建议定期复测；
6. **结果以"当前时刻+当前节点"为准**：换节点、换线路、换时段（晚高峰）都可能不同。

---

## 关于"实测数据"的说明

我们仓库的评测/入口页里，涉及流媒体解锁的结论都遵循同一口径：**我们只整理服务商公开标注的信息，没有逐一实测的，一律标注"未实测"**（可对照 [评测页](../airports/featured/) 的标注）。这篇只讲"怎么测"，不承诺任何机场的解锁表现——方法教给你，结论你自己跑一遍最可信。

> 🔬 想验证一台 VPS 的解锁表现（自建节点场景）？SSH 上去跑一遍 RegionRestrictionCheck 即可，5 分钟出全量报告。

---

## 常见问题

### ❓ 检测脚本安全吗？

这类脚本都是"下载执行"，建议只从官方仓库/官方短链运行（上文的链接均为项目官方来源），不要运行来路不明的"整合版"。想看脚本干了什么，直接读源码（都是 bash，可读）。

### ❓ 我在 Clash 里怎么测某个具体节点？

开 TUN 模式让终端流量也走代理，然后运行脚本；或者用客户端内置的"节点测试"工具看延迟（延迟≠解锁）。要精确测解锁，用本文方法配合 TUN 模式。

### ❓ 为什么同一个机场，两个香港节点解锁不一样？

落地 IP 不同。节点 A 可能用原生香港 IP，节点 B 可能是被 Netflix 标记的机房 IP。选节点时以实测为准。

### ❓ 脚本显示"Failed (Network Connection)"怎么回事？

通常是你当前没挂代理/代理没生效，或目标服务接口变了。先确认出口，再重试。

### ❓ YouTube 需要检测吗？

YouTube 本身基本不限地区，但要区分"能看"和"YouTube Premium 会员权益所在区"（Premium 价格/权益按区）。脚本会单独检测 YouTube Premium 的地区，订阅过 Premium 的用户可以留意。

### ❓ 手机/路由器上怎么测？

手机上用 Termux 跑 bash 脚本；路由器（OpenWrt/软路由）SSH 进去跑，注意加 `-I` 指定正确的出口网卡。

---

## 参考资源

- [lmc999/RegionRestrictionCheck](https://github.com/lmc999/RegionRestrictionCheck)（全平台检测脚本，含 ChatGPT/Netflix 检测源码）
- [sjlleo/netflix-verify](https://github.com/sjlleo/netflix-verify)（Netflix 专项）
- [LovelyHaochi/StreamUnlockTest](https://github.com/LovelyHaochi/StreamUnlockTest)（多地区流媒体检测）
- [xykt/IPQuality](https://github.com/xykt/IPQuality)（IP 质量体检）
- [IP.Check.Place](https://ip.check.place) / [IPCheck.ing](https://ipcheck.ing/)（在线检测站）
- 配套阅读：[Clash Meta 规则实战](clash-meta-rules.md)（分流与 DNS）· [机场架构科普](airport-architecture.md)（落地/原生 IP 概念）

---

> 📝 检测方法会随服务商接口变化而失效，脚本仓库都在持续维护；如果某个命令失效，去对应仓库看最新用法。
