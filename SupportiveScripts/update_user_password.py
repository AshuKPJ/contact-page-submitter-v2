#!/usr/bin/env python3
"""
Update passwords in `public.users` using bcrypt, then verify.

- Set DATABASE_URL below.
- Call update_password_by_email(...) or update_password_by_id(...).

Columns used: users.hashed_password, users.updated_at
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import create_engine, text
from passlib.hash import bcrypt  # from passlib[bcrypt]

# 🔑 Paste your full DB URL here
# Example: "postgresql://user:pass@host:5432/dbname"
DATABASE_URL = "postgresql://neondb_owner:npg_TIN40HCxdqBU@ep-long-glitter-aekty8cj-pooler.c-2.us-east-2.aws.neon.tech/neondb?sslmode=require"

# bcrypt cost (work factor). 12 is a solid default.
BCRYPT_ROUNDS = 12

engine = create_engine(DATABASE_URL, pool_pre_ping=True)


def _find_user_id_by_email(email: str) -> Optional[str]:
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT id::text FROM public.users WHERE email = :email LIMIT 1"),
            {"email": email},
        ).fetchone()
        return row[0] if row else None


def _set_hash_for_user_id(user_id: str, new_plain_password: str) -> str:
    # Create bcrypt hash like "$2b$12$..."
    new_hash = bcrypt.using(rounds=BCRYPT_ROUNDS).hash(new_plain_password)

    with engine.begin() as conn:
        conn.execute(
            text(
                """
                UPDATE public.users
                SET hashed_password = :hp,
                    updated_at = NOW()
                WHERE id = :uid
            """
            ),
            {"hp": new_hash, "uid": user_id},
        )
        # Read back to verify
        stored_hash = conn.execute(
            text("SELECT hashed_password FROM public.users WHERE id = :uid"),
            {"uid": user_id},
        ).scalar_one()

    if not bcrypt.verify(new_plain_password, stored_hash):
        raise RuntimeError("Hash verification failed after update.")

    return stored_hash


def update_password_by_email(email: str, new_plain_password: str) -> str:
    """Update a user's password by email. Returns the user_id on success."""
    user_id = _find_user_id_by_email(email)
    if not user_id:
        raise ValueError(f"No user found for email: {email}")
    _set_hash_for_user_id(user_id, new_plain_password)
    return user_id


def update_password_by_id(user_id: str, new_plain_password: str) -> None:
    """Update a user's password by id (UUID)."""
    # Ensure user exists
    with engine.connect() as conn:
        exists = conn.execute(
            text("SELECT 1 FROM public.users WHERE id = :uid"),
            {"uid": user_id},
        ).fetchone()
        if not exists:
            raise ValueError(f"No user found for id: {user_id}")

    _set_hash_for_user_id(user_id, new_plain_password)


if __name__ == "__main__":
    # 🔧 Quick examples — uncomment ONE block and edit values:

    # 1) Update by EMAIL
    uid = update_password_by_email("user@example.com", "NewStrongP@ssw0rd!")
    print("✅ Updated password for user id:", uid)

    # 2) Update by ID
    # update_password_by_id("b2222222-2222-2222-2222-222222222222", "RotateMe#2025")
    # print("✅ Updated password for specified user id.")
    pass
