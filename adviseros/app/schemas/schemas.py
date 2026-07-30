"""
AdviserOS — Pydantic v2 Schemas (request / response)
"""

from datetime import datetime, date
from decimal import Decimal

from pydantic import BaseModel, EmailStr, Field, ConfigDict

from app.models.models import (
    AssetClass, InvestmentStatus, RecommendationStatus,
    RecommendationType, ReportType, RiskProfile,
)


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

class OrmBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Client schemas
# ---------------------------------------------------------------------------

class ClientCreate(BaseModel):
    first_name: str = Field(..., max_length=100)
    last_name: str = Field(..., max_length=100)
    email: EmailStr
    phone: str | None = None
    date_of_birth: date | None = None
    risk_profile: RiskProfile = RiskProfile.MODERATE
    investment_horizon_years: int | None = Field(None, ge=1, le=50)
    annual_income: Decimal | None = Field(None, ge=0)
    net_worth: Decimal | None = Field(None, ge=0)
    notes: str | None = None


class ClientUpdate(BaseModel):
    first_name: str | None = Field(None, max_length=100)
    last_name: str | None = Field(None, max_length=100)
    phone: str | None = None
    risk_profile: RiskProfile | None = None
    investment_horizon_years: int | None = Field(None, ge=1, le=50)
    annual_income: Decimal | None = None
    net_worth: Decimal | None = None
    notes: str | None = None
    is_active: bool | None = None


class ClientResponse(OrmBase):
    id: int
    first_name: str
    last_name: str
    email: str
    phone: str | None
    date_of_birth: date | None
    risk_profile: RiskProfile
    investment_horizon_years: int | None
    annual_income: Decimal | None
    net_worth: Decimal | None
    is_active: bool
    notes: str | None
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Asset schemas
# ---------------------------------------------------------------------------

class AssetCreate(BaseModel):
    ticker: str | None = Field(None, max_length=20)
    name: str = Field(..., max_length=255)
    asset_class: AssetClass
    exchange: str | None = Field(None, max_length=50)
    currency: str = Field("USD", max_length=10)
    current_price: Decimal | None = Field(None, ge=0)
    isin: str | None = Field(None, max_length=20)
    description: str | None = None


class AssetUpdate(BaseModel):
    name: str | None = Field(None, max_length=255)
    current_price: Decimal | None = Field(None, ge=0)
    price_updated_at: datetime | None = None
    description: str | None = None
    is_active: bool | None = None


class AssetResponse(OrmBase):
    id: int
    ticker: str | None
    name: str
    asset_class: AssetClass
    exchange: str | None
    currency: str
    current_price: Decimal | None
    price_updated_at: datetime | None
    isin: str | None
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Investment schemas
# ---------------------------------------------------------------------------

class InvestmentCreate(BaseModel):
    client_id: int
    asset_id: int
    quantity: Decimal = Field(..., gt=0)
    purchase_price: Decimal = Field(..., gt=0)
    purchase_date: date
    account_number: str | None = None
    notes: str | None = None


class InvestmentUpdate(BaseModel):
    quantity: Decimal | None = Field(None, gt=0)
    current_value: Decimal | None = None
    status: InvestmentStatus | None = None
    close_date: date | None = None
    close_price: Decimal | None = Field(None, gt=0)
    notes: str | None = None


class InvestmentResponse(OrmBase):
    id: int
    client_id: int
    asset_id: int
    quantity: Decimal
    purchase_price: Decimal
    purchase_date: date
    current_value: Decimal | None
    status: InvestmentStatus
    close_date: date | None
    close_price: Decimal | None
    account_number: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Recommendation schemas
# ---------------------------------------------------------------------------

class RecommendationCreate(BaseModel):
    client_id: int
    asset_id: int | None = None
    recommendation_type: RecommendationType
    rationale: str
    suggested_amount: Decimal | None = Field(None, ge=0)
    suggested_quantity: Decimal | None = Field(None, gt=0)
    target_price: Decimal | None = Field(None, gt=0)
    confidence_score: Decimal | None = Field(None, ge=0, le=1)
    expires_at: datetime | None = None
    ai_model_version: str | None = None


class RecommendationUpdate(BaseModel):
    status: RecommendationStatus | None = None
    actioned_at: datetime | None = None
    rationale: str | None = None
    confidence_score: Decimal | None = Field(None, ge=0, le=1)


class RecommendationResponse(OrmBase):
    id: int
    client_id: int
    asset_id: int | None
    recommendation_type: RecommendationType
    status: RecommendationStatus
    rationale: str
    suggested_amount: Decimal | None
    suggested_quantity: Decimal | None
    target_price: Decimal | None
    confidence_score: Decimal | None
    expires_at: datetime | None
    actioned_at: datetime | None
    ai_model_version: str | None
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Report schemas
# ---------------------------------------------------------------------------

class ReportCreate(BaseModel):
    client_id: int
    report_type: ReportType
    title: str = Field(..., max_length=255)
    period_start: date | None = None
    period_end: date | None = None
    summary: str | None = None
    total_portfolio_value: Decimal | None = None
    total_gain_loss: Decimal | None = None
    total_gain_loss_pct: Decimal | None = None
    generated_by: str | None = None


class ReportUpdate(BaseModel):
    title: str | None = Field(None, max_length=255)
    summary: str | None = None
    file_url: str | None = None
    total_portfolio_value: Decimal | None = None
    total_gain_loss: Decimal | None = None
    total_gain_loss_pct: Decimal | None = None
    is_draft: bool | None = None


class ReportResponse(OrmBase):
    id: int
    client_id: int
    report_type: ReportType
    title: str
    period_start: date | None
    period_end: date | None
    file_url: str | None
    summary: str | None
    total_portfolio_value: Decimal | None
    total_gain_loss: Decimal | None
    total_gain_loss_pct: Decimal | None
    is_draft: bool
    generated_by: str | None
    created_at: datetime
    updated_at: datetime
