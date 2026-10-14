from fastapi import APIRouter, Depends
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
