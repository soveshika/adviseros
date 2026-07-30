from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.models import Client, Report
from app.schemas.schemas import ReportCreate, ReportResponse, ReportUpdate

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.post("/", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def create_report(payload: ReportCreate, db: AsyncSession = Depends(get_db)):
    client = await db.get(Client, payload.client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    report = Report(**payload.model_dump())
    db.add(report)
    await db.flush()
    await db.refresh(report)
    return report


@router.get("/", response_model=list[ReportResponse])
async def list_reports(
    client_id: int | None = None,
    skip: int = 0, limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    q = select(Report).offset(skip).limit(limit)
    if client_id:
        q = q.where(Report.client_id == client_id)
    result = await db.scalars(q)
    return result.all()


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(report_id: int, db: AsyncSession = Depends(get_db)):
    report = await db.get(Report, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.patch("/{report_id}", response_model=ReportResponse)
async def update_report(
    report_id: int, payload: ReportUpdate, db: AsyncSession = Depends(get_db)
):
    report = await db.get(Report, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(report, field, value)
    await db.flush()
    await db.refresh(report)
    return report


@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_report(report_id: int, db: AsyncSession = Depends(get_db)):
    report = await db.get(Report, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    await db.delete(report)
