from typing import List

from pydantic import BaseModel, Field

from app.api.database.models.base import PydanticModelGenerator
from app.ml.modules.processing import StableDiffusionProcessingImg2Img

StableDiffusionImg2ImgProcessingAPI = PydanticModelGenerator(
    "StableDiffusionProcessingImg2Img",
    StableDiffusionProcessingImg2Img,
    [
        {"key": "sampler_index", "type": str, "default": "Euler"},
        {"key": "init_images", "type": list, "default": None},
        {"key": "denoising_strength", "type": float, "default": 0.75},
        {"key": "mask", "type": str, "default": None},
        {"key": "include_init_images", "type": bool, "default": False, "exclude": True},
        {"key": "script_name", "type": str, "default": None},
        {"key": "script_args", "type": list, "default": []},
        {"key": "send_images", "type": bool, "default": True},
        {"key": "save_images", "type": bool, "default": False},
        {"key": "alwayson_scripts", "type": dict, "default": {}},
    ]
).generate_model()


class ImageToImageResponse(BaseModel):
    """
    The class `ImageToImageResponse` defines a response object that includes a list of generated images
    in base64 format, a dictionary of parameters, and a string of additional information.
    """
    images: List[str] = Field(default=None, title="Image",
                              description="The generated image in base64 format.")
    parameters: dict
    info: str
