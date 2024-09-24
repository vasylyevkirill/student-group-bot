from aiogram.filters import Filter
from aiogram.types import Message

from main.services.bot_user import is_user_registered


class IsRegisteredFilter(Filter):
    async def __call__(self, message: Message) -> bool:
        return await is_user_registered(message.from_user)
