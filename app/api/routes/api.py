from fastapi import APIRouter

from app.api.routes import interrogate

app = APIRouter()

app.include_router(interrogate.router, tags=["User"], prefix="/admin/user")
