"""
AdviserOS — Analysis Router
POST /api/v1/analyse/{client_id}
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.analysis import analyse_client

router = APIRouter(prefix="/analyse", tags=["AI Analysis"])


@router.post("/{client_id}", summary="Run AI financial analysis for a client")
async def run_analysis(client_id: int, db: AsyncSession = Depends(get_db)):
    """
    Fetches the full client profile, sends it to Claude,
    and returns a structured financial analysis saved to the reports table.
    """
    try:
        result = await analyse_client(client_id, db)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
