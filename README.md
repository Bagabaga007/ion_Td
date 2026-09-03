# ion_Td

HEMERA/BPPA 的热分解温度实验性评估模块。它从两个历史脚本目录重建而来，提供可安装
Python 包、命令行、确定性训练、适用域检查、不确定性区间和隔离 xTB 优化。

## 重要科学边界

当前训练集只有 36 条数据，且全部是“单价 CHNO 阳离子＋五唑阴离子”盐。严格留一法：

| 指标 | 数值 |
|---|---:|
| R² | 0.1906 |
| MAE | 8.0405 °C |
| RMSE | 9.9188 °C |
| 90% 留一残差区间半宽 | 17.3054 °C |

因此本模块是**筛选级实验模型**，不是发表级或安全决策级定量模型。非五唑阴离子、非 +1
阳离子、CHNO 之外元素或低训练集相似度默认拒绝；可以显式允许外推，但结果会携带警告，
且区间不再有域内含义。

## 安装

```bash
pip install -e ".[dev]"
```

默认预测只依赖 RDKit/scikit-learn，不要求 xTB。研究性 3D/SOAP 功能需要 `.[geometry]`
和外部 xTB 可执行文件；不再把 159 MB 第三方二进制复制进项目。

当前工作区共享的已验证版本为 `/workplace/home/yangze/packages/xtb-6.7.1/bin/xtb`，
可执行文件 SHA-256 为
`debf27a9e0fa4bfb5ca75aafe4b90d8211f08ec2f4a482f375a4987212eaa12a`。

## 预测

```bash
ion-td predict --config examples/prediction.yaml

ion-td predict \
  --name hydroxylammonium-pentazolate \
  --cation '[NH3+]O' \
  --anion 'N1=NN=N[N-]1' \
  --output result.json
```

输出包括预测温度、90% 经验区间、树间标准差、最大 Morgan/Tanimoto 相似度、是否域内、
警告和模型留一法指标。

## 模型复验

```bash
ion-td validate
ion-td show-data
```

`validate` 从打包的 `training.csv` 重新构造全部 RDKit 描述符和 Morgan 指纹，重新执行
严格 Leave-One-Out，不读取不兼容的历史 joblib。

## 确定性 xTB 优化

```bash
export ION_TD_XTB=/workplace/home/yangze/packages/xtb-6.7.1/bin/xtb
ion-td optimize \
  --name hydroxylammonium \
  --cation '[NH3+]O' \
  --output-dir ./work \
  --seed 20260903
```

每个任务使用独立目录；显式向 xTB 传递 RDKit 形式电荷；要求退出码为零、`.xtboptok`
和非空 `.xtbopt.xyz`。不会扫描或移动调用者工作目录中的其他文件。

## 测试

```bash
pytest -q
pytest -q -m unit
pytest -q -m integration
pytest -q -m config
pytest -q -m system
pytest -q --cov=ion_td --cov-branch --cov-report=term-missing --cov-fail-under=100
ruff check src tests
python -m build
```

## 数据与历史

- `src/ion_td/data/training.csv`：选择自 new-Td-salt 的修正 36 条数据；SHA-256 和 DOI
  见 `source_manifest.json`。
- `model_card.json`：模型、特征、验证、适用域和限制。
- [候选比较](docs/candidate-comparison.md)：说明为何不直接复制历史 SOAP/joblib。
- 两个原候选的完整可恢复归档位于
  `/workplace/home/yangze/archive/HEMERA_legacy/20260903/`。
