from asgiref.sync import sync_to_async

from aiogram.types.user import User
from django.db.models.query import QuerySet
from main.models import BotUser, StudentGroup


async def is_user_registered(user: User | None = None, user_query: QuerySet | None = None) -> bool:
    if user_query is None:
        if not user:
            raise ValueError(__name__ + ': requires at least one argument but 0 given.')
        user_query = BotUser.objects.filter(
            full_name=user.full_name,
            username=user.username,
        )
    get_user_count = sync_to_async(user_query.count)
    return bool(await get_user_count())


def is_user_editor(user: BotUser) -> bool:
    return user.role == BotUser.BotUserRoles.EDITOR or user.is_admin


async def get_user(user: User | None = None, user_id: int | None = None) -> BotUser | None:
    queryset = BotUser.objects.select_related('group')
    if user:
        queryset = queryset.filter(full_name=user.full_name, username=user.username)
    elif user_id:
        queryset = queryset.filter(id=user_id)
    else:
        raise ValueError(__name__ + ': requires at least one argument but 0 given.')
    user_registered = await is_user_registered(user_query=queryset)
    if not user_registered:
        return None
    return await queryset.afirst()




async def create_user(user: User, group: StudentGroup) -> BotUser:
    return await BotUser.objects.acreate(
        full_name=user.full_name,
        username=user.username,
        telegram_id=user.id,
        group=group
    )


async def _get_student_group_by_name(name: str, queryset: QuerySet) -> StudentGroup | None:
    student_group_query = queryset.filter(name=name)
    get_group_count = sync_to_async(student_group_query.count)
    is_group_exist = bool(await get_group_count())
    if not is_group_exist:
        return None
    return await student_group_query.afirst()


async def _get_student_group_by_user(user: User, queryset: QuerySet) -> StudentGroup | None:
    user = await get_user(user)
    if not user or user.group_id is None:
        return None
    student_group_query = queryset.filter(id=user.group_id)
    get_group_count = sync_to_async(student_group_query.count)
    is_group_exist = bool(await get_group_count())
    if not is_group_exist:
        return None
    return user.group


async def get_student_group(name: str | None = None, user: User | None = None) -> StudentGroup | None:
    queryset = StudentGroup.objects.select_related('admin')
    if name:
        return await _get_student_group_by_name(name, queryset)
    if user:
        return await _get_student_group_by_user(user, queryset)

    raise ValueError(__name__ + ': requires at least one argument but 0 given.')


ais_user_editor = sync_to_async(is_user_editor)
