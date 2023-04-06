

def realesrgan_models_names():
    import app.ml.modules.realesrgan_model
    return [x.name for x in modules.realesrgan_model.get_realesrgan_models(None)]


def postprocessing_scripts():
    import app.ml.modules.scripts

    return modules.scripts.scripts_postproc.scripts


def sd_vae_items():
    import app.ml.modules.sd_vae

    return ["Automatic", "None"] + list(modules.sd_vae.vae_dict)


def refresh_vae_list():
    import app.ml.modules.sd_vae

    modules.sd_vae.refresh_vae_list()
