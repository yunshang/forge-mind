# 沙盒测试功能需求文档

## 📋 概述

沙盒测试功能允许用户在本地 Anvil 环境中编译、部署和交互测试生成的智能合约。

## 🔍 现状分析

### 已实现功能

| 模块 | 文件 | 功能 |
|------|------|------|
| 后端技能 | `backend/skills/sandbox_simulation.py` | 编译、部署、提取函数 |
| 后端路由 | `backend/routes/sandbox.py` | `/api/sandbox/call` 调用合约 |
| 前端组件 | `frontend/src/components/SandboxPlayground.tsx` | 函数调用界面 |

### 存在问题

| 问题 | 影响 | 优先级 |
|------|------|--------|
| `solc not found` | 无法编译合约 | 🔴 高 |
| 编译器路径配置不灵活 | 用户环境适配困难 | 🔴 高 |
| 参数类型处理不完善 | 复杂类型参数无法输入 | 🟡 中 |
| 无 gas 估算 | 用户不知道消耗多少 gas | 🟡 中 |
| 无重置功能 | 无法重新部署测试 | 🟡 中 |
| 无交易历史 | 无法追溯调用记录 | 🟢 低 |

## 🎯 需求整理

### P0 - 核心功能（必须完成）

#### 1. 编译器自动检测

```
需求：自动检测 solc/foundry 安装位置
方案：
  1. 优先使用配置的 FORGE_SOLC_PATH
  2. 尝试 foundryup 安装路径 (~/.foundry/bin/solc)
  3. 尝试系统 PATH 中的 solc
  4. 如果都没有，提供安装指引
```

#### 2. 安装指引提示

```
需求：当 solc 未安装时，显示清晰的安装指引
内容：
  - Foundry 安装命令：curl -L https://foundry.paradigm.xyz | bash
  - 重启终端后运行：foundryup
  - 或单独安装 solc：brew install solidity
```

#### 3. 参数类型智能处理

```
需求：根据 Solidity 类型生成合适的输入控件
类型映射：
  - uint/int → 数字输入框
  - bool → 开关/复选框
  - address → 地址输入框（带 0x 前缀校验）
  - string → 文本输入框
  - bytes → hex 输入框
  - array[] → 动态列表输入
  - tuple → 嵌套表单
```

#### 4. Gas 估算显示

```
需求：写入操作前显示预估 gas 消耗
实现：
  - 调用前使用 estimateGas 估算
  - 显示预估值和当前 gas price
  - 计算预估费用（ETH）
```

### P1 - 增强功能（建议完成）

#### 5. 合约重置/重新部署

```
需求：支持重新部署合约进行测试
UI：添加"重新部署"按钮
行为：
  - 清除当前合约状态
  - 使用相同的构造函数参数重新部署
  - 更新合约地址
```

#### 6. 交易历史面板

```
需求：记录并显示所有交易调用
内容：
  - 函数名和参数
  - 交易哈希
  - Gas 消耗
  - 状态（成功/失败）
  - 时间戳
UI：可折叠的侧边面板或底部面板
```

#### 7. 错误详情展示

```
需求：显示详细的错误信息
内容：
  - Solidity 编译错误（带行号）
  - 运行时 revert 原因
  - Gas 不足错误
UI：可展开的错误详情面板
```

### P2 - 高级功能（可选）

#### 8. 事件日志监听

```
需求：监听并显示合约发出的事件
实现：
  - 使用 Web3.py 订阅事件
  - 实时显示新事件
  - 支持事件过滤
```

#### 9. 合约状态快照

```
需求：保存和恢复合约状态
功能：
  - 保存当前状态快照
  - 恢复到之前的快照
  - 比较不同状态
```

#### 10. 批量调用

```
需求：支持批量执行多个函数调用
场景：测试完整的业务流程
```

## 📐 技术实现方案

### 1. 编译器检测模块

```python
# backend/utils/solc_detector.py

class SolcDetector:
    @staticmethod
    def find_solc() -> str | None:
        """按优先级查找 solc 路径"""
        candidates = [
            settings.solc_path,                                    # 配置文件
            str(Path.home() / ".foundry" / "bin" / "solc"),       # Foundry
            "/usr/local/bin/solc",                                 # Homebrew
            shutil.which("solc"),                                  # PATH
        ]
        for path in candidates:
            if path and Path(path).exists():
                return path
        return None
    
    @staticmethod
    def get_install_instructions() -> str:
        """返回安装指引"""
        return """
        未找到 solc 编译器，请安装 Foundry：
        
        curl -L https://foundry.paradigm.xyz | bash
        source ~/.bashrc  # 或 ~/.zshrc
        foundryup
        
        安装完成后重启应用。
        """
```

