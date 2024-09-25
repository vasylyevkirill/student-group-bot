import re
from aiogram.filters import Filter
from aiogram.types import Message

from main.models import BotUser
from main.services.bot_user import is_user_registered, get_user


class IsRegisteredFilter(Filter):
    async def __call__(self, message: Message) -> bool:
        return await is_user_registered(message.from_user)


class IsEditorFilter(Filter):  # admin is also editor
    async def __call__(self, message: Message) -> bool:
        user = await get_user(message.from_user)
        if not user:
            return False
        return user.role == BotUser.BotUserRoles.EDITOR or await user.ais_admin


class IsAdminFilter(Filter):
    async def __call__(self, message: Message) -> bool:
        user = await get_user(message.from_user)
        if not user:
            return False
        return await user.ais_admin


class IsTeacherUserFilter(Filter):
    async def __call__(self, message: Message) -> bool:
        user = await get_user(message.from_user)
        if not user:
            return False
        return user.role == BotUser.BotUserRoles.TEACHER


class IsSuperUserFilter(Filter):
    async def __call__(self, message: Message) -> bool:
        user = await get_user(message.from_user)
        if not user:
            return False
        return user.role == BotUser.BotUserRoles.SUPER_USER


class DateFilter(Filter):
    DATE_MASK = re.compile(
        r'^(?:(?:31(\/|-|\.)(?:0?[13578]|1[02]))\1|(?:(?:29|30)(\/|-|\.)'
        r'(?:0?[13-9]|1[0-2])\2))(?:(?:1[6-9]|[2-9]\d)?\d{2})$|^(?:29(\/|-|\.)'
        r'0?2\3(?:(?:(?:1[6-9]|[2-9]\d)?(?:0[48]|[2468][048]|[13579][26])|(?:'
        r'(?:16|[2468][048]|[3579][26])00))))$|^(?:0?[1-9]|1\d|2[0-8])(\/|-|\.)'
        r'(?:(?:0?[1-9])|(?:1[0-2]))\4(?:(?:1[6-9]|[2-9]\d)?\d{2})$'
    )

    async def __call__(self, message: Message) -> bool:
        return bool(self.DATE_MASK.match(message.text))
