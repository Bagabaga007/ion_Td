# ion_Td 使用指南

`ion_Td` 是 HEMERA/BPPA 的热分解温度筛选模块。本文档按“安装 → 离线预测 → 模型复验
→ 可选 xTB → 适用域审查”的顺序给出可复制命令。项目不会自动连接网络或远程服务器；
真实 xTB 任务只有显式执行 `optimize` 时才会启动。

## 1. 安装和入口

推荐使用隔离环境并安装开发依赖：

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
ion-td --help
```

源码目录未安装时，也可以从项目根运行：

```bash
PYTHONPATH=src python -m ion_td --help
```

预测和模型验证不需要 xTB。只有 3D/SOAP 或 `optimize` 才需要额外的 `.[geometry]` 和
外部 xTB 可执行文件。

## 2. 最短可运行预测

使用仓库中的五唑肼/羟胺阳离子示例：

```bash
ion-td predict --config examples/prediction.yaml
python examples/run_prediction.py
```

不使用 YAML 时：

```bash
ion-td predict \
  --name hydroxylammonium-pentazolate \
  --cation '[NH3+]O' \
  --anion 'N1=NN=N[N-]1' \
  --output work/hydroxylammonium.json
```

JSON 中至少应检查：

```text
in_domain = true
maximum_tanimoto_similarity = 1.0  # 当前示例与训练域记录相同
warnings = []
```

预测温度及区间由当前打包模型确定，安装环境和随机种子均已固定；不要把区间解释成实验
误差条，更不能把筛选级结果直接用于安全或工艺决策。

## 3. 模型复验

```bash
ion-td validate
ion-td show-data
```

`validate`：从 `src/ion_td/data/training.csv` 重建描述符，使用严格 Leave-One-Out，
输出 `n`、R²、MAE、RMSE 和 90% 残差经验半宽。`show-data`：输出记录数、训练温度范围和
固定的五唑阴离子 SMILES。两条命令都只使用本地打包数据，不读取历史 joblib。

如需审查数据来源、SHA-256 和模型限制，查看：

- `src/ion_td/data/source_manifest.json`
- `src/ion_td/data/model_card.json`
- `docs/model-card.md`
- `docs/candidate-comparison.md`

## 4. xTB 可选工作流

### 4.1 选择并验证 xTB

```bash
export ION_TD_XTB=/workplace/home/yangze/packages/xtb-6.7.1/bin/xtb
"$ION_TD_XTB" --version
```

若路径不同，使用 `--xtb /absolute/path/to/xtb`。不要把二进制复制进 Git 仓库，也不要在
配置中保存用户凭据。

### 4.2 运行隔离优化

```bash
mkdir -p work/xtb
ion-td optimize \
  --name hydroxylammonium \
  --cation '[NH3+]O' \
  --output-dir work/xtb \
  --seed 20260903 \
  --xtb "$ION_TD_XTB"
```

实现会：

1. 用 RDKit 加氢并按固定 seed 生成初始三维结构；
2. 使用 MMFF，若参数不完整则回退 UFF；
3. 在 `work/xtb/hydroxylammonium/` 中写入输入 XYZ；
4. 显式传递形式电荷、`--opt loose`、`--gfn 2` 和任务 namespace；
5. 要求 xTB 返回 0、`.xtboptok` 存在且优化 XYZ 非空。

成功工件：

```text
hydroxylammonium.xyz
hydroxylammonium.xtbopt.xyz
.hydroxylammonium.xtboptok
stdout.log
stderr.log
```

输出目录非空时命令拒绝覆盖；xTB 找不到、超时、非零退出或缺少 marker 时命令失败并保留
日志。优化结果目前是结构工件和后续 SOAP/人工检查输入，不会自动改变 `predict` 的模型
温度，也不应被误读为热分解温度计算本身。

## 5. 适用域门禁和诊断性外推

当前模型只训练于单价 CHNO 阳离子与五唑阴离子盐。默认情况下，以下情况会拒绝：

- 阴离子不是固定五唑阴离子；
- 阳离子形式电荷不是 `+1`；
- 出现 CHNO 之外元素；
- 最大 Morgan/Tanimoto 相似度低于模型阈值。

确实需要诊断性外推时，必须显式使用：

```bash
ion-td predict \
  --name diagnostic-only \
  --cation '[Na+]' \
  --allow-out-of-domain \
  --output work/diagnostic.json
```

结果会包含 `warnings` 并将 `in_domain` 置为 `false`。此时 90% 区间不再具有训练域覆盖
含义，不得用于筛选结论、采购、合成或安全决策。

## 6. 结果字段

| 字段 | 解释 |
|---|---|
| `temperature_c` | 随机森林预测热分解温度（°C） |
| `interval_low_c`、`interval_high_c` | 严格 LOO 残差形成的经验区间 |
| `tree_std_c` | 森林树间预测标准差 |
| `maximum_tanimoto_similarity` | 与训练阳离子指纹的最大相似度 |
| `in_domain` | 是否通过训练域门禁 |
| `warnings` | 阴离子、电荷、元素或相似度警告 |
| `validation` | 当前模型验证指标快照 |

## 7. 测试、构建和排错

```bash
PYTHONPATH=src python -m pytest -q
PYTHONPATH=src python -m pytest -q -m unit
PYTHONPATH=src python -m pytest -q -m integration
PYTHONPATH=src python -m pytest -q -m config
PYTHONPATH=src python -m pytest -q -m system
PYTHONPATH=src python -m pytest -q --cov=ion_td --cov-branch --cov-report=term-missing
python -m build
```

普通测试使用受控 xTB stub，不会调用真实外部程序。真实 xTB 运行应另外记录 xTB 版本、
二进制路径、seed、输入 SMILES、输出工件和日志。

- `ModuleNotFoundError`：从项目根运行，或设置 `PYTHONPATH=src`。
- `找不到 xTB`：设置 `ION_TD_XTB` 或传 `--xtb`。
- 适用域拒绝：阅读异常和 `warnings`，不要默认打开外推。
- 输出目录非空：换一个任务名/输出根，避免覆盖已有实验工件。
