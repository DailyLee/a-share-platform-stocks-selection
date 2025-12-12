#!/bin/bash

# 服务器端部署脚本
# 在阿里云ECS上执行，用于安装依赖、构建项目、启动服务
# 系统: Alibaba Cloud Linux 3.2104 LTS 64位

set -e  # 遇到错误立即退出

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

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

print_info "当前部署目录: $SCRIPT_DIR"

# 检查系统版本
print_info "检查系统版本..."
if [ -f /etc/os-release ]; then
    . /etc/os-release
    print_info "系统: $PRETTY_NAME"
fi

# 安装必要工具
print_info "安装必要工具..."
if command -v yum &> /dev/null; then
    yum install -y rsync curl wget coreutils 2>/dev/null || true
elif command -v apt-get &> /dev/null; then
    apt-get update -qq && apt-get install -y rsync curl wget coreutils 2>/dev/null || true
fi

# 检查timeout命令是否可用，如果不可用则创建一个简单的包装函数
if ! command -v timeout &> /dev/null; then
    print_warn "timeout命令不可用，将使用备用方法"
    timeout() {
        local duration=$1
        shift
        # 使用后台进程和sleep实现简单的超时
        "$@" &
        local pid=$!
        sleep $duration
        if kill -0 $pid 2>/dev/null; then
            kill $pid 2>/dev/null
            return 124
        fi
        wait $pid
        return $?
    }
fi

# 1. 安装Node.js和npm（如果未安装或版本<=20）
print_info "检查Node.js安装..."
NEED_INSTALL=false
NEED_UPGRADE=false

if ! command -v node &> /dev/null; then
    NEED_INSTALL=true
    print_warn "Node.js未安装，开始安装..."
else
    # 检查当前版本
    NODE_VERSION=$(node --version | sed 's/v//' | cut -d. -f1)
    print_info "当前Node.js版本: $(node --version) (主版本: $NODE_VERSION)"
    
    if [ "$NODE_VERSION" -le 20 ]; then
        NEED_UPGRADE=true
        print_warn "Node.js版本 $NODE_VERSION <= 20，需要升级到22.x"
    else
        print_info "Node.js版本满足要求 (>=20)"
        print_info "npm版本: $(npm --version)"
    fi
fi

