"""Persistent local portrait templates, separate from downloaded model assets."""
import io
import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from PIL import Image, ImageOps, UnidentifiedImageError
from avtr1_renderer.avtr1_artifact_manager import get_storage_root


def directory():
    path = get_storage_root().parent / "custom_avatars"
    path.mkdir(parents=True, exist_ok=True)
    return path


def valid_id(avatar_id):
    return re.fullmatch(r"custom_[0-9a-f]{32}", avatar_id) is not None


def delete_template(avatar_id):
    if not valid_id(avatar_id):
        raise ValueError('Avatar personalizado invalido')
    root = directory().resolve()
    paths = [(root / (avatar_id + suffix)).resolve() for suffix in ('.json', '.png', '.jpg', '.json.tmp')]
    if any(path.parent != root for path in paths):
        raise ValueError('Caminho invalido')
    if not any(path.is_file() for path in paths):
        raise FileNotFoundError(avatar_id)
    for path in paths:
        path.unlink(missing_ok=True)


def templates():
    result = []
    for path in directory().glob("custom_*.json"):
        try:
            item = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(item["name"], str) and isinstance(item["created"], str) and valid_id(item["id"]) and (directory() / (item["id"] + ".png")).is_file():
                result.append(item)
        except (ValueError, KeyError, OSError, TypeError):
            continue
    return sorted(result, key=lambda item: item["created"], reverse=True)


def prepare_image(data):
    try:
        with Image.open(io.BytesIO(data)) as source:
            if source.width * source.height > 50_000_000:
                raise ValueError("A foto e grande demais. Use uma imagem de ate 50 megapixels.")
            if min(source.size) < 128:
                raise ValueError("A foto precisa ter pelo menos 128 pixels em cada lado.")
            if source.format not in ("PNG", "JPEG", "WEBP"):
                raise ValueError("Use uma foto PNG, JPG ou WebP.")
            image = ImageOps.exif_transpose(source)
            alpha = image.mode in ("RGBA", "LA") or "transparency" in image.info
            image = image.convert("RGBA" if alpha else "RGB")
            image = ImageOps.contain(image, (1280, 720), Image.Resampling.LANCZOS)
            canvas = Image.new(image.mode, (1280, 720), (0, 0, 0, 0) if alpha else (28, 31, 38))
            canvas.paste(image, ((1280-image.width)//2, (720-image.height)//2))
            return canvas
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
        raise ValueError("Nao foi possivel abrir a foto. Use PNG, JPG ou WebP valido.") from exc


def register(data, name, loader):
    name = " ".join(name.split())
    if not name or len(name) > 80:
        raise ValueError("Escolha um nome com 1 a 80 caracteres.")
    image = prepare_image(data)
    avatar_id = "custom_" + uuid.uuid4().hex
    path = directory() / (avatar_id + ".png")
    preview = directory() / (avatar_id + ".jpg")
    metadata = directory() / (avatar_id + ".json")
    try:
        image.save(path)
        avatar = loader.load(path, avatar_id=avatar_id)
        thumbnail = image.convert("RGB")
        thumbnail.thumbnail((320, 180))
        thumbnail.save(preview, quality=88)
        item = {"id": avatar_id, "name": name, "created": datetime.now(timezone.utc).isoformat()}
        pending = metadata.with_suffix(".json.tmp")
        pending.write_text(json.dumps(item, ensure_ascii=False), encoding="utf-8")
        pending.replace(metadata)
        return item, avatar
    except Exception:
        path.unlink(missing_ok=True)
        preview.unlink(missing_ok=True)
        metadata.unlink(missing_ok=True)
        raise
