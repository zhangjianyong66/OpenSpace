# Mem0 本地部署与 MCP 服务器配置指南

## 概述

Mem0 提供两种部署方式：
1. **Mem0 Platform（云端托管）** - 使用 Mem0 提供的云 MCP 服务器
2. **Mem0 Open Source（本地自托管）** - 在自己的基础设施上部署

本指南将详细介绍两种方式的 MCP 配置方法。

---

## 一、本地 MCP 服务器的安装和配置

### 方式一：使用 Mem0 云托管 MCP 服务器（推荐）

Mem0 提供了一个云托管的 MCP 服务器，无需本地安装，这是最简单的方式。

#### 1.1 前提条件
- Mem0 Platform 账户（需要在 https://app.mem0.ai 注册）
- API Key（从 https://app.mem0.ai/settings/api-keys 获取）
- Node.js 14+（用于运行 npx 命令）
- 支持 MCP 的客户端（Claude、Claude Code、Cursor、Windsurf、VS Code、OpenCode）

#### 1.2 快速配置命令

使用 `mcp-add` 工具一键配置所有支持的客户端：

```bash
npx mcp-add \
  --name mem0-mcp \
  --type http \
  --url "https://mcp.mem0.ai/mcp" \
  --clients "claude,claude code,cursor,windsurf,vscode,opencode"
```

#### 1.3 MCP 服务器提供的工具

| 工具 | 描述 |
|------|------|
| `add_memory` | 保存文本或对话历史 |
| `search_memories` | 语义搜索已有记忆 |
| `get_memories` | 列出记忆（支持过滤和分页） |
| `get_memory` | 通过 memory_id 获取单个记忆 |
| `update_memory` | 更新记忆内容 |
| `delete_memory` | 删除单个记忆 |
| `delete_all_memories` | 批量删除所有记忆 |
| `delete_entities` | 删除用户/代理/应用实体及其记忆 |
| `list_entities` | 枚举存储的用户/代理/应用/运行 |

---

### 方式二：完全本地部署（Mem0 OSS + 自建 MCP 服务器）

如果你需要完全离线的本地部署，需要：

#### 2.1 部署 Mem0 OSS REST API 服务器

**使用 Docker Compose（推荐）**

1. 克隆仓库并创建环境文件：
```bash
git clone https://github.com/mem0ai/mem0.git
cd mem0/server
```

2. 创建 `.env` 文件：
```bash
OPENAI_API_KEY=your-openai-api-key
# 可选：启用 API Key 认证
ADMIN_API_KEY=your-secret-api-key
```

3. 启动服务：
```bash
docker compose up
```

4. 访问 API：`http://localhost:8888`

**使用 Docker 直接运行**
```bash
# 拉取镜像
docker pull mem0/mem0-api-server

# 运行容器
docker run -p 8000:8000 --env-file .env mem0/mem0-api-server
```

**直接运行（无 Docker）**
```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

#### 2.2 配置本地组件

Mem0 OSS 支持自定义配置，包括 LLM、向量数据库、嵌入模型和重排序器：

**Python 配置示例：**
```python
from mem0 import Memory

config = {
    "vector_store": {
        "provider": "qdrant",
        "config": {"host": "localhost", "port": 6333},
    },
    "llm": {
        "provider": "openai",
        "config": {"model": "gpt-4.1-mini", "temperature": 0.1},
    },
    "embedder": {
        "provider": "ollama",  # 使用本地嵌入模型
        "config": {"model": "nomic-embed-text"},
    },
}

memory = Memory.from_config(config)
```

**支持的组件：**
- **LLM**: OpenAI, Anthropic, Azure OpenAI, Ollama, Together, Groq, LiteLLM, Mistral AI, Google AI, AWS Bedrock, DeepSeek, MiniMax, xAI, Sarvam, LM Studio, LangChain, vLLM
- **向量数据库**: Qdrant, Chroma, pgvector, Milvus, Pinecone, MongoDB, Azure, Redis, Valkey, Elasticsearch, OpenSearch, Supabase, Weaviate, FAISS 等
- **嵌入模型**: OpenAI, Azure OpenAI, Ollama, HuggingFace, Vertex AI, Google AI, LM Studio, Together, AWS Bedrock

---

## 二、与 Claude/Cursor 等客户端的本地集成方式

### 2.1 Claude Desktop 配置

**方式一：使用 mcp-add 工具**
```bash
npx mcp-add \
  --name mem0-mcp \
  --type http \
  --url "https://mcp.mem0.ai/mcp" \
  --clients "claude"
