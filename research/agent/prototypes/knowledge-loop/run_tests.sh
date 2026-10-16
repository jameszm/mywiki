#!/usr/bin/env bash
# 运行全部单元测试 (仅标准库)。
set -euo pipefail
cd "$(dirname "$0")"
python3 -m unittest discover -s tests -v
