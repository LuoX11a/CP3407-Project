# 模型更新 — 2026年7月

## 新模型性能

| 指标 | 旧模型 (7/6) | 新模型 (7/27) | 提升 |
|---|---|---|---|
| 训练数据 | ~446K 行 | **607,480 行** | +36% |
| 停车场数 | ~1,994 | **1,997** | — |
| Non-EPS | 31 个 | **0** | 全部覆盖 |
| CV MAE | 0.0708 | **0.0705** | — |
| CV RMSE | 0.1093 | **0.1101** | — |
| Hold-out R² | — | **0.7075** | — |

---

## 操作步骤

### 1. 复制文件
把这个文件夹里的内容覆盖到仓库根目录。只需覆盖 `ml/` 目录下的文件。

### 2. 提交
```bash
git add ml/
git commit -m "feat: retrain LightGBM model with July 2026 backfilled data

- 607,480 training rows, 1,997 carparks (2 months window)
- CV MAE: 0.0705, Hold-out R-squared: 0.7075
- Zero non-EPS carparks (all have valid availability data)"
```

### 3. 推送
```bash
git push origin develop
```
