import httpx

async def get_json(url: str, params: dict | None = None) -> dict:
    async with httpx.AsyncClient(timeout=45, follow_redirects=True,
                                 headers={"User-Agent": "EarthJukebox/1.0"}) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        return response.json()

async def get_bytes(url: str) -> bytes:
    async with httpx.AsyncClient(timeout=45, follow_redirects=True,
                                 headers={"User-Agent": "EarthJukebox/1.0"}) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.content
