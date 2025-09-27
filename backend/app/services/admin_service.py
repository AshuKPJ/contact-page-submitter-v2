import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, and_, func
from fastapi import HTTPException

from app.models.user import User
from app.models.campaign import Campaign
from app.models.submission import Submission
from app.models.logs import SystemLog  # Fixed import - now from logs module
from app.schemas.admin import (
    SystemStatus,
    UserManagement,
    SystemSettings,
    AdminAction,
    AdminResponse,
)


class AdminService:
    """Service for admin operations and system management"""

    def __init__(self, db: Session):
        self.db = db

    def get_system_status(self) -> SystemStatus:
        """Get current system status"""
        try:
            # Test database connection
            db_status = "healthy"
            try:
                self.db.execute("SELECT 1")
            except Exception:
                db_status = "unhealthy"

            # Get basic system metrics
            total_users = self.db.query(User).count()
            active_campaigns = (
                self.db.query(Campaign).filter(Campaign.status == "running").count()
            )
            pending_submissions = (
                self.db.query(Submission).filter(Submission.status == "pending").count()
            )

            # Determine overall status
            if db_status == "healthy" and pending_submissions < 1000:
                status = "healthy"
            elif db_status == "healthy":
                status = "degraded"
            else:
                status = "down"

            return SystemStatus(
                status=status,
                uptime=0.0,  # Would need to track app start time
                version="1.0.0",
                environment="production",  # Should come from settings
                database_status=db_status,
            )

        except Exception as e:
            return SystemStatus(
                status="down",
                uptime=0.0,
                version="1.0.0",
                environment="production",
                database_status="unhealthy",
            )

    def manage_user(
        self, admin_user_id: uuid.UUID, user_management: UserManagement
    ) -> AdminResponse:
        """Perform user management actions"""
        # Verify admin permissions
        admin_user = self.db.query(User).filter(User.id == admin_user_id).first()
        if not admin_user or admin_user.role not in ["admin", "owner"]:
            raise HTTPException(status_code=403, detail="Insufficient permissions")

        target_user = (
            self.db.query(User).filter(User.id == user_management.user_id).first()
        )
        if not target_user:
            raise HTTPException(status_code=404, detail="User not found")

        action = user_management.action

        if action == "activate":
            target_user.is_active = True
            message = f"User {target_user.email} activated"
        elif action == "deactivate":
            target_user.is_active = False
            message = f"User {target_user.email} deactivated"
        elif action == "promote":
            if target_user.role == "user":
                target_user.role = "admin"
                message = f"User {target_user.email} promoted to admin"
            else:
                message = f"User {target_user.email} is already an admin"
        elif action == "demote":
            if target_user.role == "admin":
                target_user.role = "user"
                message = f"User {target_user.email} demoted to user"
            else:
                message = f"User {target_user.email} is already a regular user"
        elif action == "delete":
            self.db.delete(target_user)
            message = f"User {target_user.email} deleted"
        else:
            raise HTTPException(status_code=400, detail="Invalid action")

        # Log admin action
        self.log_admin_action(
            admin_user_id=admin_user_id,
            action=action,
            target_type="user",
            target_id=str(user_management.user_id),
            details=user_management.reason,
        )

        self.db.commit()

        return AdminResponse(
            success=True,
            message=message,
            data={"action": action, "target_user": target_user.email},
        )

    def get_all_users(
        self, page: int = 1, per_page: int = 20, active_only: bool = False
    ) -> tuple[List[User], int]:
        """Get all users with pagination"""
        query = self.db.query(User)

        if active_only:
            query = query.filter(User.is_active == True)

        query = query.order_by(desc(User.created_at))

        total = query.count()
        users = query.offset((page - 1) * per_page).limit(per_page).all()

        return users, total

    def get_system_metrics(self) -> Dict[str, Any]:
        """Get detailed system metrics"""
        # User metrics
        total_users = self.db.query(User).count()
        active_users = self.db.query(User).filter(User.is_active == True).count()
        new_users_today = (
            self.db.query(User)
            .filter(func.date(User.created_at) == datetime.utcnow().date())
            .count()
        )

        # Campaign metrics
        total_campaigns = self.db.query(Campaign).count()
        running_campaigns = (
            self.db.query(Campaign).filter(Campaign.status == "running").count()
        )
        completed_campaigns = (
            self.db.query(Campaign).filter(Campaign.status == "completed").count()
        )

        # Submission metrics
        total_submissions = self.db.query(Submission).count()
        successful_submissions = (
            self.db.query(Submission)
            .filter(Submission.status.in_(["submitted", "success"]))
            .count()
        )
        failed_submissions = (
            self.db.query(Submission).filter(Submission.status == "failed").count()
        )
        pending_submissions = (
            self.db.query(Submission).filter(Submission.status == "pending").count()
        )

        # Calculate rates
        user_activation_rate = (
            (active_users / total_users * 100) if total_users > 0 else 0
        )
        campaign_completion_rate = (
            (completed_campaigns / total_campaigns * 100) if total_campaigns > 0 else 0
        )
        submission_success_rate = (
            (successful_submissions / total_submissions * 100)
            if total_submissions > 0
            else 0
        )

        return {
            "users": {
                "total": total_users,
                "active": active_users,
                "new_today": new_users_today,
                "activation_rate": round(user_activation_rate, 2),
            },
            "campaigns": {
                "total": total_campaigns,
                "running": running_campaigns,
                "completed": completed_campaigns,
                "completion_rate": round(campaign_completion_rate, 2),
            },
            "submissions": {
                "total": total_submissions,
                "successful": successful_submissions,
                "failed": failed_submissions,
                "pending": pending_submissions,
                "success_rate": round(submission_success_rate, 2),
            },
        }

    def log_admin_action(
        self,
        admin_user_id: uuid.UUID,
        action: str,
        target_type: str,
        target_id: Optional[str] = None,
        details: Optional[str] = None,
    ):
        """Log admin action for audit trail"""
        log = SystemLog(
            user_id=admin_user_id,
            action=f"admin_{action}",
            details=f"Admin action: {action} on {target_type} {target_id or ''}. {details or ''}",
            timestamp=datetime.utcnow(),
        )

        self.db.add(log)
        self.db.commit()

    def get_recent_system_logs(self, limit: int = 50) -> List[SystemLog]:
        """Get recent system logs"""
        return (
            self.db.query(SystemLog)
            .order_by(desc(SystemLog.timestamp))
            .limit(limit)
            .all()
        )

    def cleanup_old_logs(self, days_to_keep: int = 30) -> int:
        """Clean up old logs (older than specified days)"""
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)

        deleted_count = (
            self.db.query(SystemLog).filter(SystemLog.timestamp < cutoff_date).delete()
        )

        self.db.commit()
        return deleted_count
