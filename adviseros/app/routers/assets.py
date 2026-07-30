from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.models import Asset
from app.schemas.schemas import AssetCreate, AssetResponse, AssetUpdate

router = APIRouter(prefix="/assets", tags=["Assets"])


@router.post("/", response_model=AssetResponse, status_code=status.HTTP_201_CREATED)
async def create_asset(payload: AssetCreate, db: AsyncSession = Depends(get_db)):
    asset = Asset(**payload.model_dump())
    db.add(asset)
    await db.flush()
    await db.refresh(asset)
    return asset


@router.get("/", response_model=list[AssetResponse])
async def list_assets(
    skip: int = 0, limit: int = 100, asset_class: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    q = select(Asset).where(Asset.is_active.is_(True)).offset(skip).limit(limit)
    if asset_class:
        q = q.where(Asset.asset_class == asset_class)
    result = await db.scalars(q)
    return result.all()


@router.get("/{asset_id}", response_model=AssetResponse)
async def get_asset(asset_id: int, db: AsyncSession = Depends(get_db)):
    asset = await db.get(Asset, asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset


@router.patch("/{asset_id}", response_model=AssetResponse)
async def update_asset(asset_id: int, payload: AssetUpdate, db: AsyncSession = Depends(get_db)):
    asset = await db.get(Asset, asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(asset, field, value)
    await db.flush()
    await db.refresh(asset)
    return asset
