from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func, case, select
from sqlalchemy.ext.asyncio import AsyncSession

from auth.security import get_current_user
from db.session import get_db_session
from models.user import User
from models.incoming_request import IncomingRequest
from models.batch import ExportBatch, ImportBatch
from schemas.stats import ResponseNetworkStats

router = APIRouter(
    prefix="/stats",
    tags=["Admin & Monitoring"]
)


@router.get("/", response_model=ResponseNetworkStats)
async def get_system_stats(
    db: Annotated[AsyncSession, Depends(get_db_session)]
):
    """
    Retrieves overall statistics for the Response Network.
    This is the main data source for the admin dashboard.
    """
    # 1. Get user stats (source of truth)
    user_stats_stmt = select(
        func.count(User.id).label("total_users"),
        func.count(case((User.is_active, 1))).label("active_users")
    )
    user_stats_result = (await db.execute(user_stats_stmt)).one()

    # 2. Get incoming request stats
    req_stats_stmt = select(
        func.count(IncomingRequest.id).label("total_incoming_requests"),
        func.count(case((IncomingRequest.status == 'processing', 1))).label("processing_requests"),
        func.count(case((IncomingRequest.status == 'completed', 1))).label("completed_requests"),
        func.count(case((IncomingRequest.status == 'failed', 1))).label("failed_requests"),
    )
    req_stats_result = (await db.execute(req_stats_stmt)).one()

    # 3. Get batch stats
    try:
        stmt = select(func.count(ExportBatch.id))
        result = await db.execute(stmt)
        export_batch_count = result.scalar() or 0
    except Exception:
        export_batch_count = 0

    try:
        stmt = select(func.count(ImportBatch.id))
        result = await db.execute(stmt)
        import_batch_count = result.scalar() or 0
    except Exception:
        import_batch_count = 0
    
    return ResponseNetworkStats(
        **user_stats_result._asdict(),
        **req_stats_result._asdict(),
        total_export_batches=export_batch_count or 0,
        total_import_batches=import_batch_count or 0,
    )