import os

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import HTMLResponse

from app.api.errors.http_error import http_error_handler
from app.api.errors.validation_error import http422_error_handler
from app.api.helpers.constant import SCRIPT_PATH, RepositoryConstant
from app.api.helpers.utils import git_clone, repo_dir, run
from app.core.config import (ALLOWED_HOSTS, API_PREFIX, DEBUG, PROJECT_NAME,
                             VERSION)


def prepare_environment():
    os.makedirs(os.path.join(SCRIPT_PATH, RepositoryConstant.DIR_REPOS), exist_ok=True)
    git_clone(RepositoryConstant.BLIP_REPO, repo_dir('BLIP'),
              "BLIP", RepositoryConstant.BLIP_CONMIT_HASH)
    git_clone(RepositoryConstant.STABLE_DIFFUSION_REPO, repo_dir('stable-diffusion-stability-ai'),
              "Stable Diffusion", RepositoryConstant.STABLE_DIFFUSION_COMMIT_HASH)


prepare_environment()


def get_application() -> FastAPI:
    from app.api.routes.api import app as api_router

    application = FastAPI(title=PROJECT_NAME, debug=DEBUG, version=VERSION)

    application.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_HOSTS or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # application.add_event_handler("startup", create_start_app_handler(application))
    # application.add_event_handler("shutdown", create_stop_app_handler(application))

    application.add_exception_handler(HTTPException, http_error_handler)
    application.add_exception_handler(RequestValidationError, http422_error_handler)

    application.include_router(api_router, prefix=API_PREFIX)

    application.mount(
        "/static", StaticFiles(directory="app/frontend/static"), name="static"
    )

    templates = Jinja2Templates(directory="app/frontend/templates")

    @application.get("/", tags=["UI"], response_class=HTMLResponse, deprecated=False)
    async def read_root(request: Request):
        return templates.TemplateResponse("index.html", {"request": request})

    return application


app = get_application()

if __name__ == "__main__":
    import uvicorn

    HOST = os.getenv("APP_HOST")
    PORT = os.getenv("APP_PORT")
    uvicorn.run(app, host=HOST, port=int(PORT))
