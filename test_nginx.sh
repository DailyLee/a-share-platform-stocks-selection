#!/bin/bash
# 快速测试 Nginx 配置和 API 访问

echo "=== 测试 Nginx 配置 ==="
sudo nginx -t

echo ""
echo "=== 检查配置文件 ==="
echo "配置文件位置: /etc/nginx/conf.d/stock-scanner.conf"
if [ -f "/etc/nginx/conf.d/stock-scanner.conf" ]; then
    echo "✓ 配置文件存在"
    echo ""
    echo "配置文件内容:"
    cat /etc/nginx/conf.d/stock-scanner.conf
else
    echo "✗ 配置文件不存在"
fi

echo ""
echo "=== 检查主配置是否 include ==="
if grep -q "include.*stock-scanner" /etc/nginx/nginx.conf; then
    echo "✓ 主配置已 include"
    grep "include.*stock-scanner" /etc/nginx/nginx.conf
else
    echo "✗ 主配置未 include"
    echo "需要在 server 块中添加: include /etc/nginx/conf.d/stock-scanner.conf;"
fi

echo ""
echo "=== 检查后端服务 ==="
if sudo systemctl is-active --quiet stock-scanner.service; then
    echo "✓ 后端服务正在运行"
else
    echo "✗ 后端服务未运行"
    echo "启动命令: sudo systemctl start stock-scanner.service"
fi

echo ""
echo "=== 检查端口监听 ==="
if netstat -tlnp 2>/dev/null | grep :8001 || ss -tlnp 2>/dev/null | grep :8001; then
    echo "✓ 端口 8001 正在监听"
else
    echo "✗ 端口 8001 未监听"
fi

echo ""
echo "=== 测试后端 API（直接访问） ==="
echo "测试: curl http://127.0.0.1:8001/api/"
curl -s http://127.0.0.1:8001/api/ || echo "✗ 后端 API 无法访问"

echo ""
echo "=== 测试 Nginx 代理 ==="
echo "测试: curl http://127.0.0.1/platform/api/"
curl -s http://127.0.0.1/platform/api/ || echo "✗ Nginx 代理无法访问"

echo ""
echo "=== 查看 Nginx 错误日志（最后10行） ==="
sudo tail -10 /var/log/nginx/error.log 2>/dev/null || echo "无法读取错误日志"

echo ""
echo "=== 查看 Nginx 访问日志（最后5行） ==="
sudo tail -5 /var/log/nginx/access.log 2>/dev/null || echo "无法读取访问日志"
