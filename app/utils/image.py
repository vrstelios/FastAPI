import uuid
from io import BytesIO
import httpx
from PIL import Image, ImageOps
from starlette.concurrency import run_in_threadpool
from app.core.config import settings

http_client = httpx.Client()

def process_profile_image(content: bytes) -> tuple[bytes, str]:
    with Image.open(BytesIO(content)) as original:
        img = ImageOps.exif_transpose(original)
        img = ImageOps.fit(img, (300, 300), method=Image.Resampling.LANCZOS)

        if img.mode in ("RGBA", "LA", "P"):
            img = img.convert("RGB")

        filename = f"{uuid.uuid4().hex}.jpg"

        output = BytesIO()
        img.save(output, "JPEG", quality=85, optimize=True)
        output.seek(0)

    return output.read(), filename

def _updated_to_oracle(file_bytes: bytes, key: str) -> None:
    url = f"{settings.oracle_par_url}{key}"

    response = http_client.put(
        url,
        content=file_bytes,
        headers={"Content-Type": "image/jpeg"}
    )
    response.raise_for_status()

def _delete_from_oracle(key: str) -> None:
    url = f"{settings.oracle_par_url}{key}"
    try:
        response = http_client.delete(url)
        response.raise_for_status()
        print(f"Delete: SUCCESS for {key}")
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
           print(f"Delete: Soft-skipped (Oracle Bucket-level PARs do not support DELETE operations directly).")
        else:
            raise e

async def upload_profile_image(file_bytes: bytes, filename: str) -> None:
    key = f"profile_pics/{filename}"
    await run_in_threadpool(_updated_to_oracle, file_bytes, key)

async def delete_profile_image(filename: str | None) -> None:
    if filename is None:
        return
    key = f"profile_pics/{filename}"
    await run_in_threadpool(_delete_from_oracle, key)


