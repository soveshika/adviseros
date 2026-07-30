from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.models import Asset, Client, Investment
from app.schemas.schemas import InvestmentCreate, InvestmentResponse, InvestmentUpdate

router = APIRouter(prefix="/investments", tags=["Investments"])


async def _resolve_refs(client_id: int, asset_id: int, db: AsyncSession):
    client = await db.get(Client, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    asset = await db.get(Asset, asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return client, asset


@router.post("/", response_model=InvestmentResponse, status_code=status.HTTP_201_CREATED)
async def create_investment(payload: InvestmentCreate, db: AsyncSession = Depends(get_db)):
    await _resolve_refs(payload.client_id, payload.asset_id, db)
    inv = Investment(**payload.model_dump())
    db.add(inv)
    await db.flush()
    await db.refresh(inv)
    return inv


@router.get("/", response_model=list[InvestmentResponse])
async def list_investments(
    client_id: int | None = None,
    skip: int = 0, limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    q = select(Investment).offset(skip).limit(limit)
    if client_id:
        q = q.where(Investment.client_id == client_id)
    result = await db.scalars(q)
    return result.all()


@router.get("/{investment_id}", response_model=InvestmentResponse)
async def get_investment(investment_id: int, db: AsyncSession = Depends(get_db)):
    inv = await db.get(Investment, investment_id)
    if not inv:
        raise HTTPException(status_code=404, detail="Investment not found")
    return inv


@router.patch("/{investment_id}", response_model=InvestmentResponse)
async def update_investment(
    investment_id: int, payload: InvestmentUpdate, db: AsyncSession = Depends(get_db)
):
    inv = await db.get(Investment, investment_id)
    if not inv:
        raise HTTPException(status_code=404, detail="Investment not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(inv, field, value)
    await db.flush()
    await db.refresh(inv)
    return inv


@router.delete("/{investment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_investment(investment_id: int, db: AsyncSession = Depends(get_db)):
    inv = await db.get(Investment, investment_id)
    if not inv:
        raise HTTPException(status_code=404, detail="Investment not found")
    await db.delete(inv)
