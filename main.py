import os
import sys
import asyncio
import logging
import django


sys.dont_write_bytecode = True
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'main.settings')
django.setup()


async def main() -> None:
    from main.bot import dp, bot
    await dp.start_polling(bot)


if __name__ == '__main__':
    from django.conf import settings
    logging.basicConfig(level=logging.INFO, format=settings.LOGGING_FORMAT)
    logger = logging.getLogger(__name__)
    asyncio.run(main())
