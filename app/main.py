from fastapi import FastAPI

from app.api.auth import router as auth_router
from backend.main import app as apex_ai_app

app = FastAPI(title="RefineShield AI - Backend")

app.include_router(auth_router)
app.mount("/apex", apex_ai_app)


@app.get("/")
def read_root():
    return {"status": "RefineShield backend is running"}