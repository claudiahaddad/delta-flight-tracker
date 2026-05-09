import logging

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.models import init_db
from app.routes import router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

app = FastAPI(title="Delta Flight Tracker", version="0.1.0")

app.include_router(router)
app.mount("/", StaticFiles(directory="static", html=True), name="static")


@app.on_event("startup")
def startup():
    init_db()
    logging.getLogger(__name__).info("Delta Flight Tracker started")
