import hashlib
from app.config import CACHE_DIR
from app.services.http_service import get_bytes

async def download_cached_image(url: str) -> bytes:
    path = CACHE_DIR / f"gibs-{hashlib.sha256(url.encode()).hexdigest()}.jpg"
    if path.exists():
        return path.read_bytes()
    content = await get_bytes(url)
    path.write_bytes(content)
    return content
