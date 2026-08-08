from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import auth, upload, analyze
from app.db.session import engine
from app.db.base import Base
import app.models  # Ensures models are imported for create_all

Base.metadata.create_all(bind=engine)

app = FastAPI(title="AcousticSpace API", version="1.0.0")

# ── CORS — allow the Vite dev server and production frontend ──────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",   # Vite dev server
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Guest-Id"],
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(upload.router, prefix="/api/v1")
app.include_router(analyze.router, prefix="/api/v1")

@app.get("/")
def index():
    return {"message": "Welcome to Acoustic Space"}