if [ "$NEED_INSTALL" = true ] || [ "$NEED_UPGRADE" = true ]; then
    # 使用NodeSource安装/升级Node.js 22.x
    print_info "配置NodeSource仓库..."
    print_info "提示: 这可能需要几分钟，请耐心等待..."
    
    # 使用timeout命令限制curl执行时间（5分钟超时）
    if ! timeout 300 curl -fsSL https://rpm.nodesource.com/setup_22.x 2>/dev/null | bash - 2>&1 | tee /tmp/nodesource_setup.log; then
        EXIT_CODE=${PIPESTATUS[0]}
        if [ "$EXIT_CODE" -eq 124 ]; then
            print_error "NodeSource仓库配置超时（超过5分钟）"
        else
            print_error "NodeSource仓库配置失败（退出码: $EXIT_CODE）"
            print_error "配置日志（最后10行）:"
            tail -10 /tmp/nodesource_setup.log 2>/dev/null || true
        fi
        print_error "请检查网络连接或手动配置NodeSource仓库"
        exit 1
    fi
    print_info "NodeSource仓库配置完成"
    
    if [ "$NEED_UPGRADE" = true ]; then
        print_info "升级Node.js到22.x..."
        print_info "提示: 正在下载和安装Node.js，这可能需要几分钟..."
        print_info "提示: yum会显示下载和安装进度，请耐心等待..."
        # 升级时确保使用nodesource仓库，添加超时（10分钟）
        if timeout 600 yum install -y nodejs --disablerepo='*' --enablerepo=nodesource 2>&1 | tee /tmp/nodejs_install.log; then
            print_info "Node.js升级成功"
        else
            EXIT_CODE=${PIPESTATUS[0]}
            if [ "$EXIT_CODE" -eq 124 ]; then
                print_error "Node.js升级超时（超过10分钟）"
            else
                print_warn "使用nodesource仓库升级失败，尝试备用方法..."
                if timeout 600 yum upgrade -y nodejs 2>&1 | tee -a /tmp/nodejs_install.log; then
                    print_info "Node.js升级成功（使用备用方法）"
                else
                    EXIT_CODE2=${PIPESTATUS[0]}
                    print_error "Node.js升级失败（退出码: $EXIT_CODE2）"
                fi
            fi
            if [ "$EXIT_CODE" -eq 124 ] || [ "${EXIT_CODE2:-0}" -ne 0 ]; then
                print_error "安装日志（最后20行）:"
                tail -20 /tmp/nodejs_install.log 2>/dev/null || true
                exit 1
            fi
        fi
    else
        print_info "安装Node.js 22.x..."
        print_info "提示: 正在下载和安装Node.js，这可能需要几分钟..."
        print_info "提示: yum会显示下载和安装进度，请耐心等待..."
        # 添加超时（10分钟）
        if ! timeout 600 yum install -y nodejs 2>&1 | tee /tmp/nodejs_install.log; then
            EXIT_CODE=${PIPESTATUS[0]}
            if [ "$EXIT_CODE" -eq 124 ]; then
                print_error "Node.js安装超时（超过10分钟）"
            else
                print_error "Node.js安装失败（退出码: $EXIT_CODE）"
            fi
            print_error "安装日志（最后20行）:"
            tail -20 /tmp/nodejs_install.log 2>/dev/null || true
            exit 1
        fi
        print_info "Node.js安装成功"
    fi
    
    print_info "Node.js安装完成: $(node --version)"
    print_info "npm安装完成: $(npm --version)"
    
    # 验证版本是否符合要求
    NODE_VERSION_CHECK=$(node --version | sed 's/v//' | cut -d. -f1)
    if [ "$NODE_VERSION_CHECK" -le 20 ]; then
        print_error "Node.js升级失败，当前版本仍为 $NODE_VERSION_CHECK"
        exit 1
    fi
fi

# 2. 安装Python 3和pip（如果未安装）
print_info "检查Python 3安装..."
if ! command -v python3 &> /dev/null; then
    print_warn "Python 3未安装，开始安装..."
    yum install -y python3 python3-pip
    print_info "Python 3安装完成: $(python3 --version)"
else
    print_info "Python 3已安装: $(python3 --version)"
fi

# 检查Python版本，必须 >= 3.7
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

print_info "检查Python版本要求 (需要 >= 3.7)..."

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 7 ]); then
    print_error "Python版本不符合要求！"
    print_error "当前版本: $PYTHON_VERSION"
    print_error "要求版本: Python 3.7 或更高版本"
    print_error ""
    print_error "请升级Python版本后再继续部署。"
    print_error "可以使用以下命令安装Python 3.7+:"
    print_error "  yum install -y python37 python37-pip"
    print_error "  或使用 pyenv 等工具管理Python版本"
    exit 1
else
    print_info "✓ Python版本检查通过: $PYTHON_VERSION"
fi

# 检查并升级pip（仅在需要时）
print_info "检查pip版本..."
PIP_VERSION=$(python3 -m pip --version 2>/dev/null | grep -oP 'pip \K[0-9]+\.[0-9]+' || echo "0.0")
PIP_MAJOR=$(echo $PIP_VERSION | cut -d. -f1)
PIP_MINOR=$(echo $PIP_VERSION | cut -d. -f2)

# 只在pip版本过低时升级（例如 < 20.0）
if [ "$PIP_MAJOR" -lt 20 ]; then
    print_info "pip版本过低 ($PIP_VERSION)，正在升级..."
    python3 -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple 2>/dev/null || \
    python3 -m pip install --upgrade pip 2>/dev/null || true
    print_info "pip升级完成: $(python3 -m pip --version 2>/dev/null | grep -oP 'pip \K[0-9.]+' || echo 'unknown')"
else
    print_info "pip版本满足要求 ($PIP_VERSION)，跳过升级"
fi

