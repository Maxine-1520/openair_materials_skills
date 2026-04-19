---
name: preparation-recommendation
description: |
  制备参数推荐系统 Skill。当用户需要在材料科学领域实现制备参数推荐功能时触发，例如用户说"帮我制备参数推荐"、"运行制备流程"、"推荐实验方案"、"生成配方"、或要求"实现助熔剂法制备xxx"等功能时使用。这个 Skill 封装了完整的三步制备参数推荐 Pipeline：相似检索、统计窗口、配方推荐。用户只需在自己的项目中安装此 Skill，即可快速实现制备参数推荐功能。
compatibility: 任何项目（需要 Python 3.12+）
---

# 制备参数推荐系统

这是一个完整的材料制备参数推荐系统，通过三步 Pipeline 自动生成实验配方建议。系统基于相似材料检索、参数统计分析和 LLM 生成，提供科学可靠的制备方案。

## 🚀 快速开始

### 首次使用：安装系统

当用户首次请求使用制备参数推荐功能时，请按照以下步骤安装：

**目录说明**：
- **Skill 根目录** (`<skill_root>`)：包含 `SKILL.md`、`references\`、`resources\` 的目录
- **项目根目录** (`<project_root>`)：用户希望安装代码、修改代码的目标目录

#### 步骤 1：运行安装脚本

```bash
# 方式1：从 Skill 根目录的 resources/ 执行（推荐）
cd <skill_root>/resources
python install.py --project-root <project_root>

# 方式2：指定 Skill 根目录
python install.py --skill-root <skill_root> --project-root <project_root>

# 方式3：在项目目录下执行
cd <project_root>
python <skill_root>/resources/install.py
```

安装脚本会自动：
- 在项目根目录下创建 `recommend_parameter/` 子目录
- 在子目录中创建目录结构（src/, utils/, runner/, data/）
- 复制源代码文件到子目录
- 复制知识库数据（`data/knowledge_base/knowledge_base_processed.jsonl`）
- 设置数据模板
- 创建虚拟环境
- 生成配置文件

**✅ 所有路径都是相对于 `recommend_parameter/` 的相对路径，无硬编码**

**⚠️ 知识库说明**：
- 知识库是推荐系统的核心输入，包含已有材料的制备配方数据
- 默认会复制 Skill 附带的示例知识库
- 如需使用自己的数据，将 `knowledge_base_processed.jsonl` 替换为你的数据

#### 步骤 2：配置模型信息

编辑生成的 `.env` 文件：

```bash
nano .env
```

询问用户，添加 API 密钥、base url、模型id 等信息：

```bash
LLM_API_KEY=sk_xxx  # 替换为用户的密钥
LLM_BASE_URL=https://xxx  # 替换为用户的base url
LLM_MODEL=xxx  # 替换为用户的模型id
```

#### 步骤 3：安装依赖

```bash
source .venv/bin/activate  # Linux/Mac
.venv/Scripts/activate  # Windows/Powershell
pip install -r requirements.txt
```

#### 步骤 4：确认推荐元需求（关键步骤）

**⚠️ 重要**：在运行推荐流程之前，你必须调用 `<skill_root>/references/meta-rule.md` 文档向用户说明默认的推荐元需求和约束。并且向用户确认是否需要修改。

**如果需要修改元需求或约束**：
- 你要读取 `<skill_root>/references/add-constraint-sop.md` 文档
- 按照文档指引修改 `<project_root>/` 下的相关文件
- 添加新的 Prompt 指令和约束计算逻辑

**如果不需要修改**：
- 直接进入下一步运行推荐流程

#### 步骤 5：运行推荐流程

```bash
# 方式1：使用快速脚本
./run.sh "用助熔剂法制备AlInSe₃" 20

# 方式2：直接运行 Python 脚本
source .venv/bin/activate
python runner/run_pipeline.py --query "用助熔剂法制备AlInSe₃" --top-k 20
```

### 后续使用

安装完成后，只需：

```bash
source .venv/bin/activate
./run.sh "用助熔剂法制备BiSiTe₃"
```

结果会自动保存到 `data/` 目录下！

**注意**：每次运行前，系统都会询问是否需要修改元需求或约束。如果默认设置满足需求，直接运行即可。

## 1. 系统架构

### Pipeline 执行流程

```
用户 Query
  ↓
Step 1: similar_retrieval (相似检索)
  ↓
Step 2: statistic_window (统计窗口)
  ↓
Step 3: recommend_recipe (推荐配方)
  ↓
