#!/bin/bash

# 打包 qiaomu-anything-to-notebooklm skill 用于分享
# 生成一个不包含大文件的精简版 tar.gz
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_NAME="qiaomu-anything-to-notebooklm"
OUTPUT_DIR="${1:-$HOME/Desktop}"
mkdir -p "$OUTPUT_DIR"
OUTPUT_DIR="$(cd "$OUTPUT_DIR" && pwd)"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_FILE="$OUTPUT_DIR/${SKILL_NAME}_${TIMESTAMP}.tar.gz"

# 颜色
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  打包 ${SKILL_NAME} Skill${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 要打包的文件列表
FILES=(
    "SKILL.md"
    "README.md"
    "install.sh"
    "install.cmd"
    "install.py"
    "run.cmd"
    "windows_entry.py"
    "runtime_compat.py"
    "main.py"
    "check_env.py"
    "requirements.txt"
    ".gitignore"
    "LICENSE"
    "package.sh"
    "scripts/fetch_url.sh"
    "scripts/get_podcast_transcript.py"
    "tests/test_windows_compat.py"
    "tests/test_package.py"
    "tests/smoke_installed.py"
)

# 创建临时目录
TEMP_DIR=$(mktemp -d)
trap 'rm -rf "$TEMP_DIR"' EXIT
TEMP_SKILL="$TEMP_DIR/$SKILL_NAME"
mkdir -p "$TEMP_SKILL"

echo "📦 正在打包文件..."

# 复制文件
for file in "${FILES[@]}"; do
    mkdir -p "$TEMP_SKILL/$(dirname "$file")"
    cp "$SKILL_DIR/$file" "$TEMP_SKILL/$file"
    echo "  ✓ $file"
done

# 创建 tar.gz
cd "$TEMP_DIR"
tar -czf "$OUTPUT_FILE" "$SKILL_NAME"

# 显示结果
FILE_SIZE=$(du -h "$OUTPUT_FILE" | cut -f1)

echo ""
echo -e "${GREEN}✅ 打包完成！${NC}"
echo ""
echo "📦 文件：$OUTPUT_FILE"
echo "📊 大小：$FILE_SIZE"
echo ""
echo "📤 分享说明："
echo "  用户收到文件后，执行："
echo "    cd ~/.claude/skills/"
echo "    tar -xzf ${SKILL_NAME}_${TIMESTAMP}.tar.gz"
echo "    cd ${SKILL_NAME}"
echo "    ./install.sh"
echo ""
echo "💡 注意：wexin-read-mcp 会在安装时自动克隆，无需打包"
echo ""
