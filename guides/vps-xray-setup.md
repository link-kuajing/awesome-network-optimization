# 🛡️ VPS 自建代理节点（Xray+Reality）

> 不想用机场？自己租一台 VPS 搭建私有代理节点。更快、更稳、IP 更干净、没有跑路风险。

---

## 📋 目录

- [为什么要自建？](#为什么要自建)
- [前置条件](#前置条件)
- [方案选型](#方案选型)
- [第一步：购买 VPS](#第一步购买-vps)
- [第二步：服务器初始化](#第二步服务器初始化)
- [第三步：安装 Xray+Reality](#第三步安装-xrayreality)
- [第四步：客户端配置](#第四步客户端配置)
- [第五步：优化与安全](#第五步优化与安全)
- [对比：自建 vs 机场](#对比自建-vs-机场)
- [常见问题](#常见问题)

---

## 为什么要自建？

| 对比项 | 机场 | 自建 |
|:------|:----|:----|
| **IP 纯净度** | 共享 IP，容易风控 | **独享 IP**，几乎不会被风控 |
| **速度** | 晚高峰拥堵 | **独享带宽**，你用多少就是多少 |
| **隐私** | 服务商能看到你的流量 | **数据在你自己手里** |
| **稳定性** | 可能跑路/被封 | **只要 VPS 不倒就能用** |
| **成本** | ¥5~¥30/月 | ¥30~¥60/年（RackNerd）起 |
| **麻烦程度** | 即买即用 | 需要一些技术操作 |

**适合自建的人群：**
- 🔐 对隐私要求高（不愿让第三方看到你的网络行为）
- 🎯 需要纯净 IP（币圈交易、TikTok运营、AI账号注册）
- 🔧 有一定动手能力
- 💰 追求长期性价比

---

## 前置条件

| 条件 | 说明 |
|:----|:-----|
| 🖥️ **VPS 一台** | 海外服务器，推荐 CN2 GIA 线路（中国大陆优化） |
| 🌐 **域名（可选）** | Reality 协议不依赖域名，但有域名方便后续扩展 |
| 💻 **SSH 客户端** | Windows 用 PuTTY，Mac/Linux 直接用终端 |

### 推荐 VPS

| VPS | 线路 | 月付 | 推荐理由 |
|:----|:----|:----:|:---------|
| **BandwagonHost CN2 GIA** | 电信直连 | ¥3.5+/月 | ✅ 中国优化线路，晚高峰不丢包 |
| **RackNerd** | 普通线路 | ¥1/月 | ✅ ¥10/年白菜价，适合练手 |
| **HostDare CN2 GT** | 电信优化 | ¥3/月 | ✅ 性价比不错 |
| **DMIT** | 高端 CN2 GIA | ¥7+/月 | ✅ 顶级线路，对延迟有极致要求 |

> 💡 **新手推荐：** 先用 RackNerd ¥10/年练手，学会后再上车 BandwagonHost CN2 GIA。

---

## 方案选型

### 主流自建协议对比

| 协议 | 速度 | 安全性 | 隐蔽性 | 部署难度 | 推荐场景 |
|:----|:---:|:-----:|:-----:|:-------:|:---------|
| **Xray+Reality** ⭐ | 🚀🚀🚀 | 🛡️🛡️🛡️ | 👻👻👻 | 🟡 中等 | **首选方案，没有之一** |
| Hysteria 2 | 🚀🚀🚀🚀 | 🛡️🛡️ | 👻 | 🟢 简单 | 移动网络/UDP 优化 |
| Shadowsocks | 🚀🚀 | 🛡️ | 👻 | 🟢 简单 | 老牌协议，兼容性最好 |
| Trojan | 🚀🚀🚀 | 🛡️🛡️ | 👻👻 | 🟢 简单 | 需要域名+证书 |

**本文以 Xray+Reality 为主**，因为它：
- ✅ **最高隐蔽性**——流量伪装成普通 HTTPS 访问，无法被识别
- ✅ **不需要域名**——直接借用其他网站的 TLS 证书（域名伪装）
- ✅ **没有指纹特征**——XTLS Vision 流控技术，没有握手特征
- ✅ **不被主动探测**——没有标准 TLS 握手，GFW 无法主动探测

---

## 第一步：购买 VPS

> 如果你还没有 VPS，先通过我们的 [VPS选购指南](../vps/README.md) 选一台。

**购买要点：**
- **机房选择：** 洛杉矶（离中国近，延迟低）
- **线路选择：** CN2 GIA > CN2 GT > 普通线路
- **最低配置：** 512MB 内存 + 1核 CPU 就够用
- **操作系统：** 选 Debian 11/12 或 Ubuntu 22.04

购买完成后，你会收到一封邮件，包含：
- **服务器 IP 地址**
- **SSH 用户名和密码**（通常是 root）
- **SSH 端口**（默认 22）

---

## 第二步：服务器初始化

SSH 登录服务器后，先做基础配置：

```bash
# ① 更新系统
apt update && apt upgrade -y

# ② 修改 SSH 端口（防爆破）
sed -i 's/#Port 22/Port 2222/' /etc/ssh/sshd_config
systemctl restart sshd
# ⚠️ 先新开一个终端测试能否用新端口登录，确认后再关当前连接

# ③ 配置防火墙
apt install ufw -y
ufw allow 2222/tcp    # SSH 新端口
ufw allow 80/tcp      # HTTP（伪装用）
ufw allow 443/tcp     # HTTPS（伪装用）
ufw enable

# ④ 开启 BBR（TCP 加速）
echo "net.core.default_qdisc=fq" >> /etc/sysctl.conf
echo "net.ipv4.tcp_congestion_control=bbr" >> /etc/sysctl.conf
sysctl -p
# 验证：lsmod | grep bbr
```

---

## 第三步：安装 Xray+Reality

### 方法一：一键脚本（推荐新手）

```bash
bash -c "$(curl -L https://github.com/XTLS/Xray-install/raw/main/install-release.sh)" @ install
```

脚本安装完成后，编辑配置文件：

```bash
# Xray 配置路径
vim /usr/local/etc/xray/config.json
```

### 方法二：配置示例（全功能版）

```json
{
  "log": {
    "loglevel": "warning"
  },
  "inbounds": [
    {
      "port": 443,
      "protocol": "vless",
      "settings": {
        "clients": [
          {
            "id": "你的UUID",            // 用 xray uuid 命令生成
            "flow": "xtls-rprx-vision"
          }
        ],
        "decryption": "none"
      },
      "streamSettings": {
        "network": "tcp",
        "security": "reality",
        "realitySettings": {
          "dest": "www.microsoft.com:443",   // 伪装站点
          "serverNames": [
            "www.microsoft.com",
            "www.bing.com"
          ],
          "privateKey": "你的私钥",           // 用 xray x25519 命令生成
          "shortIds": [
            "6ba85179e30d4fc2"
          ]
        }
      }
    }
  ],
  "outbounds": [
    {
      "protocol": "freedom",
      "tag": "direct"
    }
  ]
}
```

### 生成配置所需密钥

```bash
# 生成 UUID
xray uuid

# 生成 Reality 密钥对（公钥+私钥）
xray x25519
```

### 重启 Xray 使配置生效

```bash
systemctl restart xray
systemctl status xray  # 确认运行正常
```

### 一键脚本替代方案

如果手动配置觉得麻烦，也可以用社区维护的一键脚本（如 [Xray-REALITY](https://github.com/zxcvos/Xray-REALITY)）：

```bash
bash <(curl -sL https://raw.githubusercontent.com/zxcvos/Xray-REALITY/main/install.sh)
```

---

## 第四步：客户端配置

### 获取节点信息

配置完成后，整理以下信息用于客户端：

| 字段 | 值 |
|:----|:----|
| 地址 | 你的 VPS IP |
| 端口 | 443 |
| 用户ID | 上一步生成的 UUID |
| 流控 | xtls-rprx-vision |
| 传输协议 | tcp |
| 伪装类型 | none |
| 安全 | reality |
| 伪装域名 | www.microsoft.com |
| 公钥 | 上一步生成的公钥 |
| shortId | 配置中的 shortId |
| SpiderX | / |

### Windows (v2rayN)

1. 下载 [v2rayN](https://github.com/2dust/v2rayN/releases)
2. 点击 **「服务器」→「添加 VLESS 服务器」**
3. 填入上面的节点信息
4. 点击 **「确定」**
5. 右键服务器列表中的节点 → **「设为活动服务器」**
6. 开启 **「系统代理」**

### Android (v2rayNG)

1. 下载 [v2rayNG](https://play.google.com/store/apps/details?id=com.v2ray.ang)
2. 点击右上角 **「+」→「手动输入」**
3. 选择 **VLESS** 协议
4. 填入节点信息
5. 点击右上角 **「✓」** 保存
6. 点击节点连接

### iOS (Shadowrocket / Stash)

1. 下载 Shadowrocket 或 Stash
2. 点击右上角 **「+」**
3. 选择 **VLESS** 协议
4. 填写节点信息
5. 保存并启用

### Clash Meta 配置（如果通过 Clash 使用）

```yaml
proxies:
  - name: "我的自建节点"
    type: vless
    server: 你的VPS_IP
    port: 443
    uuid: 你的UUID
    network: tcp
    tls: true
    udp: true
    flow: xtls-rprx-vision
    reality-opts:
      public-key: 你的公钥
      short-id: 你的shortId
    client-fingerprint: chrome
```

---

## 第五步：优化与安全

### BBR 加速（已开启）

确保 BBR 已生效：

```bash
sysctl net.ipv4.tcp_congestion_control
# 输出应显示: tcp_congestion_control = bbr
```

### Fail2ban（防SSH爆破）

```bash
apt install fail2ban -y
systemctl enable fail2ban
systemctl start fail2ban
```

### 定期更新

```bash
# 更新 Xray
xray update

# 更新系统
apt update && apt upgrade -y
```

### 监控流量

```bash
# 安装 iftop 查看实时流量
apt install iftop -y
iftop -i eth0

# 用 vnstat 统计月度流量
apt install vnstat -y
vnstat -m
```

---

## 对比：自建 vs 机场

```
┌──────────────────────────────────────────────┐
│              怎么选？一张图看懂               │
├────────────┬─────────────┬───────────────────┤
│   你的需求   │   推荐方案   │      理由        │
├────────────┼─────────────┼───────────────────┤
│ 新手尝鲜    │ 机场 ¥6/月  │ 便宜省事，先体验   │
│ 日常上网    │ 机场        │ 性价比高，节点多   │
│ 币圈交易    │ 自建        │ 纯净IP，不被封     │
│ TikTok运营  │ 自建        │ 原生IP最重要       │
│ 看Netflix   │ 机场        │ 机场有解锁节点     │
│ 高隐私要求   │ 自建        │ 数据流经自己手     │
│ 大流量下载   │ 机场+自建   │ 机场大流量+自建关键 │
│ 纯技术学习   │ 自建        │ 本身就在学         │
└────────────┴─────────────┴───────────────────┘
```

**组合使用是最优解：**
> 主力用机场（多节点、流媒体解锁），关键场景（币安交易、AI 注册）切自建节点。

---

## 常见问题

### ❓ 速度还不如机场？

- 检查 VPS 是否离你太远（选洛杉矶机房延迟最低）
- 确认开启了 BBR
- 确认 VPS 线路不是绕路线路（避开 CN2 以外的便宜VPS）
- **BandwagonHost CN2 GIA** 是中国大陆优化线路，其他 VPS 可能走普通线路

### ❓ IP 被墙了怎么办？

- 阿里云/腾讯云海外版：换 IP 免费或低至 ¥5/次
- BandwagonHost：后台可以免费换 IP（有限制次数）
- RackNerd：换 IP 收费 $3~$5
- 一般只要不是主动探测扫描，IP 不太会被墙

### ❓ 一个 VPS 能同时给几个人用？

可以。配置文件中 `clients` 数组可以添加多个用户：

```json
"clients": [
  {"id": "用户1的UUID", "flow": "xtls-rprx-vision"},
  {"id": "用户2的UUID", "flow": "xtls-rprx-vision"},
  {"id": "用户3的UUID", "flow": "xtls-rprx-vision"}
]
```

### ❓ 需要定期维护吗？

| 维护项 | 频率 |
|:------|:----:|
| 系统更新 | 每月一次 |
| Xray 更新 | 新版本发布时 |
| 检查是否正常 | 每周瞄一眼 |
| 流量监控 | 月底看超没超 |

---

## 参考资源

- [Xray 官方文档](https://xtls.github.io/)
- [REALITY 协议说明](https://github.com/XTLS/REALITY)
- [VPS 选购指南 →](../vps/README.md)
- [买了VPS能做什么 →](vps-use-cases.md)

> 💡 **推荐 VPS：** 自建代理推荐 [BandwagonHost CN2 GIA](https://haiwanlink.com/30)，CN2 GIA 线路对中国大陆最友好。
>
> 💡 **想省心？** 不想折腾自建的话，直接买 [机场服务 →](../README.md#-热门推荐)，¥6 起就能用。
