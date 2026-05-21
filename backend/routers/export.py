"""
Export Router — GET /api/export/{file_id}
Returns the cleaned file with a DataScrub_Issue_Status column appended.
"""
import time

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from routers.upload import sessions
from services.file_service import read_file_to_dataframe
from services.export_service import export_cleaned_file

router = APIRouter()


@router.get("/export/{file_id}")
async def export_file(file_id: str, fmt: str = "csv"):
    if file_id not in sessions:
        raise HTTPException(status_code=404, detail="File not found.")

    session = sessions[file_id]
    if session["cleaning_result"] is None:
        raise HTTPException(
            status_code=400,
            detail="Cleaning not yet performed. POST /api/clean/start first.",
        )

    start = time.time()

    df = read_file_to_dataframe(session["path"], session["extension"])
    cleaning_result = session["cleaning_result"]

    output_path = export_cleaned_file(df, cleaning_result, file_id, fmt)
    elapsed = round(time.time() - start, 3)

    media_type = "text/csv" if fmt == "csv" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    suffix = ".csv" if fmt == "csv" else ".xlsx"
    download_name = session["original_name"].rsplit(".", 1)[0] + f"_cleaned{suffix}"

    return FileResponse(
        path=str(output_path),
        media_type=media_type,
        filename=download_name,
        headers={"X-Export-Time-Sec": str(elapsed)},
    )
