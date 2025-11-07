#!/bin/bash

# Pylint 自动修复脚本
# 使用 autopep8 和 isort 自动修复常见的代码风格问题

# 获取脚本所在目录的父目录（项目根目录）
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# 切换到项目根目录
cd "$PROJECT_ROOT"

echo "🔧 Running code auto-fix..."
echo ""

echo "📦 1/2 使用 isort 整理导入..."
poetry run isort epub_generator/ --profile black --line-length 120

echo ""
echo "📝 2/2 使用 autopep8 修复代码风格..."
poetry run autopep8 --in-place --recursive --aggressive --aggressive \
  --max-line-length 120 \
  epub_generator/

echo ""
echo "✅ 自动修复完成！"
echo ""
echo "接下来："
echo "  1. 运行 'bash scripts/lint.sh' 验证修复结果"
echo "  2. 检查 git diff 查看所有更改"
echo "  3. 手动修复剩余的 pylint 问题（如果有）"
