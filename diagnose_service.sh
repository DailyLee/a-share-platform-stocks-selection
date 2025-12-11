#!/bin/bash
# 服务诊断脚本
# 在服务器上运行此脚本来诊断服务问题

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== 服务诊断脚本 ==="
echo ""

echo "1. 检查服务文件是否存在"
if [ -f "$SCRIPT_DIR/api/index.py" ]; then
    echo "✓ api/index.py 存在"
else
    echo "✗ api/index.py 不存在"
    exit 1
fi

echo ""
echo "2. 检查Python版本"
python3 --version

echo ""
echo "3. 检查必要的Python包"
echo "检查 fastapi..."
python3 -c "import fastapi; print('✓ fastapi:', fastapi.__version__)" 2>/dev/null || echo "✗ fastapi 未安装"

echo "检查 uvicorn..."
python3 -c "import uvicorn; print('✓ uvicorn:', uvicorn.__version__)" 2>/dev/null || echo "✗ uvicorn 未安装"

echo "检查 pandas..."
python3 -c "import pandas; print('✓ pandas:', pandas.__version__)" 2>/dev/null || echo "✗ pandas 未安装"

echo ""
echo "4. 测试Python模块导入"
cd "$SCRIPT_DIR/api"
if python3 -c "import sys; sys.path.insert(0, '..'); from api.index import app" 2>&1; then
    echo "✓ Python模块导入成功"
else
    echo "✗ Python模块导入失败"
    echo "错误详情:"
    python3 -c "import sys; sys.path.insert(0, '..'); from api.index import app" 2>&1 | head -30
fi

echo ""
echo "5. 检查服务状态"
if systemctl is-active --quiet stock-scanner.service 2>/dev/null; then
    echo "✓ 服务正在运行"
    systemctl status stock-scanner.service --no-pager -l | head -15
else
    echo "✗ 服务未运行"
    echo "服务状态:"
    systemctl status stock-scanner.service --no-pager -l | head -15 || true
fi

echo ""
echo "6. 检查服务日志（最近20行）"
journalctl -u stock-scanner.service -n 20 --no-pager || echo "无法读取日志"

echo ""
echo "7. 检查端口占用"
if netstat -tlnp 2>/dev/null | grep :8001 || ss -tlnp 2>/dev/null | grep :8001; then
    echo "✓ 端口8001正在监听"
else
    echo "✗ 端口8001未监听"
fi

echo ""
echo "8. 尝试手动启动测试"
echo "运行: cd $SCRIPT_DIR/api && python3 -m uvicorn index:app --host 0.0.0.0 --port 8001"
echo "（按Ctrl+C停止测试）"
