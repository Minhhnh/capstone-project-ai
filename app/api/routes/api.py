from fastapi import APIRouter

from app.api.routes import interrogate, img2img

app = APIRouter()

app.include_router(interrogate.router, tags=["CLIP"], prefix="/clip")
app.include_router(img2img.router, tags=["Stable Diffusion"], prefix="/img2img")
