
from fastapi import APIRouter, HTTPException

from app.api.database.models import InterrogateRequest, InterrogateResponse
from app.api.helpers.utils import decode_base64_to_image
from app.logger.logger import configure_logging
from app.ml.modules import shared

# to get a string like this run:
# openssl rand -hex 32

logger = configure_logging(__name__)
router = APIRouter()


@router.post("/", response_model=InterrogateResponse)
async def interrogateapi(interrogatereq: InterrogateRequest):
    image_b64 = interrogatereq.image
    if image_b64 is None:
        raise HTTPException(status_code=404, detail="Image not found")

    img = decode_base64_to_image(image_b64)
    img = img.convert('RGB')

    if interrogatereq.model == "clip":
        processed = shared.interrogator.interrogate(img)
    else:
        raise HTTPException(status_code=404, detail="Model not found")

    return InterrogateResponse(caption=processed)
