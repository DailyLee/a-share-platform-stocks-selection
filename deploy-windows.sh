#!/bin/bash

# 自动化部署脚本 - Windows/MSYS2 版本
# 部署到阿里云ECS
# 系统: Alibaba Cloud Linux 3.2104 LTS 64位
#
# 使用方法:
#   1. 在 MSYS2 终端中运行此脚本
#   2. 确保已安装必要工具:
#      pacman -S openssh rsync sshpass
#      或
#      pacman -S openssh rsync expect
#   3. 配置 .deploy.env 文件（参考 .deploy.env.example）
#   4. 运行: ./deploy-windows.sh
#
# 注意:
#   - 此脚本需要在 MSYS2 bash 环境中运行
#   - Windows 路径会自动转换为 MSYS2 路径格式
#   - SSH 密钥路径支持 Windows 和 Unix 两种格式

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查是否在 MSYS2 环境中
if [ -z "$MSYSTEM" ] && [ -z "$MSYS2_PATH" ]; then
    print_warn "未检测到 MSYS2 环境，但继续执行..."
    print_info "建议在 MSYS2 终端中运行此脚本"
fi

# 检查配置文件是否存在
if [ ! -f ".deploy.env" ]; then
    print_error "配置文件 .deploy.env 不存在！"
    print_info "请复制 .deploy.env.example 为 .deploy.env 并填写配置信息"
    exit 1
fi

