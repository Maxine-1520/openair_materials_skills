---
name: material-pipeline
description: |
  材料搜索与制备参数推荐串联Pipeline。当用户想要：
  - 基于特定实验设备（如Flux）制备二维材料
  - 同时需要搜索材料并获取制备参数推荐
  - 表达类似"我想制备XX材料，应该怎么制备"的需求

  这个skill会自动：
  1. 调用mp-material-search搜索符合要求的2D半导体材料
  2. CC自动从搜索结果中选择最合适的一个
  3. 调用preparation-recommendation生成制备参数推荐

  使用场景包括：材料发现、实验方案设计、二维材料生长参数优化等。
compatibility: mp-api, pymatgen, python 3.12+
---

# 材料搜索与制备参数推荐Pipeline

这是一个将材料搜索和制备参数推荐串联的自动化Pipeline。用户只需提供需求描述，系统会自动完成从材料筛选到制备方案生成的完整流程。

## 核心功能

1. **智能材料搜索**：基于用户需求搜索Materials Project数据库中的2D半导体材料
2. **自动材料选择**：CC根据需求自动从多个候选材料中选择最合适的一个
3. **制备参数推荐**：基于选中的材料生成具体的制备参数建议

## 工作流程

```
用户需求描述
  ↓
Step 1: 调用 mp-material-search 搜索材料
  ↓
Step 2: CC自动选择最佳匹配材料
  ↓
Step 3: 调用 preparation-recommendation 生成制备参数
  ↓
输出：材料信息 + 制备参数推荐
```

## 使用方法

### 触发条件

当用户提供类似以下的描述时使用此skill：
- "我想基于Flux实验设备，制备载流子迁移率高的二维单晶半导体材料"
- "帮我找一种适合制备的2D材料并推荐制备参数"
- "基于MBE设备，制备高迁移率的二维材料"
- "我想做二维材料实验，帮我找材料并推荐制备方案"

### 执行步骤

#### Step 1: 解析用户需求

从用户描述中提取关键信息：
- **目标材料类型**：2D材料、单晶、半导体等
- **性能要求**：载流子迁移率、带隙、稳定性等
- **实验设备**：Flux、MBE、CVD、MBE等
- **其他约束**：元素偏好、晶体结构等

**示例解析**：
用户输入："我想基于Flux实验设备，制备载流子迁移率高的二维单晶半导体材料"

提取结果：
- 设备：Flux
- 材料类型：2D材料、单晶
- 性能要求：高载流子迁移率
- 类型：半导体

#### Step 2: 调用 mp-material-search 搜索材料

根据解析结果，调用 mp-material-search skill 进行材料搜索。

**关键操作**：
1. 确定搜索参数（元素、带隙范围、结果数量等）
2. 执行搜索脚本：`python skills/mp-material-search/scripts/filter_materials.py`
3. 获取搜索结果

**搜索参数设置建议**：
- 对于"高迁移率"要求：优先选择低有效质量、高载流子迁移率的材料
- 对于"半导体"要求：设置 band_gap_min >= 0.5 eV
- 对于"2D材料"：筛选具有层状结构的材料
- 设置 `max-results` 为 5-10 以便CC选择

#### Step 3: CC自动选择最佳材料

从搜索结果中，CC根据用户需求自动选择一个最合适的材料。

**选择标准**：
1. **需求匹配度**：材料特性与用户需求的匹配程度
   - "高迁移率"：选择电子结构优异、载流子迁移率预测高的材料
   - "稳定性"：选择 energy_above_hull 低的热力学稳定材料
   - "2D"：选择具有层状结构或二维几何形状的材料

2. **综合评分**：参考 recommendation_score

3. **实际可行性**：考虑元素稀有度、制备难度等因素

**选择过程示例**：
```
候选材料列表：
1. MoS₂ - 带隙1.8eV，迁移率高，稳定性好，recommendation_score: 0.85
2. WS₂ - 带隙1.9eV，迁移率高，稳定性好，recommendation_score: 0.82
3. MoSe₂ - 带隙1.5eV，迁移率较高，稳定性一般，recommendation_score: 0.78

根据用户需求"高迁移率二维半导体"，CC选择：MoS₂
理由：MoS₂在2D过渡金属硫化物中具有最高的载流子迁移率预测，
带隙适中（1.8eV），热力学稳定性好，综合评分最高。
```

#### Step 4: 检查并安装 preparation-recommendation

在调用 preparation-recommendation 之前，检查是否已安装：

1. **检查安装状态**：
   - 查看项目根目录是否有 `recommend_parameter/` 目录
   - 检查虚拟环境 `.venv` 是否存在

2. **如果未安装**：
   - 调用 preparation-recommendation skill 的安装流程
   - 参考 preparation-recommendation/SKILL.md 的安装说明
   - 执行安装脚本并配置API密钥

