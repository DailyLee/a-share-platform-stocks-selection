# Nginx 配置指南

本指南将帮助你在服务器上配置 Nginx，使前端可以通过 `http://your-ip/platform` 访问。

## 前提条件

1. 已完成项目部署（运行过 `./deploy.sh`）
2. 服务器上已安装 Nginx
3. 前端已构建（`dist` 目录存在）
4. 后端服务已启动（运行在 8001 端口）

## 重要说明：与其他项目共存

如果你的服务器上已经有其他项目使用80端口，本配置会：
- ✅ **安全地添加** `/platform` 和 `/api` location
- ✅ **不会影响** 其他项目的配置
- ✅ 使用独立的配置文件，便于管理

nginx的location匹配规则确保：
- `/platform` 和 `/api` 路径由本配置处理
- 其他路径由现有配置处理

**如果现有配置中已有 `/api` 或 `/platform` location，可能会有冲突，请先检查。**

## 配置步骤

### 1. 登录服务器

```bash
ssh root@121.43.251.23
# 或使用你的认证方式
```

### 2. 检查部署路径

确认项目部署路径（默认是 `/opt/stock-scanner`）：

```bash
ls -la /opt/stock-scanner/dist
```

如果路径不同，请记住你的实际路径，后续配置需要修改。

### 3. 创建 Nginx 配置文件

**方法一：使用自动化脚本（最简单，推荐）**

如果你已经部署了项目，可以直接使用自动化脚本：

```bash
# 在项目部署目录下运行
cd /opt/stock-scanner
bash setup_nginx.sh
```

脚本会自动：
- 检查现有配置（不会影响其他项目）
- 检查并安装 Nginx（如果需要）
- 创建独立的配置文件
- 测试配置
- 启动 Nginx
- 检查后端服务状态

**脚本会检测是否已有80端口配置，并安全地添加location块，不会影响现有配置。**

**方法二：使用 tee 命令直接创建（推荐，手动方式）**

```bash
sudo tee /etc/nginx/conf.d/stock-scanner.conf > /dev/null <<'EOF'
server {
    listen 80;
    server_name _;

    # 前端静态文件 - /platform 路径
    location /platform {
        alias /opt/stock-scanner/dist;  # 如果部署路径不同，请修改这里
        index index.html;
        try_files $uri $uri/ /platform/index.html;
        
        # 缓存静态资源
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # 后端API代理
    location /api {
        proxy_pass http://127.0.0.1:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # 超时设置（支持长时间运行的扫描任务）
        proxy_connect_timeout 600s;
        proxy_send_timeout 600s;
        proxy_read_timeout 600s;
    }

    # WebSocket支持（如果需要）
    location /ws {
        proxy_pass http://127.0.0.1:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        
        # WebSocket超时设置
        proxy_connect_timeout 7d;
        proxy_send_timeout 7d;
        proxy_read_timeout 7d;
    }

    # 日志
    access_log /var/log/nginx/stock-scanner-access.log;
    error_log /var/log/nginx/stock-scanner-error.log;
}
EOF
```

**方法二：使用 vi/vim 编辑器**

```bash
sudo vi /etc/nginx/conf.d/stock-scanner.conf
# 或
sudo vim /etc/nginx/conf.d/stock-scanner.conf
```

vi/vim 使用说明：
- 按 `i` 进入插入模式
- 粘贴配置内容
- 按 `Esc` 退出插入模式
- 输入 `:wq` 保存并退出

**方法三：安装 nano 后使用**

```bash
# 安装 nano
sudo yum install -y nano  # CentOS/RHEL/Alibaba Cloud Linux
# 或
sudo apt-get install -y nano  # Ubuntu/Debian

# 然后使用 nano
sudo nano /etc/nginx/conf.d/stock-scanner.conf
```

**注意：** 如果部署路径不是 `/opt/stock-scanner`，请在使用方法一后编辑文件修改路径，或直接在使用方法一时修改配置中的路径。


**重要提示：**
- 如果部署路径不是 `/opt/stock-scanner`，请修改 `alias` 那一行的路径
- 如果后端端口不是 8001，请修改 `proxy_pass` 中的端口号

### 4. 测试 Nginx 配置

```bash
sudo nginx -t
```

如果看到 `syntax is ok` 和 `test is successful`，说明配置正确。

### 5. 重启 Nginx

```bash
sudo systemctl restart nginx
```

### 6. 检查 Nginx 状态

```bash
sudo systemctl status nginx
```

### 7. 检查后端服务状态

确保后端服务正在运行：

```bash
sudo systemctl status stock-scanner.service
```

如果服务未运行，启动它：

