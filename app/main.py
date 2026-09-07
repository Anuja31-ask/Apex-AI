from fastapi import FastAPI
from app.api.documents import router as documents_router
from app.api.auth import router as auth_router

app = FastAPI(title="RefineShield AI - Backend")

app.include_router(auth_router)


@app.get("/")
def read_root():
    return {"status": "RefineShield backend is running"}


app.include_router(documents_router)
