from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import create_all
from .api import router

app = FastAPI(title="BookVerse Checkout Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    create_all()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/info")
def info():
    import os
    return {"service": "checkout", "version": os.getenv("SERVICE_VERSION", "0.1.0-dev")}

app.include_router(router)

