import re

router_path = "apps/api/app/readme/router.py"
with open(router_path, "r") as f:
    code = f.read()

save_logic = """
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
"""

if "class SaveRequest" not in code:
    code += save_logic
    with open(router_path, "w") as f:
        f.write(code)

print("Readme backend save endpoint added.")
