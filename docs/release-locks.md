# 发布锁定与部署预检

`delivery/release-manifest.json` 使用统一 schema 1，提供两个独立 profile：

- `cpu`：训练集、来源清单、模型卡、源码、精确依赖版本、实时严格 LOO 和域内预测；
- `geometry`：几何源码、RDKit/DScribe 和固定的 xTB 6.7.1 二进制。

对应锁文件：

- `delivery/locks/cpu.json`
- `delivery/locks/geometry.json`

运行：

```bash
python scripts/release_preflight.py --profile cpu --json
python scripts/release_preflight.py --profile geometry --json
python scripts/release_preflight.py --profile geometry --geometry-smoke run --json
```

最后一条命令会在自动删除的临时目录执行一次真实 hydroxylammonium
RDKit→xTB 优化，不污染仓库。

## 科学基线核验

任务开始前已存在未提交的 `model_card.json` 指标改动。模型卡声明的精确环境是
Python 3.12.10、NumPy 2.2.6、RDKit 2025.03.5、scikit-learn 1.8.0；在该环境实时
重算 LOO 得到的指标与原 Git HEAD 完全一致。先前未提交的数值与复算不符，
已经单独保存于本次交付归档；发布版模型卡记录可复现的指标。

冻结版清单状态为 `frozen`，其中 `source_revision.commit` 指向已测试的源码提交：

- 所有文件哈希仍可验证；
- CPU preflight 的实时 LOO 与模型卡严格一致；
- geometry profile 独立通过；
- 如需恢复先前的候选指标，须同时提供可重现的训练数据、代码和环境依据。
