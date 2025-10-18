from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import health, tags, tag_values, schedules

app = FastAPI(title="Web Scheduler")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api")
app.include_router(tags.router, prefix="/api")
app.include_router(tag_values.router, prefix="/api")
app.include_router(schedules.router, prefix="/api")


