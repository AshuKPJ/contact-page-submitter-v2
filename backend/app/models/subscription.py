# app/models/subscription.py
"""Subscription models without circular references."""

from __future__ import annotations

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, DECIMAL
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Plan details
    name = Column(String(50), nullable=False)
    description = Column(String(500), nullable=True)

    # Limits
    max_websites = Column(Integer, nullable=True)
    max_submissions_per_day = Column(Integer, nullable=True)

    # Pricing
    price = Column(DECIMAL(10, 2), nullable=True)

    # Features
    features = Column(JSONB, nullable=True)

    # Relationships
    # REMOVED: users = relationship("User", back_populates="subscription_plan")
    # This was causing circular dependency - User already has the foreign key
    subscriptions = relationship("Subscription", back_populates="plan")

    def __repr__(self):
        return f"<SubscriptionPlan {self.name}>"


class Subscription(Base):
    __tablename__ = "subscriptions"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign keys
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    plan_id = Column(
        UUID(as_uuid=True), ForeignKey("subscription_plans.id"), nullable=True
    )

    # Subscription details
    status = Column(String(50), nullable=True)
    external_id = Column(String(255), nullable=True)  # Stripe/payment processor ID

    # Dates
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="subscriptions")
    plan = relationship("SubscriptionPlan", back_populates="subscriptions")

    def __repr__(self):
        return f"<Subscription {self.id}>"