```

**方式二：手动配置**
编辑 `claude_desktop_config.json`：
```json
{
  "mcpServers": {
    "mem0-mcp": {
      "type": "http",
      "url": "https://mcp.mem0.ai/mcp"
    }
  }
}
```

### 2.2 Claude Code 配置

```bash
npx mcp-add \
  --name mem0-mcp \
  --type http \
  --url "https://mcp.mem0.ai/mcp" \
  --clients "claude code"
```

### 2.3 Cursor 配置

**方式一：使用 mcp-add 工具**
```bash
npx mcp-add \
  --name mem0-mcp \
  --type http \
  --url "https://mcp.mem0.ai/mcp" \
  --clients "cursor"
```

**方式二：手动配置**
1. 打开 Cursor → Settings → MCP
2. 添加配置：
```json
{
  "mcpServers": {
    "mem0-mcp": {
      "type": "http",
      "url": "https://mcp.mem0.ai/mcp"
    }
  }
}
```

### 2.4 其他客户端配置

**Windsurf:**
```bash
npx mcp-add \
  --name mem0-mcp \
  --type http \
  --url "https://mcp.mem0.ai/mcp" \
  --clients "windsurf"
```

**VS Code:**
```bash
npx mcp-add \
  --name mem0-mcp \
  --type http \
  --url "https://mcp.mem0.ai/mcp" \
  --clients "vscode"
```

**OpenCode:**
```bash
npx mcp-add \
  --name mem0-mcp \
  --type http \
  --url "https://mcp.mem0.ai/mcp" \
  --clients "opencode"
```

---

## 三、是否需要 mem0-platform 账户

### 3.1 使用云托管 MCP 服务器（需要 Platform 账户）

**✅ 需要 Mem0 Platform 账户**

如果你使用 Mem0 提供的云托管 MCP 服务器（`https://mcp.mem0.ai/mcp`），则必须：
1. 在 https://app.mem0.ai 注册账户
2. 从 https://app.mem0.ai/settings/api-keys 获取 API Key
3. 将 API Key 配置到客户端环境变量中

**优点：**
- 无需本地安装和维护
- 自动扩展和高可用性
- 内置分析和仪表板
- 支持 Webhooks、记忆导出等高级功能

**缺点：**
- 需要互联网连接
- 数据存储在 Mem0 云端
- 基于使用量的定价

### 3.2 完全本地部署（不需要 Platform 账户）

**❌ 不需要 Mem0 Platform 账户**

如果你选择完全本地部署 Mem0 OSS：
1. 克隆 GitHub 仓库：https://github.com/mem0ai/mem0
2. 使用自己的 LLM API Key（OpenAI、Anthropic 等）
3. 自托管向量数据库（Qdrant、Chroma 等）

**优点：**
- 完全数据控制和隐私
- 离线运行能力
- Apache 2.0 开源许可（免费）
- 可自定义组件和扩展

**缺点：**
- 需要自己维护基础设施
- 需要手动配置和调优
- 无内置仪表板和分析
- 无 Webhooks 和记忆导出功能

---

## 四、功能对比

| 功能 | Platform (云 MCP) | OSS (本地部署) |
|------|------------------|----------------|
| 需要 Platform 账户 | ✅ 是 | ❌ 否 |
| MCP 服务器位置 | 云端托管 | 需要自建 |
| 安装复杂度 | 简单（5分钟） | 中等（15-30分钟）|
| 数据控制 | Mem0 托管 | 完全自主 |
| 离线运行 | ❌ 否 | ✅ 是 |
| 自动扩展 | ✅ 是 | 手动配置 |
| Webhooks | ✅ 是 | ❌ 否 |
| 记忆导出 | ✅ 是 | ❌ 否 |
| 仪表板 | ✅ 是 | ❌ 否 |
| 自定义 LLM | 有限 | 完全支持 |
| 自定义向量数据库 | 托管 | 20+ 选项 |

---

## 五、决策建议

### 选择云托管 MCP（需要 Platform 账户）如果你：
- 希望快速启动（5分钟内）
- 不想维护基础设施
- 需要生产级的高可用性和自动扩展
- 需要 Webhooks、记忆导出等高级功能
- 数据可以存储在云端

### 选择完全本地部署（不需要 Platform 账户）如果你：
- 需要完全的数据控制和隐私
- 需要在离线环境运行
- 希望使用自定义的 LLM 和向量数据库
- 想要修改和扩展代码
- 对成本敏感，希望使用本地模型（如 Ollama）

---

## 六、参考资源

- **Mem0 Platform**: https://app.mem0.ai
- **GitHub 仓库**: https://github.com/mem0ai/mem0
- **MCP 规范**: https://modelcontextprotocol.io
- **Python Quickstart**: https://docs.mem0.ai/open-source/python-quickstart
- **REST API 文档**: https://docs.mem0.ai/open-source/features/rest-api
- **Platform vs OSS 对比**: https://docs.mem0.ai/platform/platform-vs-oss
