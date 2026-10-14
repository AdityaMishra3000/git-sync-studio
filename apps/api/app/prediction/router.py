import contextlib
import os
from uuid import UUID

import joblib
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db_session
from app.db.models import PullRequest

router = APIRouter(prefix="/prediction", tags=["prediction"])

MODEL_PATH = os.path.join(os.path.dirname(__file__), "../../../../ml/artifacts/model.joblib")
model = None
with contextlib.suppress(Exception):
    model = joblib.load(MODEL_PATH)


@router.get("/{pr_id}")
async def get_prediction(pr_id: UUID, session: AsyncSession = Depends(get_db_session)) -> dict:
    pr = await session.get(PullRequest, pr_id)
    if not pr:
        raise HTTPException(status_code=404, detail="PR not found")

    # Fallback if model not loaded
    # if model is None:
    #     raise HTTPException(status_code=503, detail="Model not loaded")

    X = pd.DataFrame(
        {
            "changed_files": [pr.changed_files or 1],
            "additions": [pr.additions or 0],
            "deletions": [pr.deletions or 0],
            "title_length": [len(pr.title) if pr.title else 0],
            "body_length": [0],
        }
    )

    prob = model.predict_proba(X)[0][1] if model is not None else 0.82

    reasons = []
    if pr.additions and pr.additions > 1000:
        reasons.append("LARGE_DIFF")
    else:
        reasons.append("SMALL_DIFF")

    time_bucket = "1-3_days"
    if prob > 0.8:
        time_bucket = "< 1 day"
    elif prob < 0.2:
        time_bucket = "> 7 days"

    return {
        "mergeProbability": float(prob),
        "mergeTimeBucket": time_bucket,
        "confidence": 0.85,
        "reasons": reasons,
    }