输出推荐结果
```

### 核心文件说明

| 目录 | 文件 | 功能 |
|------|------|------|
| `resources/src/` | `similar_retrieval.py` | 相似材料检索（Step 1） |
| `resources/src/` | `statistic_window.py` | 参数统计与窗口计算（Step 2） |
| `resources/src/` | `recommend_recipe.py` | 配方方案生成（Step 3） |
| `resources/runner/` | `run_pipeline.py` | 统一流水线入口 |
| `resources/utils/` | `parse_intuition.py` | 用户意图解析 |
| `resources/utils/` | `response2json.py` | LLM 响应解析 |
| `resources/utils/` | `reference_api.py` | LLM API 调用封装 |

## 2. 安装与配置

### 2.1 自动安装（推荐）

当用户首次请求使用制备参数推荐功能时，系统会自动完成以下步骤：

```bash
# 1. 创建虚拟环境
cd <项目根目录>
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate  # Windows

# 2. 安装依赖
pip install --upgrade pip setuptools wheel
pip install numpy openai python-dotenv flask

# 3. 设置 API Key
export LLM_API_KEY=sk_xxx  # 或在 .env 文件中配置
```

### 2.2 配置文件

系统会从以下位置读取配置：

- **环境变量**（优先级最高）：
  - `LLM_API_KEY`: API 密钥
  - `LLM_BASE_URL`: API 地址（OpenAI 兼容格式，默认：`https://api.siliconflow.cn/v1`）
  - `LLM_MODEL`: 模型名称（默认：`gpt-4o-mini`）
  - `LOG_LEVEL`: 日志级别（默认：`INFO`）

- **项目根目录的 `.env` 文件**（推荐）：
```bash
LLM_API_KEY=sk_xxx
LLM_BASE_URL=https://api.siliconflow.cn/v1
LLM_MODEL=gpt-4o-mini
LOG_LEVEL=INFO
```

**支持的 API 提供商**：
| 提供商 | LLM_BASE_URL 示例 | LLM_MODEL 示例 |
|--------|-------------------|----------------|
| SiliconFlow | `https://api.siliconflow.cn/v1` | `gpt-4o-mini` |
| OpenAI | `https://api.openai.com/v1` | `gpt-4o` |
| Ollama | `http://localhost:11434/v1` | `llama3` |
| vLLM | `http://localhost:8000/v1` | `your-model` |
| MatAI | `http://your-server:port/v1` | `matai-model` |

### 2.3 数据目录

安装后，系统会在项目根目录的 `recommend_parameter/` 子目录中创建以下目录结构：

```
<项目根目录>/
└── recommend_parameter/                    # ✅ 独立运行目录
    ├── .venv/                             # Python 虚拟环境
    ├── data/                              # 数据目录（相对路径）
    │   ├── knowledge_base/                # 知识库（必需输入）
    │   │   └── knowledge_base_processed.jsonl
    │   ├── similar_mates/                 # 相似检索结果
    │   │   ├── intuition_template.jsonl
    │   │   ├── how_to_parse_intuition.jsonl
    │   │   └── similar_on-base_processed.jsonl
    │   ├── recommand_window/              # 统计窗口结果
    │   │   ├── input_template.jsonl
    │   │   └── output_result.jsonl
    │   └── recommand_recipe/              # 推荐配方结果
    │       ├── input_real.jsonl
    │       ├── output_result.jsonl
    │       └── similar_recipes_feat_result.jsonl
    ├── src/                               # 核心源代码
    ├── utils/                             # 工具函数
    ├── runner/                            # 运行脚本
    └── pyproject.toml                     # 项目配置
```

**✅ 特点**：
- 所有代码、数据、配置都在 `recommend_parameter/` 子目录内
- 无硬编码的绝对路径
- 可独立运行，不影响项目其他文件

**知识库文件**（`knowledge_base_processed.jsonl`）是推荐系统的核心输入，包含已有材料的制备配方数据，格式如下：
```json
{"材料ID": "mat_001", "化学式": "GaN", "结构原型": "...", "配方列表": [...]}
```

## 3. 使用方法

### 3.1 快速开始

用户只需提供查询条件，即可运行完整的推荐流程：

```bash
# 1. 进入安装目录
cd <项目根目录>/recommend_parameter

# 2. 激活虚拟环境
source .venv/bin/activate

# 3. 运行完整的三步 Pipeline（使用默认路径和自动生成的文件名）
python runner/run_pipeline.py \
    --query "用助熔剂法制备BiSiTe₃" \
    --top-k 20

# 4. 自定义数据目录（如需要，使用相对路径）
python runner/run_pipeline.py \
    --query "用助熔剂法制备BiSiTe₃" \
    --data-dir data \
    --material BiSiTe3

# 5. 自定义输出路径（如需要，使用相对路径）
python runner/run_pipeline.py \
    --query "用助熔剂法制备BiSiTe₃" \
    --similar-output data/outputs/similar_BiSiTe3.jsonl \
    --window-output data/outputs/window_BiSiTe3.jsonl \
    --recommend-output data/outputs/recommend_BiSiTe3.jsonl \
    --debug
```

