from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.routers import auth, literature, users, workspaces

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description=(
        "ResearchOS backend — this build pass implements Module 1 (User "
        "Management), Module 2 (Research Workspace), and Module 3 "
        "(Literature Discovery) end-to-end against PostgreSQL and Redis, "
        "per the SRS, SDD, Database Design Document, and API Design "
        "Document. Remaining modules are deferred; see README.md."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(auth.router, prefix=settings.api_v1_prefix)
app.include_router(users.router, prefix=settings.api_v1_prefix)
app.include_router(users.admin_router, prefix=settings.api_v1_prefix)
app.include_router(workspaces.router, prefix=settings.api_v1_prefix)
app.include_router(literature.router, prefix=settings.api_v1_prefix)


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "environment": settings.environment}
