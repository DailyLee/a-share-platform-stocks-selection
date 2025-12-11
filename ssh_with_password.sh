#!/bin/bash
# SSH密码认证辅助脚本
# 使用expect实现非交互式SSH密码认证

if [ $# -lt 3 ]; then
    echo "Usage: $0 <password> <ssh_command> <host> [args...]"
    exit 1
fi

PASSWORD="$1"
shift
SSH_CMD="$1"
shift
HOST="$1"
shift

# 检查expect是否安装
if ! command -v expect &> /dev/null; then
    echo "Error: expect is not installed. Installing..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command -v brew &> /dev/null; then
            brew install expect
        else
            echo "Please install Homebrew first: https://brew.sh"
            exit 1
        fi
    else
        # Linux
        if command -v apt-get &> /dev/null; then
            sudo apt-get install -y expect
        elif command -v yum &> /dev/null; then
            sudo yum install -y expect
        else
            echo "Please install expect manually"
            exit 1
        fi
    fi
fi

# 使用expect执行SSH命令
expect << EOF
set timeout 30
spawn $SSH_CMD $HOST $@
expect {
    "password:" {
        send "$PASSWORD\r"
        exp_continue
    }
    "Password:" {
        send "$PASSWORD\r"
        exp_continue
    }
    "yes/no" {
        send "yes\r"
        exp_continue
    }
    eof
}
catch wait result
exit [lindex \$result 3]
EOF
