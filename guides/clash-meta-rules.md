# Clash Meta 规则写法实战：匹配优先级与策略组设计

> 入门教程教你"抄一份能用的配置"，这篇教你"写出自己的规则"：规则类型怎么选、匹配顺序怎么排、策略组用哪种、为什么你的规则"不生效"。看完你就能看懂任何一份高级订阅的 rules 是怎么设计的。
>
> 🕐 更新时间：2026-08-11

---

## 📋 目录

- [这篇和入门教程的区别](#这篇和入门教程的区别)
- [规则匹配机制：先记住这条铁律](#规则匹配机制先记住这条铁律)
- [规则类型速查表](#规则类型速查表)
- [匹配优先级的实战约定](#匹配优先级的实战约定)
- [策略组设计：select / url-test / fallback / load-balance](#策略组设计select--url-test--fallback--load-balance)
- [完整实战：一套"直连/代理/流媒体"分流](#完整实战一套直连代理流媒体分流)
- [我们的实操：OpenClash 软路由 + mihomo 热更新](#我们的实操openclash-软路由--mihomo-热更新)
- [常见翻车与排查](#常见翻车与排查)
- [常见问题](#常见问题)
- [参考资源](#参考资源)

---

## 这篇和入门教程的区别

入门篇 [Clash Meta 进阶配置](clash-meta-guide.md) 给的是"能直接用的完整配置"（DNS、TUN、策略组、基础规则都有）；这篇聚焦**规则与策略组的设计思路**——不给你一整份配置，而是给你"会写、会改、会排查"的能力。建议先过一遍入门篇再读这篇。

---

## 规则匹配机制：先记住这条铁律

mihomo（Clash Meta）官方文档的原话：

> **Rules will be matched in order from top to bottom, with the rules at the top having higher priority than those below.**（规则按从上到下的顺序匹配，靠前的规则优先级更高。）

也就是说：**规则的"优先级"完全由你在文件里的顺序决定**，不存在"GEOIP 天生比 DOMAIN-SUFFIX 优先"这种内置规则。一次请求进来：

```
请求 → 从 rules 第一条开始逐条比对
        ├── 命中 → 走该规则指定的策略，停止匹配
        ├── 未命中 → 比对下一条
        └── 全部未命中 → 走到最后一条（通常放 MATCH 兜底）
```

一个常见的错误理解是"把最精确的规则放最后"。恰恰相反——**越具体、越需要优先处理的规则要放越上面**，越宽泛的兜底放越下面。比如"Netflix 走流媒体组"必须排在"国内直连"前面，否则 `DOMAIN-SUFFIX,cn` 或 `GEOIP,CN,DIRECT` 先命中，Netflix 域名永远到不了流媒体组。

### 一个容易被忽略的机制：域名规则 vs IP 规则

- **域名类规则**（DOMAIN / DOMAIN-SUFFIX / DOMAIN-KEYWORD / DOMAIN-WILDCARD / DOMAIN-REGEX / GEOSITE / RULE-SET 里的域名规则）：直接拿请求的域名比对，**不需要先解析 IP**，命中即生效；
- **IP 类规则**（IP-CIDR / IP-CIDR6 / IP-ASN / GEOIP）：如果请求目标是个域名，mihomo 会**先解析出 IP 再比对**——这引入了 DNS 环节，也会让请求"看起来"慢一点；
- **兜底**：`no-resolve` 参数可以让 IP 规则跳过"为比对而解析"这一步（比如 `GEOIP,CN,DIRECT,no-resolve`），常用于你不希望某条 IP 规则触发额外 DNS 解析的场景。

---

## 规则类型速查表

| 规则类型 | 写法示例 | 作用 | 常用场景 |
|:----|:----|:----|:----|
| DOMAIN | `DOMAIN,www.google.com,Proxy` | 精确匹配整个域名 | 单域名强制走某策略 |
| DOMAIN-SUFFIX | `DOMAIN-SUFFIX,google.com,Proxy` | 匹配域名及其所有子域名 | 最常用的域名规则 |
| DOMAIN-KEYWORD | `DOMAIN-KEYWORD,youtube,Proxy` | 域名里含关键词即命中 | 域名太多懒得枚举时 |
| DOMAIN-WILDCARD | `DOMAIN-WILDCARD,*.google.*,Proxy` | 通配符匹配域名 | 灵活匹配 |
| DOMAIN-REGEX | `DOMAIN-REGEX,^.+\.goo.+$,Proxy` | 正则匹配域名 | 复杂批量场景 |
| GEOSITE | `GEOSITE,cn,DIRECT` | 按"域名分类库"匹配（国内站点库/Google 库等） | 一键覆盖大量域名 |
| IP-CIDR | `IP-CIDR,192.168.0.0/16,DIRECT` | 匹配 IP 段 | 内网/特定机房直连 |
| IP-ASN | `IP-ASN,13335,DIRECT` | 按 ASN（运营商编号）匹配 | 按"哪家 CDN"分流 |
| GEOIP | `GEOIP,CN,DIRECT` | 按 IP 所属国家/地区匹配 | 国内 IP 直连 |
| PROCESS-NAME | `PROCESS-NAME,curl.exe,Proxy` | 按客户端进程名匹配 | 让某程序单独走代理 |
| DST-PORT | `DST-PORT,443,Proxy` | 按目标端口匹配 | 常见于端口级兜底 |
| RULE-SET | `RULE-SET,ads,REJECT` | 引用外部规则集文件 | 复用社区规则 |
| MATCH | `MATCH,Proxy` | 匹配一切（必须放最后） | 兜底策略 |

> 💡 常用外部规则集：Loyalsoldier/clash-rules（分门别类维护，质量高），配合 `rule-providers` 使用可以自动更新。入门篇的 [参考资源](clash-meta-guide.md#参考资源) 里也提到过。

---

## 匹配优先级的实战约定

虽然引擎是"顺序优先"，但社区实践中有一个推荐的排列范式，能让规则**更快命中、更好维护**：

```
1. 放行/特殊处理最优先（如内网直连、特定域名强制某策略）
2. 广告拦截（REJECT）——越早拒绝越省事
3. 需要走"专用策略组"的精确规则（流媒体、AI 工具、游戏平台）
4. 大分类域名规则（GEOSITE,google / GEOSITE,cn 等）
5. IP 类规则（GEOIP,CN / IP-CIDR）——放在域名规则之后
6. 进程/端口规则
7. MATCH 兜底
```

为什么 IP 类放后面？因为域名规则可以免解析直接命中；如果一堆 GEOIP 放前面，每个新域名请求都要先解析再比对，既慢又可能因 DNS 结果不同产生"时好时坏"的分流。IP 类规则适合做"最后一道防线"（比如所有没被域名规则覆盖的国内 IP 直连）。

另一个实战细节：**精确规则要放在宽泛规则之前**。典型反例：

```yaml
# ❌ 错误：GEOIP,CN 太靠前，会截胡后面的流媒体规则
rules:
  - GEOIP,CN,DIRECT
  - DOMAIN-SUFFIX,netflix.com,🎬 流媒体   # 永远匹配不到
  - MATCH,🌍 代理

# ✅ 正确：精确的流媒体规则在前，GEOIP 兜底在后
rules:
  - DOMAIN-SUFFIX,netflix.com,🎬 流媒体
  - DOMAIN-SUFFIX,disneyplus.com,🎬 流媒体
  - GEOIP,CN,DIRECT
  - MATCH,🌍 代理
```

---

## 策略组设计：select / url-test / fallback / load-balance

策略组（proxy-groups）决定"命中这条规则的流量交给谁"。四种内置类型各有适用场景：

| 类型 | 行为 | 适用场景 |
|:----|:----|:----|
| **select** | 手动选择，记住你的选择 | 需要自己控制的组：手动切换节点、流媒体组、游戏组 |
| **url-test** | 定时测延迟，自动选**当前最快**的 | 节点质量都差不多的"自动选择"组；注意它会频繁测速，且可能跳来跳去 |
| **fallback** | 按顺序用，**第一个可用**就坚持用，挂了才换下一个 | 有明确主备关系的场景：主节点 > 备用节点 |
| **load-balance** | 按规则在多个节点间分摊连接 | 多节点下载加速、连接数特别多的场景（游戏/TCP 长连接慎用） |

### 设计要点

1. **策略组可以嵌套**：顶级组通常用 select，里面挂子组（自动选择、流媒体、游戏……），这样手动切换时既能选"组"也能选"具体节点"；
2. **url-test 加 tolerance**：延迟差在 50ms 以内的节点不频繁切换，避免"抖"；
3. **fallback 的 interval 可以设短一点**（如 60s），故障切换更及时；
4. **load-balance 别套在游戏上**：同一会话的连接被分散到不同节点，部分服务会掉登录/掉线。

一个典型的组结构：

```yaml
proxy-groups:
  # 顶级：手动选择，嵌套子组
  - name: 🌍 默认出口
    type: select
    proxies:
      - 🚀 自动选择
      - 🎬 流媒体
      - 🎮 游戏
      - 香港-01
      - 日本-01
      - DIRECT

  # 自动选择：延迟最低者
  - name: 🚀 自动选择
    type: url-test
    url: http://www.gstatic.com/generate_204
    interval: 300
    tolerance: 50

  # 流媒体：手动选解锁节点
  - name: 🎬 流媒体
    type: select
    proxies:
      - 🚀 自动选择
      - 香港-解锁
      - 日本-解锁

  # 游戏：主备切换
  - name: 🎮 游戏
    type: fallback
    proxies:
      - 香港-01
      - 日本-01
    url: http://www.gstatic.com/generate_204
    interval: 60
```

---

## 完整实战：一套"直连/代理/流媒体"分流

把上面两个小节合起来，一份进阶 rules 的长这样（省略 DNS/TUN，入门篇有）：

```yaml
proxy-groups:
  - name: 🌍 默认出口
    type: select
    proxies: [🚀 自动选择, 🎬 流媒体, DIRECT]
  - name: 🚀 自动选择
    type: url-test
    url: http://www.gstatic.com/generate_204
    interval: 300
    tolerance: 50
  - name: 🎬 流媒体
    type: select
    proxies: [🚀 自动选择, DIRECT]

rule-providers:
  ads:
    type: http
    behavior: domain
    url: "https://cdn.jsdelivr.net/gh/Loyalsoldier/clash-rules@release/reject.txt"
    path: ./ruleset/ads.yaml
    interval: 86400

rules:
  # 1. 内网/本机直连（最高优先）
  - IP-CIDR,192.168.0.0/16,DIRECT,no-resolve
  - IP-CIDR,10.0.0.0/8,DIRECT,no-resolve
  - IP-CIDR,127.0.0.0/8,DIRECT,no-resolve

  # 2. 广告拦截（其次）
  - RULE-SET,ads,REJECT

  # 3. 精确规则：流媒体走专用组（放 GEOIP 前面！）
  - DOMAIN-SUFFIX,netflix.com,🎬 流媒体
  - DOMAIN-SUFFIX,disneyplus.com,🎬 流媒体
  - DOMAIN-SUFFIX,youtube.com,🎬 流媒体
  - DOMAIN-SUFFIX,hbo.com,🎬 流媒体

  # 4. 大分类域名：AI / 常用海外
  - DOMAIN-SUFFIX,openai.com,🌍 默认出口
  - DOMAIN-SUFFIX,chatgpt.com,🌍 默认出口
  - DOMAIN-SUFFIX,google.com,🌍 默认出口
  - DOMAIN-SUFFIX,github.com,🌍 默认出口

  # 5. 国内大分类（GEOSITE 一键覆盖）
  - GEOSITE,cn,DIRECT

  # 6. IP 兜底：国内 IP 直连（no-resolve 可避免多余解析）
  - GEOIP,CN,DIRECT,no-resolve

  # 7. 最终兜底
  - MATCH,🌍 默认出口
```

注意第 6 行 `no-resolve` 的用法：这里我们已经在第 5 步用 GEOSITE 处理过"域名已知"的情况，GEOIP 主要是拦截"域名未知但 IP 是国内的"，加 `no-resolve` 可以避免让 mihomo 为每条未命中域名再解析一次——性能更稳，代价是"纯 IP 请求"不会被 GEOIP 拦截（视你的场景决定加不加）。

---

## 我们的实操：OpenClash 软路由 + mihomo 热更新

我们的软路由方案是 OpenClash（OpenWrt 上的 Clash 客户端），内核就是 mihomo。日常维护规则时用到的两个真实技巧：

1. **改规则不用重启**：mihomo 支持通过外部控制器（external-controller，配置里常写 9090 端口）热加载配置。我们写了一个小脚本：改完 rules 后调用 `PUT /configs?force=true` 重载，OpenClash 面板里的"重载配置"也是同一个原理。这样深夜调规则不会打断全家设备正在跑的连接。
2. **规则按文件组织**：`rules/` 下拆成 direct / proxy / streaming 等小文件，配合 `rule-providers` 的远程规则集，家里网关的 rules 一直保持"能看懂"的状态。路由器上规则写错的影响面是全家，所以务必遵循"精确在前、兜底在后"。

> 💡 想了解软路由全局代理的完整配置，看 [路由器 OpenClash 配置](openclash-setup.md)。

---

## 常见翻车与排查

| 现象 | 原因 | 排查/修复 |
|:----|:----|:----|
| 某网站一直走错策略 | 它被更靠前的宽泛规则命中了 | 把它的精确规则移到上面，或检查 GEOSITE/GEOIP 是否截胡 |
| 规则改了"没生效" | 配置没重载 / 内核有缓存 | 用 external-controller 重载配置（见上文热更新） |
| 域名请求时快时慢 | IP 类规则放太前，每次都要解析 | 域名规则前置，IP 规则后置/加 no-resolve |
| 国内网站走了代理变慢 | GEOIP,CN 没写或位置太靠后 | 确认 `GEOIP,CN,DIRECT` 在 MATCH 之前 |
| DNS 泄露（访问 ip.sb 显示本地 IP 但域名走了代理） | DNS 配置里 fallback 判断失效 | 回入门篇检查 [DNS 配置](clash-meta-guide.md#22-dns-配置防-dns-泄露) |
| 流媒体节点"测速很快但看不了" | 解锁与延迟是两回事 | 用 [流媒体解锁检测方法](streaming-unlock-test.md) 单独验证解锁 |
| 游戏掉线 | load-balance 把连接分散到多节点 | 游戏组改用 select/fallback，单节点出口 |

---

## 常见问题

### ❓ DOMAIN 和 DOMAIN-SUFFIX 差在哪？

DOMAIN 精确匹配整个域名（`DOMAIN,www.google.com` 不含 `google.com` 本身）；DOMAIN-SUFFIX 匹配域名及所有子域名（`DOMAIN-SUFFIX,google.com` 同时覆盖 `www.google.com`、`mail.google.com`）。

### ❓ 为什么推荐 GEOSITE 而不是自己枚举域名？

GEOSITE 是维护好的域名分类库（cn 库、google 库等），一条规则覆盖成百上千域名，比自己手写靠谱得多。想精确控制某些站点，再用 DOMAIN-SUFFIX 单独覆盖（放在 GEOSITE 前面）。

### ❓ url-test 的 tolerance 有什么用？

tolerance（毫秒）表示"延迟相差多少以内不切换"。比如 tolerance: 50，A 节点 100ms、B 节点 120ms，B 不会抢走连接；避免测速波动导致节点频繁跳动。

### ❓ fallback 和 url-test 能不能混用？

能。常见做法：外层 fallback 组管"主备线路"，内层 url-test 管"当前线路内选最优节点"。层级嵌套是规则设计的常用手段。

### ❓ 需要 MATCH 吗？没有会怎样？

必须有（或确保最后一条规则一定命中）。mihomo 没有 MATCH 时，未命中的流量会走默认策略——很多配置默认是直连，结果就是"漏网流量全部裸连"，该代理的没代理。MATCH 放最后，配一个兜底策略组，是最稳妥的写法。

---

## 参考资源

- [mihomo 官方文档：Route Rules](https://wiki.metacubex.one/en/config/rules/)（规则类型与匹配顺序的权威说明）
- [mihomo 官方文档：Proxy-Groups](https://wiki.metacubex.one/en/config/proxy-groups/)
- [Loyalsoldier/clash-rules](https://github.com/Loyalsoldier/clash-rules)（常用规则集）
- [入门篇：Clash Meta 进阶配置](clash-meta-guide.md)（DNS/TUN 等基础）
- 配套阅读：[路由器 OpenClash 配置](openclash-setup.md) · [流媒体解锁检测方法](streaming-unlock-test.md)

---

> 📝 规则配置是"越用越懂"的活：先抄一份能跑的，再按这篇的思路一步步改成自己的。改坏了就回滚配置，不会把设备搞坏。