# 加载配置（安全地读取，避免特殊字符问题）
while IFS= read -r line || [ -n "$line" ]; do
    # 去除首尾空格
    line=$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
    
    # 跳过空行和注释行
    [[ -z "$line" ]] && continue
    [[ "$line" =~ ^# ]] && continue
    
    # 检查是否包含等号
    if [[ ! "$line" =~ = ]]; then
        continue
    fi
    
    # 分割key和value
    key="${line%%=*}"
    value="${line#*=}"
    
    # 移除key和value的前后空格
    key=$(echo "$key" | xargs)
    value=$(echo "$value" | xargs)
    
    # 跳过key为空的情况
    [[ -z "$key" ]] && continue
    
    # 移除value的引号（如果有）
    value=$(echo "$value" | sed "s/^['\"]//; s/['\"]$//")
    
    # 导出变量
    export "$key"="$value"
done < .deploy.env

# 检查必要的配置项
if [ -z "$SERVER_HOST" ] || [ -z "$SERVER_USER" ] || [ -z "$DEPLOY_PATH" ]; then
    print_error "配置文件 .deploy.env 中缺少必要的配置项！"
    exit 1
fi

# 确定认证方式
USE_PASSWORD=false
USE_EXPECT=false
if [ -n "$SERVER_PASSWORD" ]; then
    USE_PASSWORD=true
    # 检查是否安装了sshpass或expect
    if command -v sshpass &> /dev/null; then
        USE_EXPECT=false
        print_info "使用 sshpass 进行密码认证"
    elif command -v expect &> /dev/null; then
        USE_EXPECT=true
        print_info "使用 expect 进行密码认证"
    else
        print_error "使用密码认证需要安装 sshpass 或 expect 工具"
        print_info "在 MSYS2 中安装:"
        print_info "  pacman -S openssh rsync sshpass"
        print_info "  或"
        print_info "  pacman -S openssh rsync expect"
        exit 1
    fi
elif [ -n "$SSH_KEY_PATH" ]; then
    USE_PASSWORD=false
    # 转换 Windows 路径到 MSYS2 路径（如果需要）
    if [[ "$SSH_KEY_PATH" =~ ^[A-Za-z]: ]]; then
        # Windows 路径，转换为 MSYS2 路径
        if command -v cygpath &> /dev/null; then
            SSH_KEY_PATH=$(cygpath -u "$SSH_KEY_PATH" 2>/dev/null || echo "$SSH_KEY_PATH")
        else
            # 手动转换 Windows 路径格式 C:\path\to\file -> /c/path/to/file
            SSH_KEY_PATH=$(echo "$SSH_KEY_PATH" | sed 's|^\([A-Za-z]\):|/\1|' | sed 's|\\|/|g' | tr '[:upper:]' '[:lower:]' | sed 's|^/\([a-z]\)|/\1|')
        fi
    fi
    # 确保路径使用正斜杠
    SSH_KEY_PATH=$(echo "$SSH_KEY_PATH" | sed 's|\\|/|g')
    if [ -f "$SSH_KEY_PATH" ]; then
        SSH_OPTIONS="-i $SSH_KEY_PATH"
    else
        print_warn "SSH密钥文件不存在: $SSH_KEY_PATH，尝试使用默认密钥"
        SSH_OPTIONS=""
    fi
else
    # 尝试使用默认SSH密钥
    USE_PASSWORD=false
    SSH_OPTIONS=""
fi

# 设置SSH端口
SSH_PORT=${SSH_PORT:-22}
SSH_OPTIONS="$SSH_OPTIONS -p $SSH_PORT -o StrictHostKeyChecking=no"
# SCP使用-P（大写）指定端口，SSH使用-p（小写）
SCP_OPTIONS="$SSH_OPTIONS"
SCP_OPTIONS=$(echo "$SCP_OPTIONS" | sed "s/-p $SSH_PORT/-P $SSH_PORT/")

print_info "开始部署到服务器: $SERVER_HOST"
print_info "部署路径: $DEPLOY_PATH"
print_info "认证方式: $([ "$USE_PASSWORD" = true ] && echo "密码认证" || echo "密钥认证")"

# 构建SSH命令前缀
# 获取脚本所在目录（转换为 MSYS2 路径）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# 如果路径是 Windows 格式，转换为 MSYS2 格式
# MSYS2 通常已经使用 Unix 风格路径，但为了兼容性检查
if command -v cygpath &> /dev/null; then
    SCRIPT_DIR=$(cygpath -u "$SCRIPT_DIR" 2>/dev/null || echo "$SCRIPT_DIR")
fi
# 确保路径使用正斜杠（MSYS2 标准）
SCRIPT_DIR=$(echo "$SCRIPT_DIR" | sed 's|\\|/|g')

if [ "$USE_PASSWORD" = true ]; then
    if [ "$USE_EXPECT" = true ]; then
        # 使用expect脚本
        SSH_CMD="$SCRIPT_DIR/ssh_with_password.sh '$SERVER_PASSWORD' ssh $SSH_OPTIONS"
        SCP_CMD="$SCRIPT_DIR/ssh_with_password.sh '$SERVER_PASSWORD' scp $SCP_OPTIONS"
        RSYNC_CMD="rsync"
    else
        # 使用sshpass
        SSH_CMD="sshpass -p '$SERVER_PASSWORD' ssh $SSH_OPTIONS"
        SCP_CMD="sshpass -p '$SERVER_PASSWORD' scp $SCP_OPTIONS"
        RSYNC_CMD="sshpass -p '$SERVER_PASSWORD' rsync"
    fi
else
    SSH_CMD="ssh $SSH_OPTIONS"
    SCP_CMD="scp $SCP_OPTIONS"
    RSYNC_CMD="rsync"
fi

# 检查SSH连接
print_info "检查SSH连接..."
if [ "$USE_PASSWORD" = true ]; then
    if ! eval "$SSH_CMD -o ConnectTimeout=5 $SERVER_USER@$SERVER_HOST 'exit'" 2>/dev/null; then
        print_error "无法连接到服务器，请检查:"
        print_error "1. 服务器IP地址是否正确: $SERVER_HOST"
        print_error "2. 密码是否正确"
        print_error "3. 服务器是否允许SSH连接"
        exit 1
    fi
else
    if ! eval "$SSH_CMD -o ConnectTimeout=5 -o BatchMode=yes $SERVER_USER@$SERVER_HOST 'exit'" 2>/dev/null; then
        print_error "无法连接到服务器，请检查:"
        print_error "1. 服务器IP地址是否正确: $SERVER_HOST"
        print_error "2. SSH密钥是否已配置"
        print_error "3. 服务器是否允许SSH连接"
        exit 1
    fi
fi

print_info "SSH连接成功！"

# 创建部署目录并安装必要工具
print_info "创建部署目录并检查必要工具..."
eval "$SSH_CMD $SERVER_USER@$SERVER_HOST 'mkdir -p $DEPLOY_PATH && (command -v rsync >/dev/null 2>&1 || yum install -y rsync 2>/dev/null || apt-get install -y rsync 2>/dev/null || true)'"

# 上传项目文件（排除node_modules, .git等）
print_info "上传项目文件..."
if [ "$USE_PASSWORD" = true ] && [ "$USE_EXPECT" = false ]; then
    # 使用sshpass时，rsync需要特殊处理
    # 转义密码中的特殊字符
    ESCAPED_PASSWORD=$(printf '%q' "$SERVER_PASSWORD")
    rsync -avz --progress \
        -e "sshpass -p $ESCAPED_PASSWORD ssh $SSH_OPTIONS" \
        --exclude='/data/' \
        --exclude='node_modules' \
        --exclude='.git' \
        --exclude='.gitignore' \
        --exclude='dist' \
        --exclude='__pycache__' \
        --exclude='*.pyc' \
        --exclude='.env' \
        --exclude='.deploy.env' \
        --exclude='.vscode' \
        --exclude='.idea' \
        ./ "$SERVER_USER@$SERVER_HOST:$DEPLOY_PATH/"
elif [ "$USE_PASSWORD" = true ] && [ "$USE_EXPECT" = true ]; then
    # 使用expect时，需要创建一个expect包装脚本用于rsync
    # 在 bash 中构建完整的 SSH 命令字符串，确保引号正确
    SSH_CMD_STR="ssh $SSH_OPTIONS"
    
    # 创建临时expect脚本（使用 MSYS2 的 /tmp 目录）
    TEMP_EXPECT_SCRIPT=$(mktemp /tmp/deploy_rsync_XXXXXX.exp 2>/dev/null || echo "/tmp/deploy_rsync_$$.exp")
    cat > "$TEMP_EXPECT_SCRIPT" << EXPECT_EOF
set timeout 600
set password [lindex \$argv 0]
set ssh_cmd [lindex \$argv 1]
set server_user [lindex \$argv 2]
set server_host [lindex \$argv 3]
set deploy_path [lindex \$argv 4]

# 构建 rsync 命令
# 注意：在 Tcl 中，spawn 命令的参数解析可能有问题，所以我们需要确保 -e 选项后的整个 SSH 命令被当作一个参数
# 使用双引号包裹 \$ssh_cmd 以确保整个 SSH 命令字符串被当作一个整体
spawn rsync -avz -e "\$ssh_cmd" \
    --exclude=/data/ \
    --exclude=node_modules \
    --exclude=.git \
    --exclude=.gitignore \
    --exclude=dist \
    --exclude=__pycache__ \
    --exclude=*.pyc \
    --exclude=.env \
    --exclude=.deploy.env \
    --exclude=.vscode \
    --exclude=.idea \
    ./ \$server_user@\$server_host:\$deploy_path/

expect {
    -re "(?i)password:" {
        send "\$password\r"
        exp_continue
    }
    -re "yes/no" {
        send "yes\r"
        exp_continue
    }
    eof {
        catch wait result
        set exit_code [lindex \$result 3]
        exit \$exit_code
    }
    timeout {
        puts "rsync timeout after 600 seconds"
        exit 1
    }
}
EXPECT_EOF
    
    # 执行expect脚本，传递完整的 SSH 命令字符串
    expect "$TEMP_EXPECT_SCRIPT" "$SERVER_PASSWORD" "$SSH_CMD_STR" "$SERVER_USER" "$SERVER_HOST" "$DEPLOY_PATH"
    EXIT_CODE=$?
    rm -f "$TEMP_EXPECT_SCRIPT"
    
    if [ $EXIT_CODE -ne 0 ]; then
        print_error "rsync上传失败，退出码: $EXIT_CODE"
        exit 1
    fi
else
    # 使用密钥认证时，SSH选项必须通过-e参数传递给ssh
    rsync -avz --progress \
        -e "ssh $SSH_OPTIONS" \
        --exclude='/data/' \
        --exclude='node_modules' \
        --exclude='.git' \
        --exclude='.gitignore' \
        --exclude='dist' \
        --exclude='__pycache__' \
        --exclude='*.pyc' \
        --exclude='.env' \
        --exclude='.deploy.env' \
        --exclude='.vscode' \
        --exclude='.idea' \
        ./ "$SERVER_USER@$SERVER_HOST:$DEPLOY_PATH/"
fi

# 上传部署脚本
print_info "上传服务器端部署脚本..."
eval "$SCP_CMD server_deploy.sh $SERVER_USER@$SERVER_HOST:$DEPLOY_PATH/"

# 上传systemd服务文件（如果存在）
if [ -f "stock-scanner.service" ]; then
    print_info "上传systemd服务文件..."
    eval "$SCP_CMD stock-scanner.service $SERVER_USER@$SERVER_HOST:/tmp/"
fi

# 在服务器上执行部署脚本
print_info "在服务器上执行部署..."
eval "$SSH_CMD $SERVER_USER@$SERVER_HOST 'cd $DEPLOY_PATH && chmod +x server_deploy.sh && bash server_deploy.sh'"

print_info "部署完成！"
print_info "前端访问地址: http://$SERVER_HOST:${FRONTEND_PORT:-80}"
print_info "后端API地址: http://$SERVER_HOST:${BACKEND_PORT:-8001}"

