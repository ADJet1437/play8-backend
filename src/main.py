from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.database import init_database as create_tables
from src.routers import register_routers


# Lifespan event handler for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize database
    create_tables()
    from init_db import init_sample_data
    init_sample_data()
    yield
    # Shutdown: Add cleanup code here if needed

app = FastAPI(title="Play8 Court Machine Booking API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://play8.ai",
        "https://admin.play8.ai",
        "https://www.play8.ai",
        "http://localhost:3011",
        "http://localhost:5173",  # Vite default dev server
        "http://localhost:3000",  # Common React dev server
        "http://localhost:5174",  # Admin frontend (Vite dev server alternative port)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all routers
register_routers(app)

@app.get("/")
def root():
    return {"message": "Play8 Court Machine Booking API", "status": "running"}
