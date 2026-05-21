"""
Upload Router — POST /api/upload
Accepts CSV/Excel files, saves to disk, returns a file_id (UUID).
"""
import uuid
import time
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException

from config import UPLOAD_DIR, ALLOWED_EXTENSIONS

router = APIRouter()

# In-memory session store: file_id -> metadata dict
sessions: dict[str, dict] = {}


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    start = time.time()

    # Validate extension
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # Generate unique ID and save file
    file_id = str(uuid.uuid4())
    safe_name = f"{file_id}{ext}"
    dest = UPLOAD_DIR / safe_name

    contents = await file.read()
    dest.write_bytes(contents)

    file_size = len(contents)
    elapsed = round(time.time() - start, 3)

    # Store session metadata
    sessions[file_id] = {
        "file_id": file_id,
        "original_name": file.filename,
        "saved_name": safe_name,
        "path": str(dest),
        "extension": ext,
        "size_bytes": file_size,
        "upload_time": elapsed,
        "profile": None,
        "cleaning_result": None,
    }

    return {
        "file_id": file_id,
        "filename": file.filename,
        "size_bytes": file_size,
        "upload_time_sec": elapsed,
        "message": "File uploaded successfully.",
    }
