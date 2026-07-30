"""
AdviserOS — SQLAlchemy ORM Models
Tables: clients, assets, investments, recommendations, reports
"""

import enum
from datetime import datetime, date
from decimal import Decimal

from sqlalchemy import (
    BigInteger, Boolean, Date, DateTime, Enum, ForeignKey,
    Numeric, String, Text, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class RiskProfile(str, enum.Enum):
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"


class AssetClass(str, enum.Enum):
    EQUITY = "equity"
    FIXED_INCOME = "fixed_income"
    REAL_ESTATE = "real_estate"
    COMMODITY = "commodity"
    CASH = "cash"
    CRYPTO = "crypto"
    ALTERNATIVE = "alternative"


class InvestmentStatus(str, enum.Enum):
    ACTIVE = "active"
    CLOSED = "closed"
    PENDING = "pending"


class RecommendationStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"


class RecommendationType(str, enum.Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    REBALANCE = "rebalance"
    REVIEW = "review"


class ReportType(str, enum.Enum):
    PORTFOLIO_SUMMARY = "portfolio_summary"
    PERFORMANCE = "performance"
    TAX = "tax"
    RISK_ASSESSMENT = "risk_assessment"
    ANNUAL = "annual"


# ---------------------------------------------------------------------------
# Clients
# ---------------------------------------------------------------------------

class Client(Base):
    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    phone: Mapped[str | None] = mapped_column(String(30))
    date_of_birth: Mapped[date | None] = mapped_column(Date)
    risk_profile: Mapped[RiskProfile] = mapped_column(
        Enum(RiskProfile), nullable=False, default=RiskProfile.MODERATE
    )
    investment_horizon_years: Mapped[int | None] = mapped_column()
    annual_income: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    net_worth: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    investments: Mapped[list["Investment"]] = relationship("Investment", back_populates="client")
    recommendations: Mapped[list["Recommendation"]] = relationship("Recommendation", back_populates="client")
    reports: Mapped[list["Report"]] = relationship("Report", back_populates="client")

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"


# ---------------------------------------------------------------------------
# Assets
# ---------------------------------------------------------------------------

class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ticker: Mapped[str | None] = mapped_column(String(20), index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    asset_class: Mapped[AssetClass] = mapped_column(Enum(AssetClass), nullable=False)
    exchange: Mapped[str | None] = mapped_column(String(50))
    currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)
    current_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    price_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    isin: Mapped[str | None] = mapped_column(String(20), unique=True)
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    investments: Mapped[list["Investment"]] = relationship("Investment", back_populates="asset")
    recommendations: Mapped[list["Recommendation"]] = relationship("Recommendation", back_populates="asset")


# ---------------------------------------------------------------------------
# Investments
# ---------------------------------------------------------------------------

class Investment(Base):
    __tablename__ = "investments"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    client_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    asset_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("assets.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    quantity: Mapped[Decimal] = mapped_column(Numeric(24, 8), nullable=False)
    purchase_price: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    purchase_date: Mapped[date] = mapped_column(Date, nullable=False)
    current_value: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    status: Mapped[InvestmentStatus] = mapped_column(
        Enum(InvestmentStatus), nullable=False, default=InvestmentStatus.ACTIVE
    )
    close_date: Mapped[date | None] = mapped_column(Date)
    close_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    account_number: Mapped[str | None] = mapped_column(String(60))
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    client: Mapped["Client"] = relationship("Client", back_populates="investments")
    asset: Mapped["Asset"] = relationship("Asset", back_populates="investments")

    @property
    def cost_basis(self) -> Decimal:
        return self.quantity * self.purchase_price

    @property
    def unrealized_gain_loss(self) -> Decimal | None:
        if self.current_value is None:
            return None
        return self.current_value - self.cost_basis


# ---------------------------------------------------------------------------
# Recommendations
# ---------------------------------------------------------------------------

class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    client_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    asset_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("assets.id", ondelete="SET NULL"), index=True
    )
    recommendation_type: Mapped[RecommendationType] = mapped_column(
        Enum(RecommendationType), nullable=False
    )
    status: Mapped[RecommendationStatus] = mapped_column(
        Enum(RecommendationStatus), nullable=False, default=RecommendationStatus.PENDING
    )
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    suggested_amount: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    suggested_quantity: Mapped[Decimal | None] = mapped_column(Numeric(24, 8))
    target_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    confidence_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))  # 0.0000 – 1.0000
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    actioned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ai_model_version: Mapped[str | None] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    client: Mapped["Client"] = relationship("Client", back_populates="recommendations")
    asset: Mapped["Asset"] = relationship("Asset", back_populates="recommendations")


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------

class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    client_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    report_type: Mapped[ReportType] = mapped_column(Enum(ReportType), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    period_start: Mapped[date | None] = mapped_column(Date)
    period_end: Mapped[date | None] = mapped_column(Date)
    file_url: Mapped[str | None] = mapped_column(String(1024))   # S3 / object-storage path
    summary: Mapped[str | None] = mapped_column(Text)
    total_portfolio_value: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    total_gain_loss: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    total_gain_loss_pct: Mapped[Decimal | None] = mapped_column(Numeric(8, 4))
    is_draft: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    generated_by: Mapped[str | None] = mapped_column(String(100))  # adviser / AI / system
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    client: Mapped["Client"] = relationship("Client", back_populates="reports")
