"""
DataScrub — FastAPI Application Entry Point
"""
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import upload, profile, clean, export

app = FastAPI(
    title="DataScrub API",
    description="Backend API for the DataScrub data-cleaning web application",
    version="1.0.0",
)

# CORS — allow all origins during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(upload.router, prefix="/api", tags=["Upload"])
app.include_router(profile.router, prefix="/api", tags=["Profile"])
app.include_router(clean.router, prefix="/api", tags=["Clean"])
app.include_router(export.router, prefix="/api", tags=["Export"])

# WebSocket is registered inside clean.router


@app.get("/", tags=["Health"])
async def health_check():
    return {"status": "ok", "service": "DataScrub"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
