from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from routes.mentor import router as mentor_router
from routes.exercises import router as exercise_router
import os

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(mentor_router, prefix="/api")
app.include_router(exercise_router, prefix="/api")

@app.get("/")
async def read_root():
    return {"message": "Exercise Generator API is running"}

@app.get("/test")
async def serve_test_ui():
    """Serve the static HTML file for testing"""
    return FileResponse('static/index.html')