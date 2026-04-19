---
name: auto-xrd
description: 当用户需要基于化学式、CIF文件或MP材料ID自动训练XRD/PDF模型，并对真实谱图做推理时触发。也用于单目标负样本迭代优化，自动寻找最佳负样本组合直到真实数据达到满意阈值。常见说法：用公式A/B训练XRD、三相训练、指定空间群版本、MP加本地CIF混合训练、对真实数据跑预测、单目标自动找负样本迭代训练、让XRD自动重训直到真实数据达标。
---

# Auto-XRD Skill

这是一个面向 XRD 自动训练和推理的完整 skill，基于 [XRD-1.1](https://github.com/tacmon/XRD-1.1) 库实现。

## 目录说明

- **Skill 根目录** (`<skill_root>`)：包含 `SKILL.md`、`references/`、`resources/` 的目录
- **项目根目录** (`<project_root>`)：用户希望安装代码、修改代码的目标目录（安装后为 `<project_root>/auto_xrd/`）

## 首次使用：安装系统

当用户首次请求使用 Auto-XRD 功能时，请按照以下步骤安装：

### 步骤 1：运行安装脚本

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
- 在项目根目录下创建 `auto_xrd/` 子目录
- 在子目录中创建目录结构（scripts/, docker/, libs/, data/）
- 复制源代码脚本到 scripts/
- 复制 Docker 配置到 docker/
- 复制示例XRD数据到 data/ 目录（AlN、CrSiTe体系、FeS等）
- 设置 XRD-1.1 git submodule
- 设置数据模板
- 创建虚拟环境
- 生成配置文件

**✅ 所有路径都是相对于 `auto_xrd/` 的相对路径，无硬编码**

**⚠️ 示例数据说明**：
- 示例数据位于 `data/` 目录，包含真实XRD谱图
- 安装时会复制示例数据用于测试
- 用户可将 `data/` 替换为自己的数据，或在现有数据基础上添加

### 步骤 2：配置模型信息

编辑生成的 `.env` 文件：

```bash
nano auto_xrd/.env
```

添加 API 密钥：

```bash
MP_API_KEY=your_materials_project_api_key_here
```

### 步骤 3：安装依赖

```bash
cd <project_root>
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows/Powershell
cd auto_xrd
pip install -r requirements.txt
```

### 步骤 4：构建 Docker 镜像（可选）

询问用户是否使用 Docker 镜像。如果用户选择使用，执行以下命令：

```bash
cd auto_xrd/docker
docker compose up -d --build
```

**⚠️ 注意**：Docker 用于提供一致的训练环境，包含 PyTorch、pymatgen 等依赖。

## 两个主要工作流

本 skill 支持两个互补的工作流，请根据用户需求选择：

1. **基础训练推理**（xrd-formula-train-infer）：基于明确提供的化学式/CIF训练
2. **迭代负样本优化**（xrd-target-negative-loop）：单目标自动寻找最佳负样本

---

# 工作流 1：基础训练推理

## 何时使用

当用户提供了明确的化学式、材料ID或 CIF 文件，希望直接训练 XRD 模型并对真实数据做推理时使用。

## 输入

用户至少提供以下之一：
- 一个或多个化学式/标签
- 一个或多个明确的 MP material ID
- 一个或多个本地 CIF 路径

用户可选提供：
- 额外的对比相或更多相
- 精确空间群、稳定性或"就是这个结构"的约束
- 真实谱图数据路径（默认读取 `data/` 下全部 `*.txt`、`*.xy`、`*.gk`）

## 强制约束

1. 先使用 Docker 启动容器环境（如果用户允许）
2. 运行 `docker compose` 时始终带上 `LOCAL_UID=$(id -u)` 和 `LOCAL_GID=$(id -g)`
3. 所有训练和推理在容器里执行，数据保存在宿主机挂载目录
4. 每次训练使用新的 `run_name`，不要覆盖旧结果
5. 训练前清理旧的 `References`、`Models` 等状态
6. `Spectra` 和 `All_CIFs` 用相对软链接指向 `soft_link/...`
7. 如果用户指定精确结构版本，必须先核实 MP 是否存在

## 工作流步骤

### Step 1: 检查前置条件

- 确认 `auto_xrd/` 目录存在
- 检查 `docker/docker-compose.yaml` 存在（如果使用 Docker）
- 检查 `libs/XRD-1.1` submodule 已初始化
- 检查 `MP_API_KEY` 是否可用（如果需要 MP 下载）

### Step 2: 判定输入类型

按这个顺序判断：
- 用户直接给了本地 CIF：直接采用，不再去 MP 替换
- 用户直接给了 MP material ID：直接采用，不再做候选排序
- 用户给的是化学式，但附带精确要求：先查 MP 是否存在该版本
- 用户只给了化学式：进入候选排序

### Step 3: 解析 MP 候选

```bash
cd <project_root>/auto_xrd
python3 scripts/mp_formula_tool.py candidates --formula-a "A" [--formula-b "B"]
```

向用户展示前 3 个候选，包括：
- `material_id`
- `formula_pretty`
- `space group`
- `energy_above_hull`
- `top peaks (20-60 deg)`

### Step 4: 选择执行脚本

- 只有两个相，且都来自 MP：用 `run_pipeline.sh`
- 三相及以上，或混合 MP + 本地 CIF：用 `run_multiphase_pipeline.sh`

### Step 5: 运行流水线

双相全 MP 示例：

```bash
cd <project_root>/auto_xrd
bash scripts/run_pipeline.sh \
  --formula-a "A" \
  --formula-b "B" \
  --material-id-a "mp-xxxx" \
  --material-id-b "mp-yyy" \
  [--spectra-source "./data/某个子目录"]
```

多相混合来源示例：

```bash
cd <project_root>/auto_xrd
bash scripts/run_multiphase_pipeline.sh \
  --phase-label "CrSiTe3_148" \
  --phase-label "AlN_216" \
  --mp-material-id "mp-3779" \
  --mp-material-id "mp-1700" \
  --local-cif "./local_cifs/Bi2Si2Te6.cif" \
  --manual-reference "CrSiTe3_148=CrSiTe3__mp-3779.cif" \
  --manual-reference "AlN_216=AlN__mp-1700.cif"
```

### Step 6: `tabulate_cifs` 失败时的回退

遇到兼容性问题时，使用 `--skip_filter` 参数，让脚本自动追加此选项。

### Step 7: 结果汇报

完成后必须告诉用户以下路径：

- 本轮运行目录名
- 预测结果：`soft_link/All_CIFs/<run_name>/results/result.csv`
- 模型目录：`soft_link/All_CIFs/<run_name>/Models`
- 参考相目录：`soft_link/All_CIFs/<run_name>/References`
- 真实谱图副本：`soft_link/Spectra/<run_name>`
- 真实谱图预览：`figure/<run_name>`

`result.csv` 字段说明：
- `Predicted phases`：`run_CNN.py --inc_pdf` 的融合结果（主预测列）
- `XRD predicted phases`：XRD-only 结果
- `PDF predicted phases`：PDF-only 结果

### Step 8: 用户回复"不满意"时

不要覆盖当前结果，保持已确认的标签集合不变，优先：
- 更换同一标签的另一个 MP 候选
- 补本地 CIF
- 调整多相组合
- 生成新的 `run_name` 重新执行

---

# 工作流 2：迭代负样本优化

## 何时使用

当用户只给一个目标化学式 A，希望自动寻找负样本、自动训练并根据真实数据 `processed_result.csv` 评分迭代优化时使用。

## 输入

用户至少提供：
- 一个目标化学式 A

用户可选提供：
- 目标结构的精确要求（空间群、稳定性、MP ID 或本地 CIF）
- 真实数据范围（默认递归读取 `data/` 下全部 `*.txt`、`*.xy`、`*.gk`）
- 候选负样本范围或禁止使用的负样本
- 满意阈值（例如"真实数据准确率至少 95%"）

## 强制约束

1. 主 Agent 负责选目标结构、选负样本、决定是否继续；subagent 只负责执行训练推理
2. 只在用户明确允许的前提下启动 subagent
3. 所有训练和推理必须走 Docker，带 `LOCAL_UID=$(id -u)` 和 `LOCAL_GID=$(id -g)`
4. 每次训练使用新的 `run_name`，不要覆盖旧结果
5. 目标公式 A 一旦确认，不要擅自换成别的式子
6. 如果需要从 MP 下载，必须先确认 `MP_API_KEY` 可用
7. 任务是否完成必须按真实数据 `processed_result.csv` 和 `score.json` 判断，不要按原始 `result.csv`、训练 loss 或主观观感判断
8. 在开始新一轮训练前，先对当前 run 的 `result.csv` 做阈值搜索
9. 迭代过程中必须保存"当前最佳 run + 最佳阈值"

## 主 Agent 职责

主 Agent 本地完成：
1. 检查前置条件
2. 确定目标结构 A
3. 选出第一轮负样本集合
4. 生成训练计划并启动 subagent
5. 等 subagent 返回 run 目录、`result.csv`、参考相和模型路径
6. 本地运行后处理与评分脚本
7. 对当前 run 做阈值搜索，记录最佳 `confidence_threshold`
8. 根据真实数据 processed 评分判断：满意则结束，不满意则分析混淆、重新选负样本

## 目标结构 A 的确定规则

- 用户给本地 CIF：直接用本地 CIF，不要换成 MP
- 用户给 MP material ID：直接采用
- 用户给精确空间群或稳定性要求：先核实 MP 是否存在该版本
- 用户只给化学式 A：在 MP 中选优先候选，优先稳定、精确化学计量、`energy_above_hull` 更低的结构

## 负样本选择规则

第一轮优先顺序：
1. 与 A 拓扑或衍射峰型差异较大、且在 MP 中稳定的候选
2. `mp_formula_tool.py candidates` 能给出的高对比候选
3. 用户点名要求加入的负样本
4. 仓库已有本地 CIF 中与 A 同体系、但容易混淆的相

重训时优先顺序：
1. 先看 `processed_result.csv` 与评分报告中哪些文件被错分
2. 再看原始 `result.csv` 中最常作为高置信混淆项的相
3. 优先替换最可疑的一个负样本，不要整组全部推倒

## 评分闭环

### Step 1: 后处理 result.csv

```bash
cd <project_root>/auto_xrd
python3 scripts/postprocess_target_results.py \
  --input ".../result.csv" \
  --output ".../processed_result.csv" \
  --target-formula "A" \
  --confidence-threshold 50
```

### Step 2: 评分 processed_result.csv

```bash
python3 scripts/score_processed_results.py \
  --input ".../processed_result.csv" \
  --target-formula "A" \
  --known-formula "A" \
  --known-formula "Negative1" \
  --known-formula "Negative2" \
  --output-json ".../score.json"
```

### Step 3: 阈值搜索

```bash
for thr in 40 50 60 70 80 90 95 98; do
  python3 scripts/postprocess_target_results.py \
    --input ".../result.csv" \
    --output ".../processed_result_thr${thr}.csv" \
    --target-formula "A" \
    --confidence-threshold "$thr"

  python3 scripts/score_processed_results.py \
    --input ".../processed_result_thr${thr}.csv" \
    --target-formula "A" \
    --known-formula "A" \
    --known-formula "Negative1" \
    --known-formula "Negative2" \
    --output-json ".../score_thr${thr}.json"
done
```

### 评分解释

- 如果文件名或目录名里能唯一解析出 `known-formula` 之一，则记为弱标签样本
- 如果弱标签样本足够多，计算目标 A 的 precision / recall / F1
- 如果只有负样本侧标签，计算真实数据上的负样本侧 proxy accuracy

### 默认满意判据

- `evaluation_mode == weak_labels`
- `labeled_rows >= 10`
- `coverage >= 0.10`
- 真实数据 processed_result 准确率至少 `95%`（默认）
- 若存在目标正样本与负样本标签：`precision >= 0.85`, `recall >= 0.70`, `f1 >= 0.75`
- 若只能做负样本侧 proxy：明确声明是 proxy，记录相关指标

---

## 脚本索引

所有脚本位于 `<project_root>/auto_xrd/scripts/`：

| 脚本 | 用途 |
|------|------|
| `mp_formula_tool.py` | 查询 MP 材料、下载 CIF、获取候选结构 |
| `run_pipeline.sh` | 双相全 MP 的一次完整训练+推理 |
| `run_multiphase_pipeline.sh` | 三相及以上或混合来源的训练+推理 |
| `postprocess_target_results.py` | 非交互式后处理 result.csv |
| `score_processed_results.py` | 对 processed_result.csv 做评分 |

---

## 环境变量

`<project_root>/auto_xrd/.env` 只需要：

```bash
MP_API_KEY=your_materials_project_api_key_here
```

仅在需要从 MP 下载时才需要此密钥。纯本地 CIF 流程可以跳过。

---

## 禁止事项

- 不要调用交互式训练脚本
- 不要假设宿主机 Python 环境可直接运行（使用 Docker）
- 不要按原始 `result.csv`、训练 loss 或主观观感判断任务是否完成
