# Nginx 独立配置文件说明

## 什么是"独立的配置文件"？

"独立的配置文件"指的是：**创建一个新的、单独的文件来存放你的项目配置，而不是修改现有的配置文件**。

## Nginx 配置文件组织方式

### 1. 配置文件结构

Nginx 的配置文件通常组织如下：

```
/etc/nginx/
├── nginx.conf              # 主配置文件
└── conf.d/                 # 配置目录（自动加载）
    ├── default.conf        # 其他项目的配置（已存在）
    ├── other-project.conf  # 其他项目的配置（已存在）
    └── stock-scanner.conf  # 我们的配置（新创建）
```

### 2. 主配置文件如何加载

在 `nginx.conf` 中，通常有这样的配置：

```nginx
http {
    # ... 其他配置 ...
    
    # 自动加载 conf.d 目录下的所有 .conf 文件
    include /etc/nginx/conf.d/*.conf;
}
```

这意味着：
- ✅ Nginx 会自动加载 `conf.d/` 目录下的所有 `.conf` 文件
- ✅ 每个 `.conf` 文件都是独立的
- ✅ 可以创建新文件，不需要修改现有文件

## 为什么使用独立配置文件？

### 场景示例

假设你的服务器上已经有一个项目在使用 80 端口：

**现有配置** (`/etc/nginx/conf.d/default.conf`):
```nginx
server {
    listen 80;
    server_name _;
    
    location / {
        root /var/www/html;
        index index.html;
    }
    
    location /other-api {
        proxy_pass http://127.0.0.1:3000;
    }
}
```

### 方式一：修改现有配置（不推荐）

如果你直接修改 `default.conf`，添加我们的配置：

```nginx
server {
    listen 80;
    server_name _;
    
    location / {
        root /var/www/html;
        index index.html;
    }
    
    location /other-api {
        proxy_pass http://127.0.0.1:3000;
    }
    
    # 添加我们的配置
    location /platform {
        alias /opt/stock-scanner/dist;
        # ...
    }
    
    location /api {
        proxy_pass http://127.0.0.1:8001;
        # ...
    }
}
```

**问题：**
- ❌ 修改了其他项目的配置文件
- ❌ 如果配置出错，可能影响其他项目
- ❌ 不便于管理和维护
- ❌ 更新其他项目时可能被覆盖

### 方式二：创建独立配置文件（推荐）

创建新文件 `/etc/nginx/conf.d/stock-scanner.conf`:

```nginx
server {
    listen 80;
    server_name _;
    
    location /platform {
        alias /opt/stock-scanner/dist;
        # ...
    }
    
    location /api {
        proxy_pass http://127.0.0.1:8001;
        # ...
    }
}
```

**优点：**
- ✅ 不修改现有配置文件
- ✅ 配置出错只影响本项目
- ✅ 便于管理和维护
- ✅ 可以随时删除，不影响其他项目
- ✅ 多个项目配置互不干扰

## Nginx 如何处理多个配置文件？

### 1. 多个 server 块监听同一端口

Nginx 支持多个 `server` 块监听同一个端口（如 80），会根据以下规则匹配：

1. **精确匹配** `server_name`
   ```nginx
   server {
       listen 80;
       server_name example.com;  # 精确匹配
   }
   ```

2. **通配符匹配** `*.example.com`
   ```nginx
   server {
       listen 80;
       server_name *.example.com;  # 通配符匹配
   }
   ```

3. **默认 server** (`server_name _` 或第一个匹配的)
   ```nginx
   server {
       listen 80;
       server_name _;  # 默认，匹配所有请求
   }
   ```

### 2. Location 匹配规则

在同一个 `server` 块内，location 按照以下优先级匹配：

1. **精确匹配** `location = /path`
2. **前缀匹配（禁止正则）** `location ^~ /path`
3. **正则匹配** `location ~ /path`
4. **普通前缀匹配** `location /path`

**重要：** 如果多个 `server` 块都监听 80 端口，nginx 会：
1. 先根据 `server_name` 选择 server 块
2. 然后在选中的 server 块内匹配 location

## 实际工作流程

### 请求处理流程

当用户访问 `http://your-ip/platform` 时：

1. **Nginx 接收请求**（端口 80）
2. **选择 server 块**
   - 如果有多个 server 块监听 80 端口
   - 根据 `server_name` 匹配（如果都是 `_`，使用第一个）
3. **匹配 location**
   - 在选中的 server 块内查找匹配的 location
   - `/platform` 匹配到我们的配置
4. **处理请求**
   - 返回静态文件或代理到后端

### 示例：多个配置文件共存

**配置文件 1** (`/etc/nginx/conf.d/default.conf`):
```nginx
server {
    listen 80;
    server_name _;
    
    location / {
        root /var/www/html;  # 处理根路径
    }
    
    location /other-api {
        proxy_pass http://127.0.0.1:3000;  # 处理 /other-api
    }
}
```

**配置文件 2** (`/etc/nginx/conf.d/stock-scanner.conf`):
```nginx
server {
    listen 80;
    server_name _;
    
    location /platform {
        alias /opt/stock-scanner/dist;  # 处理 /platform
    }
    
    location /api {
        proxy_pass http://127.0.0.1:8001;  # 处理 /api
    }
}
```

**请求处理结果：**
- `http://your-ip/` → 由 `default.conf` 处理
- `http://your-ip/other-api` → 由 `default.conf` 处理
- `http://your-ip/platform` → 由 `stock-scanner.conf` 处理
- `http://your-ip/api` → 由 `stock-scanner.conf` 处理

## 注意事项

### 1. Location 冲突

如果两个配置文件中有相同的 location，可能会有冲突：

**配置 1**:
```nginx
location /api {
    proxy_pass http://127.0.0.1:3000;
}
```

**配置 2**:
```nginx
location /api {
    proxy_pass http://127.0.0.1:8001;
}
```

**结果：** Nginx 会使用第一个匹配的 server 块中的 location，可能导致冲突。

**解决方案：**
- 使用不同的路径（如 `/stock-api`）
- 使用不同的 `server_name`
- 合并到同一个配置文件中

### 2. 默认 Server 的选择

如果多个 server 块都使用 `server_name _`，Nginx 会使用：
- 第一个加载的配置文件中的 server 块（按文件名排序）

### 3. 配置文件加载顺序

Nginx 按照文件名的字母顺序加载配置文件：
- `a.conf` 会在 `b.conf` 之前加载
- `default.conf` 会在 `stock-scanner.conf` 之前加载

## 总结

**独立配置文件 = 创建新文件，不修改现有文件**

**优点：**
- ✅ 安全：不影响其他项目
- ✅ 灵活：可以随时添加或删除
- ✅ 清晰：每个项目的配置独立管理
- ✅ 维护：便于版本控制和备份

**工作原理：**
- Nginx 自动加载 `conf.d/` 目录下的所有 `.conf` 文件
- 每个配置文件中的 `server` 块可以独立工作
- Location 匹配规则确保请求被正确路由

这就是为什么我们的脚本创建"独立的配置文件"是安全的，不会影响其他项目！
