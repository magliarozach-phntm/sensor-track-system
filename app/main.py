from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.logging_config import configure_logging
from app.routes.health import router as health_router
from app.routes.observations import router as observations_router
from app.routes.tracks import router as tracks_router
from app.routes.websocket import router as websocket_router

configure_logging()

app = FastAPI(
    title=settings.app_name
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(observations_router)
app.include_router(tracks_router)
app.include_router(websocket_router)
app.include_router(health_router)

@app.get("/")
def root():
    return {
        "message": f"{settings.app_name} Online"
    }