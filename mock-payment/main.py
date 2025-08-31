from fastapi import FastAPI
import os
import random


app = FastAPI(title="Mock Payment Service (Demo)")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/pay")
def pay():
    ratio = float(os.getenv("PAYMENT_SUCCESS_RATIO", "1.0"))
    ok = (random.random() < ratio)
    return {"ok": ok}


