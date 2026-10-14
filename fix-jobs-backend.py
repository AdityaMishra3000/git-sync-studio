import re

router_path = "apps/api/app/jobs/router.py"
with open(router_path, "w") as f:
    f.write("""from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_db_session
from app.db.models import Job

router = APIRouter(prefix="/jobs", tags=["jobs"])

@router.get("")
async def list_jobs(session: AsyncSession = Depends(get_db_session)):
    result = await session.execute(select(Job).order_by(Job.created_at.desc()).limit(20))
    jobs = result.scalars().all()
    return [
        {
            "id": str(j.id),
            "name": j.name,
            "status": j.status,
            "created_at": j.created_at,
        }
        for j in jobs
    ]
""")

main_path = "apps/api/app/main.py"
with open(main_path, "r") as f:
    main_code = f.read()

main_code = main_code.replace("from app.readme.router import router as readme_router", "from app.readme.router import router as readme_router\nfrom app.jobs.router import router as jobs_router")
main_code = main_code.replace("v1.include_router(readme_router)", "v1.include_router(readme_router)\n    v1.include_router(jobs_router)")

with open(main_path, "w") as f:
    f.write(main_code)

print("Jobs API backend implemented.")
