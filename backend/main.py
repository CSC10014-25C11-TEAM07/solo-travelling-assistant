from fastapi import FastAPI

app = FastAPI(title="Solo Travelling Assistant")


@app.get("/health")
def health():
    return {"status": "ok"}