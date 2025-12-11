#!/bin/bash
# 快速修复Python依赖脚本
# 在服务器上运行此脚本来安装缺失的依赖

set -e

echo "=== 修复Python依赖 ==="

# 检测Python和pip
PYTHON3_CMD=$(which python3 || echo "python3")
PIP3_CMD=$(which pip3 || echo "pip3")

echo "使用Python: $PYTHON3_CMD"
echo "使用pip: $PIP3_CMD"

# 检查Python版本
$PYTHON3_CMD --version

# 升级pip
echo ""
echo "1. 升级pip..."
$PYTHON3_CMD -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple 2>/dev/null || \
$PYTHON3_CMD -m pip install --upgrade pip 2>/dev/null || true

# 安装关键依赖
echo ""
echo "2. 安装关键依赖..."

MIRRORS=(
    "https://pypi.tuna.tsinghua.edu.cn/simple"
    "https://mirrors.aliyun.com/pypi/simple"
    "https://pypi.douban.com/simple"
    "https://pypi.org/simple"
)

install_package() {
    local package=$1
    echo "安装 $package..."
    for mirror in "${MIRRORS[@]}"; do
        if $PYTHON3_CMD -m pip install "$package" -i "$mirror" 2>/dev/null; then
            echo "✓ $package 安装成功 (使用镜像: $mirror)"
            return 0
        fi
    done
    echo "✗ $package 安装失败"
    return 1
}

# 安装uvicorn
if ! $PYTHON3_CMD -c "import uvicorn" 2>/dev/null; then
    install_package "uvicorn>=0.15.0" || exit 1
else
    echo "✓ uvicorn 已安装: $($PYTHON3_CMD -c 'import uvicorn; print(uvicorn.__version__)' 2>/dev/null)"
fi

# 安装fastapi
if ! $PYTHON3_CMD -c "import fastapi" 2>/dev/null; then
    install_package "fastapi>=0.68.0" || exit 1
else
    echo "✓ fastapi 已安装: $($PYTHON3_CMD -c 'import fastapi; print(fastapi.__version__)' 2>/dev/null)"
fi

# 如果有requirements.txt，安装所有依赖
if [ -f "api/requirements.txt" ]; then
    echo ""
    echo "3. 安装requirements.txt中的所有依赖..."
    cd api
    for mirror in "${MIRRORS[@]}"; do
        if $PYTHON3_CMD -m pip install -r requirements.txt -i "$mirror" 2>&1; then
            echo "✓ 所有依赖安装成功 (使用镜像: $mirror)"
            break
        else
            echo "镜像 $mirror 失败，尝试下一个..."
        fi
    done
    cd ..
fi

# 验证安装
echo ""
echo "4. 验证安装..."
$PYTHON3_CMD -c "import uvicorn; print('✓ uvicorn:', uvicorn.__version__)" || exit 1
$PYTHON3_CMD -c "import fastapi; print('✓ fastapi:', fastapi.__version__)" || exit 1
$PYTHON3_CMD -c "import pandas; print('✓ pandas:', pandas.__version__)" 2>/dev/null || echo "⚠ pandas 未安装"
$PYTHON3_CMD -c "import numpy; print('✓ numpy:', numpy.__version__)" 2>/dev/null || echo "⚠ numpy 未安装"

echo ""
echo "=== 完成 ==="
echo "现在可以尝试重启服务:"
echo "sudo systemctl restart stock-scanner.service"
echo "sudo systemctl status stock-scanner.service"
