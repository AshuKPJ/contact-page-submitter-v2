# app/api/notifications.py - Notifications system endpoints
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


class NotificationCreate(BaseModel):
    type: str
    title: str
    message: str
    priority: str = "normal"  # low, normal, high, urgent
    action_url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class NotificationResponse(BaseModel):
    id: str
    type: str
    title: str
    message: str
    priority: str
    action_url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    read: bool
    created_at: str
    read_at: Optional[str] = None


class NotificationStats(BaseModel):
    total: int
    unread: int
    by_type: Dict[str, int]
    by_priority: Dict[str, int]


@router.get("/", response_model=List[NotificationResponse])
def get_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    unread_only: bool = Query(False),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    notification_type: Optional[str] = Query(None),
):
    """Get notifications for user"""
    try:
        query = "SELECT * FROM notifications WHERE user_id = :user_id"
        params = {"user_id": str(current_user.id)}

        if unread_only:
            query += " AND read = false"

        if notification_type:
            query += " AND type = :type"
            params["type"] = notification_type

        query += " ORDER BY created_at DESC LIMIT :limit OFFSET :offset"
        params.update({"limit": limit, "offset": offset})

        result = db.execute(text(query), params).mappings().all()

        notifications = []
        for notification in result:
            notif_dict = dict(notification)
            notifications.append(
                NotificationResponse(
                    id=notif_dict["id"],
                    type=notif_dict["type"],
                    title=notif_dict["title"],
                    message=notif_dict["message"],
                    priority=notif_dict.get("priority", "normal"),
                    action_url=notif_dict.get("action_url"),
                    metadata=notif_dict.get("metadata"),
                    read=notif_dict.get("read", False),
                    created_at=notif_dict["created_at"].isoformat(),
                    read_at=(
                        notif_dict["read_at"].isoformat()
                        if notif_dict.get("read_at")
                        else None
                    ),
                )
            )

        return notifications

    except Exception as e:
        print(f"[NOTIFICATIONS ERROR] {e}")
        return []


