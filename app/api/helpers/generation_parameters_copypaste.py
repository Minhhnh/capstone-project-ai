from app.ml.modules import shared
infotext_to_setting_name_mapping = [
    ('Clip skip', 'CLIP_stop_at_last_layers', ),
    ('Conditional mask weight', 'inpainting_mask_weight'),
    ('Model hash', 'sd_model_checkpoint'),
    ('ENSD', 'eta_noise_seed_delta'),
    ('Noise multiplier', 'initial_noise_multiplier'),
    ('Eta', 'eta_ancestral'),
    ('Eta DDIM', 'eta_ddim'),
    ('Discard penultimate sigma', 'always_discard_next_to_last_sigma'),
    ('UniPC variant', 'uni_pc_variant'),
    ('UniPC skip type', 'uni_pc_skip_type'),
    ('UniPC order', 'uni_pc_order'),
    ('UniPC lower order final', 'uni_pc_lower_order_final'),
]


def create_override_settings_dict(text_pairs):
    """creates processing's override_settings parameters from gradio's multiselect

    Example input:
        ['Clip skip: 2', 'Model hash: e6e99610c4', 'ENSD: 31337']

    Example output:
        {'CLIP_stop_at_last_layers': 2, 'sd_model_checkpoint': 'e6e99610c4', 'eta_noise_seed_delta': 31337}
    """

    res = {}

    params = {}
    for pair in text_pairs:
        k, v = pair.split(":", maxsplit=1)

        params[k] = v.strip()

    for param_name, setting_name in infotext_to_setting_name_mapping:
        value = params.get(param_name, None)

        if value is None:
            continue

        res[setting_name] = shared.opts.cast_value(setting_name, value)

    return res


def quote(text):
    if ',' not in str(text):
        return text

    text = str(text)
    text = text.replace('\\', '\\\\')
    text = text.replace('"', '\\"')
    return f'"{text}"'
