# app/services/user_service.py
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.user import User
from app.models.user_profile import UserProfile
from app.schemas.user import (
    UserProfileCreate,
    UserContactProfileCreate,
    UserProfileResponse,
)
from app.core.encryption import encryption_service


def _s(v):
    """Safe stringify for UUIDs/datetimes."""
    if v is None:
        return None
    if isinstance(v, datetime):
        return v.isoformat()
    return str(v)


def _to_response(profile: UserProfile) -> UserProfileResponse:
    return UserProfileResponse(
        id=_s(profile.id),
        user_id=_s(profile.user_id),
        first_name=profile.first_name,
        last_name=profile.last_name,
        email=profile.email,
        phone_number=profile.phone_number,
        company_name=profile.company_name,
        job_title=profile.job_title,
        website_url=profile.website_url,
        message=profile.message,
        created_at=_s(profile.created_at),
        updated_at=_s(profile.updated_at),
    )


class UserService:
    """Service for managing users and profiles."""

    def __init__(self, db: Session):
        self.db = db

    # -------------------
    # Users
    # -------------------
    def get_user_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()

    def get_user_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()

    def delete_user(self, user_id: uuid.UUID) -> bool:
        user = self.get_user_by_id(user_id)
        if not user:
            return False
        self.db.delete(user)
        self.db.commit()
        return True

    def update_user_status(self, user_id: uuid.UUID, is_active: bool) -> User:
        user = self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        user.is_active = is_active
        self.db.commit()
        self.db.refresh(user)
        return user

    def update_captcha_credentials(
        self, user_id: uuid.UUID, username: str, password: str
    ) -> User:
        user = self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        user.captcha_username = encryption_service.encrypt(username or "")
        user.captcha_password_hash = encryption_service.encrypt(password or "")

        self.db.commit()
        self.db.refresh(user)
        return user

    # -------------------
    # Profiles
    # -------------------
    def get_user_profile(self, user_id: uuid.UUID) -> Optional[UserProfileResponse]:
        profile = (
            self.db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        )
        return _to_response(profile) if profile else None

    def get_contact_profile(self, user_id: uuid.UUID) -> Optional[UserProfileResponse]:
        return self.get_user_profile(user_id)

    def create_user_profile(
        self, user_id: uuid.UUID, profile_data: UserProfileCreate
    ) -> UserProfileResponse:
        profile = (
            self.db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        )
        if profile:
            for field, value in profile_data.model_dump(exclude_unset=True).items():
                setattr(profile, field, value)
            profile.updated_at = datetime.utcnow()
        else:
            profile = UserProfile(
                user_id=user_id,
                **profile_data.model_dump(exclude_unset=True),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            self.db.add(profile)

        self.db.commit()
        self.db.refresh(profile)
        return _to_response(profile)

    def create_contact_profile(
        self, user_id: uuid.UUID, profile_data: UserContactProfileCreate
    ) -> UserProfileResponse:
        profile = (
            self.db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        )
        if profile:
            for field, value in profile_data.model_dump(exclude_unset=True).items():
                setattr(profile, field, value)
            profile.updated_at = datetime.utcnow()
        else:
            profile = UserProfile(
                user_id=user_id,
                **profile_data.model_dump(exclude_unset=True),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            self.db.add(profile)

        self.db.commit()
        self.db.refresh(profile)
        return _to_response(profile)
