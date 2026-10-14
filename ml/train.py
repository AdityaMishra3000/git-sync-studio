import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
import joblib
import os

# Create dummy historical dataset
# Features: changed_files, additions, deletions, title_length, body_length
np.random.seed(42)
n_samples = 100
changed_files = np.random.randint(1, 50, n_samples)
additions = changed_files * np.random.randint(10, 100, n_samples)
deletions = changed_files * np.random.randint(5, 50, n_samples)
title_length = np.random.randint(10, 100, n_samples)
body_length = np.random.randint(0, 1000, n_samples)

X = pd.DataFrame({
    'changed_files': changed_files,
    'additions': additions,
    'deletions': deletions,
    'title_length': title_length,
    'body_length': body_length
})

# Labels: 1 if merged, 0 if closed
# Probability is higher if fewer changed files and additions
logits = -0.05 * changed_files - 0.001 * additions + 0.005 * title_length
probs = 1 / (1 + np.exp(-logits))
y = (np.random.rand(n_samples) < probs).astype(int)

model = LogisticRegression()
model.fit(X, y)

os.makedirs('ml/artifacts', exist_ok=True)
joblib.dump(model, 'ml/artifacts/model.joblib')
print("Model trained and saved to ml/artifacts/model.joblib")
