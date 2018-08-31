import aiofiles
import asyncio

async def print_file(f):
  contents = await f.read()
  print(contents)

async def main():
  async with aiofiles.open('../README.md', 'rt') as f:
    await print_file(f)

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.close()


