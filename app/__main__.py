import logging
import random
from typing import List

import httpx
from fastapi import FastAPI

from app.adultscrapper import AdultScrapper
from app.helper import elapsed_time, format_video_payload
from app.suggestion import router as suggestion_endpoint

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s",
    handlers=[logging.StreamHandler()],
)
logging.getLogger("httpx").setLevel(logging.WARNING)


app = FastAPI(openapi_url="", redoc_url=None)
app.include_router(suggestion_endpoint)


@app.get("/xnxx/{amount}/{search}")
@elapsed_time
async def xnxx(amount: int, search: str) -> List:
    """Get Xnxx Videos"""
    xnxx = AdultScrapper(base_url="https://www.xnxx.com", session=httpx.AsyncClient())
    links = await xnxx.send_video(search, amount)
    return [format_video_payload(vid) for vid in links]


@app.get("/xvideos/{amount}/{search}")
@elapsed_time
async def xvideos(amount: int, search: str) -> List:
    """Get Xvideos Videos"""
    xvideos = AdultScrapper(
        base_url="https://www.xvideos.com", session=httpx.AsyncClient()
    )
    links = await xvideos.send_video(search, amount, True)
    return [format_video_payload(vid) for vid in links]


@app.get("/redtube/{amount}/{search}")
@elapsed_time
async def redtube(amount: int, search: str) -> List:
    """Get Redtube Videos"""
    redtube = AdultScrapper(
        base_url="https://www.redtube.com", session=httpx.AsyncClient()
    )
    links = await redtube.get_redtube_video(amount, search)
    return [format_video_payload(vid.get("video"), True) for vid in links]
