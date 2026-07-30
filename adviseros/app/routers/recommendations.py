from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.models import Client, Recommendation
from app.schemas.schemas import (
    RecommendationCreate, RecommendationResponse, RecommendationUpdate,
)

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


@router.post("/", response_model=RecommendationResponse, status_code=status.HTTP_201_CREATED)
async def create_recommendation(
    payload: RecommendationCreate, db: AsyncSession = Depends(get_db)
):
    client = await db.get(Client, payload.client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    rec = Recommendation(**payload.model_dump())
    db.add(rec)
    await db.flush()
    await db.refresh(rec)
    return rec


@router.get("/", response_model=list[RecommendationResponse])
async def list_recommendations(
    client_id: int | None = None,
    skip: int = 0, limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    q = select(Recommendation).offset(skip).limit(limit)
    if client_id:
        q = q.where(Recommendation.client_id == client_id)
    result = await db.scalars(q)
    return result.all()


@router.get("/{rec_id}", response_model=RecommendationResponse)
async def get_recommendation(rec_id: int, db: AsyncSession = Depends(get_db)):
    rec = await db.get(Recommendation, rec_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    return rec


@router.patch("/{rec_id}", response_model=RecommendationResponse)
async def update_recommendation(
    rec_id: int, payload: RecommendationUpdate, db: AsyncSession = Depends(get_db)
):
    rec = await db.get(Recommendation, rec_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(rec, field, value)
    await db.flush()
    await db.refresh(rec)
    return rec
