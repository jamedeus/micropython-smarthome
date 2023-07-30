from asyncio import *


async def sleep_us(us):
    # Convert microseconds to seconds
    await sleep(us / 1000000.0)


async def sleep_ms(ms):
    # Convert milliseconds to seconds
    await sleep(ms / 1000.0)
