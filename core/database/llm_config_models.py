"""
SQLAlchemy models for LLM configuration database schema
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    Index,
    DECIMAL,
    TEXT,
    Date,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from sqlalchemy.sql import func

Base = declarative_base()


class LLMProvider(Base):
    """Model for LLM provider configurations"""

    __tablename__ = "llm_providers"

    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    api_key_env_var = Column(String(100))
    base_url = Column(String(255))
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=0)  # Lower = higher priority
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    models = relationship("LLMModel", back_populates="provider", cascade="all, delete-orphan")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "name": self.name,
            "api_key_env_var": self.api_key_env_var,
            "base_url": self.base_url,
            "is_active": self.is_active,
            "priority": self.priority,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class LLMModel(Base):
    """Model for available LLM models from providers"""

    __tablename__ = "llm_models"

    id = Column(Integer, primary_key=True)
    provider_id = Column(Integer, ForeignKey("llm_providers.id", ondelete="CASCADE"))
    model_identifier = Column(String(255), nullable=False)
    display_name = Column(String(255))
    capabilities = Column(JSONB, default={})
    cost_per_1k_tokens = Column(DECIMAL(10, 6))
    is_available = Column(Boolean, default=True)
    last_checked = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    provider = relationship("LLMProvider", back_populates="models")
    primary_assignments = relationship(
        "LLMModelAssignment", foreign_keys="LLMModelAssignment.primary_model_id", back_populates="primary_model"
    )
    fallback_assignments = relationship("LLMFallbackModel", back_populates="model")
    metrics = relationship("LLMMetric", back_populates="model")

    # Constraints
    __table_args__ = (
        UniqueConstraint("provider_id", "model_identifier"),
        Index("idx_llm_models_provider", "provider_id"),
        Index("idx_llm_models_available", "is_available"),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "provider_id": self.provider_id,
            "provider_name": self.provider.name if self.provider else None,
            "model_identifier": self.model_identifier,
            "display_name": self.display_name,
            "capabilities": self.capabilities,
            "cost_per_1k_tokens": float(self.cost_per_1k_tokens) if self.cost_per_1k_tokens else None,
            "is_available": self.is_available,
            "last_checked": self.last_checked.isoformat() if self.last_checked else None,
        }


class LLMUseCase(Base):
    """Model for LLM use case configurations"""

    __tablename__ = "llm_use_cases"

    id = Column(Integer, primary_key=True)
    use_case = Column(String(50), unique=True, nullable=False)
    display_name = Column(String(255))
    description = Column(TEXT)
    default_temperature = Column(DECIMAL(3, 2), default=0.5)
    default_max_tokens = Column(Integer, default=2048)
    default_system_prompt = Column(TEXT)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    assignments = relationship("LLMModelAssignment", back_populates="use_case", cascade="all, delete-orphan")
    metrics = relationship("LLMMetric", back_populates="use_case")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "use_case": self.use_case,
            "display_name": self.display_name,
            "description": self.description,
            "default_temperature": float(self.default_temperature) if self.default_temperature else None,
            "default_max_tokens": self.default_max_tokens,
            "default_system_prompt": self.default_system_prompt,
        }


class LLMModelAssignment(Base):
    """Model for assigning models to use cases and tiers"""

    __tablename__ = "llm_model_assignments"

    id = Column(Integer, primary_key=True)
    use_case_id = Column(Integer, ForeignKey("llm_use_cases.id", ondelete="CASCADE"))
    tier = Column(String(20), nullable=False)  # 'premium', 'standard', 'economy'
    primary_model_id = Column(Integer, ForeignKey("llm_models.id", ondelete="SET NULL"))
    temperature_override = Column(DECIMAL(3, 2))
    max_tokens_override = Column(Integer)
    system_prompt_override = Column(TEXT)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    use_case = relationship("LLMUseCase", back_populates="assignments")
    primary_model = relationship("LLMModel", foreign_keys=[primary_model_id], back_populates="primary_assignments")
    fallback_models = relationship("LLMFallbackModel", back_populates="assignment", cascade="all, delete-orphan")

    # Constraints
    __table_args__ = (
        UniqueConstraint("use_case_id", "tier"),
        Index("idx_llm_assignments_use_case", "use_case_id"),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "use_case_id": self.use_case_id,
            "use_case": self.use_case.use_case if self.use_case else None,
            "tier": self.tier,
            "primary_model": self.primary_model.to_dict() if self.primary_model else None,
            "temperature_override": float(self.temperature_override) if self.temperature_override else None,
            "max_tokens_override": self.max_tokens_override,
            "system_prompt_override": self.system_prompt_override,
            "fallback_models": [fb.model.to_dict() for fb in sorted(self.fallback_models, key=lambda x: x.priority)],
        }


class LLMFallbackModel(Base):
    """Model for fallback model configurations"""

    __tablename__ = "llm_fallback_models"

    id = Column(Integer, primary_key=True)
    assignment_id = Column(Integer, ForeignKey("llm_model_assignments.id", ondelete="CASCADE"))
    model_id = Column(Integer, ForeignKey("llm_models.id", ondelete="CASCADE"))
    priority = Column(Integer, default=0)  # Order of fallback
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    assignment = relationship("LLMModelAssignment", back_populates="fallback_models")
    model = relationship("LLMModel", back_populates="fallback_assignments")

    # Constraints
    __table_args__ = (UniqueConstraint("assignment_id", "model_id"),)


class LLMMetric(Base):
    """Model for tracking LLM performance metrics"""

    __tablename__ = "llm_metrics"

    id = Column(Integer, primary_key=True)
    model_id = Column(Integer, ForeignKey("llm_models.id", ondelete="CASCADE"))
    use_case_id = Column(Integer, ForeignKey("llm_use_cases.id", ondelete="CASCADE"))
    request_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    total_cost = Column(DECIMAL(10, 4), default=0)
    avg_latency_ms = Column(DECIMAL(10, 2))
    date = Column(Date, default=func.current_date())
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    model = relationship("LLMModel", back_populates="metrics")
    use_case = relationship("LLMUseCase", back_populates="metrics")

    # Constraints
    __table_args__ = (
        UniqueConstraint("model_id", "use_case_id", "date"),
        Index("idx_llm_metrics_date", "date"),
        Index("idx_llm_metrics_model_use_case", "model_id", "use_case_id"),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "model": self.model.to_dict() if self.model else None,
            "use_case": self.use_case.use_case if self.use_case else None,
            "request_count": self.request_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "success_rate": (self.success_count / self.request_count * 100) if self.request_count > 0 else 0,
            "total_tokens": self.total_tokens,
            "total_cost": float(self.total_cost) if self.total_cost else 0,
            "avg_latency_ms": float(self.avg_latency_ms) if self.avg_latency_ms else None,
            "date": self.date.isoformat() if self.date else None,
        }
