# Td-salt candidate comparison

## Summary

`new-Td-salt` is the later and more relevant baseline, but neither directory is a maintainable or reproducible software project. The new directory contributes corrected labels and a fixed-pentazolate/cation-focused modeling hypothesis; `ion_Td` must rebuild the executable pipeline rather than rename or copy either candidate.

## Evidence

| Property | Td-salt | new-Td-salt | Assessment |
|---|---:|---:|---|
| Approximate size | 244 MB | 160 MB | Most size is a duplicated xTB binary distribution and run outputs. |
| Labeled rows | 36 | 36 | Same compounds/references. |
| `salt36` Tdec | −94 °C | +94 °C | New directory corrects a likely sign/transcription error. |
| Selected SOAP features | 897, 844, 333, 359, 364 | 274, 948, 123, 32, 950 | Model lineage changed. |
| Best recorded deterministic model | GBDT R² 0.363, MAE 5.348 °C | GBDT R² 0.400, MAE 6.755 °C | Metrics are not directly comparable because descriptors/geometries and one label changed. |
| Best recorded RF | R² 0.344, MAE 5.992 °C | R² 0.384, MAE 6.777 °C | New R² improves; MAE worsens. RF artifacts have `random_state=None`. |
| Extra scenarios | General two-ion scripts and source PDFs | Null/fixed N5 anion handling and LightGBM evaluation | New is explicitly specialized to pentazolate salts. |
| Tests/package metadata | None | None | Both require reconstruction. |

## Reproducibility defects shared by the candidates

- Random RDKit embedding and random ion separation without recorded seeds.
- xTB formal charge is not passed, despite cations carrying +1 charge.
- xTB subprocess uses `check=False`; exceptions and missing outputs are converted into prints/returns.
- Hard-coded developer and project paths.
- Files are selected using unsorted `os.listdir()` and index `[0]`.
- Optimization helpers move broad filename patterns from the current directory.
- Training uses unseeded random forests and persisted sklearn joblib artifacts from older versions.
- No tests, package metadata, dependency lock, model card, provenance manifest, or applicability-domain checks.

## SOAP/model defect

The stored structures contain different element sets, so dynamic SOAP dimensions vary:

- H/N sample: 952 features;
- C/H/N sample: 2100 features;
- C/H/N/O sample: 3696 features.

The scripts nevertheless force 3696 columns and use `soap[0]`, the local environment of the first atom. Recomputed selected features fail to reproduce the stored training CSV for multiple samples. The saved model therefore cannot be treated as a reproducible production artifact.

## Rebuild decision

Use the corrected `new-Td-salt/Td_salt.csv` as the authoritative 36-row label/reference table and preserve both candidates as legacy archives. Rebuild geometry and features with fixed seeds, explicit charge, isolated xTB workspaces, fixed CHNO species, molecularly averaged SOAP, deterministic model selection, strict output checks, and an explicit fixed-pentazolate applicability boundary.

## Rebuild outcome

All 36 charged xTB optimizations and fixed 3696-dimensional molecular SOAP vectors were rebuilt
deterministically. Strict leakage-free Leave-One-Out showed that this corrected global SOAP representation
did not generalize (best tested R² was approximately −0.03). Complete deterministic RDKit descriptors plus
a Morgan fingerprint performed better and became the honest default: R² 0.190633, MAE 8.040509 °C,
RMSE 9.918835 °C, with a 90% empirical half-width of 17.305399 °C. The low score is retained in every
prediction; no historical score or incompatible joblib is presented as current evidence.
