import base64
import io
import os
import subprocess
from io import BytesIO

import git
import piexif
from fastapi import HTTPException
from PIL import Image, PngImagePlugin

from app.api.helpers.constant import SCRIPT_PATH, RepositoryConstant


def decode_base64_to_image(encoding):
    if encoding.startswith("data:image/"):
        encoding = encoding.split(";")[1].split(",")[1]
    try:
        image = Image.open(BytesIO(base64.b64decode(encoding)))
        return image
    except Exception as err:
        raise HTTPException(status_code=500, detail="Invalid encoded image")


def encode_pil_to_base64(image):
    from app.ml.modules.shared import opts
    with io.BytesIO() as output_bytes:

        if opts.samples_format.lower() == 'png':
            use_metadata = False
            metadata = PngImagePlugin.PngInfo()
            for key, value in image.info.items():
                if isinstance(key, str) and isinstance(value, str):
                    metadata.add_text(key, value)
                    use_metadata = True
            image.save(output_bytes, format="PNG", pnginfo=(
                metadata if use_metadata else None), quality=opts.jpeg_quality)

        elif opts.samples_format.lower() in ("jpg", "jpeg", "webp"):
            parameters = image.info.get('parameters', None)
            exif_bytes = piexif.dump({
                "Exif": {piexif.ExifIFD.UserComment: piexif.helper.UserComment.dump(parameters or "", encoding="unicode")}
            })
            if opts.samples_format.lower() in ("jpg", "jpeg"):
                image.save(output_bytes, format="JPEG",
                           exif=exif_bytes, quality=opts.jpeg_quality)
            else:
                image.save(output_bytes, format="WEBP",
                           exif=exif_bytes, quality=opts.jpeg_quality)

        else:
            raise HTTPException(status_code=500, detail="Invalid image format")

        bytes_data = output_bytes.getvalue()

    return base64.b64encode(bytes_data)


def run(command, desc=None, errdesc=None, custom_env=None, live=False):
    if desc is not None:
        print(desc)

    if live:
        result = subprocess.run(command, shell=True,
                                env=os.environ if custom_env is None else custom_env)
        if result.returncode != 0:
            raise RuntimeError(f"""{errdesc or 'Error running command'}.
            Command: {command}
            Error code: {result.returncode}""")

        return ""

    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            shell=True, env=os.environ if custom_env is None else custom_env)

    if result.returncode != 0:

        message = f"""{errdesc or 'Error running command'}.
        Command: {command}
        Error code: {result.returncode}
        stdout: {result.stdout.decode(encoding="utf8", errors="ignore") if len(result.stdout)>0 else '<empty>'}
        stderr: {result.stderr.decode(encoding="utf8", errors="ignore") if len(result.stderr)>0 else '<empty>'}
        """
        raise RuntimeError(message)

    return result.stdout.decode(encoding="utf8", errors="ignore")


def repo_dir(name):
    return os.path.join(SCRIPT_PATH, RepositoryConstant.DIR_REPOS, name)


def git_clone(url, dir, name, commithash=None):
    # TODO clone into temporary dir and move if successful

    if os.path.exists(dir):
        # if commithash is None:
        #     return

        # current_hash = run(f'"git -C "{dir}" rev-parse HEAD', None,
        #                    f"Couldn't determine {name}'s hash: {commithash}").strip()
        # if current_hash == commithash:
        #     return

        # run(f'"git -C "{dir}" fetch',
        #     f"Fetching updates for {name}...", f"Couldn't fetch {name}")
        # run(f'"git -C "{dir}" checkout {commithash}', f"Checking out commit for {name} with hash: {commithash}...",
        #     f"Couldn't checkout commit {commithash} for {name}")
        return

    # run(f'"git clone "{url}" "{dir}"',
    #     f"Cloning {name} into {dir}...", f"Couldn't clone {name}")
    run(f'git clone "{url}" "{dir}"',
        f"Cloning {name} into {dir}...", f"Couldn't clone {name}")

    if commithash is not None:
        run(f'git -C "{dir}" checkout {commithash}', None,
            "Couldn't checkout {name}'s hash: {commithash}")
