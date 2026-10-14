const fs = require('fs');
const path = require('path');

const apiPath = path.join(__dirname, 'apps/api/app/repos/router.py');
let code = fs.readFileSync(apiPath, 'utf-8');

if (!code.includes('/{repo_id}/prs')) {
  const insertIndex = code.lastIndexOf('@router.');
  const newRoute = `
@router.get("/{repo_id}/prs")
async def list_prs(repo_id: UUID, session: AsyncSession = Depends(get_db_session)) -> list[dict]:
    from sqlalchemy import select
    from app.db.models import PullRequest
    result = await session.execute(select(PullRequest).where(PullRequest.repository_id == repo_id))
    prs = result.scalars().all()
    return [{"id": str(pr.id), "title": pr.title, "state": pr.state, "author": pr.author, "additions": pr.additions, "deletions": pr.deletions, "changed_files": pr.changed_files} for pr in prs]
`;
  code = code.substring(0, insertIndex) + newRoute + code.substring(insertIndex);
  fs.writeFileSync(apiPath, code);
}
console.log("Added PR route to repos router.");
