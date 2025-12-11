#!/bin/bash
# 安装缺失的Python模块脚本
# 在服务器上运行此脚本来安装缺失的模块

set -e

echo "=== 安装缺失的Python模块 ==="

PYTHON3_CMD=$(which python3 || echo "python3")
echo "使用Python: $PYTHON3_CMD"

# 镜像源列表
MIRRORS=(
    "https://pypi.tuna.tsinghua.edu.cn/simple"
    "https://mirrors.aliyun.com/pypi/simple"
    "https://pypi.douban.com/simple"
    "https://pypi.org/simple"
)

# 需要安装的模块（从requirements.txt）
REQUIRED_PACKAGES=(
    "uvicorn>=0.15.0"
    "fastapi>=0.68.0"
    "baostock<=0.8.9"
    "numpy>=1.19.0"
    "pandas>=1.3.0"
    "pydantic>=1.10.0"
    "python-dotenv"
    "scipy"
    "tqdm>=4.64.0"
    "colorama>=0.4.6"
)

echo ""
echo "检查并安装缺失的模块..."

for package in "${REQUIRED_PACKAGES[@]}"; do
    # 提取模块名（去掉版本号）
    module_name=$(echo "$package" | sed 's/[<>=].*//' | sed 's/python-dotenv/dotenv/')
    
    echo ""
    echo "检查 $module_name..."
    
    if $PYTHON3_CMD -c "import $module_name" 2>/dev/null; then
        echo "✓ $module_name 已安装"
    else
        echo "✗ $module_name 未安装，开始安装..."
        INSTALLED=false
        for mirror in "${MIRRORS[@]}"; do
            if $PYTHON3_CMD -m pip install "$package" -i "$mirror" 2>&1; then
                echo "✓ $package 安装成功 (使用镜像: $mirror)"
                INSTALLED=true
                break
            fi
        done
        if [ "$INSTALLED" = false ]; then
            echo "✗ $package 安装失败"
        fi
    fi
done

echo ""
echo "=== 验证安装 ==="
FAILED=0

for package in "${REQUIRED_PACKAGES[@]}"; do
    module_name=$(echo "$package" | sed 's/[<>=].*//' | sed 's/python-dotenv/dotenv/')
    if $PYTHON3_CMD -c "import $module_name" 2>/dev/null; then
        version=$($PYTHON3_CMD -c "import $module_name; print(getattr($module_name, '__version__', 'unknown'))" 2>/dev/null || echo "unknown")
        echo "✓ $module_name ($version)"
    else
        echo "✗ $module_name 仍然未安装"
        FAILED=$((FAILED + 1))
    fi
done

echo ""
if [ $FAILED -eq 0 ]; then
    echo "=== 所有模块安装成功 ==="
    echo "现在可以重启服务:"
    echo "sudo systemctl restart stock-scanner.service"
    echo "sudo systemctl status stock-scanner.service"
else
    echo "=== 警告: 有 $FAILED 个模块安装失败 ==="
    echo "请检查错误信息并手动安装"
fi