3. **如果已安装**：
   - 激活虚拟环境
   - 准备调用推荐流程

#### Step 5: 构建制备参数推荐查询

根据选中的材料，构建推荐查询。

**Query构建规则**：
- 格式：`用{设备}法制备{材料化学式}`
- 示例：`用Flux法制备MoS₂`
- 注意：化学式应使用下标数字（如 MoS2 而不是 MoS₂）

**查询构建示例**：
```
选中材料：MoS₂
用户设备：Flux
构建Query：用Flux法制备MoS2
```

#### Step 6: 调用 preparation-recommendation

执行制备参数推荐：

1. **运行Pipeline**：
```bash
cd <project_root>/recommend_parameter
source .venv/bin/activate
python runner/run_pipeline.py --query "用Flux法制备MoS2" --top-k 20
```

2. **等待结果**：
   - 系统会执行三步Pipeline：
     - Step 1: 相似检索
     - Step 2: 统计窗口
     - Step 3: 配方推荐
   - 结果保存在 `data/recommand_recipe/recommend_output_*.jsonl`

3. **解析输出**：
   - 读取推荐结果文件
   - 提取关键制备参数（温度、压力、时间、气氛等）

## 输出格式

最终输出包含两部分：

### 1. 选中的材料信息

```json
{
  "selected_material": {
    "formula": "MoS₂",
    "material_id": "mp-2815",
    "band_gap": "1.8 eV",
    "energy_above_hull": "0.02 eV/atom",
    "recommendation_score": 0.85,
    "selection_reason": "高载流子迁移率，热力学稳定，适合Flux法制备"
  }
}
```

### 2. 制备参数推荐

```json
{
  "preparation_recommendation": {
    "query": "用Flux法制备MoS2",
    "method": "Flux法",
    "recommended_parameters": {
      "temperature": {
        "growth_temp": "850-900°C",
        "ramp_rate": "10°C/min",
        "soak_time": "2h"
      },
      "pressure": "常压/低压",
      "atmosphere": "惰性气体（Ar/He）",
      "source_materials": "Mo (99.95%), S (99.99%)",
      "crucible": "Al₂O₃",
      "cooling_rate": "5°C/h"
    },
    "similar_materials_reference": [
      "WS₂", "MoSe₂", "WSe₂"
    ],
    "confidence": "高",
    "notes": [
      "建议使用化学计量比Mo:S=1:2的原料",
      "生长温度需要精确控制以获得单晶",
      "后退火处理可以提高结晶质量"
    ]
  }
}
```

## 完整执行示例

### 用户输入
```
我想基于Flux实验设备，制备载流子迁移率高的二维单晶半导体材料
```

### 系统执行

**Step 1: 需求解析**
- 设备：Flux
- 材料类型：2D材料、单晶
- 性能要求：高载流子迁移率
- 类型：半导体

**Step 2: 材料搜索**
```bash
python skills/mp-material-search/scripts/filter_materials.py \
  --band-gap-min 0.5 \
  --band-gap-max 3.0 \
  --max-results 10
```

**搜索结果**：
- MoS₂: recommendation_score=0.85
- WS₂: recommendation_score=0.82
- MoSe₂: recommendation_score=0.78
- WSe₂: recommendation_score=0.75
- ...

**Step 3: 材料选择**
选择 **MoS₂** (mp-2815)
理由：高迁移率2D半导体，热力学稳定，带隙1.8eV适中，综合评分最高

**Step 4: 制备参数推荐**
```bash
cd <project_root>/recommend_parameter
source .venv/bin/activate
python runner/run_pipeline.py --query "用Flux法制备MoS2" --top-k 20
```

**Step 5: 输出结果**

## 注意事项

1. **API密钥配置**：
   - mp-material-search 需要 MP_API_KEY
   - preparation-recommendation 需要 LLM_API_KEY

2. **安装依赖**：
   - 首次使用时，确保 preparation-recommendation 已正确安装
   - 检查虚拟环境和依赖包

3. **结果解读**：
   - 推荐参数仅供参考，实际实验需要根据具体条件调整
   - 关注 confidence 字段，高置信度结果更可靠

4. **材料选择灵活性**：
   - CC会综合考虑多个因素选择材料
   - 如果候选材料都不理想，可以调整搜索参数重新搜索

5. **错误处理**：
   - 如果搜索失败，提示用户检查API密钥和网络连接
   - 如果安装失败，参考skill文档进行手动安装

## 依赖Skill

- **mp-material-search**：用于搜索Materials Project数据库
- **preparation-recommendation**：用于生成制备参数推荐

这两个skill是本skill的核心依赖，必须正确安装和配置。
