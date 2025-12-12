#!/bin/bash
# 快速配置 Nginx 脚本
# 生成独立的配置文件，需要手动 include 到主配置中

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 获取部署路径（从环境变量或使用默认值）
DEPLOY_PATH=${DEPLOY_PATH:-/opt/stock-scanner}
BACKEND_PORT=${BACKEND_PORT:-8001}

print_info "开始生成 Nginx 配置文件..."
print_info "部署路径: $DEPLOY_PATH"
print_info "后端端口: $BACKEND_PORT"

# 检查部署路径是否存在
if [ ! -d "$DEPLOY_PATH/dist" ]; then
    print_error "部署路径不存在: $DEPLOY_PATH/dist"
    print_error "请确认部署路径是否正确，或先运行部署脚本"
    exit 1
fi

# 检查 Nginx 是否安装
if ! command -v nginx &> /dev/null; then
    print_info "安装 Nginx..."
    if command -v yum &> /dev/null; then
        sudo yum install -y nginx
    elif command -v apt-get &> /dev/null; then
        sudo apt-get update -qq && sudo apt-get install -y nginx
    else
        print_error "无法自动安装 Nginx，请手动安装"
        exit 1
    fi
fi

# 创建 Nginx 配置文件
NGINX_CONF="/etc/nginx/conf.d/stock-scanner.conf"
print_info "生成配置文件: $NGINX_CONF"

sudo tee "$NGINX_CONF" > /dev/null <<EOF
# Stock Scanner 项目配置
# 此配置文件需要手动 include 到主配置文件 (nginx.conf) 的 server 块中
# 例如：在 server { ... } 块内添加: include /etc/nginx/conf.d/stock-scanner.conf;
#
# 注意：location 顺序很重要！/platform/api 必须在 /platform 之前

# 后端API代理 - /platform/api 路径（必须在 /platform 之前）
# 使用 location /platform/api/ 确保优先匹配，避免被 /platform 拦截
location /platform/api/ {
    proxy_pass http://127.0.0.1:${BACKEND_PORT}/api/;
    proxy_http_version 1.1;
    proxy_set_header Upgrade \$http_upgrade;
    proxy_set_header Connection 'upgrade';
    proxy_set_header Host \$host;
    proxy_set_header X-Real-IP \$remote_addr;
    proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto \$scheme;
    proxy_cache_bypass \$http_upgrade;
    
    # 超时设置（支持长时间运行的扫描任务）
    proxy_connect_timeout 600s;
    proxy_send_timeout 600s;
    proxy_read_timeout 600s;
}

# WebSocket支持 - /platform/ws 路径
location ~ ^/platform/ws {
    rewrite ^/platform/ws(.*)$ /ws\$1 break;
    proxy_pass http://127.0.0.1:${BACKEND_PORT};
    proxy_http_version 1.1;
    proxy_set_header Upgrade \$http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host \$host;
    proxy_set_header X-Real-IP \$remote_addr;
    proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    
    # WebSocket超时设置
    proxy_connect_timeout 7d;
    proxy_send_timeout 7d;
    proxy_read_timeout 7d;
}

# 前端静态文件 - /platform 路径（必须在 API 之后）
location = /platform {
    return 301 /platform/;
}

location /platform {
    alias $DEPLOY_PATH/dist;
    index index.html;
    try_files \$uri \$uri/ /platform/index.html;
    
    # 缓存静态资源
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}

# WebSocket支持 - /platform/ws 路径
location /platform/ws {
    rewrite ^/platform/ws(.*)$ /ws$1 break;
    proxy_pass http://127.0.0.1:${BACKEND_PORT};
    proxy_http_version 1.1;
    proxy_set_header Upgrade \$http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host \$host;
    proxy_set_header X-Real-IP \$remote_addr;
    proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    
    # WebSocket超时设置
    proxy_connect_timeout 7d;
    proxy_send_timeout 7d;
    proxy_read_timeout 7d;
}
EOF

print_info "✓ 配置文件已生成: $NGINX_CONF"
print_info ""
print_warn "⚠️  重要：需要手动将此配置 include 到主配置文件"
print_info ""
print_info "在主配置文件 (通常是 /etc/nginx/nginx.conf) 的 server 块中添加："
print_info "  include /etc/nginx/conf.d/stock-scanner.conf;"
print_info ""
print_info "示例："
print_info "  server {"
print_info "      listen 80;"
print_info "      server_name _;"
print_info "      "
print_info "      # 其他配置..."
print_info "      "
print_info "      include /etc/nginx/conf.d/stock-scanner.conf;"
print_info "  }"
print_info ""

# 测试 Nginx 配置（如果主配置已经 include 了此文件）
print_info "测试 Nginx 配置..."
if sudo nginx -t 2>/dev/null; then
    print_info "✓ Nginx 配置测试通过"
    print_info ""
    print_info "如果主配置还未 include 此文件，测试可能会失败，这是正常的。"
    print_info "请先手动 include 后再测试。"
else
    print_warn "⚠ Nginx 配置测试失败"
    print_warn "这可能是因为主配置还未 include 此文件"
    print_warn "请先手动 include 后再运行: sudo nginx -t"
fi

# 检查后端服务
print_info ""
print_info "检查后端服务状态..."
if sudo systemctl is-active --quiet stock-scanner.service 2>/dev/null; then
    print_info "✓ 后端服务正在运行"
else
    print_warn "⚠ 后端服务未运行，请启动: sudo systemctl start stock-scanner.service"
fi

# 显示访问信息
SERVER_IP=$(hostname -I | awk '{print $1}' 2>/dev/null || echo "your-server-ip")
print_info ""
print_info "配置生成完成！"
print_info ""
print_info "下一步操作："
print_info "1. 编辑主配置文件: sudo vi /etc/nginx/nginx.conf"
print_info "2. 在 server 块中添加: include /etc/nginx/conf.d/stock-scanner.conf;"
print_info "3. 测试配置: sudo nginx -t"
print_info "4. 重启 Nginx: sudo systemctl restart nginx"
print_info ""
print_info "配置完成后，访问地址："
print_info "  前端: http://$SERVER_IP/platform"
print_info "  后端API: http://$SERVER_IP/platform/api"