### 2. 参数类型解析

```python
# 后端：从 ABI 解析参数类型详情

def parse_param_type(abi_type: str) -> dict:
    """解析 Solidity 类型字符串"""
    if abi_type.endswith("[]"):
        return {"base": parse_param_type(abi_type[:-2]), "is_array": True}
    if abi_type.startswith("uint") or abi_type.startswith("int"):
        return {"type": "number", "bits": int(abi_type[4:] or "256")}
    if abi_type == "bool":
        return {"type": "boolean"}
    if abi_type == "address":
        return {"type": "address"}
    if abi_type.startswith("bytes"):
        return {"type": "bytes", "size": abi_type[5:] or "dynamic"}
    if abi_type == "string":
        return {"type": "string"}
    if abi_type.startswith("tuple"):
        return {"type": "tuple", "components": [...]}
    return {"type": "unknown"}
```

### 3. Gas 估算

```python
# 后端路由增强

@post("/api/sandbox/estimate")
async def estimate_gas(data: CallRequest) -> EstimateResponse:
    """估算 gas 消耗"""
    w3 = Web3(Web3.HTTPProvider(settings.anvil_url))
    contract = w3.eth.contract(
        address=Web3.to_checksum_address(data.contract_address),
        abi=data.abi,
    )
    func = getattr(contract.functions, data.function_name)
    
    try:
        gas_estimate = func(*data.args).estimate_gas({"from": w3.eth.accounts[0]})
        gas_price = w3.eth.gas_price
        return EstimateResponse(
            status="success",
            gas_limit=gas_estimate,
            gas_price=gas_price,
            estimated_cost_wei=gas_estimate * gas_price,
            estimated_cost_eth=Web3.from_wei(gas_estimate * gas_price, "ether"),
        )
    except Exception as e:
        return EstimateResponse(status="error", error=str(e))
```

## 📊 UI 改进方案

### SandboxPlayground 布局

```
┌─────────────────────────────────────────────────────────────┐
│ 🎮 沙盒游乐场                                    [重新部署] │
├─────────────────────────────────────────────────────────────┤
│ 📍 0x1234...5678  ⛽ 预估: 45,231 gas ≈ 0.00012 ETH        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 🟢 只读 - totalSupply()                             │   │
│  │ ┌─────────────────────────────────────────────┐     │   │
│  │ │ 结果: 1000000                               │     │   │
│  │ └─────────────────────────────────────────────┘     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 🟡 写入 - transfer(address to, uint256 amount)      │   │
│  │ ┌─────────────────────────────────────────────┐     │   │
│  │ │ to: [0x...................................] │     │   │
│  │ │ amount: [100                           ] ⛽ │     │   │
│  │ └─────────────────────────────────────────────┘     │   │
│  │ [调用 transfer]  预估: 65,000 gas                    │   │
│  │ ┌─────────────────────────────────────────────┐     │   │
│  │ │ ✓ tx: 0xabc...def                           │     │   │
│  │ └─────────────────────────────────────────────┘     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ 📜 交易历史 (3)                              [展开/收起]    │
│ ├─ 14:23 transfer(0x123, 100) ✓ gas: 52,341                │
│ ├─ 14:22 approve(0x456, 500)  ✓ gas: 45,123                │
│ └─ 14:20 deploy()            ✓ gas: 1,234,567             │
├─────────────────────────────────────────────────────────────┤
│ > 14:23: transfer(0x1234...5678, 100)                      │
│ ✓ 成功 - Block #12345 Gas: 52,341                          │
└─────────────────────────────────────────────────────────────┘
```

## ✅ 验收标准

### P0 功能验收

- [ ] solc 未安装时显示安装指引
- [ ] 自动检测 Foundry 安装的 solc
- [ ] bool 类型显示开关控件
- [ ] address 类型验证 0x 前缀和长度
- [ ] uint/int 类型只允许数字输入
- [ ] 写入操作前显示 gas 估算
- [ ] 错误信息包含详细原因

### P1 功能验收

- [ ] "重新部署" 按钮正常工作
- [ ] 交易历史显示最近 20 条记录
- [ ] 点击交易哈希可查看详情

## 🔗 相关文件

- `backend/skills/sandbox_simulation.py` - 编译部署技能
- `backend/routes/sandbox.py` - 合约调用 API
- `frontend/src/components/SandboxPlayground.tsx` - 前端组件
- `backend/config.py` - 配置（solc_path, anvil_url）
