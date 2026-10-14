from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.readme.extract import extract_evidence, generate_readme

router = APIRouter(prefix="/readme", tags=["readme"])


class GenerateRequest(BaseModel):
    repo_path: str


@router.post("/generate")
async def generate_readme_endpoint(req: GenerateRequest) -> dict:
    path = Path(req.repo_path)
    if not path.exists():  # noqa: ASYNC240
        raise HTTPException(status_code=404, detail="Repo path not found in container")

    evidence = extract_evidence(path)
    draft = generate_readme(evidence)

    warnings = []
    if not evidence.get("tests"):
        warnings.append({"type": "MISSING_EVIDENCE", "message": "No tests found."})

    return {"draft": draft, "warnings": warnings, "evidence": evidence}

class SaveRequest(BaseModel):
    repo_path: str
    content: str

@router.post("/save")
async def save_readme(req: SaveRequest):
    p = Path(req.repo_path)
    if not p.exists():
        raise HTTPException(status_code=404, detail="Repository path not found")
    readme_path = p / "README.md"
    readme_path.write_text(req.content)
    return {"status": "success", "message": "README.md saved to repository"}
