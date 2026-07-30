"""
AdviserOS — Report Router
GET /api/v1/report/{client_id}/pdf
GET /api/v1/report/{client_id}/email
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.report_generator import generate_email, generate_report

router = APIRouter(prefix="/report", tags=["Reports & Emails"])


@router.get("/{client_id}/pdf", summary="Generate PDF suitability report")
async def get_pdf_report(client_id: int, db: AsyncSession = Depends(get_db)):
    """
    Generates a professional PDF suitability report for the client
    and returns it as a downloadable file.
    Run POST /analyse/{client_id} first to generate the analysis.
    """
    try:
        result = await generate_report(client_id, db)
        return FileResponse(
            path        = result["pdf_path"],
            media_type  = "application/pdf",
            filename    = result["filename"],
            headers     = {"Content-Disposition": f'attachment; filename="{result["filename"]}"'},
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")


@router.get("/{client_id}/email", summary="Generate client email draft")
async def get_email_draft(client_id: int, db: AsyncSession = Depends(get_db)):
    """
    Generates a warm, professional client email summarising
    the top 3 findings and recommendations.
    Run POST /analyse/{client_id} first to generate the analysis.
    """
    try:
        result = await generate_email(client_id, db)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Email generation failed: {str(e)}")