# 3. 安装前端依赖
print_info "安装前端依赖..."
if [ -f "package.json" ]; then
    npm install --production=false
    print_info "前端依赖安装完成"
else
    print_error "未找到package.json文件"
    exit 1
fi

# 4. 构建前端
print_info "构建前端项目..."
npm run build
print_info "前端构建完成"

# 5. 安装Python依赖
print_info "安装Python依赖..."
if [ -f "api/requirements.txt" ]; then
    cd api
    
    # 确保使用系统pip3
    PIP3_CMD=$(which pip3 || echo "pip3")
    PYTHON3_CMD=$(which python3 || echo "python3")
    
    print_info "使用Python: $PYTHON3_CMD"
    print_info "使用pip: $PIP3_CMD"
    
    # 检查并升级pip（仅在需要时）
    print_info "检查pip版本..."
    PIP_VERSION=$($PYTHON3_CMD -m pip --version 2>/dev/null | grep -oP 'pip \K[0-9]+\.[0-9]+' || echo "0.0")
    PIP_MAJOR=$(echo $PIP_VERSION | cut -d. -f1)
    PIP_MINOR=$(echo $PIP_VERSION | cut -d. -f2)
    
    # 只在pip版本过低时升级（例如 < 20.0）
    if [ "$PIP_MAJOR" -lt 20 ]; then
        print_info "pip版本过低 ($PIP_VERSION)，正在升级..."
        $PYTHON3_CMD -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple 2>/dev/null || \
        $PYTHON3_CMD -m pip install --upgrade pip 2>/dev/null || true
        print_info "pip升级完成: $($PYTHON3_CMD -m pip --version 2>/dev/null | grep -oP 'pip \K[0-9.]+' || echo 'unknown')"
    else
        print_info "pip版本满足要求 ($PIP_VERSION)，跳过升级"
    fi
    
    # 检查依赖是否已安装且版本满足要求
    print_info "检查Python依赖是否已安装..."
    NEED_INSTALL=false
    
    # 使用Python脚本检查requirements.txt中的所有依赖是否已安装且版本满足要求
    if $PYTHON3_CMD -c "
import sys
import subprocess

def check_requirements():
    try:
        import pkg_resources
    except ImportError:
        # 如果没有pkg_resources，尝试安装
        return False
    
    try:
        with open('requirements.txt', 'r') as f:
            for line in f:
                line = line.strip()
                # 跳过注释和空行
                if not line or line.startswith('#'):
                    continue
                try:
                    # 检查包是否满足版本要求
                    pkg_resources.require(line)
                except (pkg_resources.DistributionNotFound, pkg_resources.VersionConflict) as e:
                    return False
        return True
    except Exception as e:
        return False

