# app/api/files.py - File management endpoints
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from typing import List, Optional
import os
import csv
import io
import uuid
from datetime import datetime
import aiofiles

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/files", tags=["files"])

# Configuration
UPLOAD_DIR = "uploads"
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {".csv", ".txt", ".xlsx"}


class FileInfo(BaseModel):
    id: str
    filename: str
    original_filename: str
    file_size: int
    file_type: str
    upload_date: str
    campaign_id: Optional[str] = None


def ensure_upload_dir():
    """Ensure upload directory exists"""
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    os.makedirs(f"{UPLOAD_DIR}/csv", exist_ok=True)
    os.makedirs(f"{UPLOAD_DIR}/exports", exist_ok=True)


@router.post("/upload-csv", response_model=FileInfo)
async def upload_csv_file(
    request: Request,
    file: UploadFile = File(...),
    campaign_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upload a CSV file for campaigns"""
    try:
        ensure_upload_dir()

        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")

        if not file.filename.lower().endswith((".csv", ".txt")):
            raise HTTPException(
                status_code=400, detail="Only CSV and TXT files are allowed"
            )

        # Check file size
        contents = await file.read()
        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size is {MAX_FILE_SIZE // 1024 // 1024}MB",
            )

        # Generate unique filename
        file_id = str(uuid.uuid4())
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{file_id}{file_extension}"
        file_path = os.path.join(UPLOAD_DIR, "csv", unique_filename)

        # Save file
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(contents)

        # Validate CSV format
        try:
            # Read first few rows to validate
            with open(file_path, "r", encoding="utf-8") as csvfile:
                csv_reader = csv.reader(csvfile)
                headers = next(csv_reader, [])
                sample_rows = [
                    next(csv_reader, [])
                    for _ in range(min(3, sum(1 for _ in csv_reader)))
                ]

                if not headers:
                    os.remove(file_path)
                    raise HTTPException(
                        status_code=400,
                        detail="CSV file appears to be empty or invalid",
                    )

        except Exception as e:
            if os.path.exists(file_path):
                os.remove(file_path)
            raise HTTPException(status_code=400, detail=f"Invalid CSV format: {str(e)}")

        # Store file info in database
        file_record = {
            "id": file_id,
            "user_id": str(current_user.id),
            "campaign_id": campaign_id,
            "filename": unique_filename,
            "original_filename": file.filename,
            "file_path": file_path,
            "file_size": len(contents),
            "file_type": "csv",
            "upload_date": datetime.utcnow(),
        }

        insert_query = text(
            """
            INSERT INTO uploaded_files 
            (id, user_id, campaign_id, filename, original_filename, file_path, 
             file_size, file_type, upload_date)
            VALUES (:id, :user_id, :campaign_id, :filename, :original_filename, 
                   :file_path, :file_size, :file_type, :upload_date)
        """
        )

        db.execute(insert_query, file_record)
        db.commit()

        return FileInfo(
            id=file_id,
            filename=unique_filename,
            original_filename=file.filename,
            file_size=len(contents),
            file_type="csv",
            upload_date=file_record["upload_date"].isoformat(),
            campaign_id=campaign_id,
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"[FILE UPLOAD ERROR] {e}")
        raise HTTPException(status_code=500, detail="File upload failed")


@router.get("/list", response_model=List[FileInfo])
def list_files(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    file_type: Optional[str] = None,
    campaign_id: Optional[str] = None,
):
    """List uploaded files"""
    try:
        query = "SELECT * FROM uploaded_files WHERE user_id = :user_id"
        params = {"user_id": str(current_user.id)}

        if file_type:
            query += " AND file_type = :file_type"
            params["file_type"] = file_type

        if campaign_id:
            query += " AND campaign_id = :campaign_id"
            params["campaign_id"] = campaign_id

        query += " ORDER BY upload_date DESC"

        result = db.execute(text(query), params).mappings().all()

        files = []
        for file_record in result:
            file_dict = dict(file_record)
            files.append(
                FileInfo(
                    id=file_dict["id"],
                    filename=file_dict["filename"],
                    original_filename=file_dict["original_filename"],
                    file_size=file_dict["file_size"],
                    file_type=file_dict["file_type"],
                    upload_date=file_dict["upload_date"].isoformat(),
                    campaign_id=file_dict.get("campaign_id"),
                )
            )

        return files

    except Exception as e:
        print(f"[LIST FILES ERROR] {e}")
        return []


@router.get("/download/{file_id}")
def download_file(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Download a file"""
    try:
        # Get file info
        query = text(
            """
            SELECT * FROM uploaded_files 
            WHERE id = :file_id AND user_id = :user_id
        """
        )

        result = (
            db.execute(query, {"file_id": file_id, "user_id": str(current_user.id)})
            .mappings()
            .first()
        )

        if not result:
            raise HTTPException(status_code=404, detail="File not found")

        file_info = dict(result)
        file_path = file_info["file_path"]

        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found on disk")

        return FileResponse(
            path=file_path,
            filename=file_info["original_filename"],
            media_type="application/octet-stream",
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"[FILE DOWNLOAD ERROR] {e}")
        raise HTTPException(status_code=500, detail="File download failed")


@router.delete("/{file_id}")
def delete_file(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a file"""
    try:
        # Get file info
        query = text(
            """
            SELECT file_path FROM uploaded_files 
            WHERE id = :file_id AND user_id = :user_id
        """
        )

        result = (
            db.execute(query, {"file_id": file_id, "user_id": str(current_user.id)})
            .mappings()
            .first()
        )

        if not result:
            raise HTTPException(status_code=404, detail="File not found")

        file_path = result["file_path"]

        # Delete from database
        delete_query = text(
            """
            DELETE FROM uploaded_files 
            WHERE id = :file_id AND user_id = :user_id
        """
        )

        db.execute(delete_query, {"file_id": file_id, "user_id": str(current_user.id)})

        db.commit()

        # Delete physical file
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"[FILE DELETE WARNING] Could not delete physical file: {e}")

        return {"success": True, "message": "File deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        print(f"[FILE DELETE ERROR] {e}")
        raise HTTPException(status_code=500, detail="File deletion failed")


@router.post("/export-campaign-results/{campaign_id}")
def export_campaign_results(
    campaign_id: str,
    format: str = "csv",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Export campaign results to CSV"""
    try:
        # Verify campaign ownership
        campaign_query = text(
            """
            SELECT name FROM campaigns 
            WHERE id = :campaign_id AND user_id = :user_id
        """
        )

        campaign = (
            db.execute(
                campaign_query,
                {"campaign_id": campaign_id, "user_id": str(current_user.id)},
            )
            .mappings()
            .first()
        )

        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")

        # Get submission data
        submissions_query = text(
            """
            SELECT 
                s.id, s.status, s.success, s.created_at, s.updated_at,
                s.response_time, s.retry_count, s.error_message,
                s.captcha_encountered, s.captcha_solved,
                w.domain, w.contact_url
            FROM submissions s
            LEFT JOIN websites w ON s.website_id = w.id
            WHERE s.campaign_id = :campaign_id
            ORDER BY s.created_at DESC
        """
        )

        results = (
            db.execute(submissions_query, {"campaign_id": campaign_id}).mappings().all()
        )

        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)

        # Write headers
        headers = [
            "ID",
            "Domain",
            "Contact URL",
            "Status",
            "Success",
            "Response Time (ms)",
            "Retry Count",
            "CAPTCHA Encountered",
            "CAPTCHA Solved",
            "Error Message",
            "Created At",
            "Updated At",
        ]
        writer.writerow(headers)

        # Write data
        for result in results:
            writer.writerow(
                [
                    result["id"],
                    result.get("domain", ""),
                    result.get("contact_url", ""),
                    result["status"],
                    result["success"],
                    result.get("response_time", ""),
                    result.get("retry_count", 0),
                    result.get("captcha_encountered", False),
                    result.get("captcha_solved", False),
                    result.get("error_message", ""),
                    result["created_at"].isoformat() if result["created_at"] else "",
                    result["updated_at"].isoformat() if result["updated_at"] else "",
                ]
            )

        # Prepare response
        output.seek(0)
        filename = f"campaign_{campaign_id}_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        return StreamingResponse(
            io.StringIO(output.getvalue()),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"[EXPORT ERROR] {e}")
        raise HTTPException(status_code=500, detail="Export failed")
