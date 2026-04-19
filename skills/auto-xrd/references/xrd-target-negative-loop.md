# XRD Target Negative Loop - 详细参考

## 概述

这个工作流用于单目标负样本迭代优化。当用户只给一个目标化学式 A，希望自动寻找最佳负样本组合、自动训练并根据真实数据评分迭代优化时使用。

## 迭代流程

```
┌─────────────────┐
│  确定目标结构 A  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  选择初始负样本  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  训练 + 推理     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  后处理 + 评分   │
└────────┬────────┘
         │
         ▼
    ┌────┴────┐
    │  满意?  │
    └────┬────┘
    是   │   否
    │    │
    ▼    ▼
  结束  分析混淆
         │
         ▼
    重新选负样本
         │
         ▼
      继续训练
```

## 评分指标

### Weak Labels 模式

当文件名/目录名能解析出材料公式时：

- **Precision**：目标被正确识别的比例
- **Recall**：实际目标被识别出来的比例
- **F1**：Precision 和 Recall 的调和平均

### Proxy 模式

当只有负样本侧标签时：

- **false_positive**：目标被误识别的负样本数
- **target_prediction_ratio**：目标预测占总预测的比例
- **unidentified_ratio**：无法识别的样本比例

## 阈值搜索策略

推荐搜索范围：40 到 100，步长 1-5

```bash
for thr in 40 50 60 70 80 90 95 98; do
  python3 scripts/postprocess_target_results.py \
    --input "result.csv" \
    --output "processed_result_thr${thr}.csv" \
    --target-formula "A" \
    --confidence-threshold "$thr"

  python3 scripts/score_processed_results.py \
    --input "processed_result_thr${thr}.csv" \
    --target-formula "A" \
    --known-formula "A" \
    --known-formula "Negative1" \
    --known-formula "Negative2" \
    --output-json "score_thr${thr}.json"
done
```

## 负样本选择策略

### 首次选择

1. **高对比度**：选择与目标 XRD 峰型差异大的
2. **MP 稳定性**：优先选择 MP 中稳定的结构
3. **用户指定**：优先包含用户明确要求的负样本
4. **同体系混淆**：包含与目标同体系但易混淆的相

### 重训策略

1. **分析错误**：先看哪些文件被错分
2. **定位问题**：找到最可疑的负样本
3. **最小替换**：只替换一个最可疑的负样本
4. **避免推倒**：不要一次性替换全部负样本

## 评分阈值

### 默认阈值

- `labeled_rows >= 10`：至少有 10 个可评分样本
- `coverage >= 0.10`：至少 10% 的样本可评分
- `precision >= 0.85`：目标识别准确率
- `recall >= 0.70`：目标召回率
- `f1 >= 0.75`：综合 F1 分数
- `accuracy >= 0.95`：真实数据总体准确率

### 自定义阈值

用户可以通过命令行参数覆盖默认阈值：

```bash
python3 scripts/score_processed_results.py \
  --input "processed_result.csv" \
  --target-formula "A" \
  --known-formula "A" \
  --known-formula "Negative1" \
  --min-precision 0.90 \
  --min-recall 0.80 \
  --min-f1 0.85
```

## 最佳实践

### 保存中间结果

每次训练后保存：
- `result.csv`：原始推理结果
- `processed_result.csv`：后处理结果
- `score.json`：评分结果
- `processed_result_thr*.csv`：不同阈值的结果
- `score_thr*.json`：不同阈值的评分

### 保留历史

- 每次训练使用新的 `run_name`
- 不要覆盖历史结果
- 保存"当前最佳 run + 最佳阈值"

### 监控进度

关注以下指标：
- 混淆矩阵：哪些样本被误分
- 阈值敏感度：调整阈值是否能改善结果
- 负样本贡献：哪些负样本对区分有帮助
