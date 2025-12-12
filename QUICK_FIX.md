# 快速修复 404 问题

## 问题
访问 `http://121.43.251.23/platform/api/scan/start` 返回 404

## 后端确认
后端服务正常运行在 `http://121.43.251.23:8001/`，API 路径是 `/api/scan/start`

## 解决步骤

### 1. 检查配置文件是否被 include

```bash
# 检查主配置文件
sudo cat /etc/nginx/nginx.conf | grep -A 10 "server {" | grep -A 5 "include"
```

如果没有看到 `include /etc/nginx/conf.d/stock-scanner.conf;`，需要添加：

```bash
sudo vi /etc/nginx/nginx.conf
```

在 `server {` 块内添加：
```nginx
server {
    listen 80;
    server_name _;
    
    # 添加这一行
    include /etc/nginx/conf.d/stock-scanner.conf;
    
    # 其他配置...
}
```

### 2. 重新生成配置文件

```bash
cd /opt/stock-scanner
bash setup_nginx.sh
```

### 3. 验证配置

```bash
# 查看生成的配置
cat /etc/nginx/conf.d/stock-scanner.conf

# 测试配置语法
sudo nginx -t
```

确保配置中有：
```nginx
location /platform/api {
    rewrite ^/platform/api(.*)$ /api$1 break;
    proxy_pass http://127.0.0.1:8001;
    # ...
}
```

### 4. 重新加载 Nginx

```bash
sudo systemctl reload nginx
# 或
sudo systemctl restart nginx
```

### 5. 测试

```bash
# 测试根路径
curl http://127.0.0.1/platform/api/

# 测试扫描接口
curl -X POST http://127.0.0.1/platform/api/scan/start \
  -H "Content-Type: application/json" \
  -d '{}'
```

### 6. 检查日志

如果还是 404，查看日志：

```bash
# 错误日志
sudo tail -20 /var/log/nginx/error.log

# 访问日志
sudo tail -20 /var/log/nginx/access.log
```

## 常见问题

### 问题1：配置文件未 include
**症状：** 配置测试通过，但请求 404

**解决：** 确保主配置的 server 块中有 `include /etc/nginx/conf.d/stock-scanner.conf;`

### 问题2：location 顺序错误
**症状：** `/platform/api` 被 `/platform` 匹配

**解决：** 确保 `/platform/api` 的 location 在 `/platform` 之前

### 问题3：后端服务未运行
**症状：** 502 错误

**解决：** 
```bash
sudo systemctl start stock-scanner.service
sudo systemctl status stock-scanner.service
```

## 完整配置示例

如果手动配置，确保顺序正确：

```nginx
server {
    listen 80;
    server_name _;
    
    # 1. API 代理（必须在 /platform 之前）
    location /platform/api {
        rewrite ^/platform/api(.*)$ /api$1 break;
        proxy_pass http://127.0.0.1:8001;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    
    # 2. 前端静态文件（在 API 之后）
    location /platform {
        alias /opt/stock-scanner/dist;
        index index.html;
        try_files $uri $uri/ /platform/index.html;
    }
}
```