```bash
sudo systemctl start stock-scanner.service
sudo systemctl enable stock-scanner.service
```

### 8. 检查防火墙

确保防火墙允许 80 端口访问：

```bash
# 如果使用 firewalld
sudo firewall-cmd --permanent --add-port=80/tcp
sudo firewall-cmd --reload

# 如果使用 iptables
sudo iptables -I INPUT -p tcp --dport 80 -j ACCEPT
```

### 9. 检查阿里云安全组

在阿里云控制台，确保安全组规则允许：
- 入方向：TCP 80 端口（HTTP）
- 入方向：TCP 8001 端口（后端API，如果直接访问）

### 10. 测试访问

在浏览器中访问：
- 前端：`http://121.43.251.23/platform`
- 后端健康检查：`http://121.43.251.23/api/`（应该返回 JSON 响应）

## 与其他项目共存

### 检查是否有冲突

在配置前，检查现有配置是否有冲突：

```bash
# 检查是否已有 /api 或 /platform location
grep -r 'location.*\(/api\|/platform\)' /etc/nginx/conf.d/ /etc/nginx/nginx.conf 2>/dev/null || echo '未发现冲突'
```

### 如果现有配置已有 server 块在 80 端口

nginx支持多个server块监听同一个端口，会根据以下规则匹配：
1. 精确匹配 `server_name`
2. 通配符匹配 `*.example.com`
3. 默认server（`server_name _` 或第一个匹配的）

我们的配置使用默认server，location匹配是独立的，所以：
- ✅ `/platform` 和 `/api` 会由我们的配置处理
- ✅ 其他路径会由现有配置处理
- ✅ 不会产生冲突（除非现有配置也有相同的location）

### 手动添加到现有配置（高级）

如果你想将location添加到现有的server块中，可以：

1. 找到现有的server块配置文件
2. 在server块内添加location块：

```nginx
location /platform {
    alias /opt/stock-scanner/dist;
    index index.html;
    try_files $uri $uri/ /platform/index.html;
}

location /api {
    proxy_pass http://127.0.0.1:8001;
    # ... 其他配置
}
```

## 故障排查

### 问题1：访问 `/platform` 返回 404

**检查项：**
1. 确认 `dist` 目录存在且包含文件：
   ```bash
   ls -la /opt/stock-scanner/dist
   ```
2. 确认 Nginx 配置中的路径正确
3. 检查 Nginx 错误日志：
   ```bash
   sudo tail -f /var/log/nginx/stock-scanner-error.log
   ```

### 问题2：前端页面显示但 API 请求失败

**检查项：**
1. 确认后端服务正在运行：
   ```bash
   sudo systemctl status stock-scanner.service
   ```
2. 测试后端 API 是否可访问：
   ```bash
   curl http://127.0.0.1:8001/
   ```
3. 检查 Nginx 错误日志和访问日志：
   ```bash
   sudo tail -f /var/log/nginx/stock-scanner-error.log
   sudo tail -f /var/log/nginx/stock-scanner-access.log
   ```

### 问题3：静态资源（JS/CSS）加载失败

**检查项：**
1. 确认前端构建时使用了正确的 base path（`/platform/`）
2. 检查浏览器控制台的错误信息
3. 确认静态资源文件存在：
   ```bash
   ls -la /opt/stock-scanner/dist/assets/
   ```

### 问题4：长时间运行的扫描任务超时

如果遇到超时问题，可以增加超时时间。编辑配置文件：

```bash
sudo nano /etc/nginx/conf.d/stock-scanner.conf
```

修改超时设置（例如增加到 30 分钟）：

```nginx
proxy_connect_timeout 1800s;
proxy_send_timeout 1800s;
proxy_read_timeout 1800s;
```

然后重新加载配置：

```bash
sudo nginx -t && sudo systemctl reload nginx
```

## 重新构建前端

如果修改了 `vite.config.js` 中的 base path，需要重新构建前端：

```bash
# 在本地或服务器上
npm run build
```

然后重新部署或上传 `dist` 目录到服务器。

## 其他配置选项

### 使用域名

如果你想使用域名而不是 IP，修改配置中的 `server_name`：

```nginx
server_name your-domain.com;
```

### 启用 HTTPS

如果需要 HTTPS，可以添加 SSL 配置（参考 `nginx.conf.example` 中的注释部分）。

### 修改日志位置

可以修改日志文件路径：

```nginx
access_log /var/log/nginx/stock-scanner-access.log;
error_log /var/log/nginx/stock-scanner-error.log;
```

## 参考文件

- `nginx.conf.example` - 配置文件模板
- `vite.config.js` - 前端构建配置（包含 base path）
- `.deploy.env` - 部署配置（包含部署路径信息）
