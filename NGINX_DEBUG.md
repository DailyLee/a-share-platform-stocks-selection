# Nginx 404 问题排查指南

## 问题：访问 `/platform/api/scan/start` 返回 404

### 排查步骤

#### 1. 检查 Nginx 配置是否正确加载

```bash
# 检查配置文件是否存在
ls -la /etc/nginx/conf.d/stock-scanner.conf

# 查看配置文件内容
cat /etc/nginx/conf.d/stock-scanner.conf

# 测试 Nginx 配置
sudo nginx -t
```

#### 2. 检查主配置文件是否 include

```bash
# 查看主配置文件
sudo cat /etc/nginx/nginx.conf | grep -A 5 -B 5 "include.*stock-scanner"

# 或者查看所有 include
sudo cat /etc/nginx/nginx.conf | grep include
```

确保主配置的 server 块中有：
```nginx
server {
    listen 80;
    # ...
    include /etc/nginx/conf.d/stock-scanner.conf;
}
```

#### 3. 检查后端服务是否运行

```bash
# 检查服务状态
sudo systemctl status stock-scanner.service

# 检查端口是否监听
sudo netstat -tlnp | grep 8001
# 或
sudo ss -tlnp | grep 8001

# 直接测试后端 API
curl http://127.0.0.1:8001/api/scan/start -X POST -H "Content-Type: application/json" -d '{}'
```

#### 4. 检查 Nginx 错误日志

```bash
# 查看错误日志
sudo tail -f /var/log/nginx/error.log

# 查看访问日志
sudo tail -f /var/log/nginx/access.log
```

#### 5. 测试 rewrite 规则

```bash
# 测试 rewrite 是否正确
# 在配置文件中，rewrite 规则应该是：
# rewrite ^/platform/api(.*)$ /api$1 break;

# 测试请求
curl -v http://127.0.0.1/platform/api/scan/start -X POST -H "Content-Type: application/json" -d '{}'
```

#### 6. 检查 location 匹配顺序

确保 `/platform/api` 的 location 在 `/platform` 的 location **之后**，或者使用更精确的匹配：

```nginx
# 方式1：使用精确匹配（推荐）
location ~ ^/platform/api {
    rewrite ^/platform/api(.*)$ /api$1 break;
    proxy_pass http://127.0.0.1:8001;
}

# 方式2：确保 location 顺序正确
# /platform/api 应该在 /platform 之前
location /platform/api {
    # ...
}

location /platform {
    # ...
}
```

### 常见问题

#### 问题1：配置文件未 include

**症状：** Nginx 配置测试通过，但请求返回 404

**解决：** 在主配置的 server 块中添加 `include /etc/nginx/conf.d/stock-scanner.conf;`

#### 问题2：location 匹配顺序错误

**症状：** `/platform/api/scan/start` 被 `/platform` location 匹配

**解决：** 确保 `/platform/api` 的 location 在 `/platform` 之前，或使用正则匹配

#### 问题3：rewrite 规则错误

**症状：** 请求到达后端但路径错误

**解决：** 检查 rewrite 规则，确保正确转换路径

#### 问题4：后端服务未运行

**症状：** Nginx 返回 502 或连接错误

**解决：** 启动后端服务：`sudo systemctl start stock-scanner.service`

### 正确的配置示例

```nginx
server {
    listen 80;
    server_name _;

    # API 代理必须在 /platform 之前，使用更精确的匹配
    location ~ ^/platform/api {
        rewrite ^/platform/api(.*)$ /api$1 break;
        proxy_pass http://127.0.0.1:8001;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 前端静态文件
    location /platform {
        alias /opt/stock-scanner/dist;
        index index.html;
        try_files $uri $uri/ /platform/index.html;
    }
}
```

### 快速修复命令

如果确认是配置问题，可以：

```bash
# 1. 重新生成配置
cd /opt/stock-scanner
bash setup_nginx.sh

# 2. 检查配置
sudo nginx -t

# 3. 重新加载配置
sudo systemctl reload nginx

# 4. 测试
curl http://127.0.0.1/platform/api/
```
