# ml/

Offline machine learning for the pull request predictor. **PHASE 3.** Empty until
PHASE 2 has ingested real pull request history - there is nothing to train on
before that.

Planned layout:

```text
datasets/     built datasets (git-ignored; rebuildable from PostgreSQL)
features/     feature extraction, shared with app/prediction at serving time
training/     training entrypoints, temporal split, model selection
evaluation/   metrics, calibration curves, per-repository error analysis
models/       versioned artefacts (git-ignored; joblib + a metadata json)
notebooks/    exploration only - nothing here is imported by the application
```

Two constraints that are not negotiable:

**Temporal splits, never random.** Older pull requests train, later ones
validate, the newest ones test. A random split lets a repository's future
behaviour leak into training and inflates every metric, which is exactly the kind
of result that falls apart in a demo.

**Creation-time features stay separate from live-state features.** A model that
predicts "will this merge?" at open time must not see review comments that only
exist later. Mixing them produces a model that scores well and predicts nothing.

Serving lives in `apps/api/app/prediction`; feature extraction is shared so
training and serving cannot compute a feature two different ways.
