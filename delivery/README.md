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

## Verified scientific baseline

The earlier uncommitted `model_card.json` metrics did not match live LOO in their
declared environment. The original file is preserved in the delivery archive.
The frozen model card records the reproducible LOO result. Consequently:

- training CSV, model card, code, environment, and live LOO are bound together;
- `cpu.model_card_live_loo` and the CPU profile pass in the locked environment;
- geometry passes independently after xTB visibility and hash checks.

The frozen manifest records the tested source commit; the release tag points to
the following manifest commit. Reinstating the earlier candidate metrics requires
their own reproducible training data, code, and environment evidence.
