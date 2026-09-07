from fastapi import FastAPI

from app.api.auth import router as auth_router

app = FastAPI(title="RefineShield AI - Backend")

app.include_router(auth_router)


@app.get("/")
def read_root():
    return {"status": "RefineShield backend is running"}