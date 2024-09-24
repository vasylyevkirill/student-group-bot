import os
import sys
import asyncio
import logging
import django

from aiogram.client.default import DefaultBotProperties
from aiogram import Bot
from aiogram import Dispatcher
from aiogram.enums import ParseMode


sys.dont_write_bytecode = True
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'main.settings')
django.setup()
dp = Dispatcher()


async def main() -> None:
    from main.views import router as main_router
    from django.conf import settings
    dp.include_router(main_router)
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    await dp.start_polling(bot)


if __name__ == '__main__':
    from django.conf import settings
    logging.basicConfig(level=logging.INFO, format=settings.LOGGING_FORMAT)
    logger = logging.getLogger(__name__)
    asyncio.run(main())