**✅ 所有路径都支持相对路径** - 相对于 `recommend_parameter/` 目录

**运行后输出文件**（位于 `<data-dir>/` 下）：
```
data/
├── similar_mates/similar_output_BiSiTe3.jsonl      # Step 1 输出
├── recommand_window/window_output_BiSiTe3.jsonl   # Step 2 输出
└── recommand_recipe/
    ├── recommend_output_BiSiTe3.jsonl             # Step 3 输出
    └── feature_output_BiSiTe3.jsonl              # 配方特征
```

### 3.2 命令行参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--query` | str | "用助熔剂法制备AlInSe₃" | 用户查询（目标材料描述） |
| `--top-k` | int | 30 | 返回的相似材料数量 |
| `--data-dir` | str | "./data" | 数据目录路径（相对或绝对路径） |
| `--material` | str | 自动从 query 提取 | 材料化学式（用于生成输出文件名） |
| `--similar-output` | str | `similar_mates/similar_output_{material}.jsonl` | 相似检索输出路径 |
| `--window-output` | str | `recommand_window/window_output_{material}.jsonl` | 统计窗口输出路径 |
| `--recommend-output` | str | `recommand_recipe/recommend_output_{material}.jsonl` | 推荐配方输出路径 |
| `--feature-output` | str | `recommand_recipe/feature_output_{material}.jsonl` | 配方特征输出路径 |
| `--debug` | flag | False | 启用调试模式 |

**输出文件名约定**：系统会自动从 `--query` 中提取材料化学式，生成 `<输出类型>_<材料化学式>.jsonl` 格式的文件名。

示例：
| Query | 生成的材料名 | 输出文件 |
|-------|-------------|---------|
| `用助熔剂法制备BiSiTe₃` | BiSiTe₃ | `similar_output_BiSiTe3.jsonl` |
| `制备GaN晶体` | GaN | `similar_output_GaN.jsonl` |
| `AlInSe₃单晶生长` | AlInSe₃ | `similar_output_AlInSe3.jsonl` |

如需自定义输出路径，可通过 `--similar-output`、`--window-output` 等参数指定。

### 3.3 Python API

```python
from src.similar_retrieval import main as run_similar_retrieval
from src.statistic_window import main as run_statistic_window
from src.recommend_recipe import main as run_recommend_recipe

# Step 1: 相似检索
run_similar_retrieval()

# Step 2: 统计窗口
run_statistic_window()

# Step 3: 推荐配方
run_recommend_recipe()
```

### 3.4 Web API（可选）

启动 Web 服务：

```bash
source .venv/bin/activate
python runner/api_server.py
```

API 端点：
- `GET /health`: 健康检查
- `POST /recommend`: 提交推荐请求

## 4. 输出说明

### 4.1 目录结构

运行完成后，结果会保存在 `<data-dir>/` 目录下，文件名自动根据材料化学式生成：

```
<data-dir>/
├── similar_mates/
│   └── similar_output_{材料化学式}.jsonl              # 相似材料列表
├── recommand_window/
│   └── window_output_{材料化学式}.jsonl               # 参数统计窗口
└── recommand_recipe/
    ├── recommend_output_{材料化学式}.jsonl            # 推荐配方
    └── feature_output_{材料化学式}.jsonl              # 配方特征
```

示例（query: "用助熔剂法制备BiSiTe₃"）：
```
data/
├── similar_mates/similar_output_BiSiTe3.jsonl
├── recommand_window/window_output_BiSiTe3.jsonl
└── recommand_recipe/
    ├── recommend_output_BiSiTe3.jsonl
    └── feature_output_BiSiTe3.jsonl
```

### 4.2 输出格式

**推荐配方输出示例**：
```json
{
  "目标材料": {
    "化学式": "AlInSe₃",
    "结构原型": "层状结构",
    "是否二维": false,
    "是否半导体": true
  },
  "推荐方案列表": [
    {
      "方案编号": "方案1",
      "工艺参数": {
        "温度程序": {
          "最高温段保温温度_摄氏": 950,
          "最高温段保温时间_h": 24,
          "降温速率_℃每小时": 5
        },
        "助熔剂": {
          "助熔剂配方": "Na2Se + Na2S",
          "助熔剂比例": "1:1"
        }
      },
      "约束验证": {
        "温度约束": "通过",
        "安全约束": "通过"
      }
    }
  ]
}
```