sys.exit(0 if check_requirements() else 1)
" 2>/dev/null; then
        print_info "✓ 所有依赖已安装且版本满足要求，跳过安装"
        INSTALL_SUCCESS=true
        NEED_INSTALL=false
    else
        print_info "检测到需要安装或更新的依赖"
        NEED_INSTALL=true
    fi
    
    # 如果需要安装，尝试多个镜像源，按顺序尝试
    if [ "$NEED_INSTALL" = true ]; then
        print_info "开始安装/更新Python依赖..."
        INSTALL_SUCCESS=false
        
        # 镜像源列表
        MIRRORS=(
            "https://pypi.tuna.tsinghua.edu.cn/simple"
            "https://mirrors.aliyun.com/pypi/simple"
            "https://pypi.douban.com/simple"
            "https://pypi.org/simple"
        )
        
        for mirror in "${MIRRORS[@]}"; do
            print_info "尝试使用镜像源: $mirror"
            print_info "正在安装/更新Python依赖（这可能需要几分钟，请耐心等待）..."
            print_info "提示: 如果看起来卡住了，实际上可能正在下载和安装包，请稍候..."
            
            # 使用--upgrade-strategy only-if-needed，只在需要时升级
            # 使用tee同时显示输出和保存到文件
            # 直接显示所有输出，让用户看到进度
            if $PYTHON3_CMD -m pip install -r requirements.txt --upgrade-strategy only-if-needed -i "$mirror" 2>&1 | tee /tmp/pip_install.log; then
                PIP_EXIT_CODE=0
            else
                PIP_EXIT_CODE=1
            fi
            
            # 检查是否有错误（即使退出码为0，也可能有包安装失败）
            HAS_ERROR=false
            if grep -q "ERROR" /tmp/pip_install.log; then
                HAS_ERROR=true
                print_error "检测到安装错误:"
                grep "ERROR" /tmp/pip_install.log | head -5
            fi
            
            # 检查是否有"No matching distribution found"错误
            if grep -q "No matching distribution found\|Could not find a version" /tmp/pip_install.log; then
                HAS_ERROR=true
                print_error "检测到版本不兼容错误:"
                grep -E "No matching distribution found|Could not find a version" /tmp/pip_install.log | head -3
            fi
            
            if [ $PIP_EXIT_CODE -eq 0 ] && [ "$HAS_ERROR" = false ]; then
                INSTALL_SUCCESS=true
                print_info "✓ 使用镜像源 $mirror 安装成功"
                # 显示安装摘要
                if grep -q "Successfully installed" /tmp/pip_install.log; then
                    print_info "已安装的包:"
                    grep "Successfully installed" /tmp/pip_install.log | tail -1
                fi
                break
            else
                if [ $PIP_EXIT_CODE -ne 0 ]; then
                    print_warn "镜像源 $mirror 安装失败 (退出码: $PIP_EXIT_CODE)"
                else
                    print_warn "镜像源 $mirror 安装部分失败 (退出码: $PIP_EXIT_CODE，但检测到错误)"
                fi
                print_warn "尝试下一个镜像源..."
            fi
        done
    else
        print_info "依赖检查完成，无需安装"
    fi
    
    if [ "$INSTALL_SUCCESS" = false ] && [ "$NEED_INSTALL" = true ]; then
        print_error "所有镜像源都失败，尝试逐个安装关键依赖..."
        print_error "最后尝试的日志（最后20行）:"
        tail -20 /tmp/pip_install.log 2>/dev/null || true
        print_error ""
        
        # 尝试逐个安装关键依赖
        CRITICAL_PACKAGES=("uvicorn>=0.15.0" "fastapi>=0.68.0" "numpy>=1.19.0" "pandas>=1.3.0")
        for package in "${CRITICAL_PACKAGES[@]}"; do
            print_info "安装 $package..."
            INSTALLED=false
            for mirror in "${MIRRORS[@]}"; do
                # 显示安装进度
                if $PYTHON3_CMD -m pip install "$package" -i "$mirror" 2>&1; then
                    print_info "✓ $package 安装成功"
                    INSTALLED=true
                    break
                fi
            done
            if [ "$INSTALLED" = false ]; then
                print_error "✗ $package 安装失败"
            fi
        done
        
        # 安装其他依赖（不指定版本）
        print_info "安装其他依赖..."
        OTHER_PACKAGES=("baostock" "pydantic" "python-dotenv" "scipy" "tqdm" "colorama")
        for package in "${OTHER_PACKAGES[@]}"; do
            for mirror in "${MIRRORS[@]}"; do
                if $PYTHON3_CMD -m pip install "$package" -i "$mirror" 2>/dev/null; then
                    break
                fi
            done
        done
        
        # 最终验证
        print_info "验证关键依赖..."
        if ! $PYTHON3_CMD -c "import uvicorn" 2>/dev/null; then
            print_error "uvicorn仍然未安装，服务无法启动"
            exit 1
        fi
        if ! $PYTHON3_CMD -c "import fastapi" 2>/dev/null; then
            print_error "fastapi仍然未安装，服务无法启动"
            exit 1
        fi
        print_info "✓ 关键依赖验证通过"
    fi
    
    # 验证所有关键依赖是否安装成功
    print_info "验证所有依赖..."
    
    # 需要验证的模块列表（从requirements.txt提取）
    REQUIRED_MODULES=(
        "uvicorn"
        "fastapi"
        "baostock"
        "numpy"
        "pandas"
        "pydantic"
        "dotenv:python-dotenv"
        "scipy"
        "tqdm"
        "colorama"
    )
    
    MISSING_MODULES=()
    
    for module_info in "${REQUIRED_MODULES[@]}"; do
        # 处理模块名和包名不同的情况（如dotenv:python-dotenv）
        if [[ "$module_info" == *":"* ]]; then
            module_name="${module_info%%:*}"
            package_name="${module_info#*:}"
        else
            module_name="$module_info"
            package_name="$module_info"
        fi
        
        if ! $PYTHON3_CMD -c "import $module_name" 2>/dev/null; then
            print_warn "✗ $module_name 未安装"
            MISSING_MODULES+=("$package_name")
        else
            print_info "✓ $module_name 已安装"
        fi
    done
    
    # 如果有缺失的模块，尝试安装
    if [ ${#MISSING_MODULES[@]} -gt 0 ]; then
        print_warn "发现缺失的模块，尝试安装..."
        for package in "${MISSING_MODULES[@]}"; do
            print_info "安装 $package..."
            INSTALLED=false
            for mirror in "${MIRRORS[@]}"; do
                if $PYTHON3_CMD -m pip install "$package" -i "$mirror" 2>&1 | grep -q "Successfully installed\|Requirement already satisfied"; then
                    print_info "✓ $package 安装成功"
                    INSTALLED=true
                    break
                fi
            done
            if [ "$INSTALLED" = false ]; then
                print_error "✗ $package 安装失败"
            fi
        done
        
        # 再次验证
        print_info "再次验证缺失的模块..."
        for module_info in "${MISSING_MODULES[@]}"; do
            if [[ "$module_info" == *":"* ]]; then
                module_name="${module_info%%:*}"
            else
                module_name="$module_info"
            fi
            
            if ! $PYTHON3_CMD -c "import $module_name" 2>/dev/null; then
                print_error "✗ $module_name 仍然未安装，服务可能无法启动"
            else
                print_info "✓ $module_name 现在已安装"
            fi
        done
    fi
    
    print_info "✓ 依赖验证完成"
    
    cd ..
    print_info "Python依赖安装完成"
else
    print_error "未找到api/requirements.txt文件"
    exit 1
fi

# 6. 创建必要的目录
print_info "创建必要的目录..."
mkdir -p logs
mkdir -p data

# 7. 设置systemd服务（如果服务文件存在）
if [ -f "/tmp/stock-scanner.service" ]; then
    print_info "配置systemd服务..."
    
    # 检查必要的文件是否存在
    if [ ! -f "$SCRIPT_DIR/api/index.py" ]; then
        print_error "未找到 api/index.py 文件"
        exit 1
    fi
    
    # 验证uvicorn是否可用
    print_info "验证uvicorn是否可用..."
    if ! python3 -c "import uvicorn" 2>/dev/null; then
        print_error "uvicorn未安装，尝试安装..."
        python3 -m pip install uvicorn -i https://pypi.tuna.tsinghua.edu.cn/simple || \
        python3 -m pip install uvicorn || {
            print_error "uvicorn安装失败，服务无法启动"
            exit 1
        }
    fi
    print_info "✓ uvicorn可用"
    
    # 定义镜像源（如果还没有定义）
    if [ -z "${MIRRORS+x}" ]; then
        MIRRORS=(
            "https://pypi.tuna.tsinghua.edu.cn/simple"
            "https://mirrors.aliyun.com/pypi/simple"
            "https://pypi.douban.com/simple"
            "https://pypi.org/simple"
        )
    fi
    
    # 测试Python导入
    print_info "测试Python模块导入..."
    IMPORT_TEST=$(python3 -c "import sys; sys.path.insert(0, '$SCRIPT_DIR'); from api.index import app" 2>&1)
    IMPORT_EXIT=$?
    
    if [ $IMPORT_EXIT -ne 0 ]; then
        print_warn "Python模块导入测试失败，显示错误信息..."
        echo "$IMPORT_TEST" | head -30
        
        # 检查是否是缺少模块的错误
        if echo "$IMPORT_TEST" | grep -q "ModuleNotFoundError"; then
            MISSING_MODULE=$(echo "$IMPORT_TEST" | grep "ModuleNotFoundError" | sed "s/.*No module named '\([^']*\)'.*/\1/")
            if [ -n "$MISSING_MODULE" ]; then
                print_warn "检测到缺失的模块: $MISSING_MODULE，尝试安装..."
                INSTALLED=false
                for mirror in "${MIRRORS[@]}"; do
                    if python3 -m pip install "$MISSING_MODULE" -i "$mirror" 2>&1; then
                        print_info "✓ $MISSING_MODULE 安装成功"
                        INSTALLED=true
                        break
                    fi
                done
                
                if [ "$INSTALLED" = true ]; then
                    # 再次测试导入
                    if python3 -c "import sys; sys.path.insert(0, '$SCRIPT_DIR'); from api.index import app" 2>/dev/null; then
                        print_info "✓ Python模块导入测试现在通过"
                    else
                        print_error "模块导入仍然失败，请检查其他依赖"
                    fi
                else
                    print_error "无法安装 $MISSING_MODULE，服务可能无法启动"
                fi
            fi
        else
            print_warn "继续尝试启动服务..."
        fi
    else
        print_info "✓ Python模块导入测试通过"
    fi
    
    # 替换服务文件中的路径变量
    sed "s|{{DEPLOY_PATH}}|$SCRIPT_DIR|g" /tmp/stock-scanner.service > /tmp/stock-scanner.service.tmp
    sed "s|{{USER}}|$(whoami)|g" /tmp/stock-scanner.service.tmp > /tmp/stock-scanner.service.final
    
    # 复制服务文件
    sudo cp /tmp/stock-scanner.service.final /etc/systemd/system/stock-scanner.service
    
    # 重新加载systemd
    sudo systemctl daemon-reload
    
    # 停止可能正在运行的服务
    sudo systemctl stop stock-scanner.service 2>/dev/null || true
    
    # 启用并启动服务
    sudo systemctl enable stock-scanner.service
    sudo systemctl restart stock-scanner.service
    
    print_info "systemd服务已配置并启动"
    
    # 等待服务启动
    sleep 3
    
    # 检查服务状态
    if sudo systemctl is-active --quiet stock-scanner.service; then
        print_info "服务运行正常"
        # 显示服务状态
        sudo systemctl status stock-scanner.service --no-pager -l | head -20
    else
        print_error "服务启动失败！"
        print_error "查看详细日志:"
        sudo journalctl -u stock-scanner.service -n 50 --no-pager
        print_error ""
        print_error "尝试手动启动测试:"
        print_error "cd $SCRIPT_DIR/api && python3 -m uvicorn index:app --host 0.0.0.0 --port 8001"
        exit 1
    fi
else
    print_warn "未找到systemd服务文件，跳过服务配置"
    print_info "可以手动启动后端服务: cd api && python3 -m uvicorn index:app --host 0.0.0.0 --port 8001"
fi

# 8. 配置防火墙（如果需要）
print_info "检查防火墙配置..."
if command -v firewall-cmd &> /dev/null; then
    print_info "配置firewalld规则..."
    sudo firewall-cmd --permanent --add-port=8001/tcp 2>/dev/null || true
    sudo firewall-cmd --permanent --add-port=80/tcp 2>/dev/null || true
    sudo firewall-cmd --reload 2>/dev/null || true
elif command -v iptables &> /dev/null; then
    print_info "配置iptables规则..."
    sudo iptables -I INPUT -p tcp --dport 8001 -j ACCEPT 2>/dev/null || true
    sudo iptables -I INPUT -p tcp --dport 80 -j ACCEPT 2>/dev/null || true
fi

print_info "部署完成！"
print_info "前端文件位置: $SCRIPT_DIR/dist"
print_info "后端代码位置: $SCRIPT_DIR/api"
print_info "查看后端服务状态: sudo systemctl status stock-scanner.service"
print_info "查看后端日志: sudo journalctl -u stock-scanner.service -f"
print_warn "注意: 请手动配置Nginx来提供前端静态文件和API代理"
print_info "参考配置文件: nginx.conf.example"
