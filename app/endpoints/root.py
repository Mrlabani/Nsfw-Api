import json
from typing import List, Dict, Any

import httpx
from fastapi import APIRouter, Depends, HTTPException

from app.adultscrapper import AdultScrapper
from app.helper import elapsed_time, format_video_payload

router = APIRouter()

UPSTASH_REDIS_REST_URL = "https://quality-mastodon-17670.upstash.io"
UPSTASH_REDIS_REST_TOKEN = "AUUGAAIncDFkNzBjOTM3N2ViM2E0ZmU1OTA5N2NmZDU3YzM1YWI5ZnAxMTc2NzA"


async def get_client():
    async with httpx.AsyncClient(timeout=20) as client:
        yield client


def validate_amount(amount: int):
    if amount <= 0 or amount > 100:
        raise HTTPException(status_code=400, detail="Amount must be between 1 and 100")
    return amount


async def get_cache(key: str) -> Any:
    headers = {"Authorization": f"Bearer {UPSTASH_REDIS_REST_TOKEN}"}
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{UPSTASH_REDIS_REST_URL}/get/{key}", headers=headers)
        data = resp.json()
        if data.get("result"):
            return json.loads(data["result"])
    return None


async def set_cache(key: str, value: Any, expire: int = 3600):
    headers = {"Authorization": f"Bearer {UPSTASH_REDIS_REST_TOKEN}"}
    payload = {
        "key": key,
        "value": json.dumps(value),
        "px": expire * 1000  # expiration in milliseconds
    }
    async with httpx.AsyncClient() as client:
        await client.post(f"{UPSTASH_REDIS_REST_URL}/set", headers=headers, json=payload)


async def fetch_videos(scraper: AdultScrapper, search: str, amount: int, redtube=False, xvideos=False):
    cache_key = f"{scraper.base_url}:{search}:{amount}"
    cached = await get_cache(cache_key)
    if cached:
        return cached

    if redtube:
        videos = await scraper.get_redtube_video(amount, search)
        videos = [format_video_payload(vid.get("video"), True) for vid in videos]
    elif xvideos:
        videos = await scraper.send_video(search, amount, True)
        videos = [format_video_payload(vid) for vid in videos]
    else:
        videos = await scraper.send_video(search, amount)
        videos = [format_video_payload(vid) for vid in videos]

    await set_cache(cache_key, videos)
    return videos


@router.get("/xnxx/{amount}/{search}")
@elapsed_time
async def xnxx(amount: int, search: str, client: httpx.AsyncClient = Depends(get_client)) -> List[Dict[str, Any]]:
    validate_amount(amount)
    scraper = AdultScrapper(base_url="https://www.xnxx.com", session=client)
    return await fetch_videos(scraper, search, amount)


@router.get("/xvideos/{amount}/{search}")
@elapsed_time
async def xvideos(amount: int, search: str, client: httpx.AsyncClient = Depends(get_client)) -> List[Dict[str, Any]]:
    validate_amount(amount)
    scraper = AdultScrapper(base_url="https://www.xvideos.com", session=client)
    return await fetch_videos(scraper, search, amount, xvideos=True)


@router.get("/redtube/{amount}/{search}")
@elapsed_time
async def redtube(amount: int, search: str, client: httpx.AsyncClient = Depends(get_client)) -> List[Dict[str, Any]]:
    validate_amount(amount)
    scraper = AdultScrapper(base_url="https://www.redtube.com", session=client)
    return await fetch_videos(scraper, search, amount, redtube=True)
