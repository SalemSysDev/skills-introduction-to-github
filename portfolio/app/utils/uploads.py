"""Safe image upload handling.

Every uploaded file is:
  1. checked for an allowed extension and size,
  2. opened and verified with Pillow (rejecting anything that is not a real image),
  3. re-encoded to WebP (this strips metadata and any embedded payloads),
  4. stored under a random file name inside `static/uploads/<folder>/`.

A smaller thumbnail is generated for cards and grids.
"""
import os
import uuid

from flask import current_app
from PIL import Image, ImageOps, UnidentifiedImageError

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp", "gif"}
ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP", "GIF", "MPO"}
ALLOWED_FOLDERS = {"profile", "projects", "gallery"}
MAX_PIXELS = 40_000_000  # guards against decompression bombs
Image.MAX_IMAGE_PIXELS = MAX_PIXELS


class UploadError(ValueError):
    pass


def _has_file(file_storage) -> bool:
    return bool(file_storage and getattr(file_storage, "filename", ""))


def _extension(filename: str) -> str:
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


def _resize(img: Image.Image, max_side: int) -> Image.Image:
    copy = img.copy()
    copy.thumbnail((max_side, max_side), Image.LANCZOS)
    return copy


def save_image(file_storage, folder: str, max_side: int = 1800, thumb_side: int = 640):
    """Validate and store an uploaded image.

    Returns a dict: {"path", "thumb_path", "width", "height"} with paths
    relative to the static folder (e.g. "uploads/projects/abc.webp").
    Raises UploadError with an Arabic message on failure.
    """
    if folder not in ALLOWED_FOLDERS:
        raise UploadError("مجلد رفع غير صالح.")
    if not _has_file(file_storage):
        raise UploadError("لم يتم اختيار ملف.")

    ext = _extension(file_storage.filename)
    if ext not in ALLOWED_EXTENSIONS:
        raise UploadError("صيغة الملف غير مسموحة. الصيغ المسموحة: JPG, PNG, WEBP, GIF.")

    max_bytes = current_app.config["MAX_IMAGE_MB"] * 1024 * 1024
    stream = file_storage.stream
    stream.seek(0, os.SEEK_END)
    size = stream.tell()
    stream.seek(0)
    if size == 0:
        raise UploadError("الملف فارغ.")
    if size > max_bytes:
        raise UploadError(f"حجم الصورة يتجاوز {current_app.config['MAX_IMAGE_MB']} ميغابايت.")

    try:
        probe = Image.open(stream)
        probe.verify()  # detects truncated / corrupted / fake images
        stream.seek(0)
        img = Image.open(stream)
        if img.format not in ALLOWED_FORMATS:
            raise UploadError("الملف ليس صورة مدعومة.")
        img.load()
    except UploadError:
        raise
    except (UnidentifiedImageError, OSError, SyntaxError, Image.DecompressionBombError) as exc:
        raise UploadError("الملف ليس صورة صالحة.") from exc

    img = ImageOps.exif_transpose(img)
    return store_pil_image(img, folder, max_side, thumb_side)


def store_pil_image(img: Image.Image, folder: str, max_side: int = 1800, thumb_side: int = 640):
    """Re-encode a Pillow image to WebP (full size + thumbnail) under uploads/<folder>/."""
    if folder not in ALLOWED_FOLDERS:
        raise UploadError("مجلد رفع غير صالح.")
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGBA" if "transparency" in img.info or img.mode in ("LA", "P") else "RGB")

    target_dir = os.path.join(current_app.config["UPLOAD_FOLDER"], folder)
    os.makedirs(target_dir, exist_ok=True)
    name = uuid.uuid4().hex

    full = _resize(img, max_side)
    thumb = _resize(img, thumb_side)
    full_name, thumb_name = f"{name}.webp", f"{name}_thumb.webp"
    full.save(os.path.join(target_dir, full_name), "WEBP", quality=85, method=4)
    thumb.save(os.path.join(target_dir, thumb_name), "WEBP", quality=80, method=4)

    return {
        "path": f"uploads/{folder}/{full_name}",
        "thumb_path": f"uploads/{folder}/{thumb_name}",
        "width": full.width,
        "height": full.height,
    }


def delete_image(*relative_paths) -> None:
    """Delete stored files (only inside the uploads folder)."""
    upload_root = os.path.realpath(current_app.config["UPLOAD_FOLDER"])
    for rel in relative_paths:
        if not rel or not rel.startswith("uploads/"):
            continue
        full = os.path.realpath(os.path.join(upload_root, rel[len("uploads/"):]))
        if not full.startswith(upload_root + os.sep):
            continue  # never delete outside uploads/
        try:
            os.remove(full)
        except FileNotFoundError:
            pass


def thumb_of(path: str) -> str:
    if not path:
        return ""
    return path[:-5] + "_thumb.webp" if path.endswith(".webp") else path
