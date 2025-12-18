#!/bin/bash
# 测试 rsync 排除规则是否生效
# 这个脚本可以帮助验证 data/ 目录是否被正确排除

echo "测试 rsync 排除规则..."
echo ""

# 创建测试目录结构
mkdir -p test_deploy/data
touch test_deploy/data/stocks.db
touch test_deploy/data/test.txt
mkdir -p test_deploy/other
touch test_deploy/other/file.txt

echo "测试目录结构："
tree test_deploy 2>/dev/null || find test_deploy -type f

echo ""
echo "执行 rsync 测试（dry-run，不实际上传）..."
echo "排除规则: --exclude 'data/' --exclude 'data/*'"
echo ""

rsync -avz --dry-run \
    --exclude 'data/' \
    --exclude 'data/*' \
    --exclude 'node_modules' \
    --exclude '.git' \
    test_deploy/ test_deploy_dest/ 2>&1 | grep -E "data/|stocks.db|test.txt|file.txt" || echo "未发现 data/ 相关文件（排除规则生效）"

echo ""
echo "清理测试目录..."
rm -rf test_deploy test_deploy_dest

echo "测试完成！"

