"""
Clean Router — POST /api/clean/start + WebSocket /ws/cleaning/{file_id}
Dispatches columns to validators, broadcasts progress via WebSocket.
"""
import json
import time
import asyncio
from typing import Any

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from routers.upload import sessions
from services.file_service import read_file_to_dataframe
from services.cleaning_engine import run_cleaning
from config import WS_PROGRESS, WS_COLUMN_DONE, WS_COMPLETE, WS_ERROR

router = APIRouter()


class ColumnMapping(BaseModel):
    column: str
    type: str
    params: dict[str, Any] = {}


class CleanRequest(BaseModel):
    file_id: str
    column_mappings: list[ColumnMapping]


# Active WebSocket connections per file_id
ws_connections: dict[str, list[WebSocket]] = {}


async def broadcast(file_id: str, message: dict):
    """Send a JSON message to all WebSocket clients watching this file."""
    connections = ws_connections.get(file_id, [])
    dead = []
    for ws in connections:
        try:
            await ws.send_json(message)
        except Exception:
            dead.append(ws)
    for ws in dead:
        connections.remove(ws)


@router.websocket("/ws/cleaning/{file_id}")
async def websocket_cleaning(websocket: WebSocket, file_id: str):
    await websocket.accept()
    ws_connections.setdefault(file_id, []).append(websocket)
    try:
        while True:
            # Keep connection alive — client can send pings
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        ws_connections.get(file_id, []).remove(websocket)


@router.post("/clean/start")
async def start_cleaning(request: CleanRequest):
    file_id = request.file_id
    if file_id not in sessions:
        raise HTTPException(status_code=404, detail="File not found. Upload first.")

    session = sessions[file_id]
    start = time.time()

    # Read DataFrame
    df = read_file_to_dataframe(session["path"], session["extension"])

    total_columns = len(request.column_mappings)

    # Progress callback — broadcasts via WebSocket
    async def progress_callback(col_name: str, col_index: int, status: str, details: dict | None = None):
        msg = {
            "type": WS_PROGRESS if status == "processing" else WS_COLUMN_DONE,
            "column": col_name,
            "column_index": col_index,
            "total_columns": total_columns,
            "status": status,
            "percent": round(((col_index + 1) / total_columns) * 100, 1),
        }
        if details:
            msg["details"] = details
        await broadcast(file_id, msg)

    # Run cleaning
    try:
        result = await run_cleaning(df, request.column_mappings, progress_callback)
    except Exception as e:
        await broadcast(file_id, {"type": WS_ERROR, "message": str(e)})
        raise HTTPException(status_code=500, detail=str(e))

    elapsed = round(time.time() - start, 3)
    result["cleaning_time_sec"] = elapsed

    # Store result
    session["cleaning_result"] = result

    # Broadcast completion
    await broadcast(file_id, {
        "type": WS_COMPLETE,
        "cleaning_time_sec": elapsed,
        "total_issues": result["total_issues"],
    })

    return {
        "file_id": file_id,
        "cleaning_time_sec": elapsed,
        "total_issues": result["total_issues"],
        "columns_processed": result["columns_processed"],
        "summary": result["summary"],
    }