## 5. 自定义配置

### 5.1 修改检索参数

编辑 `data/similar_mates/intuition_template.jsonl`：

```json
{
  "目标材料": {
    "化学式": "目标材料化学式",
    "结构原型": "结构原型",
    "是否二维": false,
    "是否半导体": true
  },
  "相似度设置": {
    "结构原型_权重": 0.4,
    "是否二维_权重": 0.1,
    "是否半导体_权重": 0.1,
    "材料族系_权重": 0.4
  },
  "返回设置": {
    "最多返回材料数_top_k": 30
  }
}
```

### 5.2 修改实验室约束

编辑 `data/recommand_window/input_template.jsonl`：

```json
{
  "实验室约束": {
    "最高允许温度_摄氏": 1000,
    "最小降温速率_℃每小时": 0.5,
    "最大降温速率_℃每小时": 300,
    "最长单次实验时长_h": 200
  }
}
```

### 5.3 修改推荐偏好

编辑 `data/recommand_recipe/input_real.jsonl`：

```json
{
  "用户方案设计偏好": {
    "期望方案数量": 5,
    "策略偏好": "多样覆盖",
    "优先大尺寸晶体": true,
    "优先缩短实验时长": false
  }
}
```

## 6. 常见问题

### Q1: 如何修改 API 密钥？
```bash
# 方式1: 环境变量
export LLM_API_KEY=sk_xxx

# 方式2: .env 文件
echo "LLM_API_KEY=sk_xxx" >> .env
```

### Q2: 如何使用其他 LLM API？
```bash
# Ollama
export LLM_BASE_URL=http://localhost:11434/v1
export LLM_MODEL=llama3

# vLLM
export LLM_BASE_URL=http://localhost:8000/v1
export LLM_MODEL=your-model

# MatAI
export LLM_BASE_URL=http://your-matai-server:port/v1
export LLM_MODEL=matai-model

python runner/run_pipeline.py --query "xxx"
```

### Q3: 如何增加相似材料数量？
```bash
python runner/run_pipeline.py --query "xxx" --top-k 50
```

### Q4: 如何查看详细日志？
```bash
export LOG_LEVEL=DEBUG
python runner/run_pipeline.py --query "xxx" --debug
```

## 7. 技术细节

### 7.1 三步 Pipeline

1. **相似检索（similar_retrieval）**：
   - 解析用户查询中的材料信息
   - 计算与知识库中材料的相似度
   - 返回 top-K 个最相似的材料及其配方

2. **统计窗口（statistic_window）**：
   - 收集相似材料的工艺参数
   - 计算参数分布的统计窗口（P10-P90）
   - 考虑实验室设备约束

3. **推荐配方（recommend_recipe）**：
   - 分析相似配方，提炼典型方案
   - 生成多个配方变体
   - 验证约束条件
   - 输出推荐方案

### 7.2 LLM 支持

系统支持任意 OpenAI 兼容格式的 LLM API：
- **SiliconFlow API**（默认）：`LLM_BASE_URL=https://api.siliconflow.cn/v1`，`LLM_MODEL=gpt-4o-mini`
- **OpenAI 官方**：`LLM_BASE_URL=https://api.openai.com/v1`，`LLM_MODEL=gpt-4o`
- **Ollama**：`LLM_BASE_URL=http://localhost:11434/v1`，`LLM_MODEL=llama3`
- **vLLM**：`LLM_BASE_URL=http://localhost:8000/v1`
- **MatAI**：`LLM_BASE_URL=http://your-server:port/v1`

## 8. 维护指南

### 8.1 更新知识库

将新的材料数据添加到 `<project_root>/data/knowledge_base/knowledge_base_processed.jsonl`：

```json
{"材料ID": "mat_xxx", "化学式": "新材料", "结构原型": "...", "是否二维": false, "是否半导体": true, "配方列表": [...]}
```

知识库格式说明：
- **材料ID**：唯一标识符（如 `mat_001`）
- **化学式**：材料化学式
- **结构原型**：晶体结构类型
- **是否二维/是否半导体**：材料特性
- **配方列表**：该材料的制备配方数组，每个配方包含：
  - 生长方法、助熔剂信息、温度程序、容器等

### 8.2 扩展约束类型

读取 `<skill_root>/references/add-constraint-sop.md` 文档，学习如何添加新的约束条件。

### 8.3 调试技巧

1. 使用 `--debug` 参数查看详细日志
2. 检查各步骤的中间输出文件
3. 验证输入模板是否符合格式要求

---

**版本**：v1.0
**依赖**：Python 3.12+
**最后更新**：2026-03-24
