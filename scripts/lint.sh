#!/bin/bash

# Pylint 验证脚本
# 用于检查代码质量，显示所有的 pylint 问题

# 获取脚本所在目录的父目录（项目根目录）
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# 切换到项目根目录
cd "$PROJECT_ROOT"

# 使用 poetry 运行 pylint
poetry run pylint epub_generator/ \
  --rcfile=.pylintrc \
  --output-format=colorized \
  --reports=no

exit_code=$?

if [ $exit_code -eq 0 ]; then
  echo "✅ All checks passed!"
fi

exit $exit_code
