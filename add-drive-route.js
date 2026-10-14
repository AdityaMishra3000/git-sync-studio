const fs = require('fs');
const path = require('path');

const apiPath = path.join(__dirname, 'apps/api/app/drive/router.py');
let code = fs.readFileSync(apiPath, 'utf-8');

if (!code.includes('@router.get("")')) {
  const newRoute = `
@router.get("")
async def list_large_objects(session: AsyncSession = Depends(get_db_session)) -> list[dict]:
    from sqlalchemy import select
    from app.db.models import LargeObject, DriveObject
    result = await session.execute(select(LargeObject))
    objects = result.scalars().all()
    
    out = []
    for obj in objects:
        drive_res = await session.execute(select(DriveObject).where(DriveObject.large_object_id == obj.id))
        drive = drive_res.scalar_one_or_none()
        out.append({
            "id": str(obj.id),
            "repository_id": str(obj.repository_id),
            "oid": obj.oid,
            "size_bytes": obj.size_bytes,
            "path": obj.path,
            "drive_status": "synced" if drive else "pending",
            "created_at": obj.created_at.isoformat(),
        })
    return out
`;
  code = code + newRoute;
  fs.writeFileSync(apiPath, code);
}
console.log("Added GET route to drive router.");
