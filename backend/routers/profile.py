"""
Profile Router — POST /api/profile/{file_id}
Runs pandas profiling + ML column-type prediction, stores results in session.
"""
import time

from fastapi import APIRouter, HTTPException

from routers.upload import sessions
from services.file_service import read_file_to_dataframe
from services.profiler import profile_dataframe
from services.column_predictor import predict_column_types

router = APIRouter()


@router.post("/profile/{file_id}")
async def profile_file(file_id: str):
    if file_id not in sessions:
        raise HTTPException(status_code=404, detail="File not found. Upload first.")

    session = sessions[file_id]
    start = time.time()

    # Read file into DataFrame
    df = read_file_to_dataframe(session["path"], session["extension"])

    # Generate profile
    profile = profile_dataframe(df)

    # Predict column types
    predictions = predict_column_types(df)

    elapsed = round(time.time() - start, 3)

    result = {
        "file_id": file_id,
        "filename": session["original_name"],
        "rows": len(df),
        "columns": len(df.columns),
        "profile": profile,
        "column_predictions": predictions,
        "profiling_time_sec": elapsed,
    }

    session["profile"] = result
    return result


@router.get("/profile/{file_id}/status")
async def profile_status(file_id: str):
    if file_id not in sessions:
        raise HTTPException(status_code=404, detail="File not found.")
    session = sessions[file_id]
    if session["profile"] is None:
        return {"file_id": file_id, "status": "not_started"}
    return {"file_id": file_id, "status": "complete"}


@router.get("/profile/{file_id}/results")
async def profile_results(file_id: str):
    if file_id not in sessions:
        raise HTTPException(status_code=404, detail="File not found.")
    session = sessions[file_id]
    if session["profile"] is None:
        raise HTTPException(status_code=400, detail="Profile not yet generated. POST /api/profile/{file_id} first.")
    return session["profile"]
