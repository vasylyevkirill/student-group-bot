from aiogram.client.default import DefaultBotProperties
from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram import Dispatcher
from django.conf import settings

from main.views import router as main_router


dp = Dispatcher()
dp.include_router(main_router)
bot = Bot(
    token=settings.BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
