# ion_Td 项目简介与主题

## 一句话定位

`ion_Td` 是 HEMERA/BPPA 的热分解温度筛选模块：用可复现的 RDKit/Morgan 特征、固定随机
森林、训练域门禁和经验不确定性区间，对五唑离子盐候选进行早期筛选。

## 主题关键词

`energetic-materials`, `thermal-decomposition`, `pentazolate`, `RDKit`, `scikit-learn`,
`xTB`, `cheminformatics`, `uncertainty-quantification`, `HEMERA`。

## 输入与输出

- 输入：阳离子 SMILES、五唑阴离子 SMILES、YAML 配置，以及可选 xTB 可执行文件。
- 中间过程：描述符/指纹重建、模型适用域检查、严格 Leave-One-Out 复验和可选确定性 xTB 优化。
- 输出：预测温度、经验区间、树间标准差、最大 Tanimoto 相似度、warnings、优化 XYZ 和完整日志。

## 两条使用路径

1. [预测案例](../examples/README.md)：不需要 xTB 或网络，验证模型和域内输出。
2. [完整使用指南](usage.md)：模型复验、诊断性外推、隔离 xTB 工件和失败处理。

## 科学边界

当前训练集只有 36 条“单价 CHNO 阳离子 + 五唑阴离子”盐记录。非五唑、非 +1、含域外
元素或低相似度输入默认拒绝；`--allow-out-of-domain` 只能用于明确标记的诊断性外推。
预测结果不用于安全、采购、合成或发表级定量结论。
