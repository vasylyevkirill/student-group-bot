import re
from asgiref.sync import sync_to_async

from aiogram.filters import Filter
from aiogram.types import Message

from main.models import BotUser, SubjectScheduleItemMark
from main.services.bot_user import get_user


class _RegexFilter(Filter):
    def __init__(self):
        assert self.REGEX_MASK

    async def __call__(self, message: Message) -> bool:
        return bool(self.REGEX_MASK.match(message.text))


class DateFilter(_RegexFilter):
    REGEX_MASK = re.compile(
        r'^(?:(?:31(\/|-|\.)(?:0?[13578]|1[02]))\1|(?:(?:29|30)(\/|-|\.)'
        r'(?:0?[13-9]|1[0-2])\2))(?:(?:1[6-9]|[2-9]\d)?\d{2})$|^(?:29(\/|-|\.)'
        r'0?2\3(?:(?:(?:1[6-9]|[2-9]\d)?(?:0[48]|[2468][048]|[13579][26])|(?:'
        r'(?:16|[2468][048]|[3579][26])00))))$|^(?:0?[1-9]|1\d|2[0-8])(\/|-|\.)'
        r'(?:(?:0?[1-9])|(?:1[0-2]))\4(?:(?:1[6-9]|[2-9]\d)?\d{2})$'
    )


class NumberFilter(_RegexFilter):
    REGEX_MASK = re.compile(r'^[0-9]+$')


class IsRegisteredFilter(Filter):
    async def __call__(self, message: Message) -> bool:
        self.user = await get_user(message.from_user)
        if not self.user:
            return False
        return True


class IsEditorFilter(IsRegisteredFilter):  # admin is also editor
    async def __call__(self, message: Message) -> bool:
        if not await super().__call__(message):
            return False
        self.user.role
        return self.user.role == BotUser.BotUserRoles.EDITOR or await self.user.ais_admin


class IsAdminFilter(IsRegisteredFilter):
    async def __call__(self, message: Message) -> bool:
        if not await super().__call__(message):
            return False
        return await self.user.ais_admin


class IsTeacherUserFilter(IsRegisteredFilter):
    async def __call__(self, message: Message) -> bool:
        if not await super().__call__(message):
            return False
        return self.user.role == BotUser.BotUserRoles.TEACHER


class IsSuperUserFilter(IsRegisteredFilter):
    async def __call__(self, message: Message) -> bool:
        if not await super().__call__(message):
            return False
        return self.user.role == BotUser.BotUserRoles.SUPER_USER


class IsScheduleItemMarkEditingTitle(IsRegisteredFilter):
    async def __call__(self, message: Message) -> bool:
        if not await super().__call__(message):
            return False

        editing_marks = SubjectScheduleItemMark.objects.filter(creator=self.user, title='')
        get_edititng_marks_count = sync_to_async(editing_marks.count)
        if not await get_edititng_marks_count():
            return False
        return True


class IsScheduleItemMarkEditingText(IsRegisteredFilter):
    async def __call__(self, message: Message) -> bool:
        if not await super().__call__(message):
            return False

        editing_marks = SubjectScheduleItemMark.objects.filter(creator=self.user, text='')
        get_edititng_marks_count = sync_to_async(editing_marks.count)
        if not await get_edititng_marks_count():
            return False
        return True
