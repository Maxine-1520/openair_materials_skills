# XRD Formula Train Infer - 详细参考

## 概述

这个工作流用于基于化学式/CIF训练XRD模型并对真实数据做推理。

## 输入要求

### 必须提供（至少一项）
- 化学式/标签（例如 "Fe2O3", "TiO2")
- MP material ID（例如 "mp-1234"）
- 本地 CIF 文件路径

### 可选提供
- 额外的对比相（用于区分不同材料）
- 精确空间群或稳定性要求
- 真实谱图数据路径（默认读取 `data/` 下全部 `*.txt`, `*.xy`, `*.gk`）

## MP 候选选择标准

当用户只给化学式时，按以下标准排序候选：

1. **稳定性优先**：优先选择 `is_stable = true` 的结构
2. **能量优先**：选择 `energy_above_hull` 更低的结构
3. **精确化学计量**：优先选择化学计量精确的
4. **避免理论结构**：优先选择非 theoretical 的

## 脚本使用示例

### 查询候选结构

```bash
python3 scripts/mp_formula_tool.py candidates --formula-a "Fe2O3" --formula-b "TiO2"
```

### 双相训练

```bash
bash scripts/run_pipeline.sh \
  --formula-a "Fe2O3" \
  --formula-b "TiO2" \
  --material-id-a "mp-861" \
  --material-id-b "mp-2656"
```

### 多相混合训练

```bash
bash scripts/run_multiphase_pipeline.sh \
  --phase-label "Fe2O3_167" \
  --phase-label "TiO2_136" \
  --phase-label "Al2O3_167" \
  --mp-material-id "mp-861" \
  --mp-material-id "mp-2656" \
  --local-cif "./local_cifs/CustomPhase.cif"
```

## Docker 使用

### 启动容器

```bash
cd auto_xrd/docker
docker compose up -d --build
```

### 进入容器

```bash
docker compose exec xrd-service bash
```

### 停止容器

```bash
docker compose down
```

## 常见问题

### MP_API_KEY 不可用

如果 `MP_API_KEY` 未设置或无效：
- 脚本会提示错误
- 只能使用本地 CIF 文件
- 无法从 MP 下载候选结构

### tabulate_cifs 失败

如果遇到 `TypeError: check_array() got an unexpected keyword argument 'force_all_finite'`：
- 这是 `autoXRD/tabulate_cifs` 与当前 `pyts/sklearn` 兼容性问题
- 使用 `--skip_filter` 参数绕过
- 脚本会自动追加此选项

### Docker 权限问题

如果生成的文件是 root 所有者：
- 使用 `LOCAL_UID=$(id -u)` 和 `LOCAL_GID=$(id -g)`
- docker-compose.yaml 已配置此参数
