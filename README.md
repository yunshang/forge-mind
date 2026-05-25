# 🧠 ForgeMind

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Next.js 16](https://img.shields.io/badge/next.js-16-black.svg)](https://nextjs.org/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)

**AI Agent 驱动的智能合约协作开发平台**

ForgeMind 将自然语言描述转化为 Solidity 智能合约，通过 AI Agent 自动完成代码生成、安全审计、拓扑可视化和沙盒部署。支持实时编辑代码并动态更新合约拓扑图。

## ✨ 功能特性

| 功能 | 说明 |
|------|------|
| 🤖 **AI 代码生成** | 自然语言描述 → Solidity 智能合约，支持多次迭代优化 |
| 🔍 **安全审计** | 基于正则的静态分析，检测重入攻击、未检查算术、缺少访问控制等漏洞 |
| 🔄 **自愈循环** | 审计失败自动反馈给 AI，最多 3 轮自我修复 |
| 📊 **拓扑可视化** | 实时解析合约结构，生成函数、状态变量、继承关系图 |
| ✏️ **实时编辑** | 代码编辑后自动更新拓扑图，支持即时预览 |
| 🎮 **沙盒测试** | 自动编译部署到 Anvil，提供交互式函数调用界面 |
| 💬 **会话管理** | 支持多会话，保留历史上下文持续迭代 |

## 🏗️ 架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            ForgeMind Architecture                           │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────┐    ┌─────────────────────────────────────────────────────────┐
│   用户输入   │───▶│                    Orchestrator                         │
└─────────────┘    │  ┌─────────────────────────────────────────────────────┐ │
                   │  │              Self-Healing Loop (max 3x)             │ │
                   │  │                                                     │ │
                   │  │  ┌──────────────┐        ┌──────────────────────┐  │ │
                   │  │  │ Coder Agent  │───────▶│   Reviewer Agent     │  │ │
                   │  │  │   (LLM)      │        │   (Security Audit)   │  │ │
                   │  │  └──────────────┘◀───────┴──────────────────────┘  │ │
                   │  │         │                     │                     │ │
                   │  │         │ if FAIL ◀───────────┘                     │ │
                   │  └─────────┼───────────────────────────────────────────┘ │
                   │            │ if PASS                                     │
                   └────────────┼─────────────────────────────────────────────┘
                                │
            ┌───────────────────┼───────────────────┐
            ▼                   ▼                   ▼
    ┌───────────────┐   ┌───────────────┐   ┌───────────────┐
    │ AST Visual    │   │   Sandbox     │   │  Real-time    │
    │ Skill         │   │   Skill       │   │  Editor       │
    │               │   │               │   │               │
    │ • 解析合约结构 │   │ • solc 编译   │   │ • 代码编辑    │
    │ • 生成拓扑图  │   │ • Anvil 部署  │   │ • 实时更新    │
    │ • React Flow  │   │ • ABI 调用    │   │ • 500ms 防抖  │
    └───────────────┘   └───────────────┘   └───────────────┘
```

## 🛠️ 技术栈

### 后端

| 技术 | 用途 | 版本 |
|------|------|------|
| [Python](https://www.python.org/) | 编程语言 | 3.12+ |
| [Litestar](https://litestar.dev/) | Web 框架 | 2.x |
| [Anthropic SDK](https://github.com/anthropics/anthropic-sdk-python) | LLM 集成 | Latest |
| [Web3.py](https://web3py.readthedocs.io/) | 以太坊交互 | 6.x |
| [Pydantic](https://docs.pydantic.dev/) | 数据验证 | 2.x |

### 前端

| 技术 | 用途 | 版本 |
|------|------|------|
| [Next.js](https://nextjs.org/) | React 框架 | 16.x |
| [React](https://react.dev/) | UI 库 | 19.x |
| [TailwindCSS](https://tailwindcss.com/) | CSS 框架 | 4.x |
| [React Flow](https://reactflow.dev/) | 图可视化 | 12.x |

### 基础设施

| 技术 | 用途 |
|------|------|
| [Docker Compose](https://docs.docker.com/compose/) | 容器编排 |
| [Foundry (Anvil)](https://book.getfoundry.sh/anvil/) | 本地以太坊节点 |

## 🚀 快速开始

### 环境要求

- Node.js 18+
- Python 3.12+
- Docker & Docker Compose (可选)
- [uv](https://github.com/astral-sh/uv) (Python 包管理器)

### 1. 克隆仓库

```bash
git clone https://github.com/your-username/forge-mind.git
cd forge-mind
```

### 2. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件，配置以下变量：

```env
# LLM 配置
FORGE_ANTHROPIC_API_KEY=your_api_key_here
FORGE_ANTHROPIC_BASE_URL=https://api.anthropic.com
FORGE_ANTHROPIC_MODEL=claude-sonnet-4-20250514

# Anvil 配置
FORGE_ANVIL_URL=http://localhost:8545
```

### 3. 启动服务

#### 方式一：Docker Compose (推荐)

```bash
# 启动 Anvil + 后端
docker compose up -d

# 启动前端
cd frontend && npm run dev
```

#### 方式二：本地开发

```bash
# 终端 1: 启动 Anvil
anvil

# 终端 2: 安装依赖并启动后端
uv sync
uv run uvicorn backend.main:app --reload

# 细端 3: 安装依赖并启动前端
cd frontend
npm install
npm run dev
```

### 4. 访问应用

打开浏览器访问 [http://localhost:3000](http://localhost:3000)

## 📖 使用指南

### 基本使用

1. **创建会话** - 在左侧面板点击"新建会话"
2. **输入需求** - 用自然语言描述你要的智能合约
   ```
   创建一个 ERC20 代币合约，包含：
   - 总供应量 100 万枚
   - 支持转账和授权
   - 添加转账事件
   ```
3. **等待生成** - AI 自动生成代码并执行安全审计
4. **查看结果** - 代码、拓扑图、审计报告同时展示

### 实时编辑

1. 在代码标签页点击 **"编辑代码"** 按钮
2. 修改 Solidity 代码
3. 拓扑图会在 500ms 后自动更新
4. 点击 **"编辑中"** 退出编辑模式

### 沙盒测试

1. 生成合约后，右侧面板显示已部署的合约地址
2. 点击函数名，输入参数
3. 点击"执行"查看调用结果

## 📁 项目结构

```
forge-mind/
├── backend/                    # 后端服务
│   ├── agents/                 # AI Agent 实现
│   │   ├── coder.py           # 代码生成 Agent
│   │   ├── reviewer.py        # 代码审查 Agent
│   │   └── orchestrator.py    # 编排器
│   ├── routes/                 # API 路由
│   │   ├── contracts.py       # 合约生成
│   │   ├── sessions.py        # 会话管理
│   │   ├── sandbox.py         # 沙盒交互
│   │   └── visual.py          # 拓扑可视化
│   ├── skills/                 # 技能模块
│   │   ├── base.py            # 基础技能类
│   │   ├── solidity_generation.py  # Solidity 生成
│   │   ├── security_audit.py  # 安全审计
│   │   ├── ast_visual.py      # AST 可视化
│   │   └── sandbox_simulation.py  # 沙盒模拟
│   ├── store.py                # 会话存储
│   ├── models/                 # 数据模型
│   └── config.py               # 配置管理
├── frontend/                   # 前端应用
│   ├── src/
│   │   ├── app/               # Next.js 页面
│   │   ├── components/        # React 组件
│   │   │   ├── ChatPanel.tsx  # 聊天面板
│   │   │   ├── CodeViewer.tsx # 代码查看器
│   │   │   ├── CodeEditor.tsx # 代码编辑器
│   │   │   ├── FlowCanvas.tsx # 拓扑画布
│   │   │   ├── TerminalLog.tsx # 终端日志
│   │   │   └── SandboxPlayground.tsx  # 沙盒游乐场
│   │   ├── hooks/             # React Hooks
│   │   │   └── useAgent.ts    # Agent 状态管理
│   │   └── lib/               # 工具库
│   │       ├── api.ts         # API 客户端
│   │       └── exportUtils.ts # 导出工具
│   └── public/                # 静态资源
├── tests/                      # 测试
├── docker-compose.yml          # Docker 编排
└── .env.example                # 环境变量示例
```

## 🔌 API 文档

### 合约生成

```http
POST /api/contracts/generate
Content-Type: application/json

{
  "prompt": "Create an ERC20 token with supply of 1 million"
}
```

### 拓扑可视化

```http
POST /api/contracts/visualize
Content-Type: application/json

{
  "solidity_code": "pragma solidity ^0.8.0; contract MyToken { ... }",
  "contract_name": "MyToken"
}
```

### 会话管理

```http
# 创建会话
POST /api/sessions

# 获取会话列表
GET /api/sessions

# 获取单个会话
GET /api/sessions/{session_id}

# 删除会话
DELETE /api/sessions/{session_id}

# 在会话中生成
POST /api/sessions/{session_id}/generate
```

### 沙盒调用

```http
POST /api/sandbox/call
Content-Type: application/json

{
  "contract_address": "0x...",
  "abi": [...],
  "function_name": "transfer",
  "args": ["0x...", 1000],
  "is_read": false
}
```

完整 API 文档访问：[http://localhost:8000/schema](http://localhost:8000/schema)

## 🧪 测试

### 运行后端测试

```bash
# 运行所有测试
uv run pytest tests/ -v

# 运行单个测试文件
uv run pytest tests/test_security_audit.py -v

# 运行单个测试
uv run pytest tests/test_orchestrator.py::TestOrchestrator::test_healing_loop_fixes_vulnerabilities -v
```

### 代码检查

```bash
# 后端 lint
uv run ruff check backend/

# 前端 lint
cd frontend && npm run lint

# 前端类型检查
cd frontend && npx tsc --noEmit
```

## 🤝 贡献指南

欢迎贡献代码！请遵循以下步骤：

1. **Fork 仓库** - 点击右上角 Fork 按钮
2. **创建分支** - `git checkout -b feature/amazing-feature`
3. **提交更改** - `git commit -m 'feat: 添加新功能'`
4. **推送分支** - `git push origin feature/amazing-feature`
5. **创建 PR** - 在 GitHub 上创建 Pull Request

### 提交规范

遵循 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

- `feat:` 新功能
- `fix:` 修复 bug
- `docs:` 文档更新
- `style:` 代码格式（不影响逻辑）
- `refactor:` 重构
- `test:` 测试相关
- `chore:` 构建/工具相关

## 📄 许可证

本项目采用 [MIT License](LICENSE) 许可证。

## 🙏 致谢

- [Anthropic](https://www.anthropic.com/) - Claude API
- [Foundry](https://book.getfoundry.sh/) - 以太坊开发工具
- [React Flow](https://reactflow.dev/) - 图可视化库
- [Litestar](https://litestar.dev/) - Python Web 框架

## 📬 联系方式

- Issue Tracker: [GitHub Issues](https://github.com/your-username/forge-mind/issues)
- Discussions: [GitHub Discussions](https://github.com/your-username/forge-mind/discussions)

---

<div align="center">
  Made with ❤️ by the ForgeMind Team
</div>
