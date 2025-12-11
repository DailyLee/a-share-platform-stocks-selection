#!/bin/bash
# 快速修复Nginx配置脚本
# 在服务器上运行此脚本来配置Nginx

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== 检查前端构建文件 ==="
if [ ! -d "dist" ]; then
    echo "错误: dist目录不存在，请先构建前端"
    exit 1
fi

if [ ! -f "dist/index.html" ]; then
    echo "错误: dist/index.html不存在，请先构建前端"
    exit 1
fi

echo "✓ 前端文件存在"

echo ""
echo "=== 安装Nginx ==="
if ! command -v nginx &> /dev/null; then
    if command -v yum &> /dev/null; then
        sudo yum install -y nginx
    elif command -v apt-get &> /dev/null; then
        sudo apt-get update && sudo apt-get install -y nginx
    fi
else
    echo "✓ Nginx已安装"
fi

echo ""
echo "=== 生成Nginx配置 ==="
NGINX_CONF="/etc/nginx/conf.d/stock-scanner.conf"
BACKEND_PORT=${BACKEND_PORT:-8001}

sudo tee "$NGINX_CONF" > /dev/null <<EOF
server {
    listen 80;
    server_name _;

    # 前端静态文件
    location / {
        root $SCRIPT_DIR/dist;
        index index.html;
        try_files \$uri \$uri/ /index.html;
        
        # 缓存静态资源
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # 后端API代理
    location /api {
        proxy_pass http://127.0.0.1:${BACKEND_PORT};
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        
        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # WebSocket支持
    location /ws {
        proxy_pass http://127.0.0.1:${BACKEND_PORT};
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }

    # 日志
    access_log /var/log/nginx/stock-scanner-access.log;
    error_log /var/log/nginx/stock-scanner-error.log;
}
EOF

echo "✓ Nginx配置已生成"

echo ""
echo "=== 测试Nginx配置 ==="
if sudo nginx -t; then
    echo "✓ Nginx配置测试通过"
else
    echo "✗ Nginx配置测试失败"
    exit 1
fi

echo ""
echo "=== 启动Nginx ==="
sudo systemctl enable nginx
sudo systemctl restart nginx

echo ""
echo "=== 检查Nginx状态 ==="
sudo systemctl status nginx --no-pager -l

echo ""
echo "=== 检查端口监听 ==="
sudo netstat -tlnp | grep :80 || sudo ss -tlnp | grep :80

echo ""
echo "=== 检查防火墙 ==="
if command -v firewall-cmd &> /dev/null; then
    sudo firewall-cmd --permanent --add-port=80/tcp
    sudo firewall-cmd --reload
    echo "✓ 防火墙已配置"
elif command -v iptables &> /dev/null; then
    sudo iptables -I INPUT -p tcp --dport 80 -j ACCEPT
    echo "✓ iptables已配置"
fi

echo ""
echo "=== 完成 ==="
echo "Nginx已配置并启动"
echo "请检查："
echo "1. 阿里云安全组是否开放了80端口"
echo "2. 访问 http://$(hostname -I | awk '{print $1}') 或 http://你的服务器IP"
