from aiogram.filters import Filter
from aiogram.types import Message

from main.models import BotUser
from main.services.bot_user import is_user_registered, get_user


class IsRegisteredFilter(Filter):
    async def __call__(self, message: Message) -> bool:
        return await is_user_registered(message.from_user)


class IsEditorFilter(Filter):
    async def __call__(self, message: Message) -> bool:
        user = await get_user(message.from_user)
        if not user:
            return False
        return user.role == BotUser.BotUserRoles.EDITOR or await user.ais_admin
