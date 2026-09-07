# ion_Td project analysis

Generated for the HEMERA architecture review on 2026-09-03. The candidate comparison is in
[docs/candidate-comparison.md](docs/candidate-comparison.md); the aggregate HEMERA view is
[HEMERA/BPPA/ion_Td_ANALYSIS.md](/workplace/home/yangze/HEMERA/BPPA/ion_Td_ANALYSIS.md).

## Identity and scope

- Package: `ion-td 0.1.0`, Python >=3.10, src-layout under `src/ion_td`.
- Scope: thermal-decomposition onset screening for monovalent CHNO cations paired with the pentazolate
  anion; deterministic RDKit/Morgan model; applicability and uncertainty output; optional xTB/SOAP geometry.
- Operable examples: `examples/run_prediction.py` and `examples/prediction.yaml` provide a
  no-network prediction path; `docs/usage.md` documents model validation and the optional xTB path.
- GitHub: <https://github.com/Bagabaga007/ion_Td>, branch `main`; the current verified SHA is
  maintained in the HEMERA `system.json` manifest to avoid stale self-references in this report.
- Training data: corrected 36-row new-Td-salt baseline, including `salt36=+94 °C`.

## Verification snapshot

- 30 pytest tests across unit/integration/config/system.
- 409/409 Python statements and 78/78 branches covered.
- Ruff, real xTB 6.7.1 charged optimization, finite 3696-D molecular SOAP, sdist/wheel and isolated wheel
  prediction pass.
- Default deterministic model LOO: R² 0.190633, MAE 8.040509 °C, RMSE 9.918835 °C, empirical half-width
  17.305399 °C.

## Scientific boundary

The model is experimental screening only. The training set has one anion and 36 samples; non-pentazolate,
non-+1, non-CHNO or low-similarity inputs are rejected by default. Historical SOAP/joblib artifacts are
not used because their geometry/feature contract is not reproducible.

## Maintenance

Do not vendor the xTB binary or store model artifacts without provenance. Keep the shared validated xTB at
`/workplace/home/yangze/packages/xtb-6.7.1/bin/xtb`; record seeds, force-field status, xTB return code,
feature schema and model-card metrics for every new training lineage.
