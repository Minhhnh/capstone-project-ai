import os

SCRIPT_PATH = "."


class RepositoryConstant:
    DIR_REPOS = "repositories"
    BLIP_REPO = os.environ.get('BLIP_REPO', 'https://github.com/salesforce/BLIP.git')
    BLIP_CONMIT_HASH = os.environ.get(
        'BLIP_COMMIT_HASH', "48211a1594f1321b00f14c9f7a5b4813144b2fb9")

    STABLE_DIFFUSION_REPO = os.environ.get(
        'STABLE_DIFFUSION_REPO', "https://github.com/Stability-AI/stablediffusion.git")
    STABLE_DIFFUSION_COMMIT_HASH = os.environ.get(
        'STABLE_DIFFUSION_COMMIT_HASH', "47b6b607fdd31875c9279cd2f4f16b92e4ea958e")
