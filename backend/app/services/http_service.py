
import httpx

TIMEOUT = httpx.Timeout(
    connect=10.0,
    read=25.0,
    write=15.0,
    pool=10.0,
)

LIMITS = httpx.Limits(
    max_connections=20,
    max_keepalive_connections=10,
    keepalive_expiry=30.0,
)

_client = None


def get_client() -> httpx.AsyncClient:
    global _client

    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(
            timeout=TIMEOUT,
            limits=LIMITS,
            follow_redirects=True,
            headers={
                "User-Agent": "EarthJukebox/1.0"
            },
        )

    return _client


async def get_json(
    url: str,
    params: dict | None = None
) -> dict:
    client = get_client()

    response = await client.get(
        url,
        params=params
    )

    response.raise_for_status()
    return response.json()


async def get_bytes(url: str) -> bytes:
    client = get_client()

    response = await client.get(url)
    response.raise_for_status()

    return response.content
