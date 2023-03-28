from pydantic import BaseModel, Field


class InterrogateResponse(BaseModel):
    caption: str = Field(default=None, title="Caption",
                         description="The generated caption for the image.")
