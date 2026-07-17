from fastapi import FastAPI
from app.api.v1 import auth, upload
from app.db.session import engine
from app.db.base import Base
import app.models  # Ensures models are imported for create_all

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(auth.router, prefix="/api/v1")
app.include_router(upload.router, prefix="/api/v1")

@app.get("/")
def index():
    return {"message": "Welcome to Acoustic Space"}