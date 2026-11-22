# 📋 买了VPS能做什么？15+实用玩法大全

> 别让你的VPS只吃灰。一台低至 ¥10/年的服务器，能干的事远超你想象。

---

## 快速索引

| 类别 | 玩法 | 难度 | 最低配置 |
|:----|:----|:----:|:--------:|
| 🔐 安全 | [密码管理器](#密码管理器) | 🟢 | 512MB |
| 🛡️ 网络 | [自建代理节点](vps-xray-setup.md) | 🟡 | 512MB |
| 🤖 AI | [部署AI助手(Hermes+飞书)](hermes-agent-setup.md) | 🔴 | 1GB |
| ☁️ 存储 | [自建网盘](#自建网盘) | 🟢 | 1GB |
| 🎵 音乐 | [自建云音乐](#自建云音乐) | 🟢 | 512MB |
| 🎬 影视 | [媒体服务器](#家庭影音) | 🟡 | 2GB |
| 📝 笔记 | [知识库系统](#笔记知识库) | 🟢 | 512MB |
| 📑 RSS | [RSS阅读器](#rss阅读器) | 🟢 | 256MB |
| 🧭 导航 | [自建导航站](#导航站) | 🟢 | 256MB |
| 📊 监控 | [Uptime监控](#网站监控) | 🟢 | 256MB |
| 📁 文件 | [文件快传](#文件快传) | 🟢 | 256MB |
| 💻 代码 | [代码托管](#代码托管) | 🟡 | 1GB |
| 🖥️ 在线IDE | [VSCode浏览器版](#在线ide) | 🟡 | 1GB |
| 🔗 短链 | [短链服务](#短链服务) | 🟢 | 256MB |
| ⚙️ 自动化 | [脚本/cron/爬虫](#自动化) | 🟡 | 256MB |
| 🤖 私有AI | [运行大模型](#私有ai) | 🔴 | 4GB+ |

---

## 🔐 密码管理器

**推荐项目：** [Vaultwarden](https://github.com/dani-garcia/vaultwarden)（Bitwarden 轻量自建版）

> 还在所有网站用同一个密码？Vaultwarden 让你自建密码库，全平台（Windows/Mac/iOS/Android/浏览器扩展）同步，数据完全私有。

```bash
# 一行命令部署
docker run -d --name vaultwarden \
  -v /vw-data/:/data/ \
  -p 8080:80 \
  vaultwarden/server:latest
```

| 用途 | 说明 |
|:----|:-----|
| 密码自动填充 | 浏览器插件一键填密码 |
| 二次验证(2FA) | 内置TOTP验证码 |
| 密码泄露检测 | 检查哪些密码已被泄露 |
| 家庭共享 | 和家人共用某些密码 |

> **推荐VPS：** RackNerd ¥10/年款就够跑，512MB内存绰绰有余

---

## ☁️ 自建网盘

**推荐项目：** [Cloudreve](https://cloudreve.org/)（国产，界面漂亮） / [NextCloud](https://nextcloud.com/)（功能最全）

> 百度网盘不限速？不存在的。自建网盘上传下载跑满带宽，隐私你说了算。

```bash
# Cloudreve 一键部署
docker run -d \
  -p 5212:5212 \
  -v /cloudreve/uploads:/cloudreve/uploads \
  -v /cloudreve/config.ini:/cloudreve/config.ini \
  cloudreve/cloudreve:latest
```

**Cloudreve 亮点：**
- 拖拽上传，类百度网盘界面
- 支持直链分享（可设密码/过期时间）
- 支持阿里云OSS/腾讯COS/OneDrive等作为存储后端
- 在线预览图片/视频/文档

> **推荐VPS：** RackNerd 大硬盘套餐或 BandwagonHost 1GB款

---

## 🎵 自建云音乐

**推荐项目：** [Navidrome](https://www.navidrome.org/)

> 把自己的音乐文件上传到 VPS，随时随地听，无广告、无会员、无区域限制。配合 Subsonic 客户端（iOS/Android）体验极佳。

```bash
docker run -d \
  --name navidrome \
  -p 4533:4533 \
  -v /music:/music \
  -v /navidrome/data:/data \
  navidrome/navidrome:latest
```

**支持的客户端：**
- iOS: play:Sub / iSub
- Android: DSub / Subtracks
- Web: 浏览器直接访问

> **推荐VPS：** 任何VPS都能跑，音乐文件存NAS或对象存储更佳

---

## 🎬 家庭影音

**推荐项目：** [Jellyfin](https://jellyfin.org/)（开源免费）

> 搭建自己的 Netflix。存电影/剧集/动漫，全设备串流播放，自动刮削封面和简介。

```bash
docker run -d \
  --name jellyfin \
  -p 8096:8096 \
  -v /jellyfin/config:/config \
  -v /jellyfin/movies:/movies \
  -v /jellyfin/tv:/tv \
  jellyfin/jellyfin:latest
```

> ⚠️ 转码需要CPU或GPU性能，建议 2GB 以上内存VPS。纯串流不转码则 512MB 够用。

---

## 📝 笔记知识库

**推荐项目：** [Trilium Notes](https://github.com/zadam/trilium) / [Outline](https://www.getoutline.com/)

> 自建笔记系统，替代 Notion / 飞书文档。数据在你手里，不怕服务商跑路。

```bash
# Trilium 一键部署
docker run -d -p 8080:8080 \
  -v /trilium-data:/home/node/.local/share/trilium-data \
  zadam/trilium:latest
```

| 项目 | 特点 | 适合 |
|:----|:----|:-----|
| **Trilium** | 树形笔记，支持关系图、加密 | 个人知识管理 |
| **Outline** | 类 Notion 界面，Markdown 编辑 | 团队协作 |
| **Obsidian LiveSync** | Obsidian + 自建同步 | Obsidian 用户 |

---

## 📑 RSS阅读器

**推荐项目：** [Miniflux](https://miniflux.app/)（极简主义） / [Tiny Tiny RSS](https://tt-rss.org/)（功能全面）

> 跟踪你关注的博客、新闻源、论坛更新，不用每个网站挨个刷。信息聚合，一页看完。

```bash
# Miniflux + 数据库 一键部署
docker run -d -p 8080:8080 \
  -e DATABASE_URL=postgres://miniflux:secret@db/miniflux?sslmode=disable \
  miniflux/miniflux:latest
```

---

## 🧭 导航站

**推荐项目：** [Sun-Panel](https://doc.sun-panel.top/) / [Heimdall](https://heimdall.site/)

> 把常用的网站、工具、服务都放在一个页面，设为浏览器首页。比浏览器书签栏好用一百倍。

```bash
# Sun-Panel 一键部署（国产，界面精美）
docker run -d -p 3002:3002 \
  -v /sun-panel:/app/data \
  hslr/sun-panel:latest
```

---

## 📊 网站监控

**推荐项目：** [Uptime Kuma](https://github.com/louislam/uptime-kuma)

> 监控你的网站、服务、API 是否在线，宕机时通过 Telegram/邮件/飞书/微信 告警。

```bash
docker run -d \
  --name uptime-kuma \
  -p 3001:3001 \
  -v /uptime-kuma:/app/data \
  louislam/uptime-kuma:latest
```

**支持监控类型：** HTTP(s) / Ping / TCP 端口 / DNS / 关键字匹配 / 证书到期...
**通知渠道：** 飞书、Telegram、钉钉、邮件、Slack、Webhook 等90+

> **推荐VPS：** RackNerd ¥10/年款足够，256MB内存就能跑

---

## 📁 文件快传

**推荐项目：** [FileCodeBox](https://github.com/vastsa/FileCodeBox)（文件快递柜）

> 像快递柜一样分享文件：上传后生成取件码，对方输入码就能下载。无需注册，用完即走。

```bash
docker run -d \
  --name filecodebox \
  -p 12345:12345 \
  -v /filecodebox:/app/data \
  vastsa/filecodebox:latest
```

**适合场景：** 给朋友传大文件、临时共享、代替微信发文件（不限大小）

---

## 💻 代码托管

**推荐项目：** [Gitea](https://gitea.io/)（轻量Git服务）

> 自建私有 Git 仓库，替代 GitHub 私有库。存放不想公开的代码、配置文件、笔记。

```bash
docker run -d \
  --name gitea \
  -p 3000:3000 \
  -v /gitea:/data \
  gitea/gitea:latest
```

**特性：** 极低资源占用（256MB起跑）、内置Wiki/Issue/CI、兼容GitHub Actions

---

## 🖥️ 在线IDE

**推荐项目：** [code-server](https://github.com/coder/code-server)（浏览器里的 VSCode）

> 在任何设备上用浏览器写代码，iPad/手机都能编程。VSCode 插件全兼容。

```bash
docker run -d \
  --name code-server \
  -p 8080:8080 \
  -v /workspace:/home/coder/project \
  -e PASSWORD=yourpassword \
  codercom/code-server:latest
```

---

## 🔗 短链服务

**推荐项目：** [YOURLS](https://yourls.org/)

> 自己搭短链系统，链接想怎么缩短就怎么缩短，还能统计点击次数。

如果你在用本仓库的推广系统，短链是引流必备工具。👉 [搭建教程参考](../vps/README.md)

---

## ⚙️ 自动化

**VPS是24小时在线的，最适合跑定时任务：**

| 用途 | 实现方式 |
|:----|:---------|
| 定时备份网站/数据库 | `cron` + `rsync` / `rclone` |
| 价格监控/折扣提醒 | Python爬虫 + `cron` + 飞书/Telegram推送 |
| 签到/打卡脚本 | Python + `cron`，自动签到领积分 |
| 舆情监控 | 关键词抓取 + 通知推送 |
| 自动更新SSL证书 | `acme.sh` + `cron` |
| RSS通知 | RSS变更检测 + 推送 |
| 股市/币价提醒 | API定时查询 + 阈值告警 |

```bash
# 示例：每天凌晨2点备份数据库
0 2 * * * mysqldump -u root --all-databases | gzip > /backup/db_$(date +\%Y\%m\%d).sql.gz
```

---

## 🤖 私有AI

**推荐项目：** [Ollama](https://ollama.ai/) + [Open WebUI](https://github.com/open-webui/open-webui)

> 在 VPS 上跑私有 ChatGPT，数据不传出服务器。适合处理敏感文档、代码审查、翻译等。

```bash
# Ollama + Open WebUI 一键部署
docker run -d \
  --name ollama \
  -p 11434:11434 \
  -v /ollama:/root/.ollama \
  ollama/ollama

# 拉取模型（以 qwen2:7b 为例）
docker exec ollama ollama pull qwen2:7b

# 启动 WebUI
docker run -d \
  -p 3000:8080 \
  -e OLLAMA_BASE_URL=http://你的VPS_IP:11434 \
  -v /open-webui:/app/backend/data \
  ghcr.io/open-webui/open-webui:main
```

> ⚠️ 需要 4GB+ 内存VPS。轻量模型（qwen2:0.5b）2GB也能跑。推荐 **DMIT** 或 **BandwagonHost**。

---

## 🎯 按VPS配置选用途

| VPS配置 | 能跑什么 | 推荐VPS |
|:-------|:--------|:--------|
| **256MB~512MB** | RSS阅读器、导航站、监控、短链、脚本 | **RackNerd** ¥10/年 |
| **1GB** | 密码管理器、音乐服务器、Gitea、网盘、Hermes | **RackNerd / HostDare** |
| **2GB** | Jellyfin转码、自建代理+网站、CI/CD | **BandwagonHost** |
| **4GB+** | Ollama私有AI、多人服务、视频处理 | **DMIT** 高端线路 |

---

> 💡 **还没VPS？** 看看 [VPS选购指南](../vps/README.md) 和 [VPS购买与初始化教程](vps-quickstart.md)
>
> 🚀 **快速入口：** [RackNerd ¥10/年](https://haiwanlink.com/29) · [BandwagonHost CN2 GIA](https://haiwanlink.com/30) · [HostDare CN2 GT](https://haiwanlink.com/28) · [DMIT 高端线路](https://haiwanlink.com/27)
