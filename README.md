# ion_Td

HEMERA/BPPA 的热分解温度实验性评估模块。它从两个历史脚本目录重建而来，提供可安装
Python 包、命令行、确定性训练、适用域检查、不确定性区间和隔离 xTB 优化。

> 面向含能材料候选筛选的可复现温度评估管线：从 RDKit/ Morgan 特征和确定性随机森林预测，
> 到适用域警告、严格 LOO 指标、经验区间和可选 xTB 结构工件。

**主题关键词**：`energetic-materials` · `thermal-decomposition` · `pentazolate` ·
`RDKit` · `scikit-learn` · `xTB` · `cheminformatics` · `uncertainty-quantification` · `HEMERA`

| 你要做什么 | 推荐入口 | 主要产物 |
|---|---|---|
| 先验证安装和模型 | [预测案例](examples/README.md) | 温度、90% 经验区间、相似度和 warnings |
| 复算训练域指标 | `ion-td validate` | 严格 Leave-One-Out 指标 |
| 检查训练数据范围 | `ion-td show-data` | 记录数、温度范围、固定阴离子 |
| 生成可复查结构 | [xTB 操作指南](docs/usage.md) | 初始/优化 XYZ、marker 和完整日志 |

本项目是筛选级实验模型，不是安全、采购、合成或发表级定量工具；训练域只有 36 条
“单价 CHNO 阳离子 + 五唑阴离子”盐记录，域外输入默认拒绝。

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

# 等价的模块入口；适合源码目录或调试环境
PYTHONPATH=src python -m ion_td predict --config examples/prediction.yaml

ion-td predict \
  --name hydroxylammonium-pentazolate \
  --cation '[NH3+]O' \
  --anion 'N1=NN=N[N-]1' \
  --output result.json
```

完整的逐步操作说明见 [`docs/usage.md`](docs/usage.md)，可运行案例见
[`examples/README.md`](examples/README.md) 和 `examples/run_prediction.py`。
项目定位、主题关键词和输入/输出契约见 [`docs/project-profile.md`](docs/project-profile.md)。

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

这一步是可选的真实外部程序工作流；没有 xTB 时仍可运行预测、`validate` 和 `show-data`。
完整的 xTB 输入、输出工件和失败处理说明见 [`docs/usage.md`](docs/usage.md)。

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
