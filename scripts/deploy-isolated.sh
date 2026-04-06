#!/bin/bash
#
# OpenSpace 独立目录部署脚本
# 将 OpenSpace 数据文件与代码仓库隔离
#

set -e

# 默认数据目录
DEFAULT_DATA_DIR="$HOME/.openspace-data"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 帮助信息
usage() {
    cat << EOF
Usage: $0 [OPTIONS]

OpenSpace 独立目录部署脚本
将 OpenSpace 生成的文件（日志、录制数据、工作空间）与代码仓库隔离

OPTIONS:
    -d, --data-dir DIR      指定数据目录 (默认: ~/.openspace-data)
    -c, --cursor-proxy      同时配置 Cursor API Proxy
    -h, --help              显示帮助信息

EXAMPLES:
    $0                      # 使用默认配置部署
    $0 -d /path/to/data     # 指定自定义数据目录
    $0 -c                   # 部署并配置 Cursor API Proxy

EOF
}

# 解析参数
DATA_DIR="$DEFAULT_DATA_DIR"
SETUP_CURSOR=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--data-dir)
            DATA_DIR="$2"
            shift 2
            ;;
        -c|--cursor-proxy)
            SETUP_CURSOR=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            print_error "未知参数: $1"
            usage
            exit 1
            ;;
    esac
done

print_info "开始部署 OpenSpace 独立目录..."
print_info "数据目录: $DATA_DIR"

# 创建目录结构
print_info "创建目录结构..."
mkdir -p "$DATA_DIR"/{logs,recordings,workspace,cache,reports}
print_success "目录结构创建完成"

# 生成环境变量配置文件
ENV_FILE="$HOME/.openspace-env"
print_info "生成环境变量配置: $ENV_FILE"

cat > "$ENV_FILE" << EOF
# ============================================
# OpenSpace 独立目录配置
# 生成时间: $(date "+%Y-%m-%d %H:%M:%S")
# ============================================

# 数据目录 - 所有生成文件将保存在此目录下
export OPENSPACE_DATA_DIR="$DATA_DIR"

# 工作目录
export OPENSPACE_WORKSPACE="$DATA_DIR/workspace"

# 可选：Cursor API Proxy 配置
EOF

# 如果设置了 Cursor Proxy，添加配置
if [[ "$SETUP_CURSOR" == true ]]; then
    cat >> "$ENV_FILE" << 'EOF'

# Cursor API Proxy 配置
export OPENSPACE_LLM_API_BASE="http://localhost:4646/v1"
export OPENSPACE_LLM_API_KEY="cursor"

EOF
    print_success "Cursor API Proxy 配置已添加"
fi

# 添加使用说明
cat >> "$ENV_FILE" << EOF

# ============================================
# 使用方法
# ============================================
# 
# 方式 1: 加载环境变量后使用
#   source $ENV_FILE
#   openspace --query "你的任务"
#
# 方式 2: 添加到 ~/.zshrc 或 ~/.bashrc 永久生效
#   echo "source $ENV_FILE" >> ~/.zshrc
#
# 方式 3: 创建别名
#   alias openspace-isolated='source $ENV_FILE && openspace'

EOF

print_success "环境变量配置已生成"

# 生成配置文件
CONFIG_FILE="$DATA_DIR/openspace-config.json"
print_info "生成配置文件: $CONFIG_FILE"

cat > "$CONFIG_FILE" << EOF
{
  "llm_model": "openai/auto",
  "data_dir": "$DATA_DIR",
  "workspace_dir": "$DATA_DIR/workspace",
  "recording_log_dir": "$DATA_DIR/recordings",
  "llm_timeout": 120.0,
  "llm_max_retries": 3,
  "grounding_max_iterations": 30,
  "log_level": "INFO"
}
EOF

print_success "配置文件已生成"

# 生成便捷启动脚本
LAUNCHER="$DATA_DIR/openspace-launcher.sh"
print_info "生成启动脚本: $LAUNCHER"

cat > "$LAUNCHER" << 'EOF'
#!/bin/bash
# OpenSpace 隔离环境启动脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 加载环境变量
export OPENSPACE_DATA_DIR="$SCRIPT_DIR"
export OPENSPACE_WORKSPACE="$SCRIPT_DIR/workspace"

# 检查虚拟环境
if [[ -f "$SCRIPT_DIR/../OpenSpace/venv/bin/activate" ]]; then
    source "$SCRIPT_DIR/../OpenSpace/venv/bin/activate"
elif [[ -f "$SCRIPT_DIR/../OpenSpace/.venv/bin/activate" ]]; then
    source "$SCRIPT_DIR/../OpenSpace/.venv/bin/activate"
fi

# 启动 OpenSpace
exec openspace "$@"
EOF

chmod +x "$LAUNCHER"
print_success "启动脚本已生成"

# 输出总结
echo ""
echo "=========================================="
echo "  OpenSpace 独立目录部署完成!"
echo "=========================================="
echo ""
echo "数据目录结构:"
tree -L 1 "$DATA_DIR" 2>/dev/null || ls -la "$DATA_DIR"
echo ""
echo "使用方法:"
echo ""
echo "1. 临时使用 (当前终端):"
echo "   source $ENV_FILE"
echo "   openspace --query \"你的任务\""
echo ""
echo "2. 永久配置 (添加到 shell 配置):"
echo "   echo \"source $ENV_FILE\" >> ~/.zshrc"
echo "   source ~/.zshrc"
echo ""
echo "3. 使用配置文件启动:"
echo "   openspace --config $CONFIG_FILE --query \"你的任务\""
echo ""
echo "4. 使用启动脚本:"
echo "   $LAUNCHER --query \"你的任务\""
echo ""
echo "生成的文件:"
echo "   环境配置: $ENV_FILE"
echo "   配置文件: $CONFIG_FILE"
echo "   启动脚本: $LAUNCHER"
echo ""

if [[ "$SETUP_CURSOR" == true ]]; then
    echo "Cursor API Proxy 已配置:"
    echo "   API Base: http://localhost:4646/v1"
    echo "   模型: openai/auto"
    echo ""
fi

print_success "部署完成!"
