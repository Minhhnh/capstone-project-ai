"""Main file"""
import logging
import os
import re
import signal
import sys

import torch
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from packaging import version
from starlette.exceptions import HTTPException
from starlette.responses import HTMLResponse

import app.ml.modules.face_restoration
import app.ml.modules.hypernetworks.hypernetwork
import app.ml.modules.img2img
import app.ml.modules.lowvram
import app.ml.modules.script_callbacks
import app.ml.modules.scripts
import app.ml.modules.sd_hijack
import app.ml.modules.sd_models
import app.ml.modules.sd_vae
import app.ml.modules.textual_inversion.textual_inversion
import app.ml.modules.ui
from app.api.errors import errors
from app.api.errors.http_error import http_error_handler
from app.api.errors.validation_error import http422_error_handler
from app.api.helpers import extensions, localization
from app.api.helpers.constant import SCRIPT_PATH, RepositoryConstant
from app.api.helpers.utils import git_clone, repo_dir
from app.core.config import ALLOWED_HOSTS, API_PREFIX, DEBUG, PROJECT_NAME, VERSION
from app.ml.modules import modelloader, script_callbacks, shared, timer
from app.ml.modules.call_queue import wrap_queued_call
from app.ml.modules.shared import cmd_opts

logging.getLogger("xformers").addFilter(
    lambda record: "A matching Triton is not available" not in record.getMessage()
)


startup_timer = timer.Timer()

startup_timer.record("import torch")

startup_timer.record("import gradio")

startup_timer.record("import ldm")


# Truncate version number of nightly/local build of PyTorch to not cause exceptions with CodeFormer or Safetensors
if ".dev" in torch.__version__ or "+git" in torch.__version__:
    torch.__long_version__ = torch.__version__
    torch.__version__ = re.search(r"[\d.]+[\d]", torch.__version__).group(0)


startup_timer.record("other imports")


def prepare_environment():
    os.makedirs(os.path.join(SCRIPT_PATH, RepositoryConstant.DIR_REPOS), exist_ok=True)
    git_clone(
        RepositoryConstant.BLIP_REPO,
        repo_dir("BLIP"),
        "BLIP",
        RepositoryConstant.BLIP_CONMIT_HASH,
    )
    git_clone(
        RepositoryConstant.STABLE_DIFFUSION_REPO,
        repo_dir("stable-diffusion-stability-ai"),
        "Stable Diffusion",
        RepositoryConstant.STABLE_DIFFUSION_COMMIT_HASH,
    )
    git_clone(
        RepositoryConstant.K_DIFFUSION_REPO,
        repo_dir("k-diffusion"),
        "K-diffusion",
        RepositoryConstant.K_DIFFUSION_COMMIT_HASH,
    )
    script_callbacks.model_loaded_callback(shared.sd_model)
    cuda_visible_devices = os.environ.get("CUDA_VISIBLE_DEVICES", "1,0")


def check_versions():
    if shared.cmd_opts.skip_version_check:
        return

    expected_torch_version = "1.13.1"

    if version.parse(torch.__version__) < version.parse(expected_torch_version):
        errors.print_error_explanation(
            f"""
You are running torch {torch.__version__}.
The program is tested to work with torch {expected_torch_version}.
To reinstall the desired version, run with commandline flag --reinstall-torch.
Beware that this will cause a lot of large files to be downloaded, as well as
there are reports of issues with training tab on the latest version.

Use --skip-version-check commandline argument to disable this check.
        """.strip()
        )

    expected_xformers_version = "0.0.16rc425"
    if shared.xformers_available:
        import xformers

        if version.parse(xformers.__version__) < version.parse(
            expected_xformers_version
        ):
            errors.print_error_explanation(
                f"""
You are running xformers {xformers.__version__}.
The program is tested to work with xformers {expected_xformers_version}.
To reinstall the desired version, run with commandline flag --reinstall-xformers.

Use --skip-version-check commandline argument to disable this check.
            """.strip()
            )


def initialize():
    """
    This function initializes various components of a program, including checking versions, listing
    extensions and localizations, setting up models, refreshing VAEs, loading checkpoints, and
    registering extra networks.
    """
    check_versions()

    extensions.list_extensions()
    localization.list_localizations(cmd_opts.localizations_dir)
    startup_timer.record("list extensions")

    # if cmd_opts.ui_debug_mode:
    #     shared.sd_upscalers = upscaler.UpscalerLanczos().scalers
    #     app.ml.modules.scripts.load_scripts()
    #     return

    modelloader.cleanup_models()
    app.ml.modules.sd_models.setup_model()
    startup_timer.record("list SD models")

    # modelloader.list_builtin_upscalers()
    # startup_timer.record("list builtin upscalers")

    # app.ml.modules.scripts.load_scripts()
    # startup_timer.record("load scripts")

    # modelloader.load_upscalers()
    # startup_timer.record("load upscalers")

    app.ml.modules.sd_vae.refresh_vae_list()
    startup_timer.record("refresh VAE")

    # app.ml.modules.textual_inversion.textual_inversion.list_textual_inversion_templates()
    # startup_timer.record("refresh textual inversion templates")

    try:
        app.ml.modules.sd_models.load_model()
    except Exception as e:
        errors.display(e, "loading stable diffusion model")
        print("", file=sys.stderr)
        print("Stable diffusion model failed to load, exiting", file=sys.stderr)
        exit(1)
    startup_timer.record("load SD checkpoint")

    shared.opts.data["sd_model_checkpoint"] = shared.sd_model.sd_checkpoint_info.title

    shared.opts.onchange(
        "sd_model_checkpoint",
        wrap_queued_call(lambda: app.ml.modules.sd_models.reload_model_weights()),
    )
    shared.opts.onchange(
        "sd_vae",
        wrap_queued_call(lambda: app.ml.modules.sd_vae.reload_vae_weights()),
        call=False,
    )
    shared.opts.onchange(
        "sd_vae_as_default",
        wrap_queued_call(lambda: app.ml.modules.sd_vae.reload_vae_weights()),
        call=False,
    )
    startup_timer.record("opts onchange")

    shared.reload_hypernetworks()
    startup_timer.record("reload hypernets")

    # extra_networks.initialize()
    # extra_networks.register_extra_network(
    #     extra_networks_hypernet.ExtraNetworkHypernet())
    startup_timer.record("extra networks")

    if cmd_opts.tls_keyfile is not None and cmd_opts.tls_keyfile is not None:
        try:
            if not os.path.exists(cmd_opts.tls_keyfile):
                print("Invalid path to TLS keyfile given")
            if not os.path.exists(cmd_opts.tls_certfile):
                print(f"Invalid path to TLS certfile: '{cmd_opts.tls_certfile}'")
        except TypeError:
            cmd_opts.tls_keyfile = cmd_opts.tls_certfile = None
            print("TLS setup invalid, running webui without TLS")
        else:
            print("Running with TLS")
        startup_timer.record("TLS")

    # make the program just exit at ctrl+c without waiting for anything
    def sigint_handler(sig, frame):
        print(f"Interrupted with signal {sig} in {frame}")
        os._exit(0)

    signal.signal(signal.SIGINT, sigint_handler)


prepare_environment()
initialize()


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
