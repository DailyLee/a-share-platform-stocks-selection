# 部署文档

本文档说明如何将股票平台期扫描工具部署到阿里云ECS服务器（Alibaba Cloud Linux 3.2104 LTS 64位）。

## 前置要求

### 本地环境要求

- macOS/Linux 系统
- SSH 客户端
- rsync 工具（通常已预装）

### 服务器要求

- 阿里云ECS实例
- Alibaba Cloud Linux 3.2104 LTS 64位
- 至少 2GB 内存
- 至少 10GB 磁盘空间
- 已配置SSH密钥认证或密码认证

## 快速开始

### 1. 配置部署信息

复制部署配置模板并填写服务器信息：

```bash
cp .deploy.env.example .deploy.env
```

编辑 `.deploy.env` 文件，填写以下信息：

```bash
SERVER_HOST=your-server-ip-or-domain.com  # 服务器IP或域名
SERVER_USER=root                          # SSH用户名
DEPLOY_PATH=/opt/stock-scanner            # 部署路径
FRONTEND_PORT=80                          # 前端端口
BACKEND_PORT=8001                         # 后端端口

# SSH认证配置（二选一）
# 方式1: 使用密码认证（简单但安全性较低）
SERVER_PASSWORD=your-password-here
SSH_PORT=22

# 方式2: 使用SSH密钥认证（推荐，更安全）
# SSH_KEY_PATH=~/.ssh/id_rsa
# SSH_PORT=22
```

### 2. 选择认证方式

#### 方式1: 密码认证（简单快速）

在 `.deploy.env` 中填写 `SERVER_PASSWORD`：

```bash
SERVER_PASSWORD=your-password-here
```

**注意**: 使用密码认证需要安装 `sshpass` 工具：

- **macOS**: `brew install hudochenkov/sshpass/sshpass`
- **Linux (Ubuntu/Debian)**: `sudo apt-get install sshpass`
- **Linux (CentOS/RHEL/Alibaba Cloud Linux)**: `sudo yum install sshpass`

#### 方式2: SSH密钥认证（推荐，更安全）

为了安全起见，建议使用SSH密钥认证：

```bash
# 生成SSH密钥（如果还没有）
ssh-keygen -t rsa -b 4096

# 将公钥复制到服务器
ssh-copy-id user@your-server-ip
```

然后在 `.deploy.env` 中配置：

```bash
SSH_KEY_PATH=~/.ssh/id_rsa
```

### 3. 执行部署

给部署脚本添加执行权限并运行：

```bash
chmod +x deploy.sh
./deploy.sh
```

部署脚本会自动完成以下操作：

1. ✅ 检查SSH连接
2. ✅ 上传项目文件到服务器
3. ✅ 在服务器上安装依赖（Node.js、Python、npm包、pip包）
4. ✅ 构建前端项目
5. ✅ 配置并启动systemd服务
6. ✅ 配置防火墙规则

## 部署流程说明

### 本地部署脚本 (deploy.sh)

`deploy.sh` 在本地执行，负责：

- 验证配置文件
- 检查SSH连接
- 使用 `rsync` 同步项目文件到服务器
- 上传服务器端部署脚本
- 远程执行服务器端部署脚本

### 服务器端部署脚本 (server_deploy.sh)

`server_deploy.sh` 在服务器上执行，负责：

1. **安装运行时环境**
   - Node.js 18.x LTS
   - Python 3
   - pip

2. **安装项目依赖**
   - 前端：`npm install`
   - 后端：`pip install -r api/requirements.txt`

3. **构建前端**
   - 执行 `npm run build` 生成 `dist` 目录

4. **配置系统服务**
   - 使用 systemd 管理后端服务
   - 设置开机自启
   - 配置自动重启

5. **配置防火墙**
   - 开放后端端口（8001）
   - 开放前端端口（80）

## 服务管理

### 查看服务状态

```bash
ssh user@server-ip "sudo systemctl status stock-scanner.service"
```

