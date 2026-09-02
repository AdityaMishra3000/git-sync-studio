"""Pull request merge/timing prediction serving layer.

Reserved for PHASE 3. Loads versioned model artefacts produced under ``ml/`` and
serves advisory predictions (probability, time bucket, confidence, reasons).
Predictions are advisory only - never an automatic accept/reject decision.
"""
