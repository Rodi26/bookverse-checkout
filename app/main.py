from fastapi import FastAPI

app = FastAPI(title="BookVerse Checkout Service")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/info")
def info():
    return {"service": "checkout", "version": "0.1.0"}