### 查看服务日志

```bash
ssh user@server-ip "sudo journalctl -u stock-scanner.service -f"
```

### 重启服务

```bash
ssh user@server-ip "sudo systemctl restart stock-scanner.service"
```

### 停止服务

```bash
ssh user@server-ip "sudo systemctl stop stock-scanner.service"
```

### 启动服务

```bash
ssh user@server-ip "sudo systemctl start stock-scanner.service"
```

## Nginx配置（可选）

如果需要使用Nginx作为反向代理，可以：

1. 在服务器上安装Nginx：

```bash
sudo yum install -y nginx
```

2. 复制nginx配置文件：

```bash
scp nginx.conf.example user@server-ip:/tmp/stock-scanner.conf
ssh user@server-ip "sudo cp /tmp/stock-scanner.conf /etc/nginx/conf.d/stock-scanner.conf"
```

3. 修改配置文件中的域名和路径

4. 测试并重载配置：

```bash
ssh user@server-ip "sudo nginx -t && sudo systemctl reload nginx"
```

## 访问应用

部署完成后，可以通过以下地址访问：

- **前端**: `http://your-server-ip`
- **后端API**: `http://your-server-ip:8001`

如果配置了Nginx：

- **前端**: `http://your-domain.com`
- **后端API**: `http://your-domain.com/api`

## 故障排查

### 1. SSH连接失败

**密码认证方式**:
- 检查服务器IP地址是否正确
- 检查密码是否正确
- 检查是否已安装 `sshpass` 工具
- 检查服务器安全组是否允许SSH连接（端口22）

**密钥认证方式**:
- 检查服务器IP地址是否正确
- 检查SSH密钥路径是否正确
- 检查SSH密钥权限（应为 600）
- 检查服务器安全组是否允许SSH连接（端口22）

### 2. 服务启动失败

查看服务日志：

```bash
ssh user@server-ip "sudo journalctl -u stock-scanner.service -n 50"
```

常见问题：

- Python依赖安装失败：检查网络连接，可能需要配置pip镜像源
- 端口被占用：检查8001端口是否已被其他服务占用
- 权限问题：确保服务用户有足够的权限访问项目目录

### 3. 前端无法访问

- 检查防火墙是否开放80端口
- 检查Nginx配置是否正确（如果使用Nginx）
- 检查前端构建是否成功（查看 `dist` 目录）

### 4. 后端API无法访问

- 检查防火墙是否开放8001端口
- 检查服务是否正在运行
- 检查后端日志中的错误信息

## 更新部署

当代码更新后，只需重新运行部署脚本：

```bash
./deploy.sh
```

部署脚本会自动：

- 同步最新代码
- 重新安装依赖（如果需要）
- 重新构建前端
- 重启服务

## 安全建议

1. **使用SSH密钥认证**：避免使用密码认证
2. **配置防火墙**：只开放必要的端口
3. **使用HTTPS**：生产环境建议配置SSL证书
4. **定期更新**：保持系统和依赖包的最新版本
5. **备份数据**：定期备份重要数据

## 手动部署（如果自动部署失败）

如果自动部署脚本失败，可以手动执行以下步骤：

```bash
# 1. 连接到服务器
ssh user@server-ip

# 2. 进入项目目录
cd /opt/stock-scanner

# 3. 安装Node.js（如果未安装）
curl -fsSL https://rpm.nodesource.com/setup_18.x | sudo bash -
sudo yum install -y nodejs

# 4. 安装Python依赖
cd api
pip3 install -r requirements.txt
cd ..

# 5. 安装前端依赖并构建
npm install
npm run build

# 6. 启动后端服务
cd api
uvicorn index:app --host 0.0.0.0 --port 8001
```

## 联系支持

如果遇到问题，请检查：

1. 服务器系统版本是否为 Alibaba Cloud Linux 3.2104 LTS 64位
2. 服务器资源是否充足（内存、磁盘）
3. 网络连接是否正常
4. 查看详细的错误日志
