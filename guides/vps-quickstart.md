# VPS 购买与初始化指南

> 从选购 VPS 到跑起第一个网站，全程约 10 分钟。

---

## 第一步：选 VPS

### 你是什么需求？

| 需求 | 推荐 | 入门价 | 链接 |
|:----|:----|:-----:|:----:|
| 🇨🇳 **国内建站**（需备案） | 腾讯云 / 阿里云 | ￥几十/年 | [查看](https://haiwanlink.com/23) |
| 🌐 **免备案建站** | RackNerd / HostDare | $10+/年 | [查看](https://haiwanlink.com/29) |
| 🔧 **自建代理节点** | BandwagonHost CN2 GIA | $50+/年 | [查看](https://haiwanlink.com/30) |
| 🚀 **高端企业** | DMIT | $10+/月 | [查看](https://haiwanlink.com/27) |
| 🧪 **学习实验** | RackNerd | **$10/年** | [查看](https://haiwanlink.com/29) |

> 💡 新手练手推荐 **RackNerd**，年付 $10 起，配置简单，丢了不心疼。

---

## 第二步：购买

以 RackNerd 为例，购买流程：

1. 从 [推广链接](https://haiwanlink.com/29) 进入官网
2. 选择一个套餐（建议 `1核 / 1GB / 20GB SSD / 1TB 流量` 够用）
3. 加入购物车
4. **输入优惠码**（通常在促销页面可找到，比如 `NEWYEAR30` 可省 30%）
5. 填写个人信息，选择 **「支付宝」** 或 **PayPal** 支付
6. 支付完成后，服务器将在几分钟内开通

你会收到一封邮件，包含：
- **IP 地址**
- **SSH 用户名和密码**（通常是 root）
- **端口号**（默认 22）

---

## 第三步：SSH 登录

### Windows 推荐用 PuTTY 或 Windows Terminal

```powershell
ssh root@你的服务器IP
```

首次登录会提示确认指纹，输入 `yes`，然后输入密码（密码不会显示，正常）。

### macOS / Linux 直接在终端

```bash
ssh root@你的服务器IP
```

> ⚠️ 如果连接不上，检查：
> - IP 是否输错
> - 服务器是否已开机
> - 防火墙是否放行了 22 端口（部分厂商默认关闭）

---

## 第四步：初始化配置

登录后建议做以下几件基础配置：

### 4.1 更新系统

```bash
# Debian/Ubuntu
apt update && apt upgrade -y

# CentOS/RHEL
yum update -y
```

### 4.2 修改 SSH 端口（防爆破）

```bash
# 编辑 SSH 配置
vim /etc/ssh/sshd_config

# 找到 #Port 22，改为
Port 2222          # 改成你想要的端口

# 重启 SSH 服务
systemctl restart sshd

# 先别断开当前连接！新开一个终端测试是否能以新端口登录：
ssh -p 2222 root@你的服务器IP
# 确认能连上再断开旧连接
```

### 4.3 创建普通用户（安全）

```bash
# 创建用户
useradd -m -s /bin/bash yourname

# 设置密码
passwd yourname

# 授予 sudo 权限
usermod -aG sudo yourname
```

### 4.4 配置防火墙（UFW）

```bash
# 安装 UFW
apt install ufw -y

# 放行 SSH（你改的端口）
ufw allow 2222/tcp

# 放行 HTTP/HTTPS（如果建站）
ufw allow 80/tcp
ufw allow 443/tcp

# 开启防火墙
ufw enable
```

---

## 第五步：装点什么？

### 建站（LNMP 一键）

```bash
# 安装 Nginx
apt install nginx -y

# 安装 PHP
apt install php-fpm php-mysql php-curl php-gd php-mbstring php-xml -y

# 安装 MySQL/MariaDB
apt install mariadb-server -y
```

### 搭建机场（自建代理）

```bash
# 安装 Xray 一键脚本
bash -c "$(curl -L https://github.com/XTLS/Xray-install/raw/main/install-release.sh)" @ install
```

### 安装 Docker + Docker Compose（通用必备）

> Docker 是部署服务的**最快捷方式**，后面 VPS 上绝大多数玩法（密码管理器、网盘、AI助手）都依赖它。建议必装。

```bash
# 一键安装 Docker
curl -fsSL https://get.docker.com | bash

# 安装 Docker Compose（管理多容器应用）
apt install docker-compose-plugin -y

# 验证安装
docker --version
docker compose version
```

#### Docker 常用命令速查

| 命令 | 作用 | 示例 |
|:----|:-----|:------|
| `docker ps` | 查看运行中的容器 | `docker ps` |
| `docker ps -a` | 查看所有容器（含已停止） | `docker ps -a` |
| `docker images` | 查看已拉取的镜像 | `docker images` |
| `docker pull xxx` | 拉取镜像 | `docker pull nginx` |
| `docker run -d xxx` | 后台运行容器 | `docker run -d -p 80:80 nginx` |
| `docker stop xxx` | 停止容器 | `docker stop my-web` |
| `docker rm xxx` | 删除容器 | `docker rm my-web` |
| `docker logs xxx` | 查看容器日志 | `docker logs -f my-web` |
| `docker exec -it xxx bash` | 进入容器命令行 | `docker exec -it my-web bash` |

> 💡 **装好 Docker 后能做什么？** 看 [「买了VPS能做什么」15+玩法大全](vps-use-cases.md)，密码管理器、云音乐、导航站、AI助手，一行命令就能部署。

#### Docker Compose 示例（多服务一键启动）

创建一个 `docker-compose.yml` 文件，可以把多个服务编排在一起：

```yaml
version: '3'
services:
  nginx:
    image: nginx:latest
    ports:
      - "80:80"
    volumes:
      - ./html:/usr/share/nginx/html

  mysql:
    image: mysql:8
    environment:
      MYSQL_ROOT_PASSWORD: my-secret-pw
    volumes:
      - ./mysql-data:/var/lib/mysql
```

启动：`docker compose up -d`
停止：`docker compose down`

---

## 第六步：域名绑定（可选）

1. 在域名 DNS 解析中添加 A 记录 → 指向你的服务器 IP
2. 用 Nginx 反向代理：

```bash
# 创建站点配置
vim /etc/nginx/sites-available/你的域名

# 内容：
server {
    listen 80;
    server_name 你的域名;
    root /var/www/你的域名;
    index index.html index.php;
}

# 启用
ln -s /etc/nginx/sites-available/你的域名 /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx
```

### 配置 SSL（HTTPS，推荐）

```bash
apt install certbot python3-certbot-nginx -y
certbot --nginx -d 你的域名
```

---

## 常见问题

### ❓ SSH 连不上

- 检查 IP 和端口是否正确
- 去厂商控制台 **「重启」** 服务器
- 厂商后台可能有个 **「VNC」** 按钮，可以直接打开网页终端

### ❓ 服务器被 SSH 爆破怎么办？

- 改 SSH 端口（上面已讲）
- 禁用密码登录，改用密钥登录：

```bash
# 在本地生成密钥
ssh-keygen -t ed25519

# 复制公钥到服务器
ssh-copy-id -p 2222 root@你的服务器IP

# 服务器上禁用密码登录
vim /etc/ssh/sshd_config
# PasswordAuthentication no
systemctl restart sshd
```

### ❓ 速度慢怎么办？

- 确认服务器选择的机房离你近（比如选洛杉矶机房）
- 使用 TCP 加速（BBR）：

```bash
echo "net.core.default_qdisc=fq" >> /etc/sysctl.conf
echo "net.ipv4.tcp_congestion_control=bbr" >> /etc/sysctl.conf
sysctl -p
# 验证：lsmod | grep bbr
```

---

## 参考

- [VPS 服务商对比](../vps/README.md) — 看完选哪家
- [机场推荐](../README.md#-热门推荐) — 如果 VPS 只是用来挂代理，不如直接买机场省心

> 🔗 **[查看所有 VPS 服务商 →](https://haiwanlink.com/23)**
