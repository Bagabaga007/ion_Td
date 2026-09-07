# ion_Td 可运行案例

本目录提供两条明确区分的路径：

- **模型预测（无外部量化程序）**：使用 36 条打包训练数据，在本地重建模型，输出预测温度、
  90% 经验区间、树间标准差、最大 Tanimoto 相似度和域内警告。
- **xTB 几何优化（可选外部程序）**：用 RDKit 生成确定性初始几何，再在隔离任务目录运行
  xTB；该步骤需要用户提供 `xtb` 可执行文件，不会被普通预测测试隐式调用。

## 1. 最短预测案例

在项目根目录安装后运行：

```bash
python -m pip install -e ".[dev]"
ion-td predict --config examples/prediction.yaml
python examples/run_prediction.py
```

也可以不使用 YAML：

```bash
ion-td predict \
  --name hydroxylammonium-pentazolate \
  --cation '[NH3+]O' \
  --anion 'N1=NN=N[N-]1' \
  --output work/hydroxylammonium.json
```

输出中的 `in_domain: true` 和 `maximum_tanimoto_similarity: 1.0` 是该训练域内示例的关键
检查项。温度为筛选级预测，不应当当作安全、采购、合成或发表级定量结论。

## 2. 模型复验和数据检查

```bash
ion-td validate
ion-td show-data
```

`validate` 每次从内置 `training.csv` 重建 RDKit/Morgan 特征并重新执行严格 Leave-One-Out；
`show-data` 显示记录数、温度范围和训练域阴离子。它们不读取历史 joblib，也不访问网络。

## 3. 确定性 xTB 优化

先确认 xTB 可执行文件：

```bash
export ION_TD_XTB=/workplace/home/yangze/packages/xtb-6.7.1/bin/xtb
"$ION_TD_XTB" --version
```

运行一个隔离优化任务：

```bash
mkdir -p work/xtb
ion-td optimize \
  --name hydroxylammonium \
  --cation '[NH3+]O' \
  --output-dir work/xtb \
  --seed 20260903 \
  --xtb "$ION_TD_XTB"
```

任务会创建 `work/xtb/hydroxylammonium/`，并产生：

```text
hydroxylammonium.xyz          # RDKit 确定性初始结构
hydroxylammonium.xtbopt.xyz   # xTB 优化结构
.hydroxylammonium.xtboptok    # 成功 marker
stdout.log / stderr.log       # 完整外部程序日志
```

程序显式传递阳离子形式电荷和 `--namespace`；只接受退出码为 0、marker 存在且优化 XYZ
非空的结果。若任务目录非空、xTB 找不到、超时或缺少 marker，命令失败并保留日志，避免
静默使用不完整结构。输出目录中的既有文件不会被覆盖。

## 4. 适用域和外推

训练集域为“单价 CHNO 阳离子 + 五唑阴离子”。以下任一条件会拒绝默认预测：

- 阴离子不是训练集五唑阴离子；
- 阳离子形式电荷不是 `+1`；
- 含 C/H/N/O 之外元素；
- 最大 Tanimoto 相似度低于模型卡阈值。

确实要做诊断性外推时必须显式增加 `--allow-out-of-domain`，输出会保留 `warnings`，并将
`in_domain` 标为 `false`。外推区间不具有训练域覆盖含义：

```bash
ion-td predict \
  --name diagnostic-only \
  --cation '[Na+]' \
  --allow-out-of-domain \
  --output work/diagnostic.json
```

不要为了得到一个数字而忽略警告。

## 5. 配置和结果字段

`examples/prediction.yaml`：

```yaml
name: hydroxylammonium-pentazolate
SMILES:
  cation: "[NH3+]O"
  anion: "N1=NN=N[N-]1"
allow_out_of_domain: false
```

结果 JSON 关键字段：

| 字段 | 含义 |
|---|---|
| `temperature_c` | 随机森林预测的热分解温度（°C） |
| `interval_low_c`/`interval_high_c` | 基于严格 LOO 残差的 90% 经验区间 |
| `tree_std_c` | 森林树间标准差，仅作模型不确定性信号 |
| `maximum_tanimoto_similarity` | 与训练阳离子指纹的最大相似度 |
| `in_domain` | 是否满足训练域门禁 |
| `warnings` | 外推、元素、电荷、阴离子或相似度警告 |
| `validation` | n、R²、MAE、RMSE 和经验区间半宽 |

## 6. 目录、排错与复验

```text
work/
├── hydroxylammonium.json  # 预测输出（可选）
└── xtb/hydroxylammonium/  # 隔离 xTB 工件和日志
```

- `ModuleNotFoundError: ion_td`：从项目根执行，或使用 `PYTHONPATH=src python -m ion_td`；
  安装后优先使用 `ion-td`。
- `找不到 xTB`：设置 `ION_TD_XTB` 或传递 `--xtb /absolute/path/to/xtb`。
- 预测被拒绝：先阅读异常中的适用域警告；只有研究性诊断才显式使用
  `--allow-out-of-domain`。
- xTB 失败：检查 `stderr.log`、退出码、内存/线程资源和输入电荷；不要删除失败目录。

## 7. 四层测试和构建

```bash
PYTHONPATH=src python -m pytest -q
PYTHONPATH=src python -m pytest -q -m unit
PYTHONPATH=src python -m pytest -q -m integration
PYTHONPATH=src python -m pytest -q -m config
PYTHONPATH=src python -m pytest -q -m system
PYTHONPATH=src python -m pytest -q --cov=ion_td --cov-branch --cov-report=term-missing
python -m build
```

普通测试不会调用真实 xTB；系统测试使用受控可执行 stub 覆盖成功和失败门禁。真实 xTB
运行应作为单独的研究任务记录版本、路径、seed、输入结构和完整日志。
