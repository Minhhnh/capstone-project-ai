"""Img2img route"""
from fastapi import APIRouter, HTTPException, Response

import app.ml.modules.shared as shared
from app.api.database.models import *
from app.api.helpers.utils import (decode_base64_to_image,
                                   encode_pil_to_base64)
from app.logger.logger import configure_logging
from app.ml.modules import scripts, sd_samplers
from app.ml.modules.processing import (StableDiffusionProcessingImg2Img,
                                       process_images)
from app.ml.modules.shared import opts

# to get a string like this run:
# openssl rand -hex 32

logger = configure_logging(__name__)
router = APIRouter()

@router.get("/")
async def check_status():
    if shared.state.job_count == 0:
        return {'status': "succeeded"}
    return {'status': "busy"}

def validate_sampler_name(name):
    config = sd_samplers.all_samplers_map.get(name, None)
    if config is None:
        raise HTTPException(status_code=404, detail="Sampler not found")

    return name


def script_name_to_index(name, scripts):
    try:
        return [script.title().lower() for script in scripts].index(name.lower())
    except:
        raise HTTPException(status_code=422, detail=f"Script '{name}' not found")


def get_selectable_script(script_name, script_runner):
    if script_name is None or script_name == "":
        return None, None

    script_idx = script_name_to_index(script_name, script_runner.selectable_scripts)
    script = script_runner.selectable_scripts[script_idx]
    return script, script_idx


def get_script(script_name, script_runner):
    if script_name is None or script_name == "":
        return None, None


def init_script_args(request, selectable_scripts, selectable_idx, script_runner):
    # find max idx from the scripts in runner and generate a none array to init script_args
    last_arg_index = 1
    for script in script_runner.scripts:
        if last_arg_index < script.args_to:
            last_arg_index = script.args_to
    # None everywhere except position 0 to initialize script args
    script_args = [None] * last_arg_index
    # position 0 in script_arg is the idx+1 of the selectable script that is going to be run when using scripts.scripts_*2img.run()
    if selectable_scripts:
        script_args[selectable_scripts.args_from:selectable_scripts.args_to] = request.script_args
        script_args[0] = selectable_idx + 1
    else:
        # when [0] = 0 no selectable script to run
        script_args[0] = 0

    # Now check for always on scripts
    if request.alwayson_scripts and (len(request.alwayson_scripts) > 0):
        for alwayson_script_name in request.alwayson_scripts.keys():
            alwayson_script = get_script(alwayson_script_name, script_runner)
            if alwayson_script == None:
                raise HTTPException(
                    status_code=422, detail=f"always on script {alwayson_script_name} not found")
            # Selectable script in always on script param check
            if alwayson_script.alwayson == False:
                raise HTTPException(
                    status_code=422, detail=f"Cannot have a selectable script in the always on scripts params")
            # always on script with no arg should always run so you don't really need to add them to the requests
            if "args" in request.alwayson_scripts[alwayson_script_name]:
                script_args[alwayson_script.args_from:alwayson_script.args_to] = request.alwayson_scripts[alwayson_script_name]["args"]
    return script_args


@router.post("/", response_model=ImageToImageResponse)
async def img2imgapi(img2imgreq: StableDiffusionImg2ImgProcessingAPI):
    init_images = img2imgreq.init_images
    if init_images is None:
        raise HTTPException(status_code=404, detail="Init image not found")

    mask = img2imgreq.mask
    if mask:
        mask = decode_base64_to_image(mask)

    script_runner = scripts.scripts_img2img
    if not script_runner.scripts:
        script_runner.initialize_scripts(True)
        # ui.create_ui()
    selectable_scripts, selectable_script_idx = get_selectable_script(
        img2imgreq.script_name, script_runner)

    populate = img2imgreq.copy(update={  # Override __init__ params
        "sampler_name": validate_sampler_name(img2imgreq.sampler_name or img2imgreq.sampler_index),
        "do_not_save_samples": not img2imgreq.save_images,
        "do_not_save_grid": not img2imgreq.save_images,
        "mask": mask,
    })
    if populate.sampler_name:
        populate.sampler_index = None  # prevent a warning later on

    args = vars(populate)
    # this is meant to be done by "exclude": True in model, but it's for a reason that I cannot determine.
    args.pop('include_init_images', None)
    args.pop('script_name', None)
    # will refeed them to the pipeline directly after initializing them
    args.pop('script_args', None)
    args.pop('alwayson_scripts', None)

    script_args = init_script_args(
        img2imgreq, selectable_scripts, selectable_script_idx, script_runner)

    send_images = args.pop('send_images', True)
    args.pop('save_images', None)

    p = StableDiffusionProcessingImg2Img(sd_model=shared.sd_model, **args)
    p.init_images = [decode_base64_to_image(x) for x in init_images]
    p.scripts = script_runner
    p.outpath_grids = opts.outdir_img2img_grids
    p.outpath_samples = opts.outdir_img2img_samples

    shared.state.begin()
    if selectable_scripts != None:
        p.script_args = script_args
        processed = scripts.scripts_img2img.run(
            p, *p.script_args)  # Need to pass args as list here
    else:
        p.script_args = tuple(script_args)  # Need to pass args as tuple here
        processed = process_images(p)
    shared.state.end()

    b64images = list(map(encode_pil_to_base64, processed.images)) if send_images else []

    if not img2imgreq.include_init_images:
        img2imgreq.init_images = None
        img2imgreq.mask = None

    return ImageToImageResponse(images=b64images, parameters=vars(img2imgreq), info=processed.js())
