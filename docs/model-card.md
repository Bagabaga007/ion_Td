# Model card: rdkit-rf-pentazolate-v1

## Intended use

Rank or screen thermal-decomposition onset temperatures for salts whose anion is pentazolate and whose
cation is monovalent and contains only H/C/N/O. Always report the interval and applicability fields.

## Model

All RDKit descriptors available in the runtime version (sorted by descriptor name) plus a 512-bit Morgan
fingerprint (radius 2), followed by median imputation, variance filtering and a deterministic 500-tree
random forest (`random_state=42`, `max_features=0.5`, `min_samples_leaf=2`). The estimator is trained at
runtime from the packaged CSV, avoiding unsafe/incompatible joblib deserialization.

## Validation

Strict Leave-One-Out over all preprocessing and estimator fitting: R² 0.190633, MAE 8.040509 °C,
RMSE 9.918835 °C. The 90% finite-sample absolute-residual quantile is 17.305399 °C and is reported as a
symmetric empirical interval for in-domain inputs.

## Limitations

The dataset is too small for claims of broad generalization. It contains one anion only, and does not
encode crystal packing, heating rate, sample purity, polymorph or measurement-laboratory effects. A low
R² means the point estimate should not be used alone. Out-of-domain override is for research diagnostics,
not for safety, synthesis or procurement decisions.
