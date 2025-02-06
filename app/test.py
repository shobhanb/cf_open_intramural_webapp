import asyncio
import logging

from logger import setup_logger

from app.cf_games.service import get_cf_data

log = logging.getLogger(__name__)


async def main() -> None:
    setup_logger()
    entrants, scores = await get_cf_data("31316", "2024")

    log.info(entrants[0].keys())
    log.info(entrants[0].values())

    log.info(scores[0].keys())
    log.info(scores[0].values())


if __name__ == "__main__":
    asyncio.run(main())
