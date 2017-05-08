import logging

import aiohttp

logger = logging.getLogger(__name__)


async def get_text(url, headers=None):
    async with aiohttp.ClientSession(headers=headers) as session:
        try:
            async with session.get(url) as response:
                body = await response.read()
                return body.decode('utf-8')
        except aiohttp.client_exceptions.ClientConnectorError as e:
            logger.error(e)


async def get_json(url, headers=None):
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url) as response:
            return await response.json()