@router.post("/", response_model=NotificationResponse)
def create_notification(
    payload: NotificationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new notification (admin only)"""
    try:
        notification_id = str(uuid.uuid4())

        insert_query = text(
            """
            INSERT INTO notifications 
            (id, user_id, type, title, message, priority, action_url, metadata, 
             read, created_at)
            VALUES (:id, :user_id, :type, :title, :message, :priority, 
                   :action_url, :metadata, false, :created_at)
        """
        )

        db.execute(
            insert_query,
            {
                "id": notification_id,
                "user_id": str(current_user.id),
                "type": payload.type,
                "title": payload.title,
                "message": payload.message,
                "priority": payload.priority,
                "action_url": payload.action_url,
                "metadata": payload.metadata,
                "created_at": datetime.utcnow(),
            },
        )

        db.commit()

        return NotificationResponse(
            id=notification_id,
            type=payload.type,
            title=payload.title,
            message=payload.message,
            priority=payload.priority,
            action_url=payload.action_url,
            metadata=payload.metadata,
            read=False,
            created_at=datetime.utcnow().isoformat(),
        )

    except Exception as e:
        print(f"[CREATE NOTIFICATION ERROR] {e}")
        raise HTTPException(status_code=500, detail="Failed to create notification")


@router.put("/{notification_id}/read")
def mark_notification_read(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark a notification as read"""
    try:
        update_query = text(
            """
            UPDATE notifications 
            SET read = true, read_at = :read_at
            WHERE id = :notification_id AND user_id = :user_id
        """
        )

        result = db.execute(
            update_query,
            {
                "notification_id": notification_id,
                "user_id": str(current_user.id),
                "read_at": datetime.utcnow(),
            },
        )

        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Notification not found")

        db.commit()

        return {"success": True, "message": "Notification marked as read"}

    except HTTPException:
        raise
    except Exception as e:
        print(f"[MARK READ ERROR] {e}")
        raise HTTPException(
            status_code=500, detail="Failed to mark notification as read"
        )


@router.put("/mark-all-read")
def mark_all_notifications_read(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Mark all notifications as read"""
    try:
        update_query = text(
            """
            UPDATE notifications 
            SET read = true, read_at = :read_at
            WHERE user_id = :user_id AND read = false
        """
        )

        result = db.execute(
            update_query,
            {"user_id": str(current_user.id), "read_at": datetime.utcnow()},
        )

        db.commit()

        return {
            "success": True,
            "message": f"Marked {result.rowcount} notifications as read",
        }

    except Exception as e:
        print(f"[MARK ALL READ ERROR] {e}")
        raise HTTPException(
            status_code=500, detail="Failed to mark notifications as read"
        )


@router.delete("/{notification_id}")
def delete_notification(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a notification"""
    try:
        delete_query = text(
            """
            DELETE FROM notifications 
            WHERE id = :notification_id AND user_id = :user_id
        """
        )

        result = db.execute(
            delete_query,
            {"notification_id": notification_id, "user_id": str(current_user.id)},
        )

        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Notification not found")

        db.commit()

        return {"success": True, "message": "Notification deleted"}

    except HTTPException:
        raise
    except Exception as e:
        print(f"[DELETE NOTIFICATION ERROR] {e}")
        raise HTTPException(status_code=500, detail="Failed to delete notification")


@router.get("/stats", response_model=NotificationStats)
def get_notification_stats(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Get notification statistics"""
    try:
        stats_query = text(
            """
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN read = false THEN 1 END) as unread,
                type,
                priority,
                COUNT(CASE WHEN type = :type THEN 1 END) as type_count,
                COUNT(CASE WHEN priority = :priority THEN 1 END) as priority_count
            FROM notifications 
            WHERE user_id = :user_id
            GROUP BY type, priority
        """
        )

        # Get basic stats
        basic_stats_query = text(
            """
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN read = false THEN 1 END) as unread
            FROM notifications 
            WHERE user_id = :user_id
        """
        )

        basic_result = (
            db.execute(basic_stats_query, {"user_id": str(current_user.id)})
            .mappings()
            .first()
        )

        # Get type breakdown
        type_stats_query = text(
            """
            SELECT type, COUNT(*) as count
            FROM notifications 
            WHERE user_id = :user_id
            GROUP BY type
        """
        )

        type_results = (
            db.execute(type_stats_query, {"user_id": str(current_user.id)})
            .mappings()
            .all()
        )

        # Get priority breakdown
        priority_stats_query = text(
            """
            SELECT priority, COUNT(*) as count
            FROM notifications 
            WHERE user_id = :user_id
            GROUP BY priority
        """
        )

        priority_results = (
            db.execute(priority_stats_query, {"user_id": str(current_user.id)})
            .mappings()
            .all()
        )

        by_type = {row["type"]: row["count"] for row in type_results}
        by_priority = {row["priority"]: row["count"] for row in priority_results}

        return NotificationStats(
            total=basic_result["total"] if basic_result else 0,
            unread=basic_result["unread"] if basic_result else 0,
            by_type=by_type,
            by_priority=by_priority,
        )

    except Exception as e:
        print(f"[NOTIFICATION STATS ERROR] {e}")
        return NotificationStats(total=0, unread=0, by_type={}, by_priority={})


# Helper function to create system notifications
async def create_system_notification(
    user_id: str,
    notification_type: str,
    title: str,
    message: str,
    priority: str = "normal",
    action_url: str = None,
    metadata: Dict[str, Any] = None,
    db: Session = None,
):
    """Helper function to create system notifications"""
    if not db:
        return

    try:
        notification_id = str(uuid.uuid4())

        insert_query = text(
            """
            INSERT INTO notifications 
            (id, user_id, type, title, message, priority, action_url, metadata, 
             read, created_at)
            VALUES (:id, :user_id, :type, :title, :message, :priority, 
                   :action_url, :metadata, false, :created_at)
        """
        )

        db.execute(
            insert_query,
            {
                "id": notification_id,
                "user_id": user_id,
                "type": notification_type,
                "title": title,
                "message": message,
                "priority": priority,
                "action_url": action_url,
                "metadata": metadata,
                "created_at": datetime.utcnow(),
            },
        )

        db.commit()

        return notification_id

    except Exception as e:
        print(f"[SYSTEM NOTIFICATION ERROR] {e}")
        return None
