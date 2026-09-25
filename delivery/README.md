# ion_Td release locks

`release-manifest.json` exposes two independent acceptance profiles:

- `cpu`: training/source/model-card hashes, package source, exact validated
  dependencies, live strict leave-one-out metrics, and a prediction smoke test;
- `geometry`: geometry source/dependencies and the pinned xTB 6.7.1 executable.

Run them independently:

```bash
python scripts/release_preflight.py --profile cpu --json
python scripts/release_preflight.py --profile geometry --json
python scripts/release_preflight.py --profile geometry --geometry-smoke run --json
```

The geometry `run` mode performs one bounded hydroxylammonium RDKit→xTB
optimization in an automatically removed temporary directory. It never writes to
the repository.

## Current scientific blocker

The existing uncommitted edit to `src/ion_td/data/model_card.json` is intentionally
preserved. Its validation values do not equal live LOO under the exact environment
declared in that model card. Live LOO reproduces the Git HEAD values instead.
Consequently:

- artifact integrity can still pass because the manifest records the observed file;
- `cpu.model_card_live_loo` must fail and the command must exit 1;
- geometry can pass independently;
- this candidate is not a releasable model until the owner supplies provenance for
  the modified metrics or authorizes restoring the reproducible baseline.

The manifest therefore reports `blocked_model_card_conflict`; it does not present
the dirty working tree as a clean release.
