from fastapi import FastAPI

from places_api import router as places_router

app = FastAPI(title="Solo Travelling Assistant")
app.include_router(places_router)


@app.get("/health")
def health():
    return {"status": "ok"}
