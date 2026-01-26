#!/bin/bash

# anything-to-notebooklm Skill Installer
# 自动安装所有依赖并配置环境

set -e  # 遇到错误立即退出

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_NAME="anything-to-notebooklm"
VENV_DIR="$SKILL_DIR/.venv"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  多源内容 → NotebookLM 安装程序${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 1. 检查 Python 版本
echo -e "${YELLOW}[1/6] 检查 Python 环境...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ 未找到 Python3，请先安装 Python 3.9+${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.9"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo -e "${RED}❌ Python 版本过低（当前 $PYTHON_VERSION，需要 3.9+）${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Python $PYTHON_VERSION${NC}"

# 2. 创建虚拟环境
echo ""
echo -e "${YELLOW}[2/7] 创建虚拟环境...${NC}"
if [ -d "$VENV_DIR" ]; then
    echo -e "${GREEN}✅ 虚拟环境已存在${NC}"
else
    python3 -m venv "$VENV_DIR"
    echo -e "${GREEN}✅ 虚拟环境创建完成${NC}"
fi

source "$VENV_DIR/bin/activate"
pip install --upgrade pip -q
echo -e "${GREEN}✅ 虚拟环境已激活${NC}"

# 3. 检查并克隆 wexin-read-mcp
echo ""
echo -e "${YELLOW}[3/7] 安装 MCP 服务器...${NC}"
MCP_DIR="$SKILL_DIR/wexin-read-mcp"

if [ -d "$MCP_DIR" ]; then
    echo -e "${GREEN}✅ MCP 服务器已存在${NC}"
else
    echo "正在克隆 wexin-read-mcp..."
    git clone https://github.com/Bwkyd/wexin-read-mcp.git "$MCP_DIR"
    echo -e "${GREEN}✅ MCP 服务器克隆完成${NC}"
fi

# 4. 安装 Python 依赖
echo ""
echo -e "${YELLOW}[4/7] 安装 Python 依赖...${NC}"

# 安装 MCP 服务器依赖
if [ -f "$MCP_DIR/requirements.txt" ]; then
    echo "安装 MCP 依赖..."
    pip install -r "$MCP_DIR/requirements.txt" -q
    echo -e "${GREEN}✅ MCP 依赖安装完成${NC}"
fi

# 安装 Skill 依赖（包括 markitdown）
if [ -f "$SKILL_DIR/requirements.txt" ]; then
    echo "安装 Skill 依赖（包括 markitdown 文件转换工具）..."
    pip install -r "$SKILL_DIR/requirements.txt" -q
    echo -e "${GREEN}✅ Skill 依赖安装完成${NC}"
    echo -e "${GREEN}✅ markitdown 已安装（支持 15+ 文件格式转换）${NC}"
fi

# 5. 安装 Playwright 浏览器
echo ""
echo -e "${YELLOW}[5/7] 安装 Playwright 浏览器...${NC}"
echo "这可能需要几分钟，请耐心等待..."

if python3 -c "from playwright.sync_api import sync_playwright" 2>/dev/null; then
    playwright install chromium
    echo -e "${GREEN}✅ Playwright 浏览器安装完成${NC}"
else
    echo -e "${RED}❌ Playwright 导入失败，请检查安装${NC}"
    exit 1
fi

# 6. 检查并安装 notebooklm
echo ""
echo -e "${YELLOW}[6/7] 检查 NotebookLM CLI...${NC}"

if command -v notebooklm &> /dev/null; then
    NOTEBOOKLM_VERSION=$(notebooklm --version 2>/dev/null || echo "unknown")
    echo -e "${GREEN}✅ NotebookLM CLI 已安装 ($NOTEBOOKLM_VERSION)${NC}"
else
    echo "正在安装 notebooklm-py..."
    pip install git+https://github.com/teng-lin/notebooklm-py.git -q

    if command -v notebooklm &> /dev/null; then
        echo -e "${GREEN}✅ NotebookLM CLI 安装完成${NC}"
    else
        echo -e "${RED}❌ NotebookLM CLI 安装失败${NC}"
        echo "请手动安装：pip install git+https://github.com/teng-lin/notebooklm-py.git"
        exit 1
    fi
fi

# 7. 配置指导
echo ""
echo -e "${YELLOW}[7/7] 配置指导${NC}"
echo ""

CLAUDE_CONFIG="$HOME/.claude/config.json"
CONFIG_SNIPPET="    \"weixin-reader\": {
      \"command\": \"$VENV_DIR/bin/python\",
      \"args\": [
        \"$MCP_DIR/src/server.py\"
      ]
    }"

echo -e "${BLUE}📝 下一步：配置 MCP 服务器${NC}"
echo ""
echo "请编辑 $CLAUDE_CONFIG"
echo ""
echo "在 \"mcpServers\" 中添加："
echo -e "${GREEN}$CONFIG_SNIPPET${NC}"
echo ""
echo "完整配置示例："
echo -e "${GREEN}{
  \"primaryApiKey\": \"any\",
  \"mcpServers\": {
$CONFIG_SNIPPET
  }
}${NC}"
echo ""

# 检查是否已配置
if [ -f "$CLAUDE_CONFIG" ]; then
    if grep -q "weixin-reader" "$CLAUDE_CONFIG"; then
        echo -e "${GREEN}✅ 检测到已有 weixin-reader 配置${NC}"
    else
        echo -e "${YELLOW}⚠️  未检测到 weixin-reader 配置，请手动添加${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  未找到 Claude 配置文件，请手动创建${NC}"
fi

echo ""
echo -e "${BLUE}🔐 NotebookLM 认证${NC}"
echo ""
echo "首次使用前，请运行："
echo -e "${GREEN}  $VENV_DIR/bin/notebooklm login${NC}"
echo -e "${GREEN}  $VENV_DIR/bin/notebooklm list  # 验证认证成功${NC}"
echo ""

# 最终检查
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✅ 安装完成！${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "📦 安装位置：$SKILL_DIR"
echo ""
echo "⚠️  重要提醒："
echo "  1. 配置 MCP 服务器后需要重启 Claude Code"
echo "  2. 首次使用前运行 notebooklm login"
echo ""
echo "🚀 使用示例："
echo "  把这篇文章生成播客 https://mp.weixin.qq.com/s/xxx"
echo ""
