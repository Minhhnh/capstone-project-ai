from pydantic import BaseModel, Field


class InterrogateRequest(BaseModel):
    image: str = Field(default="", title="Image",
                       description="Image to work on, must be a Base64 string containing the image's data.")
    model: str = Field(default="clip", title="Model",
                       description="The interrogate model used.")


class InterrogateResponse(BaseModel):
    caption: str = Field(default=None, title="Caption",
                         description="The generated caption for the image.")
