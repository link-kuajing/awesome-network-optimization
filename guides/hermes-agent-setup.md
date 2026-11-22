# 🤖 Hermes Agent 部署 + 飞书集成教程

> 在 VPS 上部署开源 AI 助手 Hermes Agent，对接飞书（Lark）实现随时随地用聊天操控服务器、查资料、写代码、执行自动化任务。

---

## 📋 目录

- [什么是 Hermes Agent](#什么是-hermes-agent)
- [前置条件](#前置条件)
- [第一步：飞书应用配置（核心步骤）](#第一步飞书应用配置核心步骤)
  - [1.1 创建飞书应用](#11-创建飞书应用)
  - [1.2 权限配置详解（逐项说明）](#12-权限配置详解逐项说明)
  - [1.3 开启机器人能力](#13-开启机器人能力)
  - [1.4 事件订阅配置](#14-事件订阅配置)
  - [1.5 发布应用](#15-发布应用)
  - [1.6 获取凭证](#16-获取凭证)
- [第二步：安装 Hermes Agent](#第二步安装-hermes-agent)
- [第三步：配置飞书集成](#第三步配置飞书集成)
- [第四步：启动与验证](#第四步启动与验证)
- [第五步：systemd 服务化（开机自启）](#第五步systemd-服务化开机自启)
- [常见问题](#常见问题)

---

## 什么是 Hermes Agent

Hermes Agent 是由 Nous Research 开发的开源 AI 助手框架。它可以：

- 🤖 **接入 AI 模型**（DeepSeek/Claude/GPT 等），充当你的智能助手
- 📱 **对接聊天平台**（飞书/Telegram/Slack/Signal 等），在聊天框里操控一切
- 🛠️ **执行真实操作**：读文件、写代码、搜网页、执行命令、管理服务器
- ⏰ **定时任务**：每天自动执行运维/备份/监控任务
- 🧩 **可扩展**：通过 Skills（技能）和 MCP 工具链扩展能力

**典型用法：** 在 VPS 上部署 Hermes Agent，对接飞书 Bot，你在飞书上发消息就能操控服务器——查日志、跑脚本、部署项目，全在聊天框里完成。

---

## 前置条件

| 条件 | 说明 |
|:----|:-----|
| 🖥️ **VPS 一台** | 建议 1GB 以上内存，推荐 [BandwagonHost CN2 GIA](https://haiwanlink.com/30) 或 [RackNerd ¥10/年](https://haiwanlink.com/29) |
| 🌐 **域名（可选）** | 如果想让飞书事件订阅走公网 HTTPS 回调，需要一个域名。也可以用内网穿透替代 |
| 🔑 **AI 模型 API Key** | DeepSeek / OpenAI / Anthropic 等任选一个 |
| 📱 **飞书企业账号** | 免费版即可，不需要付费版 |

---

## 第一步：飞书应用配置（核心步骤）

Hermes Agent 通过**飞书开放平台**的 Bot 能力与飞书通信。你需要创建一个飞书应用并配置好权限。

### 1.1 创建飞书应用

1. 打开 [飞书开放平台](https://open.feishu.cn/)（需登录飞书账号）
2. 点击右上角 **「开发者后台」**
3. 点击 **「创建应用」** → **「企业自建应用」**
4. 填写应用信息：
   - **应用名称：** 例如 "服务器助手" 或 "Hermes"
   - **应用描述：** 随便写，比如 "AI 服务器管理助手"
   - **应用图标：** 可以不上传，用默认的

### 1.2 权限配置详解（逐项说明）

这是最重要的一步。点击 **「权限管理」**，按下面的说明逐项添加权限。

#### ⚠️ 权限分类说明

飞书权限分三类，理解这个才能正确配置：

| 类别 | 说明 | 审批 |
|:----|:-----|:----:|
| **基础权限** | 应用最基础的能力 | ✅ 无需审批 |
| **敏感权限** | 涉及用户数据 | ⏳ 需要管理员审批 |
| **超敏感权限** | 涉及通讯录、消息内容 | ⏳ 需要管理员+运营审批 |

#### 必需权限（不配就无法正常运行）

| 权限 Token | 权限名称 | 作用 | 为什么必需 |
|:----------|:---------|:-----|:----------|
| `im:message` | **消息与群组** | 消息读写 | ❗**核心权限**。没有这个，机器人无法收发消息 |
| ├─ `im:message:send_as_bot` | 机器人发送消息 | 机器人回复用户消息 | 用户发消息给你，机器人需要能回复 |
| ├─ `im:message.p2p` | 获取单聊消息 | 接收私聊发来的消息 | 用户在私聊里和机器人对话 |
| └─ `im:message.group` | 获取群聊消息 | 在群聊中@机器人 | 想把机器人拉进群里用 |
| `im:resource` | **获取与发送资源** | 图片/文件/语音上传下载 | ❗发图片、发文件、发语音都需要 |
| ├─ `im:resource:send_as_bot` | 机器人发送资源 | 机器人发送图片文件 | Hermes 可以发截图、发文件 |

#### 强烈推荐权限（配了体验更好）

| 权限 Token | 权限名称 | 作用 | 为什么推荐 |
|:----------|:---------|:-----|:----------|
| `contact:user.base:readonly` | 读取用户基本信息 | 获取用户名、头像 | 让机器人知道你叫什么，回复时可以带称呼 |
| `contact:contact.base:readonly` | 读取通讯录基本信息 | 获取组织架构 | 群聊中知道是谁在@机器人 |

#### 可选权限（按需开启）

| 权限 Token | 权限名称 | 作用 | 什么场景需要 |
|:----------|:---------|:-----|:------------|
| `drive:drive:readonly` | 读取云文档 | 读取飞书文档内容 | 想让 Hermes 读取飞书文档做知识库问答 |
| `drive:drive` | 云文档读写 | 创建/编辑飞书文档 | 想让 Hermes 自动写文档、生成周报 |
| `calendar:calendar:readonly` | 读取日历 | 读取日程 | 想让 Hermes 管理日程 |
| `contact:user.email:readonly` | 读取用户邮箱 | 获取邮箱地址 | 需要按邮箱识别用户 |
| `contact:user.phone:readonly` | 读取用户手机号 | 获取手机号 | ⚠️ 超敏感，一般不需要 |

#### 权限申请操作步骤

1. 在 **「权限管理」** 页面，点击 **「添加权限」**
2. 搜索框搜索上面的权限名称（如 `im:message`）
3. 勾选后点击 **「确认添加」**
4. 按这个方式添加所有需要的权限
5. 添加完成后，点击 **「全部开通」**（或在每个权限右侧点 **「开通」**）
6. 部分权限需要 **管理员审批**，联系飞书管理员确认即可

> 💡 如果这是你自己的飞书账号，你既是开发者又是管理员，审批秒过。

#### 权限对照速查表

```
权限名                         必需?   说明
─────────────────────────────────────────────
im:message                     ✅必需  机器人收发消息的根本
  im:message:send_as_bot       ✅必需  机器人能回复
  im:message.p2p               ✅必需  私聊用
  im:message.group             ✅推荐  群聊@机器人用
im:resource                    ✅必需  传图片/文件
  im:resource:send_as_bot      ✅必需  机器人传文件
contact:user.base:readonly     ⭐推荐  知道用户叫什么
contact:contact.base:readonly  ⭐推荐  知道组织架构
drive:drive:readonly           🔘可选  读云文档做知识库
drive:drive                    🔘可选  写文档生成报告
calendar:calendar:readonly     🔘可选  管理日程
```

### 1.3 开启机器人能力

1. 在左侧菜单点击 **「应用功能」→「机器人」**
2. 开启 **「启用机器人」** 开关
3. 在 **「消息卡片」** 配置中，保持默认即可
4. 如果需要机器人可以发送富文本卡片，可以研究消息卡片模板，但基础版不需要

### 1.4 事件订阅配置

事件订阅让飞书在**有新消息时主动通知你的服务器**。

1. 点击 **「事件与回调」→「事件配置」**
2. 在 **「回调配置」** 中：
   - **回调地址 URL：** 填写你的服务器地址 + 回调路径
   - 格式：`https://你的域名/hermes/callback`
   - 如果没有域名，可以先填一个占位符，后面用内网穿透调试
3. 添加事件：
   - 点击 **「添加事件」**
   - 搜索 `im.message.receive_v1` → 勾选 → 确认
   - 这个事件是**「接收消息」**，当用户发消息给机器人时触发

> ⚠️ **关于回调地址 HTTPS 要求：**
> 飞书要求回调地址必须是 HTTPS（不能是 HTTP）。有两种方式解决：
> - **方案A：** 用域名 + Nginx 反代 + Let's Encrypt 证书（推荐）
> - **方案B：** 用 Cloudflare Tunnel / frp 等内网穿透工具
> - **方案C：** 开发调试阶段临时用 `https://webhook.site` 测试连通性

4. **订阅方式选择「加密」**（推荐）：
   - 勾选 **「加密」** 后，会生成一个 **Encrypt Key（加密密钥）** 和 **Verification Token（验证令牌）**
   - 这两串字符后面配置 Hermes 时需要填进去
   - **Encrypt Key** 用于消息体加密
   - **Verification Token** 用于飞书验证你的服务器身份

### 1.5 安全设置（验证令牌和加密密钥）

在 **「事件与回调」** 页面：

| 字段 | 说明 | 配置方式 |
|:----|:-----|:---------|
| **Verification Token** | 验证令牌 | 系统自动生成，复制保存 |
| **Encrypt Key** | 加密密钥 | 系统自动生成，复制保存 |
| **回调地址** | 事件推送地址 | 格式：`https://你的域名/hermes/callback` |

> 📝 **这些信息在后面配置 Hermes 时必须用到，先复制到记事本保存好。**

### 1.6 发布应用

1. 点击左侧 **「版本管理与发布」**
2. 点击 **「创建版本」**
3. 填写版本号（如 `1.0.0`）和更新说明
4. 点击 **「保存」**
5. 点击 **「申请发布」**
6. 如果这是你自己的企业自建应用，审批通常很快

> ⚠️ **注意：** 应用必须发布（上线）后才能使用。没发布之前，机器人只是「开发中」状态。

### 1.7 获取 App ID 和 App Secret

1. 在 **「凭证与基础信息」** 页面
2. 可以看到 **App ID**（应用ID）和 **App Secret**（应用密钥）
3. **App Secret** 只显示一次，如果之前没保存可以重新生成
4. 复制保存这两个值

> ⚠️ **App Secret 相当于密码，不要暴露给任何人，不要提交到 GitHub！**

#### 至此，飞书端配置完成。你手上应该有这些信息：

```
App ID:          cli_xxxxxxxxxxxxxxx
App Secret:      xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
Verification Token: xxxxxxxxxxxxxxxxxxxxxxxxxx
Encrypt Key:        xxxxxxxxxxxxxxxxxxxxxxxxxx
回调地址:          https://你的域名/hermes/callback
```

---

## 第二步：安装 Hermes Agent

```bash
# 1. 安装 Python 3.10+
apt update && apt install python3 python3-pip python3-venv git curl -y

# 2. 克隆项目
git clone https://github.com/nousresearch/hermes-agent.git
cd hermes-agent

# 3. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 4. 安装依赖
pip install -r requirements.txt
```

---

## 第三步：配置飞书集成

创建配置文件 `config.yaml`：

```yaml
# config.yaml

# ========== AI 模型配置 ==========
provider: deepseek
model: deepseek-chat

# ========== 飞书集成配置 ==========
feishu:
  app_id: "你的AppID"           # 从飞书开放平台获取
  app_secret: "你的AppSecret"   # 从飞书开放平台获取
  verification_token: "你的VerificationToken"
  encrypt_key: "你的EncryptKey"
  
  # Webhook 监听地址
  webhook_host: "0.0.0.0"      # 监听所有网卡
  webhook_port: 8088            # 监听端口
  
  # 回调路径（对应飞书事件订阅配置的回调地址路径部分）
  callback_path: "/hermes/callback"

# ========== 工具配置 ==========
tools:
  # 允许 Hermes 执行终端命令
  terminal:
    enabled: true
    whitelist_paths:
      - "/root"
  
  # 允许读写文件
  file:
    enabled: true
  
  # 允许网络搜索
  web_search:
    enabled: true
  
  # 允许网络内容提取
  web_extract:
    enabled: true
```

> ⚠️ **注意：** 把 `config.yaml` 放在项目根目录，或者通过环境变量 `HERMES_CONFIG_PATH` 指定路径。
> 
> ⚠️ **不要把这个文件提交到 GitHub！** 建议添加到 `.gitignore`。

---

## 第四步：启动与验证

### 启动 Hermes

```bash
cd /root/hermes-agent
source venv/bin/activate
python run.py
```

启动后你会看到类似输出：

```
[INFO] Hermes Agent started
[INFO] Feishu webhook listening on 0.0.0.0:8088
[INFO] Callback path: /hermes/callback
```

### Nginx 反代（推荐，可选但建议）

为了让飞书能通过 HTTPS 回调到你的服务器，配置 Nginx 反向代理：

```nginx
server {
    listen 443 ssl;
    server_name 你的域名;

    ssl_certificate /etc/letsencrypt/live/你的域名/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/你的域名/privkey.pem;

    location /hermes/ {
        proxy_pass http://127.0.0.1:8088;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

申请 SSL 证书：

```bash
apt install certbot python3-certbot-nginx -y
certbot --nginx -d 你的域名
```

### 验证飞书回调连通性

1. 在飞书开放平台的事件配置页面，点击 **「测试回调地址」**
2. 如果显示 **「回调地址验证通过」**，说明配置成功
3. 如果不通过，检查：
   - 防火墙是否放行了 443 端口
   - Nginx 配置是否正确
   - Hermes 是否在运行

### 测试机器人

1. 打开飞书，搜索你创建的应用名称（如 "服务器助手"）
2. 找到机器人，发一条消息试试，比如 `你好`
3. 如果机器人回复了，说明集成成功！
4. 试试更多功能：`帮我查一下服务器状态`、`当前时间是多少`

---

## 第五步：systemd 服务化（开机自启）

创建 systemd 服务文件，让 Hermes Agent 开机自动启动、崩溃自动重启：

```bash
cat > /etc/systemd/system/hermes-agent.service << 'EOF'
[Unit]
Description=Hermes Agent - AI Assistant
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/hermes-agent
Environment=PATH=/root/hermes-agent/venv/bin:/usr/bin:/usr/local/bin
ExecStart=/root/hermes-agent/venv/bin/python /root/hermes-agent/run.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
```

启用并启动：

```bash
systemctl daemon-reload
systemctl enable hermes-agent
systemctl start hermes-agent

# 查看状态
systemctl status hermes-agent

# 查看日志
journalctl -u hermes-agent -f
```

---

## 常见问题

### ❓ 飞书回调地址验证失败

| 可能原因 | 解决方法 |
|:--------|:---------|
| 回调地址不是 HTTPS | 配置 Nginx 反代 + SSL 证书 |
| 防火墙拦截 | 放行 443 和 8088 端口 |
| Hermes 没启动 | 检查进程是否在运行 |
| Verification Token 填错 | 去飞书开放平台重新复制 |
| 域名解析不对 | 确认域名指向服务器 IP |

### ❓ 机器人不回复消息

| 可能原因 | 解决方法 |
|:--------|:---------|
| 事件订阅没添加 `im.message.receive_v1` | 去事件配置检查 |
| 应用没发布 | 去版本管理发布应用 |
| AI API Key 无效 | 检查 provider 密钥是否正确 |
| 控制台打印错误 | 查看 `journalctl -u hermes-agent -f` |

### ❓ 没有域名怎么办？

| 替代方案 | 说明 |
|:--------|:-----|
| **Cloudflare Tunnel** | 免费内网穿透，自动 HTTPS |
| **frp** | 自建内网穿透 |
| **ngrok** | 临时调试用，免费版有限制 |
| **Tailscale** | 组网后用 Tailscale IP |

### ❓ 飞书权限审批不通过

如果管理员审核时说"不需要这么高权限"，你可以这样解释每个权限的用途：

| 权限 | 解释话术 |
|:----|:---------|
| `im:message` | "机器人需要收消息才能回复，这是最基础的能力" |
| `im:resource` | "机器人要能发截图和文件回来" |
| `contact:user.base` | "机器人得知道谁在跟它说话，才能个性化回复" |

---

## 参考资源

- [Hermes Agent 官方文档](https://hermes-agent.nousresearch.com/docs)
- [飞书开放平台文档](https://open.feishu.cn/document)
- [Hermes Agent GitHub](https://github.com/nousresearch/hermes-agent)
- [还没 VPS？选购指南 →](../vps/README.md)

> **💡 需要更便宜的 VPS 来练手？** [RackNerd ¥10/年](https://haiwanlink.com/29) 租一台，随便折腾不心疼。
>
> **💡 需要稳定的 VPS 跑生产服务？** [BandwagonHost CN2 GIA](https://haiwanlink.com/30) 线路稳，延迟低。
